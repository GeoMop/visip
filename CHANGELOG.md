0.1.0-dev
=======
Front end
--------
Should be mostly stable. Editing and running workflow with dynamic actions and callable actions is WIP.
### New Features
- Made new tooltip to show messages to user inside editor
- Tooltip shows action status
- Actions can be renamed in editor by double clicking instance name
- Callable actions can now be visualized
- Data inspection in evaluation expands into tree structure based on source data

### Bugfixes / Improvements
- Improved navigation inside module
- Improved highlighting of selected items in editor
- Fixed category names in toolbox
- User is prevented to connect action to constant parameter and is informed about it through tooltip
- Fixed decoding error with emty config file
- Side docks will use the whole height, bottom dock will not extend to corners if there are side docks
- EvalWindow will now close when last tab closes
- When EvalWindow is closed all eval tabs are also closed, if some evaluation is running user is asked weather the evaluations should be terminated
- When new evaluation is created it will be shown as currently viewed evaluation
- Many small bugfixes
