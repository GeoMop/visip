import time
import threading

from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QThread, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QListWidgetItem

from common.evaluation import Evaluation
from common.task import Composed, Atomic
from frontend.widgets.evaluation_navigation import EvaluationNavigation
from frontend.widgets.evaluation_view import EvaluationView


class GUIEvaluation(QMainWindow):
    finished = pyqtSignal()
    def __init__(self, analysis):
        super(GUIEvaluation, self).__init__()
        self.analysis = analysis
        self.evaluation = Evaluation(self.analysis)
        thread = threading.Thread(target=self.evaluation.execute, args=())
        thread.start()

        self.view = EvaluationView(self)
        self.setWindowTitle("Evaluating: \"" + self.view.scene.workflow.name + "\"")
        self.setCentralWidget(self.view)

        self.view.scene.update_states()
        temp = self.evaluation.final_task

        self.navigation = EvaluationNavigation(self)
        self.navigation.add_item(self.evaluation.final_task, self.analysis.name)

        self.navigation_dock = QDockWidget("Navigation Stack", self)
        self.navigation_dock.setMinimumWidth(150)

        self.navigation_dock.setWidget(self.navigation)

        self.navigation_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.navigation_dock)
        self.navigation_dock.show()
        self.show()
        self.navigation_dock.hide()

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
        self.view = EvaluationView(self, task)
        self.setCentralWidget(self.view)

