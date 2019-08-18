"""
Definition of menu.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
from PyQt5 import QtWidgets, QtGui


class EvalMenu(QtWidgets.QMenu):
    """Definition of menu containing editing options."""
    def __init__(self, parent=None):
        super(EvalMenu, self).__init__(parent)
        self.setTitle("Evaluation")
        self.evaluate = QtWidgets.QAction("Evaluate...")
        self.addAction(self.evaluate)

