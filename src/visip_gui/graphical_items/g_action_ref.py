from PyQt5.QtCore import Qt, QLineF
from PyQt5.QtGui import QPen, QBrush, QPixmap, QBitmap, QPainter

from visip_gui.graphical_items.g_action import GAction

lines = [QLineF(0, 16, 16, 0),
         QLineF(16, 32, 32, 16),
         QLineF(0, 32, 32, 0),
         QLineF(1, -1, -1, 1),
         QLineF(33, 31, 31, 33)]

def make_ref_texture(background_color):
    ref_texture = QPixmap(32, 32)
    ref_texture.fill(background_color)
    painter = QPainter(ref_texture)
    pen = QPen(Qt.darkGray)
    pen.setWidth(3)
    painter.setPen(pen)
    painter.drawLines(lines)
    return ref_texture

class GActionRef(GAction):
    REF_TEXTURE = None
    def __init__(self, g_data_item, w_data_item, parent=None, eval_gui=None, appending_ports=True):
        if self.REF_TEXTURE is None:
            self.REF_TEXTURE = make_ref_texture(Qt.gray)
        super(GActionRef, self).__init__(g_data_item, w_data_item, parent, eval_gui, appending_ports)
        pen = QPen(Qt.black)
        self.setPen(pen)
        brush = QBrush()
        brush.setTexture(self.REF_TEXTURE)
        self.setBrush(brush)

        self.type_name.setText("Ref: " + w_data_item.action.value.name)
        self.width = self.width

    @property
    def status(self):
        return self.background.status

    @status.setter
    def status(self, status):
        if status != self.background.status:
            self.background.status = status
            self.REF_TEXTURE = make_ref_texture(self.background.COLOR_PALETTE[self.status])
            brush = QBrush()
            brush.setTexture(self.REF_TEXTURE)
            self.setBrush(brush)
            self.update()
