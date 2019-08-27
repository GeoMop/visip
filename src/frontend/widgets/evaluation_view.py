"""
View of currently running evaluation.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
from PyQt5 import QtGui, QtCore

from frontend.widgets.base.g_base_model_view import GBaseModelView
from frontend.widgets.evaluation_scene import EvaluationScene


class EvaluationView(GBaseModelView):
    def __init__(self, eval_gui, task=None,  parent=None):
        super(EvaluationView, self).__init__(parent)
        if task is None:
            task = eval_gui.evaluation.final_task.parent
        self.scene = EvaluationScene(eval_gui, task)
        self.setScene(self.scene)



