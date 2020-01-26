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
Grid selection representation
==============================

* :class:`Selection`: Represents grid selection independently from PyQt

"""
from builtins import zip
from builtins import range
from builtins import object


class Selection(object):
    """Represents grid selection

    Parameters
    ----------

    block_top_left: List of 2-tuples
    \tTop left edges of all selection rectangles
    block_bottom_right: List of 2-tuples
    \tBottom right edges of all selection rectangles
    rows: List
    \tList of selected rows
    cols: List
    \tList of selected columns
    cells: List of 2-tuples
    \tList of (row, column) tuples of individually selected cells

    """

    def __init__(self, block_top_left, block_bottom_right, rows, cols, cells):
        self.block_tl = block_top_left
        self.block_br = block_bottom_right
        self.rows = rows
        self.cols = cols
        self.cells = cells

    def __bool__(self):
        """Returns True iif any attribute is non-empty"""

        return any(self.parameters)

    def __repr__(self):
        """String output for printing selection"""

        return "Selection" + repr(self.parameters)

    def __eq__(self, other):
        """Returns True if self and other selection are equal

        Selections are equal iif the order of each attribute is equal
        because order precedence may change the selection outcome in the grid.

        """

        attrs = ("block_tl", "block_br", "rows", "cols", "cells")

        return all(getattr(self, at) == getattr(other, at) for at in attrs)

    def __contains__(self, cell):
        """Returns True iif cell is in selection

        Parameters
        ----------

        cell: 2-Tuple
        \tIndex of cell that is checked if it is inside selection.

        """

        assert len(cell) == 2

        cell_row, cell_col = cell

        # Block selections
        for top_left, bottom_right in zip(self.block_tl, self.block_br):
            top, left = top_left
            bottom, right = bottom_right

            if top is None:
                top = 0

            if left is None:
                left = 0

            if bottom is None:
                bottom = cell_row

            if right is None:
                right = cell_col

            if top <= cell_row <= bottom and left <= cell_col <= right:
                return True

        # Row and column selections

        if cell_row in self.rows or cell_col in self.cols:
            return True

        # Cell selections
        if cell in self.cells:
            return True

        return False

    def __add__(self, value):
        """Shifts selection down and / or right

        Parameters
        ----------

        value: 2-tuple
        \tRows and cols to be shifted up

        """

        def shifted_block(block0, block1, delta_row, delta_col):
            """Returns shifted block"""

            try:
                row = block0 + delta_row
            except TypeError:
                row = block0

            try:
                col = block1 + delta_col
            except TypeError:
                col = block1

            return row, col

        delta_row, delta_col = value

        block_tl = [shifted_block(t, l, delta_row, delta_col)
                    for t, l in self.block_tl]

        block_br = [shifted_block(b, r, delta_row, delta_col)
                    for b, r in self.block_br]

        rows = [row + delta_row for row in self.rows]
        cols = [col + delta_col for col in self.cols]
        cells = [(r + delta_row, c + delta_col) for r, c in self.cells]

        return Selection(block_tl, block_br, rows, cols, cells)

    def __and__(self, other):
        """Returns intersection selection of self and other"""

        block_tl = []
        block_br = []
        rows = []
        cols = []
        cells = []

        # Blocks
        # Check cells in block: If all are in other, add block else add cells

        for block in zip(self.block_tl, self.block_br):
            if block[0] in other.block_tl and block[1] in other.block_br:
                block_tl.append(block[0])
                block_br.append(block[1])
            else:
                block_cells = []
                for row in range(block[0][0], block[1][0] + 1):
                    for col in range(block[0][1], block[1][1] + 1):
                        cell = row, col
                        if cell in other:
                            block_cells.append(cell)

                if len(block_cells) == (block[1][0] + 1 - block[0][0]) * \
                                       (block[1][1] + 1 - block[0][1]):
                    block_tl.append(block[0])
                    block_br.append(block[1])
                else:
                    cells.extend(block_cells)

        # Rows
        # If a row/col is selected in self and other then add it.
        # Otherwise, add all cells in the respective row/col that are in other.

        for row in self.rows:
            if row in other.rows:
                rows.append(row)
            else:
                for block in zip(other.block_tl, other.block_br):
                    if block[0][0] <= row <= block[1][0]:
                        block_tl.append((row, block[0][1]))
                        block_br.append((row, block[1][1]))

                for cell in other.cells:
                    if cell[0] == row and cell not in cells:
                        cells.append(cell)

        # Columns

        for col in self.cols:
            if col in other.cols:
                cols.append(col)
            else:
                for block in zip(other.block_tl, other.block_br):
                    if block[0][1] <= col <= block[1][1]:
                        block_tl.append((block[0][0], col))
                        block_br.append((block[1][0], col))

                for cell in other.cells:
                    if cell[1] == col and cell not in cells:
                        cells.append(cell)

        # Cells

        for cell in self.cells:
            if cell in other and cell not in cells:
                cells.append(cell)

        cells = list(set(cells))

        return Selection(block_tl, block_br, rows, cols, cells)

    # Parameter access

    @property
    def parameters(self):
        """Returns tuple of selection parameters of self

        (self.block_tl, self.block_br, self.rows, self.cols, self.cells)

        """

        return self.block_tl, self.block_br, self.rows, self.cols, self.cells

    def insert(self, point, number, axis):
        """Inserts number of rows/cols/tabs into selection at point on axis
        Parameters
        ----------

        point: Integer
        \tAt this point the rows/cols are inserted or deleted
        number: Integer
        \tNumber of rows/cols to be inserted, negative number deletes
        axis: Integer in 0, 1
        \tDefines whether rows or cols are affected

        """

        def build_tuple_list(source_list, point, number, axis):
            """Returns adjusted tuple list for single cells"""

            target_list = []

            for tl in source_list:
                tl_list = list(tl)
                if tl[axis] > point:
                    tl_list[axis] += number
                target_list.append(tuple(tl_list))

            return target_list

        if number == 0:
            return

        self.block_tl = build_tuple_list(self.block_tl, point, number, axis)

        self.block_br = build_tuple_list(self.block_br, point, number, axis)

        if axis == 0:
            self.rows = \
                [row + number if row > point else row for row in self.rows]
        elif axis == 1:
            self.cols = \
                [col + number if col > point else col for col in self.cols]
        else:
            raise ValueError("Axis not in [0, 1]")

        self.cells = build_tuple_list(self.cells, point, number, axis)

    def get_bbox(self):
        """Returns ((top, left), (bottom, right)) of bounding box

        A bounding box is the smallest rectangle that contains all selections.
        Non-specified boundaries are None.

        """

        bb_top, bb_left, bb_bottom, bb_right = [None] * 4

        # Block selections

        for top_left, bottom_right in zip(self.block_tl, self.block_br):
            top, left = top_left
            bottom, right = bottom_right

            if bb_top is None or bb_top > top:
                bb_top = top
            if bb_left is None or bb_left > left:
                bb_left = left
            if bb_bottom is None or bb_bottom < bottom:
                bb_bottom = bottom
            if bb_right is None or bb_right > right:
                bb_right = right

        # Row and column selections

        for row in self.rows:
            if bb_top is None or bb_top > row:
                bb_top = row
            if bb_bottom is None or bb_bottom < row:
                bb_bottom = row

        for col in self.cols:
            if bb_left is None or bb_left > col:
                bb_left = col
            if bb_right is None or bb_right < col:
                bb_right = col

        # Cell selections

        for cell in self.cells:
            cell_row, cell_col = cell

            if bb_top is None or bb_top > cell_row:
                bb_top = cell_row
            if bb_left is None or bb_left > cell_col:
                bb_left = cell_col
            if bb_bottom is None or bb_bottom < cell_row:
                bb_bottom = cell_row
            if bb_right is None or bb_right < cell_col:
                bb_right = cell_col

        if self.rows:
            bb_left = bb_right = None

        if self.cols:
            bb_top = bb_bottom = None

        return ((bb_top, bb_left), (bb_bottom, bb_right))

    def get_grid_bbox(self, shape):
        """Returns ((top, left), (bottom, right)) of bounding box

        A bounding box is the smallest rectangle that contains all selections.
        Non-specified boundaries are filled i from size.

        Parameters
        ----------

        shape: 3-Tuple of Integer
        \tGrid shape

        """

        (bb_top, bb_left), (bb_bottom, bb_right) = self.get_bbox()

        if bb_top is None:
            bb_top = 0
        if bb_left is None:
            bb_left = 0
        if bb_bottom is None:
            bb_bottom = shape[0]
        if bb_right is None:
            bb_right = shape[1]

        return ((bb_top, bb_left), (bb_bottom, bb_right))

    def get_access_string(self, shape, table):
        """Returns a string, with which the selection can be accessed

        Parameters
        ----------
        shape: 3-tuple of Integer
        \tShape of grid, for which the generated keys are valid
        table: Integer
        \tThird component of all returned keys. Must be in dimensions

        """

        rows, columns, tables = shape

        # Negative dimensions cannot be
        assert all(dim > 0 for dim in shape)

        # Current table has to be in dimensions
        assert 0 <= table < tables

        string_list = []

        # Block selections
        templ = "[(r, c, {}) for r in xrange({}, {}) for c in xrange({}, {})]"
        for (top, left), (bottom, right) in zip(self.block_tl, self.block_br):
            string_list += [templ.format(table, top, bottom + 1,
                                         left, right + 1)]

        # Fully selected rows
        template = "[({}, c, {}) for c in xrange({})]"
        for row in self.rows:
            string_list += [template.format(row, table, columns)]

        # Fully selected columns
        template = "[(r, {}, {}) for r in xrange({})]"
        for column in self.cols:
            string_list += [template.format(column, table, rows)]

        # Single cells
        for row, column in self.cells:
            string_list += [repr([(row, column, table)])]

        key_string = " + ".join(string_list)

        if len(string_list) == 0:
            return ""

        elif len(self.cells) == 1 and len(string_list) == 1:
            return "S[{}]".format(string_list[0][1:-1])

        else:
            template = "[S[key] for key in {} if S[key] is not None]"
            return template.format(key_string)

    def shifted(self, rows, cols):
        """Returns a new selection that is shifted by rows and cols.

        Negative values for rows and cols may result in a selection
        that addresses negative cells.

        Parameters
        ----------
        rows: Integer
        \tNumber of rows that the new selection is shifted down
        cols: Integer
        \tNumber of columns that the new selection is shifted right

        """

        shifted_block_tl = \
            [(row + rows, col + cols) for row, col in self.block_tl]
        shifted_block_br = \
            [(row + rows, col + cols) for row, col in self.block_br]
        shifted_rows = [row + rows for row in self.rows]
        shifted_cols = [col + cols for col in self.cols]
        shifted_cells = [(row + rows, col + cols) for row, col in self.cells]

        return Selection(shifted_block_tl, shifted_block_br, shifted_rows,
                         shifted_cols, shifted_cells)

    def get_right_borders_selection(self, border_choice):
        """Returns selection of cells that need to be adjusted on border change

        The cells that are contained in the selection are those, on which
        the right border attributes need to be adjusted on border line and
        border color changes.

        """

        (top, left), (bottom, right) = self.get_bbox()

        if border_choice == "All borders":
            return Selection([(top, left-1)], [(bottom, right)], [], [], [])

        elif border_choice == "Top border":
            return Selection([], [], [], [], [])

        elif border_choice == "Bottom border":
            return Selection([], [], [], [], [])

        elif border_choice == "Left border":
            return Selection([(top, left-1)], [(bottom, left-1)], [], [], [])

        elif border_choice == "Right border":
            return Selection([(top, right)], [(bottom, right)], [], [], [])

        elif border_choice == "Outer borders":
            return Selection([(top, right), (top, left-1)],
                             [(bottom, right), (bottom, left-1)], [], [], [])

        elif border_choice == "Inner borders":
            return Selection([(top, left)], [(bottom, right-1)], [], [], [])

        elif border_choice == "Top and bottom borders":
            return Selection([], [], [], [], [])

        else:
            raise ValueError("border_choice {} unknown.".format(border_choice))

    def get_bottom_borders_selection(self, border_choice):
        """Returns selection of cells that need to be adjusted on border change

        The cells that are contained in the selection are those, on which
        the bottom border attributes need to be adjusted on border line and
        border color changes.

        """

        (top, left), (bottom, right) = self.get_bbox()

        if border_choice == "All borders":
            return Selection([(top-1, left)], [(bottom, right)], [], [], [])

        elif border_choice == "Top border":
            return Selection([(top-1, left)], [(top-1, right)], [], [], [])

        elif border_choice == "Bottom border":
            return Selection([(bottom, left)], [(bottom, right)], [], [], [])

        elif border_choice == "Left border":
            return Selection([], [], [], [], [])

        elif border_choice == "Right border":
            return Selection([], [], [], [], [])

        elif border_choice == "Outer borders":
            return Selection([(top-1, left), (bottom, left)],
                             [(top-1, right), (bottom, right)], [], [], [])

        elif border_choice == "Inner borders":
            return Selection([(top, left)], [(bottom-1, right)], [], [], [])

        elif border_choice == "Top and bottom borders":
            return Selection([(top-1, left), (bottom, left)],
                             [(top-1, right), (bottom, right)], [], [], [])

        else:
            raise ValueError("border_choice {} unknown.".format(border_choice))

    def single_cell_selected(self):
        """Returns True iif a single cell is selected via self.cells"""

        return (not any((self.block_tl, self.block_br, self.rows, self.cols))
                and len(self.cells) == 1)

    def cell_generator(self, shape, table=None):
        """Returns a generator of cell key tuples

        :param shape: Grid shape
        :param table: Third component of each returned key

        If table is None 2-tuples (row, column) are yielded else 3-tuples

        """

        rows, columns, tables = shape

        (top, left), (bottom, right) = self.get_grid_bbox(shape)
        bottom = min(bottom, rows - 1)
        right = min(right, columns - 1)

        for row in range(top, bottom + 1):
            for column in range(left, right + 1):
                if (row, column) in self:
                    if table is None:
                        yield row, column
                    elif table < tables - 1:
                        yield row, column, table
