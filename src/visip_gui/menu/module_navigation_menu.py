from PyQt5.QtWidgets import QMenu, QAction


class ModuleNavigationMenu(QMenu):
    def __init__(self, parent=None):
        super(ModuleNavigationMenu, self).__init__(parent)

        self.new_workflow = QAction("Create new workflow")
        self.addAction(self.new_workflow)

        self.rename_worklfow = QAction("Rename workflow")
        self.addAction(self.rename_worklfow)

        self.remove_workflow = QAction("Remove workflow")
        self.addAction(self.remove_workflow)

    def contextMenuEvent(self, event):
        #event.accept()
        super(ModuleNavigationMenu, self).contextMenuEvent(event)

    def mousePressEvent(self, event):
        super(ModuleNavigationMenu, self).mousePressEvent(event)