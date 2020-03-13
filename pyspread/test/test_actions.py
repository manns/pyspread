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
test_actions
============

Unit tests for actions in pyspread

"""

from contextlib import contextmanager
from os.path import abspath, dirname, join
from pathlib import Path
import sys

import py.test as pytest

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

pyspread_path = abspath(join(dirname(__file__) + "/.."))
sys.path.insert(0, pyspread_path)
from ..pyspread import MainWindow
sys.path.pop(0)

app = QApplication([])


class TestActions:
    """Unit tests for  file actions

    The tests launch a hidden application instance and check if the
    actions behave as they should from a user perspective.

    """

    def setup_method(self):
        """Sets up a basic pyspread instance"""

        class Args:
            file = None

        self.main_window = MainWindow(app, Args(), unit_test=True)

    param_test_file_new = [
        ((1, 1, 1), (1, 1, 1)),
        ((0, 0, 0), (1000, 100, 3)),
        ((9999999999, 0, 0), (1000, 100, 3)),
        ((1000000, 10000, 10), (1000000, 10000, 10)),
        ((1000, 100, 3), (1000, 100, 3)),
    ]

    @pytest.mark.parametrize("shape, res", param_test_file_new)
    def test_file_new(self, shape, res):
        """Unit test for File -> New"""

        self.main_window.unit_test_data = shape
        self.main_window.main_window_actions.new.trigger()
        assert self.main_window.grid.model.shape == res

    param_test_file_open = [
        ("test.pysu", True, False, "fig"),
        ("test.pysu", False, True, "fig"),
        ("test_invalid1.pysu", False, True, None),
        ("test_invalid2.pysu", False, True, None),
        ("xxx", False, False, None),
    ]

    @pytest.mark.parametrize("infilename, signed, safe_mode, res",
                             param_test_file_open)
    def test_file_open(self, infilename, signed, safe_mode, res):
        """Unit test for File -> Open"""

        infilepath = Path(__file__).parent / infilename

        self.main_window.unit_test_data = infilepath

        @contextmanager
        def signature():
            if signed:
                # Create signature
                self.main_window.safe_mode = False
                self.main_window.workflows.sign_file(infilepath)
                self.main_window.safe_mode = safe_mode

            yield

            if signed:
                # Remove signature
                sigpath = infilepath.with_suffix(infilepath.suffix + '.sig')
                sigpath.unlink()

        with signature():
            self.main_window.main_window_actions.open.trigger()

        code_array = self.main_window.grid.model.code_array

        if res is None:
            assert code_array((2, 1, 0)) is res
        else:
            assert code_array((2, 1, 0)).startswith(res)
        assert self.main_window.safe_mode == safe_mode

    def test_file_save(self):
        """Unit test for File -> Save"""

        grid = self.main_window.grid
        grid.model.setData(grid.currentIndex(), "'Test'", Qt.EditRole)

        assert self.main_window.settings.changed_since_save
        save_path = Path(__file__).parent / "save_test1.pysu"
        self.main_window.settings.last_file_input_path = save_path
        self.main_window.main_window_actions.save.trigger()

        assert save_path.with_suffix(save_path.suffix + ".sig").exists()

        save_path.with_suffix(save_path.suffix + ".sig").unlink()
        save_path.unlink()
