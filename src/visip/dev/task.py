import enum
from typing import *
from . import data
from . import base
from ..eval import cache
from .tools import compose_arguments, TaskBinding

class Status(enum.IntEnum):
    none = 0
    composed = 1
    assigned = 2
    determined = 3
    ready = 4
    submitted = 5
    running = 6
    finished = 7



class _TaskBase:
    """
    Data class passed to the computational Resources.
    Contains only input hashes, the function to call and binding of the inputs to the function parameters.
    TODO:
    - introduce ActionBody = signature + function ... the stuff necessary for execution on resources
      use it as a data member not as a base class in the Actions
    - convert _TaskBase to TaskWork, use attribs
    - reduce number of properties
    """

    no_value = cache.ResultCache.NoValue

    def __init__(self, action: base.ActionBase,
                 input_hashes: List['data.HashValue'], binding):
        self.action = action
        # Action (like function definition) of the task (like function call).
        self.input_hashes = input_hashes
        # hashes of input tasks

        self.id_args_pair = binding
        # binding of inputs to args and kwargs to be passed to actual evaluation function

        self._result_hash = None
        # Hash of the result

        self.evaluate_fn = lambda x: None
        # Returns a function accepting the input data and computing the result.
        # e.g. action.evaluate
        # TODO: set from TaskSchedule during construction

        self._result_hash = self._lazy_hash()

    def short_hash(self, h:bytes) -> str:
        return h.hex()[:4]

    def action_hash(self):
        return self.action.action_hash()

    @property
    def result_hash(self):
        return self._result_hash

    def _lazy_hash(self):
        task_hash = self.action.action_hash()
        for input_hash in self.input_hashes:
            task_hash = data.hash(input_hash, previous=task_hash)
        return task_hash

    def inputs_to_args(self, data_inputs):
        return compose_arguments(self.id_args_pair, data_inputs)


class TaskSchedule:
    """
    Task used by Scheduler.
    """
    def __init__(self, parent: 'Composed', task_binding: TaskBinding):

        input_hashes = [input.result_hash for input in task_binding.inputs]
        self.task = _TaskBase(task_binding.action, input_hashes, task_binding.id_args_pair)

        # Input tasks for the action's arguments.
        self.outputs: List['TaskSchedule'] = []
        # List of tasks dependent on the result. (Try to not use and eliminate.)

        self.parent: Optional['Composed'] = parent
        # parent task
        self.child_id = task_binding.child_name
        # name of current task within parent
        self.status = Status.none
        # Status of the task, possibly need not to be stored explicitly.

        self.resource_id = None

        self.start_time = -1
        self.end_time = -1
        self.eval_time = 0

        self._inputs = task_binding.inputs # reset in Workflow to its result, but we yet keep original in the task_binding
        # Connect to inputs.
        # TODO: remove dirrect referencing of the tasks use scheduler to refference through the result hashes
        for input in task_binding.inputs:
            assert isinstance(input, TaskSchedule)
            input.outputs.append(self)

        self.set_evaluate_fn()  # set during construction

    @property
    def id(self):
        return self.task.result_hash

    @property
    def action(self):
        return self.task.action

    @property
    def id_args_pair(self):
        return self.task.id_args_pair

    @property
    def inputs(self):
        return self._inputs

    @property
    def result_hash(self):
        return self.task.result_hash

    @property
    def priority(self):
        return 1

    def short_hash(self, h):
        return self.task.short_hash(h)

    def get_path(self):
        path = []
        t = self
        while t is not None:
            path.append(t.child_id)
            t = t.parent
        return path

    def __lt__(self, other):
        return self.priority < other.priority

    @staticmethod
    def _create_task(parent_task, task_binding) -> 'TaskSchedule':
        """
        Create task from the given action and its input tasks.
        """
        task_type = task_binding.action.task_type
        if task_type == base.TaskType.Atomic:
            child = Atomic(parent_task, task_binding)
        elif task_type == base.TaskType.Composed:
            #task_binding.id_args_pair = ([0], {}) # for final auxiliary action
            child = Composed(parent_task, task_binding)
        else:
            assert False
        return child

    def set_evaluate_fn(self):
        assert False, "Not implemented"



