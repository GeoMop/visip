from PyQt5.QtWidgets import QMenu, QAction


class ModuleViewMenu(QMenu):
    def __init__(self, parent=None):
        super(ModuleViewMenu, self).__init__(parent)

        self.show_wf = QAction("Show this workflow")
        self.addAction(self.show_wf)

        self.new_workflow = QAction("Create new workflow")
        self.addAction(self.new_workflow)

        self.remove_workflow = QAction("Remove workflow")
        self.addAction(self.remove_workflow)

        self.mark_wf = QAction("Mark as analysis")
        self.addAction(self.mark_wf)



