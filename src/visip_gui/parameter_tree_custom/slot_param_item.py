from PyQt5 import QtGui
from visip.dev import dtype

from visip_gui.parameter_tree_custom.base_widget_param_item import BaseWidgetParamItem
from visip import _Value


class SlotParamItem(BaseWidgetParamItem):
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
        if val != '' and\
                self.param.arg is not None and\
                self.param.arg.value is not None and\
                isinstance(self.param.arg.value.action, _Value) and\
                not isinstance(self.param.arg.value.action.value, dtype._ActionBase):
            action = self.param.arg.value.action
            try:
                action.value = int(val)
            except ValueError:
                try:
                    action.value = float(val)
                except ValueError:
                    if ((val[0] + val[-1] == "''" and val.count("'") == 2) or
                            (val[0] + val[-1] == '""' and val.count('"') == 2)):
                        action.value = val[1:-1]
                    elif val == 'None':
                        action.value = None
                    else:
                        print('Changing composite type not implemented yet!')
                        return
        super(SlotParamItem, self).valueChanged(param, val)

    def setFocus(self):
        pass



