from visip.dev import dtype
from visip.action.constructor import ClassActionBase
from visip.dev.parameters import Parameters, ActionParameter
import ruamel.yaml as yaml

def test_data_class_base():
    parameters = Parameters()
    parameters.append(ActionParameter('x'))
    parameters.append(ActionParameter('y'))
    dclass = ClassActionBase.dataclass_from_params("my_class", parameters, module="my_module")
    assert dclass.yaml_tag == '!my_class'
    my_instance = dclass(x=3, y=7)
    assert my_instance.x == 3
    assert my_instance.y == 7

    # class serialization
    serialized = yaml.dump(my_instance)
    # assert serialized == "!my_module.my_class {x: 3, y: 7}"

