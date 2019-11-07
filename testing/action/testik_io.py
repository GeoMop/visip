from visip import action
from visip.action import io


@action
def load():
    data = io.load_yaml('flow_input.yaml')
    print(data)



