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

from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtWidgets import QUndoCommand

from lib.selection import Selection


class CommandSetGridSize(QUndoCommand):
    """Sets size of grid"""

    def __init__(self, grid, old_shape, new_shape, description):
        super().__init__(description)

        self.grid = grid
        self.old_shape = old_shape
        self.new_shape = new_shape

        self.deleted_cells = {}  # Storage dict for deleted cells

    def redo(self):
        """Changes grid size and deletes cell code outside the new shape

        Cell formats are not deleted.

        """

        model = self.grid.model
        code_array = model.code_array

        rows, columns, tables = self.new_shape
        shape_selection = Selection([(0, 0)], [(rows, columns)], [], [], [])

        for row, column, table in code_array.keys():
            if not (table < tables and (row, column) in shape_selection):
                # Code outside grid shape. Delete it and store cell data
                key = row, column, table
                self.deleted_cells[key] = code_array.pop(key)

        # Now change the shape
        self.grid.model.shape = self.new_shape

    def undo(self):
        """Restores grid size and adds cell code outside the old shape

        Cell formats are not affected.

        """
        model = self.grid.model

        model.shape = self.old_shape

        for row, column, table in self.deleted_cells:
            index = model.index(row, column, QModelIndex())
            code = self.deleted_cells[(row, column, table)]
            model.setData(index, code, Qt.EditRole, raw=True, table=table)


class CommandSetCellCode(QUndoCommand):
    """Sets cell code in grid"""

    def __init__(self, code, model, index, description):
        super().__init__(description)

        self.description = description
        self.model = model
        self.indices = [index]
        self.old_codes = [model.code(index)]
        self.new_codes = [code]

    def id(self):
        return 1  # Enable command merging

    def mergeWith(self, other):
        if self.description != other.description:
            return False
        self.new_codes += other.new_codes
        self.old_codes += other.old_codes
        self.indices += other.indices
        return True

    def redo(self):
        for index, new_code in zip(self.indices, self.new_codes):
            self.model.setData(index, new_code, Qt.EditRole, raw=True)

    def undo(self):
        for index, old_code in zip(self.indices, self.old_codes):
            self.model.setData(index, old_code, Qt.EditRole, raw=True)


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
        return 2  # Enable command merging

    def mergeWith(self, other):
        if self.row != other.row:
            return False
        self.new_height = other.new_height
        return True

    def redo(self):
        if self.new_height != self.grid.verticalHeader().defaultSectionSize():
            self.grid.model.code_array.row_heights[(self.row, self.table)] = \
                self.new_height / self.grid.zoom
        if self.grid.rowHeight(self.row) != self.new_height:
            self.grid.undo_resizing_row = True
            self.grid.setRowHeight(self.row, self.new_height)
            self.grid.undo_resizing_row = False

    def undo(self):
        if self.old_height == self.grid.verticalHeader().defaultSectionSize():
            self.grid.model.code_array.row_heights.pop((self.row, self.table))
        else:
            self.grid.model.code_array.row_heights[(self.row, self.table)] = \
                self.old_height / self.grid.zoom
        if self.grid.rowHeight(self.row) != self.old_height:
            self.grid.undo_resizing_row = True
            self.grid.setRowHeight(self.row, self.old_height)
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
        return 3  # Enable command merging

    def mergeWith(self, other):
        if self.column != other.column:
            return False
        self.new_width = other.new_width
        return True

    def redo(self):
        if self.new_width != self.grid.horizontalHeader().defaultSectionSize():
            self.grid.model.code_array.col_widths[(self.column, self.table)] =\
                self.new_width / self.grid.zoom
        if self.grid.columnWidth(self.column) != self.new_width:
            self.grid.undo_resizing_column = True
            self.grid.setColumnWidth(self.column, self.new_width)
            self.grid.undo_resizing_column = False

    def undo(self):
        if self.old_width == self.grid.horizontalHeader().defaultSectionSize():
            self.grid.model.code_array.col_widths.pop((self.column,
                                                       self.table))
        else:
            self.grid.model.code_array.col_widths[(self.column, self.table)] =\
                self.old_width / self.grid.zoom
        if self.grid.columnWidth(self.column) != self.old_width:
            self.grid.undo_resizing_column = True
            self.grid.setColumnWidth(self.column, self.old_width)
            self.grid.undo_resizing_column = False


class CommandSetCellFormat(QUndoCommand):
    """Sets cell format in grid"""

    def __init__(self, attr, model, index, selected_idx, description):
        super().__init__(description)

        self.attr = attr
        self.model = model
        self.index = index
        self.selected_idx = selected_idx

    def redo(self):
        self.model.setData(self.selected_idx, self.attr, Qt.DecorationRole)
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def undo(self):
        self.model.code_array.cell_attributes.pop()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


class CommandSetCellMerge(CommandSetCellFormat):
    """Sets cell merges in grid"""

    def _update_cells(self):
        """Updates cell spands and emits cell change event"""

        self.model.main_window.grid.update_cell_spans()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


class CommandSetCellTextAlignment(CommandSetCellFormat):
    """Sets cell text alignment in grid"""

    def redo(self):
        self.model.setData(self.selected_idx, self.attr, Qt.TextAlignmentRole)
        self._update_cells()


class CommandFreezeCell(QUndoCommand):
    """Freezes cell in grid"""

    def __init__(self, model, current, description):
        super().__init__(description)

        self.model = model
        self.current = current

    def redo(self):
        row, column, table = self.current

        # Add frozen cache content
        res_obj = self.model.code_array[self.current]
        self.model.code_array.frozen_cache[repr(self.current)] = res_obj

        # Set the frozen state
        selection = Selection([], [], [], [], [(row, column)])
        attr = selection, table, {"frozen": True}
        self.model.setData([], attr, Qt.DecorationRole)
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def undo(self):
        self.model.code_array.frozen_cache.pop(repr(self.current))
        self.model.code_array.cell_attributes.pop()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


class CommandThawCell(CommandFreezeCell):
    """Thaw (unfreezes) cell in grid"""

    def redo(self):
        row, column, table = current = self.current

        # Remove and store frozen cache content
        self.res_obj = self.model.code_array.frozen_cache.pop(repr(current))

        # Remove the frozen state
        selection = Selection([], [], [], [], [(row, column)])
        attr = selection, table, {"frozen": False}
        self.model.setData([], attr, Qt.DecorationRole)
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def undo(self):
        self.model.code_array.frozen_cache[repr(self.current)] = self.res_obj
        self.model.code_array.cell_attributes.pop()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


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
