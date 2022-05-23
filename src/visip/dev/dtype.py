import typing
import typing_inspect
import inspect
import builtins
import enum
import attrs
from . import exceptions

class _DummyClassBase:
    pass

class _ActionBase:
    pass


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
        #print("Set visip: ", cls, " = ", type)
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
    def typevar_set(self) -> 'TypeVar':
        """
        Returns set of all TypeVars that are part of the full type tree.
        :return:
        """
        return set()

    def code(self, make_rel_name:typing.Callable[[str,str], str]) -> str:
        """
        Code representation of the type.
        :param make_rel_name: Function getting module and name of the type and producing final name after applying
        aliases of the particular module.

        This is basic implementation for non generic types, using their module and name attributes.
        """
        return make_rel_name(self.__module__, self.__name__)

    def _eq_simplify(self):
        """
        Cast single member Union to the member type, for the equivalence.
        """
        return self

    def __eq__(self, other):
        return self._eq_simplify()._equal_(other._eq_simplify())


VISIP_Type = typing.Union[DType, _ActionBase]

class DTypeBase(DType):
    """
    Base class for non-composed typing classes.
    """
    pass


##############################
#  Singleton types
##############################


class DTypeSingleton(DTypeBase):
    """
    Singleton DTypes.
    """
    __singleton_types = {}
    __from_typing = {}
    @staticmethod
    def make(name:str, typing_type=None, subtypes:typing.List['DTypeSingleton']=None) -> 'DTypeSingleton':
        try:
            return DTypeSingleton.__singleton_types[name]
        except KeyError:
            singl_type_cls = type(f"{name}Type", (DTypeSingleton,), {})
            instance = singl_type_cls(name, typing_type, subtypes)
            if typing_type is not None:
                DTypeSingleton.__from_typing[typing_type] = instance
            return DTypeSingleton.__singleton_types.setdefault(name, instance)

    @staticmethod
    def from_typing(type):
        try:
            return DTypeSingleton.__from_typing.get(type, None)
        except TypeError as e:
            print("Warning: ", e)
        return type

    def __init__(self, name, typing_type, subtypes):
        self.__name__ = name
        self.typing_type = typing_type
        if subtypes is None:
            self.subtypes = {self}
        else:
            subtypes.add(self)
            self.subtypes = subtypes
        #self.__module__ = 'visip'

    def __hash__(self):
        return hash(self.__name__)

    def _equal_(self, other):
        return self is other

    def is_subtype(self, super_type):
        return self in super_type.subtypes



class _Empty(_ActionBase):
    pass
empty = _Empty()
# Singleton value marking empty arguments of the Lazy action

Bool = DTypeSingleton.make("Bool", bool)
Int = DTypeSingleton.make("Int", int, subtypes={Bool})
Float = DTypeSingleton.make("Float", float, subtypes={Bool, Int})
Str = DTypeSingleton.make("Str", str)
Bytes = DTypeSingleton.make("Bytes", bytes)
EmptyType = DTypeSingleton.make("EmptyType", inspect.Signature.empty)
"""
Produced by `from_typing` for an empty type annotation,
must be explicitelly treated by the caller,
not accepted by other functions.
"""

Any = DTypeSingleton.make("Any", typing.Any)
NoneType = DTypeSingleton.make("NoneType", builtins.type(None))


###################################
# DTypeBase - special
###################################


@attrs.frozen
class Class(DTypeBase):
    # Wrapper around various VISIP classes, in order to work with types as instances.
    data_class: DataClassBase

    @staticmethod
    def wrap(type:DataClassBase):
        visip_class = type.visip_type()
        if visip_class is None or visip_class.data_class is not type:
            visip_class = Class(type)
            type.set_visip_type(visip_class)

        return visip_class

    # def __init__(self, data_class:DataClassBase):
    #     self.data_class = data_class

    # def __hash__(self):
    #     return hash((self.__class__, self.data_class))

    # def __repr__(self):
    #     return f"dtype.Class:{self.module}.{self.name}"

    @property
    def __module__(self):
        return self.data_class.__module__

    @property
    def __name__(self):
        return self.data_class.__name__

    def _equal_(self, other):
        if isinstance(other, Class) and self.data_class is other.data_class:
            assert self is other
            # If assert holds we can simplify the check
            return True
        return False


@attrs.frozen
class Enum(DTypeBase):
    origin_type: enum.IntEnum

    @staticmethod
    def wrap(type: enum.IntEnum):
        if hasattr(type, "__visip_type"):
            return type.__visip_type
        else:
            visip_enum = Enum(type)
            type.__visip_type = visip_enum
            return visip_enum

    # def __init__(self, origin_type):
    #     self.origin_type = origin_type

    @property
    def __module__(self):
        return self.origin_type.__module__

    @property
    def __name__(self):
        return self.origin_type.__name__

    def _equal_(self, other):
        return isinstance(other, Enum) and self.origin_type is other.origin_type



