from PyQt5.QtWidgets import QMenu, QAction


class ParamMenu(QMenu):
    def __init__(self):
        super(ParamMenu, self).__init__()
        self.const_val = QAction("Set constant value")
        self.addAction(self.const_val)