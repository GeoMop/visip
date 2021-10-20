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
    def __init__(self, module, name, origin_type):
        self.module = module
        self.name = name
        self.origin_type = origin_type


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


class Const:
    def __init__(self, arg):
        self.arg = arg


class TypeVar:
    def __init__(self, name):
        self.name = name


def from_typing(type):
    t, _ = from_typing_map(type, {})
    return t


def from_typing_map(type, var_map):
    print(type)
    # base
    if type is int:
        return Int(), var_map

    if type is float:
        return Float(), var_map

    if type is bool:
        return Bool(), var_map

    if type is str:
        return Str(), var_map


    # TypeVar
    if typing_inspect.is_typevar(type):
        if type in var_map:
            return var_map[type], var_map
        t = TypeVar(type.__name__)
        var_map = var_map.copy()
        var_map[type] = t
        return t, var_map


    # Tuple
    if typing_inspect.is_tuple_type(type):
        args = []
        xx = typing_inspect.get_args(type, evaluate=True)
        for a in typing_inspect.get_args(type, evaluate=True):
            t, var_map = from_typing_map(a, var_map)
            args.append(t)
        return Tuple(args), var_map


    # Union
    if typing_inspect.is_union_type(type):
        args = []
        for a in typing_inspect.get_args(type, evaluate=True):
            t, var_map = from_typing_map(a, var_map)
            args.append(t)
        return Union(args), var_map


    origin = typing_inspect.get_origin(type)

    # List
    if origin in [list, typing.List]:
        t, var_map = from_typing_map(typing_inspect.get_args(type, evaluate=True)[0], var_map)
        return List(t), var_map

    # Dict
    if origin in [dict, typing.Dict]:
        args = typing_inspect.get_args(type, evaluate=True)
        k, var_map = from_typing_map(args[0], var_map)
        v, var_map = from_typing_map(args[1], var_map)
        return Dict(k, v), var_map

    # Const
    if origin is dtype.Constant:
        t, var_map = from_typing_map(typing_inspect.get_args(type, evaluate=True)[0], var_map)
        return Const(t), var_map


    # Class
    if issubclass(type, dtype.DataClassBase):
        return Class(type.__module__, type.__name__, type), var_map


    raise TypeError("Not supported type.")


def is_subtype(type, typeinfo):
    b, _ = is_subtype_map(type, typeinfo, {})
    return b


def is_subtype_map(type, typeinfo, var_map, const=False):
    # var_map is not yet fully implemented

    # if type is Const, call recursively with const=True
    if isinstance(type, Const):
        return is_subtype_map(type.arg, typeinfo, var_map, True)

    # if typeinfo is Const, check if const==True then call recursively
    elif isinstance(typeinfo, Const):
        if const:
            return is_subtype_map(type, typeinfo.arg, var_map, True)

    # if typeinfo is TypeVar, always True
    elif isinstance(typeinfo, TypeVar):
        return True, []

    # if type is Union, must be satisfied for all args
    elif isinstance(type, Union):
        vm_list = []
        for arg in type.args:
            b, vm = is_subtype_map(arg, typeinfo, var_map, const)
            if not b:
                return False, []
            vm_list = _vm_merge(vm_list, vm)
        return True, vm_list

    # if typeinfo is Union, must be satisfied for at least one arg
    elif isinstance(typeinfo, Union):
        for arg in typeinfo.args:
            b, vm = is_subtype_map(type, arg, var_map, const)
            if b:
                return True, []

    # if type is Int, typeinfo must be Int
    elif isinstance(type, Int):
        if isinstance(typeinfo, Int):
            return True, [var_map]

    # if type is Float, typeinfo must be Float
    elif isinstance(type, Float):
        if isinstance(typeinfo, Float):
            return True, [var_map]

    # if type is Bool, typeinfo must be Bool or Int
    elif isinstance(type, Bool):
        if isinstance(typeinfo, (Bool, Int)):
            return True, [var_map]

    # if type is Str, typeinfo must be Str
    elif isinstance(type, Str):
        if isinstance(typeinfo, Str):
            return True, [var_map]

    # if type is Class, typeinfo must be Class and type.origin_type must be subclass of typeinfo.origin_type
    elif isinstance(type, Class):
        if isinstance(typeinfo, Class) and issubclass(type.origin_type, typeinfo.origin_type):
            return True, [var_map]

    # if type is Tuple, typeinfo must be Tuple and all args must be subtype
    elif isinstance(type, Tuple):
        if isinstance(typeinfo, Tuple) and len(type.args) == len(typeinfo.args):
            vm_list = [var_map]
            for arg, arginfo in zip(type.args, typeinfo.args):
                new_vm_list = []
                b, vm = is_subtype_map(arg, arginfo, var_map, const)
                if not b:
                    return False, []
            return True, vm_list

    # if type is List, typeinfo must be List and args must be subtype
    elif isinstance(type, List):
        if isinstance(typeinfo, List):
            b, vm = is_subtype_map(type.arg, typeinfo.arg, var_map, const)
            if b:
                return True, [var_map]

    # if type is Dict, typeinfo must be Dict and keys, values must be subtype
    elif isinstance(type, Dict):
        if isinstance(typeinfo, Dict):
            b, vm = is_subtype_map(type.key, typeinfo.key, var_map, const)
            if b:
                b, vm = is_subtype_map(type.value, typeinfo.value, var_map, const)
                if b:
                    return True, [var_map]

    return False, []


def _vm_merge(vm1, vm2):
    return vm1 + vm2
