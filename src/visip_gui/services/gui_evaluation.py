import time
import threading

from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QThread, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QListWidgetItem, QWidget, QVBoxLayout, QLayout

from visip.dev.evaluation import Evaluation
from visip.dev.task import Composed, Atomic
from visip_gui.widgets.evaluation_navigation import EvaluationNavigation
from visip_gui.widgets.evaluation_scene import EvaluationScene
from visip_gui.widgets.evaluation_view import EvaluationView


class GUIEvaluation(QWidget):
    finished = pyqtSignal()
    def __init__(self, analysis, eval_window):
        super(GUIEvaluation, self).__init__()
        self.eval_window = eval_window

        self.analysis = analysis
        self.evaluation = Evaluation(self.analysis)
        thread = threading.Thread(target=self.evaluation.execute, args=())
        thread.start()
        self.layout = QVBoxLayout(self)
        self.layout.setSizeConstraint(QLayout.SetNoConstraint)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.view = EvaluationView(self, parent=self)
        self.layout.addWidget(self.view)

        self.view.scene.update_states()
        temp = self.evaluation.final_task

        self.navigation = EvaluationNavigation(self)
        self.navigation.add_item(self.evaluation.final_task, self.analysis.name)

        self.navigation_dock = eval_window.navigation_dock

        timer = QTimer()
        timer.start(0.25)
        timer.timeout.connect(self.view.scene.update_states)

        self.view.scene.update_states()
        while thread.is_alive():
            QApplication.processEvents()

    def run(self):
        self.eval = Evaluation(self.analysis)
        self.result = self.evaluation.execute()


    def double_click(self, g_action):
        task = self.navigation.current_task().childs[g_action.name]
        if type(task) is Atomic:
            return

        self.navigation.add_item(task, g_action.name)

        self.change_view(task)

        if not self.navigation_dock.isVisible():
            self.navigation_dock.show()

    def change_view(self, task):
        self.layout.removeWidget(self.view)
        self.view = EvaluationView(self, task)
        self.layout.addWidget(self.view)
        self.eval_window.data_editor.clear()


