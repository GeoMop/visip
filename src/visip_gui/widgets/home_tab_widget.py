from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton


class HomeTabWidget(QWidget):
    def __init__(self, main_widget, parent=None):
        super(HomeTabWidget, self).__init__(parent)
        self.main_widget = main_widget
        self.layout = QVBoxLayout(self)
        self.layout.addStretch()
        self.welcome = QLabel("Welcome to VISIP.\nStart by opening existing module or create a new one.")
        self.welcome.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.welcome)

        self.open = QPushButton("Open module...")
        self.layout.addWidget(self.open)
        self.open.setStyleSheet('QPushButton {color: blue; border:0px}')
        self.open.clicked.connect(self.main_widget.file_menu.open.trigger)


        self.new = QPushButton("Create new module...")
        self.layout.addWidget(self.new)
        self.new.setStyleSheet('QPushButton {color: blue; border:0px}')
        self.new.clicked.connect(self.main_widget.file_menu.new.trigger)

        self.layout.setAlignment(self.welcome, Qt.AlignCenter)

        self.layout.addStretch()

