from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QListWidget, QListWidgetItem


class EvaluationNavigation(QListWidget):
    def __init__(self, eval_gui, parent=None):
        super(EvaluationNavigation, self).__init__(parent)
        self.stack = []
        self.eval_gui = eval_gui

    def add_item(self, task, task_name):
        self.stack.append(task)
        if self.count() != 0:
            self.mark_item(self.item(0), True)

        if task == task.parent:
            item = QListWidgetItem("Analysis: \"" + task_name + "\"")
        else:
            item = QListWidgetItem(task.action.name + ": \"" + task_name + "\"")
        self.insertItem(0, item)
        self.clearSelection()
        item.setSelected(True)
        self.mark_item(item)

    def mark_item(self, item, unmark=False):
        font = QFont()
        if not unmark:
            font.setBold(True)
        item.setFont(font)

    def current_task(self):
        return self.stack[-1]

    def mouseDoubleClickEvent(self, event):
        self.mark_item(self.item(0), True)
        while self.item(0).data(0) != self.currentItem().data(0):
            self.takeItem(0)
            self.stack.pop()

        self.mark_item(self.item(0))
        self.eval_gui.change_view(self.stack[-1])


