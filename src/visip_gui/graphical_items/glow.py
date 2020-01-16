import math

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPen, QLinearGradient, QRadialGradient
from PyQt5.QtWidgets import QGraphicsPathItem, QGraphicsBlurEffect


class Glow(QGraphicsPathItem):
    WIDTH = 6

    def __init__(self, parent):
        super(Glow, self).__init__(parent)
        self.setFlag(self.ItemStacksBehindParent, True)
        self.blur = QGraphicsBlurEffect()
        self.blur.setBlurHints(QGraphicsBlurEffect.QualityHint)
        self.blur.setBlurRadius(8)
        self.setPen(QPen(Qt.darkBlue, (self.WIDTH * 2)))
        self.setGraphicsEffect(self.blur)
        self.view = None

    def adapt_glow(self):
        self.blur.setBlurRadius(8 * self.view.zoom)


    def show(self):
        super(Glow, self).show()
        self.view = self.parentItem().scene().views()[0]
        self.view.zoom_changed.connect(self.adapt_glow)
        self.blur.setBlurRadius(8 * self.view.zoom)

    def hide(self):
        super(Glow, self).hide()
        if self.isVisible():
            view = self.parentItem().scene().views()[0]
            view.zoom_changed.disconnect(self.adapt_glow)

    def update_path(self, path):
        self.setPath(path)



