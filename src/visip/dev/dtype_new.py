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


class Int(metaclass=Singleton):
    pass


class Float(metaclass=Singleton):
    pass


class Bool(metaclass=Singleton):
    pass


class Str(metaclass=Singleton):
    pass


class Class:
    def __init__(self, module, name, origin_type):
        self.module = module
        self.name = name
        self.origin_type = origin_type

class Enum:
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


class Const:
    def __init__(self, arg):
        if isinstance(arg, Const):
            self.arg = arg.arg
        else:
            self.arg = arg
        assert not isinstance(self.arg, Const)


class TypeVar:
    def __init__(self, name):
        self.name = name


class NewType:
    def __init__(self, name, supertype):
        self.name = name
        self.supertype = supertype


class Any(metaclass=Singleton):
    pass


class NoneType(metaclass=Singleton):
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
    if isinstance(type, Const):
        if isinstance(other, Const):
            return is_equaltype(type.arg, other.arg)
        elif isinstance(type.arg, Union):
            return is_equaltype(Union([type]), other)
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


def is_subtype(subtype, type):
    b, _ = is_subtype_map(subtype, type, {})
    return b


def is_subtype_map(subtype, type, var_map, const=False):
    # if subtype is Const, call recursively with const=True
    if isinstance(subtype, Const):
        return is_subtype_map(subtype.arg, type, var_map, True)

    # if type is Const, check if const==True then call recursively
    elif isinstance(type, Const):
        if const:
            return is_subtype_map(subtype, type.arg, var_map, True)

    # if type is Any, always True
    elif isinstance(type, Any):
        return True, var_map

    # if type is TypeVar, always True
    elif isinstance(type, TypeVar):
        return True, _vm_merge(var_map, {type: Union([subtype])})

    # if subtype is Union, must be satisfied for all args
    elif isinstance(subtype, Union):
        for arg in subtype.args:
            b, vm = is_subtype_map(arg, type, var_map, const)
            if not b:
                return False, {}
            var_map = _vm_merge(var_map, vm)
        return True, var_map

    # if type is Union, must be satisfied for at least one arg
    elif isinstance(type, Union):
        for arg in type.args:
            b, vm = is_subtype_map(subtype, arg, var_map, const)
            if b:
                return True, _vm_merge(var_map, vm)

    # if type is NewType, than subtype must be appropriate NewType or subtype of supertype
    elif isinstance(subtype, NewType):
        if type is subtype:
            return True, var_map
        else:
            b, vm = is_subtype_map(subtype.supertype, type, var_map, const)
            if b:
                return True, _vm_merge(var_map, vm)

    # if subtype is Int, Float, Str, NoneType, type must be the same
    elif isinstance(subtype, (Int, Float, Str, NoneType)):
        if type is subtype:
            return True, var_map

    # if subtype is Bool, type must be Bool or Int
    elif isinstance(subtype, Bool):
        if isinstance(type, (Bool, Int)):
            return True, var_map

    # if subtype is Class, type must be Class and subtype.origin_type must be subclass of type.origin_type
    elif isinstance(subtype, Class):
        if isinstance(type, Class) and issubclass(subtype.origin_type, type.origin_type):
            return True, var_map

    # if subtype is Enum, type must be Enum and subtype.origin_type must be subclass of type.origin_type or type must be Int
    elif isinstance(subtype, Enum):
        if isinstance(type, Enum) and issubclass(subtype.origin_type, type.origin_type) \
                or isinstance(type, Int):
            return True, var_map

    # if subtype is Tuple, type must be Tuple and all args must be subtype
    elif isinstance(subtype, Tuple):
        if isinstance(type, Tuple) and len(subtype.args) == len(type.args):
            for arg, arginfo in zip(subtype.args, type.args):
                b, vm = is_subtype_map(arg, arginfo, var_map, const)
                if not b:
                    return False, {}
                var_map = _vm_merge(var_map, vm)
            return True, var_map

    # if subtype is List, type must be List and args must be subtype
    elif isinstance(subtype, List):
        if isinstance(type, List):
            b, vm = is_subtype_map(subtype.arg, type.arg, var_map, const)
            if b:
                return True, _vm_merge(var_map, vm)

    # if subtype is Dict, type must be Dict and keys, values must be subtype
    elif isinstance(subtype, Dict):
        if isinstance(type, Dict):
            b, vm = is_subtype_map(subtype.key, type.key, var_map, const)
            if b:
                var_map = _vm_merge(var_map, vm)
                b, vm = is_subtype_map(subtype.value, type.value, var_map, const)
                if b:
                    var_map = _vm_merge(var_map, vm)
                    return True, var_map

    return False, {}


def _vm_merge(a, b):
    var_map = a.copy()
    for t in b:
        if t in var_map:
            var_map[t] = Union([var_map[t], b[t]])
        else:
            var_map[t] = Union([b[t]])
    return var_map


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

    # NewType
    elif isinstance(type, NewType):
        ret.update(extract_type_var(type.supertype))

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
