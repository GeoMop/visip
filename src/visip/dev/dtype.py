import typing
import typing_inspect
import inspect
import builtins
import enum
import attr


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
    @classmethod
    def set_visip_type(cls, type):
        print("Set visip: ", cls, " = ", type)
        cls.__visip_type = type
        return type

    @classmethod
    def visip_type(cls):
        try:
            return cls.__visip_type
        except AttributeError:
            return None

class DType:
    """
    Base class for all typing classes.
    """
    def typevar_set(self):
        """
        Returns set of all TypeVars from type.
        :return:
        """
        return set()


class DTypeBase(DType):
    """
    Base class for elementary typing classes.
    """
    pass


class DTypeGeneric(DType):
    """
    Base class for composed typing classes.
    """
    def get_args(self):
        assert False, "Not implemented."

    def typevar_set(self):
        ret = set()
        for arg in self.get_args():
            if isinstance(arg, DType):
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
    # Wrapper around various VISIP classes, in order to work with types as instances.

    @staticmethod
    def wrap(type:DataClassBase):
        visip_class = type.visip_type()
        if visip_class is None or visip_class.data_class is not type:
            visip_class = Class(type)
            type.set_visip_type(visip_class)

        return visip_class

    def __init__(self, data_class:DataClassBase):
        self.data_class = data_class

    def __repr__(self):
        return f"dtype.Class:{self.module}.{self.name}"

    @property
    def module(self):
        return self.data_class.__module__

    @property
    def name(self):
        return self.data_class.__name__


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
            if isinstance(a, Union):
                self.args.extend(a.args)
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
        self.arg = arg
        assert not isinstance(self.arg, Const)

    def get_args(self):
        return [self.arg]


class TypeVar(DTypeBase):
    def __init__(self, origin_type=None, name="T", converted_from_none=False):
        if origin_type is None:
            origin_type = typing.TypeVar(name)
        else:
            assert typing_inspect.is_typevar(origin_type)
        self.origin_type = origin_type
        self.converted_from_none = converted_from_none

    def __hash__(self):
        return self.origin_type.__hash__()

    def __eq__(self, other):
        if isinstance(other, TypeVar):
            return other.origin_type is self.origin_type
        return False

    def typevar_set(self):
        return {self}


class NewType(DTypeBase):
    def __init__(self, supertype, name=""):
        if isinstance(supertype, DType):
            if supertype.typevar_set():
                raise TypeError("TypeVars are not allowed in NewType.")
            self.origin_type = None
            self.supertype = supertype
            self.name = name
        else:
            origin_type = supertype
            assert typing_inspect.is_new_type(origin_type)
            self.origin_type = origin_type
            self.supertype = from_typing(origin_type.__supertype__)
            if self.supertype.typevar_set():
                raise TypeError("TypeVars are not allowed in NewType.")
            self.name = origin_type.__name__


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


    # Class .. VISIP class must be directly subtype of ClassBase
    if inspect.isclass(type) and issubclass(type, DataClassBase):
         return Class.wrap(type)

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
        return type.data_class

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
            return type is other or (type.origin_type is not None and other.origin_type is not None and
                                     type.origin_type is other.origin_type)

    # Int, Float, Bool, Str, NoneType
    elif isinstance(type, (Int, Float, Bool, Str, NoneType)):
        return other is type

    # Class
    elif isinstance(type, Class):
        if isinstance(other, Class) and type.data_class is other.data_class:
            assert type is other
            # If assert holds we can simplify the check
            return True
        return False

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
    b, _, _ = is_subtype_map(subtype, type, {}, {})
    return b


