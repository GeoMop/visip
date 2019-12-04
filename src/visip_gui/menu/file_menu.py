"""
Definition of menu.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication


class FileMenu(QtWidgets.QMenu):
    """Definition of menu containing editing options."""
    def __init__(self, parent=None):
        super(FileMenu, self).__init__(parent)
        self.setTitle("File")

        self.new = QtWidgets.QAction("Create New Module...")
        self.addAction(self.new)

        self.open = QtWidgets.QAction("Open Module...")
        self.addAction(self.open)

        self.export = QtWidgets.QAction("Export Module...")
        self.addAction(self.export)

        self.exit = QtWidgets.QAction("Exit")
        self.addAction(self.exit)

        self.exit.triggered.connect(QApplication.quit)
