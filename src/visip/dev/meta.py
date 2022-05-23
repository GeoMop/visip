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
from typing import *

from . import base, data
from . import exceptions
from ..action.constructor import Value
from ..dev.parameters import Parameters, ActionParameter
from . import dtype
from ..code.dummy import DummyAction, Dummy, DummyWorkflow
from ..dev import tools
from ..action.constructor import Pass



class MetaAction(base.ActionBase):
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
        self.action_kind = base.ActionKind.Meta

        self.task_type = base.TaskType.Composed
        # Task type determines how the actions are converted to the tasks.
        # Composed tasks are expanded.

    def expand(self, task: 'Task', task_creator, cache):
        """
        Expansion of the composed task. In order to no break input references of other tasks
        the current task is collapsed to an effective Pass action connected to the expansion __result__ task.

        The composed task can be expanded to any new tasks including the new composed task for the same action.
        However the expansion is a recursion and may be difficult bad to visualize and debug.

        :param task: The complex task to expand.
        :param task_creator: Dependency injection method for creating tasks from the actions:
            task_creator(instance_name:str, action:base._ActionBase, input_tasks:List[Task])
        :param cache: Result cache instance
        :return:
            None if can not be expanded yet.

            List of named child tasks.
            Must contain a '__result__' child task, that will be used to connect tasks dependent on the expanded task.
        """
        assert False, "Missing definition."

    def dynamic_action(self, input_result):
        """
        Extract a dynamic action from the result of a meta action.
        :param input_result:
        :return:
        """
        action = input_result
        if isinstance(action, (DummyAction, DummyWorkflow)):
            action = action._action_value
        elif isinstance(action, Dummy):
            action = action._value
        if isinstance(action, dtype._ActionBase):
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
        super().__init__("Closure")
        self.task_type = base.TaskType.Composed
        self._action : dtype._ActionBase = action
        self._args : List['_TaskBase'] = args
        self._kwargs : Dict[str, '_TaskBase'] = kwargs
        # TODO: get callable type and check given arguments against signature
        # TODO: how to consistently reports errors at this stage

    def action_hash(self):
        # TODO: test that the hash is the same as the direct call of the action.
        task_hash = self._action.action_hash()
        for task in self._args:
            task_hash = data.hash(task.result_hash, previous=task_hash)
        for task in self._kwargs.values():
            task_hash = data.hash(task.result_hash, previous=task_hash)
        return task_hash

    def __repr__(self):
        return f"Closure({self._action}; {[task.short_hash(task.id) for task in self._args]})"

    def expand(self, task: '_ClosureTask', task_creator, cache):
        # Always expand create the task with merged inputs.
        # TODO: merge new inputs to partial_args
        # TODO: How to match inputs to unbinded args.
        # unbinded args marked as Value task with empty argument
        assert task.action is self
        def is_empty(task_in):
            try:
                return isinstance(task_in.action, Value) and task_in.action.value is dtype.empty
            except AttributeError:
                raise AttributeError(f"{task_in.action}")


        new_args, new_kwargs = tools.compose_arguments(task.id_args_pair, task.inputs)
        it_new_args = iter(new_args)
        args = []
        for t in self._args:
            if is_empty(t):
                try:
                    add = next(it_new_args)
                except StopIteration:
                    raise exceptions.ExcArgumentBindError(f"Missing positional argument, in closure of {self._action}")
            else:
                add = t
            args.append(add)
        args.extend(it_new_args)
        kwargs = self._kwargs
        kwargs.update(new_kwargs)
        id_args_pair, inputs = tools.decompose_arguments( (args, kwargs) )

        # TODO: Abstart ActionCall.bind and use it here and in DynamicCall to check bindindg errors
        #

        task_binding = tools.TaskBinding('__result__', self._action, id_args_pair, inputs)
        task = task_creator(task_binding)
        return {'__result__': task}


class _Lazy(MetaAction):
    """
    Binds arguments but do not call the action, just return resulting
    action remaining parameters.
    """
    def __init__(self):
        """
        """
        super().__init__("lazy")
        #ReturnType = dtype.TypeVar(origin_type=None, name='ReturnType')
        ReturnType = TypeVar('ReturnType')

        params = [ActionParameter("action", Callable[..., ReturnType]),
                  ActionParameter("args", dtype.Any, kind=ActionParameter.VAR_POSITIONAL),
                  ActionParameter("kwargs", dtype.Any, kind=ActionParameter.VAR_KEYWORD),
                  ]
        self._parameters = Parameters(params, ReturnType)


    def expand(self, task: 'task.Composed', task_creator, cache):
        """
        Expands to the ClosureTask, holding the action as instance of _Closure.
        The _ClosureTaks has reduced number or possibly no inputs (i.e. closure)
        TODO: When making Action call it probably wraps Empty values into Value actions.
        Need to check and extract them here.
        """
        # No need to wait for finised tasks, quite contrarly even action may be yet unfinished as it could be
        # result of other Closure.



        if cache.is_finished(task.inputs[0].result_hash):
            # TODO:
            # - wrap actions into Closure action in order to prevent storing actions into DB
            # - check task is the ClosureTask
            # - get task._result.parameters check against connected inputs
            # - Workflow typechecking should be able to derive types of callables, but need a help
            #   as the type propagation through Lazy is complicated

            # Create the closure and Lazy task finished
            # independently on the status of the enclosed intputs.
            # ac = ActionCall(self.dynamic_action(task.inputs[0]), "_closure_")
            # args = [ActionCall.create(constructor.Value(TaskValue(value))) for value in ]
            # ac.set_inputs(args, {})
            args, kwargs = tools.compose_arguments(task.id_args_pair, task.inputs)
            action = self.dynamic_action(cache.value(args[0].result_hash))


            closure = _Closure(action, args[1:], kwargs)
            cache.insert(task.result_hash, closure)
            # empty task to proceed
            task_binding = tools.TaskBinding('__result__', Pass(), ([0], {}), [task])
            pass_task = task_creator(task_binding)

            return {'__result__': pass_task}
        else:
            return None


