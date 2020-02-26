from PyQt5 import QtGui
from pyqtgraph import parametertree

from visip_gui.parameter_tree_custom.base_widget_param_item import BaseWidgetParamItem


class RootParamItem(BaseWidgetParamItem):
    def __init__(self, param, depth=0):
        opts = param.opts
        temp = {**param.opts}
        #temp["value"] = None
        param.opts = temp
        super(RootParamItem, self).__init__(param, depth)
        param.opts = opts
        #if opts.get('value', None) is not None:
        #    self.widget.setValue(opts['value'])
        #    self.updateDisplayLabel(opts['value'])
        #    #self.valueChanged(self, opts['value'], force=True)
        #else:
        #    ## no starting value was given; use whatever the widget has
        #    self.widgetValueChanged()
        #
        #self.updateDefaultBtn()
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
        
    def valueChanged(self, param, val, force=True):


        if val is not None and val != self.param.opts.get('default', None):
            try:
                self.param.g_action.name = val
                self.hideEditor()
                super(RootParamItem, self).valueChanged(self, val, force)
            except ValueError:
                self.param.g_action._msg_box.exec_()
                val = self.param.opts.get('default', None)
                if val is None:
                    val = self.param.opts.get('value', None)
                self.param.opts['value'] = val
                super(RootParamItem, self).valueChanged(self, val, force)
                self.updateDefaultBtn()
        else:
            super(RootParamItem, self).valueChanged(self, val, force)

        #self.param.g_action.w_data_item.name = val
        #self.param.g_action.scene().update_scene()


