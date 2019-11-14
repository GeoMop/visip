import importlib.util

from PyQt5.QtWidgets import QToolBox

from visip import Slot
from visip.code.dummy import Dummy
from visip.dev.action_workflow import SlotInstance
from visip.code.wrap import ActionWrapper
from frontend.config.config_data import ConfigData
from frontend.data.tree_item import TreeItem
from frontend.dialogs.import_module import ImportModule
from frontend.graphical_items.g_action import GAction
from frontend.graphical_items.g_input_action import GInputAction
from frontend.widgets.action_category import ActionCategory

import visip
import visip.dev.action_instance as instance

from frontend.widgets.toolbox_view import ToolboxView


class ToolBox(QToolBox):
    def __init__(self, main_widget, parent=None):
        super(ToolBox, self).__init__(parent)
        self.main_widget = main_widget

        self.system_actions_layout = ActionCategory()
        self.action_database = {"wf": {}}

        self.cfg = ConfigData()
        self.module = None
        self.workspace = None
        temp = visip.base_system_actions
        for action in visip.base_system_actions:
            if isinstance(action, Slot):
                inst = SlotInstance("Slot")
                g_action = GInputAction(TreeItem(["Input", 0, 0, 50, 50]), inst)
                g_action.hide_name(True)
                ToolboxView(g_action, self.system_actions_layout)
            elif not isinstance(action, Dummy):
                inst = instance.ActionInstance.create(action)
                g_action = GAction(TreeItem([action.name, 0, 0, 50, 50]), inst)
                g_action.hide_name(True)
                ToolboxView(g_action, self.system_actions_layout)

            self.action_database[action.module][action.name] = action

        # ToolboxView(GAction(TreeItem(["List", 0, 0, 50, 50]), instance.ActionInstance.create( dev.List())), toolbox_layout2)
        self.setMinimumWidth(180)
        self.addItem(self.system_actions_layout, "System actions")
        # self.toolBox.addItem(toolbox_layout2, "Data manipulation")

        self.import_modules = {}


    def on_workspace_change(self, module, curr_workspace):
        last_index = self.currentIndex()
        if module.name in self.import_modules:
            category_index = self.indexOf(self.import_modules[module.name])
            self.removeItem(category_index)
            self.action_database.pop(module.name)
        else:
            category_index = self.count()
        module_category = ActionCategory()
        if module.definitions:
            self.action_database[module.name] = {}
            for item in module.definitions:
                if not item.is_analysis and item.name != curr_workspace.scene.workflow.name:
                    g_action = GAction(TreeItem([item.name, 0, 0, 50, 50]),
                                        instance.ActionInstance.create(item))
                    g_action.hide_name(True)
                    ToolboxView(g_action, module_category)
                    self.action_database[item.module][item.name] = item

            self.import_modules[module.name] = module_category
            self.insertItem(category_index, module_category, module.name)
            self.setCurrentIndex(last_index)
            self.workspace = curr_workspace

    def on_module_change(self, module, curr_workspace):
        while self.count() > 1:
            self.removeItem(self.count()-1)
            temp = self.action_database["wf"]
            self.action_database.clear()
            self.import_modules.clear()
            self.action_database["wf"] = temp
        #self.addItem(self.system_actions_layout, "System actions")
        self.module = module
        if module is not None:
            self.on_workspace_change(module, curr_workspace)

            for m in module.imported_modules:
                if m.__name__ != "common":
                    module_category = ActionCategory()
                    self.action_database[m.__name__] = {}
                    for name, obj in m.__dict__.items():
                        if issubclass(type(obj), ActionWrapper):
                            item = obj.action
                            g_action = GAction(TreeItem([item.name, 0, 0, 50, 50]),
                                                instance.ActionInstance.create(item))
                            g_action.hide_name(True)
                            ToolboxView(g_action, module_category)
                            self.action_database[item.module][item.name] = item

                    self.import_modules[item.module] = module_category
                    self.addItem(module_category, m.__name__)

    def contextMenuEvent(self, event):
        dialog = ImportModule(self.parent())
        if dialog.exec():
            import os
            relpath = os.path.relpath(dialog.filename(), self.cfg.module_root_directory)
            namespace = os.path.dirname(relpath).replace(os.sep, ".")
            spec = importlib.util.spec_from_file_location(namespace, dialog.filename())
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.module.insert_imported_module(module, dialog.name())
            self.on_module_change(self.module, self.workspace)



