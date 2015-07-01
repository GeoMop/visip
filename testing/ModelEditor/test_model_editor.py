import model_editor
from PyQt5.QtTest import QTest
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

app_result={}

def test_err_dialog(request): 
    global dialog_result
 
    editor = model_editor.ModelEditor()
    timer=QTimer(editor._mainwindow)
    timer.timeout.connect(lambda: start_dialog(editor))
    timer.start(0)
    editor.main() 
    
    assert app_result['title']=="GeoMop Model Editor - New File"
    assert app_result['closed_window']==True
 
def start_dialog(editor):
    global dialog_result
    app_result['title']=editor._mainwindow.windowTitle()
    QTest.keyPress(editor._mainwindow, Qt.Key_Q,  Qt.ControlModifier)
    app_result['closed_window']=editor._mainwindow.close();
    editor._app.quit()
