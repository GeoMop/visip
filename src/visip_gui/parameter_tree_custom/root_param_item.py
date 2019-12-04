from PyQt5 import QtGui
from pyqtgraph import parametertree

from visip_gui.parameter_tree_custom.base_widget_param_item import BaseWidgetParamItem


class RootParamItem(BaseWidgetParamItem):
    def __init__(self, param, depth=0):
        super(RootParamItem, self).__init__(param, depth)
        super(RootParamItem, self).setExpanded(True)
        for c in [0, 1]:
            self.setBackground(c, QtGui.QBrush(QtGui.QColor(100, 100, 100)))
            self.setForeground(c, QtGui.QBrush(QtGui.QColor(220, 220, 255)))
            font = self.font(c)
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            self.setFont(c, font)

    def setExpanded(self, b):
        super(RootParamItem, self).setExpanded(True)
