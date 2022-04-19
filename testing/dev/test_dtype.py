import pytest
from visip.dev.dtype import *
from visip.dev import exceptions

import typing
import typing_inspect
import builtins


class Aclass(DataClassBase):
    a: int = 0
    b: Str


def create_class():
    return Aclass

def test_singleton():
    class A(metaclass=Singleton):
        pass

    class B(A):
        pass

    class C(A):
        pass

    assert A() is A()
    assert B() is B()
    assert B() is not C()


def test_types():
    # Union
    t = Union(Int, Union(Str))
    assert len(t.args) == 2
    assert Int in t.args
    assert Str in t.args

    # t = Union(Int, Const(Union(Str)))
    # assert len(t.args) == 2
    # assert isinstance(t.args[0], Int)
    # assert isinstance(t.args[1], Const)
    # assert isinstance(t.args[1].arg, Str)

    t = Union(Int, Int)
    assert len(t.args) == 1
    assert t.args[0] is Int

    t = Union(Int, Union(Int))
    assert len(t.args) == 1
    assert t.args[0] is Int

    t = TypeVar(typing.TypeVar(name="T"))
    u = TypeVar(typing.TypeVar(name="U"))

    try:
        Union(t, u)
    except TypeError:
        pass
    else:
        assert False

    try:
        Union(t, Const(u))
    except TypeError:
        pass
    else:
        assert False

    # Const
    # t = Const(Const(Int))
    # assert isinstance(t, Const)
    # assert isinstance(t.arg, Int)

def test_type_of_value():

    # Enum
    class A(enum.IntEnum):
        a = 1

    class B(DataClassBase):
        pass

    class C(B):
        pass

    assert type_of_value(True) is Bool
    assert type_of_value(1) is Int
    assert type_of_value(1.0) is Float
    assert type_of_value("1") is Str
    assert type_of_value([1, 1.4, "1"]) == List(Union(Int, Float, Str))
    assert type_of_value({0:1, "f":1.4, 2:"1"}) == Dict(Union(Int, Str), Union(Int, Float, Str))
    assert type_of_value( (1, 1.4, "1") ) == Tuple(Int, Float, Str)
    assert type_of_value( ( A.a, B(), C()) ) == Tuple(Enum(A), Class(B), Class(C))

def test_from_typing():
    # bas
    assert from_typing(int) is Int
    assert from_typing(float) is Float
    assert from_typing(bool) is Bool
    assert from_typing(str) is Str

    # TypeVar
    t = typing.TypeVar(name="T")
    nt = from_typing(t)
    assert isinstance(nt, TypeVar)
    assert nt.origin_type is t

    tt = typing.Tuple[t, typing.List[t]]
    nt = from_typing(tt)
    assert nt.args[0].origin_type is nt.args[1].arg.origin_type

    # NewType
    t = typing.NewType("NewInt", int)
    nt = from_typing(t)
    assert isinstance(nt, NewType)
    assert nt.origin_type is t
    assert nt.supertype is Int

    tt = typing.Tuple[t, typing.List[t]]
    nt = from_typing(tt)
    assert nt.args[0].origin_type is nt.args[1].arg.origin_type

    # Tuple
    t = typing.Tuple[int, str]
    nt = from_typing(t)
    assert isinstance(nt, Tuple)
    assert nt.args[0] is Int
    assert nt.args[1] is Str

    # Union
    t = typing.Union[int, str]
    nt = from_typing(t)
    assert isinstance(nt, Union)
    assert len(nt.args) == 2
    assert Int in nt.args and Str in nt.args


    # List
    t = typing.List[int]
    nt = from_typing(t)
    assert isinstance(nt, List)
    assert nt.arg is  Int

    # Dict
    t = typing.Dict[int, str]
    nt = from_typing(t)
    assert isinstance(nt, Dict)
    assert nt.key is Int
    assert nt.value is Str

    # Const
    with pytest.raises(exceptions.ExcNotDType):
        Const(int)
    t = Const(Int)
    nt = from_typing(t)
    assert isinstance(nt, Const)
    assert nt.args[0] is Int

    # Class
    a_class = create_class()
    assert issubclass(a_class, DataClassBase)
    nt = from_typing(a_class)
    assert isinstance(nt, Class)
    assert nt.__module__ == a_class.__module__
    assert nt.__name__ == a_class.__name__

    # Enum
    class A(enum.IntEnum):
        A = 1

    nt = from_typing(A)
    assert isinstance(nt, Enum)
    assert nt.__module__ == A.__module__
    assert nt.__name__ == A.__name__

    # Any
    assert from_typing(typing.Any) is Any

    # NoneType
    assert from_typing(builtins.type(None)) is NoneType


