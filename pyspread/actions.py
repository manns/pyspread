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

 * :class:`Action` is a quick one liner way to create `QAction`
 * :class:`MainWindowActions`
 * :class:`ChartDialogActions`

"""

from typing import Callable, List

from PyQt5.QtWidgets import QAction, QActionGroup, QWidget
from PyQt5.QtGui import QKeySequence, QIcon

try:
    import matplotlib.figure as matplotlib_figure
except ImportError:
    matplotlib_figure = None

try:
    from pyspread.icons import Icon
    from pyspread.lib.attrdict import AttrDict
    from pyspread.lib.dependencies import get_enchant_version
except ImportError:
    from icons import Icon
    from lib.attrdict import AttrDict
    from lib.dependencies import get_enchant_version


class Action(QAction):
    """A convenience class for creating a `QAction`

    .. Note: Parameter order has changed comparing with QAction

    """

    def __init__(self, parent: QWidget, label: str, *callbacks: List[Callable],
                 icon: QIcon = None, shortcut: str = None,
                 statustip: str = None, checkable: bool = False):
        """

        :param parent: The parent object, normally :class:`pyspread.MainWindow`
        :param label: The text to appear
        :param callbacks: the callback functions
        :param icon: the :class:`icons.Icon`
        :param shortcut: The magic kestrokes if ant
        :param statustip: The popup message
        :param checkable: Has a checkbox

        """
        if icon is None:
            super().__init__(label, parent, checkable=checkable)
        else:
            super().__init__(icon, label, parent, checkable=checkable)

        if shortcut is not None:
            self.setShortcut(shortcut)

        if statustip is not None:
            self.setStatusTip(statustip)

        for connect in callbacks:
            self.triggered.connect(connect)


class MainWindowActions(AttrDict):
    """Holds all QActions for the main window"""

    def __init__(self, parent: QWidget):
        """
        :param parent: The parent object, normally :class:`pyspread.MainWindow`

        """

        super().__init__()
        self.parent = parent

        self.create_file_actions()
        self.create_edit_actions()
        self.create_view_actions()
        self.create_format_actions()
        self.create_macro_actions()
        self.create_help_actions()

        self.disable_unavailable()

    def create_file_actions(self):
        """actions for File menu"""

        self.new = Action(self.parent, "&New",
                          self.parent.workflows.file_new,
                          icon=Icon.new,
                          shortcut='Ctrl+n',
                          statustip='Create a new, empty spreadsheet')

        self.open = Action(self.parent, "&Open",
                           self.parent.workflows.file_open,
                           icon=Icon.open,
                           statustip='Open spreadsheet from file')

        self.save = Action(self.parent, "&Save",
                           self.parent.workflows.file_save,
                           icon=Icon.save, shortcut='Ctrl+s',
                           statustip='Save spreadsheet')

        self.save_as = Action(self.parent, "Save &As",
                              self.parent.workflows.file_save_as,
                              icon=Icon.save_as, shortcut='Shift+Ctrl+s',
                              statustip='Save spreadsheet to a new file')

        self.imprt = Action(self.parent, "&Import",
                            self.parent.workflows.file_import,
                            icon=Icon.imprt,
                            statustip='Import a file and paste it into the '
                                      'current grid')

        self.export = Action(self.parent, "&Export",
                             self.parent.workflows.file_export,
                             icon=Icon.export,
                             statustip="Export selection to a file")

        self.approve = Action(self.parent, "&Approve file",
                              self.parent.on_approve,
                              icon=Icon.approve,
                              statustip='Approve, unfreeze and sign the '
                                        'current file')

        self.clear_globals = Action(self.parent, "&Clear globals",
                                    self.parent.on_clear_globals,
                                    icon=Icon.clear_globals,
                                    statustip='Deletes global variables '
                                              'and reloads base modules')

        self.print_preview = Action(self.parent, "Print preview",
                                    self.parent.on_preview,
                                    icon=Icon.print_preview,
                                    statustip='Print preview')

        self.print = Action(self.parent, "Print", self.parent.on_print,
                            icon=Icon.print,
                            shortcut='Ctrl+p',
                            statustip='Print current spreadsheet')

        self.preferences = Action(self.parent, "Preferences...",
                                  self.parent.on_preferences,
                                  icon=Icon.preferences,
                                  statustip='Pyspread setup parameters')

        self.quit = Action(self.parent, "&Quit", self.parent.closeEvent,
                           icon=Icon.quit,
                           shortcut='Ctrl+Q',
                           statustip='Exit pyspread')

    def create_edit_actions(self):
        """actions for Edit menu"""

        self.undo = Action(self.parent, "&Undo",
                           self.parent.on_undo,
                           icon=Icon.undo,
                           shortcut='Ctrl+z',
                           statustip='Undo last step')

        self.redo = Action(self.parent, "&Redo",
                           self.parent.on_redo,
                           icon=Icon.redo,
                           shortcut='Shift+Ctrl+z',
                           statustip='Redo last undone step')

        self.cut = Action(self.parent, "Cut",
                          self.parent.workflows.edit_cut,
                          icon=Icon.cut,
                          shortcut='Ctrl+x',
                          statustip='Cut cell to the clipboard')

        self.copy = Action(self.parent, "&Copy",
                           self.parent.workflows.edit_copy,
                           icon=Icon.copy,
                           shortcut='Ctrl+c',
                           statustip='Copy the input strings of the cells '
                                     'to the clipboard')

        self.copy_results = Action(self.parent, "Copy results",
                                   self.parent.workflows.edit_copy_results,
                                   icon=Icon.copy_results,
                                   shortcut='Shift+Ctrl+c',
                                   statustip='Copy the result strings of '
                                             'the cells to the clipboard')

        self.paste = Action(self.parent, "&Paste",
                            self.parent.workflows.edit_paste,
                            icon=Icon.paste,
                            shortcut='Ctrl+v',
                            statustip='Paste cells from the clipboard')

        self.paste_as = Action(self.parent, "Paste as...",
                               self.parent.workflows.edit_paste_as,
                               icon=Icon.paste_as,
                               shortcut='Shift+Ctrl+v',
                               statustip='Transform clipboard and paste '
                                         'results')

        self.find = Action(self.parent, "&Find...",
                           self.parent.workflows.edit_find,
                           icon=Icon.find,
                           shortcut='Ctrl+f',
                           statustip='Find dialog')

        self.find_next = Action(self.parent, "&Find next",
                                self.parent.workflows.edit_find_next,
                                icon=Icon.find_next,
                                shortcut='F3',
                                statustip='Find next matching cell')

        self.replace = Action(self.parent, "&Replace...",
                              self.parent.workflows.edit_replace,
                              icon=Icon.replace,
                              shortcut='Shift+Ctrl+f',
                              statustip='Replace sub-strings in cells')

        self.toggle_selection_mode = Action(
            self.parent, "Selection mode",
            self.parent.grid.set_selection_mode,
            icon=Icon.selection_mode, checkable=True,
            statustip='Enter/leave selection mode')

        self.quote = Action(self.parent, "&Quote",
                            self.parent.grid.on_quote,
                            icon=Icon.quote,
                            shortcut='Ctrl+Return',
                            statustip="Convert cells' code to strings by "
                                      "addding quotes")

        self.insert_rows = Action(self.parent, "Insert rows",
                                  self.parent.grid.on_insert_rows,
                                  icon=Icon.insert_row,
                                  statustip='Insert max(1, no. selected '
                                            'rows) rows at cursor')

        self.insert_columns = Action(self.parent, "Insert columns",
                                     self.parent.grid.on_insert_columns,
                                     icon=Icon.insert_column,
                                     statustip='Insert max(1, no. selected '
                                               'columns) columns at cursor')

        self.insert_table = Action(self.parent, "Insert table",
                                   self.parent.grid.on_insert_table,
                                   icon=Icon.insert_table,
                                   statustip='Insert table before current '
                                             'table')

        self.delete_rows = Action(self.parent, "Delete rows",
                                  self.parent.grid.on_delete_rows,
                                  icon=Icon.delete_row,
                                  statustip='Delete max(1, no. selected '
                                            'rows) rows at cursor')

        self.delete_columns = Action(self.parent, "Delete columns",
                                     self.parent.grid.on_delete_columns,
                                     icon=Icon.delete_column,
                                     statustip='Delete max(1, no. selected '
                                               'columns) columns at cursor')

        self.delete_table = Action(self.parent, "Delete table",
                                   self.parent.grid.on_delete_table,
                                   icon=Icon.delete_table,
                                   statustip='Delete current table')

        self.resize_grid = Action(self.parent, "Resize grid",
                                  self.parent.workflows.edit_resize,
                                  icon=Icon.resize_grid,
                                  statustip='Resizes the current grid')

    def create_view_actions(self):
        """actions for View menu"""

        self.fullscreen = Action(self.parent, "Fullscreen",
                                 self.parent.on_fullscreen,
                                 icon=Icon.fullscreen,
                                 shortcut='F11',
                                 statustip='Show grid in fullscreen mode '
                                           '(press <F11> to leave)')

        self.toggle_main_toolbar = Action(self.parent, "Main toolbar",
                                          self.parent.on_toggle_main_toolbar,
                                          checkable=True,
                                          statustip='Show/hide the main '
                                                    'toolbar')

        self.toggle_macro_toolbar = Action(self.parent, "Macro toolbar",
                                           self.parent.on_toggle_macro_toolbar,
                                           checkable=True,
                                           statustip='Show/hide the macro '
                                                     'toolbar')

        self.toggle_format_toolbar = \
            Action(self.parent, "Format toolbar",
                   self.parent.on_toggle_format_toolbar,
                   checkable=True,
                   statustip='Show/hide the format toolbar')

        self.toggle_find_toolbar = Action(self.parent, "Find toolbar",
                                          self.parent.on_toggle_find_toolbar,
                                          checkable=True,
                                          statustip='Show/hide the find '
                                                    'toolbar')

        self.toggle_entry_line = Action(self.parent, "Entry line",
                                        self.parent.on_toggle_entry_line,
                                        checkable=True,
                                        statustip='Show/hide the entry line')

        self.toggle_macro_panel = Action(self.parent, "Macro panel",
                                         self.parent.on_toggle_macro_panel,
                                         checkable=True, shortcut='F4',
                                         statustip='Show/hide the macro panel')

        self.goto_cell = Action(self.parent, "Go to cell",
                                self.parent.workflows.view_goto_cell,
                                icon=Icon.goto_cell,
                                shortcut='Ctrl+g',
                                statustip='Select a cell and put it into view')

        self.toggle_spell_checker = \
            Action(self.parent, "Toggle spell checker",
                   self.parent.entry_line.on_toggle_spell_check,
                   icon=Icon.check_spelling,
                   checkable=True,
                   statustip='Turn the spell checker in the entry line on/off')

        self.zoom_in = Action(self.parent, "Zoom in",
                              self.parent.grid.on_zoom_in,
                              icon=Icon.zoom_in,
                              shortcut='Ctrl++',
                              statustip='Zoom in the grid')

        self.zoom_out = Action(self.parent, "Zoom out",
                               self.parent.grid.on_zoom_out,
                               icon=Icon.zoom_out,
                               shortcut='Ctrl+-',
                               statustip='Zoom out the grid')

        self.zoom_1 = Action(self.parent, "Original size",
                             self.parent.grid.on_zoom_1,
                             icon=Icon.zoom_1,
                             shortcut='Ctrl+0',
                             statustip='Show grid on standard zoom level')

        self.refresh_cells = \
            Action(self.parent, "Refresh selected cells",
                   self.parent.grid.refresh_selected_frozen_cells,
                   icon=Icon.refresh, shortcut=QKeySequence.Refresh,
                   statustip='Refresh selected cells even when frozen')

        self.toggle_periodic_updates = \
            Action(self.parent, "Toggle periodic updates",
                   self.parent.on_toggle_refresh_timer,
                   icon=Icon.toggle_periodic_updates, checkable=True,
                   statustip='Toggles periodic updates for frozen cells')

        self.show_frozen = Action(self.parent, "Show frozen",
                                  self.parent.grid.on_show_frozen_pressed,
                                  icon=Icon.show_frozen,
                                  checkable=True,
                                  statustip='Indicates frozen cells with a '
                                            'background crosshatch')

    def create_format_actions(self):
        """actions for Format menu"""

        self.copy_format = Action(self.parent, "&Copy format",
                                  self.parent.workflows.format_copy_format,
                                  icon=Icon.copy_format,
                                  statustip='Copy format of selection to '
                                            'the clipboard')

        self.paste_format = \
            Action(self.parent, "&Paste format",
                   self.parent.workflows.format_paste_format,
                   icon=Icon.paste_format,
                   statustip='Apply format from the clipboard to the selected '
                             'cells')

        self.font = Action(self.parent, "&Font...",
                           self.parent.grid. on_font_dialog,
                           icon=Icon.font_dialog,
                           shortcut='Ctrl+n',
                           statustip='Lauch font dialog')

        self.bold = Action(self.parent, "&Bold",
                           self.parent.grid.on_bold_pressed,
                           icon=Icon.bold,
                           shortcut='Ctrl+b',
                           checkable=True,
                           statustip='Toggle bold font weight for the '
                                     'selected cells')

        self.italics = Action(self.parent, "&Italics",
                              self.parent.grid.on_italics_pressed,
                              icon=Icon.italics,
                              shortcut='Ctrl+i',
                              checkable=True,
                              statustip='Toggle italics font style for the '
                                        'selected cells')

        self.underline = Action(self.parent, "&Underline",
                                self.parent.grid.on_underline_pressed,
                                icon=Icon.underline,
                                shortcut='Ctrl+u',
                                checkable=True,
                                statustip='Toggle underline for the '
                                          'selected cells')

        self.strikethrough = Action(self.parent, "&Strikethrough",
                                    self.parent.grid.on_strikethrough_pressed,
                                    icon=Icon.strikethrough,
                                    checkable=True,
                                    statustip='Toggle strikethrough for the '
                                              'selected cells')

        self.text = Action(self.parent, "Text renderer",
                           self.parent.grid.on_text_renderer_pressed,
                           icon=Icon.text,
                           checkable=True,
                           statustip='Show cell results as text (default). '
                                     'Formats affect the whole cell')

        self.markup = Action(self.parent, "Markup renderer",
                             self.parent.grid.on_markup_renderer_pressed,
                             icon=Icon.markup,
                             checkable=True,
                             statustip='Show cell results as markup, which '
                                       'allows partly formatted output')

        self.image = Action(self.parent, "Image renderer",
                            self.parent.grid.on_image_renderer_pressed,
                            icon=Icon.image,
                            checkable=True,
                            statustip='Show cell results as image. A numpy '
                                      'array of shape (x, y, 3) '
                                      'is expected')
        if matplotlib_figure is not None:
            self.matplotlib = \
                Action(self.parent, "Matplotlib chart renderer",
                       self.parent.grid.on_matplotlib_renderer_pressed,
                       icon=Icon.matplotlib,
                       checkable=True,
                       statustip='Show cell results as matplotlib chart. A '
                                 'numpy array of shape (x, y, 3) is expected')

        renderer_group = QActionGroup(self.parent)
        renderer_group.addAction(self.text)
        renderer_group.addAction(self.markup)
        renderer_group.addAction(self.image)
        if matplotlib_figure is not None:
            renderer_group.addAction(self.matplotlib)

        self.text_color = Action(
            self.parent, "Text color...",
            self.parent.widgets.text_color_button.on_pressed,
            icon=Icon.text_color, statustip='Lauch text color dialog')

        self.line_color = Action(
            self.parent, "Line color...",
            self.parent.widgets.line_color_button.on_pressed,
            icon=Icon.line_color, statustip='Lauch line color dialog')

        self.background_color = Action(
            self.parent, "Background color...",
            self.parent.widgets.background_color_button.on_pressed,
            icon=Icon.background_color,
            statustip='Lauch background color dialog')

        self.freeze_cell = Action(self.parent, "Freeze cell",
                                  self.parent.grid.on_freeze_pressed,
                                  icon=Icon.freeze,
                                  checkable=True,
                                  statustip='Freeze the selected cell so that '
                                            'is is only updated when <F5> is '
                                            'pressed')

        self.lock_cell = Action(self.parent, "Lock cell",
                                self.parent.grid.on_lock_pressed,
                                icon=Icon.lock,
                                checkable=True,
                                statustip='Lock cell so that its code '
                                          'cannot be changed')

        self.button_cell = Action(self.parent, "Button cell",
                                  self.parent.grid.on_button_cell_pressed,
                                  icon=Icon.button,
                                  checkable=True,
                                  statustip='Make cell a button cell that is '
                                            'executed only when pressed')

        self.merge_cells = Action(self.parent, "Merge cells",
                                  self.parent.grid.on_merge_pressed,
                                  icon=Icon.merge_cells,
                                  checkable=True,
                                  statustip='Merge/unmerge selected cells')

        self.rotate_0 = Action(self.parent, "0°",
                               self.parent.grid.on_rotate_0,
                               icon=Icon.rotate_0,
                               checkable=True,
                               statustip='Set text rotation to 0°')

        self.rotate_90 = Action(self.parent, "90°",
                                self.parent.grid.on_rotate_90,
                                icon=Icon.rotate_90,
                                checkable=True,
                                statustip='Set text rotation to 90°')

        self.rotate_180 = Action(self.parent, "180°",
                                 self.parent.grid.on_rotate_180,
                                 icon=Icon.rotate_180,
                                 checkable=True,
                                 statustip='Set text rotation to 180°')

        self.rotate_270 = Action(self.parent, "270°",
                                 self.parent.grid.on_rotate_270,
                                 icon=Icon.rotate_270,
                                 checkable=True,
                                 statustip='Set text rotation to 270°')

        rotate_group = QActionGroup(self.parent)
        rotate_group.addAction(self.rotate_0)
        rotate_group.addAction(self.rotate_90)
        rotate_group.addAction(self.rotate_180)
        rotate_group.addAction(self.rotate_270)

        self.justify_left = Action(self.parent, "Left",
                                   self.parent.grid.on_justify_left,
                                   icon=Icon.justify_left,
                                   checkable=True,
                                   statustip='Display cell result text '
                                             'left justified')

        self.justify_center = Action(self.parent, "Center",
                                     self.parent.grid.on_justify_center,
                                     checkable=True,
                                     icon=Icon.justify_center,
                                     statustip='Display cell result text '
                                               'centered')

        self.justify_right = Action(self.parent, "Right",
                                    self.parent.grid.on_justify_right,
                                    checkable=True,
                                    icon=Icon.justify_right,
                                    statustip='Display cell result text '
                                              'right justified')

        self.justify_fill = Action(self.parent, "Fill",
                                   self.parent.grid.on_justify_fill,
                                   icon=Icon.justify_fill,
                                   checkable=True,
                                   statustip='Display cell result text '
                                             'filled into the cell')

        justify_group = QActionGroup(self.parent)
        justify_group.addAction(self.justify_left)
        justify_group.addAction(self.justify_center)
        justify_group.addAction(self.justify_right)
        justify_group.addAction(self.justify_fill)

        self.align_top = Action(self.parent, "Top",
                                self.parent.grid.on_align_top,
                                icon=Icon.align_top,
                                checkable=True,
                                statustip='Align cell result at the top of '
                                          'the cell')

        self.align_center = Action(self.parent, "Center",
                                   self.parent.grid.on_align_middle,
                                   icon=Icon.align_center,
                                   checkable=True,
                                   statustip='Center cell result within '
                                             'the cell')

        self.align_bottom = Action(self.parent, "Bottom",
                                   self.parent.grid.on_align_bottom,
                                   icon=Icon.align_bottom,
                                   checkable=True,
                                   statustip='Align cell result at the '
                                             'bottom of the cell')

        align_group = QActionGroup(self.parent)
        align_group.addAction(self.align_top)
        align_group.addAction(self.align_center)
        align_group.addAction(self.align_bottom)

        self.format_borders_all = \
            Action(self.parent, "All borders",
                   self.parent.grid.on_border_choice,
                   icon=Icon.format_borders_all, checkable=True,
                   statustip='Format all borders of selection')

        self.format_borders_top = \
            Action(self.parent, "Top border",
                   self.parent.grid.on_border_choice,
                   icon=Icon.format_borders_top, checkable=True,
                   statustip='Format top border of selection')

        self.format_borders_bottom = \
            Action(self.parent, "Bottom border",
                   self.parent.grid.on_border_choice,
                   icon=Icon.format_borders_bottom, checkable=True,
                   statustip='Format bottom border of selection')

        self.format_borders_left = \
            Action(self.parent, "Left border",
                   self.parent.grid.on_border_choice,
                   icon=Icon.format_borders_left, checkable=True,
                   statustip='Format left border of selection')

        self.format_borders_right = \
            Action(self.parent, "Right border",
                   self.parent.grid.on_border_choice,
                   icon=Icon.format_borders_right, checkable=True,
                   statustip='Format right border of selection')

        self.format_borders_outer = \
            Action(self.parent, "Outer borders",
                   self.parent.grid.on_border_choice,
                   icon=Icon.format_borders_outer, checkable=True,
                   statustip='Format outer borders of selection')

        self.format_borders_inner = \
            Action(self.parent, "Inner borders",
                   self.parent.grid.on_border_choice,
                   icon=Icon.format_borders_inner, checkable=True,
                   statustip='Format inner borders of selection')

        self.format_borders_top_bottom = \
            Action(self.parent, "Top and bottom borders",
                   self.parent.grid.on_border_choice,
                   icon=Icon.format_borders_top_bottom, checkable=True,
                   statustip='Format top and bottom borders of selection')

        self.border_group = QActionGroup(self.parent)
        self.border_group.addAction(self.format_borders_all)
        self.border_group.addAction(self.format_borders_top)
        self.border_group.addAction(self.format_borders_bottom)
        self.border_group.addAction(self.format_borders_left)
        self.border_group.addAction(self.format_borders_right)
        self.border_group.addAction(self.format_borders_outer)
        self.border_group.addAction(self.format_borders_inner)
        self.border_group.addAction(self.format_borders_top_bottom)
        self.format_borders_all.setChecked(True)

        self.format_borders_0 = Action(self.parent, "Border width 0",
                                       self.parent.grid.on_borderwidth,
                                       icon=Icon.format_borders_0,
                                       statustip='Set border width to 0')

        self.format_borders_1 = Action(self.parent, "Border width 1",
                                       self.parent.grid.on_borderwidth,
                                       icon=Icon.format_borders_1,
                                       statustip='Set border width to 1')

        self.format_borders_2 = Action(self.parent, "Border width 2",
                                       self.parent.grid.on_borderwidth,
                                       icon=Icon.format_borders_2,
                                       statustip='Set border width to 2')

        self.format_borders_4 = Action(self.parent, "Border width 3",
                                       self.parent.grid.on_borderwidth,
                                       icon=Icon.format_borders_4,
                                       statustip='Set border width to 3')

        self.format_borders_8 = Action(self.parent, "Border width 4",
                                       self.parent.grid.on_borderwidth,
                                       icon=Icon.format_borders_8,
                                       statustip='Set border width to 4')

        self.format_borders_16 = Action(self.parent, "Border width 6",
                                        self.parent.grid.on_borderwidth,
                                        icon=Icon.format_borders_16,
                                        statustip='Set border width to 6')

        self.format_borders_32 = Action(self.parent, "Border width 8",
                                        self.parent.grid.on_borderwidth,
                                        icon=Icon.format_borders_32,
                                        statustip='Set border width to 8')

        self.format_borders_64 = Action(self.parent, "Border width 12",
                                        self.parent.grid.on_borderwidth,
                                        icon=Icon.format_borders_64,
                                        statustip='Set border width to 12')

        self.border_width_group = QActionGroup(self.parent)
        self.border_width_group.addAction(self.format_borders_0)
        self.border_width_group.addAction(self.format_borders_1)
        self.border_width_group.addAction(self.format_borders_2)
        self.border_width_group.addAction(self.format_borders_4)
        self.border_width_group.addAction(self.format_borders_8)
        self.border_width_group.addAction(self.format_borders_16)
        self.border_width_group.addAction(self.format_borders_32)
        self.border_width_group.addAction(self.format_borders_64)
        self.format_borders_1.setChecked(True)

    def create_macro_actions(self):
        """Create actions for Macro menu"""

        self.insert_image = Action(self.parent, "Insert image...",
                                   self.parent.workflows.macro_insert_image,
                                   icon=Icon.insert_image,
                                   statustip='Load an image from a file '
                                             'into a cell')

        self.insert_chart = Action(self.parent, "Insert chart...",
                                   self.parent.workflows.macro_insert_chart,
                                   icon=Icon.insert_chart,
                                   statustip='Create and display matplotlib '
                                             'chart')

    def create_help_actions(self):
        """actions for Help menu"""

        self.manual = Action(self.parent, "Manual...",
                             self.parent.on_manual,
                             icon=Icon.help,
                             shortcut='F1',
                             statustip='Display the pyspread manual')

        self.tutorial = Action(self.parent, "Tutorial...",
                               self.parent.on_tutorial,
                               icon=Icon.tutorial,
                               statustip='Display a pyspread tutorial')

        self.dependencies = Action(self.parent, "Dependencies...",
                                   self.parent.on_dependencies,
                                   icon=Icon.dependencies,
                                   statustip='List and install dependencies')

        self.about = Action(self.parent, "About pyspread...",
                            self.parent.on_about,
                            icon=Icon.pyspread,
                            statustip='About pyspread')

    def disable_unavailable(self):
        """Disables unavailable menu items e.g. due to missing dependencies"""

        if get_enchant_version() is None:
            self.toggle_spell_checker.setEnabled(False)


class ChartDialogActions(AttrDict):
    """QActions for chart dialog

    Reads out template files in share/templates/matplotlib and
    adds a QAction for each template.

    """

    def __init__(self, parent: QWidget):
        """
        :param parent: The parent object

        """

        super().__init__()
        self.parent = parent
        self._add_chart_template_actions()

    def _add_chart_template_actions(self):
        """Adds actions for chart dialog toolbar"""

        self.chart_pie_1_1 = Action(self.parent, "Pie chart",
                                    self.parent.on_template,
                                    icon=Icon.chart_pie_1_1,
                                    statustip='Insert code for pie chart')
        self.chart_pie_1_1.setData("chart_pie_1_1.py")

        self.chart_ring_1_1 = Action(self.parent, "Ring chart",
                                     self.parent.on_template,
                                     icon=Icon.chart_ring_1_1,
                                     statustip='Insert code for ring chart')
        self.chart_ring_1_1.setData("chart_ring_1_1.py")

        self.chart_line_1_1 = Action(self.parent, "Line chart",
                                     self.parent.on_template,
                                     icon=Icon.chart_line_1_1,
                                     statustip='Insert code for line chart')
        self.chart_line_1_1.setData("chart_line_1_1.py")

        self.chart_polar_1_1 = Action(self.parent, "Polar chart",
                                      self.parent.on_template,
                                      icon=Icon.chart_polar_1_1,
                                      statustip='Insert code for polar '
                                      'coordinates line chart')
        self.chart_polar_1_1.setData("chart_polar_1_1.py")

        self.chart_area_1_1 = Action(self.parent, "Area chart",
                                     self.parent.on_template,
                                     icon=Icon.chart_area_1_1,
                                     statustip='Insert code for area chart')
        self.chart_area_1_1.setData("chart_area_1_1.py")

        self.chart_column_1_1 = Action(self.parent, "Grouped column chart",
                                       self.parent.on_template,
                                       icon=Icon.chart_column_1_1,
                                       statustip='Insert code for grouped '
                                                 'column chart')
        self.chart_column_1_1.setData("chart_column_1_1.py")

        self.chart_column_1_2 = Action(self.parent, "Stacked column chart",
                                       self.parent.on_template,
                                       icon=Icon.chart_column_1_2,
                                       statustip='Insert code for stacked '
                                                 'column chart')
        self.chart_column_1_2.setData("chart_column_1_2.py")

        self.chart_bar_1_3 = \
            Action(self.parent, "Normalized stacked bar chart",
                   self.parent.on_template, icon=Icon.chart_bar_1_3,
                   statustip='Insert code for normalized stacked bar chart')
        self.chart_bar_1_3.setData("chart_bar_1_3.py")

        self.chart_scatter_1_1 = Action(self.parent, "Scatter chart",
                                        self.parent.on_template,
                                        icon=Icon.chart_scatter_1_1,
                                        statustip='Insert code for a scatter '
                                                  'plot')
        self.chart_scatter_1_1.setData("chart_scatter_1_1.py")

        self.chart_bubble_1_1 = Action(self.parent, "Bubble chart",
                                       self.parent.on_template,
                                       icon=Icon.chart_bubble_1_1,
                                       statustip='Insert code for a bubble '
                                       'plot that is a scatter plot with '
                                       'individual point sizes')
        self.chart_bubble_1_1.setData("chart_bubble_1_1.py")

        self.chart_boxplot_2_2 = Action(self.parent, "Boxplot chart",
                                        self.parent.on_template,
                                        icon=Icon.chart_boxplot_2_2,
                                        statustip='Insert code for boxplot '
                                        'chart')
        self.chart_boxplot_2_2.setData("chart_boxplot_2_2.py")

        self.chart_histogram_1_1 = Action(self.parent, "Histogram chart",
                                          self.parent.on_template,
                                          icon=Icon.chart_histogram_1_1,
                                          statustip='Insert code for '
                                                    'histogram')
        self.chart_histogram_1_1.setData("chart_histogram_1_1.py")

        self.chart_histogram_1_4 = Action(self.parent,
                                          "Multiple histogram charts",
                                          self.parent.on_template,
                                          icon=Icon.chart_histogram_1_4,
                                          statustip='Insert code for multiple '
                                                    'histogram charts')
        self.chart_histogram_1_4.setData("chart_histogram_1_4.py")

        self.chart_scatterhist_1_1 = Action(self.parent,
                                            "Scatter and histogram chart",
                                            self.parent.on_template,
                                            icon=Icon.chart_scatterhist_1_1,
                                            statustip='Insert code for scatter'
                                                      ' plot with histogram'
                                                      ' for each axis')
        self.chart_scatterhist_1_1.setData("chart_scatterhist_1_1.py")

        self.chart_matrix_1_1 = Action(self.parent, "Matrix chart",
                                       self.parent.on_template,
                                       icon=Icon.chart_matrix_1_1,
                                       statustip='Insert code for matrix '
                                                 'chart')
        self.chart_matrix_1_1.setData("chart_matrix_1_1.py")

        self.chart_contour_1_2 = Action(self.parent, "Contour chart",
                                        self.parent.on_template,
                                        icon=Icon.chart_contour_1_2,
                                        statustip='Insert code for contour '
                                                  'chart')
        self.chart_contour_1_2.setData("chart_contour_1_2.py")

        self.chart_surface_2_1 = Action(self.parent, "Surface chart",
                                        self.parent.on_template,
                                        icon=Icon.chart_surface_2_1,
                                        statustip='Insert code for surface '
                                                  'chart')
        self.chart_surface_2_1.setData("chart_surface_2_1.py")
