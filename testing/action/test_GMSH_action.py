import typing

from typing import List

import pytest

from visip import Class
from visip.dev.parameters import ActionParameter
from visip.action.constructor import ClassActionBase
from visip.code import decorators as wf
from visip.code import wrap

from visip.action.GMSH_action import Point, Element, MeshGMSH, GMSH_reader, write_fields

# test_std imports
# import os
# import shutil
# import visip.dev.tools as tools
import visip as wf
from visip.dev import evaluation


# def test_GMSH_Point():
#     point_wrap = Point
#     point_action = point_wrap.action
#     params = list(point_action.parameters)
#     assert params[0].name == 'x'
#     assert params[1].name == 'y'
#     assert params[2].name == 'z'
#     point_xyz = wrap.public_action(ClassActionBase.construct_from_params("PointXYZ", params))
#     xyz_instance = point_xyz(x=0, y=11, z=222)._action_call
#     assert xyz_instance
#     assert xyz_instance.arguments[0].value.action.value == 0
#     assert xyz_instance.arguments[1].value.action.value == 11
#     assert xyz_instance.arguments[2].value.action.value == 222
#
#
# def test_GMSH_Element():
#     element_wrap = Element
#     element_action = element_wrap.action
#     params = list(element_action.parameters)
#     assert params[0].name == 'type_id'
#     assert params[1].name == 'dim' and params[1].type == int
#     assert params[2].name == 'region_id'
#     assert params[3].name == 'shape_id'
#     assert params[4].name == 'partition_id' and params[4].type == int
#     assert params[5].name == 'nodes' and params[5].type == typing.List[int]
#     element_test = wrap.public_action(ClassActionBase.construct_from_params('element_test', params))
#     element_instance = element_test(type_id=1, dim=2, region_id=3, shape_id=4, partition_id=5,
#                                     nodes=[1, 2, 3])._action_call
#     assert element_instance
#     assert element_instance.arguments[0].value.action.value == 1
#     assert element_instance.arguments[1].value.action.value == 2
#     assert element_instance.arguments[5].value.arguments[0].value.action.value == 1
#     assert element_instance.arguments[5].value.arguments[1].value.action.value == 2
#     assert element_instance.arguments[5].value.arguments[2].value.action.value == 3
#
#
# def prepare_nodes():
#     point_wrap = Point
#     point_action = point_wrap.action
#     params = list(point_action.parameters)
#     point_xyz = wrap.public_action(ClassActionBase.construct_from_params("PointXYZ", params))
#     xyz_instance = point_xyz(x=0, y=11, z=222)._action_call
#     return {0: xyz_instance}
#
#
# def prepare_elements():
#     element_wrap = Element
#     element_action = element_wrap.action
#     params = list(element_action.parameters)
#     element_test = wrap.public_action(ClassActionBase.construct_from_params('element_test', params))
#     element_instance = element_test(type_id=1, dim=2, region_id=3, shape_id=4, partition_id=5,
#                                     nodes=[1, 2, 3])._action_call
#
#     return {0: element_instance}
#
#
# def test_GMSH_Mesh():
#     mesh_wrap = MeshGMSH
#     mesh_action = mesh_wrap.action
#     params = list(mesh_action.parameters)
#     assert params
#     mesh_test = wrap.public_action(ClassActionBase.construct_from_params('mesh_test', params))
#     mesh_instance = mesh_test(nodes=prepare_nodes(), elements=prepare_elements())._action_call
#     assert mesh_instance
#     assert mesh_instance.parameters.parameters[0].name == 'nodes'
#     assert mesh_instance.parameters.parameters[1].name == 'elements'


@wf.analysis
def loading_mesh() -> MeshGMSH:
    return GMSH_reader('_workspace/random_fractures_01.msh')


def test_load_mesh():
    result = evaluation.run(loading_mesh)
    # print(result)
    assert result.nodes
    assert result.elements
    assert result.regions

    assert result.nodes[1].x == 300
    assert result.elements[1].nodes == [511, 690]
    assert result.regions['"fr"'] == (10, 2)


import numpy as np


@wf.action_def
def prepare_np_array(arr: np.ndarray) -> np.ndarray:
    fin = np.append(arr, [1, 2, 3])
    return fin


@wf.action_def
def prepare_np_array_none(arr: np.ndarray = None) -> np.ndarray:
    fin = np.append(arr, [1, 2, 3])
    return fin


def test_np_array():
    result = evaluation.run(prepare_np_array, [np.array([-1, 0])])
    print(type(result))
    assert issubclass(type(result), np.ndarray)


def test_np_array_none():
    result = evaluation.run(prepare_np_array_none)
    print(type(result))
    assert issubclass(type(result), np.ndarray)


MY_FILE = "write_fields.gmsh"
WORKSPACE = "_workspace"


@wf.workflow
def writing_fields(mesh: MeshGMSH):
    return write_fields(mesh)


def test_write_fields():
    mesh = evaluation.run(loading_mesh)
    print('!')
    write = evaluation.run(writing_fields, [mesh])
    print('_')
