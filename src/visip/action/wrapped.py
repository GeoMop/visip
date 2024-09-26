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
from .std import Append, Len

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

import math
ceil = action_def(math.ceil)
floor = action_def(math.floor)


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




@workflow
def _GenBody(results, last, condition, iterate, map_fn):
    new_results = Append(results, map_fn(last))
    return _Generate(new_results, iterate(last), condition, iterate, map_fn)

@workflow
def _Generate(results, last, condition, iterate, map_fn):
    body = lazy(_GenBody, results, last, condition, iterate, map_fn)
    return If(condition(last), body, results)

@workflow
#def Generate(init: T_Generate, condition: wf.Fn(wf.Bool, (T_Generate,), {}), iterate: wf.Fn(T_Generate, (T_Generate,))):
def Generate(init, condition, iterate, map_fn):
    """
    Similar to While but return a list of all iterations.
    """
    return _Generate([], init, condition, iterate, map_fn)



@workflow
def _MapBody(out_items, fn, items):
    last = items[Len(out_items)]
    return _map(Append(out_items, fn(last)), items, fn)

@workflow
def _map(out_list, items, fn):
    next = lazy(_MapBody, out_list, fn, items)
    return If(Len(out_list) < Len(items), next, out_list)

#TMapIn = TypeVar()
#TMapOut = TypeVar()
@workflow
#def Map(fn: wf.Fn(TMapOut, (TMapIn,)), items: wf.List(TMapIn)) -> wf.List(TMapOut):
def Map(fn, items):
        return _map([], items, fn)
