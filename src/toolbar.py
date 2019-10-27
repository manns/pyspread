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

**Contains:**

* :class:`ChartTemplatesToolBar`
* :class:`FindToolbar`
* :class:`FormatToolbar`
* :class:`MacroToolbar`
* :class:`WidgetToolbar`
* :func:`add_toolbutton_widget`

"""

import functools
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QToolBar, QToolButton, QMenu
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout,  QUndoView
from PyQt5.QtWidgets import QWidget, QWidgetAction, QCheckBox, QLabel


try:
    import matplotlib.figure as matplotlib_figure
except ImportError:
    matplotlib_figure = None

from src.icons import Icon
from src.actions import Action


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
    """The main toolbar"""

    def __init__(self, main_window):
        self.main_window = main_window
        super().__init__("Main toolbar", main_window)

        self.setObjectName("Main Toolbar")
        self._create_toolbar(main_window.main_window_actions)

    def _create_toolbar(self, actions):
        """Fills the main toolbar with QActions"""

        self.addAction(actions.new)
        self.addAction(actions.open)
        self.addAction(actions.save)
        self.addAction(actions.export)
        self.addSeparator()

        self.addAction(actions.undo)
        self.addAction(actions.redo)
        self.addSeparator()

        self.addAction(actions.toggle_spell_checker)
        self.addSeparator()

        self.addAction(actions.find)
        self.addAction(actions.replace)
        self.addSeparator()

        self.addAction(actions.cut)
        self.addAction(actions.copy)
        self.addAction(actions.copy_results)
        self.addAction(actions.paste)
        self.addAction(actions.paste)
        self.addSeparator()

        self.addAction(actions.freeze_cell)
        self.addSeparator()

        self.addAction(actions.print)

        undo_button = self.widgetForAction(actions.undo)
        undo_view = QUndoView(self.main_window.undo_stack)
        add_toolbutton_widget(undo_button, undo_view)

        self.addWidget(ToolBarManager(self))


class FindToolbar(QToolBar):
    """The find toolbar for pyspread"""

    def __init__(self, main_window):
        super().__init__("Find Toolbar", main_window)

        self.setObjectName("Find Toolbar")
        self._create_toolbar(main_window.main_window_actions)

    def _create_toolbar(self, actions):
        """Fills the find toolbar with QActions"""

        self.addSeparator()


class FormatToolbar(QToolBar):
    """The format toolbar for pyspread"""

    def __init__(self, main_window):
        super().__init__("Format Toolbar", main_window)

        self.main_window = main_window
        self.setObjectName("Format Toolbar")
        self._create_toolbar(main_window.main_window_actions)

    def _create_toolbar(self, actions):
        """Fills the format toolbar with QActions"""

        self.addWidget(self.main_window.widgets.font_combo)
        self.addWidget(self.main_window.widgets.font_size_combo)

        self.addAction(actions.bold)
        self.addAction(actions.italics)
        self.addAction(actions.underline)
        self.addAction(actions.strikethrough)

        self.addSeparator()

        self.addWidget(self.main_window.widgets.renderer_button)
        self.addAction(actions.merge_cells)

        self.addSeparator()

        self.addWidget(self.main_window.widgets.rotate_button)
        self.addWidget(self.main_window.widgets.justify_button)
        self.addWidget(self.main_window.widgets.align_button)

        self.addSeparator()

        self.border_menu_button = QToolButton(self)
        self.border_menu_button.setText("Borders")
        border_submenu = self.main_window.menuBar().border_submenu
        self.border_menu_button.setMenu(border_submenu)
        self.border_menu_button.setIcon(Icon.border_menu)
        self.addWidget(self.border_menu_button)
        self.border_menu_button.setPopupMode(
            QToolButton.InstantPopup)

        self.line_width_button = QToolButton(self)
        self.line_width_button.setText("Border Width")
        line_width_submenu = self.main_window.menuBar().line_width_submenu
        self.line_width_button.setMenu(line_width_submenu)
        self.line_width_button.setIcon(Icon.format_borders)
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

        self.addAction(actions.copy_format)
        self.addAction(actions.paste_format)

        self.addSeparator()

        self.addWidget(ToolBarManager(self))


class ToolBarManager(QToolButton):

    def __init__(self, parentToolBar):
        super().__init__()

        self.parentToolBar = parentToolBar

        self.setToolTip("Toggle item visibility")
        self.setMenu(QMenu(self))
        self.setPopupMode(QToolButton.InstantPopup)
        #  self.setIcon(Icon("TODO"))
        self.setFixedWidth(16)

        m = 0
        mainWidget = QWidget()
        mainlay = QVBoxLayout()
        mainlay.setContentsMargins(m, m, m, m)
        mainWidget.setLayout(mainlay)

        lbl = QLabel("Set preferences for visibility")
        lbl.setStyleSheet("background-color: #FFFDC3; padding: 4px;")
        mainlay.addWidget(lbl)

        m = 5
        self.grid = QGridLayout()
        self.grid.setContentsMargins(m, m, m, m)
        mainlay.addLayout(self.grid)

        self.create_widgets()

        widget_action = QWidgetAction(self)
        widget_action.setDefaultWidget(mainWidget)
        self.menu().addAction(widget_action)

    def create_widgets(self):

        for ridx, obj in enumerate(self.parentToolBar.actions()):

            if obj.isSeparator():
                # its a separator so draw a litle line
                linelbl = QLabel()
                linelbl.setStyleSheet("background-color: #dddddd")
                linelbl.setFixedHeight(1)
                self.grid.addWidget(linelbl, ridx, 0, 1, 3)
                continue

            # Viz toggle
            chk = QCheckBox()
            self.grid.addWidget(chk, ridx, 0)
            chk.setChecked(obj.isVisible())
            chk.toggled.connect(functools.partial(self.on_toggle, chk, obj))

            if isinstance(obj, Action):
                icon = QLabel()
                icon.setPixmap(obj.icon().pixmap(QSize(16, 16)))
                self.grid.addWidget(icon, ridx, 1)
                lbl = QLabel(self)
                lbl.setText(obj.text())
                self.grid.addWidget(lbl, ridx, 2)

            elif isinstance(obj, QWidgetAction):

                wid = obj.defaultWidget()
                name = None

                if hasattr(wid, "label"):  # eg Custom Combos
                    name = wid.label

                elif isinstance(wid, QToolButton):
                    name = wid.text()

                else:
                    print("ERROR: Not handled. set_toolbar()", wid.text(),
                          self)

                if hasattr(wid, "icon"):
                    icon = QLabel()
                    icon.setPixmap(wid.icon().pixmap(QSize(16, 16)))
                    self.grid.addWidget(icon, ridx, 1)

                lbl = QLabel(self)
                lbl.setText(name)
                self.grid.addWidget(lbl, ridx, 2)

        self.grid.setRowStretch(0, 0)
        self.grid.setRowStretch(1, 0)
        self.grid.setRowStretch(2, 3)

    def on_toggle(self, checkBox, srcObject):
        srcObject.setVisible(checkBox.isChecked())


class MacroToolbar(QToolBar):
    """The macro toolbar for pyspread"""

    def __init__(self, main_window):
        super().__init__("Macro toolbar", main_window)

        self.setObjectName("Macro toolbar")
        self._create_toolbar(main_window.main_window_actions)

    def _create_toolbar(self, actions):
        """Fills the macro toolbar with QActions"""

        self.addAction(actions.insert_image)
        self.addAction(actions.link_image)
        if matplotlib_figure is not None:
            self.addAction(actions.insert_chart)

        self.addWidget(ToolBarManager(self))


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

        self.addAction(actions.chart_pie_1_1)
        self.addAction(actions.chart_ring_1_1)
        self.addAction(actions.chart_line_1_1)
        self.addAction(actions.chart_polar_1_1)
        self.addAction(actions.chart_area_1_1)
        self.addAction(actions.chart_column_1_1)
        self.addAction(actions.chart_column_1_2)
        self.addAction(actions.chart_bar_1_3)
        self.addAction(actions.chart_scatter_1_1)
        self.addAction(actions.chart_bubble_1_1)
        self.addAction(actions.chart_boxplot_2_2)
        self.addAction(actions.chart_histogram_1_1)
        self.addAction(actions.chart_histogram_1_4)
        self.addAction(actions.chart_scatterhist_1_1)
        self.addAction(actions.chart_matrix_1_1)
        self.addAction(actions.chart_contour_1_2)
        self.addAction(actions.chart_surface_2_1)
