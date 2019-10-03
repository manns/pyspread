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


from PyQt5.QtWidgets import QToolBar, QToolButton, QUndoView, QMenu
from PyQt5.QtWidgets import QHBoxLayout

try:
    import matplotlib.figure as matplotlib_figure
except ImportError:
    matplotlib_figure = None

from icons import Icon


def add_toolbutton_widget(button, widget, minsize=(300, 200),
                          popup_mode=QToolButton.MenuButtonPopup):
    """Adds a widget as menu to a tool_button"""

    button.setPopupMode(popup_mode)
    menu = QMenu(button)
    menu.setMinimumSize(*minsize)
    button.setMenu(menu)
    menu_layout = QHBoxLayout()
    menu_layout.addWidget(widget)
    menu.setLayout(menu_layout)
    menu.layout()


class MainToolBar(QToolBar):
    """The main toolbar for pyspread"""

    def __init__(self, main_window):
        self.main_window = main_window
        super().__init__("Main toolbar", main_window)

        self.setObjectName("Main toolbar")
        self._create_toolbar(main_window.main_window_actions)

    def _create_toolbar(self, actions):
        """Fills the main toolbar with QActions"""

        self.addAction(actions["new"])
        self.addAction(actions["open"])
        self.addAction(actions["save"])
        self.addAction(actions["export"])
        self.addSeparator()
        self.addAction(actions["undo"])
        self.addAction(actions["redo"])
        self.addSeparator()
        self.addAction(actions["toggle_spell_checker"])
        self.addSeparator()
        self.addAction(actions["find"])
        self.addAction(actions["replace"])
        self.addSeparator()
        self.addAction(actions["cut"])
        self.addAction(actions["copy"])
        self.addAction(actions["copy_results"])
        self.addAction(actions["paste"])
        self.addAction(actions["paste"])
        self.addSeparator()
        self.addAction(actions["sort_ascending"])
        self.addAction(actions["sort_descending"])
        self.addSeparator()
        self.addAction(actions["print"])

        undo_button = self.widgetForAction(actions["undo"])
        undo_view = QUndoView(self.main_window.undo_stack)
        add_toolbutton_widget(undo_button, undo_view)


class FindToolbar(QToolBar):
    """The find toolbar for pyspread"""

    def __init__(self, main_window):
        super().__init__("Find toolbar", main_window)

        self.setObjectName("Find toolbar")
        self._create_toolbar(main_window.main_window_actions)

    def _create_toolbar(self, actions):
        """Fills the find toolbar with QActions"""

        self.addSeparator()


class FormatToolbar(QToolBar):
    """The format toolbar for pyspread"""

    def __init__(self, main_window):
        super().__init__("Format toolbar", main_window)

        self.main_window = main_window
        self.setObjectName("Format toolbar")
        self._create_toolbar(main_window.main_window_actions)

    def _create_toolbar(self, actions):
        """Fills the format toolbar with QActions"""

        self.addWidget(self.main_window.widgets.font_combo)
        self.addWidget(self.main_window.widgets.font_size_combo)

        self.addAction(actions["bold"])
        self.addAction(actions["italics"])
        self.addAction(actions["underline"])
        self.addAction(actions["strikethrough"])

        self.addSeparator()

        self.addWidget(self.main_window.widgets.renderer_button)
        self.addAction(actions["merge_cells"])

        self.addSeparator()

        self.addWidget(self.main_window.widgets.rotate_button)
        self.addWidget(self.main_window.widgets.justify_button)
        self.addWidget(self.main_window.widgets.align_button)

        self.addSeparator()

        self.border_menu_button = QToolButton(self)
        border_submenu = self.main_window.menuBar().border_submenu
        self.border_menu_button.setMenu(border_submenu)
        self.border_menu_button.setIcon(Icon("border_menu"))
        self.addWidget(self.border_menu_button)
        self.border_menu_button.setPopupMode(
            QToolButton.InstantPopup)

        self.line_width_button = QToolButton(self)
        line_width_submenu = self.main_window.menuBar().line_width_submenu
        self.line_width_button.setMenu(line_width_submenu)
        self.line_width_button.setIcon(Icon("format_borders"))
        self.addWidget(self.line_width_button)
        self.line_width_button.setPopupMode(
            QToolButton.InstantPopup)

        self.addSeparator()

        text_color_button = self.main_window.widgets.text_color_button
        text_color_button.set_max_size(self.iconSize())
        self.addWidget(text_color_button)

        line_color_button = self.main_window.widgets.line_color_button
        line_color_button.set_max_size(self.iconSize())
        self.addWidget(line_color_button)

        background_color_button = \
            self.main_window.widgets.background_color_button
        background_color_button.set_max_size(self.iconSize())
        self.addWidget(background_color_button)

        self.addSeparator()

        self.addAction(actions["copy_format"])
        self.addAction(actions["paste_format"])


class MacroToolbar(QToolBar):
    """The macro toolbar for pyspread"""

    def __init__(self, main_window):
        super().__init__("Macro toolbar", main_window)

        self.setObjectName("Macro toolbar")
        self._create_toolbar(main_window.main_window_actions)

    def _create_toolbar(self, actions):
        """Fills the macro toolbar with QActions"""

        self.addAction(actions["insert_image"])
        self.addAction(actions["link_image"])
        if matplotlib_figure is not None:
            self.addAction(actions["insert_chart"])


class WidgetToolbar(QToolBar):
    """The widget toolbar for pyspread"""

    def __init__(self, main_window):
        super().__init__("Widget toolbar", main_window)

        self.setObjectName("Widget toolbar")
        self._create_toolbar(main_window.main_window_actions)

    def _create_toolbar(self, actions):
        """Fills the widget toolbar with QActions"""

        self.addSeparator()


class ChartTemplatesToolBar(QToolBar):
    """Toolbar for chart dialog for inserting template chart code"""

    def __init__(self, parent):
        super().__init__("Chart templates toolbar", parent)

        self.setObjectName("Chart templates toolbar")
        self._create_toolbar(parent.actions)

    def _create_toolbar(self, actions):
        """Fills the main toolbar with QActions"""

        self.addAction(actions["chart_pie_1_1"])
        self.addAction(actions["chart_ring_1_1"])
        self.addAction(actions["chart_line_1_1"])
        self.addAction(actions["chart_polar_1_1"])
        self.addAction(actions["chart_area_1_1"])
        self.addAction(actions["chart_column_1_1"])
        self.addAction(actions["chart_column_1_2"])
        self.addAction(actions["chart_bar_1_3"])
        self.addAction(actions["chart_scatter_1_1"])
        self.addAction(actions["chart_bubble_1_1"])
        self.addAction(actions["chart_boxplot_2_2"])
        self.addAction(actions["chart_histogram_1_1"])
        self.addAction(actions["chart_histogram_1_4"])
        self.addAction(actions["chart_scatterhist_1_1"])
        self.addAction(actions["chart_matrix_1_1"])
        self.addAction(actions["chart_contour_1_2"])
        self.addAction(actions["chart_surface_2_1"])
