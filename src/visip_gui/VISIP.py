"""
Start script that initializes main window and runs APP.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""


import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from PyQt5.QtWidgets import QApplication
from visip_gui.widgets.main_widget import MainWidget


def main():
    app = QApplication(sys.argv)
    w = MainWidget(app)
    w.resize(1000, 720)
    w.move(300, 50)
    w.setWindowTitle('Analysis')
    w.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
