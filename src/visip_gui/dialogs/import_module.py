import os

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QStyle, QDialogButtonBox, \
    QSizePolicy, QLayout, QFileDialog, QMessageBox

from visip_gui.config.config_data import ConfigData


class ImportModule(QDialog):
    def __init__(self, parent=None):
        super(ImportModule, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        self.first_line = QHBoxLayout()
        self.layout.addLayout(self.first_line)
        self.first_line.addWidget(QLabel("Import module:"))
        self.import_module_filename = QLineEdit()
        self.first_line.addWidget(self.import_module_filename)
        self.open_dialog_button = QPushButton(self.style().standardIcon(QStyle.SP_DialogOpenButton), "")
        self.first_line.addWidget(self.open_dialog_button)

        self.second_line = QHBoxLayout()
        self.layout.addLayout(self.second_line)
        self.second_line.addWidget(QLabel("Module alias:"))
        self.module_name = QLineEdit()
        self.module_name.setPlaceholderText("Optional")
        self.second_line.addWidget(self.module_name)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
        self.buttons.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.layout.addWidget(self.buttons)
        self.setFixedHeight(self.layout.sizeHint().height())

        self.cfg = ConfigData()
        self.setWindowTitle("Import module")

        self.open_dialog_button.clicked.connect(self.open_dialog)


    def open_dialog(self):
        filename = QFileDialog.getOpenFileName(self, "Select Module", self.cfg.last_opened_directory)[0]
        if filename != "":
            self.import_module_filename.setText(filename)
            name, ext = os.path.splitext(os.path.basename(filename))
            self.module_name.setText(name)

    def filename(self):
        return self.import_module_filename.text()

    def name(self):
        return self.module_name.text()

    def done(self, code):
        #print(self.Accepted)
        #print(code)
        if code != self.Accepted or os.path.exists(self.import_module_filename.text()):
            super(ImportModule, self).done(code)
        else:
            msg = QMessageBox(self)
            msg.setText("Chosen file doesn't exist!")
            msg.exec()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = ImportModule()
    print(w.exec())

    sys.exit(app.exec_())