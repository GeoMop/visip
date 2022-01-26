"""
Implementation of meta actions other then Workflow.

We need syntax for inline workflow definitions.
Like Lambda(x=a, y=b, x[0] + y[1])


TODO:
1. Try to implement partial as it provides most of the needed functionality with
the simplest API for the implementation as it is a regular function call in Python.

2. Test recursion.

2. We can introduce sort of free parameter placeholder and then define the lambda like:

a = Slot('X') + 1
b = Slot('Y')
f = Lambda(foo, a , b , 3)

So that is better then partial as you can specify free positional arguments.
However this way the Signature of the resulting function is not clear with that `+ 1`.
Other possibility is:

a = Slot('X') + 5
b = a + Slot('Y')
f = Lambda(b, alpha='Y', beta='X')

equivalent to:
def f(alpha, beta):
    a = beta + 5
    b = a + alpha
    return b

So that Lambda collects all free slots and prescribes the signature of the resulting function.

Try also if we can manage to define new workflow inside other workflow as that is more natural way
how to define a more complex closure funcitons.



"""
from . import base
from . import exceptions
from ..action.constructor import Value
from ..dev.parameters import Parameters, ActionParameter
from . import dtype
from ..code.dummy import DummyAction, Dummy, DummyWorkflow
from ..dev import tools
from .action_instance import ActionCall, ActionInputStatus
from ..action.constructor import Pass
from typing import *


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
        if isinstance(action, (DummyAction, DummyWorkflow)):
            action = action._action_value
        elif isinstance(action, Dummy):
            action = action._value
        if isinstance(action, base._ActionBase):
            pass
        elif isinstance(action, dtype.valid_data_types):
            action = Value(action)
        else:
            raise exceptions.ExcInvalidCall(action)

        return action


"""
Partial TODO:
- DynamicCall is special case of Closure, with no remebered arguments
- Closure needs possibly special support in Scheduler as it causes creation of new 
  task connections at the call side of the closure. 
- Alternatively the meta actions may create a back reference in the previous tasks providing
  the actions and the closure could expand only if such references are obtained, not clear if we have all of them.
- Should be the case that the closure have always actions consuming its value action. 
- we can see the task DAG in hierarchical way:
  DAG of composite tasks
  DAG of big tasks
  DAG of all tasks
- The scheduler should 
  1. plan expansion of composite tasks
  2. plan big tasks to resources
  3. associate and possibly duplicate small tasks



2. Not clear how current expansion make actual task dependent on its childs.
4. Implement Partial expanding to preliminary evaluation returning the closure complex action containing the captured input tasks X.
   Partial inputs needs not to be finished at the expansion. 
5. Implement the closure complex action:
   - have dynamically determined parameters Y
   - expand to the task of closure action conected to both X and Y tasks  
"""

PartialReturnType = dtype.TypeVar('PartialReturnType')
class _Closure(MetaAction):
    """
    Action of the ClosureTask.
    Captures an action and its partially substituted arguments.
    Expands after DynamicCall which provides remaining arguments.
    TODO: Suppoert of typechecking, otherwise an error is catched at the task binding creation
    during expansion to the final Atomic task.
    TODO: Make DynamicCall special case of _Closure.
    """
    def __init__(self, action, args, kwargs):
        super().__init__("PartialClosure")
        self._action : base._ActionBase = action
        self._args : List['_TaskBase'] = args
        self._kwargs : Dict[str, '_TaskBase'] = kwargs
        # TODO: get callable type and check given arguments against signature
        # TODO: how to consistently reports errors at this stage

    def expand(self, task: '_ClosureTask', task_creator):
        # Always expand create the task with merged inputs.
        # TODO: merge new inputs to partial_args
        # TODO: How to match inputs to unbinded args.

        args = [*self._args, *task.inputs]
        self._kwargs.update(task._kw_inputs)



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







class _Empty:
    pass
empty = _Empty()
# Singleton value marking empty arguments of the Lazy action

class _Lazy(MetaAction):
    """
    Binds arguments but do not call the action, just return resulting
    action remaining parameters.
    """
    def __init__(self):
        """
        """
        super().__init__("lazy")
        ReturnType = dtype.TypeVar('ReturnType')
        params = [ActionParameter("action", dtype.Callable[...,ReturnType]),
                  ActionParameter("args", dtype.Any, kind=ActionParameter.VAR_POSITIONAL),
                  ActionParameter("kwargs", dtype.Any, kind=ActionParameter.VAR_KEYWORD),
                  ]
        self._parameters = Parameters(params, ReturnType)


    def expand(self, task: 'task.Composed', task_creator):
        """
        Expands to the ClosureTask, holding the action as instance of _Closure.
        The _ClosureTaks has reduced number or possibly no inputs (i.e. closure)
        TODO: When making Action call it probably wraps Empty values into Value actions.
        Need to check and extract them here.
        """
        # No need to wait for finised tasks, quite contrarly even action may be yet unfinished as it could be
        # result of other Closure.

        assert len(task.inputs) == self._parameters.size()
        if task.inputs[0].is_finished():
            # Create the closure and mark the Partial task finished
            # independently on the status of the enclosed intputs.
            # ac = ActionCall(self.dynamic_action(task.inputs[0]), "_closure_")
            # args = [ActionCall.create(constructor.Value(TaskValue(value))) for value in ]
            # ac.set_inputs(args, {})
            action = self.dynamic_action(task.inputs[0])
            closure = _Closure(action, task.inputs[1], task.inputs[2])
            task.finish(closure, task.lazy_hash())  # ?? May not work.

            return {'__result__': task_creator('__result__', Pass(), [task])}
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
        """
        super().__init__("DynamicCall")

        ReturnType = dtype.TypeVar('ReturnType')
        params = [ActionParameter(name="function", p_type=dtype.Callable[..., ReturnType]),
                  ActionParameter(name="args", p_type=dtype.Any, kind=ActionParameter.VAR_POSITIONAL),
                  ActionParameter(name="kwargs", p_type=dtype.Any, kind=ActionParameter.VAR_KEYWORD)]
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
            task = task_creator(task_binding)
            return {'__result__': task}
        else:
            return None



class _If(MetaAction):
    """
    How to inform scheduler, that evaluaation of the condition hve higher priority
    then the true and false inputs?
    """
    def __init__(self):
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
            return {'__result__': task_creator(task_binding)}

        else:
            return None


class While(MetaAction):
    def __init__(self):
        pass

