import importlib.util
from typing import *
import os
import sys
# TODO: use importlib instead
import traceback
# from typing import Callable
from types import ModuleType
from collections import deque
from attrs import define

from ..action import constructor
# from ..code import wrap
from ..code.dummy import DummyAction, DummyWorkflow
from ..code.representer import Representer
from . import base, action_workflow as wf
from .action_instance import ActionCall
from . import dtype


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


def visip_exec(cmd, globals=None, locals=None, description='source string'):
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


class _DefBase:
    def get_type(self):
        return None

    def get_action(self, name) -> base.ActionBase:
        return None

@define
class _DefImport(_DefBase):
    alias: str
    module: 'Module'

    def code(self, representer):
        pass

@define
class _DefFrom(_DefBase):
    alias: str
    obj: object

@define
class _DefAction(_DefBase):
    # Both @action_def and @workflow
    alias: str
    action: base.ActionBase

    def get_type(self):
        if isinstance(self.action.output_type, (dtype.Class, dtype.Enum)):
            return self.action.output_type
        else:
            return None

    def get_action(self, name) -> base.ActionBase:
        if self.alias == name:
            return self.action

@define
class _DefUnknown(_DefBase):
    alias: str
    obj: object

class StringModuleLoader(importlib.abc.Loader):
    pass



