import enum

from visip.dev import dtype

import typing
import typing_inspect
import builtins


def test_singleton():
    class A(metaclass=dtype.Singleton):
        pass

    class B(A):
        pass

    class C(A):
        pass

    assert A() is A()
    assert B() is B()
    assert B() is not C()


def test_types():
    dt = dtype

    # Union
    t = dt.Union(dt.Int(), dt.Union(dt.Str()))
    assert len(t.args) == 2
    assert isinstance(t.args[0], dt.Int)
    assert isinstance(t.args[1], dt.Str)

    t = dt.Union(dt.Int(), dt.Const(dt.Union(dt.Str())))
    assert len(t.args) == 2
    assert isinstance(t.args[0], dt.Int)
    assert isinstance(t.args[1], dt.Const)
    assert isinstance(t.args[1].arg, dt.Str)

    t = dt.Union(dt.Int(), dt.Int())
    assert len(t.args) == 1
    assert isinstance(t.args[0], dt.Int)

    t = dt.Union(dt.Int(), dt.Union(dt.Int()))
    assert len(t.args) == 1
    assert isinstance(t.args[0], dt.Int)

    t = dt.TypeVar(typing.TypeVar("T"))
    u = dt.TypeVar(typing.TypeVar("U"))

    try:
        dt.Union(t, u)
    except TypeError:
        pass
    else:
        assert False

    try:
        dt.Union(t, dt.Const(u))
    except TypeError:
        pass
    else:
        assert False

    # Const
    t = dt.Const(dt.Const(dt.Int()))
    assert isinstance(t, dt.Const)
    assert isinstance(t.arg, dt.Int)


def test_from_typing():
    # base
    assert isinstance(dtype.from_typing(int), dtype.Int)
    assert isinstance(dtype.from_typing(float), dtype.Float)
    assert isinstance(dtype.from_typing(bool), dtype.Bool)
    assert isinstance(dtype.from_typing(str), dtype.Str)


    # TypeVar
    t = typing.TypeVar("T")
    nt = dtype.from_typing(t)
    assert isinstance(nt, dtype.TypeVar)
    assert nt.origin_type is t

    tt = typing.Tuple[t, typing.List[t]]
    nt = dtype.from_typing(tt)
    assert nt.args[0].origin_type is nt.args[1].arg.origin_type


    # NewType
    t = typing.NewType("NewInt", int)
    nt = dtype.from_typing(t)
    assert isinstance(nt, dtype.NewType)
    assert nt.origin_type is t
    assert isinstance(nt.supertype, dtype.Int)

    tt = typing.Tuple[t, typing.List[t]]
    nt = dtype.from_typing(tt)
    assert nt.args[0].origin_type is nt.args[1].arg.origin_type


    # Tuple
    t = typing.Tuple[int, str]
    nt = dtype.from_typing(t)
    assert isinstance(nt, dtype.Tuple)
    assert isinstance(nt.args[0], dtype.Int)
    assert isinstance(nt.args[1], dtype.Str)

    # Union
    t = typing.Union[int, str]
    nt = dtype.from_typing(t)
    assert isinstance(nt, dtype.Union)
    assert isinstance(nt.args[0], dtype.Int)
    assert isinstance(nt.args[1], dtype.Str)

    # List
    t = typing.List[int]
    nt = dtype.from_typing(t)
    assert isinstance(nt, dtype.List)
    assert isinstance(nt.arg, dtype.Int)

    # Dict
    t = typing.Dict[int, str]
    nt = dtype.from_typing(t)
    assert isinstance(nt, dtype.Dict)
    assert isinstance(nt.key, dtype.Int)
    assert isinstance(nt.value, dtype.Str)

    # Const
    t = dtype.Const(int)
    nt = dtype.from_typing(t)
    assert isinstance(nt, dtype.Const)
    assert isinstance(nt.arg, dtype.Int)


    # Class
    class A(dtype.DataClassBase):
        pass

    nt = dtype.from_typing(A)
    assert isinstance(nt, dtype.Class)
    assert nt.module == A.__module__
    assert nt.name == A.__name__

    # Enum
    class A(enum.IntEnum):
        A = 1

    nt = dtype.from_typing(A)
    assert isinstance(nt, dtype.Enum)
    assert nt.module == A.__module__
    assert nt.name == A.__name__


    # Any
    assert isinstance(dtype.from_typing(typing.Any), dtype.Any)

    # NoneType
    assert isinstance(dtype.from_typing(builtins.type(None)), dtype.NoneType)