# def test_to_typing():
#     # base
#     assert to_typing(Int) is int
#     assert to_typing(Float) is float
#     assert to_typing(Bool) is bool
#     assert to_typing(Str) is str
#
#     # TypeVar
#     t = TypeVar(typing.TypeVar(name="T"))
#     nt = to_typing(t)
#     assert isinstance(nt, typing.TypeVar)
#     assert nt is t.origin_type
#
#     tt = Tuple(t, List(t))
#     nt = to_typing(tt)
#     args = typing_inspect.get_args(nt, evaluate=True)
#     assert args[0] is typing_inspect.get_args(args[1], evaluate=True)[0]
#
#     # NewType
#     tx = typing.NewType("NewInt", int)
#     t = NewType(tx)
#     nt = to_typing(t)
#     assert typing_inspect.is_new_type(nt)
#     assert nt is t.origin_type
#     assert nt.__supertype__ is int
#
#     tt = Tuple(t, List(t))
#     nt = to_typing(tt)
#     args = typing_inspect.get_args(nt, evaluate=True)
#     assert args[0] is typing_inspect.get_args(args[1], evaluate=True)[0]
#
#     # Tuple
#     t = Tuple(Int, Str)
#     nt = to_typing(t)
#     assert typing_inspect.get_origin(nt) in [tuple, typing.Tuple]
#     args = typing_inspect.get_args(nt, evaluate=True)
#     assert args[0] is int
#     assert args[1] is str
#
#     # Union
#     t = Union(Int, Str)
#     nt = to_typing(t)
#     assert typing_inspect.get_origin(nt) is typing.Union
#     args = typing_inspect.get_args(nt, evaluate=True)
#     assert int in args and str in args
#
#     # List
#     t = List(Int)
#     nt = to_typing(t)
#     assert typing_inspect.get_origin(nt) in [list, typing.List]
#     assert typing_inspect.get_args(nt, evaluate=True)[0] is int
#
#     # Dict
#     t = Dict(Int, Str)
#     nt = to_typing(t)
#     assert typing_inspect.get_origin(nt) in [dict, typing.Dict]
#     args = typing_inspect.get_args(nt, evaluate=True)
#     assert args[0] is int
#     assert args[1] is str
#
#     # Const
#     # t = dtype_new.Const(dtype_new.Int)
#     # nt = dtype_new.to_typing(t)
#     # assert typing_inspect.get_origin(nt) is Constant
#     # assert typing_inspect.get_args(nt, evaluate=True)[0] is int
#
#     # Class
#     a_class = create_class()
#     nt = to_typing(Class.wrap(a_class))
#     assert nt is a_class
#
#     # Enum
#     class A(enum.IntEnum):
#         pass
#
#     t = Enum(A)
#     nt = to_typing(t)
#     assert nt is A
#
#     # Any
#     assert to_typing(Any) is typing.Any
#
#     # NoneType
#     assert to_typing(NoneType) is builtins.type(None)


