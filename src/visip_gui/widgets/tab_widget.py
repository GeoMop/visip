import os

from PyQt5 import QtWidgets
from PyQt5.QtCore import QMargins
from PyQt5.QtWidgets import QTabWidget

from visip_gui.config.config_data import ConfigData
from visip_gui.widgets.home_tab_widget import HomeTabWidget
from visip_gui.widgets.module_navigation import ModuleNavigation
from visip.dev.module import Module
from visip_gui.widgets.tab import Tab


class TabWidget(QTabWidget):
    def __init__(self, main_widget, edit_menu, parent=None):
        super(TabWidget, self).__init__(parent)
        self.cfg = ConfigData()
        self.setTabsClosable(True)
        self.setTabShape(1)
        self.tabCloseRequested.connect(self.on_close_tab)
        #self.edit_menu = edit_menu
        edit_menu.return_callable_action.triggered.connect(self.return_callable_action)
        edit_menu.delete.triggered.connect(self.delete_items)
        edit_menu.order_diagram.triggered.connect(self.order_diagram)
        self.currentChanged.connect(self.current_changed)
        self.tabBarClicked.connect(self.before_curr_index_change)

        self.main_widget = main_widget

        self.module_views = {}

        self.initial_tab_name = 'Home'
        self.home_tab = HomeTabWidget(self.main_widget)
        self.addTab(self.home_tab, self.initial_tab_name)

    def before_curr_index_change(self, index):
        if not isinstance(self.currentWidget(), HomeTabWidget):
            self.currentWidget().last_category = self.main_widget.toolbox.currentIndex()

    def _add_tab(self, module_filename, module):
        self.setCurrentIndex(self.addTab(ModuleNavigation(module, self), module_filename))

    def change_workspace(self, workspace):
        self.currentWidget().setCurrentWidget(workspace)
        workspace.workflow.update(workspace.workflow._result_call)
        self.main_widget.property_editor.clear()

    def create_new_module(self, filename=None):
        if not isinstance(filename, str):
            #filename = QtWidgets.QFileDialog.getSaveFileName(self.parent(), "New Module",
            #                                                 self.cfg.last_opened_directory, "Python File (*.py)")[0]
            filename = "new_module.py"
        if filename != "":
            self.cfg.last_opened_directory = os.path.dirname(filename)
            with open(filename, "w") as file:
                file.write("import visip as wf")
            module = Module.load_module(filename)
            self._add_tab(os.path.basename(filename), module)

    def open_module(self, filename=None):
        if not isinstance(filename, str):
            filename = QtWidgets.QFileDialog.getOpenFileName(self.parent(), "Select Module",
                                                             self.cfg.last_opened_directory)[0]
        if filename != "":
            self.cfg.last_opened_directory = os.path.dirname(filename)
            module = Module.load_module(filename)
            self._add_tab(os.path.basename(filename), module)

    def current_changed(self, index):
        curr_module_view = self.widget(index)
        if index != -1 and isinstance(curr_module_view, ModuleNavigation):
            self.main_widget.file_menu.export.setDisabled(False)
            self.main_widget.toolbox_dock.setWidget(self.main_widget.toolbox)

            self.main_widget.toolbox.on_module_change(curr_module_view._module,
                                                      curr_module_view.currentWidget())
            self.main_widget.toolbox.setCurrentIndex(curr_module_view.last_category)
            curr_module_view.current_changed()

            return
        self.main_widget.file_menu.export.setDisabled(True)
        #self.disable_everything(True)
        #self.main_widget.toolbox_dock.setWidget(None)

    def on_close_tab(self, index):
        self.module_views.pop(self.tabText(index), None)
        self.removeTab(index)

    def current_workspace(self):
        return self.currentWidget().currentWidget()

    def add_action(self):
        self.current_workspace().scene.add_action(self.current_workspace().scene.new_action_pos)

    def delete_items(self):
        self.current_workspace().scene.delete_items()

    def return_callable_action(self):
        self.current_workspace().scene.change_action_to_callable()

    def add_random_items(self):
        self.current_workspace().scene.add_random_items()

    def order_diagram(self):
        self.current_workspace().scene.order_diagram()


