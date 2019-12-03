"""
Typing for action parameters and outcomes.

Strategy A: Use standard typing, protocols and the pytypes library.
Strategy B: If the previous become insufficient implemnt own scheme for composite types.

TODO:
1. Correct subtyping for lists.
Original idea to use Python typing support was not applicable as the typing
mechanisms currently works only for static checking and work with then in runtime is still in
heavy development.
"""
import pytypes
import itertools
import inspect
from . import tools
from typing import Union, List

# valid_base_types = (bool, int, float, complex, str)
BasicType = Union[bool, int, float, complex, str]
DataType = Union[BasicType, List['DataType'], 'DataClassBase']


# class DataBase:
#     def hash(self):
#         pass
#
#     def
#
# class List(list, DataBase):
#     ..


# Just an empty data class to check the types.
class DataClassBase:

    @tools.classproperty
    def yaml_tag(cls):
        """
        Provides yaml_tag for class resolution in yaml.load.
        The class has to be registered.
        :return:
        """
        return '{}'.format(cls.__name__)

    @tools.classproperty
    def yaml_module(cls):
        '''
        Provides name od the module.
        :return:
        '''
        return '{}'.format(cls.__module__)

    def from_yaml(self):
        pass

    @classmethod
    def to_yaml(cls, representer, node):
        # yaml_tag + represent like dict
        # odkaz z 13.10. ve sdílené složce
        # print(dir(node))
        if node.yaml_module == 'visip.action.constructor':
            return representer.represent_mapping('!{}'.format(node.yaml_tag), node.__dict__)
        else:
            return representer.represent_mapping('!{}.{}'.format(node.yaml_module, node.yaml_tag), node.__dict__)


def is_base_type(dtype):
    return is_subtype(dtype, BasicType)


def is_subtype(dtype, type_spec):
    try:
       ok = pytypes.is_subtype(dtype, type_spec)
    except TypeError:
        return False
    return ok



def closest_common_ancestor(*cls_list):
    mros = [reversed(inspect.getmro(cls)) for cls in cls_list]
    ancestor = None
    for ancestors in itertools.zip_longest(*mros):
        if len(set(ancestors)) == 1:
            ancestor = ancestors[0]
        else:
            break
    return ancestor
