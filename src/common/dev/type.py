"""
Typing for action parameters and outcomes.
Original idea to use Python typing support was not applicable as the typing
mechanisms currently works only for static checking and work with then in runtime is still in
heavy development.
"""

import itertools
import inspect
import typing
from numpy import array

valid_base_types = (bool, int, float, complex, str, )

#import hashlib
from typing import Union, List, NewType


BasicType = Union[bool, int, float, complex, str]
DataType = Union[BasicType, List['DataType'], 'DataClassBase']

# Just an empty data class to check the types.
class DataClassBase:
    pass


class List(typing.List):
    pass

def is_base_type(dtype):
    return dtype in valid_base_types

# class TypeBase:
#     def greater(self, other_type):
#         return False
#
#
# class Bool(TypeBase):
#     pass
#
# class Int(TypeBase):
#     pass
#
# class Float(TypeBase):
#     pass
#
# class Complex(TypeBase):
#     pass
#
# class Str(TypeBase):
#     pass
#
# class List(TypeBase, list):
#
#     def __init__(self, type):
#         super(list, self).__init__(type)
#
#     def greater(self, other_type):
#         return type(other_type) is List and self[0].greater(other_type[0])
#
# class Tuple(TypeBase, tuple):
#     def __init__(self, *args):
#         super(tuple, self).__init__(*args)
#
#     def greater(self, other_type):
#         if type(other_type) is Tuple and len(self) == len(other_type):
#             return min([s.greater(o) for s, o in zip(self, other_type)])
#         else:
#             return False
#
# class Union(TypeBase):
#     def __init__(self, *args):
#         self._possible_types = args
#
#     def greater(self, other_type):
#         return max([ s.grater(o) for s in self._possible_types])
#
#
# def is_subtype(a_type, b_type):
#      return b_type.greater(a_type)
#
#
# def common_type(*type_list):
#     pass
#
#

def closest_common_ancestor(*cls_list):
    mros = [reversed(inspect.getmro(cls)) for cls in cls_list]
    ancestor = None
    for ancestors in itertools.zip_longest(*mros):
        if len(set(ancestors)) == 1:
            ancestor = ancestors[0]
        else: break
    return ancestor
