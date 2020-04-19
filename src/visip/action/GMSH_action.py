import typing
from typing import Dict, List, Tuple, Optional, Any

import mlmc.correlated_field as cf
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


SubMesh = typing.NewType('SubMesh', List[Tuple[int, Element]])


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
def ExtractRegionElements(msh: MeshGMSH, regions: List[str]) -> SubMesh:
    """
    Extracts chosen regions from mesh and creates SubMesh from those regions.
    :param msh: whole mesh
    :param regions: regions to extract
    :return: extracted regions as SubMesh  - List[Tuple[int, Element]]
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
def ExtractRegionIds(submsh: SubMesh) -> List[int]:
    RegionIds = []
    for Element_id, Element in submsh:
        RegionIds.append(Element.region_id)
    return RegionIds


@action_def
def EleIds(msh: SubMesh) -> List[int]:
    return [x[0] for x in msh]


@action_def
def Barycenter(mesh: MeshGMSH, msh: SubMesh) -> np.ndarray:  # output?
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


# @action_def
# def sampler_fn(seed: int) -> Any:
#     return np.random.seed(seed)


@action_def
def field_mesh_sampler(all_fields: cf.Fields, outer_field_names: List[str],
                       barycenters: np.ndarray, region_ids: List[int]) -> Any:  # should return @action

    # fields = cf.Fields(all_fields)
    all_fields.set_outer_fields(outer_field_names)
    all_fields.set_points(barycenters, region_ids=region_ids)

    def sampler_fn(seed: int) -> Any:
        np.random.seed(seed)
        return all_fields.sample()

    return wf.action_def(sampler_fn)


@action_def
def make_fields() -> cf.Fields:
    return cf.Fields([
        cf.Field('conductivity', cf.FourierSpatialCorrelatedField('gauss', dim=3, corr_length=0.125, log=True)),
    ]) # Field s dim=3 není implementován. Moje chyba?
    # return cf.Fields([
    #     cf.Field(name='conductivity', field=1),
    #     cf.Field(name='conductivity1', field=2)
    # ])


@action_def
def write_fields(mesh: MeshGMSH, ele_ids: List[int], sample: wf.Any) -> Any:
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
    gmsh_io.GmshIO.write_fields(mesh, 'Mesh_write_file.txt', ele_ids=ele_ids, fields=sample)

    return -1