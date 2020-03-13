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


from os.path import abspath, dirname, join
from pathlib import Path

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QToolBar

from __init__ import VERSION, APP_NAME

PYSPREAD_DIRNAME = abspath(join(dirname(__file__), ".."))
PYSPREAD_PATH = Path(PYSPREAD_DIRNAME)
DOC_PATH = PYSPREAD_PATH / "share/doc"
TUTORIAL_PATH = DOC_PATH / "tutorial"
MANUAL_PATH = DOC_PATH / "manual"


class Settings:
    """Contains all global application states."""

    # Note that `safe_mode` is not listed here but inside
    # :class:`model.model.DataArray`

    # Names of widgets with persistant states
    widget_names = ["main_window", "main_toolbar", "find_toolbar",
                    "format_toolbar", "macro_toolbar", "entry_line",
                    "main_splitter"]

    # Shape of initial grid (rows, columns, tables)
    shape = 1000, 100, 3

    # Maximum shape of the grid
    maxshape = 1000000, 100000, 100

    # If `True` then File actions trigger a dialog
    changed_since_save = False

    # Initial :class:`~pathlib.Path` for opening files
    last_file_input_path = Path.home()

    # Initial :class:`~pathlib.Path` for saving files
    last_file_output_path = Path.home()

    # Maximum number of files in file history
    max_file_history = 5

    # Maximum number of files in file history
    file_history = []

    # Maximum length of code, for which the netry line enables highlighting
    highlighter_limit = 1000000

    # The state of the border choice button
    border_choice = "All borders"

    # Timeout for cell calculations in milliseconds
    timeout = 1000

    # Timeout for frozen cell updates in milliseconds
    refresh_timeout = 1000

    # Key for signing save files
    signature_key = None

    font_sizes = (6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32)

    zoom_levels = (0.4, 0.5, 0.6, 0.7, 0.8, 1.0,
                   1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0)

    print_zoom = None

    # If `True` then frozen cell background is striped
    show_frozen = False

    # Find dialog state - needs to be stored when dialog is closed
    find_dialog_state = None

    # Number of bytes for csv sniffer
    # sniff_size should be larger than 1st+2nd line
    sniff_size = 65536  # TODO

    def __init__(self, parent):
        super().__setattr__("parent", parent)

    def __setattr__(self, key, value):
        if not hasattr(self, key):
            raise AttributeError("{self} has no attribute {key}.".format(
                                 self=self, key=key))
        super().__setattr__(key, value)

    def add_to_file_history(self, filename):
        """Adds new file to history"""

        self.file_history = [f for f in self.file_history if f != filename]
        self.file_history.insert(0, filename)
        self.file_history = self.file_history[:self.max_file_history]

    def reset(self):
        cls_attrs = (attr for attr in dir(self)
                     if (not attr.startswith("__")
                         and attr not in ("reset", "parent", "save",
                                          "restore")))
        for cls_attr in cls_attrs:
            setattr(self, cls_attr, getattr(Settings, cls_attr))

    def save(self):
        """Saves application state to QSettings"""

        settings = QSettings(APP_NAME, APP_NAME)

        # Application state

        # Do not store the actual filename. Otherwise, after saving and closing
        # File -> Save would overwrite the last saved file.

        if self.last_file_input_path is not None:
            settings.setValue("last_file_input_path",
                              self.last_file_input_path.parent)
        if self.last_file_output_path is not None:
            settings.setValue("last_file_output_path",
                              self.last_file_output_path.parent)
        settings.setValue("max_file_history", self.max_file_history)
        settings.value("file_history", [], 'QStringList')
        if self.file_history:
            settings.setValue("file_history", self.file_history)
        settings.setValue("timeout", self.timeout)
        settings.setValue("refresh_timeout", self.refresh_timeout)
        settings.setValue("signature_key", self.signature_key)

        # GUI state
        for widget_name in self.widget_names:

            if widget_name == "main_window":
                widget = self.parent
            else:
                widget = getattr(self.parent, widget_name)

            # geometry
            geometry_name = widget_name + '/geometry'
            try:
                settings.setValue(geometry_name, widget.saveGeometry())
            except AttributeError:
                pass

            # state
            widget_state_name = widget_name + '/windowState'
            try:
                settings.setValue(widget_state_name, widget.saveState())
            except AttributeError:
                pass

            if isinstance(widget, QToolBar):
                toolbar_visibility_name = widget_name + '/visibility'
                settings.value(toolbar_visibility_name, [], bool)
                settings.setValue(toolbar_visibility_name,
                                  [a.isVisible() for a in widget.actions()])

            if widget_name == "entry_line":
                settings.setValue("entry_line_isvisible", widget.isVisible())

        settings.sync()

    def restore(self):
        """Restores application state from QSettings"""

        settings = QSettings(APP_NAME, APP_NAME)

        def setting2attr(setting_name, attr=None, mapper=None):
            """Sets attr to mapper(<Setting from setting_name>)"""

            value = settings.value(setting_name)
            if value is None:
                return
            if attr is None:
                attr = setting_name
            if mapper is None:
                def mapper(x): return x
            setattr(self, attr, mapper(value))

        # Application state

        setting2attr("last_file_input_path")
        setting2attr("last_file_output_path")
        setting2attr("max_file_history", mapper=int)
        setting2attr("file_history")
        setting2attr("timeout", mapper=int)
        setting2attr("refresh_timeout", mapper=int)
        setting2attr("signature_key")

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

            if isinstance(widget, QToolBar):
                toolbar_visibility_name = widget_name + '/visibility'
                visibility = settings.value(toolbar_visibility_name)
                if visibility is not None:
                    for is_visible, action in zip(visibility,
                                                  widget.actions()):
                        action.setVisible(is_visible == 'true')
                manager_button = widget.widgetForAction(widget.actions()[-1])
                manager_button.menu().update_checked_states()

            if widget_name == "entry_line" \
               and settings.value("entry_line_isvisible") is not None:
                visible = settings.value("entry_line_isvisible") == "true"
                widget.setVisible(visible)
