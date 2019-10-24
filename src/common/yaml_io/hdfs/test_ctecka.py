from typing import List
import common.action_base as base
import common.code.decorators as wf
import common.code.wrap as wrap


# @wf.Class
# class Point:
#     x: float = 0.0
#     y: float = 0.0
#

@wf.Class
class Data:
    data: dict


# def test_dataclass_modification():
#     #
#     point_wrap = Point
#     point_action = point_wrap.action
#     params = list(point_action.parameters)
#     param_z = base.ActionParameter(2, "z", float, 0.0)
#     params.append(param_z)
#     point_xyz = wrap.public_action(base.ClassActionBase.construct_from_params("PointXYZ", params))
#     xyz_instance = point_xyz(x=1, y=2, z=3)._action
#     assert len(xyz_instance.arguments) == 3
#     assert xyz_instance.arguments[0].value.action.value == 1.0
#     assert xyz_instance.arguments[1].value.action.value == 2.0
#     assert xyz_instance.arguments[2].value.action.value == 3.0


def test_ctecka_action():
    data_wrap = Data
    data_action = data_wrap.action
    params = list(data_action.parameters)
    param_ctecka = base.ActionParameter(0, 'Data')
    params.append(param_ctecka)
    data = wrap.public_action(base.ClassActionBase.construct_from_params('Data', params))
    data_instance = data(data)._action
    assert data_instance.arguments[0]
    print(data_instance.arguments)
    print(data_instance.arguments[0].value.action.value)

test_ctecka_action()