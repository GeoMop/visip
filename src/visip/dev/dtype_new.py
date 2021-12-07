from visip.dev import dtype

import typing
import typing_inspect
import inspect
import builtins
import enum


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Type:
    pass


class Int(Type, metaclass=Singleton):
    pass


class Float(Type, metaclass=Singleton):
    pass


class Bool(Type, metaclass=Singleton):
    pass


class Str(Type, metaclass=Singleton):
    pass


class Class(Type):
    def __init__(self, module, name, origin_type):
        self.module = module
        self.name = name
        self.origin_type = origin_type

class Enum(Type):
    def __init__(self, module, name, origin_type):
        self.module = module
        self.name = name
        self.origin_type = origin_type


class List(Type):
    def __init__(self, arg):
        self.arg = arg


class Dict(Type):
    def __init__(self, key, value):
        self.key = key
        self.value = value


class Tuple(Type):
    def __init__(self, args):
        self.args = args


class Union(Type):
    def __init__(self, args):
        self.args = []

        # expand nested unions
        for a in args:
            b = a
            const = False
            if isinstance(b, Const):
                const = True
                while isinstance(b, Const):
                    b = b.arg
            if isinstance(b, Union):
                if const:
                    ext = [Const(a) for a in b.args]
                else:
                    ext = a.args
                self.args.extend(ext)
            else:
                self.args.append(a)

        # remove duplicates
        new_args = []
        for a in self.args:
            dup = False
            for na in new_args:
                if is_equaltype(na, a):
                    dup = True
                    break
            if not dup:
                new_args.append(a)
        self.args = new_args

        # check TypeVar count
        tv_count = 0
        tv_ind = -1
        for i, a in enumerate(self.args):
            if extract_type_var(a):
                tv_count += 1
                tv_ind = i
                if tv_count > 1:
                    raise TypeError("More than one argument with TypeVars in union.")

        # place TypeVar argument to the end
        if 0 <= tv_ind < len(self.args) - 1:
            a = self.args.pop(tv_ind)
            self.args.append(a)


class Const(Type):
    def __init__(self, arg):
        if isinstance(arg, Const):
            self.arg = arg.arg
        else:
            self.arg = arg
        assert not isinstance(self.arg, Const)


class TypeVar(Type):
    def __init__(self, name):
        self.name = name


class NewType(Type):
    def __init__(self, name, supertype):
        if extract_type_var(supertype):
            raise TypeError("TypeVars are not allowed in NewType.")

        self.name = name
        self.supertype = supertype


class Any(Type, metaclass=Singleton):
    pass


class NoneType(Type, metaclass=Singleton):
    pass


def from_typing(type):
    t, _, _ = from_typing_map(type, {}, {})
    return t


def from_typing_map(type, var_map, new_map):
    # base
    if type is int:
        return Int(), var_map, new_map

    if type is float:
        return Float(), var_map, new_map

    if type is bool:
        return Bool(), var_map, new_map

    if type is str:
        return Str(), var_map, new_map


    # TypeVar
    if typing_inspect.is_typevar(type):
        if type in var_map:
            return var_map[type], var_map, new_map
        t = TypeVar(type.__name__)
        var_map = var_map.copy()
        var_map[type] = t
        return t, var_map, new_map


    # NewType
    if typing_inspect.is_new_type(type):
        if type in new_map:
            return new_map[type], var_map, new_map
        supertype, var_map, new_map = from_typing_map(type.__supertype__, var_map, new_map)
        t = NewType(type.__name__, supertype)
        new_map = new_map.copy()
        new_map[type] = t
        return t, var_map, new_map


    # Tuple
    if typing_inspect.is_tuple_type(type):
        args = []
        for a in typing_inspect.get_args(type, evaluate=True):
            t, var_map, new_map = from_typing_map(a, var_map, new_map)
            args.append(t)
        return Tuple(args), var_map, new_map


    # Union
    if typing_inspect.is_union_type(type):
        args = []
        for a in typing_inspect.get_args(type, evaluate=True):
            t, var_map, new_map = from_typing_map(a, var_map, new_map)
            args.append(t)
        return Union(args), var_map, new_map


    origin = typing_inspect.get_origin(type)

    # List
    if origin in [list, typing.List]:
        t, var_map, new_map = from_typing_map(typing_inspect.get_args(type, evaluate=True)[0], var_map, new_map)
        return List(t), var_map, new_map

    # Dict
    if origin in [dict, typing.Dict]:
        args = typing_inspect.get_args(type, evaluate=True)
        k, var_map, new_map = from_typing_map(args[0], var_map, new_map)
        v, var_map, new_map = from_typing_map(args[1], var_map, new_map)
        return Dict(k, v), var_map, new_map

    # Const
    if origin is dtype.Constant:
        t, var_map, new_map = from_typing_map(typing_inspect.get_args(type, evaluate=True)[0], var_map, new_map)
        return Const(t), var_map, new_map


    # Class
    if inspect.isclass(type) and issubclass(type, dtype.DataClassBase):
        return Class(type.__module__, type.__name__, type), var_map, new_map

    # Enum
    if inspect.isclass(type) and issubclass(type, enum.IntEnum):
        return Enum(type.__module__, type.__name__, type), var_map, new_map


    # Any
    if type is typing.Any:
        return Any(), var_map, new_map


    # NoneType
    if type is builtins.type(None):
        return NoneType(), var_map, new_map


    raise TypeError("Not supported type.")


