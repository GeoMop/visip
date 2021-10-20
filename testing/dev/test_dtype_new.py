from visip.dev import dtype_new, dtype

import typing


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
    assert nt.name == t.__name__

    tt = typing.Tuple[t, typing.List[t]]
    print(tt)
    nt = dtype_new.from_typing(tt)
    assert nt.args[0] is nt.args[1].arg


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

    # Class
    class A(dtype.DataClassBase):
        pass

    class B(dtype.DataClassBase):
        pass

    class C(A):
        pass

    a = dtype_new.from_typing(A)
    a2 = dtype_new.from_typing(A)
    b = dtype_new.from_typing(B)
    c = dtype_new.from_typing(C)

    assert sub(a, a2)
    assert sub(a2, a)
    assert not sub(a, b)
    assert sub(c, a)
    assert not sub(a, c)

    # Union
    assert sub(dt.Int(), dt.Union([dt.Int(), dt.Str()]))
    assert not sub(dt.Union([dt.Int(), dt.Str()]), dt.Int())
    assert sub(dt.Union([dt.Int(), dt.Str()]), dt.Union([dt.Int(), dt.Str()]))
    assert sub(dt.Union([dt.Union([dt.Int()]), dt.Str()]), dt.Union([dt.Int(), dt.Str()]))
    assert sub(dt.Union([dt.Int(), dt.Str()]), dt.Union([dt.Union([dt.Int()]), dt.Str()]))

    # List
    assert sub(dt.List(dt.Int()), dt.List(dt.Int()))
    assert not sub(dt.List(dt.Int()), dt.List(dt.Str()))

    # Dict
    assert sub(dt.Dict(dt.Int(), dt.Str()), dt.Dict(dt.Int(), dt.Str()))
    assert not sub(dt.Dict(dt.Int(), dt.Str()), dt.Dict(dt.Str(), dt.Str()))
    assert not sub(dt.Dict(dt.Int(), dt.Str()), dt.Dict(dt.Int(), dt.Int()))

    # Tuple
    assert sub(dt.Tuple([dt.Int(), dt.Str()]), dt.Tuple([dt.Int(), dt.Str()]))
    assert not sub(dt.Tuple([dt.Int(), dt.Str()]), dt.Tuple([dt.Int(), dt.Int()]))

    # Const
    assert sub(dt.Const(dt.Int()), dt.Int())
    assert not sub(dt.Int(), dt.Const(dt.Int()))
    assert sub(dt.Const(dt.Int()), dt.Const(dt.Int()))

    assert sub(dt.Const(dt.Const(dt.Int())), dt.Int())
    
    assert sub(dt.Const(dt.Tuple([dt.Int(), dt.Str()])), dt.Tuple([dt.Const(dt.Int()), dt.Str()]))

    # TypeVar
    t = dt.TypeVar("T")
    u = dt.TypeVar("U")

    assert sub(dt.Int(), t)
    assert not sub(t, dt.Int())
    assert sub(t, u)
    assert sub(dt.Int(), dt.Union([t, u]))
    assert sub(dt.Union([dt.Int(), dt.Str()]), t)
    assert sub(dt.Union([dt.Int(), dt.Str()]), dt.Union([t, u]))
    assert sub(dt.Tuple([dt.Union([dt.Int(), dt.Str()]), dt.Int()]), dt.Tuple([t, t]))
    assert sub(dt.Tuple([dt.Union([dt.Int(), dt.Str()]), dt.Int()]), dt.Tuple([dt.Union([t, dt.Str()]), t]))
