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

**Provides**

* :class:`MenuBar`: QMenuBar, the main menubar
* :class:`FileMenu`: File menu for the main menubar
* :class:`EditMenu`: Edit menu for the main menubar
* :class:`ViewMenu`: View menu for the main menubar
* :class:`FormatMenu`: Format menu for the main menubar
* :class:`MacroMenu`: Macro menu for the main menubar
* :class:`HelpMenu`: Help menu for the main menubar
* :class:`FileHistoryMenu`: Menu showing recent files
* :class:`BorderChoiceMenu`: QMenu for choosing cell borders
* :class:`BorderWidthMenu`: QMenu for choosing the cell border width

"""

from functools import partial
from pathlib import Path

from PyQt5.QtWidgets import (
        QMenuBar, QMenu, QAction, QMainWindow, QWidget, QToolBar)

try:
    import matplotlib.figure as matplotlib_figure
except ImportError:
    matplotlib_figure = None

try:
    from pyspread.actions import MainWindowActions
    from pyspread.icons import Icon
except ImportError:
    from actions import MainWindowActions
    from icons import Icon


class MenuBar(QMenuBar):
    """The main menubar """

    def __init__(self, main_window: QMainWindow):
        """
        :param main_window: Application main window

        """

        super().__init__()

        self.main_window = main_window
        actions = main_window.main_window_actions

        self.file_menu = FileMenu(self, actions)
        self.edit_menu = EditMenu(self, actions)
        self.view_menu = ViewMenu(self, actions)
        self.format_menu = FormatMenu(self, actions)
        self.macro_menu = MacroMenu(self, actions)
        self.help_menu = HelpMenu(self, actions)

        self.addMenu(self.file_menu)
        self.addMenu(self.edit_menu)
        self.addMenu(self.view_menu)
        self.addMenu(self.format_menu)
        self.addMenu(self.macro_menu)
        self.addMenu(self.help_menu)


class FileMenu(QMenu):
    """File menu for the main menubar"""

    def __init__(self, parent: QWidget, actions: MainWindowActions):
        """
        :param parent: Parent widget
        :param actions: Main window actions

        """

        super().__init__('&File', parent)

        self.parent = parent

        self.addAction(actions.new)
        self.addAction(actions.open)
        self.history_submenu = FileHistoryMenu(self, actions)
        self.history_action = self.addMenu(self.history_submenu)
        self.addSeparator()
        self.addAction(actions.save)
        self.addAction(actions.save_as)
        self.addSeparator()
        self.addAction(actions.imprt)
        self.addAction(actions.export)
        self.addSeparator()
        self.addAction(actions.approve)
        self.addSeparator()
        self.addAction(actions.clear_globals)
        self.addSeparator()
        self.addAction(actions.print_preview)
        self.addAction(actions.print)
        self.addSeparator()
        self.addAction(actions.preferences)
        self.addSeparator()
        self.addAction(actions.quit)


class EditMenu(QMenu):
    """Edit menu for the main menubar"""

    def __init__(self, parent: QWidget, actions: MainWindowActions):
        """
        :param parent: Parent widget
        :param actions: Main window actions

        """

        super().__init__('&Edit', parent)

        self.addAction(actions.undo)
        self.addAction(actions.redo)
        self.addSeparator()
        self.addAction(actions.cut)
        self.addAction(actions.copy)
        self.addAction(actions.copy_results)
        self.addAction(actions.paste)
        self.addAction(actions.paste_as)
        self.addSeparator()
        self.addAction(actions.find)
        self.addAction(actions.replace)
        self.addSeparator()
        self.addAction(actions.toggle_selection_mode)
        self.addSeparator()
        self.addAction(actions.quote)
        self.addSeparator()
        self.addAction(actions.insert_rows)
        self.addAction(actions.insert_columns)
        self.addAction(actions.insert_table)
        self.addSeparator()
        self.addAction(actions.delete_rows)
        self.addAction(actions.delete_columns)
        self.addAction(actions.delete_table)
        self.addSeparator()
        self.addAction(actions.resize_grid)


class ViewMenu(QMenu):
    """View menu for the main menubar"""

    def __init__(self, parent: QWidget, actions: MainWindowActions):
        """
        :param parent: Parent widget
        :param actions: Main window actions

        """

        super().__init__('&View', parent)

        self.addAction(actions.fullscreen)
        self.addSeparator()

        self.toolbar_submenu = self.addMenu('Toolbars')
        self.toolbar_submenu.addAction(actions.toggle_main_toolbar)
        self.toolbar_submenu.addAction(actions.toggle_macro_toolbar)
        self.toolbar_submenu.addAction(actions.toggle_format_toolbar)
        self.toolbar_submenu.addAction(actions.toggle_find_toolbar)

        self.addAction(actions.toggle_entry_line)
        self.addAction(actions.toggle_macro_panel)
        self.addSeparator()
        self.addAction(actions.goto_cell)
        self.addSeparator()
        self.addAction(actions.toggle_spell_checker)
        self.addSeparator()
        self.addAction(actions.zoom_in)
        self.addAction(actions.zoom_out)
        self.addAction(actions.zoom_1)
        self.addSeparator()
        self.addAction(actions.refresh_cells)
        self.addAction(actions.toggle_periodic_updates)
        self.addSeparator()
        self.addAction(actions.show_frozen)


class FormatMenu(QMenu):
    """Format menu for the main menubar"""

    def __init__(self, parent: QWidget, actions: MainWindowActions):
        """
        :param parent: Parent widget
        :param actions: Main window actions

        """

        super().__init__('&Format', parent)

        self.addAction(actions.copy_format)
        self.addAction(actions.paste_format)
        self.addSeparator()
        self.addAction(actions.font)
        self.addAction(actions.bold)
        self.addAction(actions.italics)
        self.addAction(actions.underline)
        self.addAction(actions.strikethrough)
        self.addSeparator()

        self.renderer_submenu = self.addMenu('Cell renderer')
        self.renderer_submenu.addAction(actions.text)
        self.renderer_submenu.addAction(actions.image)
        self.renderer_submenu.addAction(actions.markup)
        if matplotlib_figure is not None:
            self.renderer_submenu.addAction(actions.matplotlib)

        self.addAction(actions.freeze_cell)
        self.addAction(actions.lock_cell)
        self.addAction(actions.button_cell)

        self.addSeparator()

        self.addAction(actions.merge_cells)

        self.addSeparator()

        self.rotation_submenu = self.addMenu('Rotation')
        self.rotation_submenu.addAction(actions.rotate_0)
        self.rotation_submenu.addAction(actions.rotate_90)
        self.rotation_submenu.addAction(actions.rotate_180)
        self.rotation_submenu.addAction(actions.rotate_270)

        self.justification_submenu = self.addMenu('Justification')
        self.justification_submenu.addAction(actions.justify_left)
        self.justification_submenu.addAction(actions.justify_center)
        self.justification_submenu.addAction(actions.justify_right)
        self.justification_submenu.addAction(actions.justify_fill)

        self.alignment_submenu = self.addMenu('Alignment')
        self.alignment_submenu.addAction(actions.align_top)
        self.alignment_submenu.addAction(actions.align_center)
        self.alignment_submenu.addAction(actions.align_bottom)

        self.addSeparator()

        self.border_submenu = BorderChoiceMenu(actions)
        self.addMenu(self.border_submenu)

        self.line_width_submenu = BorderWidthMenu(actions)
        self.addMenu(self.line_width_submenu)

        self.addSeparator()
        self.addAction(actions.text_color)
        self.addAction(actions.line_color)
        self.addAction(actions.background_color)


class MacroMenu(QMenu):
    """Macro menu for the main menubar"""

    def __init__(self, parent: QWidget, actions: MainWindowActions):
        """
        :param parent: Parent widget
        :param actions: Main window actions

        """

        super().__init__('&Macro', parent)

        self.addAction(actions.insert_image)
        if matplotlib_figure is not None:
            self.addAction(actions.insert_chart)


class HelpMenu(QMenu):
    """Help menu for the main menubar"""

    def __init__(self, parent: QWidget, actions: MainWindowActions):
        """
        :param parent: Parent widget
        :param actions: Main window actions

        """

        super().__init__('&Help', parent)

        self.addAction(actions.manual)
        self.addAction(actions.tutorial)
        self.addSeparator()
        self.addAction(actions.dependencies)
        self.addSeparator()
        self.addAction(actions.about)


class FileHistoryMenu(QMenu):
    """Menu that displays the file history"""

    def __init__(self, parent: QWidget, actions: MainWindowActions):
        """
        :param parent: Parent widget
        :param actions: Main window actions

        """

        super().__init__('&Recent files', parent)

        self.main_window = parent.parent.main_window

    def update(self):
        """Updates file history menu"""

        self.clear()

        settings = self.main_window.settings
        for posixpath in settings.file_history[:settings.max_file_history]:
            filepath = Path(posixpath)
            if filepath.is_file():
                action = QAction(filepath.name, self)
                action.setStatusTip(posixpath)
                self.addAction(action)
                action.triggered.connect(self.on_recent)

    def on_recent(self):
        """Event handler for file history menu"""

        posixpath = self.sender().statusTip()
        self.main_window.workflows.file_open_recent(posixpath)


class BorderChoiceMenu(QMenu):
    """QMenu for choosing cell borders that shall be manipulated"""

    def __init__(self, actions: MainWindowActions):
        """
        :param actions: Main window actions

        """

        super().__init__()

        self.setTitle("Formatted borders")
        self.setIcon(Icon.border_menu)

        self.addAction(actions.format_borders_all)
        self.addAction(actions.format_borders_top)
        self.addAction(actions.format_borders_bottom)
        self.addAction(actions.format_borders_left)
        self.addAction(actions.format_borders_right)
        self.addAction(actions.format_borders_outer)
        self.addAction(actions.format_borders_inner)
        self.addAction(actions.format_borders_top_bottom)


class BorderWidthMenu(QMenu):
    """QMenu for choosing the cell border width"""

    def __init__(self, actions: MainWindowActions):
        """
        :param actions: Main window actions

        """

        super().__init__()

        self.setTitle("Border width")
        self.setIcon(Icon.format_borders)

        self.addAction(actions.format_borders_0)
        self.addAction(actions.format_borders_1)
        self.addAction(actions.format_borders_2)
        self.addAction(actions.format_borders_4)
        self.addAction(actions.format_borders_8)
        self.addAction(actions.format_borders_16)
        self.addAction(actions.format_borders_32)
        self.addAction(actions.format_borders_64)


class GridContextMenu(QMenu):
    """Context menu for grid"""

    def __init__(self, actions: MainWindowActions):
        """
        :param actions: Main window actions

        """

        super().__init__()

        self.addAction(actions.cut)
        self.addAction(actions.copy)
        self.addAction(actions.copy_results)
        self.addAction(actions.paste)
        self.addAction(actions.paste_as)
        self.addSeparator()
        self.addAction(actions.toggle_selection_mode)
        self.addSeparator()
        self.addAction(actions.quote)
        self.addSeparator()
        self.addAction(actions.insert_rows)
        self.addAction(actions.insert_columns)
        self.addAction(actions.insert_table)
        self.addSeparator()
        self.addAction(actions.delete_rows)
        self.addAction(actions.delete_columns)
        self.addAction(actions.delete_table)


class HorizontalHeaderContextMenu(QMenu):
    """Context menu for horizontal grid header"""

    def __init__(self, actions: MainWindowActions):
        """
        :param actions: Main window actions

        """

        super().__init__()

        self.addAction(actions.insert_columns)
        self.addAction(actions.delete_columns)


class VerticalHeaderContextMenu(QMenu):
    """Context menu for vertical grid header"""

    def __init__(self, actions: MainWindowActions):
        """
        :param actions: Main window actions

        """

        super().__init__()

        self.addAction(actions.insert_rows)
        self.addAction(actions.delete_rows)


class TableChoiceContextMenu(QMenu):
    """Context menu for table choice"""

    def __init__(self, actions: MainWindowActions):
        """
        :param actions: Main window actions

        """

        super().__init__()

        self.addAction(actions.insert_table)
        self.addAction(actions.delete_table)


class ToolbarManagerMenu(QMenu):
    """Menu with all actions of a toolbar that allows toggling visibility"""

    def __init__(self, toolbar: QToolBar):
        """
        :param toolbar: Toolbar that the menu is managing

        """

        super().__init__()
        self.toolbar = toolbar

        for action in toolbar.actions():
            if action.isSeparator():
                self.addSeparator()
            else:
                self.addAction(self._get_toggle_action(action))
        self.update_checked_states()

    def _get_toggle_action(self, action: QAction) -> QAction:
        """Returns a toggle action for a toolbar action

        :param action: Toolbar action for which the toggle state is returned

        """

        taction = QAction(action.icon(), action.text(), action, checkable=True)
        taction.triggered.connect(partial(self.on_toggled, action))

        return taction

    def update_checked_states(self):
        """Updates checked states"""

        for tool_action, action in zip(self.toolbar.actions(), self.actions()):
            action.setChecked(tool_action.isVisible())

    def on_toggled(self, action: QAction, toggled: bool):
        """Action toggle event handler

        :param action: Toolbar action for which visibility is toggled
        :param toggled: If False then action is set invisible and vice versa

        """

        action.setVisible(toggled)