def to_typing(type):
    t, _, _ = to_typing_map(type, {}, {})
    return t


def to_typing_map(type, var_map, new_map):
    # base
    if isinstance(type, Int):
        return int, var_map, new_map

    if isinstance(type, Float):
        return float, var_map, new_map

    if isinstance(type, Bool):
        return bool, var_map, new_map

    if isinstance(type, Str):
        return str, var_map, new_map


    # TypeVar
    if isinstance(type, TypeVar):
        if type in var_map:
            return var_map[type], var_map, new_map
        t = typing.TypeVar(type.name)
        var_map = var_map.copy()
        var_map[type] = t
        return t, var_map, new_map


    # NewType
    if isinstance(type, NewType):
        if type in new_map:
            return new_map[type], var_map, new_map
        supertype, var_map, new_map = to_typing_map(type.supertype, var_map, new_map)
        t = typing.NewType(type.name, supertype)
        new_map = new_map.copy()
        new_map[type] = t
        return t, var_map, new_map


    # Tuple
    if isinstance(type, Tuple):
        args = []
        for a in type.args:
            t, var_map, new_map = to_typing_map(a, var_map, new_map)
            args.append(t)
        return typing.Tuple[tuple(args)], var_map, new_map


    # Union
    if isinstance(type, Union):
        args = []
        for a in type.args:
            t, var_map, new_map = to_typing_map(a, var_map, new_map)
            args.append(t)
        return typing.Union[tuple(args)], var_map, new_map


    # List
    if isinstance(type, List):
        t, var_map, new_map = to_typing_map(type.arg, var_map, new_map)
        return typing.List[t], var_map, new_map

    # Dict
    if isinstance(type, Dict):
        k, var_map, new_map = to_typing_map(type.key, var_map, new_map)
        v, var_map, new_map = to_typing_map(type.value, var_map, new_map)
        return typing.Dict[k, v], var_map, new_map

    # Const
    if isinstance(type, Const):
        t, var_map, new_map = to_typing_map(type.arg, var_map, new_map)
        return dtype.Constant[t], var_map, new_map


    # Class
    if isinstance(type, Class):
        return type.origin_type, var_map, new_map

    # Enum
    if isinstance(type, Enum):
        return type.origin_type, var_map, new_map


    # Any
    if isinstance(type, Any):
        return typing.Any, var_map, new_map

    # NoneType
    if isinstance(type, NoneType):
        return builtins.type(None), var_map, new_map


    raise TypeError("Not supported type.")


