
from typing import List
from visip.dev.parameters import ActionParameter
from visip.action.constructor import ClassActionBase
from visip.code import decorators as wf
from visip.code.decorators import public_action, _construct_from_params
from visip.dev import dtype

@wf.Class
class Point:
    x: float = 0.0
    y: float = 0.0

@wf.Class
class Element:
    region: int
    node_ids: List[int] = []


@wf.Class
class Mesh:
    nodes: List[Point] = []
    elements: List[Element] = []



def test_dataclass_modification():
    #
    point_wrap = Point
    point_action = point_wrap._action_value
    params = list(point_action.parameters)
    params = [ActionParameter(p.name, dtype.to_typing(p.type), p.default) for p in params]
    param_z = ActionParameter("z", float, 0.0)
    params.append(param_z)
    point_xyz = public_action(_construct_from_params("PointXYZ", params) )
    xyz_instance = point_xyz(x=1, y=2, z=3)._value
    assert len(xyz_instance.arguments) == 3
    assert xyz_instance.arguments[0].value.action.value == 1.0
    assert xyz_instance.arguments[1].value.action.value == 2.0
    assert xyz_instance.arguments[2].value.action.value == 3.0




# def test_classtypes():
#     mesh = Mesh()
#     point = data.Class(x:float = 0, y:float = 0)
#
# def test_subtypes():
#
#     data.Sequence[]
