from PyQt5.QtCore import pyqtSignal
from pyqtgraph import parametertree


class EvalParamItem(parametertree.parameterTypes.WidgetParameterItem):
    def __init__(self, param, depth, on_expand):
        super(EvalParamItem, self).__init__(param, depth)
        self.on_expand = on_expand

    def setExpanded(self, b):
        super(EvalParamItem, self).setExpanded(b)
        if b:
            self.on_expand()