def is_equaltype(type, other):
    # Const
    def c2u(type):
        if isinstance(type, Const) and isinstance(type.arg, Union):
            return Union([Const(a) for a in type.arg.args])
        return type

    type = c2u(type)
    other = c2u(other)

    if isinstance(type, Const):
        if isinstance(other, Const):
            return is_equaltype(type.arg, other.arg)
        elif isinstance(other, Union):
            return is_equaltype(other, type)

    # Any
    elif isinstance(type, Any):
        return other is type

    # TypeVar
    elif isinstance(type, TypeVar):
        return type is other

    # Union
    elif isinstance(type, Union):
        if len(type.args) == 1:
            return is_equaltype(type.args[0], other)
        elif isinstance(other, Union) and len(type.args) == len(other.args):
            for arg in type.args:
                eq = False
                for oarg in other.args:
                    if is_equaltype(arg, oarg):
                        eq = True
                        break
                if not eq:
                    return False
            return True

    elif isinstance(other, Union):
        return is_equaltype(other, type)

    # NewType
    elif isinstance(type, NewType):
        if other is type:
            return True

    # Int, Float, Bool, Str, NoneType
    elif isinstance(type, (Int, Float, Bool, Str, NoneType)):
        return other is type

    # Class
    elif isinstance(type, Class):
        return isinstance(other, Class) and type.origin_type is other.origin_type

    # Enum
    elif isinstance(type, Enum):
        return isinstance(other, Enum) and type.origin_type is other.origin_type

    # Tuple
    elif isinstance(type, Tuple):
        if isinstance(other, Tuple) and len(type.args) == len(other.args):
            for arg, oarg in zip(type.args, other.args):
                if not is_equaltype(arg, oarg):
                    return False
            return True

    # List
    elif isinstance(type, List):
        if isinstance(other, List):
            return is_equaltype(type.arg, other.arg)

    # Dict
    elif isinstance(type, Dict):
        if isinstance(other, Dict):
            return is_equaltype(type.key, other.key) and is_equaltype(type.value, other.value)

    return False


def is_subtype(type, typeinfo):
    b, _, _ = is_subtype_map(type, typeinfo, {}, {})
    return b


def is_subtype_map(type, typeinfo, var_map, restraints, const=False):
    """
    Checks if type is subtype of typeinfo.
    Add new type_var mapping to var_map.
    Add new restraint to restraints.
    :param type:
    :param typeinfo:
    :param var_map: {type_var: List[int], ...}
    :param restraints: {type_var: List[int], ...}
    :param const:
    :return:
    """

    # if type is Const, call recursively with const=True
    if isinstance(type, Const):
        return is_subtype_map(type.arg, typeinfo, var_map, restraints, True)

    # if typeinfo is Const, check if const==True then call recursively
    elif isinstance(typeinfo, Const):
        if const:
            return is_subtype_map(type, typeinfo.arg, var_map, restraints, True)

    # if typeinfo is Any, always True
    elif isinstance(typeinfo, Any):
        return True, var_map, restraints

    # if typeinfo is TypeVar
    elif isinstance(typeinfo, TypeVar):
        if typeinfo in restraints:
            b, vm, rest = is_subtype_map(type, restraints[typeinfo], var_map, restraints, const)
            if not b:
                return False, {}, {}
            b, restraints = _restraints_merge(restraints, rest)
            if not b:
                return False, {}, {}
        return True, _vm_merge(var_map, {typeinfo: type}), restraints

    # if type is TypeVar, append restraint
    elif isinstance(type, TypeVar):
        rest = {type: substitute_type_vars(typeinfo, restraints)[0]}
        b, restraints = _restraints_merge(restraints, rest)
        if not b:
            return False, {}, {}
        return True, var_map, restraints

    # if type is Union, must be satisfied for all args
    elif isinstance(type, Union):
        for arg in type.args:
            b, vm, rest = is_subtype_map(arg, typeinfo, var_map, restraints, const)
            if not b:
                return False, {}, {}
            var_map = _vm_merge(var_map, vm)
            b, restraints = _restraints_merge(restraints, rest)
            if not b:
                return False, {}, {}
        return True, var_map, restraints

    # if typeinfo is Union, must be satisfied for at least one arg
    elif isinstance(typeinfo, Union):
        for arg in typeinfo.args:
            b, vm, rest = is_subtype_map(type, arg, var_map, restraints, const)
            if b:
                b, restraints = _restraints_merge(restraints, rest)
                if not b:
                    return False, {}, {}
                return True, _vm_merge(var_map, vm), restraints

    # if typeinfo is NewType, than type must be appropriate NewType or subtype of supertype
    elif isinstance(type, NewType):
        if typeinfo is type:
            return True, var_map, restraints
        else:
            b, vm, rest = is_subtype_map(type.supertype, typeinfo, var_map, restraints, const)
            if b:
                b, restraints = _restraints_merge(restraints, rest)
                if not b:
                    return False, {}, {}
                return True, _vm_merge(var_map, vm), restraints

    # if type is Int, Float, Str, NoneType, typeinfo must be the same
    elif isinstance(type, (Int, Float, Str, NoneType)):
        if typeinfo is type:
            return True, var_map, restraints

    # if type is Bool, typeinfo must be Bool or Int
    elif isinstance(type, Bool):
        if isinstance(typeinfo, (Bool, Int)):
            return True, var_map, restraints

    # if type is Class, typeinfo must be Class and type.origin_type must be subclass of typeinfo.origin_type
    elif isinstance(type, Class):
        if isinstance(typeinfo, Class) and issubclass(type.origin_type, typeinfo.origin_type):
            return True, var_map, restraints

    # if type is Enum, typeinfo must be Enum and type.origin_type must be subclass of typeinfo.origin_type or typeinfo must be Int
    elif isinstance(type, Enum):
        if isinstance(typeinfo, Enum) and issubclass(type.origin_type, typeinfo.origin_type) \
                or isinstance(typeinfo, Int):
            return True, var_map, restraints

    # if type is Tuple, typeinfo must be Tuple and all args must be subtype
    elif isinstance(type, Tuple):
        if isinstance(typeinfo, Tuple) and len(type.args) == len(typeinfo.args):
            for arg, arginfo in zip(type.args, typeinfo.args):
                b, vm, rest = is_subtype_map(arg, arginfo, var_map, restraints, const)
                if not b:
                    return False, {}, {}
                var_map = _vm_merge(var_map, vm)
                b, restraints = _restraints_merge(restraints, rest)
                if not b:
                    return False, {}, {}
            return True, var_map, restraints

    # if type is List, typeinfo must be List and args must be subtype
    elif isinstance(type, List):
        if isinstance(typeinfo, List):
            b, vm, rest = is_subtype_map(type.arg, typeinfo.arg, var_map, restraints, const)
            if b:
                b, restraints = _restraints_merge(restraints, rest)
                if not b:
                    return False, {}, {}
                return True, _vm_merge(var_map, vm), restraints

    # if type is Dict, typeinfo must be Dict and keys, values must be subtype
    elif isinstance(type, Dict):
        if isinstance(typeinfo, Dict):
            b, vm, rest = is_subtype_map(type.key, typeinfo.key, var_map, restraints, const)
            if b:
                var_map = _vm_merge(var_map, vm)
                b, restraints = _restraints_merge(restraints, rest)
                if not b:
                    return False, {}, {}
                b, vm, rest = is_subtype_map(type.value, typeinfo.value, var_map, restraints, const)
                if b:
                    var_map = _vm_merge(var_map, vm)
                    b, restraints = _restraints_merge(restraints, rest)
                    if not b:
                        return False, {}, {}
                    return True, var_map, restraints

    return False, {}, {}


