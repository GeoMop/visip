from pyqtgraph import parametertree

from visip_gui.parameter_tree_custom.root_param_item import RootParamItem


class RootParam(parametertree.parameterTypes.GroupParameter):
    itemClass = RootParamItem

    def __init__(self, g_action, **opts):
        self.g_action = g_action
        opts['name'] = 'Name:'
        opts['type'] = 'str'
        opts['value'] = g_action.name
        super(RootParam, self).__init__(**opts)


