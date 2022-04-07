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
    mod = module.Module.load_module(source)
    assert isinstance(mod.get_action("xflip"), wf._Workflow)
    assert isinstance(mod.get_action("Square"), constructor.ClassActionBase )

    mod.rename_definition("xflip", "yflip")
    assert isinstance(mod.get_action("yflip"), wf._Workflow)

    mod.rename_definition("Square", "Rectangle")
    c = mod.code()
    print(c)
    assert c.find("class Rectangle")
    assert c.find("def yflip")


def test_insert_imported_module():
    source = os.path.join(script_dir, "..", "code", "visip_sources", "import_user_defs_in.py")
    mod = module.Module.load_module(source)

    filename = os.path.join(script_dir, "..", "code", "visip_sources", "analysis_in.py")
    alias = "test"


    new_module = module.Module.load_module(filename)
    mod.insert_imported_module(new_module, alias)
    print(f'key for _object_names: {((getattr(new_module, "__module__", None), getattr(new_module, "__name__", None)))}')
    print(f"alias: {alias}")
    mod_name = mod.object_name(new_module.py_module)
    print(f"returned name: {mod_name}")
    assert mod_name == alias
