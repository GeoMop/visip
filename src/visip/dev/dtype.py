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
from typing import Any, Union, List, Dict, Tuple, Generic, TypeVar  # , GenericMeta


############################# typing - undocumented interface ##################################

def get_generic_args(generic_type):
    """
    Returns a tuple of type arguments of the input generic type.
    Returns None for a non-generic type.
    :param xtype: A type hint.
    :return: Tuple of types that are parameters of the input generic type.
    """
    # TODO: better check for generic types.
    if hasattr(generic_type, '__args__'):
        return generic_type.__args__
    else:
        return None


################################################################################################


BasicType = Union[bool, int, float, complex, str, None]
# valid_base_types = (bool, int, float, complex, str)

DataType = Union[BasicType, List['DataType'], Dict['DataType', 'DataType'], Tuple['DataType', ...], 'DataClassBase']
# All valid data types that can be passed between VISIP actions.
# TODO: check that all type check methods work with this definition.


ConstantValueType = TypeVar('ConstantValueType')


class Constant(Generic[ConstantValueType]):
    """
    Wrapper for constant values. I.e. values that are not results of other actions.
    """

    def __init__(self, val: ConstantValueType):
        self._value: ConstantValueType = val

    @property
    def value(self):
        return self._value

    @classmethod
    def inner_type(cls):
        return get_generic_args(cls)[0]


def is_constant(xtype):
    """
    Indicate that type is a generic Constant[...].
    TODO: Try to define it in better way.
    :param xtype:
    :return:
    """
    # is_subtype(xtype, Constant)
    return issubclass(xtype, Constant)


class DataClassBase:
    """
    Base class to the dataclasses used in VISIP.
    Implement some common methods for hashing, and serialization.
    """

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


def is_base_type(xtype):
    """ True for basic, i.e. scalar types."""
    return is_subtype(xtype, BasicType)


def is_subtype(xtype, type_spec):
    return pytypes.is_subtype(xtype, type_spec)
    # return pytypes.resolve_fw_decl(xtype, type_spec)


def closest_common_ancestor(*cls_list):
    mros = [reversed(inspect.getmro(cls)) for cls in cls_list]
    ancestor = None
    for ancestors in itertools.zip_longest(*mros):
        if len(set(ancestors)) == 1:
            ancestor = ancestors[0]
        else:
            break
    return ancestor
