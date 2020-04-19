
#tests_after_program_start
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
import pytest


from visip_gui.widgets.main_window import MainWindow


@pytest.fixture
def main_window(qapp, qtbot):
    widget = MainWindow(qapp)
    qtbot.addWidget(widget)
    return widget

def test_open_module(qtbot, main_window):

    test_file = "test_module.py"
    main_window.tab_widget.open_module("test_files\\" + test_file)

    assert main_window.tab_widget.tabText(main_window.tab_widget.currentIndex()) == test_file
    navigation = main_window.tab_widget.currentWidget()
    assert navigation.tabText(navigation.currentIndex()) == "test_class1"

    assert main_window.toolbox.isEnabled()

    assert main_window.property_editor.isEnabled()

def test_new_module(qtbot, main_window, tmp_path):

    test_file = "new_test_module.py"
    main_window.tab_widget.create_new_module(str(tmp_path / test_file))

    assert main_window.tab_widget.tabText(main_window.tab_widget.currentIndex()) == test_file

    navigation = main_window.tab_widget.currentWidget()
    assert navigation.tabText(navigation.currentIndex()) == "Home"

    assert not main_window.toolbox.isEnabled()

    assert not main_window.property_editor.isEnabled()

    export_filename = str(tmp_path / "export.py")
    main_window.export_to_file(export_filename)

    with open(export_filename, 'r') as file:
        assert file.read() == "import visip as wf"

def test_all(main_window, tmp_path):
    test_file = "new_test_module.py"
    main_window.tab_widget.create_new_module(str(tmp_path / test_file))

    navigation = main_window.tab_widget.currentWidget()
    toolbox = main_window.toolbox


    navigation.add_workflow("test")
    assert toolbox.import_modules.get(test_file[:-3])
    workspace = navigation.currentWidget()

    navigation.add_workflow("test2")





    #export_filename = str(tmp_path / "export.py")
    #main_window.export_to_file(export_filename)

        





