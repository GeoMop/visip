from visip.code import decorators
from visip.code import representer
from visip.code.formating import Format
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
    enum_val_repr: Format = x._value.code(rep)
    assert "test_decorators.MyEnum.a" == enum_val_repr.final_string()

    """
    TODO:
    - fix get_attr for Enum
    - enumitem.__code__, 
    - tox
    
    """