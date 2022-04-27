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
import sys
import os
from typing import Optional, List, Dict, Tuple, Any, Union
import logging
import heapq
import time

from . import data, task as task_mod, base, dfs, action_instance as instance, dtype
from .task_result import TaskResult
from .action_workflow import _Workflow
from ..eval.cache import ResultCache
from ..code.unwrap import into_action
from ..code.dummy import Dummy, DummyAction, DummyWorkflow
from . import tools


class Resource:
    """
    Model for a computational resource.
    Resource can provide various kind of feautres specified by dictionary of tags with values None, int or string.
    A task (resp. its action) can specify requested tags, such task can be assigned only to the resource that
    have these tags and have value of an integer tag greater then value of the task.

    We shall start with fixed number of resources, dynamic creation of executing PBS jobs can later be done.

    """
    def __init__(self, cache:ResultCache):
        """
        Initialize time scaling and other features of the resource.
        """
        self.start_latency = 0.0
        # Average time from assignment to actual execution of the task. [seconds]
        self.stop_latency = 0.0
        # Average time from finished task till assignment to actual execution of the task. [seconds]
        self.ref_time = 1.0
        # Average run time for a reference task with respect to the execution on the reference resource.
        self.n_threads = 1
        # Number of threads we can assign to the resource.
        self.n_mpi_proces = 0
        # Maximal number of MPI processes one can assign.
        self._finished = []


        self.cache = cache

        self.action_kind_list = [base.ActionKind.Regular, base.ActionKind.Meta, base.ActionKind.Generic]
        # list of action kind that this resource is capable run

    # def assign_task(self, task, i_thread=None):
    #     """
    #     Just evaluate tthe task immediately.
    #     :param task:
    #     :param i_thread:
    #     :return:
    #     """
    #     task.evaluate()
    #
    # def assign_mpi_task(self, task, n_mpi_procs=None):
    #     pass

    def get_finished(self):
        """
        Return list of the tasks finished since the last call.
        :return:
        """
        finished = self._finished
        self._finished = []
        return finished

    def submit(self, task):
        """
        Basic resource implementation with immediate evaluation of the task during submit.
        :param task:
        :return:
        """

        # TODO: move skipping of finished tasks to the scheduler before submit
        # Do not test again in the Resource, possibly only for longer tasks
        res_value = self.cache.value(task.result_hash)
        if res_value is self.cache.NoValue:
            #assert task.is_ready()
            data_inputs = [self.cache.value(ih) for ih in task.input_hashes]
            #if any([i is self.cache.NoValue for i in data_inputs]):
            #    print(task.action, data_inputs)
            assert not any([i is self.cache.NoValue for i in data_inputs])
            args, kwargs = task.inputs_to_args(data_inputs)
            res_value = task.evaluate_fn(*args, **kwargs)
            # print(task.action)
            # print(task.inputs)
            # print(task_hash, res_value)
            self.cache.insert(task.result_hash, res_value)

        self._finished.append(task)


