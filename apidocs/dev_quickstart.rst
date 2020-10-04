Dev Quick Start
====================

Below are quick tips and hints on how the plumbing kinda works (not definitive and WIP).

- Fundamental is python3 and the PyQt5 'bindings'
- so PyQt widget documentation is essentially upstream at https://doc.qt.io/qt-5/qt5-intro.html

The app starts with the :class:`pyspread.MainWindow`.

* It is also passed around to other widgets as argument for callback, values, etc.
* On startup the main windows call a set of `_init_*` functions eg :class:`~pyspread.MainWindow._init_toolbars`
  , :class:`~pyspread.MainWindow._init_widgets`
* App persistence is stored in the :class:`settings.Settings` object.

The :mod:`actions` module defines a set of :class:`actions.Action` objects, a convenience constructor for `QAction`.

  * The :mod:`icons` module defines a set of :class:`icons.Icon` objects

  * The icon files are located in the `share/icons/` and are primarily `.svg` (thanks Tango Icon Library project and others)

  * Toolbar item are in :mod:`toolbar` module

  * Menubar item are in :mod:`menubar` module

The `spreadsheet data` is stored in :mod:`model.model` layers:

  * The data is displayed by the :mod:`grid` widgets module

  * The :class:`entryline.EntryLine` widget allows user editing

  * The `QUndoStack` is used for undo/redo and :mod:`commands` contains the `QUndoCommands`

  * The :mod:`workflows` module is where a lot of the logic is

  * Data is written and read from `.pys` files in the :mod:`interfaces.pys` module


- :mod:`dialogs` contains most of the app dialogs
- :mod:`panels` contains some dock widgets
- :mod:`widgets` contains other widgets
- :mod:`lib` contains all sorts of stuff and is to be continued....






