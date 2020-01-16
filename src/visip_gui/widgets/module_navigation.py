from PyQt5.QtCore import QMargins, QPoint
from PyQt5.QtWidgets import QTabWidget, QWidget, QFrame, QVBoxLayout

from visip.dev.action_workflow import _Workflow
from visip_gui.dialogs.get_text import GetText
from visip_gui.menu.module_navigation_menu import ModuleNavigationMenu
from visip_gui.widgets.workspace import Workspace


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
        self.menu.remove_workflow.triggered.connect(self.remove_workflow)

        self.currentChanged.connect(self.current_changed)

        for wf in self._module.definitions:
            if issubclass(type(wf), _Workflow):
                self.addTab(Workspace(wf, self._tab_widget.main_widget,
                                      self._tab_widget.main_widget.toolbox.action_database), wf.name)

    def contextMenuEvent(self, event):
        super(ModuleNavigation, self).contextMenuEvent(event)
        if not event.isAccepted():
            self.menu_pos = event.pos()
            self.menu.exec_(event.globalPos())

    def add_workflow(self):
        names = []
        for wf in self._module.definitions:
            names.append(wf.name)
        dialog = GetText(self, "New Workflow Name:", names)
        dialog.setWindowTitle("New Workflow")
        if dialog.exec_():
            wf_name = dialog.text

            wf = _Workflow(wf_name)
            self._module.insert_definition(wf)
            ws = Workspace(wf, self._tab_widget.main_widget,
                           self._tab_widget.main_widget.toolbox.action_database)
            index = self.addTab(ws, wf.name)

            self.setCurrentIndex(index)

            self._tab_widget.main_widget.toolbox.update_category()

    def remove_workflow(self):
        index = self.tabBar().tabAt(self.menu_pos)

        for definiton in self._module.definitions:
            if definiton.name == self.tabText(index):
                self._module.definitions.remove(definiton)
                break

        self.removeTab(index)

    def current_changed(self, index):
        self._tab_widget.main_widget.toolbox.on_workspace_change(self._module, self.currentWidget())


