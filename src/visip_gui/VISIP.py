#!/usr/bin python3
# -*- coding: utf-8 -*-
"""
Start script that initializes main window and runs APP.
@author: Tomáš Blažek
@contact: tomas.blazek@tul.cz
"""


import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import PyQt5
from PyQt5.QtWidgets import QApplication
import argparse
from visip_gui.widgets.main_window import MainWindow


def read_arguments():
    parser = argparse.ArgumentParser(description="VISIP GUI")
    parser.add_argument("file", type=str, help="VISIP module to open.")
    return parser.parse_args()

def main():
    args = read_arguments()
    app = QApplication(sys.argv)
    w = MainWindow(app)
    w.setWindowTitle('ViSiP')
    if args.file:
        w.open_module(args.file)
    w.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
