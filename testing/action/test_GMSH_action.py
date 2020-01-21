from typing import List
from visip.dev.parameters import ActionParameter
from visip.action.constructor import ClassActionBase
from visip.code import decorators as wf
from visip.code import wrap

from visip.action.GMSH_action import Point, Element, MeshGMSH, GMSH_reader


def GMSH_action_and_classes():
    point_wrap = Point
    point_action = point_wrap.action
    params = list(point_action.parameters)
    print(params)


