from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QDialogButtonBox, QHBoxLayout, QGridLayout, QSizePolicy, \
    QLayout, QMessageBox


class GetText(QDialog):
    def __init__(self, parent, label):
        super(GetText, self).__init__(parent)
        self.label = QLabel()
        self.label.setText(label)
        self._text_edit = QLineEdit()
        self._text_edit.textChanged.connect(self.text_changed)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
        self.buttons.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)

        self.text_changed(self.text)

        self.lay = QGridLayout(self)
        self.lay.setSizeConstraint(QLayout.SetFixedSize)
        self.lay.addWidget(self.label, 0, 0)
        self.lay.addWidget(self._text_edit, 0, 1)
        self.lay.addWidget(self.buttons, 1, 1)

    @property
    def text(self):
        return self._text_edit.text()

    def text_changed(self, text):
        if text:
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttons.button(QDialogButtonBox.Ok).setEnabled(False)