def _vm_merge(a, b):
    var_map = a.copy()
    for t in b:
        if t in var_map:
            var_map[t] = Union([var_map[t], b[t]])
        else:
            var_map[t] = b[t]
    return var_map


def _restraints_merge(a, b):
    rest = a.copy()
    for r in b:
        if r in rest:
            bb, rest[r] = common_sub_type(rest[r], b[r])
            if not bb:
                return False, {}
        else:
            rest[r] = b[r]
    return True, rest


def common_sub_type(a, b):
    """
    Returns (True, common_subtype) if subtype exist otherwise (False, None).
    :param a:
    :param b:
    :return:
    """

    # Const
    if isinstance(a, Const):
        if isinstance(b, Const):
            bb, sub = common_sub_type(a.arg, b.arg)
        else:
            bb, sub = common_sub_type(a.arg, b)
        if bb:
            return True, Const(sub)

    elif isinstance(b, Const):
        return common_sub_type(b, a)

    # Any
    elif isinstance(a, Any):
        return True, b

    # TypeVar
    elif isinstance(a, TypeVar):
        if a is b:
            return True, a

    # Union
    elif isinstance(a, Union):
        if isinstance(b, Union):
            com = []
            for a_arg in a.args:
                for b_arg in b.args:
                    bb, sub = common_sub_type(a_arg, b_arg)
                    if bb:
                        com.append(sub)
            return True, Union(com)
        else:
            return common_sub_type(a, Union([b]))

    elif isinstance(b, Union):
        return common_sub_type(b, a)

    # NewType
    elif isinstance(a, NewType):
        if a is b:
            return True, a

    # Float, Str, NoneType
    elif isinstance(a, (Float, Str, NoneType)):
        if a is b:
            return True, a

    # Int
    elif isinstance(a, Int):
        if isinstance(b, (Int, Bool)):
            return True, a

    # Bool
    elif isinstance(a, Bool):
        if isinstance(b, Bool):
            return True, a
        elif isinstance(b, Int):
            return True, b

    # Class
    elif isinstance(a, Class):
        if isinstance(b, Class) and a.origin_type is b.origin_type:
            return True, a

    # Enum
    elif isinstance(a, Enum):
        if isinstance(b, Enum) and a.origin_type is b.origin_type:
            return True, a

    # Tuple
    elif isinstance(a, Tuple):
        if isinstance(b, Tuple) and len(a.args) == len(b.args):
            com_args = []
            for a_arg, b_arg in zip(a.args, b.args):
                bb, com_arg = common_sub_type(a_arg, b_arg)
                if not bb:
                    return False, None
                com_args.append(com_arg)
            return True, Tuple(com_args)

    # List
    elif isinstance(a, List):
        if isinstance(b, List):
            bb, com_arg = common_sub_type(a.arg, b.arg)
            if bb:
                return True, List(com_arg)

    # Dict
    elif isinstance(a, Dict):
        if isinstance(b, Dict):
            bb, com_key = common_sub_type(a.key, b.key)
            if bb:
                bb, com_val = common_sub_type(a.value, b.value)
                if bb:
                    return True, Dict(com_key, com_val)

    return False, None


