import time
import threading

from PyQt5.QtCore import QTimer, QObject, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow

from common.evaluation import Evaluation
from frontend.widgets.evaluation_view import EvaluationView


class GUIEvaluation(QMainWindow):
    finished = pyqtSignal()
    def __init__(self, analysis):
        super(GUIEvaluation, self).__init__()
        self.analysis = analysis
        self.eval = Evaluation(self.analysis)
        thread = threading.Thread(target=self.eval.execute, args=())
        thread.start()

        self.view = EvaluationView(self.eval)
        self.setWindowTitle("Evaluating: \"" + self.view.scene.workflow.name + "\"")
        self.setCentralWidget(self.view)
        self.show()


        while thread.is_alive():
            QApplication.processEvents()
            self.view.scene.update_states()
        temp = self.eval.final_task
        i = 2

    def run(self):
        self.eval = Evaluation(self.analysis)
        self.result = self.eval.execute()







