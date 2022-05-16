import pytest
import visip as wf
from visip.dev import evaluation
from visip.dev import exceptions
import pytest
# script_dir = os.path.dirname(os.path.realpath(__file__))


#######################
# Test definition of a (Python) action returning an action.
# Tests implicit usage of 'DynamicCall'

@wf.action_def
def adder(left_operand: float) -> wf.Any:
    """
    Example of an action producing action.
    :param left_operand:
    :return:
    """
    def add(right_operand: float) ->float:
        return left_operand + right_operand
    return wf.action_def(add)


@wf.analysis
def tst_adder() -> float:
    adder_val = adder(1)
    return adder_val(2)     # 'DynamicCall' involved here.



#@pytest.mark.skip
def test_action_returning_action():
    result = evaluation.run(tst_adder)
    assert result == 3


#############################
# Test IF meta action

@wf.workflow
def true_body():
    return 101

@wf.workflow
def false_body():
    return 100


@wf.workflow
def wf_condition(cond: wf.Bool) -> wf.Int:
    return wf.If(cond, true_body, false_body)


def test_if_action():
    result = evaluation.run(wf_condition, True)
    assert result == 101
    result = evaluation.run(wf_condition, False)
    assert result == 100


# simpler if
@wf.action_def
def foo(x: int) -> int:
    return x + 1

@wf.workflow
def wf_condition(cond: int) -> int:
    return wf.If(cond, foo(100), 100)

#@pytest.mark.skip
def test_if_action():
    result = evaluation.run(wf_condition, True)
    assert result == 101
    result = evaluation.run(wf_condition, False)
    assert result == 100


#######################
# Test lazy meta action.

@wf.action_def
def add(a, b):
    return a + b

@wf.workflow
def basic_lazy_wf():
    inc = wf.lazy(add, wf.empty, 1)
    return inc(2)

@wf.action_def
def lazy_action(i:int, j:float, *args, a:bool, b:str, **kwargs):
    return f"lazy_action({i} {j} {args} {a} {b} {kwargs})"

@wf.workflow
def lazy_wf():
    closure = wf.lazy(lazy_action, 100, 101, 102, a='a', b='b', d='d')
    b = closure()
    partial_1 = wf.lazy(lazy_action, wf.empty, 1, a=2, c=3)
    a1 = wf.lazy(partial_1, wf.empty, 5, b=7)
    a = a1(4)
    return (a, b)

#@pytest.mark.skip
def test_lazy():
    result = evaluation.run(basic_lazy_wf)
    assert result == 3

    #result = evaluation.run(lazy_wf, [], plot_expansion=True)

    result = evaluation.run(lazy_wf)
    assert result[0] == "lazy_action(4 1 (5,) 2 7 {'c': 3})"
    assert result[1] == "lazy_action(100 101 (102,) a b {'d': 'd'})"


@wf.workflow
def lazy_wf_err_1():
    partial = wf.lazy(lazy_action, wf.empty, 1, a=2, c=3)
    return partial(4, 5, a=6, b=7)

@pytest.mark.skip
def test_lazy_errors():
    with pytest.raises(exceptions.ExcArgumentBindError) as e:
        result = evaluation.run(lazy_wf_err_1)

#####
# test recursion

@wf.action_def
def equal(a:int, b:int) -> bool:
    return a == b

@wf.action_def
def mult(a, b):
    return a * b

@wf.action_def
def sub(a, b):
    return a - b

@wf.action_def
def make_fac1(i: int) -> wf.Any:
    """
    Example of an action producing action.
    :param left_operand:
    :return:
    """
    def add() -> int:
        return mult(i, fac1(sub(i, 1)))
    return wf.workflow(add)

@wf.workflow
def fac1(i:int):
    zero = equal(i, 0)
    fac_action = make_fac1(i)
    return wf.If(zero, 1, fac_action)

#@pytest.mark.skip
def test_recursion():
    result = evaluation.run(fac1, 0)
    assert result == 1
    result = evaluation.run(fac1, 1)
    assert result == 1
    result = evaluation.run(fac1, 2)
    assert result == 2
    result = evaluation.run(fac1, 3)
    assert result == 6
    result = evaluation.run(fac1, 4)
    assert result == 24

# TODO:
# - remove explicit setting of outputs, update them in the scheduler DFS
# - result, Value, composed action, immediate evaluation by Scheduler
# - remove task ids, use just hashes
# - link tasks indirectly through hashes, no need for Pass() result tasks, can


#########################################################
#

@wf.workflow
def outer_wf(i: int):
    @wf.workflow
    def nested():
        return i

    return nested()

# nested workflow def yet to be implemented
@pytest.mark.skip
def test_nested_wf():
    result = evaluation.run(outer_wf, 4)
    assert result == 4

#########################################################
#


@wf.workflow
def _fib_true(prev):
    i, a, b = prev
    return (i - 1, b, a + b)

@wf.workflow
def _fib_body(prev):
    i, a, b = prev
    false_body = wf.lazy(wf.Pass, None)
    true_body = wf.lazy(_fib_true, prev)
    return wf.If(i > 0, true_body, false_body)

@wf.workflow
def fibonacci(n):
    fib = wf.While(_fib_body, (n, 1, 1))
    return fib[1]

#@pytest.mark.skip
def test_while():
    assert evaluation.run(fibonacci, 0) == 1
    assert evaluation.run(fibonacci, 1) == 1
    assert evaluation.run(fibonacci, 2) == 2
    assert evaluation.run(fibonacci, 3) == 3
    assert evaluation.run(fibonacci, 4) == 5

#
#
# def test_while_cond():
#     assert evaluation.run(fibonacci, 0) == 1
#     assert evaluation.run(fibonacci, 1) == 1
#     assert evaluation.run(fibonacci, 2) == 2
#     assert evaluation.run(fibonacci, 3) == 3
#     assert evaluation.run(fibonacci, 4) == 5


# @wf.action_def
# def condition(lst:wf.List[float], num:float, end:float) -> bool:
#     return num < end
#
# @wf.action_def
# def body(lst:wf.List[float], num:float, inc:float) -> wf.List[float]:
#     lst.append(num)
#     return lst, num + inc
#
# @wf.workflow
# def linspace(self, begin: float, end:float, inc:int):
#     cond = wf.partial(condition, end=end)
#     b = wf.partial(body, inc=inc)
#     return wf.While(([], begin), cond, b)
#
# def test_while():
#     result = evaluation.run(linspace, 1.1, 3.4, 0.6)
#     assert result == ([1.1, 1.7, 2.3, 2.9], 3.5)

"""
def fib_cond(iter):
    return iter[3] > 0

@vs.workflow
def fib_body(iter):
    return (iter[1], iter[0] + iter[1], iter[2]-1)
    
@vs.workflow
def fibonaci(n:int, pair:) -> pair
    init = (pair[0], pair[1], n) 
    vs.While(init, fib_cond, fib_body)
    return
"""