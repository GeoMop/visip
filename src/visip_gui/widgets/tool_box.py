import importlib.util

from PyQt5.QtWidgets import QToolBox

from visip import _Slot
from visip.code.dummy import Dummy
from visip.dev.action_instance import ActionCall
from visip.dev.action_workflow import _SlotCall
from visip.code.dummy import DummyAction
from visip.dev import dtype

from visip_gui.config.config_data import ConfigData
from visip_gui.data.tree_item import TreeItem
from visip_gui.dialogs.import_module import ImportModule
from visip_gui.graphical_items.g_action import GAction
from visip_gui.graphical_items.g_input_action import GInputAction
from visip_gui.widgets.action_category import ActionCategory

import visip

from visip_gui.widgets.toolbox_view import ToolboxView


class ToolBox(QToolBox):
    BASE_MODULE_NAME = "visip"
    def __init__(self, main_widget, parent=None):
        super(ToolBox, self).__init__(parent)
        self.main_widget = main_widget

        self.system_actions_layout = ActionCategory(self.BASE_MODULE_NAME)
        self.action_database = {self.BASE_MODULE_NAME: {}}

        self.cfg = ConfigData()
        self.module = None
        self.workspace = None
        temp = visip.base_system_actions
        #for action in visip.base_system_actions:
        #    if isinstance(action, _Slot):
        #        inst = _SlotCall("Slot")
        #        g_action = GInputAction(TreeItem(["Input", 0, 0, 50, 50]), inst)
        #        g_action.hide_name(True)
        #        ToolboxView(g_action, self.system_actions_layout)
        #    elif not isinstance(action, Dummy):
        #        inst = ActionCall.create(action)
        #        g_action = GAction(TreeItem([action.name, 0, 0, 50, 50]), inst)
        #        g_action.hide_name(True)
        #        ToolboxView(g_action, self.system_actions_layout)

        #    if action.module not in self.action_database:
        #        self.action_database[action.module] = {}
        #    self.action_database[action.module][action.name] = action

        # ToolboxView(GAction(TreeItem(["List", 0, 0, 50, 50]), instance.ActionInstance.create( dev.List())), toolbox_layout2)
        self.setMinimumWidth(180)
        #self.addItem(self.system_actions_layout, "System actions")
        # self.toolBox.addItem(toolbox_layout2, "Data manipulation")

        self.import_modules = {}

    def update_category(self):
        if self.module is not None:
            self.on_workspace_change(self.module, self.workspace)

    def on_workspace_change(self, module, curr_workspace):
        last_index = self.currentIndex()
        if module.name in self.import_modules:
            category_index = self.indexOf(self.import_modules[module.name])
            self.removeItem(category_index)
            self.action_database.pop(module.name)
        else:
            category_index = self.count()
        module_category = ActionCategory(module.name)
        if module.definitions:
            self.action_database[module.name] = {}
            for item in module.definitions:
                #if not item.is_analysis and item.name != curr_workspace.scene.workflow.name:
                g_action = GAction(TreeItem([item.name, 0, 0, 50, 50]), ActionCall.create(item))
                g_action.hide_name(True)
                ToolboxView(g_action, module_category)
                self.action_database[module.name][item.name] = item

            self.import_modules[module.name] = module_category
            self.insertItem(category_index, module_category, module.name)
            self.setCurrentIndex(last_index)
            self.workspace = curr_workspace

    def on_module_change(self, module, curr_workspace):
        while self.count() > 0:
            self.removeItem(self.count()-1)
        #temp = self.action_database[self.BASE_MODULE_NAME]
        self.action_database.clear()
        self.import_modules.clear()
        #self.action_database[self.BASE_MODULE_NAME] = temp
        #self.addItem(self.system_actions_layout, "System actions")
        self.module = module
        if module is not None:
            self.on_workspace_change(module, curr_workspace)

            for m in module.imported_modules:
                m = m.py_module
                item = None
                for obj in m.__dict__.values():
                    if issubclass(type(obj), DummyAction):
                        item = obj
                        break
                if item is not None:
                    module_name = module.object_name(m)
                    module_category = ActionCategory(module_name)
                    self.action_database[module_name] = {}
                    for name, obj in m.__dict__.items():
                        if issubclass(type(obj), DummyAction):
                            item = obj._action_value
                            g_action = GAction(TreeItem([item.name, 0, 0, 50, 50]),
                                                ActionCall.create(item))
                            g_action.hide_name(True)
                            ToolboxView(g_action, module_category)
                            self.action_database[module_name][item.name] = item

                    self.import_modules[module_name] = module_category
                    if m.__name__ != self.BASE_MODULE_NAME:
                        self.addItem(module_category, module_name)
                    else:
                        index = 0
                        for action in visip.base_system_actions:
                            if isinstance(action, _Slot):
                                inst = _SlotCall("Slot", None)
                                g_action = GInputAction(TreeItem(["Input", 0, 0, 50, 50]), inst)
                                g_action.hide_name(True)
                                ToolboxView(g_action, module_category, index)
                                index += 1
                            elif not isinstance(action, Dummy):
                                inst = ActionCall.create(action)
                                g_action = GAction(TreeItem([action.name, 0, 0, 50, 50]), inst)
                                g_action.hide_name(True)
                                ToolboxView(g_action, module_category, index)
                                index += 1

                            if module_name not in self.action_database:
                                self.action_database[module_name] = {}
                            self.action_database[module_name][action.name] = action
                        temp = self.insertItem(0, module_category, module_name)
                        pass


    def contextMenuEvent(self, event):
        dialog = ImportModule(self.parent())
        if dialog.exec():
            temp = self.module.load_module(dialog.filename())
            self.module.insert_imported_module(temp, dialog.name())
            self.on_module_change(self.module, self.workspace)
            self.setCurrentIndex(self.count() - 1)



