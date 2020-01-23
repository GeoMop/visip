import os
from visip.dev import module
from visip.dev import action_workflow as wf
from visip.action import constructor

import pytest
script_dir = os.path.dirname(os.path.realpath(__file__))

def test_operations():
    """
    Test load, modify and safe a module.
    """
    source = os.path.join(script_dir, "..", "code", "visip_sources", "dep_module_in.py")
    mod = module.Module(source)
    assert isinstance(mod.get_action("xflip"), wf._Workflow)
    assert isinstance(mod.get_action("Square"), constructor.ClassActionBase )

    mod.rename_definition("xflip", "yflip")
    assert isinstance(mod.get_action("yflip"), wf._Workflow)

    mod.rename_definition("Square", "Rectangle")
    c = mod.code()
    print(c)
    assert c.find("class Rectangle")
    assert c.find("def yflip")
