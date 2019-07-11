from PyQt5.QtWidgets import QStackedWidget


class Tab(QStackedWidget):
    def __init__(self):
        super(Tab, self).__init__()
        self.last_category = 0
