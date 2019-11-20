from visip.action.io import load_yaml
from visip.dev import evaluation


def test_io():
    action = (load_yaml.action)

    analysis = evaluation.Evaluation.make_analysis(action, ['testing/action/test_yamls/flow_input.yaml'])

    eval = evaluation.Evaluation(analysis)

    result = eval.execute()

    print(result)
    # result drží výsledek
