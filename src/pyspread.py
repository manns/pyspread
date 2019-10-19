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

- Main Python spreadsheet application
- Run this script to start the application.

**Provides**

* Commandlineparser: Gets command line options and parameters
* MainApplication: Initial command line operations and application launch
* :class:`MainWindow`: Main windows class


"""

import os
import sys

from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer
from PyQt5.QtWidgets import QMainWindow, QApplication, QSplitter, QMessageBox
from PyQt5.QtWidgets import QDockWidget, QUndoStack
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtGui import QColor, QFont, QPalette

from src import VERSION, APP_NAME
from src.settings import Settings
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
from src.lib.hashing import genkey


LICENSE = "GNU GENERAL PUBLIC LICENSE Version 3"

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


class MainWindow(QMainWindow):
    """Pyspread main window"""

    gui_update = pyqtSignal(dict)

    def __init__(self, application):
        super().__init__()

        self._loading = True
        self.application = application
        self.settings = Settings(self)
        self.workflows = Workflows(self)
        self.undo_stack = QUndoStack(self)
        self.refresh_timer = QTimer()

        self._init_widgets()

        self.main_window_actions = MainWindowActions(self)

        self._init_window()
        self._init_toolbars()

        self.settings.restore()
        if self.settings.signature_key is None:
            self.settings.signature_key = genkey()

        self.show()
        self._update_action_toggles()

        # Update the GUI so that everything matches the model
        cell_attributes = self.grid.model.code_array.cell_attributes
        attributes = cell_attributes[self.grid.current]
        self.on_gui_update(attributes)

        self._loading = False
        self._previous_window_state = self.windowState()

    def _init_window(self):
        """Initialize main window components"""

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(Icon("pyspread"))

        self.safe_mode_widget = QSvgWidget(Icon.icon_path["warning"], self)
        msg = "%s is in safe mode.\nExpressions are not evaluated." % APP_NAME
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

        self.settings.save()

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
        self.refresh_timer.timeout.connect(self.on_refresh_timer)

    def eventFilter(self, source, event):
        """Event filter for handling QDockWidget close events

        Updates the menu if the macro panel is closed.

        """

        if event.type() == QEvent.Close \
           and isinstance(source, QDockWidget) \
           and source.windowTitle() == "Macros":
            self.main_window_actions["toggle_macro_panel"].setChecked(False)
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

        self.main_window_actions["toggle_main_toolbar"].setChecked(
                self.main_toolbar.isVisible())

        self.main_window_actions["toggle_macro_toolbar"].setChecked(
                self.macro_toolbar.isVisible())

        self.main_window_actions["toggle_widget_toolbar"].setChecked(
                self.widget_toolbar.isVisible())

        self.main_window_actions["toggle_format_toolbar"].setChecked(
                self.format_toolbar.isVisible())

        self.main_window_actions["toggle_find_toolbar"].setChecked(
                self.find_toolbar.isVisible())

        self.main_window_actions["toggle_entry_line"].setChecked(
                self.entry_line.isVisible())

        self.main_window_actions["toggle_macro_panel"].setChecked(
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
        """Preferences event handler (:class:`dialogs.PreferencesDialog`) """

        data = PreferencesDialog(self).data

        if data is not None:
            # Dialog has not been approved --> Store data to settings
            for key in data:
                if key == "signature_key" and not data[key]:
                    data[key] = genkey()
                self.settings.__setattr__(key, data[key])

    def on_undo(self):
        """Undo event handler"""

        self.undo_stack.undo()

    def on_redo(self):
        """Undo event handler"""

        self.undo_stack.redo()

    def on_toggle_refresh_timer(self, toggled):
        """Toggles periodic timer for frozen cells"""

        if toggled:
            self.refresh_timer.start(self.settings.refresh_timeout)
        else:
            self.refresh_timer.stop()

    def on_refresh_timer(self):
        """Event handler for self.refresh_timer.timeout

        Called for periodic updates of frozen cells.
        Does nothing if either the entry_line or a cell editor is active.

        """

        if not self.entry_line.hasFocus() \
           and self.grid.state() != self.grid.EditingState:
            self.grid.refresh_frozen_cells()

    def _toggle_widget(self, widget, action_name, toggled):
        """Toggles widget visibility and updates toggle actions"""

        if toggled:
            widget.show()
        else:
            widget.hide()

        self.main_window_actions[action_name].setChecked(widget.isVisible())

    def on_toggle_main_toolbar(self, toggled):
        """Main toolbar toggle event handler"""

        self._toggle_widget(self.main_toolbar, "toggle_main_toolbar", toggled)

    def on_toggle_macro_toolbar(self, toggled):
        """Macro toolbar toggle event handler"""

        self._toggle_widget(self.macro_toolbar, "toggle_macro_toolbar",
                            toggled)

    def on_toggle_widget_toolbar(self, toggled):
        """Widget toolbar toggle event handler"""

        self._toggle_widget(self.widget_toolbar, "toggle_widget_toolbar",
                            toggled)

    def on_toggle_format_toolbar(self, toggled):
        """Format toolbar toggle event handler"""

        self._toggle_widget(self.format_toolbar, "toggle_format_toolbar",
                            toggled)

    def on_toggle_find_toolbar(self, toggled):
        """Find toolbar toggle event handler"""

        self._toggle_widget(self.find_toolbar, "toggle_find_toolbar", toggled)

    def on_toggle_entry_line(self, toggled):
        """Entryline toggle event handler"""

        self._toggle_widget(self.entry_line, "toggle_entry_line", toggled)

    def on_toggle_macro_panel(self, toggled):
        """Macro panel toggle event handler"""

        self._toggle_widget(self.macro_dock, "toggle_macro_panel", toggled)

    def on_about(self):
        """Show about message box"""

        about_msg_template = "<p>".join((
            "<b>%s</b>" % APP_NAME,
            "A non-traditional Python spreadsheet application",
            "Version {version}",
            "Created by:<br>{devs}",
            "Documented by:<br>{doc_devs}",
            "Copyright:<br>Martin Manns",
            "License:<br>{license}",
            '<a href="https://pyspread.gitlab.io">pyspread.gitlab.io</a>',
            ))

        devs = "Martin Manns, Jason Sexauer<br>Vova Kolobok, mgunyho, Pete Morgan"

        doc_devs = "Martin Manns, Bosko Markovic, Pete Morgan"

        about_msg = about_msg_template.format(
                    version=VERSION, license=LICENSE,
                    devs=devs, doc_devs=doc_devs)
        QMessageBox.about(self, "About %s" % APP_NAME, about_msg)

    def on_gui_update(self, attributes):
        """GUI update event handler.

        Emitted on cell change. Attributes contains current cell_attributes.
        """

        widgets = self.widgets

        is_bold = attributes["fontweight"] == QFont.Bold
        self.main_window_actions["bold"].setChecked(is_bold)

        is_italic = attributes["fontstyle"] == QFont.StyleItalic
        self.main_window_actions["italics"].setChecked(is_italic)

        underline_action = self.main_window_actions["underline"]
        underline_action.setChecked(attributes["underline"])

        strikethrough_action = self.main_window_actions["strikethrough"]
        strikethrough_action.setChecked(attributes["strikethrough"])

        renderer = attributes["renderer"]
        widgets.renderer_button.set_current_action(renderer)
        widgets.renderer_button.set_menu_checked(renderer)

        freeze_action = self.main_window_actions["freeze_cell"]
        freeze_action.setChecked(attributes["frozen"])

        lock_action = self.main_window_actions["lock_cell"]
        lock_action.setChecked(attributes["locked"])
        self.entry_line.setReadOnly(attributes["locked"])

        rotation = "rotate_{angle}".format(angle=int(attributes["angle"]))
        widgets.rotate_button.set_current_action(rotation)
        widgets.rotate_button.set_menu_checked(rotation)
        widgets.justify_button.set_current_action(attributes["justification"])
        widgets.justify_button.set_menu_checked(attributes["justification"])
        widgets.align_button.set_current_action(attributes["vertical_align"])
        widgets.align_button.set_menu_checked(attributes["vertical_align"])

        border_action = self.main_window_actions.border_group.checkedAction()
        if border_action is not None:
            icon = border_action.icon()
            self.menuBar().border_submenu.setIcon(icon)
            self.format_toolbar.border_menu_button.setIcon(icon)

        border_width_action = \
            self.main_window_actions.border_width_group.checkedAction()
        if border_width_action is not None:
            icon = border_width_action.icon()
            self.menuBar().line_width_submenu.setIcon(icon)
            self.format_toolbar.line_width_button.setIcon(icon)

        if attributes["textcolor"] is None:
            text_color = self.grid.palette().color(QPalette.Text)
        else:
            text_color = QColor(*attributes["textcolor"])
        widgets.text_color_button.color = text_color

        if attributes["bgcolor"] is None:
            bgcolor = self.grid.palette().color(QPalette.Base)
        else:
            bgcolor = QColor(*attributes["bgcolor"])
        widgets.background_color_button.color = bgcolor

        widgets.font_combo.font = attributes["textfont"]
        widgets.font_size_combo.size = attributes["pointsize"]

        merge_cells_action = self.main_window_actions["merge_cells"]
        merge_cells_action.setChecked(attributes["merge_area"] is not None)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow(app)

    app.exec_()


if __name__ == '__main__':
    main()
