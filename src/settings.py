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

from PyQt5.QtCore import QSettings

VERSION = "1.99"


class DefaultSettings:
    """Default settings for pyspread

    These settings may be overridden by stored QSettings

    """

    config_version = VERSION  # Config file version

    max_unredo = 5000
    timeout = 10  # Cell calculation timeout in s
    timer_interval = 1000

    ui_language = 'en'  # 'system' for system locale
    check_spelling = False  # Spell checking toggle
    spell_lang = 'en_US'  # Spell checking language

    default_open_filetype = 'pysu'
    default_save_filetype = 'pysu'

    window_position = 10, 10
    window_size = 800, 600
    window_layout = ''
    icon_theme = 'Tango'
    help_window_position = 50, 50
    help_window_size = 600, 400

    grid_rows = 1000
    grid_columns = 100
    grid_tables = 3

    default_row_height = 23
    default_col_width = 80

    max_result_length = 100000  # Maximum result length in a cell in characters

    grid_color = 192, 192, 192
    background_color = 255, 255, 255
    text_color = 0, 0, 0
    freeze_color = 0, 0, 255

    font = "Sans"
    font_save_enabled = "False"

    font_default_size = 10  # Default cell font size
    font_default_sizes = [6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32]

    minimum_zoom = 0.25
    maximum_zoom = 8.0
    zoom_factor = 0.05  # Increase and decrease factor on zoom in and zoom out

    signature_key = b''

    sniff_size = 65536  # Number of bytes for csv sniffer
    #                     sniff_size should be larger than 1st+2nd line
    max_textctrl_length = 65534  # Maximum number of characters in wx.TextCtrl


class Settings:
    """QT5 settings accessor"""

    qsettings = QSettings("pyspread", "pyspread")
    defaults = DefaultSettings()

    def __getattr__(self, name):

        try:
            value = self.qsettings.value(name)
            if value is not None:
                return value
        except AttributeError:
            pass  # Attribute not in stored settings

        return getattr(self.defaults, name)

    def __setattr__(self, name, value):
        self.qsettings.setValue(name, value)
        self.qsettings.sync()
