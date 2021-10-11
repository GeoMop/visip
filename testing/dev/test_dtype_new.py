from visip.dev import dtype_new, dtype

import typing


def test_from_typing():
    # base
    assert isinstance(dtype_new.from_typing(int), dtype_new.Int)
    assert isinstance(dtype_new.from_typing(float), dtype_new.Float)
    assert isinstance(dtype_new.from_typing(bool), dtype_new.Bool)
    assert isinstance(dtype_new.from_typing(str), dtype_new.Str)


    # VarType
    t = typing.TypeVar("T")
    nt = dtype_new.from_typing(t)
    assert isinstance(nt, dtype_new.VarType)
    assert nt.name == t.__name__


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


    # Class
    class A(dtype.DataClassBase):
        pass


    nt = dtype_new.from_typing(A)
    assert isinstance(nt, dtype_new.Class)
    assert nt.module == A.__module__
    assert nt.name == A.__name__


def test_is_subtype():
    assert not dtype_new.is_subtype(dtype_new.Int(), dtype_new.Int())
