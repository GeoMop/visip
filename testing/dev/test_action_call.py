import visip as wf
from visip.dev.action_instance import ActionCall
from visip.dev.parameters import ActionParameter
from visip.code.unwrap import into_action
from visip.action.constructor import A_list
from visip.dev import tools
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


def test_action_call_str():
    ac = wf.list(1, 2, 3)
    print("List Action Call: ", str(ac._action_call))