#!/usr/bin/env python3
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

grid
====

Main grid for pyspread

Provides
--------

* Grid: QTableView of the main grid
* GridItemModel: QAbstractTableModel linking the view to the code_array backend
* GridCellDelegate: QStyledItemDelegate handling custom painting and editors

"""

from contextlib import contextmanager

import numpy

from PyQt5.QtWidgets import QTableView, QStyledItemDelegate, QTabBar
from PyQt5.QtWidgets import QStyleOptionViewItem, QApplication, QStyle
from PyQt5.QtWidgets import QAbstractItemDelegate, QHeaderView
from PyQt5.QtGui import QColor, QBrush, QPen, QFont
from PyQt5.QtGui import QImage as BasicQImage
from PyQt5.QtGui import QAbstractTextDocumentLayout, QTextDocument
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtCore import QPointF, QRectF, QSize, QRect, QItemSelectionModel

try:
    import matplotlib.figure as matplotlib_figure
except ImportError:
    matplotlib_figure = None

from src.commands import CommandSetCellCode, CommandSetCellFormat
from src.commands import CommandSetCellMerge
from src.commands import CommandSetCellRenderer, CommandSetRowHeight
from src.commands import CommandSetColumnWidth, CommandSetCellTextAlignment
from src.model.model import CodeArray
from src.lib.selection import Selection
from src.lib.string_helpers import quote, wrap_text, get_svg_aspect
from src.lib.qimage2ndarray import array2qimage
from src.lib.qimage_svg import QImage
from src.lib.typechecks import is_svg


class Grid(QTableView):
    """The main grid of pyspread"""

    def __init__(self, main_window):
        super().__init__()

        self.main_window = main_window

        dimensions = (main_window.settings.grid_rows,
                      main_window.settings.grid_columns,
                      main_window.settings.grid_tables)

        window_position = main_window.settings.window_position
        window_size = main_window.settings.window_size

        self.setGeometry(*window_position, *window_size)

        self.model = GridItemModel(main_window, dimensions)
        self.setModel(self.model)

        self.table_choice = TableChoice(self, dimensions[2])

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

        self.zoom(main_window.application_states.zoom)

        self.verticalHeader().sectionResized.connect(self.on_row_resized)
        self.horizontalHeader().sectionResized.connect(self.on_column_resized)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setShowGrid(False)

        delegate = GridCellDelegate(main_window, self.model.code_array)
        self.setItemDelegate(delegate)

        # Select upper left cell because initial selection behaves strange
        self.reset_selection()

        # Locking states for operations by undo and redo operations
        self.undo_resizing_row = False
        self.undo_resizing_column = False

    # Properties

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
        else:
            super().keyPressEvent(event)

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
        """Converts selected_idx to string wirh cell indices"""

        return ", ".join(str(self.model.current(idx)) for idx in selected_idx)

    def zoom(self, zoom):
        """Sets the zoom level to the zoom factor zoom

        Parameters
        ----------
        * zoom: float
        \tZoom factor

        """

        self.verticalHeader().zoom(zoom)
        self.horizontalHeader().zoom(zoom)

    # Event handlers

    def on_data_changed(self):
        """Event handler for data changes"""

        code = self.model.code_array(self.current)
        self.main_window.entry_line.setPlainText(code)

        if not self.main_window.application_states.changed_since_save:
            self.main_window.application_states.changed_since_save = True
            main_window_title = "* " + self.main_window.windowTitle()
            self.main_window.setWindowTitle(main_window_title)

    def on_current_changed(self, current, previous):
        """Event handler for change of current cell"""

        code = self.model.code_array(self.current)
        self.main_window.entry_line.setPlainText(code)
        self.gui_update()

    def on_row_resized(self, row, old_height, new_height):
        """Row resized event handler"""

        if self.undo_resizing_row:  # Resize from undo or redo command
            return
        description = "Resize row {} to {}".format(row, new_height)
        command = CommandSetRowHeight(self, row, self.table, old_height,
                                      new_height, description)
        self.main_window.undo_stack.push(command)

    def on_column_resized(self, column, old_width, new_width):
        """Column resized event handler"""

        if self.undo_resizing_column:  # Resize from undo or redo command
            return
        description = "Resize column {} to {}".format(column, new_width)
        command = CommandSetColumnWidth(self, column, self.table, old_width,
                                        new_width, description)
        self.main_window.undo_stack.push(command)

    def on_font(self):
        """Font change event handler"""

        font = self.main_window.widgets.font_combo.font
        attr = self.selection, self.table, {"textfont": font}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set font {} for indices {}".format(font, idx_string)
        command = CommandSetCellFormat(attr, self.model, self.currentIndex(),
                                       self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_font_size(self):
        """Font size change event handler"""

        size = self.main_window.widgets.font_size_combo.size
        attr = self.selection, self.table, {"pointsize": size}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set font size {} for cells {}".format(size, idx_string)
        command = CommandSetCellFormat(attr, self.model, self.currentIndex(),
                                       self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_bold_pressed(self, toggled):
        """Bold button pressed event handler"""

        fontweight = QFont.Bold if toggled else QFont.Normal
        attr = self.selection, self.table, {"fontweight": fontweight}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set font weight {} for cells {}".format(fontweight,
                                                               idx_string)
        command = CommandSetCellFormat(attr, self.model, self.currentIndex(),
                                       self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_italics_pressed(self, toggled):
        """Italics button pressed event handler"""

        fontstyle = QFont.StyleItalic if toggled else QFont.StyleNormal
        attr = self.selection, self.table, {"fontstyle": fontstyle}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set font style {} for cells {}".format(fontstyle,
                                                              idx_string)
        command = CommandSetCellFormat(attr, self.model, self.currentIndex(),
                                       self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_underline_pressed(self, toggled):
        """Underline button pressed event handler"""

        attr = self.selection, self.table, {"underline": toggled}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set font underline {} for cells {}".format(toggled,
                                                                  idx_string)
        command = CommandSetCellFormat(attr, self.model, self.currentIndex(),
                                       self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_strikethrough_pressed(self, toggled):
        """Strikethrough button pressed event handler"""

        attr = self.selection, self.table, {"strikethrough": toggled}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description_tpl = "Set font strikethrough {} for cells {}"
        description = description_tpl.format(toggled, idx_string)
        command = CommandSetCellFormat(attr, self.model, self.currentIndex(),
                                       self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_text_renderer_pressed(self, toggled):
        """Text renderer button pressed event handler"""

        attr = self.selection, self.table, {"renderer": "text"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set text renderer for cells {}".format(idx_string)
        entry_line = self.main_window.entry_line
        command = CommandSetCellRenderer(attr, self.model, entry_line,
                                         entry_line.document(),
                                         self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_image_renderer_pressed(self, toggled):
        """Image renderer button pressed event handler"""

        attr = self.selection, self.table, {"renderer": "image"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set image renderer for cells {}".format(idx_string)
        entry_line = self.main_window.entry_line
        command = CommandSetCellRenderer(attr, self.model, entry_line, None,
                                         self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_markup_renderer_pressed(self, toggled):
        """Markup renderer button pressed event handler"""

        attr = self.selection, self.table, {"renderer": "markup"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set markup renderer for cells {}".format(idx_string)
        entry_line = self.main_window.entry_line
        command = CommandSetCellRenderer(attr, self.model, entry_line,
                                         entry_line.document(),
                                         self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_matplotlib_renderer_pressed(self, toggled):
        """Matplotlib renderer button pressed event handler"""

        attr = self.selection, self.table, {"renderer": "matplotlib"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set matplotlib renderer for cells {}".format(idx_string)
        entry_line = self.main_window.entry_line
        command = CommandSetCellRenderer(attr, self.model, entry_line,
                                         entry_line.document(),
                                         self.currentIndex(),
                                         self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_lock_pressed(self, toggled):
        """Lock button pressed event handler"""

        attr = self.selection, self.table, {"locked": toggled}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set locked state to {} for cells {}".format(toggled,
                                                                   idx_string)
        command = CommandSetCellFormat(attr, self.model, self.currentIndex(),
                                       self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_rotate_0(self, toggled):
        """Set cell rotation to 0° left button pressed event handler"""

        attr = self.selection, self.table, {"angle": 0.0}
        self.model.setData(self.selected_idx, attr, Qt.TextAlignmentRole)
        self.gui_update()

        attr = self.selection, self.table, {"angle": 0.0}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set cell rotation to 0° for cells {}".format(idx_string)
        command = CommandSetCellTextAlignment(attr, self.model,
                                              self.currentIndex(),
                                              self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_rotate_90(self, toggled):
        """Set cell rotation to 90° left button pressed event handler"""

        attr = self.selection, self.table, {"angle": 90.0}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set cell rotation to 90° for cells {}".format(
                idx_string)
        command = CommandSetCellTextAlignment(attr, self.model,
                                              self.currentIndex(),
                                              self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_rotate_180(self, toggled):
        """Set cell rotation to 180° left button pressed event handler"""

        attr = self.selection, self.table, {"angle": 180.0}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set cell rotation to 180° for cells {}".format(
                idx_string)
        command = CommandSetCellTextAlignment(attr, self.model,
                                              self.currentIndex(),
                                              self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_rotate_270(self, toggled):
        """Set cell rotation to 270° left button pressed event handler"""

        attr = self.selection, self.table, {"angle": 270.0}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Set cell rotation to 270° for cells {}".format(
                idx_string)
        command = CommandSetCellTextAlignment(attr, self.model,
                                              self.currentIndex(),
                                              self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_justify_left(self, toggled):
        """Justify left button pressed event handler"""

        attr = self.selection, self.table, {"justification": "justify_left"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Justify cells {} left".format(idx_string)
        command = CommandSetCellTextAlignment(attr, self.model,
                                              self.currentIndex(),
                                              self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_justify_fill(self, toggled):
        """Justify fill button pressed event handler"""

        attr = self.selection, self.table, {"justification": "justify_fill"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Justify cells {} filled".format(idx_string)
        command = CommandSetCellTextAlignment(attr, self.model,
                                              self.currentIndex(),
                                              self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_justify_center(self, toggled):
        """Justify center button pressed event handler"""

        attr = self.selection, self.table, {"justification": "justify_center"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Justify cells {} centered".format(idx_string)
        command = CommandSetCellTextAlignment(attr, self.model,
                                              self.currentIndex(),
                                              self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_justify_right(self, toggled):
        """Justify right button pressed event handler"""

        attr = self.selection, self.table, {"justification": "justify_right"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Justify cells {} right".format(idx_string)
        command = CommandSetCellTextAlignment(attr, self.model,
                                              self.currentIndex(),
                                              self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_align_top(self, toggled):
        """Align top button pressed event handler"""

        attr = self.selection, self.table, {"vertical_align": "align_top"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Align cells {} to top".format(idx_string)
        command = CommandSetCellTextAlignment(attr, self.model,
                                              self.currentIndex(),
                                              self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_align_middle(self, toggled):
        """Align centere button pressed event handler"""

        attr = self.selection, self.table, {"vertical_align": "align_center"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Align cells {} to center".format(idx_string)
        command = CommandSetCellTextAlignment(attr, self.model,
                                              self.currentIndex(),
                                              self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_align_bottom(self, toggled):
        """Align bottom button pressed event handler"""

        attr = self.selection, self.table, {"vertical_align": "align_bottom"}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description = "Align cells {} to bottom".format(idx_string)
        command = CommandSetCellTextAlignment(attr, self.model,
                                              self.currentIndex(),
                                              self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_border_choice(self, event):
        """Border choice style event handler"""

        self.main_window.application_states.border_choice = \
            self.sender().text()
        self.gui_update()

    def on_text_color(self):
        """Text color change event handler"""

        text_color = self.main_window.widgets.text_color_button.color
        text_color_rgb = text_color.getRgb()
        attr = self.selection, self.table, {"textcolor": text_color_rgb}
        idx_string = self._selected_idx_to_str(self.selected_idx)
        description_tpl = "Set text color to {} for cells {}"
        description = description_tpl.format(text_color_rgb, idx_string)
        command = CommandSetCellFormat(attr, self.model, self.currentIndex(),
                                       self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_line_color(self):
        """Line color change event handler"""

        border_choice = self.main_window.application_states.border_choice
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
        command = CommandSetCellFormat(attr_bottom, self.model,
                                       self.currentIndex(),
                                       self.selected_idx, description)
        self.main_window.undo_stack.push(command)
        command = CommandSetCellFormat(attr_right, self.model,
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
        command = CommandSetCellFormat(attr, self.model, self.currentIndex(),
                                       self.selected_idx, description)
        self.main_window.undo_stack.push(command)

    def on_borderwidth(self):
        """Border width change event handler"""

        width = int(self.sender().text().split()[-1])

        border_choice = self.main_window.application_states.border_choice
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
        command = CommandSetCellFormat(attr_bottom, self.model,
                                       self.currentIndex(),
                                       self.selected_idx, description)
        self.main_window.undo_stack.push(command)
        command = CommandSetCellFormat(attr_right, self.model,
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

    def on_merge_pressed(self):
        """Merge cells button pressed event handler"""

        # This is not done in the model because setSpan does not work there

        bbox = self.selection.get_grid_bbox(self.model.shape)
        (top, left), (bottom, right) = bbox

        # Check if current cell is already merged
        if self.columnSpan(top, left) > 1 or self.rowSpan(top, left) > 1:
            selection = Selection([], [], [], [], [(top, left)])
            attr = selection, self.table, {"merge_area": None}
        elif self.columnSpan(self.row, self.column) > 1 \
                or self.rowSpan(self.row, self.column) > 1:
            # Unmerge the cell that merges the current cell (!)
            selection = Selection([], [], [], [], [(self.row, self.column)])
            attr = selection, self.table, {"merge_area": None}
        else:
            # Merge and store the current selection (!)
            merging_selection = Selection([], [], [], [], [(top, left)])
            attr = merging_selection, self.table, {"merge_area":
                                                   (top, left, bottom, right)}

        description_tpl = "Merge cells with top-left cell {}"
        description = description_tpl.format((top, left))
        command = CommandSetCellMerge(attr, self.model, self.currentIndex(),
                                      self.selected_idx, description)
        self.main_window.undo_stack.push(command)

        self.current = top, left

    def selected_cells(self, selection):
        """Generator of (row, column, table) tuples for a selection object"""

        for row, column, table in self.model.code_array.dict_grid.keys():
            if table == self.table and (row, column) in selection:
                yield row, column, table

    def on_quote(self):
        """Quote cells event handler"""

        description_tpl = "Quote code for cell selection {}"
        description = description_tpl.format(id(self.selection))

        for row, column, table in self.selected_cells(self.selection):
            code = self.model.code_array((row, column, table))
            quoted_code = quote(code)
            index = self.model.index(row, column, QModelIndex())
            command = CommandSetCellCode(quoted_code, self.model, index,
                                         description)
            self.main_window.undo_stack.push(command)


class GridHeaderView(QHeaderView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_section_size = self.defaultSectionSize()
        self.__zoom = 1.0

    def zoom(self, zoom):
        """Zooms the section sizes"""

        self.__zoom = zoom
        self.setDefaultSectionSize(self.default_section_size * zoom)

    def sizeHint(self):
        unzoomed_size = super().sizeHint()
        return QSize(unzoomed_size.width() * self.__zoom,
                     unzoomed_size.height() * self.__zoom)

    def paintSection(self, painter, rect, logicalIndex):
        zoom = self.__zoom
        unzoomed_rect = QRect(rect.x()/zoom, rect.y()/zoom,
                              rect.width()/zoom, rect.height()/zoom)
        painter.save()
        painter.scale(zoom, zoom)
        super().paintSection(painter, unzoomed_rect, logicalIndex)
        painter.restore()


class GridItemModel(QAbstractTableModel):
    def __init__(self, main_window, dimensions):
        super().__init__()

        self.main_window = main_window
        self.code_array = CodeArray(dimensions)

    @contextmanager
    def model_reset(self):
        """Context manager for handle changing/resetting model data"""

        self.beginResetModel()
        yield
        self.endResetModel()

    @property
    def shape(self):
        """Returns 3-tuple of rows, columns and tables"""

        return self.code_array.shape

    @shape.setter
    def shape(self, value):
        """Sets the shape in the code array and adjusts the table_choice"""

        with self.model_reset():
            self.code_array.shape = value
            self.main_window.grid.table_choice.no_tables = value[2]

    def current(self, index):
        """Tuple of row, column, table of given index"""

        return index.row(), index.column(), self.main_window.grid.table

    def code(self, index):
        """Code in index"""

        return self.code_array(self.current(index))

    def rowCount(self, parent=QModelIndex()):
        """Overloaded rowCount for code_array backend"""

        return self.shape[0]

    def columnCount(self, parent=QModelIndex()):
        """Overloaded columnCount for code_array backend"""

        return self.shape[1]

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
                if isinstance(value, BasicQImage):
                    return value
                else:
                    try:
                        arr = numpy.array(value)
                        return array2qimage(arr)
                    except Exception:
                        return value

        if role == Qt.BackgroundColorRole:
            if self.code_array.cell_attributes[key]["frozen"]:
                pattern_rgb = self.main_window.settings.freeze_color
                bg_color = QBrush(QColor(*pattern_rgb), Qt.BDiagPattern)
            else:
                bg_color_rgb = self.code_array.cell_attributes[key]["bgcolor"]
                bg_color = QColor(*bg_color_rgb)
            return bg_color

        if role == Qt.TextColorRole:
            text_color_rgb = self.code_array.cell_attributes[key]["textcolor"]
            return QColor(*text_color_rgb)

        if role == Qt.FontRole:
            attr = self.code_array.cell_attributes[key]
            text_font = attr["textfont"]
            pointsize = attr["pointsize"]
            fontweight = attr["fontweight"]
            italic = attr["fontstyle"]
            underline = attr["underline"]
            strikethrough = attr["strikethrough"]
            font = QFont(text_font, pointsize, fontweight, italic)
            font.setUnderline(underline)
            font.setStrikeOut(strikethrough)
            return font

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

    def setData(self, index, value, role, raw=False):
        """Overloaded setData for code_array backend"""

        if role == Qt.EditRole:
            if raw:
                self.code_array[self.current(index)] = value
            else:
                self.code_array[self.current(index)] = "{}".format(value)
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


class GridCellDelegate(QStyledItemDelegate):

    def __init__(self, main_window, code_array):
        super().__init__()

        self.main_window = main_window
        self.code_array = code_array
        self.cell_attributes = self.code_array.cell_attributes

    def _paint_bl_border_lines(self, x, y, width, height, painter, key):
        """Paint the bottom and the left border line of the cell"""

        border_bottom = (x, y + height, x + width, y + height)
        border_right = (x + width, y, x + width, y + height)

        bordercolor_bottom = self.cell_attributes[key]["bordercolor_bottom"]
        bordercolor_right = self.cell_attributes[key]["bordercolor_right"]

        borderwidth_bottom = self.cell_attributes[key]["borderwidth_bottom"]
        borderwidth_right = self.cell_attributes[key]["borderwidth_right"]

        painter.setPen(QPen(QBrush(QColor(*bordercolor_bottom)),
                            borderwidth_bottom))
        painter.drawLine(*border_bottom)

        painter.setPen(QPen(QBrush(QColor(*bordercolor_right)),
                            borderwidth_right))
        painter.drawLine(*border_right)

    def _paint_border_lines(self, rect, painter, index):
        """Paint border lines around the cell

        First, bottom and right border lines are painted.
        Next, border lines of the cell above are painted.
        Next, border lines of the cell left are painted.
        Finally, bottom and right border lines of the cell above left
        are painted.

        """

        x = rect.x() - 1
        y = rect.y() - 1
        width = rect.width()
        height = rect.height()

        row = index.row()
        column = index.column()
        table = self.main_window.grid.table

        # Paint bottom and right border lines of the current cell
        key = row, column, table
        self._paint_bl_border_lines(x, y, width, height, painter, key)

        # Paint bottom and right border lines of the cell above
        key = row - 1, column, table
        self._paint_bl_border_lines(x, y - height, width, height, painter, key)

        # Paint bottom and right border lines of the cell left
        key = row, column - 1, table
        self._paint_bl_border_lines(x - width, y, width, height, painter, key)

        # Paint bottom and right border lines of the current cell
        key = row - 1, column - 1, table
        self._paint_bl_border_lines(x - width, y - height, width, height,
                                    painter, key)

    def _render_markup(self, painter, option, index):
        """HTML markup renderer"""

        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        if options.widget is None:
            style = QApplication.style()
        else:
            style = options.widget.style()

        doc = QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(options.rect.width())

        options.text = ""
        style.drawControl(QStyle.CE_ItemViewItem, options, painter,
                          options.widget)

        ctx = QAbstractTextDocumentLayout.PaintContext()

        html_rect = style.subElementRect(QStyle.SE_ItemViewItemText, options,
                                         options.widget)
        painter.save()
        painter.translate(html_rect.topLeft())
        painter.setClipRect(html_rect.translated(-html_rect.topLeft()))
        doc.documentLayout().draw(painter, ctx)

        painter.restore()

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

            inner_aspect = inner_width / inner_height
            outer_aspect = outer_width / outer_height

            if outer_aspect < inner_aspect:
                inner_width *= outer_width / inner_width
                inner_height = inner_width / inner_aspect
            else:
                inner_height *= outer_height / inner_height
                inner_width = inner_height * inner_aspect

            return inner_width, inner_height

        key = index.row(), index.column(), self.main_window.grid.table

        justification = self.cell_attributes[key]["justification"]
        vertical_align = self.cell_attributes[key]["vertical_align"]

        if justification == "justify_fill":
            return option.rect

        rect_x, rect_y = option.rect.x(), option.rect.y()
        rect_width, rect_height = option.rect.width(), option.rect.height()

        image_width, image_height = scale_size(image_width, image_height,
                                               rect_width, rect_height)
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

        rect = option.rect

        if isinstance(qimage, BasicQImage):
            img_width, img_height = qimage.width(), qimage.height()
        else:
            key = index.row(), index.column(), self.main_window.grid.table
            res = self.code_array[key]
            if res is None:
                return
            try:
                svg_bytes = bytes(res)
            except TypeError:
                svg_bytes = bytes(res, encoding='utf-8')

            if not is_svg(svg_bytes):
                return
            else:
                svg_aspect = get_svg_aspect(svg_bytes)
                rect_aspect = rect.width() / rect.height()
                if svg_aspect > rect_aspect:
                    img_width = rect.width()
                    img_height = int(rect.width() / svg_aspect)
                else:
                    img_width = int(rect.height() * svg_aspect)
                    img_height = rect.height()

                qimage = QImage(img_width, img_height, QImage.Format_ARGB32)
                qimage.from_svg_bytes(svg_bytes)

        img_rect = self._get_aligned_image_rect(option, index,
                                                img_width, img_height)
        if img_rect is None:
            return

        key = index.row(), index.column(), self.main_window.grid.table
        justification = self.cell_attributes[key]["justification"]

        if justification == "justify_fill":
            qimage = qimage.scaled(rect.width(), rect.height(),
                                   Qt.IgnoreAspectRatio,
                                   Qt.SmoothTransformation)
            painter.drawImage(rect.x(), rect.y(), qimage)
            return

        qimage = qimage.scaled(rect.width(), rect.height(),
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)

        painter.drawImage(img_rect.x(), img_rect.y(), qimage)

    def _render_matplotlib(self, painter, option, index):
        """Matplotlib renderer"""

        if matplotlib_figure is None:
            # matplotlib is not installed
            return

        key = index.row(), index.column(), self.main_window.grid.table
        figure = self.code_array[key]

        if not isinstance(figure, matplotlib_figure.Figure):
            return

        dpi = figure.get_dpi()
        width, height = figure.get_size_inches()
        width *= dpi
        height *= dpi

        rect = self._get_aligned_image_rect(option, index, width, height)
        if rect is None:
            return

        image = QImage(rect.width(), rect.height(), QImage.Format_RGBA8888)
        image.from_matplotlib(figure)

        painter.drawImage(rect.x(), rect.y(), image)

    def __paint(self, painter, option, index):
        """Calls the overloaded paint function or creates html delegate"""

        key = index.row(), index.column(), self.main_window.grid.table
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

        key = index.row(), index.column(), self.main_window.grid.table
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
        painter.save()
        painter.translate(rectCenter.x(), rectCenter.y())
        painter.rotate(angle)
        painter.translate(-rectCenter.x(), -rectCenter.y())
        optionCopy.rect = painter.worldTransform().mapRect(option.rect)

        # Call the base class paint method
        self.__paint(painter, optionCopy, index)

        painter.restore()

    def paint(self, painter, option, index):
        """Overloads QStyledItemDelegate to add cell border painting"""

        key = index.row(), index.column(), self.main_window.grid.table
        angle = self.cell_attributes[key]["angle"]
        if abs(angle) < 0.001:
            # No rotation --> call the base class paint method
            self.__paint(painter, option, index)
        else:
            self._rotated_paint(painter, option, index, angle)

        self._paint_border_lines(option.rect, painter, index)

    def createEditor(self, parent, option, index):
        """Overloads QStyledItemDelegate

        Disables editor in frozen cells
        Switches to chart dialog in chart cells

        """

        key = index.row(), index.column(), self.main_window.grid.table

        if self.cell_attributes[key]["locked"]:
            return

        if self.cell_attributes[key]["renderer"] == "matplotlib":
            self.main_window.workflows.insert_chart()
            return

        return super(GridCellDelegate, self).createEditor(parent, option,
                                                          index)

    def setEditorData(self, editor, index):
        row = index.row()
        column = index.column()
        table = self.main_window.grid.table

        value = self.code_array((row, column, table))
        editor.setText(value)

    def setModelData(self, editor, model, index):
        description = "Set code for cell {}".format(model.current(index))
        command = CommandSetCellCode(editor.text(), model, index, description)
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

    def on_table_changed(self, current):
        """Event handler for table changes"""

        self.grid.update_cell_spans()
        self.grid.model.dataChanged.emit(QModelIndex(), QModelIndex())