def test_is_equaltype():
    def eq(type, other):
        a = is_equaltype(type, other)
        b = is_equaltype(other, type)

        assert a == b
        return a

    # base
    assert eq(Int, Int)
    assert not eq(Int, Str)

    assert eq(Str, Str)

    assert eq(Float, Float)

    assert eq(Bool, Bool)

    # NoneType
    assert eq(NoneType, NoneType)
    assert not eq(NoneType, Int)

    # Class
    class A(DataClassBase):
        pass

    class B(DataClassBase):
        pass

    class C(A):
        pass

    a = from_typing(A)
    a2 = from_typing(A)
    b = from_typing(B)
    c = from_typing(C)

    assert eq(a, a2)
    assert not eq(a, b)
    assert not eq(c, a)

    # Enum
    class A(enum.IntEnum):
        pass

    class B(enum.IntEnum):
        pass

    class C(A):
        pass

    a = from_typing(A)
    a2 = from_typing(A)
    b = from_typing(B)
    c = from_typing(C)

    assert eq(a, a2)
    assert eq(a2, a)
    assert not eq(a, b)
    assert not eq(c, a)

    # Union
    assert eq(Union(Int, Str), Union(Int, Str))
    assert eq(Union(Int, Str), Union(Str, Int))
    assert not eq(Union(Int, Str), Union(Int, Str, Bool))
    assert eq(Union(Int), Int)

    # List
    assert eq(List(Int), List(Int))
    assert not eq(List(Int), List(Str))

    # Dict
    assert eq(Dict(Int, Str), Dict(Int, Str))
    assert not eq(Dict(Int, Str), Dict(Str, Str))
    assert not eq(Dict(Int, Str), Dict(Int, Int))

    # Tuple
    assert eq(Tuple(Int, Str), Tuple(Int, Str))
    assert not eq(Tuple(Int, Str), Tuple(Int, Int))

    # Const
    assert not eq(Const(Int), Int)
    assert eq(Const(Int), Const(Int))

    #assert eq(Const(Union(Int)), Union(Const(Int)))
    #assert eq(Const(Union(Int)), Const(Union(Const(Int))))

    # Any
    assert eq(Any, Any)
    assert not eq(Any, Int)

    # TypeVar
    t = TypeVar(name="T")
    u = TypeVar(name="U")

    assert eq(t, t)
    assert not eq(t, Int)
    assert not eq(t, u)

    # NewType
    t = NewType(typing.NewType("NT1", int))
    u = NewType(typing.NewType("NT2", int))

    assert eq(t, t)
    assert not eq(t, Int)
    assert not eq(t, u)

    t = NewType(Int, name="NT1")
    u = NewType(Int, name="NT2")

    assert eq(t, t)
    assert not eq(t, Int)
    assert not eq(t, u)


