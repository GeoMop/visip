from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStackedWidget, QLabel, QVBoxLayout, QWidget, QPushButton


class Tab(QStackedWidget):
    def __init__(self, module_view):
        super(Tab, self).__init__()
        self.last_category = 0

        self.module_view = module_view
        self.user_hint_widget = self.create_user_hint_widget()
        self.addWidget(self.user_hint_widget)

    def create_user_hint_widget(self):
        user_hint_widget = QWidget()
        layout = QVBoxLayout(user_hint_widget)
        layout.addStretch()

        user_hint = QLabel("This module doesn't contain any workflows.")
        user_hint.setAlignment(Qt.AlignCenter)
        layout.addWidget(user_hint)

        new = QPushButton("Create new workflow")
        layout.addWidget(new)
        new.setStyleSheet('QPushButton {color: blue; border:0px}')
        new.clicked.connect(self.module_view.menu.new_workflow.trigger)
        layout.addStretch()
        return user_hint_widget


    def addWidget(self, q_widget):
        temp = self.count()
        if self.count() == 1 and self.currentWidget() is self.user_hint_widget:
            self.removeWidget(self.user_hint_widget)
        super(Tab, self).addWidget(q_widget)

    def removeWidget(self, q_widget):
        if self.count() == 1 and self.currentWidget() is not self.user_hint_widget:
            self.addWidget(self.user_hint_widget)

        super(Tab, self).removeWidget(q_widget)



