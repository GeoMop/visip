
#tests_after_program_start
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
import pytest

from visip_gui.widgets.main_window import MainWindow

@pytest.fixture
def test_widget(qapp):
    MainWindow(qapp)
    return

def test_after_program_start(qtbot, test_widget):
    qtbot.addWidget(test_widget)

    test_widget.file_menu.open.trigger()
