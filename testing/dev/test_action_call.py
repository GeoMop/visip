from typing import List
from visip.dev import action_instance as acall
import visip as wf
from visip.code import wrap

def test_action_call_str():
    ac = wf.list(1, 2, 3)
    print("List Action Call: ", str(ac._action_call))