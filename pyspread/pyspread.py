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

pyspread
========

- Main Python spreadsheet application
- Run this script to start the application.

**Provides**

* MainApplication: Initial command line operations and application launch
* :class:`MainWindow`: Main windows class

"""

import os
import sys

from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer, QRectF
from PyQt5.QtWidgets import (QWidget, QMainWindow, QApplication, QSplitter,
                             QMessageBox, QDockWidget, QUndoStack,
                             QStyleOptionViewItem, QAbstractItemView)
try:
    from PyQt5.QtSvg import QSvgWidget
except ImportError:
    QSvgWidget = None
from PyQt5.QtGui import QColor, QFont, QPalette, QPainter
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog

try:
    from pyspread.__init__ import VERSION, APP_NAME
    from pyspread.cli import PyspreadArgumentParser
    from pyspread.settings import Settings
    from pyspread.icons import Icon, IconPath
    from pyspread.grid import Grid
    from pyspread.grid_renderer import painter_save
    from pyspread.entryline import Entryline
    from pyspread.menus import MenuBar
    from pyspread.toolbar import (MainToolBar, FindToolbar, FormatToolbar,
                                  MacroToolbar)
    from pyspread.actions import MainWindowActions
    from pyspread.workflows import Workflows
    from pyspread.widgets import Widgets
    from pyspread.dialogs import (ApproveWarningDialog, PreferencesDialog,
                                  ManualDialog, TutorialDialog,
                                  PrintAreaDialog, PrintPreviewDialog)
    from pyspread.installer import DependenciesDialog
    from pyspread.panels import MacroPanel
    from pyspread.lib.hashing import genkey
    from pyspread.model.model import CellAttributes
except ImportError:
    from __init__ import VERSION, APP_NAME
    from cli import PyspreadArgumentParser
    from settings import Settings
    from icons import Icon, IconPath
    from grid import Grid
    from grid_renderer import painter_save
    from entryline import Entryline
    from menus import MenuBar
    from toolbar import MainToolBar, FindToolbar, FormatToolbar, MacroToolbar
    from actions import MainWindowActions
    from workflows import Workflows
    from widgets import Widgets
    from dialogs import (ApproveWarningDialog, PreferencesDialog, ManualDialog,
                         TutorialDialog, PrintAreaDialog, PrintPreviewDialog)
    from installer import DependenciesDialog
    from panels import MacroPanel
    from lib.hashing import genkey
    from model.model import CellAttributes


LICENSE = "GNU GENERAL PUBLIC LICENSE Version 3"

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)


class MainWindow(QMainWindow):
    """Pyspread main window"""

    gui_update = pyqtSignal(dict)

    def __init__(self, filepath: str = None, reset_settings: bool = False):
        """
        :param filepath: File path for inital file to be opened
        :param reset_settings: Ignore stored `QSettings` and use defaults

        """

        super().__init__()

        self._loading = True

        self.settings = Settings(self, reset_settings=reset_settings)
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

        # Print area for print requests
        self.print_area = None

        # Update recent files in the file menu
        self.menuBar().file_menu.history_submenu.update()

        # Update toolbar toggle checkboxes
        self.update_action_toggles()

        # Update the GUI so that everything matches the model
        cell_attributes = self.grid.model.code_array.cell_attributes
        attributes = cell_attributes[self.grid.current]
        self.on_gui_update(attributes)

        self._loading = False
        self._previous_window_state = self.windowState()

        # Open initial file if provided by the command line
        if filepath is not None:
            if self.workflows.filepath_open(filepath):
                self.workflows.update_main_window_title()
            else:
                msg = "File '{}' could not be opened.".format(filepath)
                self.statusBar().showMessage(msg)

    def _init_window(self):
        """Initialize main window components"""

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(Icon.pyspread)

        # Safe mode widget
        self.safe_mode_widget = QSvgWidget(str(IconPath.safe_mode),
                                           self.statusBar())
        msg = "%s is in safe mode.\nExpressions are not evaluated." % APP_NAME
        self.safe_mode_widget.setToolTip(msg)
        self.statusBar().addPermanentWidget(self.safe_mode_widget)
        self.safe_mode_widget.hide()

        # Selection mode widget
        self.selection_mode_widget = QSvgWidget(str(IconPath.selection_mode),
                                                self.statusBar())
        msg = "Selection mode active. Cells cannot be edited.\n" + \
              "Selecting cells adds relative references into the entry " + \
              "line. Additionally pressing `Meta` switches to absolute " + \
              "references.\nEnd selection mode by clicking into the entry " + \
              "line or with `Esc` when focusing the grid."
        self.selection_mode_widget.setToolTip(msg)
        self.statusBar().addPermanentWidget(self.selection_mode_widget)
        self.selection_mode_widget.hide()

        # Disable the approve fiel menu button
        self.main_window_actions.approve.setEnabled(False)

        self.setMenuBar(MenuBar(self))

    def resizeEvent(self, event: QEvent):
        """Overloaded, aborts on self._loading

        :param event: Resize event

        """

        if self._loading:
            return

        super(MainWindow, self).resizeEvent(event)

    def closeEvent(self, event: QEvent = None):
        """Overloaded, allows saving changes or canceling close

        :param event: Any QEvent

        """

        if event:
            event.ignore()
        self.workflows.file_quit()  # has @handle_changed_since_save decorator

    def _init_widgets(self):
        """Initialize widgets"""

        self.widgets = Widgets(self)

        self.entry_line = Entryline(self)
        self.grid = Grid(self)

        self.macro_panel = MacroPanel(self, self.grid.model.code_array)

        self.main_splitter = QSplitter(Qt.Vertical, self)
        self.setCentralWidget(self.main_splitter)

        self.main_splitter.addWidget(self.entry_line)
        self.main_splitter.addWidget(self.grid)
        self.main_splitter.addWidget(self.grid.table_choice)
        self.main_splitter.setSizes([self.entry_line.minimumHeight(),
                                     9999, 20])

        self.macro_dock = QDockWidget("Macros", self)
        self.macro_dock.setObjectName("Macro Panel")
        self.macro_dock.setWidget(self.macro_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.macro_dock)

        self.macro_dock.installEventFilter(self)

        QApplication.instance().focusChanged.connect(self.on_focus_changed)
        self.gui_update.connect(self.on_gui_update)
        self.refresh_timer.timeout.connect(self.on_refresh_timer)

    def eventFilter(self, source: QWidget, event: QEvent) -> bool:
        """Overloaded event filter for handling QDockWidget close events

        Updates the menu if the macro panel is closed.

        :param source: Source widget of event
        :param event: Any QEvent

        """

        if event.type() == QEvent.Close \
           and isinstance(source, QDockWidget) \
           and source.windowTitle() == "Macros":
            self.main_window_actions.toggle_macro_panel.setChecked(False)
        return super().eventFilter(source, event)

    def _init_toolbars(self):
        """Initialize the main window toolbars"""

        self.main_toolbar = MainToolBar(self)
        self.macro_toolbar = MacroToolbar(self)
        self.find_toolbar = FindToolbar(self)
        self.format_toolbar = FormatToolbar(self)

        self.addToolBar(self.main_toolbar)
        self.addToolBar(self.macro_toolbar)
        self.addToolBar(self.find_toolbar)
        self.addToolBarBreak()
        self.addToolBar(self.format_toolbar)

    def update_action_toggles(self):
        """Updates the toggle menu check states"""

        actions = self.main_window_actions

        maintoolbar_visible = self.main_toolbar.isVisibleTo(self)
        actions.toggle_main_toolbar.setChecked(maintoolbar_visible)

        macrotoolbar_visible = self.macro_toolbar.isVisibleTo(self)
        actions.toggle_macro_toolbar.setChecked(macrotoolbar_visible)

        formattoolbar_visible = self.format_toolbar.isVisibleTo(self)
        actions.toggle_format_toolbar.setChecked(formattoolbar_visible)

        findtoolbar_visible = self.find_toolbar.isVisibleTo(self)
        actions.toggle_find_toolbar.setChecked(findtoolbar_visible)

        entryline_visible = self.entry_line.isVisibleTo(self)
        actions.toggle_entry_line.setChecked(entryline_visible)

        macrodock_visible = self.macro_dock.isVisibleTo(self)
        actions.toggle_macro_panel.setChecked(macrodock_visible)

    @property
    def safe_mode(self) -> bool:
        """Returns safe_mode state. In safe_mode cells are not evaluated."""

        return self.grid.model.code_array.safe_mode

    @safe_mode.setter
    def safe_mode(self, value: bool):
        """Sets safe mode.

        This triggers the safe_mode icon in the statusbar.

        If safe_mode changes from True to False then caches are cleared and
        macros are executed.

        :param value: Safe mode

        """

        if self.grid.model.code_array.safe_mode == bool(value):
            return

        self.grid.model.code_array.safe_mode = bool(value)

        if value:  # Safe mode entered
            self.safe_mode_widget.show()
            # Enable approval menu entry
            self.main_window_actions.approve.setEnabled(True)
        else:  # Safe_mode disabled
            self.safe_mode_widget.hide()
            # Disable approval menu entry
            self.main_window_actions.approve.setEnabled(False)
            # Clear result cache
            self.grid.model.code_array.result_cache.clear()
            # Execute macros
            self.macro_panel.on_apply()

    def on_print(self):
        """Print event handler"""

        # Create printer
        printer = QPrinter(mode=QPrinter.HighResolution)

        # Get print area
        self.print_area = PrintAreaDialog(self, self.grid,
                                          title="Print area").area
        if self.print_area is None:
            return

        # Create print dialog
        dialog = QPrintDialog(printer, self)
        if dialog.exec_() == QPrintDialog.Accepted:
            self.on_paint_request(printer)

    def on_preview(self):
        """Print preview event handler"""

        # Create printer
        printer = QPrinter(mode=QPrinter.HighResolution)

        # Get print area
        self.print_area = PrintAreaDialog(self, self.grid,
                                          title="Print area").area
        if self.print_area is None:
            return

        # Create print preview dialog
        dialog = PrintPreviewDialog(printer)

        dialog.paintRequested.connect(self.on_paint_request)
        dialog.exec_()

    def on_paint_request(self, printer: QPrinter):
        """Paints to printer

        :param printer: Target printer

        """

        painter = QPainter(printer)
        option = QStyleOptionViewItem()
        painter.setRenderHints(QPainter.SmoothPixmapTransform
                               | QPainter.SmoothPixmapTransform)

        page_rect = printer.pageRect()

        rows = list(self.workflows.get_paint_rows(self.print_area.top,
                                                  self.print_area.bottom))
        columns = list(self.workflows.get_paint_columns(self.print_area.left,
                                                        self.print_area.right))
        tables = list(self.workflows.get_paint_tables(self.print_area.first,
                                                      self.print_area.last))
        if not all((rows, columns, tables)):
            return

        old_table = self.grid.table

        for i, table in enumerate(tables):
            self.grid.table = table

            zeroidx = self.grid.model.index(0, 0)
            zeroidx_rect = self.grid.visualRect(zeroidx)

            minidx = self.grid.model.index(min(rows), min(columns))
            minidx_rect = self.grid.visualRect(minidx)

            maxidx = self.grid.model.index(max(rows), max(columns))
            maxidx_rect = self.grid.visualRect(maxidx)

            grid_width = maxidx_rect.x() + maxidx_rect.width() \
                - minidx_rect.x()
            grid_height = maxidx_rect.y() + maxidx_rect.height() \
                - minidx_rect.y()
            grid_rect = QRectF(minidx_rect.x() - zeroidx_rect.x(),
                               minidx_rect.y() - zeroidx_rect.y(),
                               grid_width, grid_height)

            self.settings.print_zoom = min(page_rect.width() / grid_width,
                                           page_rect.height() / grid_height)

            with painter_save(painter):
                painter.scale(self.settings.print_zoom,
                              self.settings.print_zoom)

                # Translate so that the grid starts at upper left paper edge
                painter.translate(zeroidx_rect.x() - minidx_rect.x(),
                                  zeroidx_rect.y() - minidx_rect.y())

                # Draw grid cells
                self.workflows.paint(painter, option, grid_rect, rows, columns)

            self.settings.print_zoom = None

            if i != len(tables) - 1:
                printer.newPage()

        self.grid.table = old_table

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

    def on_clear_globals(self):
        """Clear globals event handler"""

        self.grid.model.code_array.result_cache.clear()

        # Clear globals
        self.grid.model.code_array.clear_globals()
        self.grid.model.code_array.reload_modules()

    def on_preferences(self):
        """Preferences event handler (:class:`dialogs.PreferencesDialog`) """

        data = PreferencesDialog(self).data

        if data is not None:
            max_file_history_changed = \
                self.settings.max_file_history != data['max_file_history']

            # Dialog has been approved --> Store data to settings
            for key in data:
                if key == "signature_key" and not data[key]:
                    data[key] = genkey()
                self.settings.__setattr__(key, data[key])

            # Immediately adjust file history in menu
            if max_file_history_changed:
                self.menuBar().file_menu.history_submenu.update()

    def on_dependencies(self):
        """Dependancies installer (:class:`installer.InstallerDialog`) """

        dial = DependenciesDialog(self)
        dial.exec_()

    def on_undo(self):
        """Undo event handler"""

        self.undo_stack.undo()

    def on_redo(self):
        """Undo event handler"""

        self.undo_stack.redo()

    def on_toggle_refresh_timer(self, toggled: bool):
        """Toggles periodic timer for frozen cells

        :param toggled: Toggle state

        """

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

    def _toggle_widget(self, widget: QWidget, action_name: str, toggled: bool):
        """Toggles widget visibility and updates toggle actions

        :param widget: Widget to be toggled shown or hidden
        :param action_name: Name of action from Action class
        :param toggled: Toggle state

        """

        if toggled:
            widget.show()
        else:
            widget.hide()

        self.main_window_actions[action_name].setChecked(widget.isVisible())

    def on_toggle_main_toolbar(self, toggled: bool):
        """Main toolbar toggle event handler

        :param toggled: Toggle state

        """

        self._toggle_widget(self.main_toolbar, "toggle_main_toolbar", toggled)

    def on_toggle_macro_toolbar(self, toggled: bool):
        """Macro toolbar toggle event handler

        :param toggled: Toggle state

        """

        self._toggle_widget(self.macro_toolbar, "toggle_macro_toolbar",
                            toggled)

    def on_toggle_format_toolbar(self, toggled: bool):
        """Format toolbar toggle event handler

        :param toggled: Toggle state

        """

        self._toggle_widget(self.format_toolbar, "toggle_format_toolbar",
                            toggled)

    def on_toggle_find_toolbar(self, toggled: bool):
        """Find toolbar toggle event handler

        :param toggled: Toggle state

        """

        self._toggle_widget(self.find_toolbar, "toggle_find_toolbar", toggled)

    def on_toggle_entry_line(self, toggled: bool):
        """Entryline toggle event handler

        :param toggled: Toggle state

        """

        self._toggle_widget(self.entry_line, "toggle_entry_line", toggled)

    def on_toggle_macro_panel(self, toggled: bool):
        """Macro panel toggle event handler

        :param toggled: Toggle state

        """

        self._toggle_widget(self.macro_dock, "toggle_macro_panel", toggled)

    def on_manual(self):
        """Show manual browser"""

        dialog = ManualDialog(self)
        dialog.show()

    def on_tutorial(self):
        """Show tutorial browser"""

        dialog = TutorialDialog(self)
        dialog.show()

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

        devs = "Martin Manns, Jason Sexauer<br>Vova Kolobok, mgunyho, " \
               "Pete Morgan"

        doc_devs = "Martin Manns, Bosko Markovic, Pete Morgan"

        about_msg = about_msg_template.format(version=VERSION, license=LICENSE,
                                              devs=devs, doc_devs=doc_devs)
        QMessageBox.about(self, "About %s" % APP_NAME, about_msg)

    def on_focus_changed(self, old: QWidget, now: QWidget):
        """Handles grid clicks from entry line"""

        if old == self.grid and now == self.entry_line:
            self.grid.selection_mode = False

    def on_gui_update(self, attributes: CellAttributes):
        """GUI update that shall be called on each cell change

        :param attributes: Attributes of current cell

        """

        widgets = self.widgets
        menubar = self.menuBar()

        is_bold = attributes.fontweight == QFont.Bold
        self.main_window_actions.bold.setChecked(is_bold)

        is_italic = attributes.fontstyle == QFont.StyleItalic
        self.main_window_actions.italics.setChecked(is_italic)

        underline_action = self.main_window_actions.underline
        underline_action.setChecked(attributes.underline)

        strikethrough_action = self.main_window_actions.strikethrough
        strikethrough_action.setChecked(attributes.strikethrough)

        renderer = attributes.renderer
        widgets.renderer_button.set_current_action(renderer)
        widgets.renderer_button.set_menu_checked(renderer)

        freeze_action = self.main_window_actions.freeze_cell
        freeze_action.setChecked(attributes.frozen)

        lock_action = self.main_window_actions.lock_cell
        lock_action.setChecked(attributes.locked)
        self.entry_line.setReadOnly(attributes.locked)

        button_action = self.main_window_actions.button_cell
        button_action.setChecked(attributes.button_cell is not False)

        rotation = "rotate_{angle}".format(angle=int(attributes.angle))
        widgets.rotate_button.set_current_action(rotation)
        widgets.rotate_button.set_menu_checked(rotation)
        widgets.justify_button.set_current_action(attributes.justification)
        widgets.justify_button.set_menu_checked(attributes.justification)
        widgets.align_button.set_current_action(attributes.vertical_align)
        widgets.align_button.set_menu_checked(attributes.vertical_align)

        border_action = self.main_window_actions.border_group.checkedAction()
        if border_action is not None:
            icon = border_action.icon()
            menubar.format_menu.border_submenu.setIcon(icon)
            self.format_toolbar.border_menu_button.setIcon(icon)

        border_width_action = \
            self.main_window_actions.border_width_group.checkedAction()
        if border_width_action is not None:
            icon = border_width_action.icon()
            menubar.format_menu.line_width_submenu.setIcon(icon)
            self.format_toolbar.line_width_button.setIcon(icon)

        if attributes.textcolor is None:
            text_color = self.grid.palette().color(QPalette.Text)
        else:
            text_color = QColor(*attributes.textcolor)
        widgets.text_color_button.color = text_color

        if attributes.bgcolor is None:
            bgcolor = self.grid.palette().color(QPalette.Base)
        else:
            bgcolor = QColor(*attributes.bgcolor)
        widgets.background_color_button.color = bgcolor

        if attributes.textfont is None:
            widgets.font_combo.font = QFont().family()
        else:
            widgets.font_combo.font = attributes.textfont
        widgets.font_size_combo.size = attributes.pointsize

        merge_cells_action = self.main_window_actions.merge_cells
        merge_cells_action.setChecked(attributes.merge_area is not None)


def main():
    """Pyspread main"""

    parser = PyspreadArgumentParser()
    args, unknown = parser.parse_known_args()

    app = QApplication(sys.argv)
    main_window = MainWindow(args.file, reset_settings=args.reset_settings)

    main_window.show()

    app.exec_()


if __name__ == '__main__':
    main()
