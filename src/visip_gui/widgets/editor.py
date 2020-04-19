"""
Workspace where all user input is processed.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""
import cProfile
import time
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QFileDialog, QApplication

from visip_gui.widgets.base.g_base_model_view import GBaseModelView
from .scene import Scene


class Editor(GBaseModelView):
    """Graphics scene which handles user input and shows user the results."""
    def __init__(self, workflow, main_widget, available_actions, parent=None):
        """Initializes class."""
        super(Editor, self).__init__(parent)
        self.workflow = workflow
        self.scene = Scene(main_widget, workflow, available_actions, self)
        self.setScene(self.scene)
        self.available_actions = available_actions

        # for deciding if context menu should appear
        self.viewport_moved = False

        self.edit_menu = main_widget.edit_menu

        self.setAcceptDrops(True)

        # timer for updating scene
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.scene.update_scene)
        timer.start(16.6)
        self.fps_count = 0
        self.frame_time = 0

        self.prof = cProfile.Profile()
        self.prof.enable()

        self.last_mouse_event_pos = QPoint(0, 0)
        self.mouse_press_event_pos = QPoint(0, 0)


    def __repr__(self):
        return "Workspace: " + self.scene.workflow.name

    def mousePressEvent(self, press_event):
        """Store information about position where this event occurred."""
        super(Editor, self).mousePressEvent(press_event)
        self.last_mouse_event_pos = press_event.pos()
        self.mouse_press_event_pos = press_event.pos()

    def dragEnterEvent(self, drag_enter):
        """Accept drag event if it carries action."""
        if drag_enter.mimeData().hasFormat("ActionDrag"):
            identifier = drag_enter.mimeData().data("ActionDrag").data().decode("utf-8")
            index = identifier.rfind(".")
            module = identifier[:index]
            action_name = identifier[index + 1:]
            try:
                self.available_actions[module][action_name]
            except KeyError as e:
                print("Unknown action " + identifier)
            else:
                drag_enter.acceptProposedAction()

    def dropEvent(self, drop_event):
        """Create new action from dropped information"""
        self.scene.add_action(self.mapToScene(drop_event.pos()) - drop_event.source().get_pos_correction(),
                              drop_event.mimeData().data("ActionDrag").data().decode("utf-8"))
        drop_event.acceptProposedAction()

    def dragMoveEvent(self, move_event):
        move_event.acceptProposedAction()

    def mouseMoveEvent(self, move_event):
        """ If new connection is being crated, move the loose end to mouse position.
            If user drags with right button pressed, move visible rectangle. """
        super(Editor, self).mouseMoveEvent(move_event)
        if self.scene.new_connection is not None:
            self.scene.new_connection.set_port2_pos(self.mapToScene(move_event.pos()))
            self.scene.update()

        dist = (self.mouse_press_event_pos - move_event.pos()).manhattanLength()
        if move_event.buttons() & QtCore.Qt.RightButton and dist >= QApplication.startDragDistance():
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            self.viewport_moved = True
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() -
                                                (move_event.x() - self.last_mouse_event_pos.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() -
                                                (move_event.y() - self.last_mouse_event_pos.y()))
            self.scene.update()
        self.last_mouse_event_pos = move_event.pos()

    def mouseReleaseEvent(self, release_event):
        super(Editor, self).mouseReleaseEvent(release_event)
        '''
        self.last_mouse_event_pos = release_event.pos()
        mouse_grabber = self.scene.mouseGrabberItem()
        if mouse_grabber is not None and issubclass(type(mouse_grabber), Action):
            for item in self.items(release_event.pos()):
                if issubclass(type(item), ActionForSubactions) and item is not mouse_grabber:
                    mouse_grabber.setParentItem(item)
        '''

    def contextMenuEvent(self, event):
        """Open context menu on right mouse button click if no dragging occurred."""
        super(Editor, self).contextMenuEvent(event)
        if not event.isAccepted():
            if not self.viewport_moved:
                self.scene.new_action_pos = self.mapToScene(event.pos())
                self.edit_menu.exec_(event.globalPos())
                event.accept()
            else:
                self.setCursor(QtCore.Qt.ArrowCursor)
                self.viewport_moved = False

    def show_fps(self):
        """Debug tool"""
        print("Fps: " + str(self.fps_count))
        print("Avarage frame time: " + str(self.frame_time / (self.fps_count if self.fps_count else 1)))
        self.frame_time = 0
        self.fps_count = 0

        self.prof.disable()
        self.prof.print_stats()
        self.prof.clear()

        self.prof = cProfile.Profile()
        self.prof.enable()

    def paintEvent(self, event):
        if self.center_on_content:
            self.center_on_content = False
            self.centerOn(self.scene.itemsBoundingRect().center())
        start = time.time()

        super(Editor, self).paintEvent(event)
        self.frame_time += time.time() - start
        self.fps_count += 1

    def save(self):
        save_location = QFileDialog.getSaveFileName(self.parent(), "Select Save Location")
        #print(save_location)
        with open(save_location[0],'w') as save_file:
            self.scene.save_item(save_file, self.scene.action_model.get_item())

    def load(self):
        pass
