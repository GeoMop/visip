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


@Class
class Element:
    type_id: int = 0  # v commitu přepsáno na dict: type_id -> (dim,n_nodes)
    dim: int = 0
    region_id: int = 0
    shape_id: int = 0  # má být optional
    partition_id: int = 0  # má být optional
    nodes: List[int] = []

    # tags: [region_id, shape_id, partition_id]


@Class
class MeshGMSH:
    nodes: Dict[int, Point] = None
    elements: Dict[int, Element] = None
    # regions: Dict[str, List[int]] = None


@action_def
def GMSH_reader(path: str) -> MeshGMSH:
    reader = gmsh_io.GmshIO(path)
    reader.read()

    points = {}
    for idx, point in reader.nodes.items():
        points[idx] = Point(x=point[0], y=point[1], z=point[2])

    elements = {}
    for idx, element in reader.elements.items():
        try:
            elements[idx] = Element(type_id=element[0], dim=None, region_id=element[1][0], shape_id=element[1][1],
                                    partition_id=element[1][2], nodes=element[2])
        except:
            elements[idx] = Element(type_id=element[0], dim=None, region_id=element[1][0], shape_id=element[1][1],
                                    nodes=element[2])

    my_Mesh = MeshGMSH(points, elements)  # , reader.physical)
    return my_Mesh
