import os
import sys
import imp
# TODO: use importlib instead
import traceback
#from typing import Callable
from types import ModuleType
from collections import deque

from ..action import constructor
#from ..code import wrap
from ..code.dummy import DummyAction
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

    def __init__(self, module_path:str) -> None:
        """
        Constructor of the _Module wrapper.
        :param module_obj: a python module object
        """
        self.module_file = module_path
        # File with the module source code.
        self.module = self.load_module(module_path)
        # The python module object.

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
        # self._module_name_dict = {}
        #  Map the full module name to the alias and the module object (e.g. numpy.linalg to la)

        self._object_names = {}
        # Map from the (obj.__module__, obj.__name__) of an object to
        # the correct referencing of the object in this module.
        # This is necessary in particular for actions defined through 'action_def', for the imported modules
        # and also for the actions of the visip library.
        # Note: id(obj) can not be used since a type hint of a decorated class does not undergo the decoration

        # TODO: generalize for other 'rebranding' packages.

        self.ignored_definitions = []
        # Objects of the module, that can not by sourced.
        # If there are any we can not reproduce the source.

        self.extract_definitions()


    @classmethod
    def mod_name(cls, obj):
        return (getattr(obj, "__module__", None), getattr(obj, "__name__", None))

    def object_name(self, obj):
        return self._object_names.get(self.mod_name(obj), None)

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
            if isinstance(obj, DummyAction):
                action = obj._action_value
                self.insert_definition(action)
                assert isinstance(action, base._ActionBase)
                assert name == action.name
                if action.is_analysis:
                    analysis.append(action)

            else:
                if type(obj) is ModuleType:
                    self.imported_modules.append(obj)
                elif name[0] == '_':
                    self.ignored_definitions.append((name, obj))

        self.create_object_names(self.module, "")

        assert len(analysis) <= 1
        if analysis:
            # make instance of the main workflow
            analysis = analysis[0]
            self.analysis = ActionCall.create(analysis)
        else:
            self.analysis = None

    def insert_imported_module(self, mod_obj, alias):
        self.imported_modules.append(mod_obj)
        self.create_object_names(mod_obj, alias)
        self._object_names[(None, mod_obj.__name__)] = alias


    def _set_object_names(self, mod_name, alias):
        # Internal _object_names setter to simplify debugging.

        # print("Map: ", mod_name, alias)
        self._object_names.setdefault(mod_name, alias)


    def create_object_names(self, mod_obj, alias):
        """
        Collect (module, name) -> reference name map self._object_names.

        This is done by BFS through the tree of imported modules and processing
        their dictionaries. These names are used to define 'reference names'
        (module, name) keys are retrieved from the objects __module__ and __name__
        attributes.
        During code representation we can not, however, use the same mechanism as
        1. actions are instances and these do not have __name__attribute. So we add this attribute consistently
        possibly modifying __module__ of the instance as well.
        2. type hints of the classes do not undergo decoration so the object processed in `create_object_names`
        is not the same as the type hint object of the class used in an annotation. However we are able to
        retrieve the same (module, name) key. This is reason why we can not use simply `id(obj)` as the key.
        3. The generic type hints from `typing` module do not have __name__ attribute since Python 3.7 so we use
        the name from the module dictionary.
        4. We only process modules from the `visip` package and the modules importing the `visip` modules.
        """
        # TODO: use BFS to find minimal reference, use aux dist or set to mark visited objects
        module_queue  = deque()     # queue of (module, alias_module_name)
        module_queue.append( (mod_obj, alias) )
        while module_queue:

            mod_obj, mod_alias = module_queue.popleft()
            print("Processing module: ", mod_obj.__name__, mod_alias)

            # process new module
            package = mod_obj.__name__.split('.')[0]
            # process only for visip modules and for
            # modules importing visip
            attr_names = {attr.__name__ for attr in mod_obj.__dict__.values() if hasattr(attr, '__name__')}
            if not (package == 'visip' or 'visip' in attr_names):
                continue

            for name, obj in mod_obj.__dict__.items():
                obj_mod_name = self.mod_name(obj)
                if obj_mod_name in self._object_names:
                    continue
                if name.startswith('__'):
                    continue

                alias_name = f"{mod_alias}.{name}".lstrip('.')
                if isinstance(obj, DummyAction):
                    obj_mod_name = self.mod_name(obj._action_value)
                elif type(obj) is ModuleType:
                    module_queue.append((obj, alias_name))
                elif obj_mod_name[0] == 'typing':
                    # for Python >= 3.7 the typing generic instances have no attribute __name__
                    obj_mod_name = ('typing', name)
                self._set_object_names(obj_mod_name, alias_name)


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

    def rename_definition(self, name:str, new_name: str) -> None:
        """
        Rename workflow or dataclass. Renaming other actions fails.
        """
        action = self.get_action(name)
        if isinstance(action, wf._Workflow):
            action.name = new_name
            self._name_to_def[new_name] = action
            del self._name_to_def[name]
        elif isinstance(action, constructor.ClassActionBase):
            action.name = new_name
            self._name_to_def[new_name] = action
            del self._name_to_def[name]
        else:
            assert False, "Only workflow and classes can be renamed."


    def relative_name(self, obj_module, obj_name):
        """
        Construct the action class name for given set of imported modules.
        :param module_dict: A dict mapping the full module path to its imported alias.
        :return: The action name using the alias instead of the full module path.
        """
        if obj_module == 'builtins':
            return obj_name
        mod_name = (obj_module, obj_name)
        reference_name = self._object_names.get(mod_name, None)
        if reference_name is None:
            print("Undef reference for:", mod_name)
            return None
        return reference_name


    @property
    def name(self):
        return self.module.__name__


    def code(self) -> str:
        """
        Generate the source code of the whole module.
        :return:
        """
        representer = Representer(self.relative_name)
        source = []
        # make imports
        for impr in self.imported_modules:

            alias = self.object_name(impr)
            if alias == impr.__name__:
                import_line = f"import {impr.__name__}"
            else:
                import_line = f"import {impr.__name__} as {alias}"
            source.append(import_line)

        # make definitions
        for v in self.definitions:
            # TODO:
            # Definitions are not arbitrary actions, currently only Workflow and DataClass
            # currently these provides the code_of_definition method.
            # We should move the code definition routines into Representer as the representation
            # should not be specialized for user defined actions since the representation is given by the Python syntax.
            action = v
            source.extend(["", ""])     # two empty lines as separator
            def_code = action.code_of_definition(representer)
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

    # def get_dataclass(self, name:str) -> Callable[..., dtype.DataClassBase]:
    #     """
    #     ??? Not clear why this should exist.
    #     """
    #     assert False
    #     #dclass = self._name_to_def[name]
    #     #return dclass._evaluate

