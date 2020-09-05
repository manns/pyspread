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
test_selection
==============

Unit tests for selection.py

"""

import pytest

from ..selection import Selection


class TestSelection:
    """Unit tests for Selection"""

    param_test_nonzero = [
        (Selection([], [], [], [], [(32), (34)]),),
        (Selection([], [], [], [], [(32, 53), (34, 56)]),),
        (Selection([], [], [], [3], []),),
        (Selection([], [], [2], [], []),),
        (Selection([(1, 43)], [(2, 354)], [], [], []),),
    ]

    @pytest.mark.parametrize("selection", param_test_nonzero)
    def test_nonzero(self, selection):
        """Unit test for __nonzero__"""

        assert selection

    def test_repr(self):
        """Unit test for __repr__"""

        selection = Selection([], [], [], [], [(32, 53), (34, 56)])
        assert str(selection) == \
            "Selection([], [], [], [], [(32, 53), (34, 56)])"

    param_test_eq = [
        (Selection([], [], [], [], [(32, 53), (34, 56)]),
         Selection([], [], [], [], [(32, 53), (34, 56)]),
         True),
        (Selection([], [], [], [], [(32, 53)]),
         Selection([], [], [], [], [(32, 53), (34, 56)]),
         False),
        (Selection([], [], [], [], [(34, 56), (32, 53)]),
         Selection([], [], [], [], [(32, 53), (34, 56)]),
         False),
        (Selection([], [], [3, 5], [1, 4], [(32, 53)]),
         Selection([], [], [5, 3], [1, 4], [(32, 53)]),
         False),
        (Selection([], [], [3, 5], [1, 4], [(32, 2343)]),
         Selection([], [], [5, 3], [1, 4], [(32, 53)]),
         False),
        (Selection([(2, 3), (9, 10)], [(5, 9), (100, 34)], [], [], []),
         Selection([(2, 3), (9, 10)], [(5, 9), (100, 34)], [], [], []),
         True),
        (Selection([(9, 10), (2, 3)], [(100, 34), (5, 9)], [], [], []),
         Selection([(2, 3), (9, 10)], [(5, 9), (100, 34)], [], [], []),
         False),
    ]

    @pytest.mark.parametrize("sel1, sel2, res", param_test_eq)
    def test_eq(self, sel1, sel2, res):
        """Unit test for __eq__"""

        assert (sel1 == sel2) == res
        assert (sel2 == sel1) == res

    param_test_contains = [
        # Cell selections
        (Selection([], [], [], [], [(32, 53), (34, 56)]), (32, 53), True),
        (Selection([], [], [], [], [(32, 53), (34, 56)]), (23, 34534534),
         False),
        # Block selections
        (Selection([(4, 5)], [(100, 200)], [], [], []), (4, 5), True),
        (Selection([(4, 5)], [(100, 200)], [], [], []), (99, 199), True),
        (Selection([(4, 5)], [(100, 200)], [], [], []), (100, 200), True),
        (Selection([(4, 5)], [(100, 200)], [], [], []), (0, 0), False),
        (Selection([(4, 5)], [(100, 200)], [], [], []), (0, 1), False),
        (Selection([(4, 5)], [(100, 200)], [], [], []), (1, 0), False),
        (Selection([(4, 5)], [(100, 200)], [], [], []), (4, 4), False),
        (Selection([(4, 5)], [(100, 200)], [], [], []), (3, 5), False),
        (Selection([(4, 5)], [(100, 200)], [], [], []), (100, 201), False),
        (Selection([(4, 5)], [(100, 200)], [], [], []), (10**10, 10**10),
         False),
        # Row selection
        (Selection([], [], [3], [], []), (0, 0), False),
        (Selection([], [], [3], [], []), (3, 0), True),
        (Selection([], [], [3, 5], [], []), (3, 0), True),
        (Selection([], [], [3, 5], [], []), (5, 0), True),
        (Selection([], [], [3, 5], [], []), (4, 0), False),
        # Column selection
        (Selection([], [], [], [2, 234, 434], []), (234, 234), True),
        (Selection([], [], [], [2, 234, 434], []), (234, 0), False),
        # Combinations
        (Selection([(0, 0)], [(90, 23)], [0], [0, 34], [((0, 0))]), (0, 0),
         True),
    ]

    @pytest.mark.parametrize("sel, key, res", param_test_contains)
    def test_contains(self, sel, key, res):
        """Unit test for __contains__

        Used in: ele in selection

        """

        assert (key in sel) == res

    param_test_add = [
        (Selection([], [], [], [], [(0, 0), (34, 56)]), (4, 5),
         Selection([], [], [], [], [(4, 5), (38, 61)])),
        (Selection([], [], [], [], [(0, 0), (34, 56)]), (0, 0),
         Selection([], [], [], [], [(0, 0), (34, 56)])),
        (Selection([], [], [], [], [(0, 0), (34, 56)]), (-3, -24),
         Selection([], [], [], [], [(-3, -24), (31, 32)])),
        (Selection([(2, 5)], [(4, 6)], [1], [0], [(0, 0), (34, 56)]), (1, 0),
         Selection([(3, 5)], [(5, 6)], [2], [0], [(1, 0), (35, 56)])),
    ]

    @pytest.mark.parametrize("sel, add, res", param_test_add)
    def test_add(self, sel, add, res):
        """Unit test for __add__"""

        val = sel + add
        assert val == res

    param_test_and = [
        (Selection([], [], [], [], []),
         Selection([], [], [], [], []),
         Selection([], [], [], [], [])),
        (Selection([], [], [], [], [(0, 0)]),
         Selection([], [], [], [], []),
         Selection([], [], [], [], [])),
        (Selection([], [], [], [], [(0, 0)]),
         Selection([], [], [], [], [(0, 0)]),
         Selection([], [], [], [], [(0, 0)])),
        (Selection([], [], [], [], [(0, 0)]),
         Selection([(0, 0)], [(5, 5)], [], [], []),
         Selection([], [], [], [], [(0, 0)])),
        (Selection([(0, 0)], [(1000, 200)], [], [], []),
         Selection([(0, 0)], [(1000, 200)], [], [], []),
         Selection([(0, 0)], [(1000, 200)], [], [], [])),
        (Selection([(0, 0)], [(1000, 200)], [], [], []),
         Selection([(1, 2)], [(10, 20)], [], [], []),
         [(1, 2), (10, 20)]),
        (Selection([(0, 0)], [(1000, 200)], [], [], []),
         Selection([], [], [(2)], [], []),
         [(2, 3), (2, 0), (2, 200)]),
        (Selection([(0, 0)], [(1000, 200)], [], [], []),
         Selection([], [], [], [(5)], []),
         [(0, 5), (1000, 5)]),
    ]

    @pytest.mark.parametrize("s1, s2, res", param_test_and)
    def test_and(self, s1, s2, res):
        """Unit test for __and__"""

        s1_and_s2 = s1 & s2
        if isinstance(res, list):
            for cell in res:
                assert cell in s1_and_s2
        else:
            assert s1_and_s2 == res

    param_test_insert = [
        (Selection([], [], [2], [], []), 1, 10, 0,
         Selection([], [], [12], [], [])),
        (Selection([], [], [], [], [(234, 23)]), 20, 4, 1,
         Selection([], [], [], [], [(234, 27)])),
        (Selection([], [], [21], [33, 44], [(234, 23)]), 40, 4, 1,
         Selection([], [], [21], [33, 48], [(234, 23)])),
    ]

    @pytest.mark.parametrize("sel, point, number, axis,res", param_test_insert)
    def test_insert(self, sel, point, number, axis, res):
        """Unit test for insert"""

        sel.insert(point, number, axis)
        assert sel == res

    param_test_get_bbox = [
        (Selection([], [], [], [], [(32, 53), (34, 56)]),
         ((32, 53), (34, 56))),
        (Selection([(4, 5)], [(100, 200)], [], [], []), ((4, 5), (100, 200))),
        (Selection([], [], [2], [3], []), ((None, None), (None, None))),
        (Selection([], [], [], [3], []), ((None, 3), (None, 3))),
    ]

    @pytest.mark.parametrize("sel, res", param_test_get_bbox)
    def test_get_bbox(self, sel, res):
        """Unit test for get_bbox"""

        assert sel.get_bbox() == res

    param_get_absolute_access_string = [
        (Selection([], [], [], [], [(32, 53), (34, 56)]), (1000, 100, 3), 0,
         "[S[key] for key in [(32, 53, 0)] + [(34, 56, 0)] "
         "if S[key] is not None]"),
        (Selection([], [], [4, 5], [53], []), (1000, 100, 3), 2,
         "[S[key] for key in [(4, c, 2) for c in range(100)] + "
         "[(5, c, 2) for c in range(100)] + [(r, 53, 2) for r in "
         "range(1000)] if S[key] is not None]"),
        (Selection([(0, 0), (2, 2)], [(1, 1), (7, 5)], [], [], []),
         (1000, 100, 3), 0,
         "[S[key] for key in [(r, c, 0) for r in range(0, 2) for c in "
         "range(0, 2)] + [(r, c, 0) for r in range(2, 8) for c in "
         "range(2, 6)] if S[key] is not None]"),
    ]

    @pytest.mark.parametrize("sel, shape, table, res",
                             param_get_absolute_access_string)
    def test_get_absolute_access_string(self, sel, shape, table, res):
        """Unit test for get_access_string"""

        assert sel.get_absolute_access_string(shape, table) == res

    param_test_shifted = [
        (Selection([], [], [], [], [(32, 53), (34, 56)]), 0, 0,
         Selection([], [], [], [], [(32, 53), (34, 56)])),
        (Selection([], [], [], [], [(32, 53), (34, 56)]), 1, 1,
         Selection([], [], [], [], [(33, 54), (35, 57)])),
        (Selection([], [], [], [], [(32, 53), (34, 56)]), -1, 0,
         Selection([], [], [], [], [(31, 53), (33, 56)])),
        (Selection([], [], [], [], [(32, 53), (34, 56)]), -1, -1,
         Selection([], [], [], [], [(31, 52), (33, 55)])),
        (Selection([], [], [], [], [(32, 53), (34, 56)]), -1, 1,
         Selection([], [], [], [], [(31, 54), (33, 57)])),
        (Selection([], [], [], [], [(32, 53), (34, 56)]), -100, 100,
         Selection([], [], [], [], [(-68, 153), (-66, 156)])),
        (Selection([(0, 0), (1, 1)], [(10, 10), (50, 50)], [], [], []), 1, 0,
         Selection([(1, 0), (2, 1)], [(11, 10), (51, 50)], [], [], [])),
        (Selection([], [], [1, 4, 6], [3, 4], []), 2, 1,
         Selection([], [], [3, 6, 8], [4, 5], [])),
    ]

    @pytest.mark.parametrize("sel, rows, cols, res", param_test_shifted)
    def test_shifted(self, sel, rows, cols, res):
        """Unit test for shifted"""

        assert sel.shifted(rows, cols) == res

    param_test_single_cell_selected = [
        (Selection([], [], [], [], [(32, 53)]), True),
        (Selection([], [], [], [], [(32, 53), (34, 56)]), False),
        (Selection([(0, 0)], [(2, 2)], [], [], []), False),
        (Selection([], [], [(1, 2)], [], []), False),
        (Selection([], [], [], [(1, 2)], []), False),
    ]

    @pytest.mark.parametrize("sel, res", param_test_single_cell_selected)
    def test_single_cell_selected(self, sel, res):
        """Unit test for single_cell_selected"""

        assert sel.single_cell_selected() is res

    param_test_cell_generator = [
        (Selection([], [], [], [], [(32, 53), (34, 56)]), (200, 200, 1), None,
         set([(32, 53), (34, 56)])),
        (Selection([], [], [], [], [(32, 53), (34, 56)]), (1, 1, 1), None,
         set()),
        (Selection([], [], [(2)], [], []), (20, 20, 3), None,
         set([(2, i) for i in range(20)])),
        (Selection([], [], [2], [3], []), (4, 4, 3), None,
         set([(2, i) for i in range(4)] + [(i, 3) for i in range(4)])),
    ]

    @pytest.mark.parametrize("sel, shape, tab, res", param_test_cell_generator)
    def test_cell_generator(self, sel, shape, tab, res):
        """Unit test for cell_generator"""

        assert set(sel.cell_generator(shape, tab)) == res
