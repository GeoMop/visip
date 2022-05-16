"""
This module provides wrapped default actions defined in the 'action' directory.

Problematic are actions generated from special constructs by the 'code' package:
- convertors/constructors, operators, ...
- actions that are already wrapped are just imported
"""
from . import constructor
from ..code.decorators import public_action, action_def, workflow
from ..dev import meta
from ..dev import dtype

dict = public_action(constructor.A_dict())
list = public_action(constructor.A_list())
tuple = public_action(constructor.A_tuple())
Pass = public_action(constructor.Pass())

If = public_action(meta._If())
"""
Meta action for the blocking condition.

Syntax:
    If(condition, true_body, false_body)
    
The expansion og the condition is postponed until the condition is evaluated, then 
the If metaaction is expanded to the true_body action or to the false_body action so that only one of them is
actually evaluated. The true_body and false_body actions must be actions taking no parameters. Possible parameters 
must be wrapped into a closure action, e.g.

    If(x>0, lazy(my_action, x), lazy(other_action, x))

see 'lazy' meta action for more details.
"""
lazy = public_action(meta._Lazy())
"""
Meta action for (partial)  argument binding. 

Syntax:
    lazy(action, *args, **kwargs)
    
    First argument is an action then the positional arguments (*args) and the 
    keyword arguments (**kwrags) of the 'action' follows. You can omit a positional argument using 
    a special value 'empty', the keyword arguments are all optional. The result is an action with 
    parameters corresponding to omitted arguments. Example:
    
    @action_def
    def foo(a:int, *argv:float, b:str, **kwargs:Any) -> int:
           return a
    
    @workflow
    def work():
        fa = lazy(foo, empty, 1.1, 2.2, b="a", c="any") # fa(a, *argv, **kwargs) -> int
        value_a = fa(1)
        fb = lazy(foo, value_a) # fb(*argv, b, **kwargs) -> int
        value_b = fb(b="a")
        return value_b        
    
"""
empty = dtype.empty
"""
Specific value used to mark unbound positional parameters in the 'lazy' meta action. 
"""
abs = action_def(abs)
round = action_def(round)
pow = action_def(pow)
divmod = action_def(divmod)

@workflow
def While(body, previous):
    next = body(previous)
    true_body = lazy(While, body, next)
    false_body = lazy(Pass, previous)
    return If(next == None, false_body, true_body)

@workflow
def _while_body(init, condition, iterate):
    return WhileCond(iterate(init), condition, iterate)

@workflow
def WhileCond(init, condition, iterate):
    continue_body = lazy(_while_body, init, condition, iterate)
    return If(condition(init), continue_body, init)


@action_def
def _append(a_list, fn, item):
    return a_list.append(fn(item))

@workflow
def _Recursion(_recursion, items, fn, last, a):
    return _recursion(_append(items, fn(last)), a, fn)

@workflow
def _GenBody(results, condition, iterate):
    last = results[-1]
    continue_body = lazy(_Recursion, _GenBody, results, iterate, last, condition, iterate)
    stop_body = lazy(results)
    return If(condition(results[-1]), continue_body, stop_body)

@workflow
#def Generate(init: T_Generate, condition: wf.Fn(wf.Bool, (T_Generate,), {}), iterate: wf.Fn(T_Generate, (T_Generate,))):
def Generate(init, condition, iterate):
    """
    Similar to While but return a list of all iterations.
    """
    true_body = lazy(_GenBody, [init], condition, iterate)
    return If(condition(init), true_body, [])

@workflow
def _map(out_list, items, fn):
    next = lazy(_Recursion, _map, out_list, fn, items[Len(out_list)], items)
    return If(Len(out_list) < Len(items), next, out_list)

#TMapIn = TypeVar()
#TMapOut = TypeVar()
@workflow
#def Map(fn: wf.Fn(TMapOut, (TMapIn,)), items: wf.List(TMapIn)) -> wf.List(TMapOut):
def Map(fn, items):
        return _map([], items, fn)
