import pytest
import visip as wf
from visip.dev.action_instance import ActionCall
from visip.dev.parameters import ActionParameter
from visip.code.unwrap import into_action
from visip.action.constructor import A_list
from visip.dev.exceptions import ExcArgumentBindError
from typing import *


@wf.action_def
def fa(a:int, /, b: float, *other_args: Tuple[int], c: str, **other_kwargs: Tuple[float]) -> Tuple[str]:
    pass

def test_action_call():
    ac = ActionCall(A_list(), "my_list")
    assert ac.action.name == "list"
    assert len(ac.parameters) == 1
    assert ac.parameters['args'].kind == ActionParameter.VAR_POSITIONAL
    assert ac.arguments == []
    args = [into_action(1), into_action('A'), into_action([4, 'A'])]
    ac.set_inputs(args)
    assert len(ac.arguments) == 3

"""
Following test fails becase ac is not DataClass.
"""
def test_action_call_str():
    ac = wf.list(1, 2, 3)
    print("List Action Call: ", str(ac._action_call))





def call(action, *args, **kwargs):
    args = [ActionCall.into_action(a) for a in args]

def test_binding():
    ac1 = fa(0, 1, 2, 3, c=4, d=5, e=6)._value
    a_names = [a.parameter.name for a in ac1.arguments]
    assert a_names == ['a', 'b', 'other_args', 'other_args', 'c', 'other_kwargs', 'other_kwargs']
    ac2 = fa(0, b=1, c=4, d=5, e=6)._value
    a_names = [a.parameter.name for a in ac2.arguments]
    assert a_names == ['a', 'b', 'c', 'other_kwargs', 'other_kwargs']

    # TODO: report binding errors
    with pytest.raises(ExcArgumentBindError) as e:
        fa(0, 1, 2, c=4, b=3, d=5, e=6)  # duplicate 'b' parameter
    assert "BindError.DUPLICATE" in str(e.value)
    fa(0, c=4, d=5, e=6)     # Missing 'b' parrameter
