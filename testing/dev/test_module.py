import os
from visip.dev import module
from visip.dev import action_workflow as wf
from visip.action import constructor

import pytest
script_dir = os.path.dirname(os.path.realpath(__file__))

"""
TODO:
- load module and test resulting Module, for files of various complexity
- modifications
"""

def source_path(file_name):
    return os.path.abspath(os.path.join(script_dir, "..", "code", "visip_sources", file_name))

def load_file(file_name):
    return module.Module.load_module(source_path(file_name))


def test_module_load():
    """
    Test load, modify and safe a module.
    """
    test_file = "dep_module_in.py"
    mod = load_file(test_file)

    # definitions - imported modules
    assert mod.py_module.__name__ == "dep_module_in"
    assert mod.module_file == source_path(test_file)
    assert mod.is_visip_module()
    assert len(mod.imported_modules) == 2       # visip, analysis_in
    visip_def = mod.new_definitions[(None, 'visip')]
    assert visip_def.alias == "wf"
    assert visip_def.module.name == "visip"
    analysis_in_def = mod.new_definitions[(None, 'analysis_in')]
    assert analysis_in_def.alias == "tool"
    assert analysis_in_def.module.name == "analysis_in"

    # definitions - workflows

    # _modules
    visip_mod = mod.get_module("visip")
    assert visip_mod.name == "visip"
    assert visip_mod.is_visip_module()
    assert len(visip_mod.ignored_definitions) == 0
    analysis_mod = mod.get_module("analysis_in")
    assert analysis_mod.name == "analysis_in"
    assert analysis_mod.is_visip_module()
    assert len(analysis_mod.ignored_definitions) == 0
    dummy_mod= mod.get_module("visip.code.dummy")
    assert dummy_mod.name == "visip.code.dummy"
    assert not dummy_mod.is_visip_module()
    assert len(dummy_mod.ignored_definitions) > 0
    os_mod = mod.get_module("os")
    assert os_mod.name == "os"
    assert not os_mod.is_visip_module()

    tm = mod.types_map()
    print("\n".join([str(x) for x in tm.items()]))
    point = tm[('analysis_in', 'Point')]

def test_operations():
    """
    Test load, modify and safe a module.
    """
    mod = load_file("dep_module_in.py")
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
