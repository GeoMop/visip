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
import itertools
import inspect
import typing
from . import tools
from typing import Any, List, Dict, Tuple, TypeVar, Callable
# reusing some Python typehints, before we have own typing schema
################################################################################################

class TypeBase:
    # Future base class of all type hint classes
    pass

BasicType = typing.Union[bool, int, float, complex, str]
valid_base_types = (bool, int, float, complex, str)

DataType = typing.Union[BasicType, typing.List['DataType'], typing.Dict['DataType', 'DataType'], typing.Tuple['DataType', ...], 'DataClassBase']
# All valid data types that can be passed between VISIP actions.
# TODO: check that all type check methods work with this definition.
# ?? Can pytypes of typing inspect work with this recursive type definition.
# We can possibly simplify code in wrap.unwrap_type.

ConstantValueType = typing.TypeVar('ConstantValueType')

class Constant(typing.Generic[ConstantValueType]):
    """enum,
    Wrapper for constant values. I.e. values that are not results of other actions.
    TODO: Why and how to implement inner type.
    """
    def __init__(self, val: ConstantValueType):
        self._value: ConstantValueType = val


    @property
    def value(self):
        return self._value


    # @classmethod
    # def inner_type(cls):
    #     return TypeInspector().get_args(cls)[0]


Function = typing.Any
# class Fn(typing.Generic[ConstantValueType]):
#     """
#     Wrapper for constant values. I.e. values that are not results of other actions.enum,
#     TODO: Why and how to implement inner type.
#     """
#     def __init__(self, val: ConstantValueType):
#         self._value: ConstantValueType = val
#
#
#     @property
#     def value(self):
#         return self._value


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
        return '!{}'.format(cls.__name__)

    def from_yaml(self):
        pass

    def to_yaml(self):
        pass




def closest_common_ancestor(*cls_list):
    mros = [reversed(inspect.getmro(cls)) for cls in cls_list]
    ancestor = None
    for ancestors in itertools.zip_longest(*mros):
        if len(set(ancestors)) == 1:
            ancestor = ancestors[0]
        else: break
    return ancestor
