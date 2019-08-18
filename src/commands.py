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
Pyspread undoable commands
--------------------------

"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QUndoCommand


class CommandSetCellCode(QUndoCommand):
    """Sets cell code in grid"""

    def __init__(self, code, model, index, description):
        super().__init__(description)

        self.model = model
        self.index = index
        self.old_code = model.code(index)
        self.new_code = code

    def redo(self):
        self.model.setData(self.index, self.new_code, Qt.EditRole, raw=True)

    def undo(self):
        self.model.setData(self.index, self.old_code, Qt.EditRole, raw=True)


class CommandSetRowHeight(QUndoCommand):
    """Sets row height in grid"""

    def __init__(self, grid, row, table, old_height, new_height, description):
        super().__init__(description)

        self.grid = grid
        self.row = row
        self.table = table
        self.old_height = old_height
        self.new_height = new_height

    def id(self):
        return 1  # Enable command merging

    def mergeWith(self, other):
        if self.row != other.row:
            return False
        self.new_height = other.new_height
        return True

    def redo(self):
        if self.grid.rowHeight(self.row) != self.new_height:
            self.grid.undo_resizing_row = True
            self.grid.setRowHeight(self.row, self.new_height)
            self.grid.model.code_array.row_heights[(self.row, self.table)] = \
                self.new_height
            self.grid.undo_resizing_row = False

    def undo(self):
        if self.grid.rowHeight(self.row) != self.old_height:
            self.grid.undo_resizing_row = True
            self.grid.setRowHeight(self.row, self.old_height)
            self.grid.model.code_array.row_heights[(self.row, self.table)] = \
                self.old_height
            self.grid.undo_resizing_row = False


class CommandSetColumnWidth(QUndoCommand):
    """Sets column width in grid"""

    def __init__(self, grid, column, table, old_width, new_width, description):
        super().__init__(description)

        self.grid = grid
        self.column = column
        self.table = table
        self.old_width = old_width
        self.new_width = new_width

    def id(self):
        return 2  # Enable command merging

    def mergeWith(self, other):
        if self.column != other.column:
            return False
        self.new_width = other.new_width
        return True

    def redo(self):
        if self.grid.columnWidth(self.column) != self.new_width:
            self.grid.undo_resizing_column = True
            self.grid.setColumnWidth(self.column, self.new_width)
            self.grid.model.code_array.col_widths[(self.column, self.table)] =\
                self.new_width
            self.grid.undo_resizing_column = False

    def undo(self):
        if self.grid.columnWidth(self.column) != self.old_width:
            self.grid.undo_resizing_column = True
            self.grid.setColumnWidth(self.column, self.old_width)
            self.grid.model.code_array.col_widths[(self.column, self.table)] =\
                self.old_width
            self.grid.undo_resizing_column = False


class CommandSetCellFormat(QUndoCommand):
    """Sets cell format in grid"""

    def __init__(self, attr, model, index, selected_idx, description):
        super().__init__(description)

        self.attr = attr
        self.model = model
        self.index = index
        self.selected_idx = selected_idx

    def _update_cells(self):
        """Emits cell updates for all affected cells"""

        for idx in self.selected_idx:
            self.model.dataChanged.emit(idx, idx)

        border_attr_keys = ("bordercolor_bottom", "bordercolor_right",
                            "borderwidth_bottom", "borderwidth_right")
        if any(attr in self.attr[2] for attr in border_attr_keys):
            (top, left), (bottom, right) = self.attr[0].get_bbox()
            rowcols = []
            for row in range(top, bottom + 2):
                rowcols += [(row, left), (row, right+1), (row, left-1)]
            for column in range(left, right + 2):
                rowcols += [(top, column), (bottom+1, column)]
            for row, column in rowcols:
                idx = idx.sibling(row, column)
                self.model.dataChanged.emit(idx, idx)
        self.model.dataChanged.emit(self.index, self.index)

    def redo(self):
        self.model.setData(self.selected_idx, self.attr, Qt.DecorationRole)
        self._update_cells()

    def undo(self):
        self.model.code_array.cell_attributes.pop()
        self._update_cells()


class CommandSetCellTextAlignment(CommandSetCellFormat):
    """Sets cell text alignment in grid"""

    def redo(self):
        self.model.setData(self.selected_idx, self.attr, Qt.TextAlignmentRole)
        self.model.dataChanged.emit(self.index, self.index)


class CommandSetCellRenderer(QUndoCommand):
    """Sets cell renderer in grid"""

    def __init__(self, attr, model, entry_line, highlighter_document,
                 index, selected_idx, description):
        super().__init__(description)

        self.attr = attr
        self.model = model
        self.entry_line = entry_line
        self.new_highlighter_document = highlighter_document
        self.old_highlighter_document = self.entry_line.highlighter.document()
        self.index = index
        self.selected_idx = selected_idx

    def redo(self):
        self.model.setData(self.selected_idx, self.attr, Qt.DecorationRole)
        self.entry_line.highlighter.setDocument(self.new_highlighter_document)
        self.model.dataChanged.emit(self.index, self.index)

    def undo(self):
        self.model.code_array.cell_attributes.pop()
        self.entry_line.highlighter.setDocument(self.old_highlighter_document)
        self.model.dataChanged.emit(self.index, self.index)
