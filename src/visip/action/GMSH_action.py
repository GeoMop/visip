from typing import Dict, List, Tuple, Optional

from bgem.gmsh import gmsh_io

# from visip import action_def
# from src.visip.code.decorators import Class


from ..code.decorators import action_def
from ..code.decorators import Class


@Class
class Point:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    # def __init__(self, x, y, z):
    #     self._x = x
    #     self._y = y
    #     self._z = z


@Class
class Element:
    type_id: int = 0  # v commitu přepsáno na dict: type_id -> (dim,n_nodes)
    dim: int = 0
    region_id: int = 0
    shape_id: Optional[int] = 0
    partition_id: Optional[int] = 0
    nodes: List[int] = []

    # tags: [region_id, shape_id, partition_id]

    # def __init__(self, type_id: int, dim: int, tags: List[int], nodes: List[int]):
    #     self._type = type_id
    #     self._dim = dim
    #     if len(tags) == 3:
    #         self._region_id = tags[0]
    #         self._shape_id = tags[1]
    #         self._partition_id = tags[2]
    #     elif len(tags) == 2:
    #         self._region_id = tags[0]
    #         self._shape_id = tags[1]
    #     self._nodes = nodes


@Class
class MeshGMSH:
    nodes: Dict[int, Point] = None
    elements: Dict[int, Element] = None
    regions: Dict[str, Tuple[int, int]] = None


# def __init__(self, nodes: Dict[int, Point], elements: Dict[int, Element], regions: Dict[str, Tuple[int, int]]):
#     self._nodes = nodes
#     self._elements = elements
#     self._regions = regions


@action_def
def GMSH_reader(path):
    reader = gmsh_io.GmshIO(path)
    reader.read()
    # print(reader.physical)
    # print(reader.elements)
    # print(reader.nodes)
    # print(reader.element_data)
    # print(reader.filename)

    points = {}
    for idx, point in reader.nodes.items():
        points[idx] = Point(x=point[0], y=point[1], z=point[2])

    elements = {}
    for idx, element in reader.elements.items():
        print(element)
        elements[idx] = Element(type_id=element[0], dim=None)  # , tags=element[1], nodes=element[2])

    # my_Mesh = MeshGMSH(points, elements, reader.physical)
    # print(my_Mesh)
    # return my_Mesh
    return elements

# path = "D:\\Git\\muj_PyBS\\PyBS\\tests\\gmsh\\complex\\meshes\\random_fractures_01.msh"
# GMSH_reader(path)