class EvalLogger:
    def __init__(self):
        logger = logging.getLogger('eval_logger')

        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.setFormatter(formatter)

        file_handler = logging.FileHandler('evaluation.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stdout_handler)
        self._logger = logger

    def task_submit(self, task: task_mod.TaskSchedule, value):
        self._logger.info(f"Finished: {task.action.name}#{task.short_hash(task.id)} := {value}")
        hashes = [task.short_hash(h) for h in task.task.input_hashes]
        self._logger.info(f"        Inputs: {hashes}\n")


    def task_expand(self, composed: task_mod.Composed, new_tasks: Dict[str, task_mod.TaskSchedule]):
        """
        :param composed:
        :param new_tasks: action_call name -> TackSchedule
        :return:
        """

        if new_tasks is not None:
            self._logger.info(f"Expand: {composed}, {composed.short_hash(composed.id)}")
            for t in new_tasks.values():
                self._logger.info(f"    {t.action}#{t.short_hash(t.id)}  <- {[t.short_hash(h) for h in t.task.input_hashes]}")
        # else:
        #     self._logger.info(f"    Can not expand yet.")

class Scheduler:
    def __init__(self, resources:Resource, cache:ResultCache, n_tasks_limit:int = 1024):
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

        self.tasks = {}
        # all not yet sumitted tasks, vertices of the DAG that is optimized by the scheduler
        # maps task ID to the task

        self._ready_queue = []
        # Priority queue of the 'ready' tasks.  Used to submit the ready tasks without
        # whole DAG optimization. Priority is the

        self._task_map = {}
        # Maps task.result_hash to list of scheduler tasks.

        self._start_time = time.perf_counter()
        # Start time of the DAG evaluation.

        self._topology_sort = []
        # Topological sort of the tasks.


        self._resource_map = {base.ActionKind.Regular: [],
                              base.ActionKind.Meta: [],
                              base.ActionKind.Generic: []}
        # map from action kind to list of capable resources

        for i, res in enumerate(self.resources):
            for kind in res.action_kind_list:
                self._resource_map[kind].append(i)

    def can_expand(self):
        return self.n_assigned_tasks < self.n_tasks_limit

    @property
    def n_assigned_tasks(self):
        return len(self.tasks)

    def is_finished(self, task: task_mod.TaskSchedule):
        return self.cache.is_finished(task.result_hash)


    def get_time(self):
        return time.perf_counter() - self._start_time

    def append(self, tasks):
        """
        Add more tasks of the same DAG to be scheduled to the resources,
        :param tasks: All tasks that are new or have changed inputs.
        :return: List of composed tasks to expand. If empty the optimization should be called.
        """
        self.tasks.update({ t.id: t for t in tasks})

    def ready_queue_push(self, task):
        if task.is_ready(self.cache):
            heapq.heappush(self._ready_queue, task)

    def log_submit(self, task):
        pass

    def log_expand(self, task):
        pass


    def _collect_finished(self):
        # collect finished tasks, update ready queue
        finished = []
        for resource in self.resources:
            # res_finished_iter = ( self._task_map.pop(task.result_hash) for task in resource.get_finished() )
            # new_finished = list(itertools.chain.from_iterable(res_finished_iter))
            new_finished = []
            for task in resource.get_finished():
                scheduled_tasks = self._task_map[task.result_hash]
                new_finished.extend(scheduled_tasks)
                scheduled_tasks.clear()

            for task in new_finished:
                for dep_task in task.outputs:
                     self.ready_queue_push(dep_task)
            finished.extend(new_finished)
        return finished


    def update(self):
        """
        Update resources, collect finished tasks, submit new ready tasks.
        Should be called approximately every 'call_period' seconds.
        """
        finished = self._collect_finished()
        while self._ready_queue:
            task = heapq.heappop(self._ready_queue)
            if task.id in self.tasks:   # deal with duplicate entrieas in the queue
                if not self.is_finished(task):
                    assert task.is_ready(self.cache)
                    # TODO: remove _task_map and use just task hashes for task referencing
                    # automaticaly eliminating duplicities in the evaluation DAG
                    # However should be accompanied by the checking the database in order to allow memoizing only
                    # short term history of tasks.
                    key = task.result_hash
                    if key in self._task_map:
                        # We skip evaluation of all tasks with the same result hash.
                        self._task_map[key].append(task)
                    else:
                        self._task_map[key] = [task]
                        self.resources[task.resource_id].submit(task.task)
                        value = self.cache.value(task.id)
                        self.log.task_submit(task, value)
                del self.tasks[task.id]
        return finished

    def optimize(self):
        """
        Perform CPM on the DAG of non-submitted tasks.
        Assign start_times and priorities according to the slack time.
        Assume just a single resource.
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
            scheduler = Scheduler([ Resource(self.cache) ], self.cache)
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


    def tasks_update(self, tasks):
        for t in tasks:
            self.estimate_task_eval_time(t)
        self.scheduler.append(tasks)

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
        workspace -

        :return:
        """
        #TODO: Reinit scheduler and own structures to allow reuse of the Evaluation object.
        task_binding = tools.TaskBinding('__root__', analysis, ([],{}), [])
        self.final_task = task_mod.TaskSchedule._create_task(None, task_binding)
        self.enqueue(self.final_task)
        # init scheduler
        self.tasks_update([self.final_task])


        with tools.change_cwd(self.workspace):
            # print("CWD: ", os.getcwd())
            invalid_connections = self.validate_connections(self.final_task.action)
            if invalid_connections:
                raise Exception(invalid_connections)
            self.expansion_iter = 0
            while not self.force_finish:
                schedule = self.expand_tasks()  # returns list of expanded atomic tasks to schedule
                if self.plot_expansion:
                    self._plot_task_graph(self.expansion_iter)
                self.tasks_update(schedule)     # pass the list to the scheduler, update its hash -> task dictionary
                self.scheduler.optimize()       # currently performs full CPM algorithm
                self.scheduler.update()
                if self.scheduler.n_assigned_tasks == 0:
                    self.force_finish = True
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
            task_dict = composed_task.expand(self.cache)

            if task_dict is None:
                # Can not expand yet, return back into queue
                postpone_expand.append(composed_task)
            else:
                self.log.task_expand(composed_task, task_dict)
                # print("Expanded: ", task_dict)
                for task in task_dict.values():
                    if isinstance(task, task_mod.Composed):
                        self.enqueue(task)
                    schedule.append(task)
                self.tasks_update([composed_task])  # ?? direct scheduling of resulting composed task stub, can be avoided ?
        for task in postpone_expand:
            self.enqueue(task)
        return schedule

    # def extract_input(self):
    #     input_data = List(*[i._result for i in self._inputs])



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

