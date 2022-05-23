"""
This module provides public interface of the VISIP language.
Public names are:

Decorators: workflow, analysis, action, Class

wrapped actions:
    list, tuple, dict, ...

All underscored names are private
"""

# def decorators
from .code.decorators import workflow, analysis, action_def, Class, Enum

# builtin
from .action.wrapped import list, dict, tuple, If, lazy, empty, Pass, While, abs, round, pow, divmod


# std
from .action.std import \
    file_in, file_out, FileIn, FileOut, Folder, system, SysFile, ExecResult, \
    derived_file, file_from_template, format

# internal (possibly remove from public API)
from .action.slots import _Slot as _Slot
from .dev.action_workflow import _Result as _Result
from .action.constructor import Value as _Value
from .action import converter as _converter
from .dev.dtype import Bool, Int, Float, Str, Any, NoneType, List, Dict, Tuple, Union, Const

# TODO:
# distinguish:
# - wrapped actions, i.e. names used in workflow definitions
#   e.g. list, dict, tuple, load_yaml
#
# - action instances, single instance for every base action class (used in following list and then in the visip_gui)
#   list.action, dict.action, tuple.action, load_yaml.action
#
# - action classes (internal use only)
#   A_list, A_dict, A_tuple
#
# Make unique naming scheme to clearly distinguish these objects.
# Consider what should be in the visip namespace in particular which actions.
#
# Can we treat all actions in visip module directly instead of using following special list?
# TB: If all available action are in ActionWrapper than its no problem.
# TB: Currently present actions in this list aren't ActionWrapper.
base_system_actions = [_Slot(),
                       _converter.GetAttribute(),
                       _converter.GetItem(), #GetKey()
                       ]

"""
FUTURE:
- Resources:
    latency, speed, tags (supported features, HW, SW)  

TODO:  
- side_effect results - perform some actions for their sideefect, need a way to connect them to the result action instance
  that way result should have arbitrary number of parameters, but only the first is used (not good for a workflow with side effect but no true return value)

- introduce other special action instance SideEffect (works like result but is used for DFS,
  side effect always contains result as its input

3. GUI way to modify dataclasses and enums

3. test importing of user modules, better test of module functions
    - every action knows its __module__ that is full module name (not the alias from the import) 
    - must pass imports as a dictionalry to translate full module names to aliasses
    - implement full and iterative collection of used modules in definitions of the module
    #instance should  know its module path 
4. test_gui_api, etc

6. Typechecking

- have common class for actions (current classes)
- other class (composition) for action instance
  ... no dynamical class creation
- How to deal with types, i.e. with dataclasses ... thats fine current spec have no support for inheritance
- Need typing extension to specify protocol "a dataclass with a key xyz"
- Can use dataclasses both as constructors and as type specification 
   (must set a _type attribute to the action wrapper function)

3. user modules: 
    - from analysis.workflow import *
        - decorators: workflow, analysis, Class, Enum
        - actions - basic, other in modules, lowercase
        - types - basic, other in modules, UpperCase 

    - from analysis import impl
        - @impl.action
        - impl.ActionBase
        - impl.AtomicAction
        - impl.DynamicAction  

    - Module
      [ Workflow, Class, Enum, Analysis]
    - Workflow
      [ ActionInstance ]
    - ActionInstance
      [ ActionBase ]
    code, workflow_dag, task_dag, scheduler


0: base actions overview
    data manipulation:
    - Value
    - Class ..
    - List
    - Dict
    - GetAttribute
    - GetListItem
    - GetDictItem

    ?? transpose - List[Class] -> Class[List] etc.
    ... sort of 'zip'

    expressions:
    - operators: +, -, *, /, %, **, @, 
    - math functions
    - not able to capture parenthesis

    file: 
    - load/save YAML/JSON + template substitution
    - serialization/deserialization of dataclasses and whole datatrees


    metaactions (actions taking a workflow as parameter):
    - foreach - apply a workflow with single slot to every item of a list 
    - while - takes the BODY workflow (automorphism) and PREDICATE (bool result)
            - expand BODY only if PREDICATE is true. 


5. Safe loading of sources in separate process.
    - Load and safe in separate process, catching the errors and prevent crashes and infinite loops.
    - Load the round trip source in the GUI/evaluation 

"""