def test_is_subtype():
    sub = is_subtype

    # base
    assert sub(Int, Int)
    assert not sub(Int, Str)

    assert sub(Str, Str)
    assert sub(Float, Float)
    assert sub(Bool, Bool)

    assert sub(Bool, Int)
    assert not sub(Int, Bool)

    # NoneType
    assert sub(NoneType, NoneType)
    assert not sub(NoneType, Int)
    assert not sub(Int, NoneType)

    # Class
    class A(DataClassBase):
        pass

    class B(DataClassBase):
        pass

    class C(A):
        pass

    a = from_typing(A)
    a2 = from_typing(A)
    b = from_typing(B)
    c = from_typing(C)


    assert sub(a, a2)
    assert sub(a2, a)
    assert not sub(a, b)
    assert sub(c, a)
    assert not sub(a, c)

    # Enum
    class A(enum.IntEnum):
        pass

    class B(enum.IntEnum):
        pass

    class C(A):
        pass

    a = from_typing(A)
    a2 = from_typing(A)
    b = from_typing(B)
    c = from_typing(C)

    assert sub(a, a2)
    assert sub(a2, a)
    assert not sub(a, b)
    assert sub(c, a)
    assert not sub(a, c)

    assert sub(a, Int)
    assert not sub(Int, a)

    # Union
    assert sub(Int, Union(Int, Str))
    assert not sub(Union(Int, Str), Int)
    assert sub(Union(Int, Str), Union(Int, Str))
    assert sub(Union(Union(Int), Str), Union(Int, Str))
    assert sub(Union(Int, Str), Union(Union(Int), Str))

    # List
    assert sub(List(Int), List(Int))
    assert not sub(List(Int), List(Str))

    # Dict
    assert sub(Dict(Int, Str), Dict(Int, Str))
    assert not sub(Dict(Int, Str), Dict(Str, Str))
    assert not sub(Dict(Int, Str), Dict(Int, Int))

    # Tuple
    assert sub(Tuple(Int, Str), Tuple(Int, Str))
    assert not sub(Tuple(Int, Str), Tuple(Int, Int))

    # Const
    assert sub(Const(Int), Int)
    assert not sub(Int, Const(Int))
    assert sub(Const(Int), Const(Int))

    #assert sub(Const(Const(Int)), Int)

    #assert sub(Const(Tuple(Int, Str)), Tuple(Const(Int), Str))

    # Any
    assert sub(Int, Any)
    assert not sub(Any, Int)
    assert sub(Any, Any)

    # TypeVar
    t = TypeVar(name="T")
    u = TypeVar(name="U")

    assert sub(Int, t)
    assert sub(t, Int)
    assert sub(t, u)
    # assert sub(Int, Union([t, u]))
    assert sub(Union(Int, Str), t)
    # assert sub(Union([Int, Str]), Union([t, u]))
    assert sub(Tuple(Union(Int, Str), Int), Tuple(t, t))
    assert sub(Tuple(Union(Int, Str), Int), Tuple(Union(t, Str), t))

    b, vm, _ = is_subtype_map(Int, t, {}, {})
    assert is_equaltype(vm[t], Int)

    b, vm, _ = is_subtype_map(Union(Int), Union(t), {}, {})
    assert is_equaltype(vm[t], Int)

    b, vm, _ = is_subtype_map(Union(Int), Union(t, Int), {}, {})
    assert vm == {}

    b, vm, _ = is_subtype_map(List(Int), List(t), {}, {})
    assert is_equaltype(vm[t], Int)

    b, vm, _ = is_subtype_map(Tuple(Int, Str), Tuple(t, t), {}, {})
    assert is_equaltype(vm[t], Union(Int, Str))

    b, vm, _ = is_subtype_map(Tuple(Int, Str), Tuple(t, u), {}, {})
    assert is_equaltype(vm[t], Int)
    assert is_equaltype(vm[u], Str)

    b, _, rest = is_subtype_map(t, Int, {}, {})
    assert is_equaltype(rest[t], Int)

    b, _, rest = is_subtype_map(t, List(Int), {}, {})
    assert is_equaltype(rest[t], List(Int))

    b, vm, rest = is_subtype_map(Str, u, {}, {u: Int})
    assert not b

    b, vm, rest = is_subtype_map(t, u, {}, {u: Int})
    assert is_equaltype(vm[u], t)
    assert is_equaltype(rest[t], Int)

    b, vm, rest = is_subtype_map(t, List(u), {}, {u: Int})
    assert is_equaltype(rest[t], List(Int))

    b, vm, rest = is_subtype_map(List(t), u, {}, {u: List(Int)})
    assert is_equaltype(vm[u], List(t))
    assert is_equaltype(rest[t], Int)

    # NewType
    t = NewType(typing.NewType("NT1", int))
    u = NewType(typing.NewType("NT2", int))

    assert sub(t, t)
    assert sub(t, Int)
    assert sub(Int, t)
    assert sub(t, u)

    t = NewType(Int, name="NT1")
    u = NewType(Int, name="NT2")

    assert sub(t, t)
    assert sub(t, Int)
    assert sub(Int, t)
    assert sub(t, u)


def test_common_sub_type():
    com_sub = common_sub_type
    eq = is_equaltype

    # base
    b, t = com_sub(Int, Int)
    assert b
    assert eq(t, Int)

    b, t = com_sub(Int, Str)
    assert not b

    b, t = com_sub(Int, Bool)
    assert b
    assert eq(t, Bool)

    b, t = com_sub(Bool, Int)
    assert b
    assert eq(t, Bool)

    # Class
    A = create_class()

    a = from_typing(A)
    a2 = from_typing(A)

    b, t = com_sub(a, a2)
    assert b
    assert eq(t, a)

    # Enum
    class A(enum.IntEnum):
        pass

    a = from_typing(A)
    a2 = from_typing(A)

    b, t = com_sub(a, a2)
    assert b
    assert eq(t, a)

    # Union
    b, t = com_sub(Union(Int, Str), Union(Str, Float))
    assert b
    assert eq(t, Union(Int, Str))

    b, t = com_sub(Union(Int, Str), Str)
    assert b
    assert eq(t, Str)

    b, t = com_sub(Str, Union(Str, Float))
    assert b
    assert eq(t, Str)

    # Tuple
    b, t = com_sub(Tuple(Int, Str), Tuple(Int, Str))
    assert b
    assert eq(t, Tuple(Int, Str))

    b, t = com_sub(Tuple(Int, Str), Tuple(Int, Int))
    assert not b

    # List
    b, t = com_sub(List(Int), List(Int))
    assert b
    assert eq(t, List(Int))

    b, t = com_sub(List(Int), List(Str))
    assert not b

    # Dict
    b, t = com_sub(Dict(Int, Str), Dict(Int, Str))
    assert b
    assert eq(t, Dict(Int, Str))

    b, t = com_sub(Dict(Int, Str), Dict(Str, Str))
    assert not b

    b, t = com_sub(Dict(Int, Str), Dict(Int, Int))
    assert not b

    # Const
    b, t = com_sub(Const(Int), Const(Int))
    assert b
    assert eq(t, Const(Int))

    b, t = com_sub(Const(Int), Int)
    assert b
    assert eq(t, Const(Int))

    b, t = com_sub(Int, Const(Int))
    assert b
    assert eq(t, Const(Int))

    # b, t = com_sub(Const(Union(Int)), Union(Const(Int)))
    # assert b
    # assert eq(t, Const(Union(Int)))

    # Any
    b, t = com_sub(Any, Any)
    assert b
    assert eq(t, Any)

    # TypeVar
    t = TypeVar(name="T")
    u = TypeVar(name="U")

    b, tt = com_sub(t, t)
    assert b
    assert eq(tt, t)

    b, tt = com_sub(t, u)
    assert not b

    # NewType
    t = NewType(Int, name="NT")
    u = NewType(Int, name="NT2")

    b, tt = com_sub(t, t)
    assert b
    assert eq(tt, t)

    b, tt = com_sub(t, u)
    assert not b


