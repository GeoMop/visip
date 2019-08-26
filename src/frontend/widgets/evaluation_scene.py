"""
Scene of currently running evaluation.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
from PyQt5.QtCore import QPoint

from common.task import Status
from frontend.graphical_items.g_action_background import ActionStatus
from frontend.widgets.base.g_base_model_scene import GBaseModelScene

StatusMaping = {
    Status.none: ActionStatus.IDLE,
    Status.composed: ActionStatus.PAUSED,
    Status.assigned: ActionStatus.PAUSED,
    Status.determined: ActionStatus.PAUSED,
    Status.ready: ActionStatus.PAUSED,
    Status.submitted: ActionStatus.PAUSED,
    Status.running: ActionStatus.PAUSED,
    Status.finished: ActionStatus.OK
}


class EvaluationScene(GBaseModelScene):
    def __init__(self, evaluation, parent=None):
        super(EvaluationScene, self).__init__(evaluation.final_task.parent.action, parent)
        self.evaluation = evaluation

        self.initialize_scene_from_evaluation()

    def initialize_scene_from_evaluation(self):
        for action_name in {**self.workflow._actions, "__result__": self.workflow._result}:
            self._add_action(QPoint(0.0, 0.0), action_name)

        self.update_scene()
        self.order_diagram()
        self.update_scene()
        #self.parent().center_on_content = True

    def update_states(self):
        i = 2
        for instance_name, instance in self.evaluation.final_task.childs.items():

            self.get_action(instance_name).status = StatusMaping[instance.status]