def test_to_typing():
    # base
    assert dtype.to_typing(dtype.Int()) is int
    assert dtype.to_typing(dtype.Float()) is float
    assert dtype.to_typing(dtype.Bool()) is bool
    assert dtype.to_typing(dtype.Str()) is str


    # TypeVar
    t = dtype.TypeVar(typing.TypeVar("T"))
    nt = dtype.to_typing(t)
    assert isinstance(nt, typing.TypeVar)
    assert nt is t.origin_type

    tt = dtype.Tuple(t, dtype.List(t))
    nt = dtype.to_typing(tt)
    args = typing_inspect.get_args(nt, evaluate=True)
    assert args[0] is typing_inspect.get_args(args[1], evaluate=True)[0]


    # NewType
    tx = typing.NewType("NewInt", int)
    t = dtype.NewType(tx)
    nt = dtype.to_typing(t)
    assert typing_inspect.is_new_type(nt)
    assert nt is t.origin_type
    assert nt.__supertype__ is int

    tt = dtype.Tuple(t, dtype.List(t))
    nt = dtype.to_typing(tt)
    args = typing_inspect.get_args(nt, evaluate=True)
    assert args[0] is typing_inspect.get_args(args[1], evaluate=True)[0]


    # Tuple
    t = dtype.Tuple(dtype.Int(), dtype.Str())
    nt = dtype.to_typing(t)
    assert typing_inspect.get_origin(nt) in [tuple, typing.Tuple]
    args = typing_inspect.get_args(nt, evaluate=True)
    assert args[0] is int
    assert args[1] is str

    # Union
    t = dtype.Union(dtype.Int(), dtype.Str())
    nt = dtype.to_typing(t)
    assert typing_inspect.get_origin(nt) is typing.Union
    args = typing_inspect.get_args(nt, evaluate=True)
    assert args[0] is int
    assert args[1] is str

    # List
    t = dtype.List(dtype.Int())
    nt = dtype.to_typing(t)
    assert typing_inspect.get_origin(nt) in [list, typing.List]
    assert typing_inspect.get_args(nt, evaluate=True)[0] is int

    # Dict
    t = dtype.Dict(dtype.Int(), dtype.Str())
    nt = dtype.to_typing(t)
    assert typing_inspect.get_origin(nt) in [dict, typing.Dict]
    args = typing_inspect.get_args(nt, evaluate=True)
    assert args[0] is int
    assert args[1] is str

    # Const
    # t = dtype_new.Const(dtype_new.Int())
    # nt = dtype_new.to_typing(t)
    # assert typing_inspect.get_origin(nt) is dtype.Constant
    # assert typing_inspect.get_args(nt, evaluate=True)[0] is int


    # Class
    class A(dtype.DataClassBase):
        pass

    t = dtype.Class(A.__module__, A.__name__, A)
    nt = dtype.to_typing(t)
    assert nt is A

    # Enum
    class A(enum.IntEnum):
        pass

    t = dtype.Enum(A.__module__, A.__name__, A)
    nt = dtype.to_typing(t)
    assert nt is A


    # Any
    assert dtype.to_typing(dtype.Any()) is typing.Any

    # NoneType
    assert dtype.to_typing(dtype.NoneType()) is builtins.type(None)


