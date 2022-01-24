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
from ..dev.action_instance import ActionCall
from . import dtype
from ..code.dummy import DummyAction
from ..dev import tools
from .action_instance import ActionCall, ActionInputStatus

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
        Expansion of the composed task. In order to no break input references of other tasks
        the current task is collapsed to an effective Pass action connected to the expansion __result__ task.

        The composed task can be expanded to any new tasks including the new composed task for the same action.
        However the expansion is a recursion and may be difficult bad to visualize and debug.

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
        """
        Extract a dynamic action from the result of a meta action.
        :param input_task:
        :return:
        """
        action = input_task.result
        if isinstance(action, DummyAction):
            action = action._action_value
        if not isinstance(action, base._ActionBase):
            raise exceptions.ExcInvalidCall(action)
        return action


"""
Partial TODO:

2. Not clear how current expansion make actual task dependent on its childs.
4. Implement Partial expanding to preliminary evaluation returning the closure complex action containing the captured input tasks X.
5. Implement the closure complex action:
   - have dynamically determined parameters Y
   - expand to the task of closure action conected to both X and Y tasks  
"""

PartialReturnType = dtype.TypeVar('PartialReturnType')
class _PartialClosure(MetaAction):

    def __init__(self, function, inputs, kw_inputs):
        super().__init__("PartialClosure")
        self._function = function
        self._inputs = inputs
        self._kw_inputs = kw_inputs
        #self.
        # Use acion call to consistently construct Parameters
        # TODO: not clear how to use expansion to validate dynamic action calls
        # and how to consistently report wrong connections
        ac = ActionCall(function, '_closure_')
        ac.set_inputs([self.task_value(ii) for ii in inputs],
                      {k: self.task_value(ii) for k, ii in kw_inputs.items()}
                      )
        # TODO: filter paratemters set Paratemers
        self._parameters = Parameters()
        for arg in ac.arguments:
            arg.status in  {ac.ActionInputStatus.default, ac.ActionInputStatus.missing}
            self._parameters.append(arg.parameter)
        # Keep only unbinded parameters.
        # 1. Get all parameters of the 'function'.
        # 2. Bind 'args' to the positional parameters from the beginning.
        # 3. Bind 'kwargs' to named arguments.
        # 4. anonymous positional and named gathered
        #
        # To not duplicate arguments processing:
        # 1.Create an ActionCall in Partial with just some inputs set we must use a BindTask data
        # to wrap input tasks to the Value actions.
        # 2. Pass ActionCall to the Closure, extract unset parameters.
        # 3. Finish ActionCall an expansion.


        # ?? Probably no need to specify parameters as the closure input substitution works only with tasks.
        # But we can make a check in the expansion step.


        # This allows DynamicCall to work

    def expand(self, task, task_creator):
        # Always expand create the task with merged inputs.
        # TODO: merge new inputs to partial_args
        # TODO: How to match inputs to unbinded args.

        ac = ActionCall(self.dynamic_action(task.inputs[0]), "_closure_")
        self._inputs.expand(task.inputs)
        self._kw_inputs.update(task._kw_inputs)
        ac = ActionCall(self._function, '_closure_')
        ac.set_inputs([self.task_value(ii) for ii in self._inputs],
                      {k: self.task_value(ii) for k, ii in self._kw_inputs.items()}
                      )
        arg_tasks = [arg.value.input for arg in ac.arguments]
        # TODO: How the args and kw_args will work in action call, here and in workflow expansion
        # a bit complicated. 
        task = task_creator('__result__', self._function, arg_tasks)
        return [task]

class Partial(MetaAction):
    def __init__(self):
        """
        Partial argument binding, creates a closure.
        TODO: support kwargs in visip, necessary for perfect forwarding
        """
        super().__init__("Partial")
        self._parameters = Parameters()
        PartialReturnType = dtype.TypeVar('PartialReturnType')

        self._parameters.append(
            ActionParameter(name="function", type=dtype.Callable[..., PartialReturnType]))
        self._parameters.append(
            ActionParameter(name=None, type=dtype.Any, default=ActionParameter.no_default))
        # self._parameters.append(
        #     ActionParameter(name=None, type=dtype.Any, default=ActionParameter.no_default))
        # TODO: Support for kwargs forwarding.
        # TODO: Match 'function' parameters and given arguments.
        #self._parameters.append(
        #    ActionParameter(name=None, type=typing.Any, default=ActionParameter.no_default))
        self._output_type = dtype.Callable[..., PartialReturnType]


    def expand(self, task, task_creator):
        # TODO: need either support for partial substitution in Action Wrapper or must do it here.
        # Parameters of the resulting action must be determined dynamicaly.
        # TODO: Here is significant problem with parameter types since all are
        # optional
        assert len(task.inputs) == self._parameters.size()
        if task.inputs[0].is_finished():
            # Create the closure and mark the Partial task finished
            # independently on the status of the enclosed intputs.
            #ac = ActionCall(self.dynamic_action(task.inputs[0]), "_closure_")
            #args = [ActionCall.create(constructor.Value(TaskValue(value))) for value in ]
            #ac.set_inputs(args, {})
            action = self.dynamic_action(task.inputs[0])
            closure = _PartialClosure(action, task.inputs[1], task.inputs[2])
            task.finish(closure, task.lazy_hash()) # ?? May not work.

            return [task_creator('__result__', constructor.Pass(), [task])]
        else:
            return None

#

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
        params =[]
        ReturnType = dtype.TypeVar('ReturnType')
        params.append(
            ActionParameter(name="function", p_type=dtype.Callable[..., ReturnType]))
        params.append(
            ActionParameter(name="args", p_type=dtype.Any, kind=ActionParameter.VAR_POSITIONAL))
        params.append(
            ActionParameter(name="kwargs", p_type=dtype.Any, kind=ActionParameter.VAR_KEYWORD))
        self._parameters = Parameters(params, ReturnType)
        # TODO: Support for kwargs forwarding.
        # TODO: Match 'function' parameters and given arguments.
        #self._parameters.append(
        #    ActionParameter(name=None, type=typing.Any, default=ActionParameter.no_default))


    def expand(self, task, task_creator):
        if task.inputs[0].is_finished():
            args, kwargs = tools.compose_arguments(task.id_args_pair, task.inputs)
            action = self.dynamic_action(args[0])
            task_binding = tools.TaskBinding('__result__', action, task.id_args_pair, task.inputs[1:])
            return [task_creator(task_binding)]
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
        #super().__init__("DynamicCall")
        super().__init__("If") # Dynamic Cal
        params = []
        ReturnType = dtype.TypeVar('ReturnType')
        params.append(
            ActionParameter(name="condition", p_type=bool))
        params.append(
            ActionParameter(name="true_body", p_type=dtype.Callable[..., ReturnType]))
        params.append(
            ActionParameter(name="false_body", p_type=dtype.Callable[..., ReturnType]))
        self._parameters = Parameters(params, ReturnType)

    def expand(self, task, task_creator):
        if all([ i_task.is_finished() for i_task in task.inputs]):
            condition = task.inputs[0].result
            if condition:
                action = self.dynamic_action(task.inputs[1])
            else:
                action = self.dynamic_action(task.inputs[2])
            task_binding = tools.TaskBinding('__result__', action, ([], {}), [])
            return [task_creator(task_binding)]

        else:
            return None


class While(MetaAction):
    def __init__(self):
        pass

