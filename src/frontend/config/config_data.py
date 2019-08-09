import json
import os


class ConfigData(object):

    __instance = None

    if 'APPDATA' in os.environ:
        __config_dir__ = os.path.join(os.environ['APPDATA'], 'VISIP')
    else:
        __config_dir__ = os.path.join(os.environ['HOME'], '.visip')

    FILENAME = "config.json"
    FILE_PATH = os.path.join(__config_dir__, FILENAME)

    def __new__(cls):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
            cls.__instance.__init()
        return cls.__instance

    def __init(self):
        if os.path.exists(self.FILE_PATH):
            self.load()
        else:
            os.mkdir(self.__config_dir__)
            self.cwd = os.getcwd()
            self.last_opened_directory = self.cwd

    def save(self):
        with open(self.FILE_PATH, "w") as cfg_file:
            json.dump(self.__dict__, cfg_file)

    def load(self):
        with open(self.FILE_PATH, "r") as cfg_file:
            obj = json.load(cfg_file)
            self.__dict__ = obj


