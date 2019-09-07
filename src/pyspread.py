#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Copyright Martin Manns
# Distributed under the terms of the GNU General Public License

# --------------------------------------------------------------------
# pyspread is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyspread is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyspread.  If not, see <http://www.gnu.org/licenses/>.
# --------------------------------------------------------------------

"""

========
pyspread
========

Python spreadsheet application

Run this script to start the application.

Provides
--------

* Commandlineparser: Gets command line options and parameters
* MainApplication: Initial command line operations and application launch

"""

from pathlib import Path
import os
import sys

from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtWidgets import QMainWindow, QApplication, QSplitter, QMessageBox
from PyQt5.QtWidgets import QDockWidget, QUndoStack
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QColor, QFont

from src.settings import Settings, VERSION
from src.icons import Icon
from src.grid import Grid
from src.entryline import Entryline
from src.menubar import MenuBar
from src.toolbar import MainToolBar, FindToolbar, FormatToolbar, MacroToolbar
from src.toolbar import WidgetToolbar
from src.actions import MainWindowActions
from src.workflows import Workflows
from src.widgets import Widgets
from src.dialogs import ApproveWarningDialog, PreferencesDialog
from src.panels import MacroPanel


LICENSE = "GNU GENERAL PUBLIC LICENSE Version 3"

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


class ApplicationStates:
    """Holds all global application states"""

    # Names of widgets with persistant states
    widget_names = ['main_window', "main_toolbar", "find_toolbar",
                    "format_toolbar", "macro_toolbar", "widget_toolbar"]

    # Note that safe_mode is not listed here but inside model.DataArray

    changed_since_save = False  # If True then File actions trigger a dialog
    last_file_input_path = Path.home()  # Initial path for opening files
    last_file_output_path = Path.home()  # Initial path for saving files
    border_choice = "All borders"  # The state of the border choice button

    def __init__(self, parent):
        super().__setattr__("parent", parent)
        super().__setattr__("settings", parent.settings)

    def __setattr__(self, key, value):
        if not hasattr(self, key):
            raise AttributeError("{self} has no attribute {key}.".format(
                                 self=self, key=key))
        object.__setattr__(self, key, value)

    def reset(self):
        cls_attrs = (attr for attr in dir(self)
                     if (not attr.startswith("__")
                         and attr not in ("reset", "parent", "settings",
                                          "save_gui_states",
                                          "restore_gui_states")))
        for cls_attr in cls_attrs:
            setattr(self, cls_attr, getattr(ApplicationStates, cls_attr))

    def save_gui_states(self):
        """Saves GUI states to QSettings"""

        for widget_name in self.widget_names:
            geometry_name = widget_name + '/geometry'
            widget_state_name = widget_name + '/windowState'

            if widget_name == "main_window":
                widget = self.parent
            else:
                widget = getattr(self.parent, widget_name)
            try:
                self.settings.qsettings.setValue(geometry_name,
                                                 widget.saveGeometry())
            except AttributeError:
                pass
            try:
                self.settings.qsettings.setValue(widget_state_name,
                                                 widget.saveState())
            except AttributeError:
                pass

        self.settings.qsettings.sync()

    def restore_gui_states(self):
        """Restores GUI states from QSettings"""

        for widget_name in self.widget_names:
            geometry_name = widget_name + '/geometry'
            widget_state_name = widget_name + '/windowState'

            if widget_name == "main_window":
                widget = self.parent
            else:
                widget = getattr(self.parent, widget_name)

            geometry = self.settings.qsettings.value(geometry_name)
            if geometry:
                widget.restoreGeometry(geometry)
            widget_state = self.settings.qsettings.value(widget_state_name)
            if widget_state:
                widget.restoreState(widget_state)


