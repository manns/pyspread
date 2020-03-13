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


**Widgets**

 * :class:`MultiStateBitmapButton`
 * :class:`RotationButton`
 * :class:`JustificationButton`
 * :class:`RendererButton`
 * :class:`AlignmentButton`
 * :class:`ColorButton`
 * :class:`TextColorButton`
 * :class:`LineColorButton`
 * :class:`BackgroundColorButton`
 * :class:`FontChoiceCombo`
 * :class:`Widgets`
 * :class:`FindEditor`
 * :class:`CellButton`

"""

from PyQt5.QtCore import pyqtSignal, QSize, Qt, QModelIndex
from PyQt5.QtWidgets \
    import (QToolButton, QColorDialog, QFontComboBox, QComboBox, QSizePolicy,
            QLineEdit, QPushButton)
from PyQt5.QtGui import QPalette, QColor, QFont, QIntValidator, QCursor

from actions import Action
from icons import Icon


class MultiStateBitmapButton(QToolButton):
    """QToolButton that cycles through arbitrary states

    The states are defined by an iterable of QIcons

    Parameters
    ----------

    * actions: List of QActions
    \tThe list of actions to be cycled through

    """

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self._current_action_idx = 0

        self.clicked.connect(self.on_clicked)

    @property
    def current_action_idx(self):
        return self._current_action_idx

    @current_action_idx.setter
    def current_action_idx(self, index):
        """Sets current action index and updates button and menu"""

        self._current_action_idx = index
        action = self.get_action(index)
        self.setIcon(action.icon())

    def get_action(self, index):
        """Returns action from index in action_names"""

        action_name = self.action_names[index]
        return self.main_window.main_window_actions[action_name]

    def set_current_action(self, action_name):
        """Sets current action"""

        self.current_action_idx = self.action_names.index(action_name)

    def next(self):
        """Advances current_action_idx and returns current action"""

        if self.current_action_idx >= len(self.action_names) - 1:
            self.current_action_idx = 0
        else:
            self.current_action_idx += 1

        return self.get_action(self.current_action_idx)

    def set_menu_checked(self, action_name):
        """Sets checked status of menu"""

        action = self.main_window.main_window_actions[action_name]
        action.setChecked(True)

    def on_clicked(self):
        """Button clicked event handler. Chechs corresponding menu item"""

        action = self.next()
        action.trigger()
        action.setChecked(True)


class RotationButton(MultiStateBitmapButton):
    """Rotation button for the format toolbar"""

    label = "Rotate"
    action_names = "rotate_0", "rotate_90", "rotate_180", "rotate_270"

    def __init__(self, main_window):
        super().__init__(main_window)

        self.setStatusTip("Text rotation")
        self.setToolTip("Text rotation")

    def icon(self):
        """Returns QIcon for button identification"""

        return Icon.rotate_0


class JustificationButton(MultiStateBitmapButton):
    """Justification button for the format toolbar"""

    label = "Justification"
    action_names = ("justify_left", "justify_center", "justify_right",
                    "justify_fill")

    def __init__(self, main_window):
        super().__init__(main_window)

        self.setStatusTip("Text justification")
        self.setToolTip("Text justification")

    def icon(self):
        """Returns QIcon for button identification"""

        return Icon.justify_left


class RendererButton(MultiStateBitmapButton):
    """Cell render button for the format toolbar"""

    label = "Renderer"
    action_names = "text", "markup", "image", "matplotlib"

    def __init__(self, main_window):
        super().__init__(main_window)

        self.setStatusTip("Cell render type")
        self.setToolTip("Cell render type")

    def icon(self):
        """Returns QIcon for button identification"""

        return Icon.text


class AlignmentButton(MultiStateBitmapButton):
    """Alignment button for the format toolbar"""

    label = "Alignment"
    action_names = "align_top", "align_center", "align_bottom"

    def __init__(self, main_window):
        super().__init__(main_window)

        self.setStatusTip("Text alignment")
        self.setToolTip("Text alignment")

    def icon(self):
        """Returns QIcon for button identification"""

        return Icon.align_top


class ColorButton(QToolButton):
    """Color button widget

    Parameters
    ----------

    * qcolor: QColor
    \tColor that is initially set
    * icon: QIcon, defaults to None
    \tButton foreground image
    * max_size: QSize, defaults to QSize(28, 28)
    \tMaximum Size of the button

    """

    colorChanged = pyqtSignal()
    title = "Select Color"

    def __init__(self, color, icon=None, max_size=QSize(28, 28)):
        super().__init__()

        if icon is not None:
            self.setIcon(icon)

        self.color = color

        self.pressed.connect(self.on_pressed)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        """Color setter that adjusts internal state and button background.

        Parameters
        ----------
        * color: QColor
        \tNew color attribute to be set
        """

        if hasattr(self, "_color") and self._color == color:
            return

        self._color = color

        palette = self.palette()
        palette.setColor(QPalette.Button, color)
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        self.update()

    def set_max_size(self, size):
        """Set the maximum size of the widget

        size: Qsize
        \tMaximum size of the widget

        """

        self.setMaximumWidth(size.width())
        self.setMaximumHeight(size.height())

    def on_pressed(self):
        """Button pressed event handler

        Shows color dialog and sets the chosen color.

        """

        dlg = QColorDialog(self.parent())

        dlg.setCurrentColor(self.color)
        dlg.setWindowTitle(self.title)

        dlg.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        dlg.setWindowModality(Qt.ApplicationModal)
        dlg.setOptions(QColorDialog.DontUseNativeDialog)

        p = self.mapFromGlobal(QCursor.pos())
        p.setX(p.x() + (self.rect().width() / 2))
        p.setY(p.y() + (self.rect().height() / 2))
        dlg.move(self.mapToGlobal(p))

        if dlg.exec_():
            self.color = dlg.currentColor()
            self.colorChanged.emit()


class TextColorButton(ColorButton):
    """Color button with text icon"""

    label = "Text Color"

    def __init__(self, color):
        icon = Icon.text_color
        super().__init__(color, icon=icon)

        self.title = "Select text color"
        self.setStatusTip("Text color")
        self.setToolTip("Text color")


class LineColorButton(ColorButton):
    """Color button with text icon"""

    label = "Line Color"

    def __init__(self, color):
        icon = Icon.line_color
        super().__init__(color, icon=icon)

        self.title = "Select cell border line color"
        self.setStatusTip("Cell border line color")
        self.setToolTip("Cell border line color")


class BackgroundColorButton(ColorButton):
    """Color button with text icon"""

    label = "Background Color"

    def __init__(self, color):
        icon = Icon.background_color
        super().__init__(color, icon=icon)

        self.title = "Select cell background color"
        self.setStatusTip("Cell background color")
        self.setToolTip("Cell background color")


class FontChoiceCombo(QFontComboBox):
    """Font choice combo box"""

    label = "Font Family"

    fontChanged = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()

        self.setMaximumWidth(150)

        # Set default font
        self.setFont(QFont())

        self.currentFontChanged.connect(self.on_font)

    @property
    def font(self):
        return self.currentFont().family()

    @font.setter
    def font(self, font):
        """Sets font without emitting currentTextChanged"""

        self.currentFontChanged.disconnect(self.on_font)
        self.setCurrentFont(QFont(font))
        self.currentFontChanged.connect(self.on_font)

    def icon(self):
        """Returns QIcon for button identification"""

        return Icon.font_dialog

    def on_font(self, font):
        """Font choice event handler"""

        self.fontChanged.emit()


class FontSizeCombo(QComboBox):
    """Font choice combo box"""

    label = "Font Size"
    fontSizeChanged = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()

        self.setEditable(True)

        for size in main_window.settings.font_sizes:
            self.addItem(str(size))

        idx = self.findText(str(main_window.settings.font_sizes))
        if idx >= 0:
            self.setCurrentIndex(idx)

        validator = QIntValidator(1, 128, self)
        self.setValidator(validator)

        self.currentTextChanged.connect(self.on_text)

    @property
    def size(self):
        return int(self.currentText())

    @size.setter
    def size(self, size):
        """Sets size without emitting currentTextChanged"""

        self.currentTextChanged.disconnect(self.on_text)
        self.setCurrentText(str(size))
        self.currentTextChanged.connect(self.on_text)

    def icon(self):
        """Returns QIcon for button identification"""

        return Icon.font_dialog

    def on_text(self, size):
        """Font size choice event handler"""

        try:
            value = int(self.currentText())
        except ValueError:
            value = 1
            self.setCurrentText("1")

        if value < 1:
            self.setCurrentText("1")
        if value > 128:
            self.setCurrentText("128")

        self.fontSizeChanged.emit()


class Widgets:
    def __init__(self, main_window):

        # Format toolbar widgets

        self.font_combo = FontChoiceCombo(main_window)

        self.font_size_combo = FontSizeCombo(main_window)

        text_color = QColor("black")
        self.text_color_button = TextColorButton(text_color)

        background_color = QColor("white")
        self.background_color_button = BackgroundColorButton(background_color)

        line_color = QColor("black")
        self.line_color_button = LineColorButton(line_color)

        self.renderer_button = RendererButton(main_window)
        self.rotate_button = RotationButton(main_window)
        self.justify_button = JustificationButton(main_window)
        self.align_button = AlignmentButton(main_window)


class FindEditor(QLineEdit):
    """The Find editor widget for the find toolbar"""

    up = False
    word = False
    case = False
    regexp = False
    results = False

    def __init__(self, parent):
        super().__init__(parent)

        self.actions = parent.main_window.main_window_actions

        self.label = "Find editor"
        self.icon = lambda: Icon.find_next
        self.sizePolicy().setHorizontalPolicy(QSizePolicy.Preferred)
        self.setClearButtonEnabled(True)
        self.addAction(self.actions.find_next, QLineEdit.LeadingPosition)

        workflows = parent.main_window.workflows
        self.returnPressed.connect(workflows.edit_find_next)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_context_menu)

    def prepend_actions(self, menu):
        """Prepends find specific actions to menu"""

        toggle_case = Action(self, "Match &case",
                             self.on_toggle_case, checkable=True,
                             statustip='Match case in search')

        toggle_results = Action(self, "Code and results",
                                self.on_toggle_results, checkable=True,
                                statustip='Search also considers string '
                                          'representations of result objects.')

        toggle_up = Action(self, "Search &backward",
                           self.on_toggle_up, checkable=True,
                           statustip='Search fore-/backwards')

        toggle_word = Action(self, "&Whole words",
                             self.on_toggle_word, checkable=True,
                             statustip='Whole word search')

        toggle_regexp = Action(self, "Regular expression",
                               self.on_toggle_regexp, checkable=True,
                               statustip='Regular expression search')

        toggle_case.setChecked(self.case)
        toggle_results.setChecked(self.results)
        toggle_up.setChecked(self.up)
        toggle_word.setChecked(self.word)
        toggle_regexp.setChecked(self.regexp)

        actions = (toggle_case, toggle_results, toggle_up, toggle_word,
                   toggle_regexp)
        menu.insertActions(menu.actions()[0], actions)

    def on_context_menu(self, point):
        """Context menu event handler"""

        menu = self.createStandardContextMenu()
        menu.insertSeparator(menu.actions()[0])
        self.prepend_actions(menu)
        menu.exec(self.mapToGlobal(point))

    def on_toggle_up(self, toggled):
        """Find upwards toggle event handler"""

        self.up = toggled

    def on_toggle_word(self, toggled):
        """Find whole word toggle event handler"""

        self.word = toggled

    def on_toggle_case(self, toggled):
        """Find case sensitively toggle event handler"""

        self.case = toggled

    def on_toggle_regexp(self, toggled):
        """Find with regular expression toggle event handler"""

        self.regexp = toggled

    def on_toggle_results(self, toggled):
        """Find in results toggle event handler"""

        self.results = toggled


class CellButton(QPushButton):
    """Button that is used for button cells in the grid

    :text: str: Button text
    :grid: QTableView
    :key: 3-tuple of int: row, column, table

    """

    def __init__(self, text, grid, key):
        super().__init__(text, grid)

        self.grid = grid
        self.key = key  # Key of button cell

        self.clicked.connect(self.on_clicked)

    def on_clicked(self):
        """Clicked event handler, executes cell code"""

        code = self.grid.model.code_array(self.key)
        result = self.grid.model.code_array._eval_cell(self.key, code)
        self.grid.model.code_array.frozen_cache[repr(self.key)] = result
        self.grid.model.code_array.result_cache.clear()
        self.grid.model.dataChanged.emit(QModelIndex(), QModelIndex())
