from visip.dev import dtype

import typing
import typing_inspect


class Int:
    pass


class Float:
    pass


class Bool:
    pass


class Str:
    pass


class Class:
    def __init__(self, module, name):
        self.module = module
        self.name = name


class List:
    def __init__(self, arg):
        self.arg = arg


class Dict:
    def __init__(self, key, value):
        self.key = key
        self.value = value


class Tuple:
    def __init__(self, args):
        self.args = args


class Union:
    def __init__(self, args):
        self.args = args


class VarType:
    def __init__(self, name):
        self.name = name


def from_typing(type):
    # base
    if type is int:
        return Int()

    if type is float:
        return Float()

    if type is bool:
        return Bool()

    if type is str:
        return Str()


    # VarType
    if typing_inspect.is_typevar(type):
        return VarType(type.__name__)


    # Tuple
    if typing_inspect.is_tuple_type(type):
        args = typing_inspect.get_args(type)
        return Tuple([from_typing(a) for a in args])


    # Union
    if typing_inspect.is_union_type(type):
        args = typing_inspect.get_args(type)
        return Union([from_typing(a) for a in args])


    origin = typing_inspect.get_origin(type)

    # List
    if origin in [list, typing.List]:
        return List(from_typing(typing_inspect.get_args(type)[0]))

    # Dict
    if origin in [dict, typing.Dict]:
        args = typing_inspect.get_args(type)
        return Dict(from_typing(args[0]), from_typing(args[1]))


    # Class
    if issubclass(type, dtype.DataClassBase):
        return Class(type.__module__, type.__name__)


def is_subtype(a, b):
    return False
