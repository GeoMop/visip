from pyqtgraph import parametertree

from frontend.parameter_tree_custom.root_param_item import RootParamItem


class RootParam(parametertree.parameterTypes.GroupParameter):
    itemClass = RootParamItem

    def __init__(self, name):
        opts = {'name': "Name:", 'type': 'str', 'value':name}
        super(RootParam, self).__init__(**opts)


