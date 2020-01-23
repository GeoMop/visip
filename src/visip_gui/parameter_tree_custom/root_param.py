from pyqtgraph import parametertree

from visip_gui.parameter_tree_custom.root_param_item import RootParamItem


class RootParam(parametertree.parameterTypes.GroupParameter):
    itemClass = RootParamItem

    def __init__(self, name, **opts):
        opts['name'] = 'Name:'
        opts['type'] = 'str'
        opts['value'] = name
        super(RootParam, self).__init__(**opts)


