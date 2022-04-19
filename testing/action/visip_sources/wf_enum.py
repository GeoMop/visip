import visip as wf
import enum

class PyEnum(enum.IntEnum):
    a=10
    b=50


@wf.Enum
class MyEnum:
    a=1
    b=5
    c=PyEnum.a
    d=PyEnum.b

@wf.action_def
def test(a, b) -> str:
    s = f"a:{type(a)} = {a}. b:{type(b)} = {b}"
    print(s)
    return s

@wf.analysis
def script():
    return test(MyEnum(1), MyEnum.d)
