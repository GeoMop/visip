from PyQt5.QtWidgets import QToolBox

from common import Slot
from common.dev.action_workflow import SlotInstance
from frontend.data.tree_item import TreeItem
from frontend.graphical_items.g_action import GAction
from frontend.graphical_items.g_input_action import GInputAction
from frontend.widgets.action_category import ActionCategory

import common as analysis
import common.dev.action_instance as instance

from frontend.widgets.toolbox_view import ToolboxView


class ToolBox(QToolBox):
    def __init__(self, main_widget, parent=None):
        super(ToolBox, self).__init__(parent)
        self.main_widget = main_widget

        self.system_actions_layout = ActionCategory()
        self.action_database = {"wf": {}}

        for action in analysis.base_system_actions:
            if isinstance(action, Slot):
                inst = SlotInstance("Slot")
                ToolboxView(GInputAction(TreeItem(["Input", 0, 0, 50, 50]), inst), self.system_actions_layout)
            else:
                inst = instance.ActionInstance.create(action)
                ToolboxView(GAction(TreeItem([action.name, 0, 0, 50, 50]),
                                    inst), self.system_actions_layout)

            self.action_database["wf"][action.name] = action

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
                    ToolboxView(GAction(TreeItem([item.name, 0, 0, 50, 50]),
                                        instance.ActionInstance.create(item)), module_category)
                    self.action_database[module.name][item.name] = item

            self.import_modules[module.name] = module_category
            self.insertItem(category_index, module_category, module.name)
            self.setCurrentIndex(last_index)


    def on_module_change(self, module, curr_workspace):
        while self.count() > 1:
            self.removeItem(self.count()-1)
            temp = self.action_database["wf"]
            self.action_database.clear()
            self.import_modules.clear()
            self.action_database["wf"] = temp
        #self.addItem(self.system_actions_layout, "System actions")
        if module is not None:
            self.on_workspace_change(module, curr_workspace)
