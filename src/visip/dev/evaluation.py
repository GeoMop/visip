"""
Evaluation of a workflow.
1. workflow is dynamically rewritten to the Task DAG
2. small tasks may be merged in this process
3. Evaluation of tasks is given by evaluate methods of actions.
4. Task is a mapping of its inputs to its outputs.
5. All task evaluations are stored in a database, with lookup by the hash of the task's input.
6. As the Task DAG is processed the tasks with the input in the database are skipped.
7. Hashes are long enough to have probability of the collision small enough, so we
    relay on equality of the data if the hashes are equal.
4. Tasks are assigned to the resources by scheduler,
"""
import queue
import sys
import os
from typing import Optional, List, Dict, Tuple, Any, Union
import logging
import heapq
import time
from .environment import Environment

from . import data, task as task_mod, base, dfs, action_instance as instance, dtype
from .task_result import TaskResult
from .action_workflow import _Workflow
from ..eval.cache import ResultCache
from ..code.unwrap import into_action
from ..code.dummy import Dummy, DummyAction, DummyWorkflow
from . import tools, module, resource
from ..action.constructor import Value

logger = logging.getLogger(__name__)
def setup_logger(logger):
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler('evaluation.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)
    logger.setLevel(logging.INFO)

    return logger
setup_logger(logger)

class EvalLogger:
    def __init__(self):
        self._logger = logger

    def task_expand(self, composed: task_mod.Composed, new_tasks: Dict[str, task_mod.TaskSchedule]):
        """
        :param composed:
        :param new_tasks: action_call name -> TackSchedule
        :return:
        """

        if new_tasks is not None:
            self._logger.info(f"Expand: {composed} <- {[composed.short_hash(h) for h in composed.task.input_hashes]}")
            for t in new_tasks.values():
                self._logger.info(f"    {t.action}#{t.short_hash(t.result_hash)}  <- {[t.short_hash(h) for h in t.input_hashes]}")
        # else:
        #     self._logger.info(f"    Can not expand yet.")

    def task_schedule(self, task: task_mod.TaskSchedule):
        self._logger.info(f"Schedule: {task}")

    def task_assign(self, task: task_mod.TaskSchedule, resource):
        self._logger.info(f"Assign: {task} to {resource}")
        hashes = [task.short_hash(h) for h in task.task.input_hashes]
        self._logger.info(f"        Inputs: {hashes}\n")



class Scheduler:
    """
    Simplest scheduler:
    - topological sort, simulated asignment to the resource (implemented in ResourceBase)
    - get resource with minimal load
    TODO: Scheduler based on Khan algorithm tracking the front of tasks with complete prerequisities.
    See: Coffman–Graham algorithm : add first the task that had been added as the first to the front, i.e. use front data structure fo the
    task front representation. Without accounting for the task times, assign at most 2-3 tasks to the resource in advance.
    - task time estimation model
    - select critical tasks first,
    - determine resources "result latency" for the task
    - assign to the lowest latency resource
    - then assign tasks with lower priority (have a slack), use the slack possibly to use larger latency resources
    """
    def __init__(self, resources: resource.ResourceBase, cache:ResultCache, n_tasks_limit:int = 1024):
        """
        :param tasks_dag: Tasks to be evaluated.
        """

        self.resources = resources
        # Dict of available resources
        self.cache = cache
        # Result cache instance
        self.n_tasks_limit = n_tasks_limit
        # When number of assigned (and unprocessed) tasks is over the limit we do not accept
        # further DAG expansion.

        # self.tasks = {}
        # !! possibly depricated
        # all not yet sumitted tasks, vertices of the DAG that is optimized by the scheduler
        # maps task ID to the task

        self._ready_queue = []
        # Priority queue of the 'ready' tasks.  Used to submit the ready tasks without
        # whole DAG optimization. Priority is the

        self._task_map: Dict[int, task_mod.TaskSchedule] = {}
        # Maps task.result_hash to scheduler task.
        # - get TaskSchedule from finished TaskBase
        # - flexible referencing inputs and outputs
        # TODO: implement deleting of completed tasks (possible problem with dependent tasks)


        self._start_time = time.perf_counter()
        # Start time of the DAG evaluation.


        # self._topology_sort = []
        # !! possibly depricated
        # Topological sort of the tasks.

        self.n_scheduled_tasks = 0
        self.n_assigned_tasks = 0
        self.n_finished_tasks = 0

        self._resource_map = {base.ActionKind.Regular: [],
                              base.ActionKind.Meta: [],
                              base.ActionKind.Generic: []}
        # map from action kind to list of capable resources
        self._scheduled_not_finished = set()
        self._all_ready_set = set()

        for i, res in enumerate(self.resources):
            for kind in res.action_kind_list:
                self._resource_map[kind].append(i)

    def can_expand(self):
        return self.n_assigned_tasks < self.n_tasks_limit

    def is_finished(self, task: task_mod.TaskSchedule):
        return self.cache.is_finished(task.result_hash)

    # @property
    # def n_assigned_tasks(self):
    #     return len(self.tasks)

    """
    ####  Graph modification functions.
    """

    def task(self, task_hash):
        return self._task_map[task_hash]

    def create_task(self, parent, child_name, task_base):
        """
        Create task from the given action and its input tasks.
        """
        try:
            task = self.task(task_base.result_hash)
            #print("Duplicit: ", task, task_base)
            return task
        except KeyError:
            pass

        task_type = task_base.action.task_type
        if task_type == base.TaskType.Atomic:
            sched_task = task_mod.Atomic(parent, child_name, task_base, self)
        elif task_type == base.TaskType.Composed:
            sched_task = task_mod.Composed(parent, child_name, task_base, self)
        else:
            assert False
        self.log.task_schedule(sched_task)
        self._task_map[sched_task.id] = sched_task
        self.n_scheduled_tasks += 1
        self._scheduled_not_finished.add(sched_task.id)
        return sched_task

    def expand_task(self, composed, result):
        # assert len(result.output_tasks) == 0
        # result could have existing outputs if it is duplicate
        # that could happen for Value and constant value actions, e.g. factorial(16)
        # could be used repetitively leading to repetitive expansion, but results
        # are taken from the result cache.

        composed.shortcut(result_task=result)
        for t in result.output_tasks:
            self.ready_queue_push(t)
        self.finish_task(composed)
        composed.status = task_mod.Status.expanded

    def get_time(self):
        return time.perf_counter() - self._start_time

    def ready_queue_push(self, task):
        if task.status >= task_mod.Status.ready:
            #print("RQ dupl: ", task)
            # assert isinstance(task.action, Value), task
            return

        if task.is_ready(self.cache):
            task.status = task_mod.Status.ready
            if task.id in self._all_ready_set:
                print(f"Duplicate: {task}")
            self._all_ready_set.add(task.id)
            heapq.heappush(self._ready_queue, task)


    def _collect_finished(self):
        # collect finished tasks, update ready queue
        for resource in self.resources:
            for task in resource.get_finished():
                self.finish_task(task)

    def finish_task(self, task):
        print("Finish: ", task)
        sched_task = self._task_map[task.result_hash] # !!!! ???? pop
        try:
            self._scheduled_not_finished.remove(sched_task.id)
        except KeyError:
            print(f"Already finished: {sched_task}")
            assert sched_task.status == task_mod.Status.finished
            return
        sched_task.status = task_mod.Status.finished
        self.n_finished_tasks += 1
        for dep_task in sched_task.output_tasks:
            if dep_task.status >= task_mod.Status.ready:
                print(f"Cyclic dependency: {dep_task} on {sched_task}.")
                assert False
            # TODO: more efficient ready_queue update
            self.ready_queue_push(dep_task)

    def update(self, tasks):
        """
        Update resources, collect finished tasks, submit new ready tasks.
        Should be called approximately every 'call_period' seconds.
        """
        for t in tasks:
            #self.estimate_task_eval_time(t)
            self.ready_queue_push(t)

        #self..append(tasks)

        #self.optimize()  # currently performs full CPM algorithm

        finished = self._collect_finished()

        print(f"{self.n_scheduled_tasks} > {len(self._all_ready_set)} ( >  RQ: {len(self._ready_queue)}) > {self.n_assigned_tasks} > {self.n_finished_tasks}")
        completed = len(self._ready_queue) == 0
        while self._ready_queue:
            task = heapq.heappop(self._ready_queue)
 #           if task.id in self.tasks:   # deal with duplicate entrieas in the queue
            assert not self.is_finished(task), task
            #assert task.status == Status.ready
            self.assign_task(task)

            #del self.tasks[task.id]
        completed = completed and self.n_finished_tasks == self.n_assigned_tasks
        print([self.task(h) for h in self._scheduled_not_finished])
        return len(self._scheduled_not_finished) == 0

    def assign_task(self, task):
        self.n_assigned_tasks += 1
        assert not isinstance(task, task_mod.Composed)
        # Deal directly with Value and Pass actions, possibly even in early stages of scheduling.

        kind = task.task.action.action_kind
        kind_list = self._resource_map[kind]
        assert kind_list, 'There are no resource capable of run "{}".'.format(kind)
        task.resource_id = kind_list[0]
        resource = self.resources[task.resource_id]
        self.log.task_assign(task, resource)
        task.status = task_mod.Status.submitted
        resource.submit(task.task)



    def optimize(self):
        """
        Perform CPM on the DAG of non-submitted tasks.
        Assign start_times and priorities according to the slack time.
        Assume just a single resource.

        Update:
         - task.start_time - currently no use
         - update ready_queue (if finish doesn't work)
         - _topological_sort - not in use
        :return:
        """
        # perform topological sort
        def predecessors(task):
            if self.is_finished(task):
                return []
            else:
                max_end_time = 0
                for pre in task.inputs:
                    max_end_time = max(max_end_time, pre.start_time + pre.eval_time)
                task.start_time = max_end_time
            return task.inputs

        def post_visit(task):
            kind = task.task.action.action_kind
            kind_list = self._resource_map[kind]
            assert kind_list, 'There are no resource capable of run "{}".'.format(kind)
            task.resource_id = kind_list[0]

            self.ready_queue_push(task)
            self._topology_sort.append(task)


        dfs.DFS(neighbours=predecessors,
                postvisit=post_visit).run(self.tasks.values())



# @attr.s(auto_attribs=True)
# class Result:
#     input: bytearray
#     result: bytearray
#     result_hash: bytes
#
#     @staticmethod
#     def make_result(input, result):
#         input = data.serialize(input)
#         result = data.serialize(result)
#         res_hash = data.hash_fn(result)
#         return Result(input, result, res_hash)
#
#     def extract_result(self):
#         return deserialize(self.result)





ActionOrDummy = Union[dtype._ActionBase, DummyAction, DummyWorkflow]
DataOrDummy = Union[dtype.DType, Dummy, DummyAction, DummyWorkflow]

class Evaluation:
    """/
    The class for evaluation of a workflow.
    - perform expansion of composed tasks into the task DAG
    - can evaluate a workflow in interaction with the Scheduler
    - hierarchical view of the execution DAG, tasks are organised to the tree of composed tasks
      currently all tasks are kept, in future, just a map from the task address in the tree to its input hash would be
      enough computing results of the micro action on the fly
    - grouping of actions into macro actions is done here as the part of the expansion process



    Execute the 'wf' workflow for the data arguments given by 'inputs'.

    - Assign 'inputs' to the workflow inputs, effectively creating an analysis (workflow without inputs).
    - Expand the workflow to the Task DAG.
    - while not finished:
        expand_composed_tasks
        update scheduler

    We use Dijkstra algorithm (on incoplete graph) to process tasks according to the execution time on the reference resource.
    Tasks are identified by the hash of their inputs.
    :param wf:
    :param inputs:
    :return: List of all tasks.
    """






    def __init__(self,
                 scheduler: Scheduler = None,
                 workspace: str = ".",
                 plot_expansion: bool = False
                 ):
        """
        Create object for evaluation of the workflow 'analysis' with no parameters.
        Use 'make_analysis' to substitute arguments to arbitrary action.

        :param analysis: an action without inputs
        """
        self.log = EvalLogger()
        self.cache = ResultCache()

        if scheduler is None:
            scheduler = Scheduler([ resource.Resource(self.cache) ], self.cache)
        self.scheduler = scheduler
        self.scheduler.log = self.log
        self.workspace = workspace
        self.plot_expansion = plot_expansion
        #self.plot_expansion = True
        self.final_task = None

        self.composed_id = 0
        # Auxiliary ID of composed tasks to break ties
        self.queue = []
        # Priority queue of the composed tasks to expand. Tasks are expanded until the task DAG is not
        # complete or number of unresolved tasks is smaller then given limit.
        os.makedirs(workspace, exist_ok=True)

        self.force_finish = False
        # Used to force end of evaluation after an error.
        self.error_tasks = []
        # List of tasks finished with error.
        self.expansion_iter = 0
        # Expansion iteration.



    def estimate_task_eval_time(self, task):
        """
        Estimate the task evaluation time using the action and result_db.
        :param task:
        :return:
        """
        if self.scheduler.is_finished(task):
            task.eval_time = task.end_time - task.start_time
        else:
            task.time_estimate = 1

    def validate_connections(self, action):
        """
        Validation of connections in workflows and other composed actions.
        TODO:
        - make a base class for composed actions, implementing 'validate_connections', 'expand' etc.
        - implement this check
        - accept the error limit
        :param action:
        :return: List of invalid or possibly invalid connections.
        """
        return []

    def _make_analysis(self, action: ActionOrDummy, args:List[DataOrDummy], kwargs:Dict['str', DataOrDummy]):
        """
        Bind values 'inputs' as parameters of the action using the Value action wrappers,
        returns a workflow without parameters.
        :param action:
        :param inputs:
        :return: a bind workflow instance
        """
        #assert action.parameters.is_variadic() or len(inputs) == action.parameters.size()
        if isinstance(action, DummyAction):
            action = action._action_value
        if isinstance(action, DummyWorkflow):
            action = action.workflow

        bind_name = 'all_bind_' + action.name
        workflow = _Workflow(bind_name)

        args_ = [into_action(arg) for arg in args]
        kwargs_ = {key: into_action(arg) for (key, arg) in kwargs.items()}
        bind_action = instance.ActionCall.create(action, *args_, **kwargs_)
            #assert bind_action.arguments[i].status >= instance.ActionInputStatus.seems_ok
        workflow.set_action_input(workflow.result_call, 0, bind_action)
        return workflow

    def run(self, action, *args, **kwargs) -> TaskResult:
        """
        Evaluate given action with given arguments.
        :return:
        """
        analysis = self._make_analysis(action, args, kwargs)
        return self.execute(analysis)

    def execute(self, analysis) -> task_mod.TaskSchedule:
        """
        Execute the workflow.
        assigned_tasks_limit -  maximum number of tasks processed by the Scheduler
                                TODO: should be part of the Scheduler config
        TODO: Reinit scheduler and own structures to allow reuse of the Evaluation object.
        """
        task_base = task_mod._TaskBase(analysis, [], ([],{}))
        self.final_task = self.scheduler.create_task(None, '__root__', task_base)
        self.enqueue(self.final_task)
        # init scheduler

        with tools.change_cwd(self.workspace):
            # print("CWD: ", os.getcwd())
            invalid_connections = self.validate_connections(self.final_task.action)
            if invalid_connections:
                raise Exception(invalid_connections)
            self.expansion_iter = 0
            while True:
                schedule = self.expand_tasks()  # returns list of expanded atomic tasks to schedule
                if self.plot_expansion:
                    self._plot_task_graph(self.expansion_iter)
                completed = self.scheduler.update(schedule)
                if completed:
                    break
                self.expansion_iter += 1
        return TaskResult(self.final_task, self.cache)




    def enqueue(self, task: task_mod.Composed):
        heapq.heappush(self.queue, (self.composed_id, task.time_estimate, task))
        self.composed_id += 1


    def expand_tasks(self):
        """
        Expand composed tasks until number of planed tasks in the scheduler is under the given limit.
        :return: schedule
        # List of new atomic tasks to schedule for execution.
        """
        # Force end of evaluation before all tasks are finished, e.g. due to an error.
        schedule = []
        postpone_expand = []
        # List of composed tasks with postponed expansion, have to be re-enqueued.

        while self.queue and not self.force_finish and self.scheduler.can_expand():
            composed_id, time, composed_task = heapq.heappop(self.queue)
            if composed_task.status == task_mod.Status.expanded:
                # Could happen, for composed tasks dependent only on constants.
                continue
            raw_task_dict = composed_task.expand(self.cache)
            if raw_task_dict is None:
                # Can not expand yet, return back into queue
                postpone_expand.append(composed_task)
            else:
                assert len(raw_task_dict) > 0
                self.log.task_expand(composed_task, raw_task_dict)
                task_dict = {name: self.scheduler.create_task(composed_task, name, task)
                             for name, task in raw_task_dict.items()}
                composed_task.childs = task_dict  # {task.child_id: _TaskBase}
                result_task = composed_task.childs['__result__']

                self.scheduler.expand_task(composed_task, result_task)

                for task in task_dict.values():
                    if isinstance(task, task_mod.Composed):
                        self.enqueue(task)
                    schedule.append(task)

        for task in postpone_expand:
            self.enqueue(task)
        return schedule


    def make_graphviz_digraph(self):
        from . dag_view import DAGView
        from graphviz import Digraph
        g = DAGView("Task DAG")
        #g.attr('graph', rankdir="BT")

        def predecessors(task: task_mod.TaskSchedule):
            for in_task in task.inputs:
                g.edge(task.id.hex()[:6], in_task.id.hex()[:6])
            return task.inputs

        def previsit(task: task_mod.TaskSchedule):

            if self.scheduler.is_finished(task):
                color = 'green'
            elif task.is_ready(self.cache):
                color = 'orange'
            else:
                color = 'gray'
            if isinstance(task, task_mod.Composed):
                style = 'rounded'
            else:
                style = 'solid'
            hex_str = task.id.hex()[:4]
            node_label = f"{task.action.name}:#{hex_str}"   # 4 hex digits, hex returns 0x7d29d9f
            g.node(task.id.hex()[:6], label=node_label, color=color, shape='box', style=style)

        dfs.DFS(neighbours=predecessors,
                previsit=previsit).run([self.final_task])
        return g


    def _plot_task_graph(self, iter):
        filename = "{}_{:02d}".format(self.final_task.action.name, iter)
        print("\nPlotting expansion iter: ", iter)
        #g = self.make_graphviz_digraph()
        #output_path = g.render(filename=filename, format='pdf', cleanup=True, view=True)
        g = self.make_dagviz()
        g.show_qt()
        #print("Out: ", os.path.abspath(output_path))

    def make_dagviz(self):
        from . dag_view import DAGView
        g = DAGView("Task DAG")

        def predecessors(task: task_mod.TaskSchedule):
            inputs = []
            for in_hash in task.task.input_hashes:
                try:
                    in_task = self.scheduler.tasks[in_hash]
                    g.add_edge(task.id.hex()[:6], in_task.id.hex()[:6])
                    inputs.append(in_task)
                except KeyError:
                    pass
            return inputs

        def previsit(task: task_mod.TaskSchedule):

            if self.scheduler.is_finished(task):
                color = 'green'
            elif task.is_ready(self.cache):
                color = 'orange'
            else:
                color = 'gray'
            if isinstance(task, task_mod.Composed):
                style = 'rounded'
            else:
                style = 'solid'
            hex_str = task.id.hex()[:4]
            node_label = f"{task.action.name}:#{hex_str}"   # 4 hex digits, hex returns 0x7d29d9f
            g.add_task_node(task.id.hex()[:6], node_label, color, style)

        dfs.DFS(neighbours=predecessors,
                previsit=previsit).run([self.final_task])
        return g


    def plot_task_graph(self):
        try:
            #self._plot_task_graph()
            self._plot_dag_qt()
        except Exception as e:
            print(e)

    # def task_result(self, task):
    #     return self.cache.value(task.result_hash)


def run(action: Union[dtype._ActionBase, DummyAction],
        *args: DataOrDummy,
        **kwargs: DataOrDummy) -> dtype.DType:
    """
    Use default evaluation setup (local resource only) to evaluate the
    'action' with given arguments 'args' and 'kwargs',
     return just the resulting value not the evaluation structure (TaskResult).
    """
    return Evaluation().run(action, *args, **kwargs).result


def run_plot(action: Union[dtype._ActionBase, DummyAction],
        *args: DataOrDummy,
        **kwargs: DataOrDummy) -> dtype.DType:
    """
    Use default evaluation setup (local resource only) to evaluate the
    'action' with given arguments 'args' and 'kwargs',
     return just the resulting value not the evaluation structure (TaskResult).
    """
    return Evaluation(plot_expansion=True).run(action, *args, **kwargs).result

def run_env(script_path:str, env_cfg: dict=None):
    if env_cfg is None:
        env_cfg = {}
    env = Environment.load(env_cfg)
    if env.pbs is None:
        # locally running VISIP
        assert env.container is None    # not supported yet
        cache = ResultCache()

        resources_lists = [resource.create(r, cache) for r in env.resources]
        resources = [resource.Resource(cache)] # always have the local resource
        for rl in resources_lists:
            resources.extend([r for r in rl if r is not None])
        scheduler = Scheduler(resources, cache)
        eval = Evaluation(scheduler, env.workspace)

        mod = module.Module.load_module(script_path)
        analysis = mod.get_analysis()
        if len(analysis) == 0:
            raise ValueError(f"Missing analysis in the script file: {script_path}")
        if len(analysis) > 1:
            raise ValueError(f"More then one analysis in the script file: {script_path}")
        analysis = analysis[0]

        return eval.run(analysis)

        # must load module, only module analysis
        # done in the same
    else:
        # PBS
        pass