import time
import threading

from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QThread, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QDockWidget, QListWidgetItem, QWidget, QVBoxLayout, QLayout
from visip.dev.action_workflow import _Workflow

from visip.dev.evaluation import Evaluation
from visip.dev.task import Composed, Atomic, Status
from visip_gui.widgets.evaluation_navigation import EvaluationNavigation
from visip_gui.widgets.evaluation_scene import EvaluationScene
from visip_gui.widgets.evaluation_view import EvaluationView



class GUIEvaluation(QWidget):
    finished = pyqtSignal()
    def __init__(self, analysis, eval_window):
        super(GUIEvaluation, self).__init__()
        self.view = None
        self.eval_thread = None
        self.running = False
        self.timer = QTimer()
        self.eval_window = eval_window

        self.analysis = analysis
        self.evaluation = Evaluation()

        self.layout = QVBoxLayout(self)
        self.layout.setSizeConstraint(QLayout.SetNoConstraint)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.run()
        self.navigation = EvaluationNavigation(self)
        self.navigation.add_item(self.evaluation.final_task, self.analysis.name)

        self.navigation_dock = eval_window.navigation_dock

        self.finished.connect(self.end_evaluation)

    def run(self):
        self.eval_thread = threading.Thread(target=self.evaluation.execute, args=[self.analysis])
        self.eval_thread.start()
        self.running = True

        self.timer.start(0.25)

        while self.evaluation.final_task is None:
            time.sleep(0.01)

        self.view = EvaluationView(self)
        self.layout.addWidget(self.view)
        self.timer.timeout.connect(self.view.scene.update_states)

        #while thread.is_alive():
        #    QApplication.processEvents()

    def cached_result(self, result_hash):
        return self.evaluation.cache.value(result_hash)

    def end_evaluation(self):
        self.timer.stop()
        if self.evaluation.final_task.status != Status.finished:
            self.evaluation.force_finish = True
            while self.eval_thread.is_alive():
                time.sleep(0.01)
        self.running = False
        self.view.scene.update_states(finished=True)


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
        if not isinstance(task.action, _Workflow):
            if task.childs is not None and len(task.childs) == 1:
                task = list(task.childs.values())[0]
            else:
                assert False, "Multiple tasks inside meta function. Behavior not implemented yet!"
        self.view = EvaluationView(self, task)
        self.layout.addWidget(self.view)
        self.eval_window.data_editor.clear()


