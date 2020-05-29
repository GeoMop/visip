from PyQt5.QtCore import QMargins, QPoint
from PyQt5.QtWidgets import QTabWidget, QWidget, QFrame, QVBoxLayout

from visip.dev.action_workflow import _Workflow
from visip_gui.dialogs.get_text import GetText
from visip_gui.menu.module_navigation_menu import ModuleNavigationMenu
from visip_gui.widgets.no_workflow_tab import NoWorkflowTab
from visip_gui.widgets.editor import Editor


class ModuleNavigation(QTabWidget):
    def __init__(self, module, tab_widget,  parent=None):
        super(ModuleNavigation, self).__init__(parent)
        self.menu_pos = QPoint(0, 0)
        self.last_category = 0
        self.setLayout(QVBoxLayout(self))
        self._module = module
        self._tab_widget = tab_widget
        self.menu = ModuleNavigationMenu()
        self.menu.new_workflow.triggered.connect(self.add_workflow)
        self.menu.rename_worklfow.triggered.connect(self.rename_workflow)
        self.menu.remove_workflow.triggered.connect(self.remove_workflow)
        self.home_tab_name = "Home"

        self.currentChanged.connect(self.current_changed)

        for wf in self._module.definitions:
            if issubclass(type(wf), _Workflow):
                self.addTab(Editor(wf, self._tab_widget.main_widget,
                                   self._tab_widget.main_widget.toolbox.action_database), wf.name)

        if self.count() == 0:
            self.addTab(NoWorkflowTab(self.add_workflow), self.home_tab_name)

    def contextMenuEvent(self, event):
        super(ModuleNavigation, self).contextMenuEvent(event)
        if not event.isAccepted():
            self.menu_pos = event.pos()
            self.menu.exec_(event.globalPos())

    def add_workflow(self, wf_name=None):
        names = []
        for wf in self._module.definitions:
            names.append(wf.name)
        if type(wf_name) is not str:
            dialog = GetText(self, "New Workflow Name:", names)
            dialog.setWindowTitle("New Workflow")
            if dialog.exec_():
                wf_name = dialog.text
            else:
                return

        if type(self.widget(0)) is NoWorkflowTab:
            self.removeTab(0)

        wf = _Workflow(wf_name)
        self._module.insert_definition(wf)
        ws = Editor(wf, self._tab_widget.main_widget,
                    self._tab_widget.main_widget.toolbox.action_database)
        index = self.addTab(ws, wf.name)

        self.setCurrentIndex(index)

        self._tab_widget.main_widget.toolbox.update_category()

    def rename_workflow(self):
        names = []
        for wf in self._module.definitions:
            names.append(wf.name)
        dialog = GetText(self, "New Workflow Name:", names)
        dialog.setWindowTitle("Rename Workflow")
        if dialog.exec_():
            index = self.tabBar().tabAt(self.menu_pos)
            self._module.rename_definition(self.tabText(index), dialog.text)
            self.setTabText(index, dialog.text)

    def remove_workflow(self):
        index = self.tabBar().tabAt(self.menu_pos)

        for definiton in self._module.definitions:
            if definiton.name == self.tabText(index):
                self._module.definitions.remove(definiton)
                break

        self.removeTab(index)
        if self.count() == 0:
            self.addTab(NoWorkflowTab(self.add_workflow), self.home_tab_name)

    def current_changed(self, index=None):
        if index is None:
            index = self.currentIndex()

        self._tab_widget.main_widget.toolbox.on_workspace_change(self._module, self.currentWidget())
        if isinstance(self.widget(index), Editor):
            self._tab_widget.main_widget.disable_everything(False)
            self.currentWidget().scene.on_selection_changed()
        else:
            self._tab_widget.main_widget.disable_everything(True)


