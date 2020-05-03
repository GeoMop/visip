# visip
Visual Simulation Programming

## Python based syntax

Sources are stored in individual module files. There are two kinds of the file:
Files containing actions implemented in Python using the `@action_def` decorator.
Files containing workflows (functional definitions of actions) using the `@worflow` decorator.
  
The first kind can only be modified through in the source form not through the GUI.
The second kind can be fully modified through the gUI allowing graphical composition
of the actions of the first kind.
  
Further one can define classes (@Class) and enums (@Enum) data types.
All names must be valid Python names and must not begin with underscore.
All invalid names are ignored in the module and result in error when used in a workflow.    