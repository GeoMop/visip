# import sys
#
# import yaml
# from yaml.constructor import SafeConstructor
#
#
# class CS(yaml.YAMLObject):
#     yaml_loader = yaml.SafeLoader
#     yaml_tag = u'!Coupling_Sequential'
#
#     name = '!Coupling_Sequential'
#
#     def __repr__(self):
#         return self.name
#
#     def __init__(self, description, mesh):
#         self.description = list(description)
#         self.mesh = list(mesh)
#
#     def __iter__(self):
#         yield self.description
#         yield self.mesh
#
#         # def __repr__(self):
#         #     return "{} \n description: {} \n mesh: {}".format(self.name, self.description, self.mesh)
#
#     # couple = CS('Simple dual porosity test - steady flow, simple transport', ['mesh_file', 'cesta'])
#     # serialized_user = yaml.dump(couple)
#     #
#     # print(serialized_user)
#     #
#     # def my_undf_cons(self, node):
#     #     data = {}
#     #     yield data
#     #     value = self.construct_mapping(node)
#     #     data.update(value)
#     #
#     #
#     # SafeConstructor.add_constructor(None, my_undf_cons)
#
#
# with open("muj_yaml.yaml", 'r')as stream:
#     data = yaml.safe_load(stream)
#     print(data)
#     print(list(data['problem']))
#     # yaml.dump(data, sys.stdout)
#
#
from dataclasses import dataclass

import attr
import yaml
from typing import List


@attr.s
class Colute_Advection_FV(yaml.YAMLObject):
    yaml_tag = '!Solute_Advection_FV'
    yaml_loader = yaml.SafeLoader


@attr.s
class FirstOrderReaction(yaml.YAMLObject):
    yaml_tag = '!FirstOrderReaction'
    yaml_loader = yaml.SafeLoader


@attr.s
class SorptionMobile(yaml.YAMLObject):
    yaml_tag = '!SorptionMobile'
    yaml_loader = yaml.SafeLoader


@attr.s
class SorptionImmobile(yaml.YAMLObject):
    yaml_tag = '!SorptionImmobile'
    yaml_loader = yaml.SafeLoader


@attr.s
class DualPorosity(yaml.YAMLObject):
    yaml_tag = '!DualPorosity'
    yaml_loader = yaml.SafeLoader


@attr.s
class vtk(yaml.YAMLObject):
    yaml_tag = '!vtk'
    yaml_loader = yaml.SafeLoader

    variant = attr.ib(str)


@attr.s
class Coupling_OperatorSplitting(yaml.YAMLObject):
    yaml_tag = '!Coupling_OperatorSplitting'
    yaml_loader = yaml.SafeLoader


@attr.s
class Petsc(yaml.YAMLObject):
    yaml_tag = '!Petsc'
    yaml_loader = yaml.SafeLoader

    a_tol = attr.ib(float)

    # snaha o vlastní loader _:(
    # @classmethod
    # def from_yaml(cls, loader, node):
    #     print(loader)
    #     print(node)
    #     print('____')
    #     print(loader.construct_mapping(node))
    #     print('____')
    #     cls.a_tol = loader.construct_mapping(node)
    #     return cls.a_tol

    # @attr.s


@dataclass
class input_fields:
    region: str = None
    conductivity: float = None
    bc_type: str = None
    bc_pressure: float = None
    diffusion_rate_immobile: List[float] = None
    porosity_immobile: float = None
    init_conc_immobile: List[float] = None
    rock_density: float = None
    sorption_type: str = None
    distribution_coefficient: float = None
    isotherm_other: float = None


@dataclass
class output:
    fields: List[str]


@dataclass
class output_stream:
    file: str
    format: vtk


@attr.s
class Flow_Darcy_MH(yaml.YAMLObject):
    yaml_tag = '!Flow_Darcy_MH'
    yaml_loader = yaml.SafeLoader

    nonlinear_solver = attr.ib(validator=Petsc)
    input_fields = attr.ib(validator=input_fields)
    output = attr.ib(validator=output)
    output_stream = attr.ib(validator=output_stream)

    # @classmethod
    # def from_yaml(cls, loader, node):
    #     # mapping = loader.construct_mapping(node)
    #     # print(loader.construct_mapping(node, deep=True))
    #     # print(loader.construct_yaml_object(cls, node))
    #     # print('___')
    #     # print(node.value[0][1].value[0][1].value)
    #     return loader.construct_mapping(node, deep=True)


