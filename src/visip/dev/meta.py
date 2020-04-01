"""
Implementation of meta actions other then Workflow.

We need syntax for inline workflow definitions.

Like Lambda(x=a, y=b, x[0] + y[1])

result = If(cond, true_res, false_res)
# possibly detect expressions as minimum independent chains

result = If(cond, true_wf, false_wf)(input)

While(body_


"""
from . import base
from . import exceptions
from ..dev.parameters import Parameters, ActionParameter
from . import dtype
from ..code import wrap

class MetaAction(base._ActionBase):
    """
    Common ancestor of the meta actions.
    """
    def __init__(self, name):
        super().__init__(name)

        self.task_type = base.TaskType.Composed
        # Task type determines how the actions are converted to the tasks.
        # Composed tasks are expanded.

    def expand(self, inputs: dtype.List['Task'], task_creator):
        """
        Expansion of the composed task with given data inputs (possibly None if not evaluated yet).
        :param inputs: List[Task]
        :param task_creator: Dependency injection method for creating tasks from the actions:
            task_creator(instance_name:str, action:base._ActionBase, input_tasks:List[Task])
        :return:
            None if can not be expanded yet.
            Dict of named child tasks:
                task_name ->  a_created_task
            Must contain a '__result__' child task, that will be used to connect tasks dependent on the expanded task.
        TODO: return not a dict but just a list of tasks, and construct dict by extracting the task.child_id as a key.
        """
        assert False, "Missing definition."


class Partial(MetaAction):
    pass

class DynamicCall(MetaAction):
    def __init__(self):
        """
        Constructed by the Dummy.__call__.
        TODO: support kwargs in visip, necessary for perferct forwarding
        """
        super().__init__("DynamicCall")
        self._parameters = Parameters()
        ReturnType = dtype.TypeVar('ReturnType')
        self._parameters.append(
            ActionParameter(name="function", type=dtype.Callable[..., ReturnType]))
        self._parameters.append(
            ActionParameter(name=None, type=dtype.Any, default=ActionParameter.no_default))
        # TODO: Support for kwargs forwarding.
        # TODO: Match 'function' parameters and given arguments.
        #self._parameters.append(
        #    ActionParameter(name=None, type=typing.Any, default=ActionParameter.no_default))
        self._output_type = ReturnType

    def expand(self, inputs, task_creator):

        if inputs[0].is_finished():
            dynamic_action = inputs[0].result
            assert isinstance(dynamic_action, wrap.ActionWrapper)
            dynamic_action = dynamic_action.action
            if not isinstance(dynamic_action, base._ActionBase):
                raise exceptions.ExcInvalidCall(dynamic_action)
            return {'__result__': task_creator('__result__', dynamic_action, inputs[1:])}
        else:
            return None


class If(MetaAction):
    """
    This possibly should not be meta action, since scheduler should
    How to inform scheduler, that evaluaation of the condition hve higher priority
    then the true and false inputs?
    """
    pass

class While(MetaAction):
    def __init__(self):
        pass

