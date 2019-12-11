from PyQt5.QtWidgets import QMenu, QAction


class ModuleNavigationMenu(QMenu):
    def __init__(self, parent=None):
        super(ModuleNavigationMenu, self).__init__(parent)

        self.new_workflow = QAction("Create new workflow")
        self.addAction(self.new_workflow)

        self.remove_workflow = QAction("Remove workflow")
        self.addAction(self.remove_workflow)
