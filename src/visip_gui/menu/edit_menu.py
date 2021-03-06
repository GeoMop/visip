"""
Definition of menu.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
from PyQt5 import QtWidgets, QtGui


class EditMenu(QtWidgets.QMenu):
    """Definition of menu containing editing options."""
    def __init__(self, parent=None):
        super(EditMenu, self).__init__(parent)
        self.setTitle("Edit")

        self.return_callable_action = QtWidgets.QAction("Return as Callable")
        self.addAction(self.return_callable_action)

        self.delete = QtWidgets.QAction("Delete")
        self.delete.setShortcut(QtGui.QKeySequence.Delete)
        self.addAction(self.delete)

        #self.add_random = QtWidgets.QAction("Add random action (for test purposes)")
        #self.addAction(self.add_random)

        self.order_diagram = QtWidgets.QAction("Arrange diagram")
        self.addAction(self.order_diagram)