#PartialReturnType = dtype.TypeVar(name='PartialReturnType')

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

        ReturnType = TypeVar('ReturnType')
        params = [ActionParameter(name="function", p_type=Callable[..., ReturnType]),
                  ActionParameter(name="args", p_type=dtype.Any, kind=ActionParameter.VAR_POSITIONAL),
                  ActionParameter(name="kwargs", p_type=dtype.Any, kind=ActionParameter.VAR_KEYWORD)]
        self._parameters = Parameters(params, ReturnType)
        # TODO: Support for kwargs forwarding.
        # TODO: Match 'function' parameters and given arguments.
        #self._parameters.append(
        #    ActionParameter(name=None, type=typing.Any, default=ActionParameter.no_default))


    def expand(self, task, task_creator, cache):
        if cache.is_finished(task.inputs[0].result_hash):
            #args, kwargs = tools.compose_arguments(task.id_args_pair, task.inputs)
            action = self.dynamic_action(cache.value(task.inputs[0].result_hash))
            id_args, id_kwargs = task.task.id_args_pair
            id_args = [i - 1 for i in id_args[1:]]
            id_kwargs = {k: (i-1) for k, i in id_kwargs.items()}
            task_binding = tools.TaskBinding('__result__', action, (id_args, id_kwargs), task.inputs[1:])
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
        super().__init__("If")
        params = []
        ReturnType = TypeVar('ReturnType')
        params.append(
            ActionParameter(name="condition", p_type=dtype.Bool))
        params.append(
            ActionParameter(name="true_body", p_type=Callable[..., ReturnType]))
        params.append(
            ActionParameter(name="false_body", p_type=Callable[..., ReturnType]))
        self._parameters = Parameters(params, ReturnType)

    def expand(self, task, task_creator, cache):
        if all([cache.is_finished(i_task.result_hash) for i_task in task.inputs]):
            condition = cache.value(task.inputs[0].result_hash)
            if condition:
                action = self.dynamic_action(cache.value(task.inputs[1].result_hash))
            else:
                action = self.dynamic_action(cache.value(task.inputs[2].result_hash))
            task_binding = tools.TaskBinding('__result__', action, ([], {}), [])
            return {'__result__': task_creator(task_binding)}

        else:
            return None







"""
@vs.workflow
def _true_while_body(condition, body, previous):
    return While(condition, body, body(previous)

@vs.workflow
def While(condition, body, previous):
    cond = condition(previous)    
    true_body = vs.lazy(_true_while_body, condition, body, previous)
    false_body = vs.lazy(Pass, previous) 
    return vs.If(cond, true_body, false_body)

# Usage

def fibonacci(prev):
    i, a, b = prev
    return i - 1, b, a + b
    
fib = While(vs.Slot[0][0] > 0, fibonacci, (i, 1, 1) ) 
return fib[1]
"""


"""
@vs.workflow
def While(body, previous):
    next = body(previous)    
    true_body = vs.lazy(While, body, next)
    false_body = vs.lazy(Pass, previous) 
    return vs.If(is_none(next), true_body, false_body)

# Usage

def fib_body(prev)
    
    
def fibonacci(prev):
    i, a, b = prev    
    false_body = vs.lazy(Pass, None)
    return If(i > 0, fib_true, None) 
    
fib = While(fibonacci, (i, 1, 1) ) 
return fib[1]
"""


"""
@vs.workflow
def _true_generate_body(body, previous):
    return _GenerateLoop(body, body(previous)

    
@vs.workflow
def _GenerateLoop(condition, body, previous):
    list, last = previous
    cond = condition(last)
    new_list = append(list, last)
    true_body = vs.lazy(_GenerateLoop, body, (new_list, body(previous)))
    false_body = vs.lazy(Pass, previous) 
    return vs.If(cond, true_body, false_body)
    return 
    
    
def Generate(condition, body, init):
    

"""