#!/usr/bin/python3
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

pyspread settings
=================

"""

from pathlib import Path

from PyQt5.QtCore import QSettings

VERSION = "1.99"


class Settings:
    """Holds all global application states"""

    # Names of widgets with persistant states
    widget_names = ['main_window', "main_toolbar", "find_toolbar",
                    "format_toolbar", "macro_toolbar", "widget_toolbar"]

    # Note that safe_mode is not listed here but inside model.DataArray

    shape = 1000, 100, 3  # Shape of initial grid (rows, columns, tables)
    changed_since_save = False  # If True then File actions trigger a dialog
    last_file_input_path = Path.home()  # Initial path for opening files
    last_file_output_path = Path.home()  # Initial path for saving files
    border_choice = "All borders"  # The state of the border choice button
    timeout = 1.0  # Timeout for cell calculations in seconds
    signature_key = None  # Key for signing save files

    font_sizes = 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32

    zoom_levels = (0.4, 0.5, 0.6, 0.7, 0.8, 1.0,
                   1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0)

    # TODO: Adjust in code
    sniff_size = 65536  # Number of bytes for csv sniffer
    #                     sniff_size should be larger than 1st+2nd line

    def __init__(self, parent):
        super().__setattr__("parent", parent)

    def __setattr__(self, key, value):
        if not hasattr(self, key):
            raise AttributeError("{self} has no attribute {key}.".format(
                                 self=self, key=key))
        super().__setattr__(key, value)

    def reset(self):
        cls_attrs = (attr for attr in dir(self)
                     if (not attr.startswith("__")
                         and attr not in ("reset", "parent", "save",
                                          "restore")))
        for cls_attr in cls_attrs:
            setattr(self, cls_attr, getattr(Settings, cls_attr))

    def save(self):
        """Saves application states to QSettings"""

        settings = QSettings("pyspread", "pyspread")

        # Application state

        settings.setValue("last_file_input_path", self.last_file_input_path)
        settings.setValue("last_file_output_path", self.last_file_output_path)
        settings.setValue("timeout", self.timeout)
        settings.setValue("signature_key", self.signature_key)

        # GUI state

        for widget_name in self.widget_names:
            geometry_name = widget_name + '/geometry'
            widget_state_name = widget_name + '/windowState'

            if widget_name == "main_window":
                widget = self.parent
            else:
                widget = getattr(self.parent, widget_name)
            try:
                settings.setValue(geometry_name, widget.saveGeometry())
            except AttributeError:
                pass
            try:
                settings.setValue(widget_state_name, widget.saveState())
            except AttributeError:
                pass

        settings.sync()

    def restore(self):
        """Restores application states from QSettings"""

        settings = QSettings("pyspread", "pyspread")

        # Application state

        self.last_file_input_path = settings.value("last_file_input_path")
        self.last_file_output_path = settings.value("last_file_output_path")
        self.timeout = settings.value("timeout")
        self.signature_key = settings.value("signature_key")

        # GUI state

        for widget_name in self.widget_names:
            geometry_name = widget_name + '/geometry'
            widget_state_name = widget_name + '/windowState'

            if widget_name == "main_window":
                widget = self.parent
            else:
                widget = getattr(self.parent, widget_name)

            geometry = settings.value(geometry_name)
            if geometry:
                widget.restoreGeometry(geometry)
            widget_state = settings.value(widget_state_name)
            if widget_state:
                widget.restoreState(widget_state)
