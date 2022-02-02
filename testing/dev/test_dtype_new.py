import enum

from visip.dev import dtype_new, dtype

import typing
import typing_inspect
import builtins


def test_singleton():
    class A(metaclass=dtype_new.Singleton):
        pass

    class B(A):
        pass

    class C(A):
        pass

    assert A() is A()
    assert B() is B()
    assert B() is not C()


def test_types():
    dt = dtype_new

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
    assert isinstance(dtype_new.from_typing(int), dtype_new.Int)
    assert isinstance(dtype_new.from_typing(float), dtype_new.Float)
    assert isinstance(dtype_new.from_typing(bool), dtype_new.Bool)
    assert isinstance(dtype_new.from_typing(str), dtype_new.Str)


    # TypeVar
    t = typing.TypeVar("T")
    nt = dtype_new.from_typing(t)
    assert isinstance(nt, dtype_new.TypeVar)
    assert nt.origin_type is t

    tt = typing.Tuple[t, typing.List[t]]
    nt = dtype_new.from_typing(tt)
    assert nt.args[0].origin_type is nt.args[1].arg.origin_type


    # NewType
    t = typing.NewType("NewInt", int)
    nt = dtype_new.from_typing(t)
    assert isinstance(nt, dtype_new.NewType)
    assert nt.origin_type is t
    assert isinstance(nt.supertype, dtype_new.Int)

    tt = typing.Tuple[t, typing.List[t]]
    nt = dtype_new.from_typing(tt)
    assert nt.args[0].origin_type is nt.args[1].arg.origin_type


    # Tuple
    t = typing.Tuple[int, str]
    nt = dtype_new.from_typing(t)
    assert isinstance(nt, dtype_new.Tuple)
    assert isinstance(nt.args[0], dtype_new.Int)
    assert isinstance(nt.args[1], dtype_new.Str)

    # Union
    t = typing.Union[int, str]
    nt = dtype_new.from_typing(t)
    assert isinstance(nt, dtype_new.Union)
    assert isinstance(nt.args[0], dtype_new.Int)
    assert isinstance(nt.args[1], dtype_new.Str)

    # List
    t = typing.List[int]
    nt = dtype_new.from_typing(t)
    assert isinstance(nt, dtype_new.List)
    assert isinstance(nt.arg, dtype_new.Int)

    # Dict
    t = typing.Dict[int, str]
    nt = dtype_new.from_typing(t)
    assert isinstance(nt, dtype_new.Dict)
    assert isinstance(nt.key, dtype_new.Int)
    assert isinstance(nt.value, dtype_new.Str)

    # Const
    t = dtype.Constant[int]
    nt = dtype_new.from_typing(t)
    assert isinstance(nt, dtype_new.Const)
    assert isinstance(nt.arg, dtype_new.Int)


    # Class
    class A(dtype.DataClassBase):
        pass

    nt = dtype_new.from_typing(A)
    assert isinstance(nt, dtype_new.Class)
    assert nt.module == A.__module__
    assert nt.name == A.__name__

    # Enum
    class A(enum.IntEnum):
        A = 1

    nt = dtype_new.from_typing(A)
    assert isinstance(nt, dtype_new.Enum)
    assert nt.module == A.__module__
    assert nt.name == A.__name__


    # Any
    assert isinstance(dtype_new.from_typing(typing.Any), dtype_new.Any)

    # NoneType
    assert isinstance(dtype_new.from_typing(builtins.type(None)), dtype_new.NoneType)


def test_to_typing():
    # base
    assert dtype_new.to_typing(dtype_new.Int()) is int
    assert dtype_new.to_typing(dtype_new.Float()) is float
    assert dtype_new.to_typing(dtype_new.Bool()) is bool
    assert dtype_new.to_typing(dtype_new.Str()) is str


    # TypeVar
    t = dtype_new.TypeVar(typing.TypeVar("T"))
    nt = dtype_new.to_typing(t)
    assert isinstance(nt, typing.TypeVar)
    assert nt is t.origin_type

    tt = dtype_new.Tuple(t, dtype_new.List(t))
    nt = dtype_new.to_typing(tt)
    args = typing_inspect.get_args(nt, evaluate=True)
    assert args[0] is typing_inspect.get_args(args[1], evaluate=True)[0]


    # NewType
    tx = typing.NewType("NewInt", int)
    t = dtype_new.NewType(tx)
    nt = dtype_new.to_typing(t)
    assert typing_inspect.is_new_type(nt)
    assert nt is t.origin_type
    assert nt.__supertype__ is int

    tt = dtype_new.Tuple(t, dtype_new.List(t))
    nt = dtype_new.to_typing(tt)
    args = typing_inspect.get_args(nt, evaluate=True)
    assert args[0] is typing_inspect.get_args(args[1], evaluate=True)[0]


    # Tuple
    t = dtype_new.Tuple(dtype_new.Int(), dtype_new.Str())
    nt = dtype_new.to_typing(t)
    assert typing_inspect.get_origin(nt) in [tuple, typing.Tuple]
    args = typing_inspect.get_args(nt, evaluate=True)
    assert args[0] is int
    assert args[1] is str

    # Union
    t = dtype_new.Union(dtype_new.Int(), dtype_new.Str())
    nt = dtype_new.to_typing(t)
    assert typing_inspect.get_origin(nt) is typing.Union
    args = typing_inspect.get_args(nt, evaluate=True)
    assert args[0] is int
    assert args[1] is str

    # List
    t = dtype_new.List(dtype_new.Int())
    nt = dtype_new.to_typing(t)
    assert typing_inspect.get_origin(nt) in [list, typing.List]
    assert typing_inspect.get_args(nt, evaluate=True)[0] is int

    # Dict
    t = dtype_new.Dict(dtype_new.Int(), dtype_new.Str())
    nt = dtype_new.to_typing(t)
    assert typing_inspect.get_origin(nt) in [dict, typing.Dict]
    args = typing_inspect.get_args(nt, evaluate=True)
    assert args[0] is int
    assert args[1] is str

    # Const
    t = dtype_new.Const(dtype_new.Int())
    nt = dtype_new.to_typing(t)
    assert typing_inspect.get_origin(nt) is dtype.Constant
    assert typing_inspect.get_args(nt, evaluate=True)[0] is int


    # Class
    class A(dtype.DataClassBase):
        pass

    t = dtype_new.Class(A.__module__, A.__name__, A)
    nt = dtype_new.to_typing(t)
    assert nt is A

    # Enum
    class A(enum.IntEnum):
        pass

    t = dtype_new.Enum(A.__module__, A.__name__, A)
    nt = dtype_new.to_typing(t)
    assert nt is A


    # Any
    assert dtype_new.to_typing(dtype_new.Any()) is typing.Any

    # NoneType
    assert dtype_new.to_typing(dtype_new.NoneType()) is builtins.type(None)


def test_is_equaltype():
    dt = dtype_new

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


def test_is_subtype():
    dt = dtype_new
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


def test_extract_type_var():
    dt = dtype_new

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
    dt = dtype_new

    t = dt.TypeVar()

    assert dt.check_type_var(t, t)
    assert dt.check_type_var(t, dt.Int())
    assert not dt.check_type_var(dt.Int(), t)
