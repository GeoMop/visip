import common as analysis
from common import types
import os
import pytest


class A:
    pass
class B(A):
    pass
class C(A):
    pass
class D(B):
    pass
class E(B):
    pass


def test_closest_common_ancestor():
    cca = analysis.types.closest_common_ancestor
    assert cca(D, E) is B
    assert cca(C, D) is A
    assert cca(A, B) is A
    assert cca(A, int) is object




@pytest.mark.parametrize("src_file", ["analysis_in.py", "dep_module_in.py", 'quadrature_in.py'])
def test_representation(src_file):
    module = analysis.module.Module(src_file)
    code = module.code()
    round_module_name = "round."+module.name
    with open(round_module_name +".py", "w") as f:
        f.write(code)

    round_module = analysis.module.Module(round_module_name + ".py")
    round_code = round_module.code()
    assert code == round_code

    with open(round_module_name +".py", "w") as f:
        f.write(round_code)
    base, ext = os.path.splitext(src_file)
    assert ext == ".py"
    tokens = base.split('_')
    base = '_'.join(tokens[:-1])
    _in = tokens[-1]
    assert _in == "in"
    ref_out = "{}.ref.py".format(base)
    with open(ref_out, "r") as f:
        ref_code = f.read()
    assert code == ref_code

# def test_module()
#     module = analysis.module.Module("dep_module_in.py")
#
#     # access module imports
#
#     # access definitions of the module
#     module

