
class ExcVFileNotFound(Exception):
    pass


class ExcVWrongFileMode(Exception):
    pass

class ExcVCommandFailed(Exception):
    def __init__(self, command, res):
        self.command = command
        self.res = res

    def __str__(self):
        return "Command: {}\n Failed with output: {}".format(self.command, str(self.res))


class ExcInvalidCall(Exception):
    pass