from visip.action.visipIO import load_yaml, write_yaml
from visip.dev import evaluation
from visip.dev.dtype import DataClassBase
import os

this_folder = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(this_folder, 'test_yamls\\flow_input.yaml')
output_file = os.path.join(this_folder, 'test_yamls\\write_yaml.yaml')

#špatné volání?
def test_io_load():
    action = load_yaml.action
    assert action
    # analysis = evaluation.Evaluation.make_analysis(action, [
    #     'D:\\Git\\muj_visip\\visip\\testing\\action\\test_yamls\\flow_input.yaml'])

    analysis = evaluation.Evaluation.make_analysis(action, [input_file])

    eval = evaluation.Evaluation(analysis)
    assert eval
    result = eval.execute()

    assert result._result['flow123d_version'] == '3.1.0'
    assert isinstance(result._result['problem'].flow_equation, DataClassBase)
    assert result._result['problem'].flow_equation.nonlinear_solver['linear_solver'].a_tol == 1e-07

    print(result._result)

    loaded_dict = result._result
    return loaded_dict


# def test_io_write():
#     action = write_yaml.action
#     assert action
#     # analysis = evaluation.Evaluation.make_analysis(action, [
#     #     'D:\\Git\\muj_visip\\visip\\testing\\action\\test_yamls\\flow_input.yaml'])
#
#     # test_dict = '''
#     # {solute_equation=Coupling_OperatorSplitting(transport=Solute_Advection_FV(input_fields=[{'region': 'ALL', 'init_conc': [1.0, 0.0], 'porosity': 0.25}, {'region': '.BOUNDARY', 'bc_conc': 0}]), substances=['A', 'B']}
#     # '''
#     analysis = evaluation.Evaluation.make_analysis(action, [dict({'pokus': 'prvni'}), output_file])
#
#     eval = evaluation.Evaluation(analysis)
#     assert eval
#     result = eval.execute()
#
#     print(result._result)
