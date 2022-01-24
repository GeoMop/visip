from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton


class NoWorkflowTab(QWidget):
    def __init__(self, fnc_create_new_workflow, parent=None):
        super(NoWorkflowTab, self).__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.addStretch()
        self.welcome = QLabel("This module is empty.")
        self.welcome.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.welcome)

        self.new = QPushButton("Create new workflow...")
        self.layout.addWidget(self.new)
        self.new.setStyleSheet('QPushButton {color: blue; border:0px}')
        self.new.clicked.connect(fnc_create_new_workflow)

        self.layout.setAlignment(self.welcome, Qt.AlignCenter)

        self.layout.addStretch()