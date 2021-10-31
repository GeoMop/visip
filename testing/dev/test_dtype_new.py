from visip.dev import dtype_new, dtype

import typing
import typing_inspect


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


def test_to_typing():
    # base
    assert dtype_new.to_typing(dtype_new.Int()) is int
    assert dtype_new.to_typing(dtype_new.Float()) is float
    assert dtype_new.to_typing(dtype_new.Bool()) is bool
    assert dtype_new.to_typing(dtype_new.Str()) is str


    # TypeVar
    t = dtype_new.TypeVar("T")
    nt = dtype_new.to_typing(t)
    print(type(nt))
    assert isinstance(nt, typing.TypeVar)
    assert nt.__name__ == t.name

    tt = dtype_new.Tuple([t, dtype_new.List(t)])
    nt = dtype_new.to_typing(tt)
    args = typing_inspect.get_args(nt, evaluate=True)
    assert args[0] is typing_inspect.get_args(args[1], evaluate=True)[0]


    # Tuple
    t = dtype_new.Tuple([dtype_new.Int(), dtype_new.Str()])
    nt = dtype_new.to_typing(t)
    assert typing_inspect.get_origin(nt) in [tuple, typing.Tuple]
    args = typing_inspect.get_args(nt, evaluate=True)
    assert args[0] is int
    assert args[1] is str

    # Union
    t = dtype_new.Union([dtype_new.Int(), dtype_new.Str()])
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


def test_extract_type_var():
    dt = dtype_new

    t = dt.TypeVar("T")
    u = dt.TypeVar("U")

    assert dt.extract_type_var(t) == {t}
    assert dt.extract_type_var(dt.Int()) == set()
    assert dt.extract_type_var(dt.Tuple([t])) == {t}
    assert dt.extract_type_var(dt.Union([t, u])) == {t, u}
    assert dt.extract_type_var(dt.Union([t, dt.Int()])) == {t}
    assert dt.extract_type_var(dt.List(t)) == {t}
    assert dt.extract_type_var(dt.Dict(t, u)) == {t, u}
    assert dt.extract_type_var(dt.Const(t)) == {t}
    assert dt.extract_type_var(dt.Dict(dt.Str(), dt.List(t))) == {t}
    assert dt.extract_type_var(dt.Union([t, dt.Int(), dt.Union([u, dt.Str()])])) == {t, u}


def test_check_type_var():
    dt = dtype_new

    t = dt.TypeVar("T")

    assert dt.check_type_var(t, t)
    assert dt.check_type_var(t, dt.Int())
    assert not dt.check_type_var(dt.Int(), t)
