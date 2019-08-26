"""
View of currently running evaluation.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
from PyQt5 import QtGui, QtCore

from frontend.widgets.base.g_base_model_view import GBaseModelView
from frontend.widgets.evaluation_scene import EvaluationScene


class EvaluationView(GBaseModelView):
    def __init__(self, evaluation, parent=None):
        super(EvaluationView, self).__init__(parent)
        self.scene = EvaluationScene(evaluation)
        self.setScene(self.scene)



