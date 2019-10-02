import common as analysis
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
    cca = common.dev.type.closest_common_ancestor
    assert cca(D, E) is B
    assert cca(C, D) is A
    assert cca(A, B) is A
    assert cca(A, int) is object




@pytest.mark.parametrize("src_file", ["analysis_in.py", "dep_module_in.py", 'quadrature_in.py'])
def test_representation(src_file):
    base, ext = os.path.splitext(src_file)
    assert ext == ".py"
    tokens = base.split('_')
    base = '_'.join(tokens[:-1])
    _in = tokens[-1]
    assert _in == "in"

    base_dir = "visip_sources"
    source_in_path = os.path.join(base_dir, src_file)
    round_src_path = os.path.join(base_dir, "{}.round.py".format(base))
    round2_src_path = os.path.join(base_dir, "{}.round2.py".format(base))
    reference_path = os.path.join(base_dir, "{}.ref.py".format(base))

    module = analysis.module.Module(source_in_path)
    code = module.code()
    with open(round_src_path, "w") as f:
        f.write(code)

    round_module = analysis.module.Module(round_src_path)
    round_code = round_module.code()
    assert code == round_code

    with open(round2_src_path, "w") as f:
        f.write(round_code)
    with open(reference_path, "r") as f:
        ref_code = f.read()
    assert code == ref_code, "round_code_file: {}  != ref_code_file: {}".format(round2_src_path, reference_path)

# def test_module()
#     module = analysis.module.Module("dep_module_in.py")
#
#     # access module imports
#
#     # access definitions of the module
#     module

