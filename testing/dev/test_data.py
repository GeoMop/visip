from visip.dev import data
from typing import *
import attr

@attr.s(auto_attribs=True)
class A:
    a: Tuple[float, float]

@attr.s(auto_attribs=True)
class B:
    a: int
    b: str
    c: List[A]
    d: Dict[int, A]

def test_data():
    b_inst = B(a=123, b="ahoj", c=[A((1,2)), A((3,4))], d={123: A((5,6))})
    hb1 = data.hash(b_inst)
    b_inst2 = B(a=123, b="ahoj", c=[A((1, 2)), A((3, 4))], d={123: A((5, 6))})
    hb2 = data.hash(b_inst2)
    assert hb1 == hb2
    b_inst.a = 134
    assert hb1 != data.hash(b_inst)