class TypeVar(DTypeBase):
    """
    TypeVar
    """
    def __init__(self, origin_type=None, name="_TypeVar_"):
        if origin_type is None or origin_type is EmptyType:
            origin_type = typing.TypeVar(name)
        else:
            assert typing_inspect.is_typevar(origin_type)
        self.origin_type = origin_type

    @property
    def __name__(self):
        return self.origin_type.__name__

    @property
    def __module__(self):
        return self.origin_type.__module__

    def __hash__(self):
        return self.origin_type.__hash__()

    def __repr__(self):
        return f"TypeVar({self.origin_type})"

    def _equal_(self, other):
        if isinstance(other, TypeVar):
            return other.origin_type is self.origin_type
        return False



    def typevar_set(self):
        return {self}

    def code(self, make_rel_name):
        return empty


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


    def __hash__(self):
        return self.origin_type.__hash__()

    def __repr__(self):
        return f"NewType({self.origin_type}"

    def _equal_(self, other):
        #assert  self.origin_type is not None and other.origin_type is not None, f"None NewType: {self}, {other}"
        if isinstance(other, NewType):
            return self is other or (self.origin_type is not None and other.origin_type is not None and
                                     self.origin_type is other.origin_type)
        return False

################################
# DTypeGeneric
################################

class DTypeGeneric(DType):
    """
    Base class for composed typing classes.
    """
    def __init__(self, args: typing.List[VISIP_Type], n_args=0):
        if n_args:
            if len(args) != n_args:
                raise exceptions.ExcGenericArgs(f"Wrong number {len(args)} of the generic tyep {self.__name__}, expected: {n_args}.")

        # Unwrap Class and Enum
        args = [_unwrap_action_type(a) for a in args]
        for a in args:
            if not isinstance(a, (DType, _ActionBase)):
                raise exceptions.ExcNotDType(f"Argument {a} of generic type {self.__name__} is not DType (or Action).")
        self._args = args

    @property
    def __name__(self):
        return self.__class__.__name__


    def __hash__(self):
        return hash((self.__class__, *self.args))

    @property
    def args(self):
        return self._args

    def get_args(self) -> typing.List[DType]:
        """
        Return list of inner types.
        """
        return self.args

    def code(self, make_rel_name):
        # Overrides DType.code method.
        assert len(self.args) > 0
        args_code = ", ".join([type_code(arg, make_rel_name) for arg in self.args])
        origin_name = make_rel_name(self.__module__, self.__name__)
        code = f"{origin_name}({args_code})"
        return code


    def from_typing(self):
        return self.__class__(*(from_typing(a) for a in self.args))

    def typevar_set(self):
        ret = set()
        for arg in self.get_args():
            if isinstance(arg, DType):
                ret.update(arg.typevar_set())
        return ret

    def _equal_(self, other):
        if isinstance(other, self.__class__):
            return tuple(self.args) == tuple(other.args)
        return False


class List(DTypeGeneric):
    def __init__(self, *args):
        super().__init__(args, 1)

    @property
    def arg(self):
        return self.args[0]



class Dict(DTypeGeneric):
    def __init__(self, *args):
        super().__init__(args, 2)

    @property
    def key(self):
        return self.args[0]

    @property
    def value(self):
        return self.args[1]


class Tuple(DTypeGeneric):
    def __init__(self, *args):
        super().__init__(args)


class Union(DTypeGeneric):
    def __init__(self, *args):

        # expand nested unions, extract typevars
        _args = set()
        _tvars = []
        for a in args:
            if isinstance(a, Union):
                _args.update(a.args)
            else:
                _args.add(a)
        self._args = [_unwrap_action_type(a) for a in _args]   # omit DType check of args until we support Callable
        # TODO: upse super() after introduction of Callable, makes problems in lazy test.

        # check TypeVar count
        # TODO: too restrictive, inner typevars are not problem
        #  we should deal with this later in comparisons

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

    def _eq_simplify(self):
        if len(self.args) == 1:
            return self.args[0]
        return self

    def _equal_(self, other):
        if isinstance(other, Union) and len(self.args) == len(other.args):
            return set(self.args) == set(self.args)
        return False

class Const(DTypeGeneric):
    def __init__(self, *args):
        super().__init__(args, 1)
        assert not isinstance(self.args[0], Const)


