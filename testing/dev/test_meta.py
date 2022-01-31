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
def wf_condition(cond: int) -> int:
    return wf.If(cond, true_body, false_body)

def test_if_action():
    result = evaluation.run(wf_condition, [True])
    assert result == 101
    result = evaluation.run(wf_condition, [False])
    assert result == 100


# simpler if
@wf.action_def
def foo(x):
    return x + 1

@wf.workflow
def wf_condition(cond: int) -> int:
    return wf.If(cond, foo(100), 100)


def test_if_action():
    result = evaluation.run(wf_condition, [True])
    assert result == 101
    result = evaluation.run(wf_condition, [False])
    assert result == 100


#######################
# Test lazy meta action.
# No control over free positional arguments, must use keyword arguments instead.

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

def test_lazy():
    #result = evaluation.run(lazy_wf, [], plot_expansion=True)
    result = evaluation.run(lazy_wf, [])
    assert result[0] == "lazy_action(4 1 (5,) 2 7 {'c': 3})"
    assert result[1] == "lazy_action(100 101 (102,) a b {'d': 'd'})"


@wf.workflow
def lazy_wf_err_1():
    partial = wf.lazy(lazy_action, wf.empty, 1, a=2, c=3)
    return partial(4, 5, a=6, b=7)

@pytest.mark.skip
def test_lazy_errors():
    with pytest.raises(exceptions.ExcArgumentBindError) as e:
        result = evaluation.run(lazy_wf_err_1, [])

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

# @wf.workflow
# def true_fac(i:int):
#     return 1

@wf.action_def
def make_fac(i: int) -> wf.Any:
    """
    Example of an action producing action.
    :param left_operand:
    :return:
    """
    def add() -> int:
        return fac(i)
    return wf.action_def(add)

@wf.workflow
def fac(i:int):
    i_1 = sub(i, 1)
    zero = equal(i, 0)
    fac_action = make_fac(i_1)
    fac_1 = wf.If(zero, 1, fac_action)
    return mult(i, fac_1)

@pytest.mark.skip
def test_recursion():
    result = evaluation.run(fac, [4])
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
    result = evaluation.run(outer_wf, [4])
    assert result == 4


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
