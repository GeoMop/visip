import visip as wf


@wf.Enum
class MyVals:
    a = 1
    b = 2
    c = 4


@wf.action_def
def foo(x: MyVals) -> wf.Any:
    # User defined action cen not been represented.
    pass


@wf.workflow
def goo(self, x: wf.Int):
    foo_1 = foo(x=MyVals(enum_item=x))
    return foo_1