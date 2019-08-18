import time

from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

from common.evaluation import Evaluation


class GUIEvaluation(QObject):
    finished = pyqtSignal()
    def __init__(self, analysis):

        self.analysis = analysis
        self.eval = Evaluation(analysis)
        while not self.eval.force_finish:
            QApplication.processEvents()
            self.eval.process()
        self.result = self.eval.final_task
        i = 2