def is_subtype_map(subtype, type, var_map, restraints, check_const=True):
    """
    Checks if subtype is subtype of type.

    Add new type_var mapping to var_map.
    Type var mapping define lower limit of TypeVar, for concrete TypeVar may be raised, like T -> Int to T -> Union[Int, Str].
    Type var mapping appear if type is TypeVar, for example if type is TypeVar(T) and subtype is Int(),
    than mapping TypeVar(T) -> Int() is created.

    Add new restraint to restraints.
    Type var restraints define upper limit of TypeVar, for concrete TypeVar may be lowered, like T -> Union[Int, Str] to T -> Int.
    Type var restraints appear if subtype is TypeVar, for example if subtype is TypeVar(T) and type is Int(),
    than restraint TypeVar(T) -> Int() is created.

    :param subtype:
    :param type:
    :param var_map: {type_var: List[int], ...}
    :param restraints: {type_var: List[int], ...}
    :param check_const: if True and type is Const, than subtype must be Const
    :return: (is_subtype, var_map, restraints)
    """

    # if check_const is True and type is Const, than subtype must be Const
    if isinstance(type, Const) and check_const:
        if isinstance(subtype, Const):
            return is_subtype_map(subtype.arg, type.arg, var_map, restraints, False)
        elif not check_const:
            return is_subtype_map(subtype, type.arg, var_map, restraints, False)
        else:
            return False, {}, {}

    # if subtype is Const, call recursive
    elif isinstance(subtype, Const):
        return is_subtype_map(subtype.arg, type, var_map, restraints, False)

    # if type is NewType, than call recursively
    elif isinstance(type, NewType):
        return is_subtype_map(subtype, type.supertype, var_map, restraints, False)

    # if type is Any, always True
    elif isinstance(type, Any):
        return True, var_map, restraints

    # if type is TypeVar
    elif isinstance(type, TypeVar):
        # if exist restraint for type, check if subtype is subtype of that restraint
        if type in restraints:
            b, vm, restraints = is_subtype_map(subtype, restraints[type], var_map, restraints, False)
            if not b:
                return False, {}, {}
        if subtype != type:
            # add new mapping to var map
            var_map = _vm_merge(var_map, {type: subtype})
        return True, var_map, restraints

    # if subtype is TypeVar, append restraint
    elif isinstance(subtype, TypeVar):
        rest = {subtype: substitute_type_vars(type, restraints)[0]}
        b, restraints = _restraints_merge(restraints, rest)
        if not b:
            return False, {}, {}
        return True, var_map, restraints

    # if subtype is Union, must be satisfied for all args
    elif isinstance(subtype, Union):
        for arg in subtype.args:
            b, vm, rest = is_subtype_map(arg, type, var_map, restraints, False)
            if not b:
                return False, {}, {}
            var_map = _vm_merge(var_map, vm)
            b, restraints = _restraints_merge(restraints, rest)
            if not b:
                return False, {}, {}
        return True, var_map, restraints

    # if type is Union, must be satisfied for at least one arg
    elif isinstance(type, Union):
        for arg in type.args:
            b, vm, rest = is_subtype_map(subtype, arg, var_map, restraints, False)
            if b:
                b, restraints = _restraints_merge(restraints, rest)
                if not b:
                    return False, {}, {}
                return True, _vm_merge(var_map, vm), restraints

    # if type is NewType, than subtype must be appropriate NewType or subtype of supertype
    elif isinstance(subtype, NewType):
        if isinstance(type, NewType):
            if type is subtype or (type.origin_type is not None and subtype.origin_type is not None and
                                   type.origin_type is subtype.origin_type):
                return True, var_map, restraints
        else:
            return is_subtype_map(subtype.supertype, type, var_map, restraints, False)

    # if subtype is Int, Float, Str, NoneType, type must be the same
    elif isinstance(subtype, (Int, Float, Str, NoneType)):
        if type is subtype:
            return True, var_map, restraints

    # if subtype is Bool, type must be Bool or Int
    elif isinstance(subtype, Bool):
        if isinstance(type, (Bool, Int)):
            return True, var_map, restraints

    # if subtype is Class, type must be Class and subtype.origin_type must be subclass of type.origin_type
    elif isinstance(subtype, Class):
        if isinstance(type, Class) and issubclass(subtype.data_class, type.data_class):
            return True, var_map, restraints

    # if subtype is Enum, type must be Enum and subtype.origin_type must be subclass of type.origin_type or type must be Int
    elif isinstance(subtype, Enum):
        if isinstance(type, Enum) and issubclass(subtype.origin_type, type.origin_type) \
                or isinstance(type, Int):
            return True, var_map, restraints

    # if subtype is Tuple, type must be Tuple and all args must be subtype
    elif isinstance(subtype, Tuple):
        if isinstance(type, Tuple) and len(subtype.args) == len(type.args):
            for arg, arginfo in zip(subtype.args, type.args):
                b, vm, rest = is_subtype_map(arg, arginfo, var_map, restraints, False)
                if not b:
                    return False, {}, {}
                var_map = _vm_merge(var_map, vm)
                b, restraints = _restraints_merge(restraints, rest)
                if not b:
                    return False, {}, {}
            return True, var_map, restraints

    # if subtype is List, type must be List and args must be subtype
    elif isinstance(subtype, List):
        if isinstance(type, List):
            b, vm, rest = is_subtype_map(subtype.arg, type.arg, var_map, restraints, False)
            if b:
                b, restraints = _restraints_merge(restraints, rest)
                if not b:
                    return False, {}, {}
                return True, _vm_merge(var_map, vm), restraints

    # if subtype is Dict, type must be Dict and keys, values must be subtype
    elif isinstance(subtype, Dict):
        if isinstance(type, Dict):
            b, vm, rest = is_subtype_map(subtype.key, type.key, var_map, restraints, False)
            if b:
                var_map = _vm_merge(var_map, vm)
                b, restraints = _restraints_merge(restraints, rest)
                if not b:
                    return False, {}, {}
                b, vm, rest = is_subtype_map(subtype.value, type.value, var_map, restraints, False)
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
            var_map[t] = Union(var_map[t], b[t])
        else:
            var_map[t] = b[t]
    return var_map


def _restraints_merge(a, b):
    """
    This algorithm has O(n^2) complexity and allowing updates of the map and restraints during the recursive call
    could improve performance.
    :param a:
    :param b:
    :return: (is_mergeable, merge_result)
    """
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
    For example for Union[Int, Str] and Union[Int, Float] is common subtype Int.
    :param a:
    :param b:
    :return: (True, common_subtype) or (False, None)
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
            return True, Union(*com)
        else:
            return common_sub_type(a, Union(b))

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
        if isinstance(b, Class) and a.data_class is b.data_class:
            # TODO: more elaborate if we allow inheritance of VISIP classes
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
            return True, Tuple(*com_args)

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

    def have_attributes(self, type: 'dtype.DType'):
        return isinstance(type, Any) or isinstance(type, TypeVar) or isinstance(type, Class) or isinstance(type, Dict)


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


def substitute_type_vars(type, var_map, create_new=False, recursive=False):
    """
    If type contains type_var which is in var_map than substitutes it.
    If create_new is True than every type_var which is not in var_map is substituted with new type_var.
    If recursive is True than all type_vars in substituted type are substituted too.

    :param type:
    :param var_map: 
    :param create_new: 
    :param recursive: 
    :return: (substituted_type, updated_var_map)
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
            t = TypeVar(name=type.origin_type.__name__)
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
        return Tuple(*args), var_map

    # Union
    if isinstance(type, Union):
        args = []
        for a in type.args:
            t, var_map = substitute_type_vars(a, var_map, create_new, recursive)
            args.append(t)
        return Union(*args), var_map

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


valid_base_types = (bool, int, float, complex, str)
valid_data_types = (*valid_base_types, list, dict, DataClassBase)
