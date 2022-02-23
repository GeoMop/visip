import typing
import typing_inspect
import inspect
import builtins
import enum


class _ActionBase:
    pass

class TypeBase:
    # Future base class of all type hint classes
    pass

class _Empty(_ActionBase):
    pass
empty = _Empty()
# Singleton value marking empty arguments of the Lazy action


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class DataClassBase:
    """
    Base class to the dataclasses used in VISIP.
    Implement some common methods for hashing, and serialization.
    """
    pass


valid_base_types = (bool, int, float, complex, str)
valid_data_types = (*valid_base_types, list, dict, DataClassBase)


class DType:
    def typevar_set(self):
        """
        Returns set of all TypeVars from type.
        :return:
        """
        return set()


class DTypeBase(DType):
    pass


class DTypeGeneric(DType):
    def get_args(self):
        assert False, "Not implemented."

    def typevar_set(self):
        ret = set()
        for arg in self.get_args():
            ret.update(arg.typevar_set())
        return ret


class Int(DTypeBase, metaclass=Singleton):
    pass


class Float(DTypeBase, metaclass=Singleton):
    pass


class Bool(DTypeBase, metaclass=Singleton):
    pass


class Str(DTypeBase, metaclass=Singleton):
    pass


class Class(DTypeBase):
    def __init__(self, module, name, origin_type):
        self.module = module
        self.name = name
        self.origin_type = origin_type

class Enum(DTypeBase):
    def __init__(self, module, name, origin_type):
        self.module = module
        self.name = name
        self.origin_type = origin_type


class List(DTypeGeneric):
    def __init__(self, arg):
        self.arg = arg

    def get_args(self):
        return [self.arg]


class Dict(DTypeGeneric):
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def get_args(self):
        return [self.key, self.value]


class Tuple(DTypeGeneric):
    def __init__(self, *args):
        self.args = args

    def get_args(self):
        return self.args


class Union(DTypeGeneric):
    def __init__(self, *args):
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

    def get_args(self):
        return self.args


class Const(DTypeGeneric):
    def __init__(self, arg):
        if not isinstance(arg, DType):
            arg = from_typing(arg)
        if isinstance(arg, Const):
            self.arg = arg.arg
        else:
            self.arg = arg
        assert not isinstance(self.arg, Const)

    def get_args(self):
        return [self.arg]


class TypeVar(DTypeBase):
    def __init__(self, origin_type=None):
        if origin_type is None:
            origin_type = typing.TypeVar("T")
        self.origin_type = origin_type

    def __hash__(self):
        return self.origin_type.__hash__()

    def __eq__(self, other):
        if isinstance(other, TypeVar):
            return other.origin_type is self.origin_type
        return False

    def typevar_set(self):
        return {self}


class NewType(DTypeBase):
    def __init__(self, origin_type):
        self.origin_type = origin_type
        self.supertype = from_typing(origin_type.__supertype__)

    def typevar_set(self):
        return self.supertype.typevar_set()


class Any(DTypeBase, metaclass=Singleton):
    pass


class NoneType(DTypeBase, metaclass=Singleton):
    pass


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


    # TypeVar
    if typing_inspect.is_typevar(type):
        return TypeVar(type)


    # NewType
    if typing_inspect.is_new_type(type):
        return NewType(type)


    # Tuple
    if typing_inspect.is_tuple_type(type):
        args = []
        for a in typing_inspect.get_args(type, evaluate=True):
            args.append(from_typing(a))
        return Tuple(*args)


    # Union
    if typing_inspect.is_union_type(type):
        args = []
        for a in typing_inspect.get_args(type, evaluate=True):
            args.append(from_typing(a))
        return Union(*args)


    origin = typing_inspect.get_origin(type)

    # List
    if origin in [list, typing.List]:
        return List(from_typing(typing_inspect.get_args(type, evaluate=True)[0]))

    # Dict
    if origin in [dict, typing.Dict]:
        args = typing_inspect.get_args(type, evaluate=True)
        return Dict(from_typing(args[0]), from_typing(args[1]))

    # Const
    # No more supported
    # if origin is dtype.Constant:
    #     return Const(from_typing(typing_inspect.get_args(type, evaluate=True)[0]))


    # Class
    if inspect.isclass(type) and issubclass(type, DataClassBase):
        return Class(type.__module__, type.__name__, type)

    # Enum
    if inspect.isclass(type) and issubclass(type, enum.IntEnum):
        return Enum(type.__module__, type.__name__, type)


    # Any
    if type is typing.Any:
        return Any()


    # NoneType
    if type is builtins.type(None):
        return NoneType()


    #raise TypeError("Not supported type.")
    return type


def to_typing(type):
    # base
    if isinstance(type, Int):
        return int

    if isinstance(type, Float):
        return float

    if isinstance(type, Bool):
        return bool

    if isinstance(type, Str):
        return str


    # TypeVar
    if isinstance(type, TypeVar):
        return type.origin_type


    # NewType
    if isinstance(type, NewType):
        return type.origin_type


    # Tuple
    if isinstance(type, Tuple):
        args = []
        for a in type.args:
            args.append(to_typing(a))
        return typing.Tuple[tuple(args)]


    # Union
    if isinstance(type, Union):
        args = []
        for a in type.args:
            args.append(to_typing(a))
        return typing.Union[tuple(args)]


    # List
    if isinstance(type, List):
        return typing.List[to_typing(type.arg)]

    # Dict
    if isinstance(type, Dict):
        return typing.Dict[to_typing(type.key), to_typing(type.value)]

    # Const
    if isinstance(type, Const):
        #return dtype.Constant[to_typing(type.arg)]
        assert False, "Unable to return unambiguous value."


    # Class
    if isinstance(type, Class):
        return type.origin_type

    # Enum
    if isinstance(type, Enum):
        return type.origin_type


    # Any
    if isinstance(type, Any):
        return typing.Any

    # NoneType
    if isinstance(type, NoneType):
        return builtins.type(None)


    raise TypeError("Not supported type.")


def is_equaltype(type, other):
    # Const
    if isinstance(type, Const):
        if isinstance(other, Const):
            return is_equaltype(type.arg, other.arg)
        elif isinstance(type.arg, Union):
            return is_equaltype(Union(type), other)
        elif isinstance(other, Union):
            return is_equaltype(other, type)

    # Any
    elif isinstance(type, Any):
        return other is type

    # TypeVar
    elif isinstance(type, TypeVar):
        if isinstance(other, TypeVar):
            return type.origin_type is other.origin_type

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
        if isinstance(other, NewType):
            return type.origin_type is other.origin_type

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
        return True, _vm_merge(var_map, {type: Union(subtype)})

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
        if isinstance(type, NewType):
            if type.origin_type is subtype.origin_type:
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
            var_map[t] = Union(var_map[t], b[t])
        else:
            var_map[t] = Union(b[t])
    return var_map


class TypeInspector:
    def is_constant(self, type):
        return isinstance(type, Const)

    def constant_type(self, type):
        return type.arg

    def have_attributes(self, type):
        return isinstance(type, Any) or isinstance(type, Class) or isinstance(type, Dict) or \
               type is typing.Any or (inspect.isclass(type) and issubclass(type, DataClassBase)) or type in [typing.Dict, dict]


def extract_type_var(type):
    """
    Returns set of all TypeVars from composed type.
    :param type:
    :return:
    """
    if isinstance(type, DType):
        return type.typevar_set()
    return set()


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
