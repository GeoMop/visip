from PyQt5.QtCore import QTimer, QPoint, QObject
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsProxyWidget, QWidget

from visip_gui.graphical_items.graphics_proxy_widget import GraphicsProxyWidget
from visip_gui.widgets.composite_type_view import CompositeTypeView


class GTooltipBase(QGraphicsItem):
    def __init__(self, parent=None):
        super(GTooltipBase, self).__init__(parent)
        self.setAcceptHoverEvents(True)
        self.__timer = QTimer()
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self.show_tooltip)
        self.__timer.setInterval(500)
        self.__position = QPoint()
        self.__widget_proxy = GraphicsProxyWidget(self)
        self.__widget_proxy.setVisible(False)
        self.__widget_proxy.hide()
        self.__widget = None

        self.__auto_show = False

    @property
    def widget(self):
        return self.__widget

    @widget.setter
    def widget(self, widget):
        self.__widget = widget
        self.__widget_proxy.setWidget(widget)
        if widget is not None:
            self.__widget.hide()

    def auto_show_tooltip(self, b):
        if b:
            self.__auto_show = False
        else:
            self.__auto_show = True

    def tooltip_disabled(self):
        return self.__disabled

    def show_tooltip(self):
        if self.__widget is not None:
            self.__timer.stop()
            self.__widget_proxy.show()
            view = self.scene().views()[0]
            self.__position = view.mapFromGlobal(QCursor.pos())
            self.__position = view.mapToScene(self.__position)
            self.__widget_proxy.setPos(self.__position)

            scene_rect = view.mapToScene(view.viewport().geometry()).boundingRect()
            widget_rect = self.mapRectToScene(self.__widget_proxy.boundingRect())

            if widget_rect.bottom() > scene_rect.bottom():
                self.__widget_proxy.setPos(self.__position + QPoint(0, -widget_rect.height()))
            if widget_rect.right() > scene_rect.right():
                self.__widget_proxy.setPos(self.__widget_proxy.pos() + QPoint(-widget_rect.width(), 0))


            if self.__widget_proxy.scene() is None:
                self.scene().addItem(self.__widget_proxy)


    def hoverEnterEvent(self, event):
        super(GTooltipBase, self).hoverEnterEvent(event)
        if not self.__widget_proxy.isVisible() and not self.__auto_show:
            self.__timer.start()

    def hoverLeaveEvent(self, event):
        super(GTooltipBase, self).hoverLeaveEvent(event)
        self.__timer.stop()
        if not self.__widget_proxy.boundingRect().contains(self.mapToItem(self.__widget_proxy, event.pos())):
            self.__widget_proxy.hide()


    def wheelEvent(self, event):
        super(GTooltipBase, self).wheelEvent(event)
        i=1