# mesh by mohl být dataclass !!!

class mesh:
    mesh_file = str

    def __init__(self, meshh):
        self.mesh_file = meshh

    def __repr__(self):
        print(self.mesh_file)
        return 'mesh(\n' \
               '\t mesh_file: {})'.format(self.mesh_file)


# @attr.s(auto_attribs=True)
class Coupling_Sequential(yaml.YAMLObject):
    yaml_tag = '!Coupling_Sequential'
    yaml_loader = yaml.SafeLoader

    # jaká je správná validace??
    description: str
    mesh: mesh
    flow_equation: Flow_Darcy_MH
    solute_equation: Coupling_OperatorSplitting

    @classmethod
    def from_yaml(cls, loader, node):
        # print(cls)
        data_CS = loader.construct_mapping(node, cls)
        # print(data_CS)
        # print('___')
        # print(data_CS['description'])
        # print(data_CS['mesh']['mesh_file'])
        # print(data_CS['flow_equation'])
        # print(data_CS['solute_equation'])
        # print('___')
        # return data_CS
        # return cls.__init__(self=cls, desc=data_CS['description'], msh=data_CS['mesh'], flow_eq=data_CS['flow_equation'], solute_eq=data_CS['solute_equation'])
        return Coupling_Sequential(data_CS['description'], data_CS['mesh']['mesh_file'], data_CS['flow_equation'], data_CS['solute_equation'])

    def __init__(self, desc, msh, flow_eq, solute_eq):
        self.description = desc  # string
        self.mesh = mesh(msh)  # třída? - náhrada slovníku asi nebude třeba definovat třídu, ale vymyslet uložení podobné slovníku
        self.flow_equation = flow_eq  # třída...
        self.solute_equation = solute_eq  # třída...

    def __repr__(self):
        return '{} {} {} {} {}'.format(self.yaml_tag, self.description, self.mesh, self.flow_equation,
                                       self.solute_equation)

    # možnost udělat z tříd, které se nenachází v yaml file objekty???
    # jak se dostat na atributy třídy??
    # @classmethod
    # def from_yaml(cls, loader, node):
    #     pom = loader.construct_mapping(node, deep=True)
    #     # print(loader.construct_mapping(node, deep=True))
    #     meshhhhh = pom['mesh']['mesh_file']
    #     # print(meshhhhh)
    #     print(mesh)
    #     return pom['mesh']


def load_file(path=None):
    with open("flow_input.yaml", 'r')as stream:
        data = yaml.safe_load(stream)
        # print(data)
        # print(data['problem'].flow_equation.input_fields[0])
        # print(data['problem'].mesh['mesh_file'])
    return data


# load_file()
print(load_file())
"""
        17.9.
        TODO: nastudovat attr a vyřešit vytvořené nezbytně nutných tříd.
            Zkus se zamyslet nad náhradou slovníku u položek jako je desc a mesh ---> udělat pomocí třídy @dataclass
            
        19.9.
        TODO: stále neprostudován attr tak jak bych si představoval.
            Přijít na to, jak yaml parseru vnutit mé vlastní @dataclass.
            popřípadě načítata přeparsovat kompletně jinak _:(
            
            jde například o mesh...
                mesh:
                    mesh_file: ../00_mesh/square_1x1_40el.msh
                    
        23.9.
        TODO: zjistit jaká je správná validate po přečtení YAML souboru.
            @dataclass
            @attr.s
                <- jsou tyto dva dekorátory kompatibilní s tím, co tvořím staticky a bez nich? jak to zapsat pomocí těchto dekorátorů?
            
            zjistit všechny možné hodnoty načítání YAML (!třídy a třídy nahrazující dict) <-> ((popřípadě si nechat poradit, jak psát parser správně)) je moje dosavadní implementace nepoužítelná?
        
        TODO_visip: jak správně použít @action? moje pokusy selhaly, neočekávaný atribut 'evaluate=func' ???
        
                    
        POZNATKY:
            snaha tvořit třídy a číst data, tak aby mohla probíhat datová kontrola. Je to nezbytně nutné u všech atributů?
"""
