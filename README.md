# Visip - VIsual SImulation Programming

## Rationale
Simulation workflows are usually composed from several dependent steps forming a directid acyclic graph ([DAG](https://en.wikipedia.org/wiki/Directed_acyclic_graph)).
A single step of this DAG could be a simple task as copying of a file or extracting a few numbers from a file via. a Python script, 
ot it may be a complex task as several hours long parallel finite element calculation.
Developing such a DAG is often painful for following reasons:

### Slow Feedback
Slow error feedback is related to the complex tasks. Thier runtimes are huge and usage of an [HPC](https://en.wikipedia.org/wiki/High-performance_computing) system is necessary.
Further latency is caused by waiting to the free resources as the task is processed by the job scheduling system (JSS), e.g. [PBS](https://en.wikipedia.org/wiki/Portable_Batch_System)).
One solution is to test the task DAG with simplified complex tasks (e.g. using a coarse computational grid) idealy on the local workstation without dealing with JSS.
However, this leads to other issues ..

### Scaling and Portability Issues
Porting the workflow from the workstation to the HPC system is laborous due to complex software dependencies.

## Essential features 
- simulation workflow DAG is described in a form of simple pure functional language based on Python
- automatic type deduction and checking is performed to catch some errors before execution
- task results are stored to a permanent cache allowing to skip repeated calculations for the same inputs
- automatic parallelization (grouping of small tasks)
- graphical language
- conteiners

## Pure Functional Language
- visip docker image
- typy: time map (time -> snapshot), bilance, VTK,
- zobrazovani dat z vypoctu: hodnoty, pole, BREP, MSH, VTK

## Important features (TODO)


## Test cases
- BGEM - GMSH - Flow123d
- Model editor - Flow123d
- Simple calibration (While + foreach) - fracture position - Flow123d
- Flow123d mikro model - Flow123d makro model
- Flow123d HM - Flow123d Transport



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

