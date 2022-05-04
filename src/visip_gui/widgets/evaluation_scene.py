"""
Scene of currently running evaluation.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
from PyQt5.QtCore import QPoint

from visip import _Value
from visip.dev.action_instance import ActionCall
from visip.dev.action_workflow import _SlotCall
from visip.dev import dtype
from visip.dev.task import Status
from visip_gui.data.g_action_data_model import GActionData
from visip_gui.graphical_items.g_action import GAction
from visip_gui.graphical_items.g_action_background import ActionStatus
from visip_gui.graphical_items.g_action_ref import GActionRef
from visip_gui.graphical_items.g_input_action import GInputAction
from visip_gui.widgets.base.g_base_model_scene import GBaseModelScene
from visip_gui.widgets.composite_type_view import CompositeTypeView

StatusMaping = {
    Status.none: ActionStatus.IDLE,
    Status.composed: ActionStatus.READY,
    Status.assigned: ActionStatus.READY,
    Status.determined: ActionStatus.READY,
    Status.ready: ActionStatus.READY,
    Status.submitted: ActionStatus.READY,
    Status.running: ActionStatus.READY,
    Status.finished: ActionStatus.DONE
}


class EvaluationScene(GBaseModelScene):
    def __init__(self, eval_gui, task, parent=None):
        super(EvaluationScene, self).__init__(task.action, parent)
        self.eval_gui = eval_gui
        self.task = task
        self.initialize_scene_from_workflow(task.action)
        self.update_states()
        self.selectionChanged.connect(self.on_selection_changed)

    def initialize_scene_from_workflow(self, workflow):
        self._clear_actions()
        self.workflow = workflow
        for action_name in {**self.workflow.action_call_dict, "__result__": self.workflow._result_call}:
            self._add_action(QPoint(0.0, 0.0), action_name)

        self.update_scene()
        self.order_diagram()
        self.update_scene()
        #self.parent().center_on_content = True

    def draw_action(self, item):
        action = {**self.workflow.action_call_dict, "__result__":self.workflow._result_call}.get(item.data(GActionData.NAME))

        if action is None:
            action = self.unconnected_actions.get(item.data(GActionData.NAME))

        if not isinstance(action.action, _Value) or isinstance(action.action.value, dtype._ActionBase):
            if isinstance(action, _SlotCall):
                self.actions.append(GInputAction(item, action, self.root_item, self.eval_gui, False))
            elif isinstance(action, ActionCall):
                if isinstance(action.action, _Value):
                    self.actions.append(GActionRef(item, action, self.root_item, self.eval_gui, False))
                else:
                    self.actions.append(GAction(item, action, self.root_item, self.eval_gui, False))

            self.actions[-1].widget = CompositeTypeView()
            for child in item.children():
                self.draw_action(child)

            self.update()

    def update_states(self, finished=False):
        if self.task.childs is not None:
            for instance_name, task in self.task.childs.items():
                if isinstance(task.action, _Value):
                    if not isinstance(task.action.value, dtype._ActionBase):
                        continue

                action = self.get_action(instance_name)
                status = StatusMaping[task.status]
                if action.status != status:
                    action.status = status
                    action.widget.set_data(self.eval_gui.cached_result(task.result_hash))
        if not self.eval_gui.eval_thread.is_alive() and not finished:
            self.eval_gui.finished.emit()

    def on_selection_changed(self):
        data_editor = self.eval_gui.eval_window.data_editor
        if len(self.selectedItems()) == 1:
            data_editor.set_action(self.workflow, self.selectedItems()[0])

        else:
            data_editor.clear()

