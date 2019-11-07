from PyQt5.QtWidgets import QTabWidget


class EvalTabWidget(QTabWidget):
    def __init__(self):
        super(EvalTabWidget, self).__init__()
        self.evals = {}
        self.setwid

    def add_tab(self, eval_gui):
        name = eval_gui.view.scene.workflow.name
        i = 0
        while name in self.evals:
            name = eval_gui.view.scene.workflow.name + str(i)
            i += 1
        self.evals[name] = eval_gui
        self.addTab(eval_gui.view, name)
        eval_gui.view.ensureVisible(eval_gui.view.scene.root_item.boundingRect())

    def get_eval_gui(self, index):
        return self.evals[self.tabText(index)]