class TypeInspector:
    @staticmethod
    def is_constant(type):
        return isinstance(type, Const)

    @staticmethod
    def constant_type(type):
        return type.args[0]

    @staticmethod
    def have_attributes(type: 'dtype.DType'):
        return type is Any or isinstance(type, (TypeVar, Class, Dict, Enum))

    @staticmethod
    def unwrap_type(type: Any):
        """
        Return wrapped type (DataClassBase or IntEnum) for
        the DummyAction wrapper. Return original type otherwise.
        """
        return type

def type_code(type_hint, make_rel_name):
    assert isinstance(type_hint, DType), type_hint
    if type_hint is EmptyType:
        # TODO: represent None as no type annotation, but it should be forbidden.
        return None
    return type_hint.code(make_rel_name)

    #raise Exception(f"No code representation for the type: {type_hint}")


def type_of_value(value):
    val_type = type(value)
    assert not isinstance(val_type, (_DummyClassBase, DType))
    basic_type = DTypeSingleton.from_typing(val_type)
    if basic_type is not None:
        return basic_type

    # Class
    if isinstance(value, DataClassBase):
        return Class.wrap(val_type)

    # Enum
    if isinstance(value, enum.IntEnum):
        return Enum.wrap(val_type)

    # Tuple
    if val_type is tuple:
        args = [type_of_value(v) for v in value]
        return Tuple(*args)

    # List
    if val_type is list:
        args = [type_of_value(v) for v in value]
        return List(Union(*args))

    # Dict
    if val_type is dict:
        keys = [type_of_value(v) for v in value.keys()]
        vals = [type_of_value(v) for v in value.values()]
        return Dict(Union(*keys), Union(*vals))

    if isinstance(value, _ActionBase):
        return _ActionBase

    raise TypeError(f"Value {value} of unsupported type: {val_type}")

def _unwrap_action_type(type: Any) -> DType:
    """
    Unwrap action types (i.e. Class and Enum) that are wrppaed into DummyAction.
    Pass through other types.
    """
    if isinstance(type, _DummyClassBase):
        try:
            data_class = type._action_value._data_class  # Class action
            assert issubclass(data_class, DataClassBase)
            return Class.wrap(data_class)
        except AttributeError:
            pass

        try:
            enum_class = type._action_value._enum_class  # Enum action
            assert issubclass(enum_class, enum.IntEnum)
            return Enum.wrap(enum_class)

        except AttributeError:
            pass
    return type


def from_typing(type):
    """
    Convert to dtype type:
    - from Python typing types
    - from VISIP Class and Enum actions (containing the underlying DataClass or IntEnum respectively)
      these actions are wrapped into DummyAction objects.
    - unwraping is done recursively even for the DType generic types
    Produce EmptyType instance for missing annotation (inspect.Signature.empty / inspect.Parameter.empty)
    must be treated by the caller.
    """
    if isinstance(type, DTypeGeneric):
        return type.from_typing()
    if isinstance(type, DType):
        return type

    if isinstance(type, _DummyClassBase):
        return _unwrap_action_type(type)

    basic_type = DTypeSingleton.from_typing(type)
    if basic_type is not None:
        return basic_type

    # Class
    if inspect.isclass(type) and issubclass(type, DataClassBase):
        return Class.wrap(type)

    # Enum
    if inspect.isclass(type) and issubclass(type, enum.IntEnum):
        return Enum.wrap(type)

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
        args = typing_inspect.get_args(type, evaluate=True)
        return List(from_typing(args[0]))

    # Dict
    if origin in [dict, typing.Dict]:
        args = typing_inspect.get_args(type, evaluate=True)
        return Dict(from_typing(args[0]), from_typing(args[1]))

    raise TypeError(f"Unsupported type: {type}")



# def to_typing(type):
#     # base
#     if isinstance(type, DTypeSingleton):
#         return type.typing_type
#
#     # TypeVar
#     if isinstance(type, TypeVar):
#         return type.origin_type
#
#
#     # NewType
#     if isinstance(type, NewType):
#         return type.origin_type
#
#
#     # Tuple
#     if isinstance(type, Tuple):
#         args = []
#         for a in type.args:
#             args.append(to_typing(a))
#         return typing.Tuple[tuple(args)]
#
#
#     # Union
#     if isinstance(type, Union):
#         args = []
#         for a in type.args:
#             args.append(to_typing(a))
#         return typing.Union[tuple(args)]
#
#
#     # List
#     if isinstance(type, List):
#         return typing.List[to_typing(type.arg)]
#
#     # Dict
#     if isinstance(type, Dict):
#         return typing.Dict[to_typing(type.key), to_typing(type.value)]
#
#     # Const
#     if isinstance(type, Const):
#         #return dtype.Constant[to_typing(type.arg)]
#         assert False, "Unable to return unambiguous value."
#
#
#     # Class
#     if isinstance(type, Class):
#         return type.data_class
#
#     # Enum
#     if isinstance(type, Enum):
#         return type.origin_type
#
#
#     # Any
#     if isinstance(type, Any):
#         return typing.Any
#
#     # NoneType
#     if isinstance(type, NoneType):
#         return builtins.type(None)
#
#
#     raise TypeError("Not supported type.")
#

