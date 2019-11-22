import os
import sys
import imp
import traceback
from typing import Callable
from types import ModuleType

from ..code import wrap
from ..code.representer import Representer
from . import base, action_workflow as wf, dtype as dtype
from .action_instance import ActionCall



class InterpreterError(Exception): pass


class sys_path_append:
    """
    Context manager for adding a path to the sys.path
    """
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        sys.path.insert(0, self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            sys.path.remove(self.path)
        except ValueError:
            pass



def my_exec(cmd, globals=None, locals=None, description='source string'):
    try:
        exec(cmd, globals, locals)
    except SyntaxError as err:
        error_class = err.__class__.__name__
        detail = err.args[0] if err.args else None
        line_number = err.lineno

        raise InterpreterError("%s at line %d of %s: %s" % (error_class, line_number, description, detail))
    except Exception as err:
        error_class = err.__class__.__name__
        detail = err.args[0] if err.args else None
        etype, exc, tb = sys.exc_info()
        line_number = traceback.extract_tb(tb)[-1][1]

        traceback.print_exception(etype, exc, tb)
        raise InterpreterError("%s at line %d of %s: %s" % (error_class, line_number, description, detail))
    #else:
    #    return



class Module:
    """
    Object representing a module (whole file) that can contain
    several worflow and converter definitions and possibly also a script itself.
    Module is used just to capture the code and do not participate on exectution in any way.
    Underlying python module is responsible.

    We  inspect __dict__ of the loaded module to find all definitions.
    The script must be a workflow function decorated with @analysis decorator.

    Only objects decorated by one of decorators from code.decorators are captured,
    remaining code is ignored. Possible non-workflow actions can be used but
    their code can not be reproduced. In order to do not break the code we prevent
    saving of the generated code to the original file.

    Captured object are stored in the list self.definitions which can be
    """


    # @staticmethod
    # def catch_object(name, object):
    #     """
    #     Predicate to identify Analysis definitions in the modlue dict.
    #     TODO: possibly catch without decorators
    #     Currently:
    #     - ignore underscored names
    #     - ignore non-classes
    #     - ignore classes not derived from _ActionBase
    #     - print all non-underscore ignored names
    #     """
    #     pass



    def __init__(self, module_path:str) -> None:
        """
        Constructor of the _Module wrapper.
        :param module_obj: a python module object
        """
        self.module_file = module_path
        # File with the module source code.
        self.module = self.load_module(module_path)
        # Ref to wrapped python module object.

        self.definitions = []
        # Actions defined in the module. Includes:
        # Workflows, python source actions (GUI can not edit modules with these actions),
        # data classes, enums.
        # GUI note: Can be directly reorganized by the GUI. Adding, removing, changing order.
        # TODO: implement a method for sorting the definitions (which criteria)
        self._name_to_def = {}
        # Maps identifiers to the definitions. (e.g. name of a workflow to its object)

        self.imported_modules = []
        # List of imported modules.
        self._full_name_dict = {}
        #  Map the full module name to the alias and the module object (e.g. numpy.linalg to np)
        self.ignored_definitions = []
        # Objects of the module, that can not by sourced.
        # If there are any we can not reproduce the source.

        self.extract_definitions()

    @classmethod
    def load_module(cls, file_path: str) -> ModuleType:
        """
        Import the python module from the file.
        Temporary add its directory to the sys.path in order to find modules in the same directory.
        TODO: Create an empty module if the file doesn't exist.
        :param file_path: Module path to load.
        :return:
        """
        module_dir = os.path.dirname(file_path)
        module_name = os.path.basename(file_path)
        module_name, ext = os.path.splitext(module_name)
        assert ext == ".py"
        with open(file_path, "r") as f:
            source = f.read()
        with sys_path_append(module_dir):
            new_module = imp.new_module(module_name)
            my_exec(source, new_module.__dict__, locals=None, description=module_name)
        return new_module

    def extract_definitions(self):
        """
        Extract definitions from the python module.
        :return:
        """
        analysis = []
        for name, obj in self.module.__dict__.items():
            # print(name, type(obj))
            if isinstance(obj, wrap.ActionWrapper):
                action = obj.action
                self.insert_definition(action)
                assert isinstance(action, base._ActionBase)
                assert name == action.name
                if action.is_analysis:
                    analysis.append(action)

            else:
                if type(obj) is ModuleType:
                    self.insert_imported_module(obj, name)
                elif name[0] == '_':
                    self.ignored_definitions.append((name, obj))

        assert len(analysis) <= 1
        if analysis:
            # make instance of the main workflow
            analysis = analysis[0]
            self.analysis = ActionCall.create(analysis)
        else:
            self.analysis = None

    def insert_imported_module(self, obj, name):
        full_name = obj.__name__
        self.imported_modules.append(obj)
        self._full_name_dict[full_name] = name

    def insert_definition(self, action: base._ActionBase, pos:int=None):
        """
        Insert a new definition of the 'action' to given position 'pos'.
        :param action: An action class (including dataclass construction actions).
        :param pos: Target position, default is __len__ meaning append to the list.
        :return:
        """
        if pos is None:
            pos = len(self.definitions)
        assert isinstance(action, base._ActionBase)
        self.definitions.insert(pos, action)
        self._name_to_def[action.name] = action


    def relative_name(self, module, name):
        """
        Construct the action class name for given set of imported modules.
        :param module_dict: A dict mapping the full module path to its imported alias.
        :return: The action name using the alias instead of the full module path.
        """
        alias = self._full_name_dict.get(module, module)
        if alias in {'builtins', 'typing', self.name}:
            return name
        return "{}.{}".format(alias, name)





    @property
    def name(self):
        return self.module.__name__


    def code(self) -> str:
        """
        Generate the source code of the whole module.
        :return:
        """
        representer = Representer()
        source = []
        # make imports
        for impr in self.imported_modules:
            full_name = impr.__name__
            alias = self._full_name_dict.get(full_name, None)
            if alias:
                import_line = "import {full} as {alias}".format(full=full_name, alias=alias)
            else:
                import_line = "import {full}".format(full=full_name)
            source.append(import_line)

        # make definitions
        for v in self.definitions:
            # TODO:
            # Definitions are not arbitrary actions, currently only Workflow and DataClass
            # currently these provides the cond_of_definition method.
            # We should move the code definition routines into Representer as the representation
            # should not specialized for user defined actions since the representation is given by the Python syntax.
            action = v
            source.extend(["", ""])     # two empty lines as separator
            def_code = action.code_of_definition(representer, self.relative_name)
            source.append(def_code)
        return "\n".join(source)


    def save(self) -> None:
        assert not self.ignored_definitions
        with open(self.module_file, "w") as f:
            f.write(self.code())


    def update_imports(self):
        """
        Pass through all definition and collect all necessary imports.
        :return:
        TODO: ...
        """
        pass


    def get_analysis(self):
        """
        Return the list of analysis workflows of the module.
        :return:
        """
        analysis = [d for d in self.definitions if d.is_analysis]
        return analysis

    def get_action(self, name: str) -> wf._Workflow:
        """
        Get the workflow by the name.
        :param name:
        :return:
        """
        return self._name_to_def[name]

    def get_dataclass(self, name:str) -> Callable[..., dtype.DataClassBase]:
        dclass = self._name_to_def[name]
        return dclass._evaluate

"""
Object progression:
- Actions (implementation)

- Syntactic sugger classes
- ActionInstances - connection into WorkFlow
  This needs to be in close relation to previous since we want GUI - Python bidirectional conversions.
  
- Tasks - execution DAG
- Jobs
"""


"""
TODO:
1. first implement Class action with _name config parameter
2. Config parameters or impl. parameters - used to set some metadata of action.
3. Implement action decorator.
4. Implement evaluation mechanism - conversion to tasks, scheduler, evaluation of tasks by calling action evaluate methods.
5. Implement Evaluation class - keeping data from tasks and evaluation progress - close realtion to MJ, need concept of Resources.
"""
