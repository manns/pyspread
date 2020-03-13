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

* :class:`Grid`: QTableView of the main grid
* :class:`GridTableModel`: QAbstractTableModel linking the view to code_array
  backend
* :class:`GridCellNavigator`: Find neighbors of a cell
* :class:`GridCellDelegate`: QStyledItemDelegate handling custom painting and
  editors
* :class:`TableChoice`: The TabBar below the main grid

"""

from ast import literal_eval
from contextlib import contextmanager
from io import BytesIO
from math import isclose

import numpy

from PyQt5.QtWidgets \
    import (QTableView, QStyledItemDelegate, QTabBar, QWidget,
            QStyleOptionViewItem, QApplication, QStyle, QAbstractItemDelegate,
            QHeaderView, QFontDialog, QInputDialog, QLineEdit)
from PyQt5.QtGui \
    import (QColor, QBrush, QPen, QFont, QPainter, QPalette, QImage,
            QTextOption, QAbstractTextDocumentLayout, QTextDocument)
from PyQt5.QtCore \
    import (Qt, QAbstractTableModel, QModelIndex, QVariant, QEvent, QPointF,
            QRectF, QLineF, QSize, QRect, QItemSelectionModel)

try:
    import matplotlib
    import matplotlib.figure
except ImportError:
    matplotlib = None

import commands
from model.model import CodeArray
from lib.selection import Selection
from lib.string_helpers import quote, wrap_text, get_svg_size
from lib.qimage2ndarray import array2qimage
from lib.qimage_svg import QImageSvg
from lib.typechecks import is_svg
from menus \
    import (GridContextMenu, TableChoiceContextMenu,
            HorizontalHeaderContextMenu, VerticalHeaderContextMenu)
from widgets import CellButton


class Grid(QTableView):
    """The main grid of pyspread"""

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window

        dimensions = main_window.settings.shape

        self.model = GridTableModel(main_window, dimensions)
        self.setModel(self.model)

        self.table_choice = TableChoice(self, dimensions[2])

        self.widget_indices = []  # Store each index with an indexWidget here

        # Signals
        self.model.dataChanged.connect(self.on_data_changed)
        self.selectionModel().currentChanged.connect(self.on_current_changed)

        self.main_window.widgets.text_color_button.colorChanged.connect(
                self.on_text_color)
        self.main_window.widgets.background_color_button.colorChanged.connect(
                self.on_background_color)
        self.main_window.widgets.line_color_button.colorChanged.connect(
                self.on_line_color)
        self.main_window.widgets.font_combo.fontChanged.connect(self.on_font)
        self.main_window.widgets.font_size_combo.fontSizeChanged.connect(
                self.on_font_size)

        self.setHorizontalHeader(GridHeaderView(Qt.Horizontal, self))
        self.setVerticalHeader(GridHeaderView(Qt.Vertical, self))

        self.setCornerButtonEnabled(False)

        self._zoom = 1.0  # Initial zoom level for the grid

        self.verticalHeader().sectionResized.connect(self.on_row_resized)
        self.horizontalHeader().sectionResized.connect(self.on_column_resized)

        self.setShowGrid(False)

        self.delegate = GridCellDelegate(main_window, self.model.code_array)
        self.setItemDelegate(self.delegate)

        # Select upper left cell because initial selection behaves strange
        self.reset_selection()

        # Locking states for operations by undo and redo operations
        self.__undo_resizing_row = False
        self.__undo_resizing_column = False

        # Initially, select top left cell on table 0
        self.current = 0, 0, 0

    @contextmanager
    def undo_resizing_row(self):
        self.__undo_resizing_row = True
        yield
        self.__undo_resizing_row = False

    @contextmanager
    def undo_resizing_column(self):
        self.__undo_resizing_column = True
        yield
        self.__undo_resizing_column = False

    @property
    def row(self):
        """Current row"""

        return self.currentIndex().row()

    @row.setter
    def row(self, value):
        """Sets current row to value"""

        self.current = value, self.column

    @property
    def column(self):
        """Current column"""

        return self.currentIndex().column()

    @column.setter
    def column(self, value):
        """Sets current column to value"""

        self.current = self.row, value

    @property
    def table(self):
        """Current table"""

        return self.table_choice.table

    @table.setter
    def table(self, value):
        """Sets current table"""

        self.table_choice.table = value

    @property
    def current(self):
        """Tuple of row, column, table of the current index"""

        return self.row, self.column, self.table

    @current.setter
    def current(self, value):
        """Sets the current index to row, column and if given table"""

        if len(value) == 2:
            row, column = value

        elif len(value) == 3:
            row, column, self.table = value

        else:
            msg = "Current cell must be defined with a tuple " + \
                  "(row, column) or (rol, column, table)."
            raise ValueError(msg)

        index = self.model.index(row, column, QModelIndex())
        self.setCurrentIndex(index)

    @property
    def row_heights(self):
        """Returns list of tuples (row_index, row height) for current table"""

        row_heights = self.model.code_array.row_heights
        return [(row, row_heights[row, tab]) for row, tab in row_heights
                if tab == self.table]

    @property
    def column_widths(self):
        """Returns list of tuples (col_index, col_width) for current table"""

        col_widths = self.model.code_array.col_widths
        return [(col, col_widths[col, tab]) for col, tab in col_widths
                if tab == self.table]

    @property
    def selection(self):
        """Pyspread selection based on self's QSelectionModel"""

        selection = self.selectionModel().selection()

        block_top_left = []
        block_bottom_right = []
        cells = []

        # Selection are made of selection ranges that we call span

        for span in selection:
            top, bottom = span.top(), span.bottom()
            left, right = span.left(), span.right()

            # If the span is a single cell then append it
            if top == bottom and left == right:
                cells.append((top, right))
            else:
                # Otherwise append a block
                block_top_left.append((top, left))
                block_bottom_right.append((bottom, right))

        return Selection(block_top_left, block_bottom_right, [], [], cells)

    @property
    def selected_idx(self):
        """Currently selected indices"""

        return self.selectionModel().selectedIndexes()

    @property
    def zoom(self):
        """Returns zoom level"""

        return self._zoom

    @zoom.setter
    def zoom(self, zoom):
        """Updates _zoom property and zoom visualization of the grid"""

        self._zoom = zoom
        self.update_zoom()

    # Overrides

    def closeEditor(self, editor, hint):
        """Overrides QTableView.closeEditor

        Changes to overridden behavior:
         * Data is submitted when a cell is changed without pressing <Enter>
           e.g. by mouse click or arrow keys.

        """

        if hint == QAbstractItemDelegate.NoHint:
            hint = QAbstractItemDelegate.SubmitModelCache

        super().closeEditor(editor, hint)

    def keyPressEvent(self, event):
        """Overrides QTableView.keyPressEvent

        Changes to overridden behavior:
         * If Shift is pressed, the cell in the next column is selected.
         * If Shift is not pressed, the cell in the next row is selected.

        """

        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            if event.modifiers() & Qt.ShiftModifier:
                self.current = self.row, self.column + 1
            else:
                self.current = self.row + 1, self.column
        elif event.key() == Qt.Key_Delete:
            self.main_window.workflows.delete()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        """Overrides mouse wheel event handler"""

        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.on_zoom_in()
            else:
                self.on_zoom_out()
        else:
            super().wheelEvent(event)

    def contextMenuEvent(self, event):
        """Overrides contextMenuEvent to install GridContextMenu"""

        menu = GridContextMenu(self.main_window.main_window_actions)
        menu.exec_(self.mapToGlobal(event.pos()))

    # Helpers

    def reset_selection(self):
        """Select upper left cell"""

        self.setSelection(QRect(1, 1, 1, 1), QItemSelectionModel.Select)

    def gui_update(self):
        """Emits gui update signal"""

        attributes = self.model.code_array.cell_attributes[self.current]
        self.main_window.gui_update.emit(attributes)

    def adjust_size(self):
        """Adjusts size to header maxima"""

        w = self.horizontalHeader().length() + self.verticalHeader().width()
        h = self.verticalHeader().length() + self.horizontalHeader().height()
        self.resize(w, h)

    def _selected_idx_to_str(self, selected_idx):
        """Converts selected_idx to string with cell indices"""

        return ", ".join(str(self.model.current(idx)) for idx in selected_idx)

    def update_zoom(self):
        """Updates the zoom level visualization to the current zoom factor"""

        self.verticalHeader().update_zoom()
        self.horizontalHeader().update_zoom()

    def has_selection(self):
        """Returns True if more than one cell is selected, else False

        This method handles spanned/merged cells. One single cell that is
        selected is considered as no cell being selected.

        """

        cell_attributes = self.model.code_array.cell_attributes
        merge_area = cell_attributes[self.current]["merge_area"]

        if merge_area is None:
            merge_sel = Selection([], [], [], [], [])
        else:
            top, left, bottom, right = merge_area
            merge_sel = Selection([(top, left)], [(bottom, right)], [], [], [])

        return not(self.selection.single_cell_selected()
                   or merge_sel.get_bbox() == self.selection.get_bbox())

    # Event handlers

    def on_data_changed(self):
        """Event handler for data changes"""

        code = self.model.code_array(self.current)

        self.main_window.entry_line.setPlainText(code)

        if not self.main_window.settings.changed_since_save:
            self.main_window.settings.changed_since_save = True
            main_window_title = "* " + self.main_window.windowTitle()
            self.main_window.setWindowTitle(main_window_title)

    def on_current_changed(self, current, previous):
        """Event handler for change of current cell"""

        code = self.model.code_array(self.current)
        self.main_window.entry_line.setPlainText(code)
        self.gui_update()

    def on_row_resized(self, row, old_height, new_height):
        """Row resized event handler"""

        if self.__undo_resizing_row:  # Resize from undo or redo command
            return

        (top, _), (bottom, _) = self.selection.get_grid_bbox(self.model.shape)
        if bottom - top > 1 and top <= row <= bottom:
            rows = list(range(top, bottom + 1))
        else:
            rows = [row]

        description = "Resize rows {} to {}".format(rows, new_height)
        command = commands.SetRowsHeight(self, rows, self.table, old_height,
                                         new_height, description)
        self.main_window.undo_stack.push(command)

    def on_column_resized(self, column, old_width, new_width):
        """Column resized event handler"""

        if self.__undo_resizing_column:  # Resize from undo or redo command
            return

        (_, left), (_, right) = self.selection.get_grid_bbox(self.model.shape)
        if right - left > 1 and left <= column <= right:
            columns = list(range(left, right + 1))
        else:
            columns = [column]

        description = "Resize columns {} to {}".format(columns, new_width)
        command = commands.SetColumnsWidth(self, columns, self.table,
                                           old_width, new_width, description)
        self.main_window.undo_stack.push(command)

    def on_zoom_in(self):
        """Zoom in event handler"""

        zoom_levels = self.main_window.settings.zoom_levels
        larger_zoom_levels = [zl for zl in zoom_levels if zl > self.zoom]
        if larger_zoom_levels:
            self.zoom = min(larger_zoom_levels)

    def on_zoom_out(self):
        """Zoom out event handler"""

        zoom_levels = self.main_window.settings.zoom_levels
        smaller_zoom_levels = [zl for zl in zoom_levels if zl < self.zoom]
        if smaller_zoom_levels:
            self.zoom = max(smaller_zoom_levels)

    def on_zoom_1(self):
        """Sets zoom level ot 1.0"""

        self.zoom = 1.0

    def _refresh_frozen_cell(self, key):
        """Refreshes the frozen cell key

        Does neither emit dataChanged nor clear _attr_cache or _table_cache.

        :key: 3-tuple of int: row, column, table

        """

        if self.model.code_array.cell_attributes[key]["frozen"]:
            code = self.model.code_array(key)
            result = self.model.code_array._eval_cell(key, code)
            self.model.code_array.frozen_cache[repr(key)] = result

    def refresh_frozen_cells(self):
        """Refreshes all frozen cells"""

        frozen_cache = self.model.code_array.frozen_cache
        cell_attributes = self.model.code_array.cell_attributes

        for repr_key in frozen_cache:
            key = literal_eval(repr_key)
            self._refresh_frozen_cell(key)

        cell_attributes._attr_cache.clear()
        cell_attributes._table_cache.clear()
        self.model.code_array.result_cache.clear()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def refresh_selected_frozen_cells(self):
        """Refreshes selected frozen cells"""

        for idx in self.selected_idx:
            self._refresh_frozen_cell((idx.row(), idx.column(), self.table))

        self.model.code_array.cell_attributes._attr_cache.clear()
        self.model.code_array.cell_attributes._table_cache.clear()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def on_show_frozen_pressed(self, toggled):
        """Show frozen cells event handler"""

        self.main_window.settings.show_frozen = toggled

    def on_font_dialog(self):
        """Font dialog event handler"""

        # Determine currently active font as dialog preset
        font = self.model.font(self.current)
        font, ok = QFontDialog().getFont(font, self.main_window)
        if ok:
            attr_dict = {}
            attr_dict["textfont"] = font.family()
            attr_dict["pointsize"] = font.pointSizeF()
            attr_dict["fontweight"] = font.weight()
            attr_dict["fontstyle"] = font.style()
            attr_dict["underline"] = font.underline()
            attr_dict["strikethrough"] = font.strikeOut()
            attr = self.selection, self.table, attr_dict
            idx_string = self._selected_idx_to_str(self.selected_idx)
            description = "Set font {} for indices {}".format(font, idx_string)
            command = commands.SetCellFormat(attr, self.model,
                                             self.currentIndex(),
                                             self.selected_idx, description)
            self.main_window.undo_stack.push(command)

    def on_font(self):
        """Font change event handler"""

        font = self.main_window.widgets.font_combo.font
        attr = self.selection, self.table, {"textfont": font}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set font {} for indices {}".format(font, idx_string)
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_font_size(self):
        """Font size change event handler"""

        size = self.main_window.widgets.font_size_combo.size
        attr = self.selection, self.table, {"pointsize": size}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set font size {} for cells {}".format(size, idx_string)
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_bold_pressed(self, toggled):
        """Bold button pressed event handler"""

        fontweight = QFont.Bold if toggled else QFont.Normal
        attr = self.selection, self.table, {"fontweight": fontweight}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set font weight {} for cells {}".format(fontweight,
                                                               idx_string)
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_italics_pressed(self, toggled):
        """Italics button pressed event handler"""

        fontstyle = QFont.StyleItalic if toggled else QFont.StyleNormal
        attr = self.selection, self.table, {"fontstyle": fontstyle}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set font style {} for cells {}".format(fontstyle,
                                                              idx_string)
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_underline_pressed(self, toggled):
        """Underline button pressed event handler"""

        attr = self.selection, self.table, {"underline": toggled}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set font underline {} for cells {}".format(toggled,
                                                                  idx_string)
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_strikethrough_pressed(self, toggled):
        """Strikethrough button pressed event handler"""

        attr = self.selection, self.table, {"strikethrough": toggled}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description_tpl = "Set font strikethrough {} for cells {}"
        description = description_tpl.format(toggled, idx_string)
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_text_renderer_pressed(self, toggled):
        """Text renderer button pressed event handler"""

        attr = self.selection, self.table, {"renderer": "text"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set text renderer for cells {}".format(idx_string)
        entry_line = self.main_window.entry_line
        document = entry_line.document()

        # Disable highlighter to speed things up
        highlighter_limit = self.main_window.settings.highlighter_limit
        if len(document.toRawText()) > highlighter_limit:
            document = None

        command = commands.SetCellRenderer(attr, self.model, entry_line,
                                           document, self.currentIndex(),
                                           self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_image_renderer_pressed(self, toggled):
        """Image renderer button pressed event handler"""

        attr = self.selection, self.table, {"renderer": "image"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set image renderer for cells {}".format(idx_string)
        entry_line = self.main_window.entry_line
        command = commands.SetCellRenderer(attr, self.model, entry_line, None,
                                           self.currentIndex(),
                                           self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_markup_renderer_pressed(self, toggled):
        """Markup renderer button pressed event handler"""

        attr = self.selection, self.table, {"renderer": "markup"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set markup renderer for cells {}".format(idx_string)
        entry_line = self.main_window.entry_line
        document = entry_line.document()

        # Disable highlighter to speed things up
        highlighter_limit = self.main_window.settings.highlighter_limit
        if len(document.toRawText()) > highlighter_limit:
            document = None

        command = commands.SetCellRenderer(attr, self.model, entry_line,
                                           document, self.currentIndex(),
                                           self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_matplotlib_renderer_pressed(self, toggled):
        """Matplotlib renderer button pressed event handler"""

        attr = self.selection, self.table, {"renderer": "matplotlib"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set matplotlib renderer for cells {}".format(idx_string)
        entry_line = self.main_window.entry_line
        document = entry_line.document()

        # Disable highlighter to speed things up
        highlighter_limit = self.main_window.settings.highlighter_limit
        if len(document.toRawText()) > highlighter_limit:
            document = None

        command = commands.SetCellRenderer(attr, self.model, entry_line,
                                           document, self.currentIndex(),
                                           self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_lock_pressed(self, toggled):
        """Lock button pressed event handler"""

        attr = self.selection, self.table, {"locked": toggled}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set locked state to {} for cells {}".format(toggled,
                                                                   idx_string)
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_rotate_0(self, toggled):
        """Set cell rotation to 0° left button pressed event handler"""

        attr = self.selection, self.table, {"angle": 0.0}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set cell rotation to 0° for cells {}".format(idx_string)
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_rotate_90(self, toggled):
        """Set cell rotation to 90° left button pressed event handler"""

        attr = self.selection, self.table, {"angle": 90.0}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set cell rotation to 90° for cells {}".format(
                idx_string)
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_rotate_180(self, toggled):
        """Set cell rotation to 180° left button pressed event handler"""

        attr = self.selection, self.table, {"angle": 180.0}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set cell rotation to 180° for cells {}".format(
                idx_string)
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_rotate_270(self, toggled):
        """Set cell rotation to 270° left button pressed event handler"""

        attr = self.selection, self.table, {"angle": 270.0}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set cell rotation to 270° for cells {}".format(
                idx_string)
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_justify_left(self, toggled):
        """Justify left button pressed event handler"""

        attr = self.selection, self.table, {"justification": "justify_left"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Justify cells {} left".format(idx_string)
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_justify_fill(self, toggled):
        """Justify fill button pressed event handler"""

        attr = self.selection, self.table, {"justification": "justify_fill"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Justify cells {} filled".format(idx_string)
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_justify_center(self, toggled):
        """Justify center button pressed event handler"""

        attr = self.selection, self.table, {"justification": "justify_center"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Justify cells {} centered".format(idx_string)
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_justify_right(self, toggled):
        """Justify right button pressed event handler"""

        attr = self.selection, self.table, {"justification": "justify_right"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Justify cells {} right".format(idx_string)
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_align_top(self, toggled):
        """Align top button pressed event handler"""

        attr = self.selection, self.table, {"vertical_align": "align_top"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Align cells {} to top".format(idx_string)
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_align_middle(self, toggled):
        """Align centere button pressed event handler"""

        attr = self.selection, self.table, {"vertical_align": "align_center"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Align cells {} to center".format(idx_string)
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_align_bottom(self, toggled):
        """Align bottom button pressed event handler"""

        attr = self.selection, self.table, {"vertical_align": "align_bottom"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Align cells {} to bottom".format(idx_string)
        command = commands.SetCellTextAlignment(attr, self.model,
                                                self.currentIndex(),
                                                self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_border_choice(self, event):
        """Border choice style event handler"""

        self.main_window.settings.border_choice = self.sender().text()
        self.gui_update()

    def on_text_color(self):
        """Text color change event handler"""

        text_color = self.main_window.widgets.text_color_button.color
        text_color_rgb = text_color.getRgb()
        attr = self.selection, self.table, {"textcolor": text_color_rgb}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description_tpl = "Set text color to {} for cells {}"
        description = description_tpl.format(text_color_rgb, idx_string)
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_line_color(self):
        """Line color change event handler"""

        border_choice = self.main_window.settings.border_choice
        bottom_selection = \
            self.selection.get_bottom_borders_selection(border_choice)
        right_selection = \
            self.selection.get_right_borders_selection(border_choice)

        line_color = self.main_window.widgets.line_color_button.color
        line_color_rgb = line_color.getRgb()

        attr_bottom = bottom_selection, self.table, {"bordercolor_bottom":
                                                     line_color_rgb}
        attr_right = right_selection, self.table, {"bordercolor_right":
                                                   line_color_rgb}

        idx_string = self._selected_idx_to_str(self.selected_idx)
        description_tpl = "Set line color {} for cells {}"
        description = description_tpl.format(line_color_rgb, idx_string)
        command = commands.SetCellFormat(attr_bottom, self.model,
                                         self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)
        command = commands.SetCellFormat(attr_right, self.model,
                                         self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_background_color(self):
        """Background color change event handler"""

        bg_color = self.main_window.widgets.background_color_button.color
        bg_color_rgb = bg_color.getRgb()
        self.gui_update()
        attr = self.selection, self.table, {"bgcolor": bg_color_rgb}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description_tpl = "Set cell background color to {} for cells {}"
        description = description_tpl.format(bg_color_rgb, idx_string)
        command = commands.SetCellFormat(attr, self.model, self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_borderwidth(self):
        """Border width change event handler"""

        width = int(self.sender().text().split()[-1])

        border_choice = self.main_window.settings.border_choice
        bottom_selection = \
            self.selection.get_bottom_borders_selection(border_choice)
        right_selection = \
            self.selection.get_right_borders_selection(border_choice)

        attr_bottom = bottom_selection, self.table, {"borderwidth_bottom":
                                                     width}
        attr_right = right_selection, self.table, {"borderwidth_right":
                                                   width}

        idx_string = self._selected_idx_to_str(self.selected_idx)
        description_tpl = "Set border width to {} for cells {}"
        description = description_tpl.format(width, idx_string)
        command = commands.SetCellFormat(attr_bottom, self.model,
                                         self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)
        command = commands.SetCellFormat(attr_right, self.model,
                                         self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def update_cell_spans(self):
        """Update cell spans from model data"""

        self.clearSpans()

        spans = {}  # Dict of (top, left): (bottom, right)

        for selection, table, attrs in self.model.code_array.cell_attributes:
            if table == self.table:
                try:
                    if attrs["merge_area"] is None:
                        bbox = self.selection.get_grid_bbox(self.model.shape)
                        (top, left), (_, _) = bbox
                        spans[(top, left)] = None
                    else:
                        top, left, bottom, right = attrs["merge_area"]
                        spans[(top, left)] = bottom, right
                except (KeyError, TypeError):
                    pass

        for top, left in spans:
            try:
                bottom, right = spans[(top, left)]
                self.setSpan(top, left, bottom-top+1, right-left+1)
            except TypeError:
                pass

    def update_index_widgets(self):
        """Remove old index widgets from model data"""

        # Remove old button cells
        for index in self.widget_indices:
            self.setIndexWidget(index, None)
        self.widget_indices.clear()

        # Add button cells for current table
        code_array = self.model.code_array
        for selection, table, attr in code_array.cell_attributes:
            if table == self.table and 'button_cell' in attr \
               and attr['button_cell']:
                row, column = selection.get_bbox()[0]
                index = self.model.index(row, column, QModelIndex())
                text = attr['button_cell']
                button = CellButton(text, self, (row, column, table))
                self.setIndexWidget(index, button)
                self.widget_indices.append(index)

    def on_freeze_pressed(self, toggled):
        """Freeze cell event handler"""

        current_attr = self.model.code_array.cell_attributes[self.current]
        if current_attr["frozen"] == toggled:
            return  # Something is wrong with the GUI update

        if toggled:
            # We have an non-frozen cell that has to be frozen
            description = "Freeze cell {}".format(self.current)
            command = commands.FreezeCell(self.model, self.current,
                                          description)
        else:
            # We have an frozen cell that has to be unfrozen
            description = "Thaw cell {}".format(self.current)
            command = commands.ThawCell(self.model, self.current, description)
        self.main_window.undo_stack.push(command)

    def on_button_cell_pressed(self, toggled):
        """Button cell event handler"""

        current_attr = self.model.code_array.cell_attributes[self.current]
        if not toggled and current_attr["button_cell"] is False \
           or toggled and current_attr["button_cell"] is not False:
            # Something is not syncronized in the menu
            return

        if toggled:
            # Get button text from user
            text, accept = QInputDialog.getText(self.main_window,
                                                "Make button cell",
                                                "Button text:",
                                                QLineEdit.Normal, "")
            if accept and text:
                description_tpl = "Make cell {} a button cell"
                description = description_tpl.format(self.current)
                command = commands.MakeButtonCell(self, text,
                                                  self.currentIndex(),
                                                  description)
                self.main_window.undo_stack.push(command)
        else:
            description_tpl = "Make cell {} a non-button cell"
            description = description_tpl.format(self.current)
            command = commands.RemoveButtonCell(self, self.currentIndex(),
                                                description)
            self.main_window.undo_stack.push(command)

    def on_merge_pressed(self):
        """Merge cells button pressed event handler"""

        # This is not done in the model because setSpan does not work there

        bbox = self.selection.get_grid_bbox(self.model.shape)
        (top, left), (bottom, right) = bbox

        # Check if current cell is already merged
        if self.columnSpan(top, left) > 1 or self.rowSpan(top, left) > 1:
            selection = Selection([], [], [], [], [(top, left)])
            attr = selection, self.table, {"merge_area": None}
            description_tpl = "Unmerge cells with top-left cell {}"
        elif bottom > top or right > left:
            # Merge and store the current selection
            merging_selection = Selection([], [], [], [], [(top, left)])
            attr = merging_selection, self.table, {"merge_area":
                                                   (top, left, bottom, right)}
            description_tpl = "Merge cells with top-left cell {}"
        else:
            # Cells are not merged because the span is one
            return

        description = description_tpl.format((top, left))
        command = commands.SetCellMerge(attr, self.model, self.currentIndex(),
                                        self.selected_idx, description)
        self.main_window.undo_stack.push(command)

        self.current = top, left

    def on_quote(self):
        """Quote cells event handler"""

        description_tpl = "Quote code for cell selection {}"
        description = description_tpl.format(id(self.selection))

        for idx in self.selected_idx:
            row = idx.row()
            column = idx.column()
            code = self.model.code_array((row, column, self.table))
            quoted_code = quote(code)
            index = self.model.index(row, column, QModelIndex())
            command = commands.SetCellCode(quoted_code, self.model, index,
                                           description)
            self.main_window.undo_stack.push(command)

    def on_insert_rows(self):
        """Insert rows event handler"""

        try:
            (top, _), (bottom, _) = \
                self.selection.get_grid_bbox(self.model.shape)
        except TypeError:
            top = bottom = self.row
        count = bottom - top + 1

        index = self.currentIndex()
        description_tpl = "Insert {} rows above row {}"
        description = description_tpl.format(count, top)
        command = commands.InsertRows(self.main_window.grid, self.model,
                                      index, top, count, description)
        self.main_window.undo_stack.push(command)

    def on_delete_rows(self):
        """Delete rows event handler"""

        try:
            (top, _), (bottom, _) = \
                self.selection.get_grid_bbox(self.model.shape)
        except TypeError:
            top = bottom = self.row
        count = bottom - top + 1

        index = self.currentIndex()
        description_tpl = "Delete {} rows starting from row {}"
        description = description_tpl.format(count, top)
        command = commands.DeleteRows(self.main_window.grid, self.model,
                                      index, top, count, description)
        self.main_window.undo_stack.push(command)

    def on_insert_columns(self):
        """Insert columns event handler"""

        try:
            (_, left), (_, right) = \
                self.selection.get_grid_bbox(self.model.shape)
        except TypeError:
            left = right = self.column
        count = right - left + 1

        index = self.currentIndex()
        description_tpl = "Insert {} columns left of column {}"
        description = description_tpl.format(count, self.column)
        command = commands.InsertColumns(self.main_window.grid, self.model,
                                         index, left, count, description)
        self.main_window.undo_stack.push(command)

    def on_delete_columns(self):
        """Delete columns event handler"""

        try:
            (_, left), (_, right) = \
                self.selection.get_grid_bbox(self.model.shape)
        except TypeError:
            left = right = self.column
        count = right - left + 1

        index = self.currentIndex()
        description_tpl = "Delete {} columns starting from column {}"
        description = description_tpl.format(count, self.column)
        command = commands.DeleteColumns(self.main_window.grid, self.model,
                                         index, left, count, description)
        self.main_window.undo_stack.push(command)

    def on_insert_table(self):
        """Insert table event handler"""

        description = "Insert table in front of table {}".format(self.table)
        command = commands.InsertTable(self.main_window.grid, self.model,
                                       self.table, description)
        self.main_window.undo_stack.push(command)

    def on_delete_table(self):
        """Delete table event handler"""

        description = "Delete table {}".format(self.table)
        command = commands.DeleteTable(self.main_window.grid, self.model,
                                       self.table, description)
        self.main_window.undo_stack.push(command)


class GridHeaderView(QHeaderView):
    """QHeaderView with zoom support"""

    def __init__(self, orientation, grid):
        super().__init__(orientation, grid)
        self.setSectionsClickable(True)
        self.default_section_size = self.defaultSectionSize()
        self.grid = grid

    # Overrides

    def sizeHint(self):
        """Overrides sizeHint, which supports zoom"""

        unzoomed_size = super().sizeHint()
        return QSize(unzoomed_size.width() * self.grid.zoom,
                     unzoomed_size.height() * self.grid.zoom)

    def sectionSizeHint(self, logicalIndex):
        """Overrides sectionSizeHint, which supports zoom"""

        unzoomed_size = super().sectionSizeHint(logicalIndex)
        return QSize(unzoomed_size.width() * self.grid.zoom,
                     unzoomed_size.height() * self.grid.zoom)

    def paintSection(self, painter, rect, logicalIndex):
        """Overrides paintSection, which supports zoom"""

        unzoomed_rect = QRect(0, 0,
                              rect.width()/self.grid.zoom,
                              rect.height()/self.grid.zoom)
        with self.grid.delegate.painter_save(painter):
            painter.translate(rect.x(), rect.y())
            painter.scale(self.grid.zoom, self.grid.zoom)
            super().paintSection(painter, unzoomed_rect, logicalIndex)

    def contextMenuEvent(self, event):
        """Overrides contextMenuEvent

        Installs HorizontalHeaderContextMenu or VerticalHeaderContextMenu
        depending on self.orientation().

        """

        actions = self.grid.main_window.main_window_actions
        if self.orientation() == Qt.Horizontal:
            menu = HorizontalHeaderContextMenu(actions)
        else:
            menu = VerticalHeaderContextMenu(actions)
        menu.exec_(self.mapToGlobal(event.pos()))

    # End of overrides

    def update_zoom(self):
        """Updates zoom for the section sizes"""

        with self.grid.undo_resizing_row():
            with self.grid.undo_resizing_column():
                self.setDefaultSectionSize(self.default_section_size
                                           * self.grid.zoom)

                if self.orientation() == Qt.Horizontal:
                    section_sizes = self.grid.column_widths
                else:
                    section_sizes = self.grid.row_heights

                for section, size in section_sizes:
                    self.resizeSection(section, size * self.grid.zoom)


class GridTableModel(QAbstractTableModel):
    """QAbstractTableModel for Grid"""

    def __init__(self, main_window, dimensions):
        super().__init__()

        self.main_window = main_window
        self.code_array = CodeArray(dimensions, main_window.settings)

    @contextmanager
    def model_reset(self):
        """Context manager for handle changing/resetting model data"""

        self.beginResetModel()
        yield
        self.endResetModel()

    @contextmanager
    def inserting_rows(self, index, first, last):
        """Context manager for inserting rows"""

        self.beginInsertRows(index, first, last)
        yield
        self.endInsertRows()

    @contextmanager
    def inserting_columns(self, index, first, last):
        """Context manager for inserting columns"""

        self.beginInsertColumns(index, first, last)
        yield
        self.endInsertColumns()

    @contextmanager
    def removing_rows(self, index, first, last):
        """Context manager for removing rows"""

        self.beginRemoveRows(index, first, last)
        yield
        self.endRemoveRows()

    @contextmanager
    def removing_columns(self, index, first, last):
        """Context manager for removing columns"""

        self.beginRemoveColumns(index, first, last)
        yield
        self.endRemoveColumns()

    @property
    def grid(self):
        return self.main_window.grid

    @property
    def shape(self):
        """Returns 3-tuple of rows, columns and tables"""

        return self.code_array.shape

    @shape.setter
    def shape(self, value):
        """Sets the shape in the code array and adjusts the table_choice"""

        with self.model_reset():
            self.code_array.shape = value
            self.grid.table_choice.no_tables = value[2]

    def current(self, index):
        """Tuple of row, column, table of given index"""

        return index.row(), index.column(), self.grid.table

    def code(self, index):
        """Code in index"""

        return self.code_array(self.current(index))

    def rowCount(self, parent=QModelIndex()):
        """Overloaded rowCount for code_array backend"""

        return self.shape[0]

    def columnCount(self, parent=QModelIndex()):
        """Overloaded columnCount for code_array backend"""

        return self.shape[1]

    def insertRows(self, row, count):
        """Overloaded insertRows for code_array backend"""

        self.code_array.insert(row, count, axis=0, tab=self.grid.table)
        return True

    def removeRows(self, row, count):
        """Overloaded removeRows for code_array backend"""

        try:
            self.code_array.delete(row, count, axis=0, tab=self.grid.table)
        except ValueError:
            return False
        return True

    def insertColumns(self, column, count):
        """Overloaded insertColumns for code_array backend"""

        self.code_array.insert(column, count, axis=1, tab=self.grid.table)
        return True

    def removeColumns(self, column, count):
        """Overloaded removeColumns for code_array backend"""

        try:
            self.code_array.delete(column, count, axis=1, tab=self.grid.table)
        except ValueError:
            return False
        return True

    def insertTable(self, table, count=1):
        """Inserts a table"""

        self.code_array.insert(table, count, axis=2)

    def removeTable(self, table, count=1):
        """Inserts a table"""

        self.code_array.delete(table, count, axis=2)

    def font(self, key):
        """Returns font for given key"""

        attr = self.code_array.cell_attributes[key]
        font = QFont()
        if attr["textfont"] is not None:
            font.setFamily(attr["textfont"])
        if attr["pointsize"] is not None:
            font.setPointSizeF(attr["pointsize"])
        if attr["fontweight"] is not None:
            font.setWeight(attr["fontweight"])
        if attr["fontstyle"] is not None:
            font.setStyle(attr["fontstyle"])
        if attr["underline"] is not None:
            font.setUnderline(attr["underline"])
        if attr["strikethrough"] is not None:
            font.setStrikeOut(attr["strikethrough"])
        return font

    def data(self, index, role=Qt.DisplayRole):
        """Overloaded data for code_array backend"""

        def safe_str(obj):
            """Returns str(obj), on RecursionError returns error message"""
            try:
                return str(value)
            except RecursionError as err:
                return str(err)

        key = self.current(index)

        if role == Qt.DisplayRole:
            value = self.code_array[key]
            renderer = self.code_array.cell_attributes[key]["renderer"]
            if renderer == "image" or value is None:
                return ""
            else:
                return safe_str(value)

        if role == Qt.ToolTipRole:
            value = self.code_array[key]
            if value is None:
                return ""
            else:
                return wrap_text(safe_str(value))

        if role == Qt.DecorationRole:
            renderer = self.code_array.cell_attributes[key]["renderer"]
            if renderer == "image":
                value = self.code_array[key]
                if isinstance(value, QImage):
                    return value
                else:
                    try:
                        arr = numpy.array(value)
                        return array2qimage(arr)
                    except Exception:
                        return value

        if role == Qt.BackgroundColorRole:
            if self.main_window.settings.show_frozen \
               and self.code_array.cell_attributes[key]["frozen"]:
                pattern_rgb = self.grid.palette().highlight().color()
                bg_color = QBrush(pattern_rgb, Qt.BDiagPattern)
            else:
                bg_color_rgb = self.code_array.cell_attributes[key]["bgcolor"]
                if bg_color_rgb is None:
                    bg_color = self.grid.palette().color(QPalette.Base)
                else:
                    bg_color = QColor(*bg_color_rgb)
            return bg_color

        if role == Qt.TextColorRole:
            text_color_rgb = self.code_array.cell_attributes[key]["textcolor"]
            if text_color_rgb is None:
                return self.grid.palette().color(QPalette.Text)
            else:
                return QColor(*text_color_rgb)

        if role == Qt.FontRole:
            return self.font(key)

        if role == Qt.TextAlignmentRole:
            pys2qt = {
                "justify_left": Qt.AlignLeft,
                "justify_center": Qt.AlignHCenter,
                "justify_right": Qt.AlignRight,
                "justify_fill": Qt.AlignJustify,
                "align_top": Qt.AlignTop,
                "align_center": Qt.AlignVCenter,
                "align_bottom": Qt.AlignBottom,
            }
            attr = self.code_array.cell_attributes[key]
            alignment = pys2qt[attr["vertical_align"]]
            justification = pys2qt[attr["justification"]]
            alignment |= justification
            return alignment

        return QVariant()

    def setData(self, index, value, role, raw=False, table=None):
        """Overloaded setData for code_array backend"""

        if role == Qt.EditRole:
            if table is None:
                key = self.current(index)
            else:
                key = index.row(), index.column(), table

            if raw:
                if value is None:
                    try:
                        self.code_array.pop(key)
                    except KeyError:
                        pass
                else:
                    self.code_array[key] = value
            else:
                self.code_array[key] = "{}".format(value)
            self.dataChanged.emit(index, index)

            return True

        if role == Qt.DecorationRole or role == Qt.TextAlignmentRole:
            self.code_array.cell_attributes.append(value)
            # We have a selection and no single cell
            for idx in index:
                self.dataChanged.emit(idx, idx)
            return True

    def flags(self, index):
        return QAbstractTableModel.flags(self, index) | Qt.ItemIsEditable

    def headerData(self, idx, orientation, role):
        if role == Qt.DisplayRole:
            return str(idx)

    def reset(self):
        """Deletes all grid data including undo data"""

        with self.model_reset():
            # Clear cells
            self.code_array.dict_grid.clear()

            # Clear attributes
            del self.code_array.dict_grid.cell_attributes[:]

            # Clear row heights and column widths
            self.code_array.row_heights.clear()
            self.code_array.col_widths.clear()

            # Clear macros
            self.code_array.macros = ""

            # Clear caches
            # self.main_window.undo_stack.clear()
            self.code_array.result_cache.clear()

            # Clear globals
            self.code_array.clear_globals()
            self.code_array.reload_modules()


class GridCellNavigator:
    """Find neighbors of a cell"""

    def __init__(self, main_window, key):
        self.main_window = main_window
        self.code_array = main_window.grid.model.code_array
        self.row, self.column, self.table = self.key = key

    @property
    def borderwidth_bottom(self):
        """Width of bottom border line"""

        return self.code_array.cell_attributes[self.key]["borderwidth_bottom"]

    @property
    def borderwidth_right(self):
        """Width of right border line"""

        return self.code_array.cell_attributes[self.key]["borderwidth_right"]

    @property
    def border_qcolor_bottom(self):
        """Color of bottom border line"""

        color = self.code_array.cell_attributes[self.key]["bordercolor_bottom"]
        if color is None:
            return self.main_window.grid.palette().color(QPalette.Mid)
        else:
            return QColor(*color)

    @property
    def border_qcolor_right(self):
        """Color of right border line"""

        color = self.code_array.cell_attributes[self.key]["bordercolor_right"]
        if color is None:
            return self.main_window.grid.palette().color(QPalette.Mid)
        else:
            return QColor(*color)

    @property
    def merge_area(self):
        """Merge area of the key cell"""

        return self.code_array.cell_attributes[self.key]["merge_area"]

    def _merging_key(self, *key):
        """Merging cell if key is merged else key"""

        merging_key = self.code_array.cell_attributes.get_merging_cell(key)
        return key if merging_key is None else merging_key

    def above_keys(self):
        """Key list of neighboring cells above the key cell"""

        merge_area = self.merge_area
        if merge_area is None:
            return [self._merging_key(self.row - 1, self.column, self.table)]
        else:
            top, left, bottom, right = merge_area
            return [self._merging_key(self.row - 1, col, self.table)
                    for col in range(left, right + 1)]

    def below_keys(self):
        """Key list of neighboring cells below the key cell"""

        merge_area = self.merge_area
        if merge_area is None:
            return [self._merging_key(self.row + 1, self.column, self.table)]
        else:
            top, left, bottom, right = merge_area
            return [self._merging_key(self.row + 1, col, self.table)
                    for col in range(left, right + 1)]

    def left_keys(self):
        """Key list of neighboring cells left of the key cell"""

        merge_area = self.merge_area
        if merge_area is None:
            return [self._merging_key(self.row, self.column - 1, self.table)]
        else:
            top, left, bottom, right = merge_area
            return [self._merging_key(row, self.column - 1, self.table)
                    for row in range(top, bottom + 1)]

    def right_keys(self):
        """Key list of neighboring cells right of the key cell"""

        merge_area = self.merge_area
        if merge_area is None:
            return [self._merging_key(self.row, self.column + 1, self.table)]
        else:
            top, left, bottom, right = merge_area
            return [self._merging_key(row, self.column + 1, self.table)
                    for row in range(top, bottom + 1)]

    def above_left_key(self):
        """Key of neighboring cell above left of the key cell"""

        return self._merging_key(self.row - 1, self.column - 1, self.table)

    def above_right_key(self):
        """Key of neighboring cell above right of the key cell"""

        return self._merging_key(self.row - 1, self.column + 1, self.table)

    def below_left_key(self):
        """Key of neighboring cell below left of the key cell"""

        return self._merging_key(self.row + 1, self.column - 1, self.table)

    def below_right_key(self):
        """Key of neighboring cell below right of the key cell"""

        return self._merging_key(self.row + 1, self.column + 1, self.table)


class GridCellDelegate(QStyledItemDelegate):

    def __init__(self, main_window, code_array):
        super().__init__()

        self.main_window = main_window
        self.code_array = code_array
        self.cell_attributes = self.code_array.cell_attributes

    @property
    def grid(self):
        return self.main_window.grid

    @contextmanager
    def painter_save(self, painter):
        painter.save()
        yield
        painter.restore()

    def _paint_bl_border_lines(self, x, y, width, height, painter, key):
        """Paint the bottom and the left border line of the cell"""

        cell = GridCellNavigator(self.main_window, key)

        borderline_bottom = [x - .5,
                             y + height - .5,
                             x + width - .5,
                             y + height - .5]
        borderline_right = [x + width - .5,
                            y - .5,
                            x + width - .5,
                            y + height - .5]

        # Check, which line is the thickest at each edge
        # Shorten line accordingly

        above_left_cell = GridCellNavigator(self.main_window,
                                            cell.above_left_key())
        above_cells = [GridCellNavigator(self.main_window, key)
                       for key in cell.above_keys()]
        above_right_cell = GridCellNavigator(self.main_window,
                                             cell.above_right_key())
        right_cells = [GridCellNavigator(self.main_window, key)
                       for key in cell.right_keys()]
#        below_right_cell = GridCellNavigator(self.main_window,
#                                             cell.below_right_key())
        below_cells = [GridCellNavigator(self.main_window, key)
                       for key in cell.below_keys()]
        below_left_cell = GridCellNavigator(self.main_window,
                                            cell.below_left_key())
        left_cells = [GridCellNavigator(self.main_window, key)
                      for key in cell.left_keys()]

        # Lower left edge:
        # Bottom lines of left cells and right line of below left cell

        lower_left_edge_width = max([c.borderwidth_bottom for c in left_cells]
                                    + [below_left_cell.borderwidth_right])
        if lower_left_edge_width > cell.borderwidth_bottom:
            borderline_bottom[0] += lower_left_edge_width / 2

        # Lower right edge:
        # Right lines of below cells and bottom lines of right cells

        lower_right_edge_width = \
            max([c.borderwidth_right for c in below_cells]
                + [c.borderwidth_bottom for c in right_cells])

        if lower_right_edge_width > cell.borderwidth_bottom:
            borderline_bottom[2] -= lower_right_edge_width / 2

        if lower_right_edge_width > cell.borderwidth_right:
            borderline_right[3] -= lower_right_edge_width / 2

        # Top right edge:
        # Right lines of above cells and bottom line of above right cell

        top_right_edge_width = max([c.borderwidth_right for c in above_cells]
                                   + [above_right_cell.borderwidth_bottom])
        if top_right_edge_width > cell.borderwidth_bottom:
            borderline_right[1] += top_right_edge_width / 2

        # Draw lines if their width is not 0

        if cell.borderwidth_bottom:
            painter.setPen(QPen(QBrush(cell.border_qcolor_bottom),
                                cell.borderwidth_bottom))
            bottom_border_line = QLineF(*borderline_bottom)
            painter.drawLine(bottom_border_line)

        if cell.borderwidth_right:
            painter.setPen(QPen(QBrush(cell.border_qcolor_right),
                                cell.borderwidth_right))
            right_border_line = QLineF(*borderline_right)
            painter.drawLine(right_border_line)

        # Inner rect
        irect_x = x - .5 + max(above_left_cell.borderwidth_right,
                               *[c.borderwidth_right for c in left_cells],
                               below_left_cell.borderwidth_right) / 2
        irect_y = y - .5 + max(above_left_cell.borderwidth_bottom,
                               *[c.borderwidth_bottom for c in above_cells],
                               above_right_cell.borderwidth_bottom) / 2
        irect_width = (x + width - irect_x
                       - max(above_cells[-1].borderwidth_right,
                             cell.borderwidth_right,
                             below_cells[-1].borderwidth_right) / 2)
        irect_height = (y + height - irect_y
                        - max(left_cells[-1].borderwidth_bottom,
                              cell.borderwidth_bottom,
                              right_cells[-1].borderwidth_bottom) / 2)

        return irect_x, irect_y, irect_width, irect_height

    def _paint_border_lines(self, width, height, painter, index):
        """Paint border lines around the cell

        First, bottom and right border lines are painted.
        Next, border lines of the cell above are painted.
        Next, border lines of the cell left are painted.
        Finally, bottom and right border lines of the cell above left
        are painted.

        """

        row = index.row()
        column = index.column()
        table = self.grid.table

        # Paint bottom and right border lines of the current cell
        key = row, column, table
        return self._paint_bl_border_lines(0, 0, width, height, painter, key)

    def _render_markup(self, painter, option, index):
        """HTML markup renderer"""

        self.initStyleOption(option, index)

        style = option.widget.style()

        doc = QTextDocument()

        font = self.grid.model.data(index, role=Qt.FontRole)
        doc.setDefaultFont(font)

        alignment = self.grid.model.data(index, role=Qt.TextAlignmentRole)
        doc.setDefaultTextOption(QTextOption(alignment))

        bg_color = self.grid.model.data(index, role=Qt.BackgroundColorRole)
        css = "background-color: {bg_color};".format(bg_color=bg_color)
        doc.setDefaultStyleSheet(css)

        doc.setHtml(option.text)
        doc.setTextWidth(option.rect.width())

        option.text = ""
        style.drawControl(QStyle.CE_ItemViewItem, option, painter,
                          option.widget)

        ctx = QAbstractTextDocumentLayout.PaintContext()

        text_color = self.grid.model.data(index, role=Qt.TextColorRole)
        ctx.palette.setColor(QPalette.Text, text_color)

        with self.painter_save(painter):
            painter.translate(option.rect.topLeft())
            painter.setClipRect(option.rect.translated(-option.rect.topLeft()))
            doc.documentLayout().draw(painter, ctx)

    def _get_aligned_image_rect(self, option, index,
                                image_width, image_height):
        """Returns image rect dependent on alignment and justification"""

        def scale_size(inner_width, inner_height, outer_width, outer_height):
            """Scales up inner_rect to fit in outer_rect

            Returns width, height tuple that maintains aspect ratio.

            Parameters
            ----------

             * inner_width: int or float
             \tWidth of the inner rect that is scaled up to the outer rect
             * inner_height: int or float
             \tHeight of the inner rect that is scaled up to the outer rect
             * outer_width: int or float
             \tWidth of the outer rect
             * outer_height: int or float
             \tHeight of the outer rect

            """

            if inner_width and inner_height and outer_width and outer_height:
                inner_aspect = inner_width / inner_height
                outer_aspect = outer_width / outer_height

                if outer_aspect < inner_aspect:
                    inner_width *= outer_width / inner_width
                    inner_height = inner_width / inner_aspect
                else:
                    inner_height *= outer_height / inner_height
                    inner_width = inner_height * inner_aspect

            return inner_width, inner_height

        key = index.row(), index.column(), self.grid.table

        justification = self.cell_attributes[key]["justification"]
        vertical_align = self.cell_attributes[key]["vertical_align"]

        if justification == "justify_fill":
            return option.rect

        rect_x, rect_y = option.rect.x(), option.rect.y()
        rect_width, rect_height = option.rect.width(), option.rect.height()

        try:
            image_width, image_height = scale_size(image_width, image_height,
                                                   rect_width, rect_height)
        except ZeroDivisionError:
            pass
        image_x, image_y = rect_x, rect_y

        if justification == "justify_center":
            image_x = rect_x + rect_width / 2 - image_width / 2
        elif justification == "justify_right":
            image_x = rect_x + rect_width - image_width

        if vertical_align == "align_center":
            image_y = rect_y + rect_height / 2 - image_height / 2
        elif vertical_align == "align_bottom":
            image_y = rect_y + rect_height - image_height

        return QRect(image_x, image_y, image_width, image_height)

    def _render_qimage(self, painter, option, index, qimage=None):
        """QImage renderer"""

        if qimage is None:
            qimage = index.data(Qt.DecorationRole)

        row, column = index.row(), index.column()
        row_span = self.grid.rowSpan(row, column)
        column_span = self.grid.columnSpan(row, column)
        if row_span == column_span == 1:
            rect = option.rect
        else:
            height = 0
            width = 0
            for __row in range(row, row + row_span + 1):
                height += self.grid.rowHeight(__row)
            for __column in range(column, column + column_span + 1):
                width += self.grid.columnWidth(__column)
            rect = QRect(option.rect.x(), option.rect.y(), width, height)

        if isinstance(qimage, QImage):
            img_width, img_height = qimage.width(), qimage.height()
        else:
            if qimage is None:
                return
            try:
                svg_bytes = bytes(qimage)
            except TypeError:
                try:
                    svg_bytes = bytes(qimage, encoding='utf-8')
                except TypeError:
                    return

            if not is_svg(svg_bytes):
                return

            svg_width, svg_height = get_svg_size(svg_bytes)
            try:
                svg_aspect = svg_width / svg_height
            except ZeroDivisionError:
                svg_aspect = 1
            try:
                rect_aspect = rect.width() / rect.height()
            except ZeroDivisionError:
                rect_aspect = 1

            rect_width = rect.width() * 2.0
            rect_height = rect.height() * 2.0

            if svg_aspect > rect_aspect:
                # svg is wider than rect --> shrink height
                img_width = rect_width
                img_height = rect_width / svg_aspect
            else:
                img_width = rect_height * svg_aspect
                img_height = rect_height

            if self.main_window.settings.print_zoom is not None:
                img_width *= self.main_window.settings.print_zoom
                img_height *= self.main_window.settings.print_zoom
            qimage = QImageSvg(img_width, img_height, QImage.Format_ARGB32)
            qimage.from_svg_bytes(svg_bytes)

        img_rect = self._get_aligned_image_rect(option, index,
                                                img_width, img_height)
        if img_rect is None:
            return

        key = index.row(), index.column(), self.grid.table
        justification = self.cell_attributes[key]["justification"]

        if justification == "justify_fill":
            qimage = qimage.scaled(img_width, img_height,
                                   Qt.IgnoreAspectRatio,
                                   Qt.SmoothTransformation)
        else:
            qimage = qimage.scaled(img_width, img_height,
                                   Qt.KeepAspectRatio,
                                   Qt.SmoothTransformation)

        with self.painter_save(painter):
            try:
                scale_x = img_rect.width() / img_width
            except ZeroDivisionError:
                scale_x = 1
            try:
                scale_y = img_rect.height() / img_height
            except ZeroDivisionError:
                scale_y = 1
            painter.translate(img_rect.x(), img_rect.y())
            painter.scale(scale_x, scale_y)
            painter.drawImage(0, 0, qimage)

    def _render_matplotlib(self, painter, option, index):
        """Matplotlib renderer"""

        if matplotlib is None:
            # matplotlib is not installed
            return

        key = index.row(), index.column(), self.grid.table
        figure = self.code_array[key]

        if not isinstance(figure, matplotlib.figure.Figure):
            return

        # Save SVG in a fake file object.
        filelike = BytesIO()
        figure.savefig(filelike, format="svg")
        svg_str = filelike.getvalue().decode()

        self._render_qimage(painter, option, index, qimage=svg_str)

    def __paint(self, painter, option, index):
        """Calls the overloaded paint function or creates html delegate"""

        key = index.row(), index.column(), self.grid.table
        renderer = self.cell_attributes[key]["renderer"]

        if renderer == "text":
            super(GridCellDelegate, self).paint(painter, option, index)

        elif renderer == "markup":
            self._render_markup(painter, option, index)

        elif renderer == "image":
            self._render_qimage(painter, option, index)

        elif renderer == "matplotlib":
            self._render_matplotlib(painter, option, index)

    def sizeHint(self, option, index):
        """Overloads SizeHint"""

        key = index.row(), index.column(), self.grid.table
        if not self.cell_attributes[key]["renderer"] == "markup":
            return super(GridCellDelegate, self).sizeHint(option, index)

        # HTML
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        doc = QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(options.rect.width())
        return QSize(doc.idealWidth(), doc.size().height())

    def _rotated_paint(self, painter, option, index, angle):
        """Paint cell contents for rotated cells"""

        # Rotate evryting by 90 degree

        optionCopy = QStyleOptionViewItem(option)
        rectCenter = QPointF(QRectF(option.rect).center())
        with self.painter_save(painter):
            painter.translate(rectCenter.x(), rectCenter.y())
            painter.rotate(angle)
            painter.translate(-rectCenter.x(), -rectCenter.y())
            optionCopy.rect = painter.worldTransform().mapRect(option.rect)

            # Call the base class paint method
            self.__paint(painter, optionCopy, index)

    def paint(self, painter, option, index):
        """Overloads QStyledItemDelegate to add cell border painting"""

        def get_unzoomed_rect_args(rect, zoom):
            x = 0
            y = 0
            width = rect.width() / zoom
            height = rect.height() / zoom
            return x, y, width, height

        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        zoom = self.grid.zoom
        x = option.rect.x()
        y = option.rect.y()

        rectf = option.rect = QRect(*get_unzoomed_rect_args(option.rect, zoom))
        if hasattr(option, "rectf"):
            rectf = QRectF(*get_unzoomed_rect_args(option.rectf, zoom))
            x = option.rectf.x()
            y = option.rectf.y()

        with self.painter_save(painter):
            painter.translate(x, y)
            painter.scale(zoom, zoom)
            key = index.row(), index.column(), self.grid.table
            angle = self.cell_attributes[key]["angle"]

            ix, iy, iw, ih = self._paint_border_lines(rectf.width(),
                                                      rectf.height(),
                                                      painter, index)
            with self.painter_save(painter):
                painter.translate(ix, iy)
                option.rect = QRect(0, 0, iw, ih)
                if isclose(angle, 0):
                    # No rotation --> call the base class paint method
                    self.__paint(painter, option, index)
                else:
                    self._rotated_paint(painter, option, index, angle)

    def createEditor(self, parent, option, index):
        """Overloads QStyledItemDelegate

        Disables editor in locked cells
        Switches to chart dialog in chart cells

        """

        key = index.row(), index.column(), self.grid.table

        if self.cell_attributes[key]["locked"]:
            return

        if self.cell_attributes[key]["renderer"] == "matplotlib":
            self.main_window.workflows.macro_insert_chart()
            return

        self.editor = super(GridCellDelegate, self).createEditor(parent,
                                                                 option, index)

        self.editor.installEventFilter(self)
        return self.editor

    def eventFilter(self, source, event):
        """Quotes cell editor content for <Ctrl>+<Enter> and <Ctrl>+<Return>

        Overrides QLineEdit default shortcut. Counts as undoable action.

        """

        if event.type() == QEvent.ShortcutOverride \
           and source is self.editor \
           and event.modifiers() == Qt.ControlModifier \
           and event.key() in (Qt.Key_Return, Qt.Key_Enter):

            code = quote(source.text())
            index = self.grid.currentIndex()
            description = "Quote code for cell {}".format(index)
            cmd = commands.SetCellCode(code, self.grid.model, index,
                                       description)
            self.main_window.undo_stack.push(cmd)
        return QWidget.eventFilter(self, source, event)

    def setEditorData(self, editor, index):
        row = index.row()
        column = index.column()
        table = self.grid.table

        value = self.code_array((row, column, table))
        editor.setText(value)

    def setModelData(self, editor, model, index):
        description = "Set code for cell {}".format(model.current(index))
        command = commands.SetCellCode(editor.text(), model, index,
                                       description)
        self.main_window.undo_stack.push(command)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class TableChoice(QTabBar):
    """The TabBar below the main grid"""

    def __init__(self, grid, no_tables):
        super().__init__(shape=QTabBar.RoundedSouth)
        self.setExpanding(False)

        self.grid = grid
        self.no_tables = no_tables

        self.currentChanged.connect(self.on_table_changed)

    @property
    def no_tables(self):
        return self._no_tables

    @no_tables.setter
    def no_tables(self, value):
        self._no_tables = value

        if value > self.count():
            # Insert
            for i in range(self.count(), value):
                self.addTab(str(i))

        elif value < self.count():
            # Remove
            for i in range(self.count()-1, value-1, -1):
                self.removeTab(i)

    @property
    def table(self):
        """Returns current table from table_choice that is displayed"""

        return self.currentIndex()

    @table.setter
    def table(self, value):
        """Sets a new table to be displayed"""

        self.setCurrentIndex(value)

    # Overrides

    def contextMenuEvent(self, event):
        """Overrides contextMenuEvent to install GridContextMenu"""

        actions = self.grid.main_window.main_window_actions

        menu = TableChoiceContextMenu(actions)
        menu.exec_(self.mapToGlobal(event.pos()))

    # Event handlers

    def on_table_changed(self, current):
        """Event handler for table changes"""

        with self.grid.undo_resizing_row():
            with self.grid.undo_resizing_column():
                self.grid.update_cell_spans()
                self.grid.update_zoom()

        self.grid.update_index_widgets()
        self.grid.model.dataChanged.emit(QModelIndex(), QModelIndex())
        self.grid.gui_update()
