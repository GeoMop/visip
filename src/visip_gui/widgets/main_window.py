"""
Main window.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""

import os

from PyQt5.QtCore import Qt, QByteArray
from PyQt5.QtWidgets import QMessageBox

from visip_gui.config.config_data import ConfigData
from visip_gui.menu.eval_menu import EvalMenu
from visip_gui.menu.file_menu import FileMenu
from visip_gui.widgets.gui_evaluation import GUIEvaluation
from visip_gui.widgets.eval_window import EvalWindow
from visip_gui.widgets.inputs_editor import InputsEditor
from visip_gui.widgets.tool_box import ToolBox

from .tab_widget import TabWidget

from PyQt5 import QtWidgets
from visip_gui.menu.edit_menu import EditMenu


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app, parent=None):
        super(MainWindow, self).__init__(parent)
        self.cfg = ConfigData()
        self._init_menu()
        self._init_docks()

        if not self.cfg.contains("mainWindow/geometry"):
            self.resize(1000, 720)
            self.move(300, 50)
        else:
            self.restoreGeometry(self.cfg.value("mainWindow/geometry", QByteArray()))


        self.property_editor = InputsEditor()
        self.properities_dock.setWidget(self.property_editor)

        self.tab_widget = TabWidget(self, self.edit_menu)
        self.setCentralWidget(self.tab_widget)

        self.file_menu.new.triggered.connect(self.tab_widget.create_new_module)
        self.file_menu.open.triggered.connect(self.tab_widget.open_module)
        self.file_menu.export.triggered.connect(self.export_to_file)

        self.toolbox = ToolBox(self)
        self.toolbox_dock.setWidget(self.toolbox)

        self.evaluation_window = EvalWindow()


        self.restoreState(self.cfg.value("mainWindow/windowState", QByteArray()))

        app.aboutToQuit.connect(self.before_exit)

    def before_exit(self):
        self.cfg.setValue("mainWindow/geometry", self.saveGeometry())
        self.cfg.setValue("mainWindow/windowState", self.saveState())

    def _init_menu(self):
        """Initializes menus"""
        self.menu_bar = self.menuBar()
        self.file_menu = FileMenu()
        self.menu_bar.addMenu(self.file_menu)
        self.edit_menu = EditMenu()
        self.menu_bar.addMenu(self.edit_menu)
        self.eval_menu = EvalMenu()
        self.menu_bar.addMenu(self.eval_menu)
        self.eval_menu.evaluate.triggered.connect(self.evaluate)

    def _init_docks(self):
        """Initializes docks"""
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        self.toolbox_dock = QtWidgets.QDockWidget("Toolbox")
        self.toolbox_dock.setObjectName("toolbox_dock")
        self.toolbox_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.toolbox_dock)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)

        self.properities_dock = QtWidgets.QDockWidget("Inputs Editor", self)
        self.properities_dock.setObjectName("properities_dock")
        self.properities_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properities_dock)

    def open_module(self, filename):
        self.tab_widget.open_module(filename)

    def export_to_file(self, filename=None):
        if not isinstance(filename, str):
            filename = QtWidgets.QFileDialog.getSaveFileName(self, "Export Module", self.cfg.last_opened_directory, "Python source (*.py);;All (*)")[0]
        if filename != "":
            self.cfg.last_opened_directory = os.path.dirname(filename)
            code = self.tab_widget.currentWidget()._module.code()
            with open(filename, 'w') as f:
                f.write(code)

    def evaluate(self):
        workflow = self.tab_widget.current_workspace().workflow
        if workflow.is_analysis:
            self.evaluation_window.add_eval(GUIEvaluation(workflow, self.evaluation_window))
        else:
            msg = QMessageBox(self)
            msg.setText( "This isn't analysis. Todo: make a dialog to fill empty slots!")
            msg.exec()

    def disable_everything(self, b):
        self.toolbox_dock.setDisabled(b)
        self.property_editor.setDisabled(b)
        self.edit_menu.setDisabled(b)
        self.eval_menu.setDisabled(b)
