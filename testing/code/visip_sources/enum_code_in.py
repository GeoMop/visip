import visip as wf

@wf.Enum
class MyVals:
    a=1
    b=2
    c=4

@wf.action_def
def foo(x:MyVals):
    return x + 1

@wf.workflow
def goo(x:int):
    return foo(MyVals(x))
