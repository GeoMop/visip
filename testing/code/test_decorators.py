from visip.code import decorators
from visip.code import representer

def test_action_decorator():
  pass


@decorators.Enum
class MyEnum:
    a=0
    b=2


def test_enum_decorator():
    x = MyEnum.a

    def make_rel_name():
        pass

    rep = representer.Representer(make_rel_name)
    print(x.__code__(rep))