class Module:
    """
    Object representing a module (whole file) that can contain
    several workflow (including main analysis), Python action definitions, Class and Enum definitions.
    Module is used just to capture the code and do not participate on exectution, which is performed
    by the Evaluation class.

    We  inspect __dict__ of the loaded module to find all definitions. We reconginze only  decorated objects:
    @workflow, @action_def, @Class, @Enum.
    TODO: support loading of nondecorated module together with typedefs in an external file (can use standard used for typedefs).

    The @action_def actions, can not reproduce the code so these should rather be in a separate source file.
    In order to do not break the code we prevent saving of the generated code to the original file.

    New concept:
    The Module class have two purposes:
    1. Collect defined names and corresponding objects in order to recreate the text representation of the code.
       In particular we need map (obj.__module__, obj.__name__) -> alias. Where alias is possibly different name for the object
       used in the module.
       - We need list of imported modules.
       - We collect names with other module as coming from the `from MOD import XYZ` construct.

    2. From all definitions extract the VISIP decorated definitions: atomic action, workflow, class, enum
       - We need access to these definitions by their name.
       - We need a global list of imported modules with appropriate Module instance. Can be empty for modules that does not contain any VISIP
         definitions.
       - Need global map of VISIP types: classes, enums in form of the (module, name) -> data_type constructor.


    Changes:
    - TODO: dict of (various) definitions for single module
      finalize and test for all Defs

    - remove trivial items from _object_names
    - nontrivial should use only: module aliases (imports), name aliasse (from)
      other recursion should not be necessary if we use the names of other Modules.
    - TODO: test from .. import .. as .. ; not clear where to create the visip objects; in the new or in the source module
      should be source, but it is in fact not imported in current implementation, we should import it as well
    """

    ModNamePair = Tuple[str, str]           # (module_name, object_name)
    _modules: Dict[str, 'Module'] = {}
    _types_map: Dict[ModNamePair, Union[dtype.Enum, dtype.Class]] = None

    @classmethod
    def get_module(cls, module_name: str) -> Optional['Module']:
        return cls._modules[module_name]

    @classmethod
    def types_map(cls, force=False):
        if cls._types_map is None or force:
            _types_map = {}
            for m in cls._modules.values():
                for mod_name, def_ in m.new_definitions.items():
                    type_obj = def_.get_type()
                    if type_obj is not None:
                        key = (type_obj.__module__, type_obj.__name__)
                        if key in _types_map:
                            assert _types_map[key] is type_obj
                        else:
                            _types_map[key] = type_obj
        return _types_map

    @classmethod
    def mod_name(cls, obj):
        return (getattr(obj, "__module__", None), getattr(obj, "__name__", None))

    @staticmethod
    def is_dunder(name):
        return len(name) > 4 and name.isascii() and name.startswith('__') and name.endswith('__')

    @classmethod
    def add_module(cls, py_module, reload=False):
        try:
            if not reload:
                return cls._modules[py_module.__name__]
        except KeyError:
            pass
        try:
            mod_path = py_module.__file__
        except AttributeError:
            mod_path = None
        if mod_path is None:
            mod_path = ""
        else:
            mod_path = os.path.abspath(mod_path)

        visip_mod = cls(py_module, mod_path)
        cls._modules.setdefault(py_module.__name__, visip_mod)
        visip_mod.extract_definitions()
        #if visip_mod.is_visip_module():
        #    print(visip_mod.info())
        return visip_mod

    @classmethod
    def make_module(cls, module_name: str, source_string: str) -> 'Module':
        loader = StringModuleLoader()
        spec = importlib.machinery.ModuleSpec(module_name, loader)
        new_module = importlib.util.module_from_spec(spec)
        visip_exec(source_string, new_module.__dict__, locals=None, description=module_name)
        new_module.__file__ = "__from_string__"
        return cls.add_module(new_module, reload=True)

    @classmethod
    def load_module(cls, file_path: str) -> 'Module':
        """
        Load VISIP main module, recursively search all loaded modules detect
        VISIP modules and moke Module instances for them.
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
            spec = importlib.util.find_spec(module_name)
            new_module = importlib.util.module_from_spec(spec)
            visip_exec(source, new_module.__dict__, locals=None, description=module_name)
            return cls.add_module(new_module)

    def __init__(self, py_module: ModuleType, module_path: str) -> None:
        """
        Constructor of the _Module wrapper.
        :param module_obj: a python module object
        """
        self.module_file = module_path
        # File with the module source code.
        self.py_module = py_module
        # The python module object.

        self.definitions = []
        # Actions defined in the module. Includes:
        # Workflows, python source actions (GUI can not edit modules with these actions),
        # data classes, enums.
        # GUI note: Can be directly reorganized by the GUI. Adding, removing, changing order.
        # TODO: implement a method for sorting the definitions (which criteria)
        #self._name_to_def = {}
        # Maps identifiers to the definitions. (e.g. name of a workflow to its object)

        # self.imported_modules = []
        # # List of imported modules.

        self._object_names = {}
        # Map from the (obj.__module__, obj.__name__) of an object to
        # the correct referencing of the object in this module.
        # This is necessary in particular for actions defined through 'action_def', for the imported modules
        # and also for the actions of the visip library.
        # Note: id(obj) can not be used since a type hint of a decorated class does not undergo the decoration

        # TODO: generalize for other 'rebranding' packages.

        #self.ignored_definitions = []
        # Objects of the module, that can not by sourced.
        # If there are any we can not reproduce the source.

        # self.extract_definitions()

        self.new_definitions : Dict[str, _DefBase] = {}
        # Map alias -> _Def*

        # need separate list to keep and modify order and map for module, name lookup
        # can rather keep just map alias -> definition, and existing _object_names: (module, name) -> alias
        # .. complemented by the list of definitions for the ordering this list will be modified by GUI,
        # rest is internal

    @property
    def __name__(self):
        return self.py_module.__name__

    @property
    def name(self):
        return self.py_module.__name__

    # @property
    # def _object_names(self):
    #     # TODO:
    #     return


    @property
    def imported_modules(self) -> List['Module']:
        return [def_.module for mod_name, def_ in self.new_definitions.items() if isinstance(def_, _DefImport)]

    @property
    def ignored_definitions(self) -> List[str]:
        return [def_.alias for mod_name, def_ in self.new_definitions.items() if isinstance(def_, _DefUnknown)]

    # def _object_name(self, mod_name):
    #     try:
    #         # try to find own alias
    #         return self.new_definitions[mod_name].alias
    #     except KeyError:
    #         pass
    #     mod, name = mod_name
    #     try:
    #         # objects from imported modules
    #         module = self.get_module(mod)
    #     except KeyError:
    #         assert False
    #     try:
    #
    #     return

    def object_name(self, obj):
        return self._object_names.get(self.mod_name(obj), None)

    def is_visip_module(self):
        return len(self.definitions) > 0

    def __repr__(self):
        if self.is_visip_module():
            return f"VISIP module {self.name}"
        else:
            return f"non-VISIP module: {self.name}"

    def info(self):
        return f"{self}, #defs: {len(self.definitions)}, #other: {len(self.ignored_definitions)}, file: {self.module_file}"

    def is_visip_def(self, obj: object):
        is_visip_instance = isinstance(obj, (DummyAction, DummyWorkflow))
        return is_visip_instance and hasattr(obj, 'wrapped')



    def extract_definitions(self):
        """
        Extract definitions from the python module.
        :return:
        """
        analysis = []
        for name, obj in self.py_module.__dict__.items():
            if self.is_dunder(name):
                continue
            obj_module, obj_name = self.mod_name(obj)
            if type(obj) is ModuleType:

                # import 'obj' as 'name'
                visip_mod = self.add_module(obj)
                assert visip_mod is not None
                #self.imported_modules.append(visip_mod)
                self.new_definitions[(obj_module, obj_name)] = _DefImport(name, visip_mod)

                #self._module_name_dict[obj.__name__] = name

                continue
            if self.is_visip_def(obj):
                visip_obj = obj.wrapped()
                obj_module, obj_name = self.mod_name(visip_obj)
                if obj_module != self.py_module.__name__:
                    #assert False, "from .. import ..  : not implemented yet for VISIP objects "
                    pass

                #print("DBG wrap: ", obj)
                mod_name = self.mod_name(visip_obj)
                #self.add_module_by_name(mod_name[0])

                self.insert_definition(visip_obj)
                if visip_obj.is_analysis:
                    analysis.append(visip_obj)
                self.new_definitions[(obj_module, obj_name)] = _DefAction(name, visip_obj)

            else:
                if obj_module != self.py_module.__name__:
                    # from 'obj_module' import 'obj_name' as 'name'
                    self.new_definitions[(obj_module, obj_name)] = _DefFrom(name, obj)
                    # TODO: test and full implementation
                    # we shoul import the source module and then take here reference to the created VISIP objects

                else:
                    self.new_definitions[(obj_module, obj_name)] = _DefUnknown(name, obj)

        #print("Create object names module: ", self.py_module.__name__)
        self._create_object_names(self.py_module, "")

        if self.is_visip_module():
            assert self.module_file != "", f"Missing file path for the VISIP module: {self}"

        # self.analysis = analysis
        # #assert len(analysis) <= 1, [x.name for x in analysis]
        # if analysis:
        #     # make instance of the main workflow
        #     analysis = analysis[0]
        #     self.analysis = ActionCall.create(analysis)
        # else:
        #     self.analysis = None

    def new_object_names(self):
        """
        Create from extracted definitions.
        :return:
        """


    def _create_object_names(self, mod_obj, alias):
        """
        Create
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

        TODO: merge with creation of new_definitions.
        - imported renamed modules must be taken into account
        - possibly need helper dictionaries or getters to access e.g. only _DefImports of given name
        """
        module_queue = deque()  # queue of (module, alias_module_name)
        name, obj = alias, mod_obj
        obj_mod_name = self.mod_name(obj)
        if obj_mod_name in self._object_names:
            return
        alias_name = f"{name}".lstrip('.')
        module_queue.append((obj, alias_name))
        self._set_object_names(obj_mod_name, alias_name)
        # ================

        while module_queue:

            mod_obj, mod_alias = module_queue.popleft()
            # print("Processing module: ", mod_obj.__name__, mod_alias)

            # process new module
            package = mod_obj.__name__.split('.')[0]
            # process only for visip modules and for
            # modules importing visip
            attr_names = {attr.__name__ for attr in mod_obj.__dict__.values() if hasattr(attr, '__name__')}
            if not (package == 'visip' or 'visip' in attr_names):
                continue

            for name, obj in mod_obj.__dict__.items():
                obj_mod_name = self.mod_name(obj)
                if name.startswith('__'):
                    continue

                alias_name = f"{mod_alias}.{name}".lstrip('.')
                if isinstance(obj, (DummyAction, DummyWorkflow)):
                    obj_mod_name = self.mod_name(obj._action_value)
                elif type(obj) is ModuleType:
                    module_queue.append((obj, alias_name))
                elif obj_mod_name[0] == 'typing':
                    # for Python >= 3.7 the typing generic instances have no attribute __name__
                    obj_mod_name = ('typing', name)

                if obj_mod_name in self._object_names:
                    continue
                self._set_object_names(obj_mod_name, alias_name)

    def _set_object_names(self, mod_name, alias):
        # Internal _object_names setter to simplify debugging.

        # print("Map: ", mod_name, alias)
        mod, name = mod_name
        if mod is not None:
            #print(f"Missing  {mod}:{name}")
            pass
        self._object_names.setdefault(mod_name, alias)

    """
    ===================
    GUI modifiers
    ===================
    """

    """
    TODO: generalize modifications:
    We consider the module as a list of definitions and support
    insertion and removal from that list. 
    Renaming is operation on the definition.
    Curently new_definitions is a dict, but seems there is no usage for the key access.
    """

    def insert_imported_module(self, mod_obj: 'Module', alias: str):
        mod_obj = Module.add_module(mod_obj.py_module)
        mod_obj.extract_definitions()
        self.new_definitions[self.mod_name(mod_obj)] = _DefImport(alias, mod_obj)
        # self.imported_modules.append(mod_obj)
        # if alias == "":
        #     alias = getattr(mod_obj, "__name__", None)
        # self._create_object_names(mod_obj.py_module, alias)


    def insert_definition(self, action: dtype._ActionBase, pos: int = None):
        """
        Insert a new definition of the 'action' to given position 'pos'.
        :param action: An action class (including dataclass construction actions).
        :param pos: Target position, default is __len__ meaning append to the list.
        :return:
        """
        if pos is None:
            pos = len(self.definitions)
        #print("DBG insert def:",  action)
        assert isinstance(action, dtype._ActionBase) , action
               #or issubclass(action, constructor.visip_enum)
        self.definitions.insert(pos, action)
        #self._name_to_def[action.name] = action

    def rename_definition(self, name: str, new_name: str) -> None:
        """
        Rename workflow, dataclass, enum definition.
        Renaming other actions fails.

        Does not deal with references to the original name.
        TODO: sort of global index with usages of individual definitions.
        """
        action = self.get_action(name)
        if isinstance(action, wf._Workflow):
            action.name = new_name
            #self._name_to_def[new_name] = action
            #del self._name_to_def[name]
        elif isinstance(action, constructor.ClassActionBase):
            action.name = new_name
            #self._name_to_def[new_name] = action
            #del self._name_to_def[name]
        else:
            assert False, "Only workflow and classes can be renamed."

    def relative_name(self, obj_module, obj_name):
        """
        Construct the action class name for given set of imported modules.
        :param module_dict: A dict mapping the full module path to its imported alias.
        :return: The action name using the alias instead of the full module path.
        """
        try:
            mod_name = (obj_module, obj_name)
            return self._object_names[mod_name]
        except KeyError:
            if obj_module == 'builtins':
                return obj_name
            else:
                print("Undef reference for:", mod_name)
                return f"{obj_module}.{obj_name}"



    def code(self) -> str:
        """
        Generate the source code of the whole module.
        :return:
        """
        representer = Representer(self.relative_name)
        source = []
        # make imports
        for visip_module in self.imported_modules:
            impr = visip_module.py_module
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
            source.extend(["", ""])  # two empty lines as separator
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


    def get_action(self, name: str) -> base.ActionBase:
        """
        Get the action by the name (alias).
        """
        for d in self.new_definitions.values():
            action = d.get_action(name)
            if action:
                return action
        return None

    # def get_dataclass(self, name:str) -> Callable[..., dtype.DataClassBase]:
    #     """
    #     ??? Not clear why this should exist.
    #     """
    #     assert False
    #     #dclass = self._name_to_def[name]
    #     #return dclass._evaluate
