from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QSizePolicy
from pyqtgraph import parametertree

from visip import _Value


class SlotParamItem(parametertree.parameterTypes.WidgetParameterItem):
    def __init__(self, param, depth):
        param.opts['enabled'] = False
        param.opts['default'] = 'None'
        #self._constant.sigValueChanged.connect(self.on_constant_change)
        value = param.get_data()

        super(SlotParamItem, self).__init__(param, 0)
        self.updateDepth(depth)
        self.valueChanged(param, value)

        #print(self.widget.sizePolicy().horizontalPolicy())
        #print(self.widget.sizePolicy().verticalPolicy())
        #self.widget.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)

    def updateDepth(self, depth):
        ## Change item's appearance based on its depth in the tree
        ## This allows highest-level groups to be displayed more prominently.
        if depth == 0:
            for c in [0, 1]:
                self.setBackground(c, QtGui.QBrush(QtGui.QColor(100, 100, 100)))
                self.setForeground(c, QtGui.QBrush(QtGui.QColor(220, 220, 255)))
                font = self.font(c)
                font.setBold(True)
                font.setPointSize(font.pointSize() + 1)
                self.setFont(c, font)
                #self.setSizeHint(0, QtCore.QSize(0, 30))
        else:
            for c in [0, 1]:
                self.setBackground(c, QtGui.QBrush(QtGui.QColor(220, 220, 220)))
                self.setForeground(c, QtGui.QBrush(QtGui.QColor(50, 50, 50)))
                font = self.font(c)
                font.setBold(True)
                # font.setPointSize(font.pointSize()+1)
                self.setFont(c, font)
                #self.setSizeHint(0, QtCore.QSize(0, 20))

    def valueChanged(self, param, val):
        super(SlotParamItem, self).valueChanged(param, val)
        if val != '' and\
                self.param.arg is not None and\
                self.param.arg.value is not None and\
                isinstance(self.param.arg.value.action, _Value):

            try:
                self.param.arg.value.action.value = int(val)
            except ValueError:
                try:
                    self.param.arg.value.action.value = float(val)
                except ValueError:
                    if val[0] + val[-1] == "''" or val[0] + val[-1] == '""':
                        self.param.arg.value.action.value = val[1:-1]
                    elif val == 'None':
                        self.param.arg.value.action.value = None
                    else:
                        print('Changing composite type not implemented yet!')
                        return

        self.hideEditor()

    def setFocus(self):
        pass