def test_is_equaltype():
    dt = dtype

    def eq(type, other):
        a = dt.is_equaltype(type, other)
        b = dt.is_equaltype(other, type)

        assert a == b
        return a
    
    # base
    assert eq(dt.Int(), dt.Int())
    assert not eq(dt.Int(), dt.Str())

    assert eq(dt.Str(), dt.Str())

    assert eq(dt.Float(), dt.Float())

    assert eq(dt.Bool(), dt.Bool())

    # NoneType
    assert eq(dt.NoneType(), dt.NoneType())
    assert not eq(dt.NoneType(), dt.Int())

    # Class
    class A(dtype.DataClassBase):
        pass

    class B(dtype.DataClassBase):
        pass

    class C(A):
        pass

    a = dt.from_typing(A)
    a2 = dt.from_typing(A)
    b = dt.from_typing(B)
    c = dt.from_typing(C)

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

    a = dt.from_typing(A)
    a2 = dt.from_typing(A)
    b = dt.from_typing(B)
    c = dt.from_typing(C)

    assert eq(a, a2)
    assert eq(a2, a)
    assert not eq(a, b)
    assert not eq(c, a)

    # Union
    assert eq(dt.Union(dt.Int(), dt.Str()), dt.Union(dt.Int(), dt.Str()))
    assert eq(dt.Union(dt.Int(), dt.Str()), dt.Union(dt.Str(), dt.Int()))
    assert not eq(dt.Union(dt.Int(), dt.Str()), dt.Union(dt.Int(), dt.Str(), dt.Bool()))
    assert eq(dt.Union(dt.Int()), dt.Int())

    # List
    assert eq(dt.List(dt.Int()), dt.List(dt.Int()))
    assert not eq(dt.List(dt.Int()), dt.List(dt.Str()))

    # Dict
    assert eq(dt.Dict(dt.Int(), dt.Str()), dt.Dict(dt.Int(), dt.Str()))
    assert not eq(dt.Dict(dt.Int(), dt.Str()), dt.Dict(dt.Str(), dt.Str()))
    assert not eq(dt.Dict(dt.Int(), dt.Str()), dt.Dict(dt.Int(), dt.Int()))

    # Tuple
    assert eq(dt.Tuple(dt.Int(), dt.Str()), dt.Tuple(dt.Int(), dt.Str()))
    assert not eq(dt.Tuple(dt.Int(), dt.Str()), dt.Tuple(dt.Int(), dt.Int()))

    # Const
    assert not eq(dt.Const(dt.Int()), dt.Int())
    assert eq(dt.Const(dt.Int()), dt.Const(dt.Int()))

    assert eq(dt.Const(dt.Union(dt.Int())), dt.Union(dt.Const(dt.Int())))

    # Any
    assert eq(dt.Any(), dt.Any())
    assert not eq(dt.Any(), dt.Int())

    # TypeVar
    t = dt.TypeVar()
    u = dt.TypeVar()

    assert eq(t, t)
    assert not eq(t, dt.Int())
    assert not eq(t, u)

    # NewType
    t = dt.NewType(typing.NewType("NT1", int))
    u = dt.NewType(typing.NewType("NT2", int))

    assert eq(t, t)
    assert not eq(t, dt.Int())
    assert not eq(t, u)

    t = dt.NewType(dt.Int(), "NT1")
    u = dt.NewType(dt.Int(), "NT2")

    assert eq(t, t)
    assert not eq(t, dt.Int())
    assert not eq(t, u)


