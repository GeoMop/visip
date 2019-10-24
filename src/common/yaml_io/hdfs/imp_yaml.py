import sys
import ruamel.yaml

from common.code import wrap
import common.action_base as base
from src.common.action_base import ClassActionBase


# yaml_str = """\
# foo:
#   scalar: !Ref barr
#   mapping: !Select
#     a: !Ref 1
#     b: !Base64 A413
#   sequence: !Split
#   - !Ref baz
#   - !Split Multi word scalar
# """


class Generic:
    def __init__(self, tag, value, style=None):
        self._value = value
        self._tag = tag
        self._style = style

    # def __repr__(self):
    #     return self._tag + str(list(x for x in self._value.items()))
    #
    # def __getitem__(self, item):
    #     return self._value


class GenericScalar(Generic):
    @classmethod
    def to_yaml(self, representer, node):
        return representer.represent_scalar(node._tag, node._value)

    @staticmethod
    def construct(constructor, node):
        return constructor.construct_scalar(node)


tagy = ['!Coupling_Sequential', '!Flow_Darcy_MH', '!Petsc', '!vtk', '!Coupling_OperatorSplitting',
        '!Solute_Advection_FV', '!DualPorosity',
        '!SorptionMobile', '!FirstOrderReaction', '!SorptionImmobile']


class GenericMapping(Generic):
    @classmethod
    def to_yaml(self, representer, node):
        return representer.represent_mapping(node._tag, node._value)

    @staticmethod
    def construct(constructor, node):
        return constructor.construct_mapping(node, deep=True)


class GenericSequence(Generic):
    @classmethod
    def to_yaml(self, representer, node):
        return representer.represent_sequence(node._tag, node._value)

    @staticmethod
    def construct(constructor, node):
        return constructor.construct_sequence(node, deep=True)


def default_constructor(constructor, tag_suffix, node):
    generic = {
        ruamel.yaml.ScalarNode: GenericScalar,
        ruamel.yaml.MappingNode: GenericMapping,
        ruamel.yaml.SequenceNode: GenericSequence,
    }.get(type(node))
    if generic is None:
        raise NotImplementedError('Node: ' + str(type(node)))
    style = getattr(node, 'style', None)
    instance = generic.__new__(generic)
    yield instance
    state = generic.construct(constructor, node)
    instance.__init__(tag_suffix, state, style=style)


ruamel.yaml.add_multi_constructor('', default_constructor, Loader=ruamel.yaml.SafeLoader)

yaml = ruamel.yaml.YAML(typ='safe', pure=True)
yaml.default_flow_style = False
yaml.register_class(GenericScalar)
yaml.register_class(GenericMapping)
yaml.register_class(GenericSequence)

'''
načíst yaml do slovníku, vytvorit moji tridu a potom projít klíče ve slovníku ( ty tridy co mám uedelat ) a vytvorit je.
'''
with open("flow_input.yaml", 'r')as stream:
    data = yaml.load(stream)
    print(data)
    # print(data)
    # print('___')
    # print(slovnik['problem'].description)

    # pokus = ClassActionBase(slovnik)
    # print(pokus)

    yaml.dump(data, sys.stdout)  # dump lze i do složky!!
    # print('_')

#
# def create_classes(slovnik):
#     for keys, values in slovnik.items():
#         print(keys, values)
#         if isinstance(values, Generic):
#             ClassActionBase(values)
#             print(ClassActionBase(create_classes(slovnik)))
#
#
# create_classes(slovnik)


# base = yaml.load(yaml_str)
# base['bar'] = {
#     'name': 'abc',
#     'Resources': {
#         'RouteTableId': GenericScalar('!Ref', 'aaa'),
#         'VpcPeeringConnectionId': GenericScalar('!Ref', 'bbb'),
#         'yourname': 'dfw',
#         's': GenericSequence('!Split', ['a', GenericScalar('!Not', 'b'), 'c']),
#     }
# }
# yaml.dump(base, sys.stdout)
