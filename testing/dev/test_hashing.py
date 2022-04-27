"""
Test proper hashing of the actions:
- action_def hash change after change of code (even if the name is the same)
- workflow hash change after change
- recursive workflow hash
"""
#import importlib
#importlib.reload(module)
from visip.dev import module
import visip
from visip.dev import data
from visip.action import std

mod1 = """
import visip as wf

@wf.action_def
def work(a:int):
    return a 

@wf.action_def
def work2(a:int):
    return a 

@wf.action_def
def work3(a:int):
    return a 
"""

mod2 = """
import visip as wf

@wf.action_def
def work(a:int):
    return a*a 

@wf.action_def
def work2(a:str):
    return a 
@wf.action_def
def work3(a:int):
    return a 
"""

def action_hash(mod, name):
    return mod.get_action(name).action_hash()

def test_action_def_hash():
    m1 = module.Module.make_module("mod1", mod1)
    m2 = module.Module.make_module("mod1", mod2)
    assert m1.py_module is not m2.py_module
    assert action_hash(m1, "work") != action_hash(m2, "work")   # different code
    assert action_hash(m1, "work2") == action_hash(m2, "work2")  # different signature
    assert action_hash(m1, "work3") == action_hash(m2, "work3") # same




@visip.workflow
def fac(self, i: int):
    self.fac_action = visip.lazy(fac, i-1)
    prev = visip.If(i == 0, 1, self.fac_action)
    return prev * i
fac1 = fac

@visip.workflow
def fac(self, i: int):
    fac_action = visip.lazy(fac, i-1)
    self.prev = visip.If(i == 0, 1, fac_action)
    return self.prev * i
fac2 = fac

@visip.workflow
def fac(self, i: int):
    fac_action = visip.lazy(fac, i - 1)
    self.prev = visip.If(i == 1, 1, fac_action)
    return self.prev * i
fac3 = fac

def test_meta():
    assert fac1.workflow.action_hash() == fac2.workflow.action_hash()
    assert fac1.workflow.action_hash() != fac3.workflow.action_hash()

def test_data():
    a = data.hash(std.SysFile.PIPE._value.action.value)
    b = data.hash(std.SysFile.STDOUT._value.action.value)
    c = data.hash(std.SysFile.DEVNULL._value.action.value)
    assert a != b
    assert a != c
    assert b != c