def test_is_subtype():
    dt = dtype
    sub = dt.is_subtype
    
    # base
    assert sub(dt.Int(), dt.Int())
    assert not sub(dt.Int(), dt.Str())

    assert sub(dt.Str(), dt.Str())
    assert sub(dt.Float(), dt.Float())
    assert sub(dt.Bool(), dt.Bool())

    assert sub(dt.Bool(), dt.Int())
    assert not sub(dt.Int(), dt.Bool())

    # NoneType
    assert sub(dt.NoneType(), dt.NoneType())
    assert not sub(dt.NoneType(), dt.Int())
    assert not sub(dt.Int(), dt.NoneType())

    # Class
    class A(dtype.DataClassBase):
        pass

    class B(dtype.DataClassBase):
        pass

    class C(A):
        pass

    a = dt.from_typing(A)
    a2 = dt.from_typing(A)
    b = dt.from_typing(B)
    c = dt.from_typing(C)

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

    a = dt.from_typing(A)
    a2 = dt.from_typing(A)
    b = dt.from_typing(B)
    c = dt.from_typing(C)

    assert sub(a, a2)
    assert sub(a2, a)
    assert not sub(a, b)
    assert sub(c, a)
    assert not sub(a, c)

    assert sub(a, dt.Int())
    assert not sub(dt.Int(), a)

    # Union
    assert sub(dt.Int(), dt.Union(dt.Int(), dt.Str()))
    assert not sub(dt.Union(dt.Int(), dt.Str()), dt.Int())
    assert sub(dt.Union(dt.Int(), dt.Str()), dt.Union(dt.Int(), dt.Str()))
    assert sub(dt.Union(dt.Union(dt.Int()), dt.Str()), dt.Union(dt.Int(), dt.Str()))
    assert sub(dt.Union(dt.Int(), dt.Str()), dt.Union(dt.Union(dt.Int()), dt.Str()))

    # List
    assert sub(dt.List(dt.Int()), dt.List(dt.Int()))
    assert not sub(dt.List(dt.Int()), dt.List(dt.Str()))

    # Dict
    assert sub(dt.Dict(dt.Int(), dt.Str()), dt.Dict(dt.Int(), dt.Str()))
    assert not sub(dt.Dict(dt.Int(), dt.Str()), dt.Dict(dt.Str(), dt.Str()))
    assert not sub(dt.Dict(dt.Int(), dt.Str()), dt.Dict(dt.Int(), dt.Int()))

    # Tuple
    assert sub(dt.Tuple(dt.Int(), dt.Str()), dt.Tuple(dt.Int(), dt.Str()))
    assert not sub(dt.Tuple(dt.Int(), dt.Str()), dt.Tuple(dt.Int(), dt.Int()))

    # Const
    assert sub(dt.Const(dt.Int()), dt.Int())
    assert not sub(dt.Int(), dt.Const(dt.Int()))
    assert sub(dt.Const(dt.Int()), dt.Const(dt.Int()))

    assert sub(dt.Const(dt.Const(dt.Int())), dt.Int())
    
    assert sub(dt.Const(dt.Tuple(dt.Int(), dt.Str())), dt.Tuple(dt.Const(dt.Int()), dt.Str()))

    # Any
    assert sub(dt.Int(), dt.Any())
    assert not sub(dt.Any(), dt.Int())
    assert sub(dt.Any(), dt.Any())

    # TypeVar
    t = dt.TypeVar()
    u = dt.TypeVar()

    assert sub(dt.Int(), t)
    assert not sub(t, dt.Int())
    assert sub(t, u)
    #assert sub(dt.Int(), dt.Union([t, u]))
    assert sub(dt.Union(dt.Int(), dt.Str()), t)
    #assert sub(dt.Union([dt.Int(), dt.Str()]), dt.Union([t, u]))
    assert sub(dt.Tuple(dt.Union(dt.Int(), dt.Str()), dt.Int()), dt.Tuple(t, t))
    assert sub(dt.Tuple(dt.Union(dt.Int(), dt.Str()), dt.Int()), dt.Tuple(dt.Union(t, dt.Str()), t))

    b, vm = dt.is_subtype_map(dt.Int(), t, {})
    assert dt.is_equaltype(vm[t], dt.Int())

    b, vm = dt.is_subtype_map(dt.Union(dt.Int()), dt.Union(t), {})
    assert dt.is_equaltype(vm[t], dt.Int())

    b, vm = dt.is_subtype_map(dt.Union(dt.Int()), dt.Union(t, dt.Int()), {})
    assert vm == {}

    b, vm = dt.is_subtype_map(dt.List(dt.Int()), dt.List(t), {})
    assert dt.is_equaltype(vm[t], dt.Int())

    b, vm = dt.is_subtype_map(dt.Tuple(dt.Int(), dt.Str()), dt.Tuple(t, t), {})
    assert dt.is_equaltype(vm[t], dt.Union(dt.Int(), dt.Str()))

    b, vm = dt.is_subtype_map(dt.Tuple(dt.Int(), dt.Str()), dt.Tuple(t, u), {})
    assert dt.is_equaltype(vm[t], dt.Int())
    assert dt.is_equaltype(vm[u], dt.Str())

    # NewType
    t = dt.NewType(typing.NewType("NT1", int))
    u = dt.NewType(typing.NewType("NT2", int))

    assert sub(t, t)
    assert sub(t, dt.Int())
    assert not sub(dt.Int(), t)
    assert not sub(t, u)

    t = dt.NewType(dt.Int(), "NT1")
    u = dt.NewType(dt.Int(), "NT2")

    assert sub(t, t)
    assert sub(t, dt.Int())
    assert not sub(dt.Int(), t)
    assert not sub(t, u)


def test_extract_type_var():
    dt = dtype

    t = dt.TypeVar()
    u = dt.TypeVar()

    assert dt.extract_type_var(t) == {t}
    assert dt.extract_type_var(dt.Int()) == set()
    assert dt.extract_type_var(dt.Tuple(t)) == {t}
    #assert dt.extract_type_var(dt.Union([t, u])) == {t, u}
    assert dt.extract_type_var(dt.Union(t, dt.Int())) == {t}
    assert dt.extract_type_var(dt.List(t)) == {t}
    assert dt.extract_type_var(dt.Dict(t, u)) == {t, u}
    assert dt.extract_type_var(dt.Const(t)) == {t}
    assert dt.extract_type_var(dt.Dict(dt.Str(), dt.List(t))) == {t}
    #assert dt.extract_type_var(dt.Union([t, dt.Int(), dt.Union([u, dt.Str()])])) == {t, u}
    assert list(dt.extract_type_var(dt.NewType(typing.NewType("NT", t.origin_type))))[0].origin_type is t.origin_type


def test_check_type_var():
    dt = dtype

    t = dt.TypeVar()

    assert dt.check_type_var(t, t)
    assert dt.check_type_var(t, dt.Int())
    assert not dt.check_type_var(dt.Int(), t)
