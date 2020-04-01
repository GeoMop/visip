import os
#import shutil
import visip.dev.tools as tools
import visip as wf
from visip.dev import evaluation
script_dir = os.path.dirname(os.path.realpath(__file__))

# Test definition of an action that returns an action.

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
    return adder_val(2)

def test_action_returning_action():
    result = evaluation.run(tst_adder)
    assert result == 3


def test_partial():


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
