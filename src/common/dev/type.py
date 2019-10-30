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
from typing import Union, List


# valid_base_types = (bool, int, float, complex, str)
BasicType = Union[bool, int, float, complex, str]
DataType = Union[BasicType, List['DataType'], 'DataClassBase']


# Just an empty data class to check the types.
class DataClassBase:
    pass


def is_base_type(dtype):
    return is_subtype(dtype, BasicType)


def is_subtype(dtype, type_spec):
    return pytypes.is_subtype(dtype, type_spec)


def closest_common_ancestor(*cls_list):
    mros = [reversed(inspect.getmro(cls)) for cls in cls_list]
    ancestor = None
    for ancestors in itertools.zip_longest(*mros):
        if len(set(ancestors)) == 1:
            ancestor = ancestors[0]
        else: break
    return ancestor
