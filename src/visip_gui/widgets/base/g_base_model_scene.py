"""
Base class of scene of containing DAG.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
import math

from PyQt5 import QtCore
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtWidgets import QGraphicsScene

from visip import _Value
from visip.dev.action_instance import ActionInputStatus
from visip.dev import dtype
from visip_gui.data.g_action_data_model import GActionDataModel
from visip_gui.graphical_items.g_action import GAction
from visip_gui.graphical_items.g_connection import GConnection
from visip_gui.graphical_items.root_action import RootAction
from visip.dev import type_inspector as ti

class GBaseModelScene(QGraphicsScene):
    def __init__(self, workflow, parent=None):
        super(GBaseModelScene, self).__init__(parent)
        self.actions = []
        self.update_model = False
        self.root_item = RootAction()
        self.addItem(self.root_item)

        self.action_model = GActionDataModel()
        self.action_model.dataChanged.connect(self.data_changed)

        self.setSceneRect(QtCore.QRectF(QtCore.QPoint(-10000000, -10000000), QtCore.QPoint(10000000, 10000000)))

        self.new_connection = None
        self.workflow = workflow

        self.unconnected_actions = {}

    def get_action(self, name: str) -> GAction:
        for action in self.actions:
            if action.name == name:
                return action
        assert False, "Action not found!"

    def data_changed(self):
        self.update_model = True

    def update_scene(self):
        # When you start optimizing, start in this function (shame on me!!!)
        if self.update_model and self.new_connection is None:
            self.workflow.update()
            unconnected = self.unconnected_actions.values()
            self.unconnected_actions = {item.name: item for item in unconnected}
            selected = [item.name + 'g' if isinstance(item, GAction) else 'c' for item in self.selectedItems()]
            self.update_model = False
            self.clear()
            self.actions.clear()
            self.root_item = RootAction()
            self.addItem(self.root_item)
            self.workflow.is_analysis = True

            for child in self.action_model.get_item().children():
                self.draw_action(child)

            if self.new_connection is not None:
                self.addItem(self.new_connection)

            all_actions = {**self.workflow.action_call_dict, **self.unconnected_actions, "__result__": self.workflow._result_call}
            for action_name, action in all_actions.items():
                i = 0
                for action_argument in action.arguments:
                    status = action_argument.status
                    if action_argument.parameter.type is not None:
                        if hasattr(action_argument.parameter.type, '__name__'):
                            if dtype.TypeInspector.is_constant(action_argument.parameter.type):
                            #if action_argument.parameter.type.__name__ == "Constant":  # hacky way, but the only one that I found
                                g_action = self.get_action(action_name)
                                port = g_action.in_ports[i]
                                port.set_constant(True)
                    if status != ActionInputStatus.missing:
                        if not isinstance(action_argument.value.action, _Value):
                            self.make_connection(action_name, action_argument.value, i, status)
                        else:
                            if isinstance(action_argument.value.action.value, dtype._ActionBase):
                                self.make_connection(action_name, action_argument.value, i, status)
                            else:
                                g_action = self.get_action(action_name)
                                port = g_action.in_ports[i]
                                port.set_default(True)

                    i += 1
            actions = {item.name + 'g' if isinstance(item, GAction) else 'c': item for item in self.items() if hasattr(item, 'name')}
            for uid in selected:
                select = actions.get(uid, None)
                if select is None:
                    print('Ooops...')
                select.setSelected(True)

            self.update()

    def make_connection(self, action_name, arg_value, arg_index, arg_status):
        g_action = self.get_action(arg_value.name)
        port1 = g_action.out_ports[0]

        g_action = self.get_action(action_name)
        port2 = g_action.in_ports[arg_index]
        conn = GConnection(port1, port2, arg_status, self.root_item)
        if isinstance(arg_value.action, _Value) and isinstance(arg_value.action.value, dtype._ActionBase):
            conn.setPen(conn.dash_pen)


        port1.connections.append(conn)
        port2.connections.append(conn)
        # self.addItem(port1.connections[-1])

    def draw_action(self, item):
        raise NotImplementedError

    def order_diagram(self):
        #todo: optimize by assigning levels when scanning from bottom actions
        if self.actions:
            queue = []
            for action in self.actions:
                if action.previous_actions():
                    action.level = self.get_distance(action)
                else:
                    queue.append(action)

            for action in queue:
                action.level = math.inf
                for next_action in action.next_actions():
                    action.level = min(next_action.level - 1, action.level)
            self.reorganize_actions_by_levels()

    def reorganize_actions_by_levels(self):
        actions_by_levels = {}
        for action in self.actions:
            if action.level in actions_by_levels:
                actions_by_levels[action.level].append(action)
            else:
                actions_by_levels[action.level] = [action]
        levels = list(actions_by_levels.keys())
        levels.sort()
        base_item = actions_by_levels[levels[0]][-1]
        prev_y = base_item.y()
        max_height = base_item.height
        for level in levels:
            for item in actions_by_levels[level]:
                max_height = max(max_height, item.height)
            for item in actions_by_levels[level]:
                self.move(item.g_data_item, None, prev_y)
            items = sorted(actions_by_levels[level], key=lambda item:item.x())
            middle = math.floor(len(items)/2)
            prev_x = items[middle].pos().x()
            prev_width = items[middle].width
            for i in range(middle + 1, len(items)):
                if items[i].pos().x() < prev_x + prev_width:
                    prev_x = prev_x + prev_width + 10
                    self.move(items[i].g_data_item, prev_x, None)
                prev_width = items[i].width

            prev_x = items[middle].pos().x()
            prev_width = items[middle].width

            for i in range(middle - 1, -1, -1):
                if items[i].pos().x() + items[i].width > prev_x:
                    prev_x = prev_x - items[i].width - 10
                    self.move(items[i].g_data_item, prev_x, None)

            prev_y = prev_y + max_height + 30

        self.update_model = True
        self.update()

    def rename_action(self,old_name, new_name):
        self.action_model

    def get_distance(self, action):
        prev_actions = set(action.previous_actions())
        next_prev_actions = set()
        dist = 0
        while prev_actions:
            next_prev_actions = next_prev_actions.union(set(prev_actions.pop().previous_actions()))
            if not prev_actions:
                dist += 1
                prev_actions = next_prev_actions
                next_prev_actions = set()

        return dist

    def _add_action(self, new_action_pos, name=None):
        """Create new action and add it to workspace."""
        #[parent, pos] = self.find_top_afs(new_action_pos)
        pos = new_action_pos
        self.action_model.add_item(pos.x(), pos.y(), 50, 50, name)
        self.update_model = True

    def _clear_actions(self):
        del self.action_model
        self.action_model = GActionDataModel()
        self.action_model.dataChanged.connect(self.data_changed)

    def move(self, action, new_x, new_y):
        self.action_model.move(action, new_x, new_y)
        self.update_model = False
        self.update()


    @staticmethod
    def is_action(obj):
        """Return True if given object obj is an g_action."""
        if issubclass(type(obj), GAction):
            return True
        else:
            return False

    def add_connection(self, port):
        pass

    def detach_connection(self, in_port, alt):
        pass

    def wheelEvent(self, event):
        super(GBaseModelScene, self).wheelEvent(event)
        if event.modifiers() & Qt.ControlModifier:
            event.accept()
