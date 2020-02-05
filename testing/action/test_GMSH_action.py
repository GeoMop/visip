import typing

from typing import List

import pytest

from visip.dev.parameters import ActionParameter
from visip.action.constructor import ClassActionBase
from visip.code import decorators as wf
from visip.code import wrap

from visip.action.GMSH_action import Point, Element, MeshGMSH


def test_GMSH_Point():
    point_wrap = Point
    point_action = point_wrap.action
    params = list(point_action.parameters)
    assert params[0].name == 'x'
    assert params[1].name == 'y'
    assert params[2].name == 'z'


def test_GMSH_Element():
    element_wrap = Element
    element_action = element_wrap.action
    params = list(element_action.parameters)
    assert params[0].name == 'type_id'
    assert params[1].name == 'dim' and params[1].type == int
    assert params[2].name == 'region_id'
    assert params[3].name == 'shape_id'
    assert params[4].name == 'partition_id' and params[4].type == int
    assert params[5].name == 'nodes' and params[5].type == typing.List[int]


def test_GMSH_Mesh():
    mesh_wrap = MeshGMSH
    mesh_action = mesh_wrap.action
    params = list(mesh_action.parameters)
    assert params
    print(params)

# @pytest.mark.parametrize('file', ['D:\\Git\\muj_PyBS\\PyBS\\tests\\gmsh\\complex\\meshes\\random_fractures_01.msh'])
# def test_GMSH_reader(file):
#     reader = GMSH_reader(file).action
#     print(reader)
