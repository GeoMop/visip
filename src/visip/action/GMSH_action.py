from typing import Dict, List, Tuple

from ..code.decorators import Class

# from bgem.??


@Class
class Point:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@Class
class Element:
    type_id: int
    dim: int
    region_id: int
    shape_id: int
    partition_id: int
    nodes: List[int]

    tags: [region_id, shape_id, partition_id]


@Class
class MeshGMSH:
    nodes: Dict[int, Point]
    elements: Dict[int, Element]
    regions: Dict[str, Tuple[int, int]]
