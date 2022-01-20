"""
Test dev/parameters.py which should be renamed to signature.py
after significant merges with RS branches.
"""
from typing import *
from visip.dev.parameters import Parameters, ActionParameter as AP
from visip.dev.extract_signature import _extract_signature

def fa(a:bool, /, b:int, *args: Tuple[bool], c:float, **kwargs: Tuple[int]) -> Tuple[float]:
    pass

def fb(self, a:bool) -> bool:
    pass

def fc(self, b:int=0) -> int:
    pass

def test_signature():
    s = _extract_signature(fa)
    assert len(s) == 5
    # kinds
    kinds = [p.kind for p in s]
    ref_kinds = [AP.POSITIONAL_ONLY, AP.POSITIONAL_OR_KEYWORD, AP.VAR_POSITIONAL, AP.KEYWORD_ONLY, AP.VAR_KEYWORD]
    assert ref_kinds == kinds

    # get item, names
    names = []
    for p in s:
        assert p.name == s[p.name].name
        names.append(p.name)
    # at
    for i in range(3):
        assert s.at(i).name == names[i]

    # types
    assert str(s.return_type) == 'typing.Tuple[float]'
    ref_param_types = [
        'bool',
        'int',
        'float',
        'typing.Tuple[bool]',
        'typing.Tuple[int]'
    ]

    s1 = _extract_signature(fb, omit_self=True)
    assert len(s1) == 1
    assert s1['a'].get_default()[0] == False

    s2 = _extract_signature(fc, omit_self=False)
    assert len(s2) == 2
    assert s2['b'].get_default() == (True, 0)
