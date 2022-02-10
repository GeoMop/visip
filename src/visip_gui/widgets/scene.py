from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QStaticText, QCursor
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsItem

from visip_gui.graphical_items.g_action_ref import GActionRef
from visip_gui.graphical_items.g_output_action import GOutputAction
from visip import _Value

from visip.dev import dtype
from visip.dev.action_instance import ActionCall
from visip.dev.action_workflow import _SlotCall, _ResultCall, _Slot
from visip_gui.graphical_items.g_input_action import GInputAction
from visip_gui.graphical_items.g_action import GAction
from visip_gui.graphical_items.g_connection import GConnection
from visip_gui.graphical_items.g_port import GOutputPort
from visip_gui.graphical_items.action_for_subactions import GActionForSubactions
from visip_gui.data.g_action_data_model import GActionData
import random

from visip_gui.graphical_items.g_tooltip_item import GTooltipItem
from visip_gui.widgets.base.g_base_model_scene import GBaseModelScene


class ActionTypes:
    ACTION = 0
    CONNECTION = 1


class Scene(GBaseModelScene):
    def __init__(self, main_widget, workflow, available_actions, parent=None):
        super(Scene, self).__init__(workflow, parent)
        self.detached_port = None
        self.available_actions = available_actions

        self.main_widget = main_widget
        self.workflow_name = QGraphicsSimpleTextItem(workflow.name)
        self.workflow_name.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self.selectionChanged.connect(self.on_selection_changed)

        self.new_action_pos = QtCore.QPoint()

        self.initialize_workspace_from_workflow()

    def on_selection_changed(self):
        if len(self.selectedItems()) == 1:
            self.main_widget.property_editor.set_action( self.workflow, self.selectedItems()[0])
            pass
        else:
            self.main_widget.property_editor.clear()

    def initialize_workspace_from_workflow(self):
        for action_name, action in {**self.workflow.action_call_dict, "__result__": self.workflow._result_call}.items():
            if isinstance(action.action, _Value):
                if issubclass(type(action.action.value), dtype._ActionBase):
                    self._add_action(QPoint(0.0, 0.0), action_name)
            else:
                self._add_action(QPoint(0.0, 0.0), action_name)


        self.update_scene()
        self.order_diagram()
        self.update_scene()
        self.parent().center_on_content = True

    def draw_action(self, item):
        action_name = item.data(GActionData.NAME)
        action = self.workflow.action_call_dict.get(action_name)
        if action is None:
            action = self.unconnected_actions.get(action_name)
        assert action is not None, f"Unknown action call name: {action_name}"

        if action is None:
            return

        if isinstance(action.action, _Value):
            if isinstance(action.action.value, dtype._ActionBase):
                self.actions.append(GActionRef(item, action, self.root_item))
        else:
            if isinstance(action.action, _Slot):
                self.actions.append(GInputAction(item, action, self.root_item))
                self.workflow.is_analysis = False
                self.main_widget.toolbox.update_category()
            elif isinstance(action, _ResultCall):
                self.actions.append(GOutputAction(item, action, self.root_item))
            elif isinstance(action, ActionCall):
                self.actions.append(GAction(item, action, self.root_item))

        for child in item.children():
            self.draw_action(child)

    def drawForeground(self, painter, rectf):
        super(Scene, self).drawForeground(painter, rectf)
        painter.resetTransform()
        painter.scale(1.5, 1.5)
        text = QStaticText("Workflow: " + self.workflow.name)
        painter.drawStaticText(QPoint(5,5), text)

    def find_top_afs(self, pos):
        for item in self.items(pos):
            if issubclass(type(item), GActionForSubactions):
                return [item, item.mapFromScene(pos)]
        return [self.root_item, pos]

    def add_random_items(self):
        if not self.actions:
            self.new_action_pos = QtCore.QPoint(0, 0)
            self.add_action()
        for i in range(200):
            if i > 100:
                action = self.actions[random.randint(0,len(self.actions) - 1)]
                self.add_connection(action.in_ports[random.randint(0, len(action.in_ports) - 1)])
                action = self.actions[random.randint(0, len(self.actions) - 1)]
                self.add_connection(action.out_ports[random.randint(0, len(action.out_ports) - 1)])
            else:
                self.new_action_pos = QtCore.QPoint(random.randint(-800, 800), random.randint(-800, 800))
                self.add_action(QtCore.QPoint(random.randint(-800, 800), random.randint(-800, 800)))
                self.update_scene()

    def mouseReleaseEvent(self, release_event):
        super(Scene, self).mouseReleaseEvent(release_event)

    def action_name_changed(self, action_data, new_name):
        if self.action_model.exists(new_name):
            return False
        self.action_model.name_changed(action_data,new_name)
        return True

    def is_graph_acyclic(self):
        leaf_nodes = []
        processed_nodes = []
        acyclic_nodes = []
        for node in self.actions:
            if node.next_actions():
                pass
            else:
                leaf_nodes.append(node)

        while leaf_nodes:
            node = leaf_nodes.pop()
            processed_nodes.append(node)
            acyclic_nodes.append(node)

            prev_actions = node.previous_actions()
            i = 0
            while len(prev_actions) > i:
                curr = prev_actions[i]
                if curr in processed_nodes:
                    return False
                else:
                    processed_nodes.append(curr)
                    for act in curr.previous_actions():
                        if act not in prev_actions:
                            prev_actions.append(act)
                i += 1

        if len(processed_nodes) == len(self.actions):
            return True
        else:
            return False

    # Modifying functions
    def add_action(self, new_action_pos, action_type="wf.List"):
        index = action_type.rfind(".")
        module = action_type[:index]
        action_name = action_type[index + 1:]

        action = self.available_actions[module][action_name]

        if isinstance(action, _Slot):
            action = _SlotCall("slot", None)
            name = self.action_model.add_item(new_action_pos.x(), new_action_pos.y(), 50, 50, action.name)
            action.name = name
            self.workflow.insert_slot(len(self.workflow.slots), None, action)

        elif action_name in self.available_actions[module]:
            action = ActionCall.create(self.available_actions[module][action_name])
            name = self.action_model.add_item(new_action_pos.x(), new_action_pos.y(), 50, 50, action.name)
            action.name = name

        else:
            assert False, "Action isn't supported by scene!"

        self.unconnected_actions[name] = action

    def change_action_to_callable(self):
        actions = self.selectedItems()
        if len(actions) == 1:
            g_action = actions[0]
            base_action = g_action.w_data_item.action
            if not (isinstance(base_action, _Value) and isinstance(base_action.value, dtype._ActionBase)):
                g_data = g_action.g_data_item._item_data
                action_call = ActionCall.create(_Value(base_action))
                action_call.name = g_action.w_data_item.name
                self.delete_items()
                self.action_model.add_item(*g_data[1:], g_data[0])

                self.unconnected_actions[action_call.name] = action_call

    '''
    def add_while_loop(self):
        [parent, pos] = self.find_top_afs(self.new_action_pos)
        self.actions.append(ActionForSubactions(parent, pos))
    '''

    def detach_connection(self, in_port, alt):
        action_name1 = in_port.parentItem().name
        port_index1 = in_port.parentItem().in_ports.index(in_port)
        action_name2 = in_port.connections[0].port1.parentItem().name
        self._delete_connection(in_port.connections[0])
        self.update_model = True
        self.update_scene()
        port1 = self.get_action(action_name1).in_ports[port_index1]
        port2 = self.get_action(action_name2).out_ports[0]
        if alt:
            connected_port = port2
            self.detached_port = port1
        else:
            connected_port = port1
            self.detached_port = port2

        self.add_connection(connected_port)

    def add_connection(self, port):
        """Create new connection from/to specified port and add it to workspace."""
        if self.new_connection is None:
            self.clearSelection()
            if isinstance(port, GOutputPort):
                self.enable_ports(False, False)
            else:
                self.enable_ports(True, False)
            self.new_connection = GConnection(port)
            self.new_connection.tool_tip.disable()
            self.new_connection.unsetCursor()
            self.addItem(self.new_connection)
            self.new_connection.setFlag(QtWidgets.QGraphicsPathItem.ItemIsSelectable, False)
            self.new_connection.set_port2_pos(self.views()[0].mapToScene(self.views()[0].mapFromGlobal(QCursor.pos())))
        else:
            if isinstance(port, GOutputPort):
                self.enable_ports(True, True)
            else:
                self.enable_ports(False, True)
            orig_port = self.new_connection.port1
            self.new_connection.set_port2(port)

            port1 = self.new_connection.port1
            port2 = self.new_connection.port2
            port1.connections.append(self.new_connection)
            port2.connections.append(self.new_connection)
            action1 = port1.parentItem().w_data_item
            action2 = port2.parentItem().w_data_item

            if self.workflow.set_action_input(action2, port2.index, action1):
                self.new_connection.setFlag(QtWidgets.QGraphicsPathItem.ItemIsSelectable, True)
                self.new_connection.setCursor(Qt.ArrowCursor)
                self.new_connection = None
                self.detached_port = None
                self.update_model = True

                if port1.appending_port:
                    port1.appending_port = False

                def update_unconected(action):
                    if action is None:
                        return
                    self.unconnected_actions.pop(action.name, None)
                    for argument in action.arguments:
                        update_unconected(argument.value)

                if action1 in self.workflow.action_call_dict.values():
                    update_unconected(action1)

                if action2 in self.workflow.action_call_dict.values():
                    update_unconected(action2)

                if port2.appending_port:
                    port2.appending_port = False


            else:
                self.tooltip = GTooltipItem(port)
                self.tooltip.set_text("This connection would create cycle.\nThis is not allowed!")
                self.tooltip.tooltip_request(port.boundingRect().center(), Qt.red, 0)
                self._delete_connection(self.new_connection)
                self.new_connection = None
                self.add_connection(orig_port)

    def enable_ports(self, in_ports, enable):
        for action in self.actions:
            for port in action.in_ports if in_ports else action.out_ports:
                port.setEnabled(enable)

            for port in action.in_ports:
                if port.connections:
                    port.setEnabled(enable)

    def keyPressEvent(self, key_event):
        super(Scene, self).keyPressEvent(key_event)
        if key_event.key() == Qt.Key_Escape and not key_event.isAccepted():
            if self.detached_port:
                self.add_connection(self.detached_port)
            else:
                self.removeItem(self.new_connection)
                self.new_connection = None
                self.enable_ports(True, True)
                self.enable_ports(False, True)


    def delete_items(self):
        """Delete all selected items from workspace."""
        if self.new_connection is None:
            while self.selectedItems():

                item = self.selectedItems()[0]
                if self.is_action(item):
                    for port in item.ports():
                        while port.connections:
                            self._delete_connection(port.connections[0])

                    self._delete_action(item)
                else:
                    self._delete_connection(item)

            self.update_model = True
            self.update()

    def _delete_action(self, action):
        """Delete specified action from workspace."""
        if not isinstance(action.w_data_item, _ResultCall):
            self.action_model.removeRow(action.g_data_item.child_number())
            self.actions.remove(action)
            self.removeItem(action)
            self.unconnected_actions.pop(action.name)

            action_call = action.w_data_item
            input_calls = [a.value for a in action_call.arguments if a.value is not None]
            for a in input_calls:
                if isinstance(a.action, _Value) and not isinstance(a.action.value, dtype._ActionBase):
                        self.unconnected_actions.pop(a.name, None)

            if isinstance(action, GInputAction):
                self.workflow.remove_slot(self.workflow.slots.index(action_call))
                self.main_widget.toolbox.update_category()
            action.w_data_item = None

        else:
            action.setSelected(False)

    def _delete_connection(self, conn):
        action1 = conn.port1.parentItem().w_data_item
        action2 = conn.port2.parentItem().w_data_item
        for i in range(len(action2.arguments)):
            if action1 == action2.arguments[i].value:
                self.workflow.set_action_input(action2, i, None)
                break
        if isinstance(action1, _Value) and not isinstance(action1.value, dtype._ActionBase):
            self._delete_action(conn.port1.parentItem())

        def put_all_actions_to_unconnected(action):
            if action is None:
                print('Processing None')
                return
            self.unconnected_actions[action.name] = action
            for argument in action.arguments:
                put_all_actions_to_unconnected(argument.value)

        if action1 not in self.workflow.action_call_dict:
            put_all_actions_to_unconnected(action1)
        conn.port1.connections.remove(conn)
        conn.port2.connections.remove(conn)
        self.removeItem(conn)

    def save_item(self, save_file, item, level=0):
        for child in item.children():
            save_file.write("\t"*level)
            for col in range(child.column_count()):
                save_file.write(str(child.data(col)) + ",")
            save_file.write("\n")
            self.save_item(save_file, child, level+1)

    def save_connection(self, index=QtCore.QModelIndex()):
        for child in self.connection_model.get_item().children():
            self.draw_connection(child)

    def load_item(self):
        pass

    def update_parameters(self):
        self.workflow._parameters = self.workflow.signature_from_dag()