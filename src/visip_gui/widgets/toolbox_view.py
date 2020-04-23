from PyQt5.QtCore import QMimeData, QPoint, QByteArray
from PyQt5.QtGui import QDrag
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt


class ToolboxView(QLabel):
    def __init__(self, item, parent, insert_index=None):
        super(ToolboxView, self).__init__(parent)
        if insert_index is None:
            parent.add_widget(self)
        else:
            parent.insert_widget(insert_index, self)
        self.item = item
        self.pixmap = item.paint_pixmap()

        self.selected = False
        self.setPixmap(self.pixmap)

    def get_pos_correction(self):
        return QPoint(self.item.width/2, self.item.height/2)

    def mousePressEvent(self, press_event):
        parent = self.parent()
        for item in parent.items:
            item.deselect()
        self.selected = True
        drag = QDrag(self)
        mime = QMimeData()
        #print(self.item.w_data_item.action.module + "." + self.item.w_data_item.action_name)
        mime.setData("ActionDrag", QByteArray((parent.name + "." + self.item.w_data_item.action_name).encode("utf-8")))
        drag.setMimeData(mime)
        drag.setPixmap(self.pixmap)
        drag.setHotSpot(QPoint( drag.pixmap().width()/2,
                                drag.pixmap().height()/2))
        ret = drag.exec(Qt.MoveAction)

    def deselect(self):
        if self.selected:
            self.selected = False

    def enterEvent(self, *args, **kwargs):
        super(ToolboxView, self).enterEvent(*args, **kwargs)
        self.setCursor(Qt.OpenHandCursor)

    def leaveEvent(self, *args, **kwargs):
        super(ToolboxView, self).leaveEvent(*args, **kwargs)
        self.setCursor(Qt.ArrowCursor)


