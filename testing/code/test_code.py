from visip.dev import dtype
from visip.dev import module
import os
import pytest
script_dir = os.path.dirname(os.path.realpath(__file__))







@pytest.mark.parametrize("src_file", ["analysis_in.py", "dep_module_in.py", 'quadrature_in.py', 'wf_complex_in.py', 'import_user_defs_in.py', 'meta_actions_in.py'])
#@pytest.mark.parametrize("src_file", ["analysis_in.py", "dep_module_in.py", 'quadrature_in.py'])
def test_representation(src_file):
    base, ext = os.path.splitext(src_file)
    assert ext == ".py"
    tokens = base.split('_')
    base = '_'.join(tokens[:-1])
    _in = tokens[-1]
    assert _in == "in"

    base_dir = os.path.join(script_dir, "visip_sources")
    source_in_path = os.path.join(base_dir, src_file)
    round_src_path = os.path.join(base_dir, "{}.round.py".format(base))
    round2_src_path = os.path.join(base_dir, "{}.round2.py".format(base))
    reference_path = os.path.join(base_dir, "{}.ref.py".format(base))

    test_mod = module.Module(source_in_path)
    code = test_mod.code()
    with open(round_src_path, "w") as f:
        f.write(code)

    round_module = module.Module(round_src_path)
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

