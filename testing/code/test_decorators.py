from visip.code import decorators
from visip.code import representer
import visip as wf
import inspect

def test_action_decorator():
  pass


@wf.Enum
class MyEnum:
    a=0
    b=2


def test_enum_decorator():
    x = MyEnum.a

    def make_rel_name(module, name):
        return "{}.{}".format(module, name)
    rep = representer.Representer(make_rel_name)
    assert "test_decorators.MyEnum.a" == x.__code__(rep)

