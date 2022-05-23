
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

class ExcArgumentBindError(Exception):
    pass


class ExcActionExpected(Exception):
    pass

class ExcConstantKey(Exception):
    pass

class ExcInvalidCall(Exception):
    pass

class ExcNoType(Exception):
    # Missing type annotation of :function args or return types, class attributes.
    pass

class ExcTypeBase(Exception):
    # catch typechecking errors, provide suitable details
    # TODO: remove, not in use any more, type checking errors goes to the error list
    pass

class ExcInvalidWorkflow(Exception):
    pass

class ExcGenericArgs(Exception):
    pass

class ExcNotDType(Exception):
    pass

class ExcVariableOverwrite(Exception):
    pass