import pytest
import os

from visip.dev import evaluation, task, module
from visip.code import decorators

script_dir = os.path.dirname(os.path.realpath(__file__))

@pytest.mark.parametrize("src_file", ["analysis_in.py"])
def test_evaluation(src_file):
    base_dir = os.path.join(script_dir, "..", "code", "visip_sources")
    source_in_path = os.path.join(base_dir, src_file)


    mod = module.Module.load_module(source_in_path)
    wf_test_class = mod.get_action(name='test_class')
    assert sorted(list(wf_test_class.action_call_dict.keys())) == ['Point_1', 'Value_1', 'Value_2', '__result__', 'a', 'a_x', 'b', 'b_y']
    Point = mod.get_action(name='Point')
    pa = Point.evaluate(x=0, y=1)
    pb = Point.evaluate(x=2, y=3)

    # TODO: support for argument binding in the code wrapper.
    # Implement it as a function that creates a bind workflow consisting of the
    # binded action and few Value action instances.
    # Then make_analysis (which binds all parameters) can be replaced this more general feature.
    eval = evaluation.Evaluation()
    analysis = eval._make_analysis(wf_test_class, [pa, pb], {})
    assert sorted(list(analysis.action_call_dict.keys())) == ['Value_1', 'Value_2', '__result__', 'test_class_1']
    result = eval.execute(analysis)

    assert isinstance(result._task, task.Composed)
    res = result.result
    assert isinstance(res, Point._data_class)
    assert res.x == 0
    assert res.y == 3

    # first level workflow
    assert result._task.action == analysis
    assert result.child('Value_1')._task.action.value == pa
    test_wf_task = result.child('test_class_1')

    # second level workflow
    assert test_wf_task._task.action == wf_test_class
    assert test_wf_task.result.x == 0
    assert test_wf_task.result.y == 3
    assert test_wf_task.child('a_x').result == 0
    assert test_wf_task.child('b_y').result == 3

global_n_calls = 0

@decorators.action_def
def count_calls(a: int) -> int:
    global global_n_calls
    global_n_calls += 1
    return 2 * a


@decorators.analysis
def make_calls(self):
    return [
        count_calls(0),
        count_calls(1),
        count_calls(0)]


def test_action_skipping():
    """
    Test skipping already performed actions. Currently only within single
    evaluation.
    :return:
    """
    result = evaluation.run(make_calls)
    assert len(result) == 3
    assert global_n_calls == 2
