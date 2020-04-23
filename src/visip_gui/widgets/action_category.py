from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout


class ActionCategory(QWidget):
    def __init__(self, name):
        super(ActionCategory, self).__init__()
        self.name = name
        self.inner_layout = QVBoxLayout()
        self.setLayout(self.inner_layout)
        self.items = []

    def add_widget(self, widget):
        self.inner_layout.addWidget(widget,0,Qt.AlignCenter)
        self.items.append(widget)

    def insert_widget(self, index, widget):
        self.inner_layout.insertWidget(index, widget, 0, Qt.AlignCenter)
        self.items.insert(index, widget)