class Atomic(TaskSchedule):


    def is_ready(self, cache):
        """
        Update ready status, return
        :return:
        """
        if self.status < Status.ready:
            is_ready = all([cache.is_finished(input_hash) for input_hash in self.task.input_hashes])
            if is_ready:
                self.status = Status.ready
        return self.status >= Status.ready

    def set_evaluate_fn(self):
        """
        For given data evaluate the action and store the result.
        TODO: should handle just status and possibly store the result
        since Resource may execute the task remotely.
        """
        self.task.evaluate_fn = self.action.evaluate


class Composed(Atomic):
    """
    Composed tasks are non-leaf vertices of the execution (recursion) tree.
    The Evaluation class takes care of their expansion during execution according to the
    preferences assigned by the Scheduler.

    After the expansion a composed task is still connected to its inputs, but the inputs are newly
    connected to its slots. Moreover the composed task is made dependent on its own result and
    while its evaluation is empty so any task dependent on the expanded task depends on the result only indirectly
    through the expanded task. So the expansion doesn't break existing task dependencies.
    """

    def __init__(self, parent: 'Composed', task_binding: TaskBinding):
        # TODO: modify Task.create to accept input binding in form of id_args_pair
        super().__init__(parent, task_binding)

        self.time_estimate = 0
        # estimate of the start time, used as expansion priority
        self.childs: Dict[Union[int, str], Atomic] = {}
        # map child_id to the child task, filled during expand.

    def __repr__(self):
        return f"{self.action}"

    def is_ready(self, cache):
        """
        Block submission of unexpanded tasks.
        :return:
        """
        return self.is_expanded() and Atomic.is_ready(self, cache)


    def child(self, item: Union[int, str]) -> Optional[Atomic]:
        """
        Return subtask given by parameter 'item'
        :param item: A unique idenfication of the subtask. The name of the
        action_instance within a workflow, the loop index for ForEach and While actions.
        :return: The subtask or None if the item is no defined.
        """
        assert self.childs
        return self.childs.get(item, None)

    def invalidate(self):
        """
        Invalidate the task and its descendants in the execution DAG using the call tree.
        :return:
        """

    def is_expanded(self):
        return self.childs is not None


    def create_child_task(self, task_binding: TaskBinding) -> TaskSchedule:
        args, kwargs = task_binding.id_args_pair
        assert len(args) + len(kwargs) == len(task_binding.inputs)
        return TaskSchedule._create_task(self, task_binding)

    def expand(self, cache) -> Dict[str, TaskSchedule]:
        """
        Composed task expansion.

        Connect the head tasks to the body and the 'self' (i.e. the tail task) to the result
        action instance of the body. Auxiliary tasks for the heads, result and tail
        are used in order to minimize modification of the task links.

        :return:
            None if the expansion can not be performed, yet.
            Dictionary of child tasks (action_instance_name -> task)
            Empty dict is valid result, used to indicate end of a loop e.g. in the case of ForEach and While actions.
        TODO: tail expansion:
        - no (artificial) task dependent on the body of expansion
        - remove auxiliary Pass tasks from the DAG, can possibly be done with two side hash links
        - task.outputs used in expand() and _collect_finished()
        - composed inputs are hashes, expansion must replace slots (in their outputs)
        - or we can have dedicated PassTask (for slots etc.) this can be removed on any  DAG search
        - tasks dependent on the result - got through composed.outputs (must be pair task, input), must replace particular input hash
        - tasks dependent on the composed have invalid hash

        """
        assert self.action.task_type is base.TaskType.Composed
        assert hasattr(self.action, 'expand')

        # Generate and connect body tasks.
        childs = self.action.expand(self, self.create_child_task, cache)
        if childs is not None:
            assert len(childs) > 0
            self.childs = childs #{task.child_id: task for task in childs}
            #self.childs.expand({})
            result_task = self.childs['__result__']
            assert len(result_task.outputs) == 0
            result_task.outputs.append(self)
            self.task.id_args_pair = ([0],{})
            #B: self._inputs = [result_task]
            #print(f"Expanding {self}#{self.short_hash(self.id)} depends on {result_task}#{self.short_hash(result_task.result_hash)}")
            self.task.input_hashes = [result_task.result_hash]
            # After expansion the composed task is just a dummy task dependent on the previoous result.
            # This works with Workflow, see how it will work with other composed actions:
            # if, reduce (for, while)

        return childs

    def set_evaluate_fn(self):
        """
        Composed tasks use evaluate to finish expansion.
        """
        #TODO: move to calling point: assert len(self.inputs) == 1
        def ff(*args):
            return args[0]
        #self.task.evaluate_fn = lambda *args: args[0]
        self.task.evaluate_fn = ff

