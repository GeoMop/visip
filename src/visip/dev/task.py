import enum
from typing import Optional, Union, List

from . import data
from ..action.constructor import Pass
from . import base



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
    def __init__(self, action: 'dev._ActionBase', inputs: List['Atomic'] = []):
        self.action = action
        # Action (like function definition) of the task (like function call).
        self.inputs = inputs
        # Input tasks for the action's arguments.
        for input in inputs:
            assert isinstance(input, _TaskBase)
            input.outputs.append(self)
        self.outputs: List['Atomic'] = []
        # List of tasks dependent on the result. (Try to not use and eliminate.)
        result: Optional[data.DataType] = None
        # Result of the task.
        self.id: int = 0
        # Task is identified by the hash of the hash of its parent task and its name within the parent.
        self.parent: Optional['Composed'] = None
        # parent task, filled during expand
        self.status = Status.none
        # Status of the task, possibly need not to be stored explicitly.
        self._result = None
        # The task result.
        self.resource_id = None

        self.start_time = -1
        self.end_time = -1
        self.eval_time = 0

    @property
    def priority(self):
        return 1

    @property
    def result(self):
        return self._result

    def evaluate(self):
        assert False, "Not implemented."

    def is_finished(self):
        return self.result is not None

    def is_ready(self):
        assert False, "Not implemented."


    def set_id(self, parent_task, child_id):
        self.parent = parent_task
        if parent_task is None:
            parent_hash = data.hash(None)
        else:
            parent_hash = parent_task.id
        self.id = data.hash(child_id, previous=parent_hash)

    def __lt__(self, other):
        return self.priority < other.priority

    @staticmethod
    def _create_task(parent_task, child_name, action, input_tasks):
        """
        Create task from the given action and its input tasks.
        """
        task_type = action.task_type
        if task_type == base.TaskType.Atomic:
            child = Atomic(action, input_tasks)
        elif task_type == base.TaskType.Composed:
            child = Composed(action, input_tasks)
        else:
            assert False
        child.set_id(parent_task, child_name)
        return child


class Atomic(_TaskBase):
    pass



    def is_ready(self):
        """
        Update ready status, return
        :return:
        """
        if self.status < Status.ready:
            is_ready = all([task.is_finished() for task in self.inputs])
            if is_ready:
                self.status = Status.ready
        return self.status == Status.ready

    def evaluate(self):
        assert self.is_ready()
        data_inputs = [i.result for i in self.inputs]
        self._result = self.action.evaluate(data_inputs)
        self.status = Status.finished
        assert self.result is not None


class ComposedHead(Atomic):
    """
    Auxiliary task for the inputs of the composed task. Simplifies
    expansion as we need not to change input and output links of outer tasks, just link between head and tail.
    """
    @property
    def result(self):
        return self.inputs[0].result


class Composed(Atomic):
    """
    Composed tasks are non-leaf vertices of the execution tree.
    The Evaluation class takes care of their expansion during execution according to the
    preferences assigned by the Scheduler. It also keeps a map from
    """

    def __init__(self, action: 'dev._ActionBase', inputs: List['Atomic'] = []):
        heads = [ComposedHead(Pass(), [input]) for input in inputs]
        super().__init__(action, heads)
        self.time_estimate = 0
        # estimate of the start time, used as expansion priority
        self.childs: Atomic = None
        # map child_id to the child task, filled during expand.

    def is_ready(self):
        """
        Block submission of unexpanded tasks.
        :return:
        """
        return self.is_expanded() and Atomic.is_ready(self)


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


    def create_child_task(self, name, action, inputs):
        return _TaskBase._create_task(self, name, action, inputs)

    def expand(self):
        """
        Composed task expansion.

        Connect the head tasks to the body and the 'self' (i.e. the tail task) to the result
        action instance of the body. Auxiliary tasks for the heads, result and tail
        are used in order to minimize modification of the task links.

        :return:
            None if the expansion can not be performed.
            Dictionary of child tasks (action_instance_name -> task)
            Empty dict is valid result, used to indicate end of a loop e.g. in the case of ForEach and While actions.
        """
        assert self.action.task_type == base.TaskType.Composed
        assert hasattr(self.action, 'expand')

        # Disconnect composed task heads.
        heads = self.inputs.copy()
        for head in heads:
            head.outputs = []
        # Generate and connect body tasks.
        self.childs = self.action.expand(self.inputs, self.create_child_task)
        if self.childs:
            result_task = self.childs['__result__']
            assert len(result_task.outputs) == 0
            result_task.outputs.append(self)
            self.inputs = [result_task]
            # After expansion the composed task is just a dummy task dependent on the previoous result.
            # This works with Workflow, see how it will work with other composed actions:
            # if, reduce (for, while)

        else:
            # No expansion: reconnect heads
            for head in heads:
                head.outputs = [self]
        return self.childs

    def evaluate(self):
        assert self.is_ready()
        assert len(self.inputs) == 1
        assert self.inputs[0].action.name == "_ResultAction"

        self._result = self.inputs[0].result
        self.status = Status.finished
        assert self.result is not None



