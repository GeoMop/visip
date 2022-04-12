import pytest
import os

from visip.dev import evaluation, task, module
from visip.code import decorators

script_dir = os.path.dirname(os.path.realpath(__file__))

@pytest.mark.skip
def test_evaluation():
    enum_sript = "wf_enum.py"
    source_in_path = os.path.join("visip_sources", enum_sript)

    mod = module.Module.load_module(source_in_path)
    wf_test_class = mod.get_action(name='script')

    eval = evaluation.Evaluation()
    analysis = eval._make_analysis(wf_test_class, [], {})
    #assert sorted(list(analysis.action_call_dict.keys())) == ['Value_1', 'Value_2', '__result__', 'test_class_1']
    result = eval.execute(analysis)
