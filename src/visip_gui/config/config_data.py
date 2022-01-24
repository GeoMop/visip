import json
import os
from pathlib import Path

from PyQt5.QtCore import QSettings, QVariant


class ConfigData(QSettings):
    def __init__(self):
        super(ConfigData, self).__init__("GeoPax", "ViSiP")

    @property
    def last_opened_directory(self):
        return self.value("last_opened_directory", "")

    @last_opened_directory.setter
    def last_opened_directory(self, directory: str):
        self.setValue("last_opened_directory", directory)



