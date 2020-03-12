
#tests_after_program_start
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
import pytest


from visip_gui.widgets.main_widget import MainWidget

@pytest.fixture
def test_widget(qapp, qtbot):
    widget = MainWidget(qapp)
    qtbot.addWidget(widget)
    return widget

def test_open_module(qtbot, test_widget):

    test_file = "test_module.py"
    test_widget.tab_widget.open_module("test_files\\" + test_file)

    assert test_widget.tab_widget.tabText(test_widget.tab_widget.currentIndex()) == test_file
    navigation = test_widget.tab_widget.currentWidget()
    assert navigation.tabText(navigation.currentIndex()) == "test_class1"

    assert test_widget.toolbox.isEnabled()

    assert test_widget.property_editor.isEnabled()

def test_new_module(qtbot, test_widget, tmp_path):

    test_file = "new_test_module.py"
    test_widget.tab_widget.create_new_module(str(tmp_path / test_file))

    assert test_widget.tab_widget.tabText(test_widget.tab_widget.currentIndex()) == test_file

    navigation = test_widget.tab_widget.currentWidget()
    assert navigation.tabText(navigation.currentIndex()) == "Home"

    assert not test_widget.toolbox.isEnabled()

    assert not test_widget.property_editor.isEnabled()

    export_filename = str(tmp_path / "export.py")
    test_widget.export_to_file(export_filename)

    with open(export_filename, 'r') as file:
        assert file.read() == "import visip as wf"





