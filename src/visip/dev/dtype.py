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
#import pytypes
import itertools
import inspect
from . import tools
import typing
import typing_inspect
import enum
from . import base
from typing import *
################################################################################################


BasicType = typing.Union[bool, int, float, complex, str]
valid_base_types = (bool, int, float, complex, str)

DataType = typing.Union[BasicType, typing.List['DataType'], typing.Dict['DataType', 'DataType'], typing.Tuple['DataType', ...], 'DataClassBase']
# All valid data types that can be passed between VISIP actions.
# TODO: check that all type check methods work with this definition.
# ?? Can pytypes of typing inspect work with this recursive type definition.
# We can possibly simplify code in wrap.unwrap_type.


ConstantValueType = typing.TypeVar('ConstantValueType')

class Constant(typing.Generic[ConstantValueType]):
    """
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
#     Wrapper for constant values. I.e. values that are not results of other actions.
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



class TypeInspector_36:
    """
    Dropback solution for python < 3.7.4.
    """
    map_origin = {typing.List: list, typing.Dict: dict, typing.Tuple: tuple, typing.Union: typing.Union, Constant: Constant}
    origin_typing = {list: typing.List, dict: typing.Dict, tuple: typing.Tuple, typing.Union: typing.Union}

    def is_any(self, xtype):
        return xtype is typing.Any

    def is_base_type(self, xtype):
        """ True for basic, i.e. scalar types."""
        return xtype in valid_base_types

    def is_enum(self, xtype):
        try:
            return issubclass(xtype, enum.IntEnum)
        except:
            return False

    def get_origin(self, xtype):
        """
        Returns: list, dict, tuple, typing.Union (also for typing.Optional),
        None for: scalar types, None, and typing.Any
        Compatible with Python 3.8.
        :param xtype: a typehint.
        :return:
        """
        origin = typing_inspect.get_origin(xtype)
        return self.map_origin.get(origin, None)

    def get_typing_origin(self, xtype):
        return self.origin_typing[self.get_origin(xtype)]

    def get_args(self, xtype):
        return typing_inspect.get_last_args(xtype)

    def is_dataclass(self, xtype):
        try:
            return issubclass(xtype, DataClassBase)
        except:
            return False


    def is_constant(self, xtype):
        return self.get_origin(xtype) is Constant

    def constant_type(self, xtype):
        return self.get_args(xtype)[0]

    def is_callable(self, xtype):
        try:
            return issubclass(xtype, base._ActionBase)
        except:
            return False

    def is_subtype(self, xtype, type_spec):
        """
        pytypes works only for 3.6
        TODO!!! implement
        :param xtype:
        :param type_spec:
        :return:
        """
        return False


class TypeInspector_37(TypeInspector_36):
    """
    Solution for 3.7.4 <= python < 3.8.
    """
    def get_origin(self, xtype):
        """
        Returns: list, dict, tuple, typing.Union (also for typing.Optional),
        None for: scalar types, None, and typing.Any
        Compatible with Python 3.8.
        :param xtype: a typehint.
        :return:
        """
        return typing_inspect.get_origin(xtype)

    def get_args(self, xtype):
        return typing_inspect.get_args(xtype)


@tools.fallback(TypeInspector_36, before_version=(3, 7, 4))
@tools.fallback(TypeInspector_37, before_version=(3, 8, 0))
class TypeInspector(TypeInspector_37):
    """
    Based typing inspection, which is supported for python >= 3.8
    """

    # def is_any(self, xtype):
    #     return xtype is typing.Any
    #
    # def is_base_type(self, xtype):
    #     """ True for basic, i.e. scalar types."""
    #     return self.isinstance(xtype, valid_base_types)

    def get_origin(self, xtype):
        """
        Returns: list, dict, tuple, typing.Union (also for typing.Optional),
        None for: scalar types, None, and typing.Any
        Compatible with Python 3.8.
        :param xtype: a typehint.
        :return:
        """
        return typing.get_origin(xtype)


    def get_args(self, xtype):
        return typing.get_args(xtype)







def closest_common_ancestor(*cls_list):
    mros = [reversed(inspect.getmro(cls)) for cls in cls_list]
    ancestor = None
    for ancestors in itertools.zip_longest(*mros):
        if len(set(ancestors)) == 1:
            ancestor = ancestors[0]
        else: break
    return ancestor
