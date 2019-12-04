from PyQt5.QtWidgets import QGraphicsProxyWidget


class GraphicsProxyWidget(QGraphicsProxyWidget):
    def __init__(self, source):
        super(GraphicsProxyWidget, self).__init__()
        self.source = source
        self.setAcceptHoverEvents(True)

    def hoverLeaveEvent(self, event):
        super(GraphicsProxyWidget, self).hoverLeaveEvent(event)
        if not self.source.boundingRect().contains(self.mapToItem(self.source, event.pos())):
            self.hide()

    def wheelEvent(self, event):
        super(GraphicsProxyWidget, self).wheelEvent(event)
        event.setAccepted(True)

