"""
Scene of currently running evaluation.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
from PyQt5.QtCore import QPoint

from common.action_instance import ActionInstance
from common.action_workflow import SlotInstance
from common.task import Status
from frontend.data.g_action_data_model import GActionData
from frontend.graphical_items.g_action import GAction
from frontend.graphical_items.g_action_background import ActionStatus
from frontend.graphical_items.g_connection import GConnection
from frontend.graphical_items.g_input_action import GInputAction
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
    def __init__(self, eval_gui, task, parent=None):
        super(EvaluationScene, self).__init__(task.action, parent)
        self.eval_gui = eval_gui
        self.task = task
        self.initialize_scene_from_workflow(task.action)
        self.update_states()

    def initialize_scene_from_workflow(self, workflow):
        self._clear_actions()
        self.workflow = workflow
        for action_name in {**self.workflow._actions, "__result__": self.workflow._result}:
            self._add_action(QPoint(0.0, 0.0), action_name)

        self.update_scene()
        self.order_diagram()
        self.update_scene()
        #self.parent().center_on_content = True

    def draw_action(self, item):
        action = {**self.workflow._actions, "__result__":self.workflow._result}.get(item.data(GActionData.NAME))
        if action is None:
            action = self.unconnected_actions.get(item.data(GActionData.NAME))
        if isinstance(action, SlotInstance):
            self.actions.append(GInputAction(item, action, self.root_item, self.eval_gui))
        elif isinstance(action, ActionInstance):
            self.actions.append(GAction(item, action, self.root_item, self.eval_gui))

        for child in item.children():
            self.draw_action(child)

        self.update()

    def update_states(self):
        for instance_name, instance in self.task.childs.items():
            self.get_action(instance_name).status = StatusMaping[instance.status]
