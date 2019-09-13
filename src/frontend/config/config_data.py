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
            if not os.path.exists(self.__config_dir__):
                os.mkdir(self.__config_dir__)
            self.cwd = os.getcwd()
            self._last_opened_directory = self.cwd
            self._module_root_directory = self.cwd

    @property
    def module_root_directory(self):
        return self._module_root_directory

    @property
    def last_opened_directory(self):
        return self._last_opened_directory

    @last_opened_directory.setter
    def last_opened_directory(self, directory: str):
        self._last_opened_directory = directory


    def save(self):
        with open(self.FILE_PATH, "w") as cfg_file:
            json.dump(self.__dict__, cfg_file)

    def load(self):
        with open(self.FILE_PATH, "r") as cfg_file:
            obj = json.load(cfg_file)
            self.__dict__ = obj