class TypeInspector:
    def is_constant(self, type):
        return isinstance(type, Const)

    def constant_type(self, type):
        return type.arg


def extract_type_var(type):
    """
    Returns set of all TypeVars from composed type.
    :param type:
    :return:
    """
    ret = set()

    # TypeVar
    if isinstance(type, TypeVar):
        ret.add(type)

    # Tuple
    elif isinstance(type, Tuple):
        for a in type.args:
            ret.update(extract_type_var(a))

    # Union
    elif isinstance(type, Union):
        for a in type.args:
            ret.update(extract_type_var(a))

    # List
    elif isinstance(type, List):
        ret.update(extract_type_var(type.arg))

    # Dict
    elif isinstance(type, Dict):
        ret.update(extract_type_var(type.key))
        ret.update(extract_type_var(type.value))

    # Const
    elif isinstance(type, Const):
        ret.update(extract_type_var(type.arg))

    return ret


def check_type_var(input, output):
    """
    Returns True if all TypeVars at output there are also at input.
    :param input: input type
    :param output: output type
    :return:
    """
    in_set = extract_type_var(input)
    out_set = extract_type_var(output)
    return out_set.issubset(in_set)


def substitute_type_vars(type, var_map, create_new=False, recursive=False):
    """
    If type contains type_var which is in var_map than substitutes it.
    If create_new is True than every type_var is substituted with new type_var.
    """

    # TypeVar
    if isinstance(type, TypeVar):
        if type in var_map:
            if recursive:
                sub, var_map = substitute_type_vars(var_map[type], var_map, create_new, True)
                return sub, var_map
            else:
                return var_map[type], var_map
        if create_new:
            t = TypeVar(type.name)
            var_map = var_map.copy()
            var_map[type] = t
            return t, var_map
        else:
            return type, var_map

    # Tuple
    if isinstance(type, Tuple):
        args = []
        for a in type.args:
            t, var_map = substitute_type_vars(a, var_map, create_new, recursive)
            args.append(t)
        return Tuple(args), var_map

    # Union
    if isinstance(type, Union):
        args = []
        for a in type.args:
            t, var_map = substitute_type_vars(a, var_map, create_new, recursive)
            args.append(t)
        return Union(args), var_map

    # List
    if isinstance(type, List):
        t, var_map = substitute_type_vars(type.arg, var_map, create_new, recursive)
        return List(t), var_map

    # Dict
    if isinstance(type, Dict):
        k, var_map = substitute_type_vars(type.key, var_map, create_new, recursive)
        v, var_map = substitute_type_vars(type.value, var_map, create_new, recursive)
        return Dict(k, v), var_map

    # Const
    if isinstance(type, Const):
        t, var_map = substitute_type_vars(type.arg, var_map, create_new, recursive)
        return Const(t), var_map

    # others
    return type, var_map


def expand_var_map(var_map):
    """
    Expand all type_var in var_map recursively.
    :param var_map:
    :return:
    """
    exp_var_map = {}
    for var, t in var_map.items():
        sub, _ = substitute_type_vars(t, var_map, recursive=True)
        exp_var_map[var] = sub
    return exp_var_map