def test_extract_type_var():
    t = TypeVar(name="T")
    u = TypeVar(name="U")

    assert extract_type_var(t) == {t}
    assert extract_type_var(Int) == set()
    assert extract_type_var(Tuple(t)) == {t}
    # assert extract_type_var(Union([t, u])) == {t, u}
    assert extract_type_var(Union(t, Int)) == {t}
    assert extract_type_var(List(t)) == {t}
    assert extract_type_var(Dict(t, u)) == {t, u}
    assert extract_type_var(Const(t)) == {t}
    assert extract_type_var(Dict(Str, List(t))) == {t}
    # assert extract_type_var(Union([t, Int, Union([u, Str])])) == {t, u}
    # assert extract_type_var(NewType("NT", t)) == {t}
    # assert list(extract_type_var(NewType(typing.NewType("NT", t.origin_type))))[0].origin_type is t.origin_type


def test_check_type_var():
    t = TypeVar(name="T")

    assert check_type_var(t, t)
    assert check_type_var(t, Int)
    assert not check_type_var(Int, t)


def test_substitute_type_vars():
    sub_tv = substitute_type_vars
    eq = is_equaltype

    t = TypeVar(name="T")
    u = TypeVar(name="U")
    v = TypeVar(name="V")

    # type_var
    tt, vm = sub_tv(t, {})
    assert tt is t
    assert vm == {}

    tt, vm = sub_tv(t, {t: Int})
    assert eq(tt, Int)
    assert eq(vm[t], Int)

    # create_new
    tt, vm = sub_tv(t, {t: v}, create_new=True)
    assert eq(tt, v)
    assert eq(vm[t], v)

    tt, vm = sub_tv(t, {}, create_new=True)
    assert isinstance(tt, TypeVar)
    assert tt is not t
    assert eq(vm[t], tt)

    # recursive
    tt, vm = sub_tv(t, {t: List(u), u: Int}, recursive=True)
    assert eq(tt, List(Int))

    # Tuple
    tt, vm = sub_tv(Tuple(t, Int), {t: Str})
    assert eq(tt, Tuple(Str, Int))

    # Union
    tt, vm = sub_tv(Union(t, Int), {t: Str})
    assert eq(tt, Union(Str, Int))

    # List
    tt, vm = sub_tv(List(t), {t: Str})
    assert eq(tt, List(Str))

    # Dict
    tt, vm = sub_tv(Dict(t, v), {t: Str, v: Int})
    assert eq(tt, Dict(Str, Int))

    # Const
    tt, vm = sub_tv(Const(t), {t: Str})
    assert eq(tt, Const(Str))


def test_expand_var_map():
    eq = is_equaltype

    t = TypeVar(name="T")
    u = TypeVar(name="U")
    v = TypeVar(name="V")

    vm1 = {
        u: List(v),
        t: Int,
        v: List(t)
    }
    vm2 = expand_var_map(vm1)
    assert len(vm2) == 3
    assert eq(vm2[t], Int)
    assert eq(vm2[u], List(List(Int)))
    assert eq(vm2[v], List(Int))
