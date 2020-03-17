from typing import Dict, List, Tuple, Optional, Any

import numpy as np
from bgem.gmsh import gmsh_io

# from visip import action_def
# from src.visip.code.decorators import Class
from visip import FileOut
from ..code.decorators import action_def
from ..code.decorators import Class
from ..dev import action_instance as instance
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


@action_def
def GMSH_reader(path: str) -> MeshGMSH:
    """
    reader for .msh files
    :param path: target file
    :return: Mesh like variable
    """
    reader = gmsh_io.GmshIO(path)
    reader.read()

    points = {}
    for idx, point in reader.nodes.items():
        points[idx] = Point.call(point[0], point[1], point[2])

    elements = {}
    for idx, element in reader.elements.items():
        try:
            elements[idx] = Element.call(element[0], None, element[1][0], element[1][1], element[1][2], element[2])
        except:
            elements[idx] = Element.call(element[0], None, element[1][0], element[1][1], None, element[2])

    my_Mesh = MeshGMSH.call(points, elements, reader.physical)
    return my_Mesh


@action_def
def ExtractRegionElements(msh: MeshGMSH, regions: List[str]) -> List[Tuple[int, Element]]:
    """

    :param msh:
    :param regions:
    :return:
    """
    region_id_dim = []
    for region in regions:
        if region in msh.regions.keys():
            region_val = [val for name, val in msh.regions.items() if name == region]
            region_id_dim.append(*region_val)

    element_id = []
    elements = []
    region_dim_only = [x[0] for x in region_id_dim]
    for ele_id, ele_val in msh.elements.items():
        for region_dim in region_dim_only:
            if ele_val.region_id == region_dim:
                element_id.append(ele_id)
                elements.append(ele_val)

    result = list(zip(element_id, elements))
    return result


@action_def
def EleIds(msh: List[Tuple[int, Element]]) -> List[int]:
    return [x[0] for x in msh]


@action_def
def Barycenter(mesh: MeshGMSH, msh: List[Tuple[int, Element]]) -> np.ndarray:  # output?
    pp_bary = []
    for id, elem in msh:
        keys = ['x', 'y', 'z']
        pom_dict = {key: [] for key in keys}
        for point_id in elem.nodes:
            point = mesh.nodes[point_id]
            pom_dict['x'].append(point.x)
            pom_dict['y'].append(point.y)
            pom_dict['z'].append(point.z)
        bary_x = np.average(pom_dict['x'])
        bary_y = np.average(pom_dict['y'])
        bary_z = np.average(pom_dict['z'])

        pp_bary.append([bary_x, bary_y, bary_z])

    barycenter = np.array(pp_bary)
    return barycenter


@action_def
def field_mesh_sampler(all_fields: List[str], outer_field_names: List[str],
                       barycenters: np.ndarray) -> Any:  # all_fields:List[Field] -> function
    return -1  # function


@action_def
def Generate_Field():
    # fields: Dict[str, np.array] # vsechna np.array by mela mit velikost
    # jako pocet elementu v siti == len(ele_ids)
    return -1


@action_def
def write_fields(mesh: MeshGMSH) -> int: # (ele_ids:List[int],sampler:Action) -> ??: ???
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
    :param ele_ids: Element IDs in computational mesh corresponding to order of
    field values in element's barycenter.
    :param fields: {'field_name' : values_array, ..}
    """

    RegionElements = ExtractRegionElements.call(mesh,
                                                list(mesh.regions.keys()))
    Element_ids = EleIds.call(RegionElements)
    Bary = Barycenter.call(mesh, RegionElements)

    return Bary
    # rozparsování mesh
    # co přesně je ele_ids a fields?
    # writter = gmsh_io.GmshIO(msh_file)
    # ele_ids = None
    # fields = None
    # writter.write_fields(msh_file=msh_file, ele_ids=ele_ids, fields=fields)
    # return -1
