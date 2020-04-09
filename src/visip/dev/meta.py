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

    Not a good definition of meta action:
    A meta action is an action producing other action or an action accepting other action as a parameter.
    As the meta actions are expanded out of the scheduler we are able to do all expansions locally.
    (Can be problematic in future, e.g. evaluation of a complex workflow inside a MC.

    ... producing an action can not be always implemented as an expansion. We need a separate mechanism to process
    actions operating with actions locally or we have to simplify the core ( possibly in truly functional manner).
    """
    def __init__(self, name):
        super().__init__(name)

        self.task_type = base.TaskType.Composed
        # Task type determines how the actions are converted to the tasks.
        # Composed tasks are expanded.

    def expand(self, task: 'Task', task_creator):
        """
        Expansion of the composed task with given data inputs (possibly None if not evaluated yet).
        :param task: The complex task to expand.
        :param task_creator: Dependency injection method for creating tasks from the actions:
            task_creator(instance_name:str, action:base._ActionBase, input_tasks:List[Task])
        :return:
            None if can not be expanded yet.

            List of named child tasks.
            Must contain a '__result__' child task, that will be used to connect tasks dependent on the expanded task.
        """
        assert False, "Missing definition."

    def dynamic_action(self, input_task):
        action = input_task.result
        if isinstance(action, wrap.ActionWrapper):
            action = action.action
        if not isinstance(action, base._ActionBase):
            raise exceptions.ExcInvalidCall(action)
        return action


"""
Partial TODO:

2. modify expand API in order to allow modification of the task itself.
   In particular we want to allow preliminary task evaluation even if the inputs are not completed
   Not clear how current expansion make actual task dependent on its childs.
3. Review if the dependency of If and Call after expansion is OK. 
4. Implement Partial expanding to preliminary evaluation returning the closure complex action containing the captured input tasks X.
5. Implement the closure complex action:
   - have dynamically determined parameters Y
   - expand to the task of closure action conected to both X and Y tasks  
"""


# class _PartialClosure(base._ActionBase):
#
#     def __init__(self, function, partial_args):
#         super().__init__()
#         self._function = function
#         self._args = args
#
#     def evaluate(self, inputs):
#         #TODO: merge new inputs to partial_args



#
# class Partial(MetaAction):
#     def __init__(self):
#         """
#         Constructed by the Dummy.__call__.
#         TODO: support kwargs in visip, necessary for perfect forwarding
#         """
#         super().__init__("DynamicCall")
#         self._parameters = Parameters()
#         ReturnType = dtype.TypeVar('ReturnType')
#         self._parameters.append(
#             ActionParameter(name="function", type=dtype.Callable[..., ReturnType]))
#         self._parameters.append(
#             ActionParameter(name=None, type=dtype.Any, default=ActionParameter.no_default))
#         # TODO: Support for kwargs forwarding.
#         # TODO: Match 'function' parameters and given arguments.
#         #self._parameters.append(
#         #    ActionParameter(name=None, type=typing.Any, default=ActionParameter.no_default))
#         self._output_type = ReturnType
#
#
#     def expand(self, inputs, task_creator):
#         # TODO: need either support for partial substitution in Action Wrapper or must do it here.
#         # Parameters of the resulting action must be determined dynamicaly.
#         # TODO: Here is significant problem with parameter types since all are
#         # optional
#         if inputs[0].is_finished():
#
#             # Create a workflow for the partial.
#             closure = _PartialClosure(dynamic_action, inputs[1:])
#
#             return {'__result__': task_creator('__result__', dynamic_action, inputs[1:])}
#         else:
#             return None
#
# PartialReturnType = dtype.TypeVar('PartialReturnType')
# @decorators.action_def
# def partial(function:dtype.Callable[..., PartialReturnType], *args:dtype.List[dtype.Any]) -> dtype.Callable[..., PartialReturnType]:
#     # TODO: kwargs support
#     assert isinstance(function, base._ActionBase)
#     partial_fn_evaluate = functools.partial(function.evaluate, *args)
#     partial_fn_evaluate.__name__ = "partial_" + function.name
#     #partial_fn_evaluate.__annotations__
#     return decorators.action_def(_PartialResult(function, *args))
#
#
# class _PartialResult(base._ActionBase):
#     def __init__(self, function, *args):
#         super().__init__(action_name="partial_" + function.name)
#         self._function = function
#         self._args = args
#         all_parameters = function._parameters
#         self._parameters = parameters.Parameters()
#         self._parameters
#
#     def evaluate(self, inputs):

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

    def expand(self, task, task_creator):
        if task.inputs[0].is_finished():
            return [task_creator('__result__',
                    self.dynamic_action(task.inputs[0]), task.inputs[1:])]
        else:
            return None


class _If(MetaAction):
    """
    How to inform scheduler, that evaluaation of the condition hve higher priority
    then the true and false inputs?
    """
    def __init__(self):
        """
        Constructed by the Dummy.__call__.
        TODO: support kwargs in visip, necessary for perferct forwarding
        """
        super().__init__("DynamicCall")
        self._parameters = Parameters()
        ReturnType = dtype.TypeVar('ReturnType')
        self._parameters.append(
            ActionParameter(name="condition", type=bool))
        self._parameters.append(
            ActionParameter(name="true_body", type=dtype.Callable[..., ReturnType]))
        self._parameters.append(
            ActionParameter(name="false_body", type=dtype.Callable[..., ReturnType]))
        self._output_type = ReturnType

    def expand(self, task, task_creator):
        if all([ i_task.is_finished() for i_task in task.inputs]):
            condition = task.inputs[0].result
            if condition:
                return [task_creator('__result__', self.dynamic_action(task.inputs[1]), [])]
            else:
                return [task_creator('__result__', self.dynamic_action(task.inputs[2]), [])]
        else:
            return None


class While(MetaAction):
    def __init__(self):
        pass

