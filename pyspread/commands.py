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

**Provides**

* :class:`SetGridSize`
* :class:`SetCellCode`
* :class:`SetCellFormat`
* :class:`SetCellMerge`
* :class:`SetCellRenderer`
* :class:`SetCellTextAlignment`
* :class:`SetColumnWidth`
* :class:`SetRowHeight`


"""

from copy import copy

from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtWidgets import QUndoCommand

from lib.selection import Selection
from widgets import CellButton


class SetGridSize(QUndoCommand):
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
        shapeselection = Selection([(0, 0)], [(rows-1, columns-1)], [], [], [])

        for row, column, table in code_array.keys():
            if not (table < tables and (row, column) in shapeselection):
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


class SetCellCode(QUndoCommand):
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
        with self.model.main_window.entry_line.disable_highlighter():
            for index, new_code in zip(self.indices, self.new_codes):
                self.model.setData(index, new_code, Qt.EditRole, raw=True)
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def undo(self):
        with self.model.main_window.entry_line.disable_highlighter():
            for index, old_code in zip(self.indices, self.old_codes):
                self.model.setData(index, old_code, Qt.EditRole, raw=True)
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


class SetRowsHeight(QUndoCommand):
    """Sets rows height in grid"""

    def __init__(self, grid, rows, table, old_height, new_height, description):
        super().__init__(description)

        self.grid = grid
        self.rows = rows
        self.table = table
        self.old_height = old_height
        self.new_height = new_height

        self.default_size = self.grid.verticalHeader().defaultSectionSize()

    def id(self):
        return 2  # Enable command merging

    def mergeWith(self, other):
        if self.rows != other.rows:
            return False
        self.new_height = other.new_height
        return True

    def redo(self):
        for row in self.rows:
            if self.new_height != self.default_size:
                self.grid.model.code_array.row_heights[(row, self.table)] = \
                    self.new_height / self.grid.zoom
            if self.grid.rowHeight(row) != self.new_height:
                with self.grid.undo_resizing_row():
                    self.grid.setRowHeight(row, self.new_height)

    def undo(self):
        for row in self.rows:
            if self.old_height == self.default_size:
                self.grid.model.code_array.row_heights.pop((row, self.table))
            else:
                self.grid.model.code_array.row_heights[(row, self.table)] = \
                    self.old_height / self.grid.zoom
            if self.grid.rowHeight(row) != self.old_height:
                with self.grid.undo_resizing_row():
                    self.grid.setRowHeight(row, self.old_height)


class SetColumnsWidth(QUndoCommand):
    """Sets column width in grid"""

    def __init__(self, grid, columns, table, old_width, new_width,
                 description):
        super().__init__(description)

        self.grid = grid
        self.columns = columns
        self.table = table
        self.old_width = old_width
        self.new_width = new_width

        self.default_size = self.grid.horizontalHeader().defaultSectionSize()

    def id(self):
        return 3  # Enable command merging

    def mergeWith(self, other):
        if self.columns != other.columns:
            return False
        self.new_width = other.new_width
        return True

    def redo(self):
        for column in self.columns:
            if self.new_width != self.default_size:
                self.grid.model.code_array.col_widths[(column, self.table)] =\
                    self.new_width / self.grid.zoom
            if self.grid.columnWidth(column) != self.new_width:
                with self.grid.undo_resizing_column():
                    self.grid.setColumnWidth(column, self.new_width)

    def undo(self):
        for column in self.columns:
            if self.old_width == self.default_size:
                self.grid.model.code_array.col_widths.pop((column, self.table))
            else:
                self.grid.model.code_array.col_widths[(column, self.table)] =\
                    self.old_width / self.grid.zoom
            if self.grid.columnWidth(column) != self.old_width:
                with self.grid.undo_resizing_column():
                    self.grid.setColumnWidth(column, self.old_width)


class InsertRows(QUndoCommand):
    """Inserts grid rows"""

    def __init__(self, grid, model, index, row, count, description):
        super().__init__(description)
        self.grid = grid
        self.model = model
        self.index = index
        self.first = self.row = row
        self.last = row + count
        self.count = count

    def redo(self):
        with self.model.inserting_rows(self.index, self.first, self.last):
            self.model.insertRows(self.row, self.count)
        self.grid.table_choice.on_table_changed(self.grid.current)

    def undo(self):
        with self.model.removing_rows(self.index, self.first, self.last):
            self.model.removeRows(self.row, self.count)
        self.grid.table_choice.on_table_changed(self.grid.current)


class DeleteRows(QUndoCommand):
    """Deletes grid rows"""

    def __init__(self, grid, model, index, row, count, description):
        super().__init__(description)
        self.grid = grid
        self.model = model
        self.index = index
        self.first = self.row = row
        self.last = row + count
        self.count = count

    def redo(self):
        # Store content of deleted rows
        self.old_row_heights = copy(self.model.code_array.row_heights)
        self.old_cell_attributes = copy(self.model.code_array.cell_attributes)
        self.old_code = {}
        rows = list(range(self.first, self.last+1))
        selection = Selection([], [], rows, [], [])
        for key in selection.cell_generator(self.model.shape, self.grid.table):
            self.old_code[key] = self.model.code_array(key)

        with self.model.removing_rows(self.index, self.first, self.last):
            self.model.removeRows(self.row, self.count)
        self.grid.table_choice.on_table_changed(self.grid.current)

    def undo(self):
        with self.model.inserting_rows(self.index, self.first, self.last):
            self.model.insertRows(self.row, self.count)
        self.model.code_array.dict_grid.row_heights = self.old_row_heights
        self.model.code_array.dict_grid.cell_attributes = \
            self.old_cell_attributes
        for key in self.old_code:
            self.model.code_array[key] = self.old_code[key]

        self.grid.table_choice.on_table_changed(self.grid.current)


class InsertColumns(QUndoCommand):
    """Inserts grid columns"""

    def __init__(self, grid, model, index, column, count, description):
        super().__init__(description)
        self.grid = grid
        self.model = model
        self.index = index
        self.column = column
        self.first = self.column = column
        self.last = column + count
        self.count = count

    def redo(self):
        with self.model.inserting_columns(self.index, self.first, self.last):
            self.model.insertColumns(self.column, self.count)
        self.grid.table_choice.on_table_changed(self.grid.current)

    def undo(self):
        with self.model.removing_rows(self.index, self.first, self.last):
            self.model.removeColumns(self.column, self.count)
        self.grid.table_choice.on_table_changed(self.grid.current)


class DeleteColumns(QUndoCommand):
    """Deletes grid columns"""

    def __init__(self, grid, model, index, column, count, description):
        super().__init__(description)
        self.grid = grid
        self.model = model
        self.index = index
        self.column = column
        self.first = self.column = column
        self.last = column + count
        self.count = count

    def redo(self):
        # Store content of deleted columns
        self.old_col_widths = copy(self.model.code_array.col_widths)
        self.old_cell_attributes = copy(self.model.code_array.cell_attributes)
        self.old_code = {}
        columns = list(range(self.first, self.last+1))
        selection = Selection([], [], [], columns, [])
        for key in selection.cell_generator(self.model.shape, self.grid.table):
            self.old_code[key] = self.model.code_array(key)

        with self.model.removing_columns(self.index, self.first, self.last):
            self.model.removeColumns(self.column, self.count)
        self.grid.table_choice.on_table_changed(self.grid.current)

    def undo(self):
        with self.model.inserting_columns(self.index, self.first, self.last):
            self.model.insertColumns(self.column, self.count)

        self.model.code_array.dict_grid.col_widths = self.old_col_widths
        self.model.code_array.dict_grid.cell_attributes = \
            self.old_cell_attributes
        for key in self.old_code:
            self.model.code_array[key] = self.old_code[key]

        self.grid.table_choice.on_table_changed(self.grid.current)


class InsertTable(QUndoCommand):
    """Inserts table"""

    def __init__(self, grid, model, table, description):
        super().__init__(description)
        self.grid = grid
        self.model = model
        self.table = table

    def redo(self):
        with self.grid.undo_resizing_row():
            with self.grid.undo_resizing_column():
                self.model.insertTable(self.table)
        self.grid.table_choice.on_table_changed(self.grid.current)

    def undo(self):
        with self.grid.undo_resizing_row():
            with self.grid.undo_resizing_column():
                self.model.removeTable(self.table)
        self.grid.table_choice.on_table_changed(self.grid.current)


class DeleteTable(QUndoCommand):
    """Deletes table"""

    def __init__(self, grid, model, table, description):
        super().__init__(description)
        self.grid = grid
        self.model = model
        self.table = table

    def redo(self):
        # Store content of deleted table
        self.old_row_heights = copy(self.model.code_array.row_heights)
        self.old_col_widths = copy(self.model.code_array.col_widths)
        self.old_cell_attributes = copy(self.model.code_array.cell_attributes)
        self.old_code = {}
        for key in self.model.code_array:
            if key[2] == self.table:
                self.old_code[key] = self.model.code_array(key)

        with self.grid.undo_resizing_row():
            with self.grid.undo_resizing_column():
                self.model.removeTable(self.table)
        self.grid.table_choice.on_table_changed(self.grid.current)

    def undo(self):
        with self.grid.undo_resizing_row():
            with self.grid.undo_resizing_column():
                self.model.insertTable(self.table)

                self.model.code_array.dict_grid.row_heights = \
                    self.old_row_heights
                self.model.code_array.dict_grid.col_widths = \
                    self.old_col_widths
                self.model.code_array.dict_grid.cell_attributes = \
                    self.old_cell_attributes
                for key in self.old_code:
                    self.model.code_array[key] = self.old_code[key]

        self.grid.table_choice.on_table_changed(self.grid.current)


class SetCellFormat(QUndoCommand):
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


class SetCellMerge(SetCellFormat):
    """Sets cell merges in grid"""

    def redo(self):
        self.model.setData(self.selected_idx, self.attr, Qt.DecorationRole)
        self.model.main_window.grid.update_cell_spans()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())

    def undo(self):
        self.model.code_array.cell_attributes.pop()
        self.model.main_window.grid.update_cell_spans()
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


class SetCellTextAlignment(SetCellFormat):
    """Sets cell text alignment in grid"""

    def redo(self):
        self.model.setData(self.selected_idx, self.attr, Qt.TextAlignmentRole)
        self.model.dataChanged.emit(QModelIndex(), QModelIndex())


class FreezeCell(QUndoCommand):
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


class ThawCell(FreezeCell):
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


class SetCellRenderer(QUndoCommand):
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


class MakeButtonCell(QUndoCommand):
    """Makes a button cell"""

    def __init__(self, grid, text, index, description):
        super().__init__(description)
        self.grid = grid
        self.text = text
        self.index = index
        self.key = self.index.row(), self.index.column(), self.grid.table

    def redo(self):
        row, column, table = self.key
        selection = Selection([], [], [], [], [(row, column)])
        ca = selection, table, {"button_cell": self.text}
        self.grid.model.setData([self.index], ca, Qt.DecorationRole)

        if table == self.grid.table:
            # Only add widget if we are in the right table
            button = CellButton(self.text, self.grid, self.key)
            self.grid.setIndexWidget(self.index, button)
            self.grid.widget_indices.append(self.index)

        self.grid.model.dataChanged.emit(self.index, self.index)

    def undo(self):
        if self.index not in self.grid.widget_indices:
            return

        row, column, table = self.key
        selection = Selection([], [], [], [], [(row, column)])
        ca = selection, table, {"button_cell": False}
        self.grid.model.setData([self.index], ca, Qt.DecorationRole)

        if table == self.grid.table:
            # Only remove widget if we are in the right table
            self.grid.setIndexWidget(self.index, None)
            self.grid.widget_indices.remove(self.index)
        self.grid.model.dataChanged.emit(self.index, self.index)


class RemoveButtonCell(QUndoCommand):
    """Removes a button cell"""

    def __init__(self, grid, index, description):
        super().__init__(description)
        self.grid = grid
        self.text = None
        self.index = index
        self.key = self.index.row(), self.index.column(), self.grid.table

    def redo(self):
        if self.index not in self.grid.widget_indices:
            return
        attr = self.grid.model.code_array.cell_attributes[self.key]
        self.text = attr["button_cell"]
        row, column, table = self.key
        selection = Selection([], [], [], [], [(row, column)])
        ca = selection, table, {"button_cell": False}
        self.grid.model.setData([self.index], ca, Qt.DecorationRole)

        if table == self.grid.table:
            # Only remove widget if we are in the right table
            self.grid.setIndexWidget(self.index, None)
            self.grid.widget_indices.remove(self.index)
        self.grid.model.dataChanged.emit(self.index, self.index)

    def undo(self):
        row, column, table = self.key
        selection = Selection([], [], [], [], [(row, column)])
        ca = selection, table, {"button_cell": self.text}
        self.grid.model.setData([self.index], ca, Qt.DecorationRole)

        if table == self.grid.table:
            # Only add widget if we are in the right table
            button = CellButton(self.text, self.grid, self.key)
            self.grid.setIndexWidget(self.index, button)
            self.grid.widget_indices.append(self.index)
        self.grid.model.dataChanged.emit(self.index, self.index)
