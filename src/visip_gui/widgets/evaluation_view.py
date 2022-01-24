"""
View of currently running evaluation.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
from visip_gui.widgets.base.g_base_model_view import GBaseModelView
from visip_gui.widgets.evaluation_scene import EvaluationScene


class EvaluationView(GBaseModelView):
    def __init__(self, eval_gui, task=None,  parent=None):
        super(EvaluationView, self).__init__(parent)
        if task is None:
            task = eval_gui.evaluation.final_task
        self.scene = EvaluationScene(eval_gui, task)
        self.setScene(self.scene)
        self.centerOn(self.scene.root_item)



