from visip.action.ruamel_visipIO import load_yaml, write_yaml
from visip.dev import evaluation
from visip.dev.dtype import DataClassBase
import os

this_folder = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(this_folder, 'test_yamls', 'flow_input.yaml')
output_file = os.path.join(this_folder, 'test_yamls', 'write_yaml.yaml')


def test_io_load():
    action = load_yaml.action
    assert action

    analysis = evaluation.Evaluation.make_analysis(action, [input_file])

    eval = evaluation.Evaluation(analysis)
    assert eval
    result = eval.execute()

    assert isinstance(result._result, dict)
    assert result._result['flow123d_version'] == '3.1.0'
    assert result._result['problem']['flow_equation']['nonlinear_solver']['linear_solver']['a_tol'] == 1e-07
    assert result._result['problem']['flow_equation']['nonlinear_solver']['linear_solver']['_class_'] == 'Petsc'
    assert result._result['problem']['flow_equation']['nonlinear_solver']['linear_solver']['_module_'] == ''
    # print(result._result)


def prepare_dict_for_write():
    action = load_yaml.action
    analysis = evaluation.Evaluation.make_analysis(action, [input_file])
    eval = evaluation.Evaluation(analysis)
    result = eval.execute()
    return result._result


def test_io_write():
    action = write_yaml.action
    assert action
    analysis = evaluation.Evaluation.make_analysis(action, [prepare_dict_for_write(), output_file])

    eval = evaluation.Evaluation(analysis)
    assert eval
    result = eval.execute()
