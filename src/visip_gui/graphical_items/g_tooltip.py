from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPainterPath
from PyQt5.QtWidgets import QGraphicsSimpleTextItem, QGraphicsPathItem, QGraphicsItem


class GTooltip(QGraphicsSimpleTextItem):
    ARROW_HEIGHT = 10
    MARGIN = 3
    def __init__(self, g_item):
        super(GTooltip, self).__init__()
        self.g_item = g_item
        self.background = QGraphicsPathItem(self)
        self.background.setBrush(Qt.red)
        self.background.setFlag(self.ItemStacksBehindParent, True)
        self.setAcceptHoverEvents(True)
        self.setZValue(10.0)
        self.setFlag(self.ItemIgnoresTransformations, True)
        self.hide()
        self.setCursor(Qt.ArrowCursor)

    def setText(self, text):
        if text != self.text():
            super(GTooltip, self).setText(text)
            self.update_gfx()

    def update_gfx(self):
        path = QPainterPath()
        rect = super(GTooltip, self).boundingRect()
        rect.adjust(-2, -2, 2, 2)
        path.addRoundedRect(rect, 3, 3)
        self.background.setPath(path)
        return path


    def shape(self):
        shape = QPainterPath()
        shape.addRect(self.boundingRect())
        return shape

    def boundingRect(self):
        return super(GTooltip, self).boundingRect().united(self.g_item.mapRectToItem(self, self.g_item.boundingRect()))

    def show_tooltip(self):
        if not self.isVisible():
            rect = self.g_item.mapRectToScene(self.g_item.boundingRect())
            this_rect = super(GTooltip, self).boundingRect()
            pos = QPoint(rect.center().x() - this_rect.width() / 2, rect.bottom() + self.ARROW_HEIGHT)

            view = self.g_item.scene().views()[0]
            scene_rect = view.mapToScene(view.viewport().geometry()).boundingRect()
            this_rect.moveTo(pos)
            pos.setX(max(scene_rect.left() + self.MARGIN,
                         min(pos.x(), scene_rect.right() - this_rect.width() - self.MARGIN)))
            if scene_rect.height() < this_rect.bottom() + self.ARROW_HEIGHT:
                pos = QPoint(pos.x(),
                             rect.top() - this_rect.height() - self.ARROW_HEIGHT)
                self.setPos(pos)
                path = self.update_gfx()
                rect = path.boundingRect()
                item_rect = self.g_item.mapRectToItem(self, self.g_item.boundingRect())
                path.moveTo(item_rect.center().x() - self.ARROW_HEIGHT, rect.bottom())
                path.lineTo(item_rect.center().x(), item_rect.top())
                path.lineTo(item_rect.center().x() + self.ARROW_HEIGHT, rect.bottom())
                self.background.setPath(path)
            else:
                self.setPos(pos)
                path = self.update_gfx()
                rect = path.boundingRect()
                item_rect = self.g_item.mapRectToItem(self, self.g_item.boundingRect())
                path.moveTo(item_rect.center().x() - self.ARROW_HEIGHT, rect.top())
                path.lineTo(item_rect.center().x(), item_rect.bottom())
                path.lineTo(item_rect.center().x() + self.ARROW_HEIGHT, rect.top())
                self.background.setPath(path)

            self.g_item.scene().addItem(self)
            self.show()

    def setPos(self, *__args):
        super(GTooltip, self).setPos(*__args)

    def setVisible(self, b):
        pass

    def mousePressEvent(self, *args, **kwargs):
        pass

    def hoverLeaveEvent(self, *args, **kwargs):
        self.g_item.scene().removeItem(self)
        self.hide()