def is_equaltype(type, other):
    return type == other


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

    # TODO: turn following to assert after fixing check_types of recursive workflow
    subtype = from_typing(subtype)

    # if check_const is True and type is Const, than subtype must be Const
    if isinstance(type, Const) and check_const:
        if isinstance(subtype, Const):
            return is_subtype_map(subtype.args[0], type.args[0], var_map, restraints, False)
        elif not check_const:
            return is_subtype_map(subtype, type.args[0], var_map, restraints, False)
        else:
            return False, {}, {}

    # if subtype is Const, call recursive
    elif isinstance(subtype, Const):
        return is_subtype_map(subtype.args[0], type, var_map, restraints, False)

    # if type is NewType, than call recursively
    elif isinstance(type, NewType):
        return is_subtype_map(subtype, type.supertype, var_map, restraints, False)

    # if type is Any, always True
    elif type is Any:
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
    elif isinstance(subtype, DTypeSingleton) and isinstance(type, DTypeSingleton) and subtype.is_subtype(type):
        return True, var_map, restraints

    # if subtype is Bool, type must be Bool or Int
    elif subtype is Bool:
        if isinstance(type, (Bool, Int)):
            return True, var_map, restraints

    # if subtype is Class, type must be Class and subtype.origin_type must be subclass of type.origin_type
    elif isinstance(subtype, Class):
        if isinstance(type, Class) and issubclass(subtype.data_class, type.data_class):
            return True, var_map, restraints

    # if subtype is Enum, type must be Enum and subtype.origin_type must be subclass of type.origin_type or type must be Int
    elif isinstance(subtype, Enum):
        if isinstance(type, Enum) and issubclass(subtype.origin_type, type.origin_type) \
                or type is Int:
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
            bb, sub = common_sub_type(a.args[0], b.args[0])
        else:
            bb, sub = common_sub_type(a.args[0], b)
        if bb:
            return True, Const(sub)

    elif isinstance(b, Const):
        return common_sub_type(b, a)

    # Any
    elif a is Any:
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

    # DTypeSingleton
    elif isinstance(a, DTypeSingleton) and isinstance(b, DTypeSingleton):
        if a is b:
            return True, a
        common = a.subtypes.intersection(b.subtypes)
        if len(common) == 0:
            return False, None
        elif len(common) == 2:  # Boll, Int
            return True, Int
        else:
            return True, Bool

    # # Int
    # elif a is Int:
    #     if b in {Int, Bool}:
    #         return True, a
    #
    # # Bool
    # elif isinstance(a, Bool):
    #     if isinstance(b, Bool):
    #         return True, a
    #     elif isinstance(b, Int):
    #         return True, b

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


def substitute_type_vars(type, var_map, create_new=False):
    """
    If type contains type_var which is in var_map than substitutes it.
    If create_new is True than every type_var which is not in var_map is substituted with new type_var.

    :param type:
    :param var_map: 
    :param create_new: 
    :return: (substituted_type, updated_var_map)
    """

    # TypeVar
    if isinstance(type, TypeVar):
        if type in var_map:
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
            t, var_map = substitute_type_vars(a, var_map, create_new)
            args.append(t)
        return Tuple(*args), var_map

    # Union
    if isinstance(type, Union):
        args = []
        for a in type.args:
            t, var_map = substitute_type_vars(a, var_map, create_new)
            args.append(t)
        return Union(*args), var_map

    # List
    if isinstance(type, List):
        t, var_map = substitute_type_vars(type.arg, var_map, create_new)
        return List(t), var_map

    # Dict
    if isinstance(type, Dict):
        k, var_map = substitute_type_vars(type.key, var_map, create_new)
        v, var_map = substitute_type_vars(type.value, var_map, create_new)
        return Dict(k, v), var_map

    # Const
    if isinstance(type, Const):
        t, var_map = substitute_type_vars(type.args[0], var_map, create_new)
        return Const(t), var_map

    # others
    return type, var_map


def expand_var_map(var_map):
    """
    Expand all type_var in var_map recursively.
    :param var_map:
    :return:
    """
    new_var_map = var_map
    var_map = {}
    while var_map != new_var_map:
        var_map = new_var_map
        var_map_list = list(var_map.items())
        new_var_map = {}
        for var, t in var_map_list:
            sub, _ = substitute_type_vars(t, var_map)
            new_var_map[var] = sub

    return var_map


valid_base_types = (bool, int, float, complex, str)
valid_data_types = (*valid_base_types, list, dict, DataClassBase)
