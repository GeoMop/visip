from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsPathItem


class GTooltip(QGraphicsSimpleTextItem):
    def __init__(self, g_item):
        super(GTooltip, self).__init__()
        self.g_item = g_item
        self.background = QGraphicsPathItem(self)
        self.background.setBrush(Qt.red)
        self.background.setFlag(self.ItemStacksBehindParent, True)
        self.hide()
        self.setAcceptHoverEvents(True)
        self.setZValue(1.0)


    def setText(self, text):
        super(GTooltip, self).setText(text)
        path = QPainterPath()
        path.addRoundedRect(self.boundingRect(), 10, 10)
        self.background.setPath(path)

    def shape(self):
        shape = self.background.shape()
        shape.addPath(self.g_item.shape())

        return shape

    def show_tooltip(self):
        rect = self.mapRectFromItem(self.g_item, self.g_item.boundingRect())
        this_rect = self.boundingRect()

        pos = QPoint(rect.center().x() - this_rect.center().x(), rect.bottom())
        print(pos)
        self.setPos(pos)
        self.g_item.scene().addItem(self)
        self.show()


    def setVisible(self, b):
        pass

    def hoverLeaveEvent(self, *args, **kwargs):
        print("leave")