class MainWindow(QMainWindow):
    """Pyspread main window"""

    gui_update = pyqtSignal(dict)

    def __init__(self, application):
        super().__init__()

        self._loading = True
        self.application = application
        self.settings = Settings()
        self.application_states = ApplicationStates(self)
        self.workflows = Workflows(self)
        self.undo_stack = QUndoStack(self)

        self._init_widgets()

        self.actions = MainWindowActions(self)

        self._init_window()
        self._init_toolbars()

        self.application_states.restore_gui_states()

        self.show()
        self._update_action_toggles()

        self._loading = False
        self._previous_window_state = self.windowState()

    def _init_window(self):
        """Initialize main window components"""

        self.setWindowTitle('Pyspread')
        self.setWindowIcon(Icon("pyspread"))

        self.safe_mode_widget = QSvgWidget(Icon.icon_path["warning"], self)
        msg = "Pyspread is in safe mode.\nExpressions are not evaluated."
        self.safe_mode_widget.setToolTip(msg)
        self.statusBar().addPermanentWidget(self.safe_mode_widget)
        self.safe_mode_widget.hide()

        self.setMenuBar(MenuBar(self))

    def resizeEvent(self, event):
        super(MainWindow, self).resizeEvent(event)
        if self._loading:
            return

    def closeEvent(self, event):
        """Overloaded close event, allows saving changes or canceling close"""

        self.application_states.save_gui_states()

        self.workflows.file_quit()
        event.ignore()

    def _init_widgets(self):
        """Initialize widgets"""

        self.widgets = Widgets(self)

        self.entry_line = Entryline(self)
        self.grid = Grid(self)

        self.macro_panel = MacroPanel(self, self.grid.model.code_array)

        main_splitter = QSplitter(Qt.Vertical, self)
        self.setCentralWidget(main_splitter)

        main_splitter.addWidget(self.entry_line)
        main_splitter.addWidget(self.grid)
        main_splitter.addWidget(self.grid.table_choice)
        main_splitter.setSizes([self.entry_line.minimumHeight(), 9999, 20])

        self.macro_dock = QDockWidget("Macros", self)
        self.macro_dock.setObjectName("Macro panel")
        self.macro_dock.setWidget(self.macro_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.macro_dock)

        self.macro_dock.installEventFilter(self)

        self.gui_update.connect(self.on_gui_update)

    def eventFilter(self, source, event):
        """Event filter for handling QDockWidget close events

        Updates the menu if the macro panel is closed.

        """

        if event.type() == QEvent.Close \
           and isinstance(source, QDockWidget) \
           and source.windowTitle() == "Macros":
            self.actions["toggle_macro_panel"].setChecked(False)
        return super().eventFilter(source, event)

    def _init_toolbars(self):
        """Initialize the main window toolbars"""

        self.main_toolbar = MainToolBar(self)
        self.find_toolbar = FindToolbar(self)
        self.format_toolbar = FormatToolbar(self)
        self.macro_toolbar = MacroToolbar(self)
        self.widget_toolbar = WidgetToolbar(self)

        self.addToolBar(self.main_toolbar)
        self.addToolBar(self.find_toolbar)
        self.addToolBarBreak()
        self.addToolBar(self.format_toolbar)
        self.addToolBar(self.macro_toolbar)
        self.addToolBar(self.widget_toolbar)

    def _update_action_toggles(self):
        """Updates the toggle menu check states"""

        self.actions["toggle_main_toolbar"].setChecked(
                self.main_toolbar.isVisible())

        self.actions["toggle_macro_toolbar"].setChecked(
                self.macro_toolbar.isVisible())

        self.actions["toggle_widget_toolbar"].setChecked(
                self.widget_toolbar.isVisible())

        self.actions["toggle_format_toolbar"].setChecked(
                self.format_toolbar.isVisible())

        self.actions["toggle_find_toolbar"].setChecked(
                self.find_toolbar.isVisible())

        self.actions["toggle_entry_line"].setChecked(
                self.entry_line.isVisible())

        self.actions["toggle_macro_panel"].setChecked(
                self.macro_dock.isVisible())

    @property
    def safe_mode(self):
        """Returns safe_mode state. In safe_mode cells are not evaluated."""

        return self.grid.model.code_array.safe_mode

    @safe_mode.setter
    def safe_mode(self, value):
        """Sets safe mode.

        This triggers the safe_mode icon in the statusbar.

        If safe_mode changes from True to False then caches are cleared and
        macros are executed.

        """

        if self.grid.model.code_array.safe_mode == bool(value):
            return

        self.grid.model.code_array.safe_mode = bool(value)

        if value:  # Safe mode entered
            self.safe_mode_widget.show()
        else:  # Safe_mode disabled
            self.safe_mode_widget.hide()
            # Clear result cache
            self.grid.model.code_array.result_cache.clear()
            # Execute macros
            self.grid.model.code_array.execute_macros()

    def on_nothing(self):
        """Dummy action that does nothing"""
        pass

    def on_fullscreen(self):
        """Fullscreen toggle event handler"""

        if self.windowState() == Qt.WindowFullScreen:
            self.setWindowState(self._previous_window_state)
        else:
            self._previous_window_state = self.windowState()
            self.setWindowState(Qt.WindowFullScreen)

    def on_approve(self):
        """Approve event handler"""

        if ApproveWarningDialog(self).choice:
            self.safe_mode = False

    def on_preferences(self):
        """Preferences event handler"""

        data = PreferencesDialog(self).data
        if data is not None:
            # Dialog has not been approved --> Store data to settings
            for key in data:
                self.settings.__setattr__(key, data[key])

    def on_undo(self):
        """Undo event handler"""

        self.undo_stack.undo()

    def on_redo(self):
        """Undo event handler"""

        self.undo_stack.redo()

    def _toggle_widget(self, widget, action_name):
        """Toggles widget visibility and updates toggle actions"""

        if widget.isVisible():
            widget.hide()
        else:
            widget.show()

        self.actions[action_name].setChecked(widget.isVisible())

    def on_toggle_main_toolbar(self):
        """Main toolbar toggle event handler"""

        self._toggle_widget(self.main_toolbar, "toggle_main_toolbar")

    def on_toggle_macro_toolbar(self):
        """Macro toolbar toggle event handler"""

        self._toggle_widget(self.macro_toolbar, "toggle_macro_toolbar")

    def on_toggle_widget_toolbar(self):
        """Wwidget toolbar toggle event handler"""

        self._toggle_widget(self.widget_toolbar, "toggle_widget_toolbar")

    def on_toggle_format_toolbar(self):
        """Format toolbar toggle event handler"""

        self._toggle_widget(self.format_toolbar, "toggle_format_toolbar")

    def on_toggle_find_toolbar(self):
        """Find toolbar toggle event handler"""

        self._toggle_widget(self.find_toolbar, "toggle_find_toolbar")

    def on_toggle_entry_line(self):
        """Entryline toggle event handler"""

        self._toggle_widget(self.entry_line, "toggle_entry_line")

    def on_toggle_macro_panel(self):
        """Macro panel toggle event handler"""

        self._toggle_widget(self.macro_dock, "toggle_macro_panel")

    def on_about(self):
        """Show about message box"""

        about_msg_template = "<p>".join((
            "<b>Pyspread</b>",
            "A non-traditional Python spreadsheet application",
            "Version {version}",
            "Created by:<br>{devs}",
            "Documented by:<br>{doc_devs}",
            "Copyright:<br>Martin Manns",
            "License:<br>{license}",
            '<a href="https://manns.github.io/pyspread/">Pyspread website</a>',
            ))

        devs = "Martin Manns, Jason Sexauer<br>Vova Kolobok, mgunyho"

        doc_devs = "Martin Manns, Bosko Markovic"

        about_msg = about_msg_template.format(
            version=VERSION, devs=devs, doc_devs=doc_devs, license=LICENSE)
        QMessageBox.about(self, "About pyspread", about_msg)

    def on_gui_update(self, attributes):
        """GUI update event handler.

        Emmitted on cell change. Attributes contains current cell_attributes.

        """

        widgets = self.widgets

        is_bold = attributes["fontweight"] == QFont.Bold
        self.actions["bold"].setChecked(is_bold)

        is_italic = attributes["fontstyle"] == QFont.StyleItalic
        self.actions["italics"].setChecked(is_italic)

        underline_action = self.actions["underline"]
        underline_action.setChecked(attributes["underline"])

        strikethrough_action = self.actions["strikethrough"]
        strikethrough_action.setChecked(attributes["strikethrough"])

        renderer = attributes["renderer"]
        widgets.renderer_button.set_current_action(renderer)
        widgets.renderer_button.set_menu_checked(renderer)

        lock_action = self.actions["lock_cell"]
        lock_action.setChecked(attributes["locked"])
        self.entry_line.setReadOnly(attributes["locked"])

        rotation = "rotate_{angle}".format(angle=int(attributes["angle"]))
        widgets.rotate_button.set_current_action(rotation)
        widgets.rotate_button.set_menu_checked(rotation)
        widgets.justify_button.set_current_action(attributes["justification"])
        widgets.justify_button.set_menu_checked(attributes["justification"])
        widgets.align_button.set_current_action(attributes["vertical_align"])
        widgets.align_button.set_menu_checked(attributes["vertical_align"])

        border_action = self.actions.border_group.checkedAction()
        if border_action is not None:
            icon = border_action.icon()
            self.menuBar().border_submenu.setIcon(icon)
            self.format_toolbar.border_menu_button.setIcon(icon)

        border_width_action = self.actions.border_width_group.checkedAction()
        if border_width_action is not None:
            icon = border_width_action.icon()
            self.menuBar().line_width_submenu.setIcon(icon)
            self.format_toolbar.line_width_button.setIcon(icon)

        widgets.text_color_button.color = QColor(*attributes["textcolor"])
        widgets.background_color_button.color = QColor(*attributes["bgcolor"])
        widgets.font_combo.font = attributes["textfont"]
        widgets.font_size_combo.size = attributes["pointsize"]

        merge_cells_action = self.actions["merge_cells"]
        merge_cells_action.setChecked(attributes["merge_area"] is not None)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow(app)

    app.exec_()


if __name__ == '__main__':
    main()
