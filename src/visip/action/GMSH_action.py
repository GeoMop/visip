from typing import Dict, List, Tuple, Optional

import numpy as np
from bgem.gmsh import gmsh_io

# from visip import action_def
# from src.visip.code.decorators import Class
from visip import FileOut
from ..code.decorators import action_def
from ..code.decorators import Class
import visip as wf


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

    # gmsh_io.elements:(type,tags,nodes)
    # tags: [region_id, shape_id, partition_id]


@Class
class MeshGMSH:
    nodes: Dict[int, Point] = None
    elements: Dict[int, Element] = None
    regions: Dict[str, List[int]] = None

    # def ExtractRegionElements(self,regions:List[str]) -> List[Tuple[int,Element]]:
    #     region_id_dim = List[Tuple[int,int]]
    #     for region in regions:
    #         if region in self.regions.keys():
    #             region_id_dim.append(self.regions.values())
    #
    #     return region_id_dim


@action_def
def GMSH_reader(path: str) -> MeshGMSH:
    reader = gmsh_io.GmshIO(path)
    reader.read()

    points = {}
    for idx, point in reader.nodes.items():
        points[idx] = Point.call(point[0], point[1], point[2])

    elements = {}
    for idx, element in reader.elements.items():
        # print(element)
        # print('type_id = {}'.format(element[0]))
        # print('tags = {}'.format(element[1]))
        # try:
        #     print('region;shape;partition = {0};{1};{2}'.format(element[1][0],element[1][1],element[1][2]))
        # except:
        #     print('region;shape;partition = {0};{1}'.format(element[1][0], element[1][1]))
        # print('nodes = {}'.format(element[2]))

        # elements[idx] = Element.call(element[0], None, element[1][0], element[1][1], element[1][2], element[2])

        try:
            elements[idx] = Element.call(element[0], None, element[1][0], element[1][1], element[1][2], element[2])
        # elements[idx] = Element(type_id=element[0], dim=None, region_id=element[1][0], shape_id=element[1][1],
        #                         partition_id=element[1][2], nodes=element[2])
        except:
            elements[idx] = Element.call(element[0], None, element[1][0], element[1][1], None, element[2])
        # elements[idx] = Element(type_id=element[0], dim=None, region_id=element[1][0], shape_id=element[1][1],
        #                         nodes=element[2])

    my_Mesh = MeshGMSH.call(points, elements, reader.physical)
    return my_Mesh


def ExtractRegionElements(msh: MeshGMSH, regions: List[str]) -> List[Tuple[int, Element]]:
    region_id_dim = []
    for region in regions:
        if region in msh.regions.keys():
            region_val = [val for name, val in msh.regions.items() if name == region]
            region_id_dim.append(*region_val)

    idecka = []
    elementy = []
    region_dim_only = [x[0] for x in region_id_dim]
    for ele_id, ele_val in msh.elements.items():
        for region_dim in region_dim_only:
            if ele_val.region_id == region_dim:
                idecka.append(ele_id)
                elementy.append(ele_val)

    result = list(zip(idecka, elementy))
    return result


def EleIds(msh: List[Tuple[int, Element]]) -> List[int]:
    return [x[0] for x in msh]


def Barycenter(mesh: MeshGMSH, msh: List[Tuple[int, Element]]) -> np.ndarray:  # output?
    barycenter = np.array([float])
    kvuli_insertu = -1
    for id, elem in msh:
        sum_elem = 0
        for point_id in elem.nodes:
            kvuli_insertu += 1
            point = mesh.nodes[point_id]
            pp = sum(point.__dict__.values()) / len(point.__dict__.values())
            sum_elem += pp
        avg_elem = sum_elem / len(elem.nodes)
        barycenter = np.append(barycenter, [avg_elem])

    return barycenter


def Generate_Field():  # input / output?
    # fields: Dict[str, np.array] # vsechna np.array by mela mit velikost
    # jako pocet elementu v siti == len(ele_ids)
    pass


@action_def
def write_fields(mesh: MeshGMSH) -> int:
    """
    Preparing action for visip from bgem to write mesh fields
    :param msh_file: target file
    :param ele_ids: List[int] ; pro kazdou hodnotu v np.array cislo
    prislusneho elementu
    :param fields: Dict[str, np.array] ; vsechna np.array by mela mit
    velikost jako pocet elementu v siti == len(ele_ids)
    :return: ??


    #bgem desc
    Creates input data msh file for Flow model.
    :param msh_file: Target file (or None for current mesh file)
    :param ele_ids: Element IDs in computational mesh corrsponding to order of
    field values in element's barycenter.
    :param fields: {'field_name' : values_array, ..}
    """

    RegionElements = ExtractRegionElements(mesh, ['".side_y0"'])#, '".side_y1"', '"fr"'])  # , list(mesh.regions.keys()))
    Element_ids = EleIds(RegionElements)
    Bary = Barycenter(mesh, RegionElements)

    return RegionElements
    # rozparsování mesh
    # co přesně je ele_ids a fields?
    # writter = gmsh_io.GmshIO(msh_file)
    # ele_ids = None
    # fields = None
    # writter.write_fields(msh_file=msh_file, ele_ids=ele_ids, fields=fields)
    # return -1
