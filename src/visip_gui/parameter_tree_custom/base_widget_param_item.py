from PyQt5 import QtCore
from pyqtgraph import parametertree


class BaseWidgetParamItem(parametertree.parameterTypes.WidgetParameterItem):
    def widgetEventFilter(self, obj, ev):
        ## filter widget's events
        ## catch TAB to change focus
        ## catch focusOut to hide editor
        if ev.type() == ev.KeyPress:
            if ev.key() == QtCore.Qt.Key_Tab:
                self.focusNext(forward=True)
                return True  ## don't let anyone else see this event
            elif ev.key() == QtCore.Qt.Key_Backtab:
                self.focusNext(forward=False)
                return True  ## don't let anyone else see this event
            elif ev.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                pass
                #self.hideEditor()
            elif ev.key() == QtCore.Qt.Key_Escape:
                pass

        elif ev.type() == ev.FocusOut:
            pass
            #self.hideEditor()

        return False




