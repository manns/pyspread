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
test_grid_renderer
==================

Unit tests for grid_renderer.py

"""

from contextlib import contextmanager
from os.path import abspath, dirname, join
import sys

import pytest

from PyQt5.QtWidgets import QApplication

PYSPREADPATH = abspath(join(dirname(__file__) + "/.."))
LIBPATH = abspath(PYSPREADPATH + "/lib")


@contextmanager
def insert_path(path):
    sys.path.insert(0, path)
    yield
    sys.path.pop(0)


with insert_path(PYSPREADPATH):
    from ..pyspread import MainWindow
    from ..grid_renderer import GridCellNavigator

app = QApplication.instance()
if app is None:
    app = QApplication([])
main_window = MainWindow()


class TestGridCellNavigator:
    """Unit tests for GridCellNavigator in grid_renderer.py"""

    grid = main_window.grid

    param_test_above_keys = [
        ((0, 0, 0), [(-1, 0, 0)]),
        ((20, 0, 0), [(19, 0, 0)]),
        ((20, 0, 2), [(19, 0, 2)]),
        ((20, 2, 2), [(19, 2, 2)]),
    ]

    @pytest.mark.parametrize("key, res", param_test_above_keys)
    def test_above_keys(self, key, res):
        """Unit test for above_keys"""

        cell = GridCellNavigator(self.grid, key)
        assert set(cell.above_keys()) == set(res)

    param_test_below_keys = [
        ((0, 0, 0), [(1, 0, 0)]),
        ((1000, 0, 0), [(1001, 0, 0)]),
        ((20, 0, 2), [(21, 0, 2)]),
        ((20, 2, 2), [(21, 2, 2)]),
    ]

    @pytest.mark.parametrize("key, res", param_test_below_keys)
    def test_below_keys(self, key, res):
        """Unit test for below_keys"""

        cell = GridCellNavigator(self.grid, key)
        assert set(cell.below_keys()) == set(res)

    param_test_left_keys = [
        ((0, 0, 0), [(0, -1, 0)]),
        ((20, 0, 0), [(20, -1, 0)]),
        ((20, 0, 2), [(20, -1, 2)]),
        ((20, 2, 2), [(20, 1, 2)]),
    ]

    @pytest.mark.parametrize("key, res", param_test_left_keys)
    def test_left_keys(self, key, res):
        """Unit test for left_keys"""

        cell = GridCellNavigator(self.grid, key)
        assert set(cell.left_keys()) == set(res)

    param_test_right_keys = [
        ((0, 0, 0), [(0, 1, 0)]),
        ((20, 0, 0), [(20, 1, 0)]),
        ((20, 0, 2), [(20, 1, 2)]),
        ((20, 2, 2), [(20, 3, 2)]),
    ]

    @pytest.mark.parametrize("key, res", param_test_right_keys)
    def test_right_keys(self, key, res):
        """Unit test for right_keys"""

        cell = GridCellNavigator(self.grid, key)
        assert set(cell.right_keys()) == set(res)

    param_test_above_left_key = [
        ((0, 0, 0), (-1, -1, 0)),
        ((20, 0, 0), (19, -1, 0)),
        ((20, 0, 2), (19, -1, 2)),
        ((20, 2, 2), (19, 1, 2)),
    ]

    @pytest.mark.parametrize("key, res", param_test_above_left_key)
    def test_above_left_key(self, key, res):
        """Unit test for above_left_key"""

        cell = GridCellNavigator(self.grid, key)
        assert cell.above_left_key() == res

    param_test_above_right_key = [
        ((0, 0, 0), (-1, 1, 0)),
        ((20, 0, 0), (19, 1, 0)),
        ((20, 0, 2), (19, 1, 2)),
        ((20, 2, 2), (19, 3, 2)),
    ]

    @pytest.mark.parametrize("key, res", param_test_above_right_key)
    def test_above_right_key(self, key, res):
        """Unit test for above_right_key"""

        cell = GridCellNavigator(self.grid, key)
        assert cell.above_right_key() == res

    param_test_below_left_key = [
        ((0, 0, 0), (1, -1, 0)),
        ((20, 0, 0), (21, -1, 0)),
        ((20, 0, 2), (21, -1, 2)),
        ((20, 2, 2), (21, 1, 2)),
    ]

    @pytest.mark.parametrize("key, res", param_test_below_left_key)
    def test_below_left_key(self, key, res):
        """Unit test for below_left_key"""

        cell = GridCellNavigator(self.grid, key)
        assert cell.below_left_key() == res

    param_test_below_right_key = [
        ((0, 0, 0), (1, 1, 0)),
        ((20, 0, 0), (21, 1, 0)),
        ((20, 0, 2), (21, 1, 2)),
        ((20, 2, 2), (21, 3, 2)),
    ]

    @pytest.mark.parametrize("key, res", param_test_below_right_key)
    def test_below_right_key(self, key, res):
        """Unit test for below_right_key"""

        cell = GridCellNavigator(self.grid, key)
        assert cell.below_right_key() == res
