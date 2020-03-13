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

"""


**Modal dialogs**

 * :class:`DiscardChangesDialog`
 * :class:`ApproveWarningDialog`
 * :class:`DataEntryDialog`
 * :class:`GridShapeDialog`
 * :class:`PrintAreaDialog`
 * :class:`CsvExportAreaDialog`
 * (:class:`FileDialogBase`)
 * :class:`FileOpenDialog`
 * :class:`FileSaveDialog`
 * :class:`ImageFileOpenDialog`
 * :class:`CsvFileImportDialog`
 * :class:`FindDialog`
 * :class:`ChartDialog`
 * :class:`CsvImportDialog`
 * :class:`CsvExportDialog`
 * (:class:`HelpDialogBase`)
 * :class:`TutorialDialog`
 * :class:`ManualDialog`
 * :class:`PrintPreviewDialog`
"""

import csv
try:
    from dataclasses import dataclass
except ImportError:
    from pyspread.lib.dataclasses import dataclass  # Python 3.6 compatibility
from functools import partial
import io

from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtWidgets \
    import (QApplication, QMessageBox, QFileDialog, QDialog, QLineEdit, QLabel,
            QFormLayout, QVBoxLayout, QGroupBox, QDialogButtonBox, QSplitter,
            QTextBrowser, QCheckBox, QGridLayout, QLayout, QHBoxLayout,
            QPushButton, QWidget, QComboBox, QTableView, QAbstractItemView,
            QPlainTextEdit, QToolBar)
from PyQt5.QtGui \
    import (QIntValidator, QImageWriter, QStandardItemModel, QStandardItem,
            QTextDocument)

from PyQt5.QtPrintSupport import QPrintPreviewDialog, QPrintPreviewWidget

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
except ImportError:
    Figure = None

from actions import ChartDialogActions
from toolbar import ChartTemplatesToolBar
from icons import PYSPREAD_PATH
from lib.csv import sniff, csv_reader, get_header, typehandlers, convert
from lib.markdown2 import markdown
from lib.spelltextedit import SpellTextEdit
from lib.testlib import unit_test_dialog_override
from settings import TUTORIAL_PATH, MANUAL_PATH

MPL_TEMPLATE_PATH = PYSPREAD_PATH / 'share/templates/matplotlib'


class DiscardChangesDialog:
    """Modal dialog that asks if the user wants to discard or save unsaved data

    The modal dialog is shown on accessing the property choice.

    """

    title = "Unsaved changes"
    text = "There are unsaved changes.\nDo you want to save?"
    choices = QMessageBox.Discard | QMessageBox.Cancel | QMessageBox.Save
    default_choice = QMessageBox.Save

    def __init__(self, main_window):
        self.main_window = main_window

    @property
    def choice(self):
        """User choice

        Returns True if the user confirms in a user dialog that unsaved
        changes will be discarded if conformed.
        Returns False if the user chooses to save the unsaved data
        Returns None if the user chooses to abort the operation

        """

        button_approval = QMessageBox.warning(self.main_window, self.title,
                                              self.text, self.choices,
                                              self.default_choice)
        if button_approval == QMessageBox.Discard:
            return True
        elif button_approval == QMessageBox.Save:
            return False


class ApproveWarningDialog:
    """Modal warning dialog for approving files to be evaled

    The modal dialog is shown on accessing the property choice.

    """

    title = "Security warning"
    text = ("You are going to approve and trust a file that you have not "
            "created yourself. After proceeding, the file is executed.\n \n"
            "It may harm your system as any program can. Please check all "
            "cells thoroughly before proceeding.\n \n"
            "Proceed and sign this file as trusted?")
    choices = QMessageBox.No | QMessageBox.Yes
    default_choice = QMessageBox.No

    def __init__(self, parent):
        self.parent = parent

    @property
    def choice(self):
        """User choice

        Returns True iif the user approves leaving safe_mode.
        Returns False iif the user chooses to stay in safe_mode
        Returns None if the user chooses to abort the operation

        """

        button_approval = QMessageBox.warning(self.parent, self.title,
                                              self.text, self.choices,
                                              self.default_choice)
        if button_approval == QMessageBox.Yes:
            return True
        elif button_approval == QMessageBox.No:
            return False


class DataEntryDialog(QDialog):
    """Modal dialog for entering multiple values

    Parameters
    ----------
    * parent: QWidget
    \tParent window
    * title: str
    \tDialog title
    * labels: list or tuple of str
    \tLabels for the values in the dialog
    * initial_data: list or tuple of str, defaults to None
    \tInitial values to be displayed in the dialog, must match no. labels
    * validators: list or tuple of QValidator, defaults to None
    \tValidators for the editors of the dialog, must match no. labels

    """

    def __init__(self, parent, title, labels, initial_data=None,
                 groupbox_title=None, validators=None):
        super().__init__(parent)

        self.labels = labels
        self.groupbox_title = groupbox_title

        if initial_data is None:
            self.initial_data = [""] * len(labels)
        elif len(initial_data) != len(labels):
            raise ValueError("Length of labels and initial_data not equal")
        else:
            self.initial_data = initial_data

        if validators is None:
            self.validators = [None] * len(labels)
        elif len(validators) != len(labels):
            raise ValueError("Length of labels and validators not equal")
        else:
            self.validators = validators

        self.editors = []

        layout = QVBoxLayout(self)
        layout.addWidget(self.create_form())
        layout.addStretch(1)
        layout.addWidget(self.create_buttonbox())
        self.setLayout(layout)

        self.setWindowTitle(title)
        self.setMinimumWidth(300)
        self.setMinimumHeight(150)

    @property
    def data(self):
        """Executes the dialog and returns a tuple of strings

        Returns None if the dialog is canceled.

        """

        result = self.exec_()

        if result == QDialog.Accepted:
            return tuple(editor.text() for editor in self.editors)

    def create_form(self):
        """Returns form inside a QGroupBox"""

        form_group_box = QGroupBox()
        if self.groupbox_title:
            form_group_box.setTitle(self.groupbox_title)
        form_layout = QFormLayout()

        for label, initial_value, validator in zip(self.labels,
                                                   self.initial_data,
                                                   self.validators):
            editor = QLineEdit(str(initial_value))
            editor.setAlignment(Qt.AlignRight)
            if validator:
                editor.setValidator(validator)
            form_layout.addRow(QLabel(label + " :"), editor)
            self.editors.append(editor)

        form_layout.setLabelAlignment(Qt.AlignRight)
        form_group_box.setLayout(form_layout)

        return form_group_box

    def create_buttonbox(self):
        """Returns a QDialogButtonBox with Ok and Cancel"""

        button_box = QDialogButtonBox(QDialogButtonBox.Ok
                                      | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        return button_box


class GridShapeDialog(DataEntryDialog):
    """Modal dialog for entering the number of rows, columns and tables

    Parameters
    ----------
    * parent: QWidget
    \tParent window
    * shape: 3-tuple of Integer
    \tInitial shape to be displayed in the dialog: (rows, columns, tables)

    """

    def __init__(self, parent, shape, title="Create a new Grid"):
        groupbox_title = "Grid Shape"
        labels = ["Number of Rows", "Number of Columns", "Number of Tables"]
        validator = QIntValidator()
        validator.setBottom(1)  # Do not allow negative values
        validators = [validator] * len(labels)
        super().__init__(parent, title, labels, shape, groupbox_title,
                         validators)

    @property
    @unit_test_dialog_override
    def shape(self):
        """Executes the dialog and returns an int tuple rows, columns, tables

        Returns None if the dialog is canceled.

        """

        data = self.data
        if data is not None:
            try:
                return tuple(map(int, data))
            except (TypeError, ValueError):
                return


class PrintAreaDialog(DataEntryDialog):
    """Modal dialog for entering print area

    Initially, this dialog is filled with the selection bounding box
    if present or with the visible area of <= 1 cell is selected.

    Parameters
    ----------
    * parent: QWidget
    \tParent window
    * shape: 3-tuple of Integer
    \tInitial shape to be displayed in the dialog: (rows, columns, tables)

    """

    groupbox_title = "Print area"
    labels = ["Top", "Left", "Bottom", "Right"]

    def __init__(self, parent, grid, title="Print settings"):

        self.shape = grid.model.shape

        row_validator = QIntValidator()
        row_validator.setBottom(0)  # Do not allow negative values
        row_validator.setTop(self.shape[0] - 1)
        column_validator = QIntValidator()
        column_validator.setBottom(0)  # Do not allow negative values
        column_validator.setTop(self.shape[1] - 1)

        if grid.selection and len(grid.selected_idx) > 1:
            (bb_top, bb_left), (bb_bottom, bb_right) = \
                grid.selection.get_grid_bbox(self.shape)
        else:
            bb_top, bb_bottom = grid.rowAt(0), grid.rowAt(grid.height())
            bb_left, bb_right = grid.columnAt(0), grid.columnAt(grid.width())

        initial_values = bb_top, bb_left, bb_bottom, bb_right

        validators = [row_validator, column_validator] * 2
        super().__init__(parent, title, self.labels, initial_values,
                         self.groupbox_title, validators)

    @property
    def area(self):
        """Executes the dialog and returns int tuple top, left, bottom, right

        Returns None if the dialog is canceled.

        """

        try:
            int_data = map(int, self.data)
            data = (min(self.shape[i % 2], d) for i, d in enumerate(int_data))
        except (TypeError, ValueError):
            return

        if data is not None:
            try:
                return tuple(data)
            except ValueError:
                return


class CsvExportAreaDialog(PrintAreaDialog):
    """Modal dialog for entering csv export area"""

    groupbox_title = "CSV export area"


class SvgExportAreaDialog(PrintAreaDialog):
    """Modal dialog for entering svg export area"""

    groupbox_title = "SVG export area"


class PreferencesDialog(DataEntryDialog):
    """Modal dialog for entering pyspread preferences"""

    def __init__(self, parent):
        title = "Preferences"
        groupbox_title = "Global settings"
        labels = ["Signature key for files", "Cell calculation timeout [ms]",
                  "Frozen cell refresh period [ms]", "Number of recent files"]
        self.keys = ["signature_key", "timeout", "refresh_timeout",
                     "max_file_history"]
        self.mappers = [str, int, int, int]
        data = [getattr(parent.settings, key) for key in self.keys]
        validator = QIntValidator()
        validator.setBottom(0)  # Do not allow negative values
        validators = [None, validator, validator, validator]
        super().__init__(parent, title, labels, data, groupbox_title,
                         validators)

    @property
    def data(self):
        """Executes the dialog and returns a dict containing preferences data

        Returns None if the dialog is canceled.

        """

        data = super().data
        if data is not None:
            data_dict = {}
            for key, mapper, data in zip(self.keys, self.mappers, data):
                data_dict[key] = mapper(data)
            return data_dict


class CellKeyDialog(DataEntryDialog):
    """Modal dialog for entering a cell key, i.e. row, column and table

    Parameters
    ----------
    * parent: QWidget
    \tParent window
    * shape: 3-tuple of Integer
    \tShape of the grid: (rows, columns, tables)

    """

    def __init__(self, parent, shape):
        title = "Go to cell"
        groupbox_title = "Cell index"
        labels = ["Row", "Column", "Table"]

        row_validator = QIntValidator()
        row_validator.setRange(0, shape[0] - 1)
        column_validator = QIntValidator()
        column_validator.setRange(0, shape[1] - 1)
        table_validator = QIntValidator()
        table_validator.setRange(0, shape[2] - 1)
        validators = [row_validator, column_validator, table_validator]

        super().__init__(parent, title, labels, None, groupbox_title,
                         validators)

    @property
    def key(self):
        """Executes the dialog and returns an int tuple rows, columns, tables

        Returns None if the dialog is canceled.

        """

        data = self.data
        if data is not None:
            try:
                return tuple(map(int, data))
            except ValueError:
                return


class FileDialogBase:
    """Base class for modal file dialogs

    The choosen filename is stored in the file_path attribute
    The choosen name filter is stored in the chosen_filter attribute
    If the dialog is aborted then both filepath and chosen_filter are None

    _get_filepath must be overloaded

    """
    file_path = None
    suffix = None

    title = "Choose file"

    filters_list = [
        "Pyspread un-compressed (*.pysu)",
        "Pyspread compressed (*.pys)"
    ]
    selected_filter = None

    @property
    def filters(self):
        """Formatted filters for qt"""

        return ";;".join(self.filters_list)

    @property
    def suffix(self):
        """Suffix for filepath"""

        if self.filters_list.index(self.selected_filter):
            return ".pys"
        else:
            return ".pysu"

    def __init__(self, main_window):

        self.main_window = main_window
        self.selected_filter = self.filters_list[0]

        self.show_dialog()

    def show_dialog(self):
        """Sublasses must overload this method"""

        raise Exception("show_dialog() - Needs method overload")


class FileOpenDialog(FileDialogBase):
    """Modal dialog for opening a pyspread file"""

    title = "Open"

    def show_dialog(self):
        """Present dialog and update values"""

        path = self.main_window.settings.last_file_input_path
        self.file_path, self.selected_filter = \
            QFileDialog.getOpenFileName(self.main_window, self.title,
                                        str(path), self.filters,
                                        self.selected_filter)


class FileSaveDialog(FileDialogBase):
    """Modal dialog for saving a pyspread file"""

    title = "Save"

    def show_dialog(self):
        """Present dialog and update values"""

        path = self.main_window.settings.last_file_output_path
        self.file_path, self.selected_filter = \
            QFileDialog.getSaveFileName(self.main_window, self.title,
                                        str(path), self.filters,
                                        self.selected_filter)


class ImageFileOpenDialog(FileDialogBase):
    """Modal dialog for inserting an image"""

    title = "Insert image"

    img_formats = QImageWriter.supportedImageFormats()
    img_format_strings = ("*." + fmt.data().decode('utf-8')
                          for fmt in img_formats)
    img_format_string = " ".join(img_format_strings)
    name_filter = "Images ({})".format(img_format_string) + ";;" \
                  "Scalable Vector Graphics (*.svg *.svgz)"

    def show_dialog(self):
        """Present dialog and update values"""

        path = self.main_window.settings.last_file_input_path
        self.file_path, self.selected_filter = \
            QFileDialog.getOpenFileName(self.main_window,
                                        self.title,
                                        str(path),
                                        self.name_filter)


class CsvFileImportDialog(FileDialogBase):
    """Modal dialog for importing csv files"""

    title = "Import data"
    filters_list = [
        "CSV file (*.*)",
    ]

    @property
    def suffix(self):
        """Do not offer suffix for filepath"""

        return

    def show_dialog(self):
        """Present dialog and update values"""

        path = self.main_window.settings.last_file_input_path
        self.file_path, self.selected_filter = \
            QFileDialog.getOpenFileName(self.main_window, self.title,
                                        str(path), self.filters,
                                        self.filters_list[0])


class CsvFileExportDialog(FileDialogBase):
    """Modal dialog for exporting csv files"""

    title = "Export data"
    filters_list = [
        "CSV file (*.*)",
        "SVG file (*.svg)",
    ]

    @property
    def suffix(self):
        """Suffix for filepath"""

        if self.filters_list.index(self.selected_filter):
            return ".svg"
        else:
            return

    def show_dialog(self):
        """Present dialog and update values"""

        path = self.main_window.settings.last_file_output_path
        self.file_path, self.selected_filter = \
            QFileDialog.getSaveFileName(self.main_window, self.title,
                                        str(path), self.filters,
                                        self.filters_list[0])


@dataclass
class FindDialogState:
    """Dataclass for FindDialog state storage"""

    pos: QPoint
    case: bool
    results: bool
    more: bool
    backward: bool
    word: bool
    regex: bool
    start: bool


class FindDialog(QDialog):
    """Find dialog that is launched from the main menu"""

    def __init__(self, main_window):
        super().__init__(main_window)

        self.main_window = main_window
        workflows = main_window.workflows

        self._create_widgets()
        self._layout()
        self._order()

        self.setWindowTitle("Find")

        self.extension.hide()

        self.more_button.toggled.connect(self.extension.setVisible)
        self.find_button.clicked.connect(
                partial(workflows.find_dialog_on_find, self))

        # Restore state
        state = self.main_window.settings.find_dialog_state
        if state is not None:
            self.restore(state)

    def _create_widgets(self):
        """Create find dialog widgets"""

        self.search_text_label = QLabel("Search for:")
        self.search_text_editor = QLineEdit()
        self.search_text_label.setBuddy(self.search_text_editor)

        self.case_checkbox = QCheckBox("Match &case")
        self.results_checkbox = QCheckBox("Code and &results")

        self.find_button = QPushButton("&Find")
        self.find_button.setDefault(True)

        self.more_button = QPushButton("&More")
        self.more_button.setCheckable(True)
        self.more_button.setAutoDefault(False)

        self.extension = QWidget()

        self.backward_checkbox = QCheckBox("&Backward")
        self.word_checkbox = QCheckBox("&Whole words")
        self.regex_checkbox = QCheckBox("Regular e&xpression")
        self.from_start_checkbox = QCheckBox("From &start")

        self.button_box = QDialogButtonBox(Qt.Vertical)
        self.button_box.addButton(self.find_button,
                                  QDialogButtonBox.ActionRole)
        self.button_box.addButton(self.more_button,
                                  QDialogButtonBox.ActionRole)

    def _layout(self):
        """Find dialog layout"""

        self.extension_layout = QVBoxLayout()
        self.extension_layout.setContentsMargins(0, 0, 0, 0)
        self.extension_layout.addWidget(self.backward_checkbox)
        self.extension_layout.addWidget(self.word_checkbox)
        self.extension_layout.addWidget(self.regex_checkbox)
        self.extension_layout.addWidget(self.from_start_checkbox)
        self.extension.setLayout(self.extension_layout)

        self.text_layout = QGridLayout()
        self.text_layout.addWidget(self.search_text_label, 0, 0)
        self.text_layout.addWidget(self.search_text_editor, 0, 1)
        self.text_layout.setColumnStretch(0, 1)

        self.search_layout = QVBoxLayout()
        self.search_layout.addLayout(self.text_layout)
        self.search_layout.addWidget(self.case_checkbox)
        self.search_layout.addWidget(self.results_checkbox)

        self.main_layout = QGridLayout()
        self.main_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.main_layout.addLayout(self.search_layout, 0, 0)
        self.main_layout.addWidget(self.button_box, 0, 1)
        self.main_layout.addWidget(self.extension, 1, 0, 1, 2)
        self.main_layout.setRowStretch(2, 1)

        self.setLayout(self.main_layout)

    def _order(self):
        """Find dialog tabOrder"""

        self.setTabOrder(self.results_checkbox, self.backward_checkbox)
        self.setTabOrder(self.backward_checkbox, self.word_checkbox)
        self.setTabOrder(self.word_checkbox, self.regex_checkbox)
        self.setTabOrder(self.regex_checkbox, self.from_start_checkbox)

    def restore(self, state):
        """Restores state from FindDialogState"""

        self.move(state.pos)
        self.case_checkbox.setChecked(state.case)
        self.results_checkbox.setChecked(state.results)
        self.more_button.setChecked(state.more)
        self.backward_checkbox.setChecked(state.backward)
        self.word_checkbox.setChecked(state.word)
        self.regex_checkbox.setChecked(state.regex)
        self.from_start_checkbox.setChecked(state.start)

    # Overrides

    def closeEvent(self, event):
        """Store state for next invocation and close"""

        state = FindDialogState(pos=self.pos(),
                                case=self.case_checkbox.isChecked(),
                                results=self.results_checkbox.isChecked(),
                                more=self.more_button.isChecked(),
                                backward=self.backward_checkbox.isChecked(),
                                word=self.word_checkbox.isChecked(),
                                regex=self.regex_checkbox.isChecked(),
                                start=self.from_start_checkbox.isChecked())
        self.main_window.settings.find_dialog_state = state

        super().closeEvent(event)


class ReplaceDialog(FindDialog):
    """Replace dialog that is launched from the main menu"""

    def __init__(self, main_window):
        super().__init__(main_window)

        workflows = main_window.workflows

        self.setWindowTitle("Replace")

        self.replace_text_label = QLabel("Replace with:")
        self.replace_text_editor = QLineEdit()
        self.replace_text_label.setBuddy(self.replace_text_editor)

        self.text_layout.addWidget(self.replace_text_label, 1, 0)
        self.text_layout.addWidget(self.replace_text_editor, 1, 1)

        self.replace_button = QPushButton("&Replace")
        self.replace_all_button = QPushButton("Replace &all")

        self.button_box.addButton(self.replace_button,
                                  QDialogButtonBox.ActionRole)
        self.button_box.addButton(self.replace_all_button,
                                  QDialogButtonBox.ActionRole)

        self.setTabOrder(self.search_text_editor, self.replace_text_editor)
        self.setTabOrder(self.more_button, self.replace_button)

        self.replace_button.clicked.connect(
                partial(workflows.replace_dialog_on_replace, self))

        self.replace_all_button.clicked.connect(
                partial(workflows.replace_dialog_on_replace_all, self))


class ChartDialog(QDialog):
    """The chart dialog"""

    def __init__(self, parent):
        if Figure is None:
            raise ImportError

        super().__init__(parent)

        self.actions = ChartDialogActions(self)

        self.chart_templates_toolbar = ChartTemplatesToolBar(self)

        self.setWindowTitle("Chart dialog")
        self.setModal(True)
        self.resize(800, 600)
        self.parent = parent

        self.actions = ChartDialogActions(self)

        self.dialog_ui()

    def on_template(self):
        """Event handler for pressing a template toolbar button"""

        chart_template_name = self.sender().data()
        chart_template_path = MPL_TEMPLATE_PATH / chart_template_name
        try:
            with open(chart_template_path) as template_file:
                chart_template_code = template_file.read()
        except OSError:
            return

        self.editor.insertPlainText(chart_template_code)

    def dialog_ui(self):
        """Sets up dialog UI"""

        msg = "Enter Python code into the editor to the left. Globals " + \
              "such as X, Y, Z, S are available as they are in the grid. " + \
              "The last line must result in a matplotlib figure.\n \n" + \
              "Pressing Apply displays the figure or an error message in " + \
              "the right area."

        self.message = QTextBrowser(self)
        self.message.setText(msg)
        self.editor = SpellTextEdit(self)
        self.splitter = QSplitter(self)

        buttonbox = self.create_buttonbox()

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.message)
        self.splitter.setOpaqueResize(False)
        self.splitter.setSizes([9999, 9999])

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.chart_templates_toolbar)

        layout.addWidget(self.splitter)
        layout.addWidget(buttonbox)

        self.setLayout(layout)

    def apply(self):
        """Executes the code in the dialog and updates the canvas"""

        # Get current cell
        key = self.parent.grid.current
        code = self.editor.toPlainText()

        figure = self.parent.grid.model.code_array._eval_cell(key, code)

        if isinstance(figure, Figure):
            canvas = FigureCanvasQTAgg(figure)
            self.splitter.replaceWidget(1, canvas)
            canvas.draw()
        else:
            if isinstance(figure, Exception):
                self.message.setText("Error:\n{}".format(figure))
            else:
                msg_text = "Error:\n{} has type '{}', " + \
                           "which is no instance of {}."
                msg = msg_text.format(figure,
                                      type(figure).__name__,
                                      Figure)
                self.message.setText(msg)
            self.splitter.replaceWidget(1, self.message)

    def create_buttonbox(self):
        """Returns a QDialogButtonBox with Ok and Cancel"""

        button_box = QDialogButtonBox(QDialogButtonBox.Ok
                                      | QDialogButtonBox.Apply
                                      | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply)
        return button_box


class CsvParameterGroupBox(QGroupBox):
    """QGroupBox that holds parameter widgets for the csv import dialog"""

    title = "Parameters"

    encodings = (
        "ascii", "big5", "big5hkscs", "cp037", "cp424", "cp437",
        "cp500", "cp720", "cp737", "cp775", "cp850", "cp852", "cp855", "cp856",
        "cp857", "cp858", "cp860", "cp861", "cp862", "cp863", "cp864", "cp865",
        "cp866", "cp869", "cp874", "cp875", "cp932", "cp949", "cp950",
        "cp1006", "cp1026", "cp1140", "cp1250", "cp1251", "cp1252", "cp1253",
        "cp1254", "cp1255", "cp1256", "cp1257", "cp1258", "euc-jp",
        "euc-jis-2004", "euc-jisx0213", "euc-kr", "gb2312", "gbk", "gb18030",
        "hz", "iso2022-jp", "iso2022-jp-1", "iso2022-jp-2", "iso2022-jp-2004",
        "iso2022-jp-3", "iso2022-jp-ext", "iso2022-kr", "latin-1", "iso8859-2",
        "iso8859-3", "iso8859-4", "iso8859-5", "iso8859-6", "iso8859-7",
        "iso8859-8", "iso8859-9", "iso8859-10", "iso8859-13", "iso8859-14",
        "iso8859-15", "iso8859-16", "johab", "koi8-r", "koi8-u",
        "mac-cyrillic", "mac-greek", "mac-iceland", "mac-latin2", "mac-roman",
        "mac-turkish", "ptcp154", "shift-jis", "shift-jis-2004",
        "shift-jisx0213", "utf-32", "utf-32-be", "utf-32-le", "utf-16",
        "utf-16-be", "utf-16-le", "utf-7", "utf-8", "utf-8-sig",
    )

    quotings = "QUOTE_ALL", "QUOTE_MINIMAL", "QUOTE_NONNUMERIC", "QUOTE_NONE"

    # Tooltips
    encoding_widget_tooltip = "CSV file encoding"
    quoting_widget_tooltip = \
        "Controls when quotes should be generated by the writer and " \
        "recognised by the reader."
    quotechar_tooltip = \
        "A one-character string used to quote fields containing special " \
        "characters, such as the delimiter or quotechar, or which contain " \
        "new-line characters."
    delimiter_tooltip = "A one-character string used to separate fields."
    escapechar_tooltip = "A one-character string used by the writer to " \
        "escape the delimiter if quoting is set to QUOTE_NONE and the " \
        "quotechar if doublequote is False. On reading, the escapechar " \
        "removes any special meaning from the following character."
    hasheader_tooltip = \
        "Analyze the CSV file and treat the first row as strings if it " \
        "appears to be a series of column headers."
    doublequote_tooltip = \
        "Controls how instances of quotechar appearing inside a field " \
        "should be themselves be quoted. When True, the character is " \
        "doubled. When False, the escapechar is used as a prefix to the " \
        "quotechar."
    skipinitialspace_tooltip = "When True, whitespace immediately following " \
        "the delimiter is ignored."

    # Default values that are displayed if the sniffer fails
    default_encoding = "utf-8"
    default_quoting = "QUOTE_MINIMAL"
    default_quotechar = '"'
    default_delimiter = ','

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.setTitle(self.title)
        self._create_widgets()
        self._layout()

    def _create_widgets(self):
        """Create widgets for all parameters"""

        # Encoding
        self.encoding_label = QLabel("Encoding")
        self.encoding_widget = QComboBox(self.parent)
        self.encoding_widget.addItems(self.encodings)
        if self.default_encoding in self.encodings:
            default_encoding_idx = self.encodings.index(self.default_encoding)
            self.encoding_widget.setCurrentIndex(default_encoding_idx)
        self.encoding_widget.setEditable(False)
        self.encoding_widget.setToolTip(self.encoding_widget_tooltip)

        # Quote character
        self.quotechar_label = QLabel("Quote character")
        self.quotechar_widget = QLineEdit(self.default_quotechar, self.parent)
        self.quotechar_widget.setMaxLength(1)
        self.quotechar_widget.setToolTip(self.quotechar_tooltip)

        # Delimiter
        self.delimiter_label = QLabel("Quote character")
        self.delimiter_widget = QLineEdit(self.default_delimiter, self.parent)
        self.delimiter_widget.setMaxLength(1)
        self.delimiter_widget.setToolTip(self.delimiter_tooltip)

        # Escape character
        self.escapechar_label = QLabel("Escape character")
        self.escapechar_widget = QLineEdit(self.parent)
        self.escapechar_widget.setMaxLength(1)
        self.escapechar_widget.setToolTip(self.escapechar_tooltip)

        # Quote style
        self.quoting_label = QLabel("Quote style")
        self.quoting_widget = QComboBox(self.parent)
        self.quoting_widget.addItems(self.quotings)
        if self.default_quoting in self.quotings:
            default_quoting_idx = self.quotings.index(self.default_quoting)
            self.quoting_widget.setCurrentIndex(default_quoting_idx)
        self.quoting_widget.setEditable(False)
        self.quoting_widget.setToolTip(self.quoting_widget_tooltip)

        # Header present
        self.hasheader_label = QLabel("Header present")
        self.hasheader_widget = QCheckBox(self.parent)
        self.hasheader_widget.setToolTip(self.hasheader_tooltip)

        # Double quote
        self.doublequote_label = QLabel("Doublequote")
        self.doublequote_widget = QCheckBox(self.parent)
        self.doublequote_widget.setToolTip(self.doublequote_tooltip)

        # Skip initial space
        self.skipinitialspace_label = QLabel("Skip initial space")
        self.skipinitialspace_widget = QCheckBox(self.parent)
        self.skipinitialspace_widget.setToolTip(self.skipinitialspace_tooltip)

        # Mapping to csv dialect

        self.csv_parameter2widget = {
            "encoding": self.encoding_widget,  # Extra dialect attribute
            "quotechar": self.quotechar_widget,
            "delimiter": self.delimiter_widget,
            "escapechar": self.escapechar_widget,
            "quoting": self.quoting_widget,
            "hasheader": self.hasheader_widget,  # Extra dialect attribute
            "doublequote": self.doublequote_widget,
            "skipinitialspace": self.skipinitialspace_widget,
        }

    def _layout(self):
        """Layout widgets"""

        hbox_layout = QHBoxLayout()
        left_form_layout = QFormLayout()
        right_form_layout = QFormLayout()

        hbox_layout.addLayout(left_form_layout)
        hbox_layout.addSpacing(20)
        hbox_layout.addLayout(right_form_layout)

        left_form_layout.setLabelAlignment(Qt.AlignRight)
        right_form_layout.setLabelAlignment(Qt.AlignRight)

        left_form_layout.addRow(self.encoding_label, self.encoding_widget)
        left_form_layout.addRow(self.quotechar_label, self.quotechar_widget)
        left_form_layout.addRow(self.delimiter_label, self.delimiter_widget)
        left_form_layout.addRow(self.escapechar_label, self.escapechar_widget)

        right_form_layout.addRow(self.quoting_label, self.quoting_widget)
        right_form_layout.addRow(self.hasheader_label, self.hasheader_widget)
        right_form_layout.addRow(self.doublequote_label,
                                 self.doublequote_widget)
        right_form_layout.addRow(self.skipinitialspace_label,
                                 self.skipinitialspace_widget)

        self.setLayout(hbox_layout)

    def adjust_csvdialect(self, dialect):
        """Adjusts csv dialect from widget settings

        Note that the dialect has two extra attributes encoding and hasheader

        """

        for parameter in self.csv_parameter2widget:
            widget = self.csv_parameter2widget[parameter]
            if hasattr(widget, "currentText"):
                value = widget.currentText()
            elif hasattr(widget, "isChecked"):
                value = widget.isChecked()
            elif hasattr(widget, "text"):
                value = widget.text()
            else:
                raise AttributeError("{} unsupported".format(widget))

            # Convert strings to csv constants
            if parameter == "quoting" and isinstance(value, str):
                value = getattr(csv, value)

            setattr(dialect, parameter, value)

        return dialect

    def set_csvdialect(self, dialect):
        """Update widgets from given csv dialect"""

        for parameter in self.csv_parameter2widget:
            try:
                value = getattr(dialect, parameter)
            except AttributeError:
                value = None

            if value is not None:
                widget = self.csv_parameter2widget[parameter]
                if hasattr(widget, "setCurrentText"):
                    try:
                        widget.setCurrentText(value)
                    except TypeError:
                        try:
                            widget.setCurrentIndex(value)
                        except TypeError:
                            pass
                elif hasattr(widget, "setChecked"):
                    widget.setChecked(bool(value))
                elif hasattr(widget, "setText"):
                    widget.setText(value)
                else:
                    raise AttributeError("{} unsupported".format(widget))


class CsvTable(QTableView):
    """Table for previewing csv file content"""

    no_rows = 9

    def __init__(self, parent):
        super().__init__(parent)

        self.comboboxes = []

        self.model = QStandardItemModel(self)
        self.setModel(self.model)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.verticalHeader().hide()

    def add_choice_row(self, length):
        """Adds row with comboboxes for digest choice"""

        class TypeCombo(QComboBox):
            def __init__(self):
                super().__init__()

                for typehandler in typehandlers:
                    self.addItem(typehandler)

        item_row = map(QStandardItem, [''] * length)
        self.comboboxes = [TypeCombo() for _ in range(length)]
        self.model.appendRow(item_row)
        for i, combobox in enumerate(self.comboboxes):
            self.setIndexWidget(self.model.index(0, i), combobox)

    def fill(self, filepath, dialect, digest_types=None):
        """Fills the csv table with values from the csv file"""

        self.model.clear()

        self.verticalHeader().hide()

        try:
            with open(filepath, newline='') as csvfile:
                if hasattr(dialect, 'hasheader') and dialect.hasheader:
                    header = get_header(csvfile, dialect)
                    self.model.setHorizontalHeaderLabels(header)
                    self.horizontalHeader().show()
                else:
                    self.horizontalHeader().hide()

                for i, row in enumerate(csv_reader(csvfile, dialect,
                                                   digest_types)):
                    if i >= self.no_rows:
                        break
                    elif i == 0:
                        self.add_choice_row(len(row))
                    if digest_types is None:
                        item_row = map(QStandardItem, map(str, row))
                    else:
                        codes = (convert(ele, t)
                                 for ele, t in zip(row, digest_types))
                        item_row = map(QStandardItem, codes)
                    self.model.appendRow(item_row)
        except OSError:
            return

    def get_digest_types(self):
        """Returns list of digest types from comboboxes"""

        return [cbox.currentText() for cbox in self.comboboxes]

    def update_comboboxes(self, digest_types):
        """Updates the cono boxes to show digest_types"""

        for combobox, digest_type in zip(self.comboboxes, digest_types):
            combobox.setCurrentText(digest_type)


class CsvImportDialog(QDialog):
    """Modal dialog for importing csv files

    :filepath: pathlib.Path to csv file

    """

    title = "CSV import"

    def __init__(self, parent, filepath):
        super().__init__(parent)

        self.parent = parent

        self.filepath = filepath

        self.sniff_size = parent.settings.sniff_size

        self.setWindowTitle(self.title)

        self.parameter_groupbox = CsvParameterGroupBox(self)
        self.csv_table = CsvTable(self)

        layout = QVBoxLayout(self)
        layout.addWidget(self.parameter_groupbox)
        layout.addWidget(self.csv_table)
        layout.addWidget(self.create_buttonbox())

        self.setLayout(layout)

        self.reset()

    def create_buttonbox(self):
        """Returns a QDialogButtonBox"""

        button_box = QDialogButtonBox(QDialogButtonBox.Reset
                                      | QDialogButtonBox.Apply
                                      | QDialogButtonBox.Ok
                                      | QDialogButtonBox.Cancel)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Reset).clicked.connect(self.reset)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

        return button_box

    # Button event handlers

    def reset(self):
        """Button event handler, resets parameter_groupbox and csv_table"""

        try:
            dialect = sniff(self.filepath, self.sniff_size)
        except OSError as error:
            self.parent.statusBar().showMessage(str(error))
            return
        self.parameter_groupbox.set_csvdialect(dialect)
        self.csv_table.fill(self.filepath, dialect)

    def apply(self):
        """Button event handler, applies parameters to csv_table"""

        try:
            sniff_dialect = sniff(self.filepath, self.sniff_size)
        except OSError as error:
            self.parent.statusBar().showMessage(str(error))
            return
        try:
            dialect = self.parameter_groupbox.adjust_csvdialect(sniff_dialect)
        except AttributeError as error:
            self.parent.statusBar().showMessage(str(error))
            return

        digest_types = self.csv_table.get_digest_types()
        self.csv_table.fill(self.filepath, dialect, digest_types)
        self.csv_table.update_comboboxes(digest_types)

    def accept(self):
        """Button event handler, starts csv import"""

        sniff_dialect = sniff(self.filepath, self.sniff_size)
        try:
            dialect = self.parameter_groupbox.adjust_csvdialect(sniff_dialect)
        except AttributeError as error:
            self.parent.statusBar().showMessage(str(error))
            self.reject()
            return

        digest_types = self.csv_table.get_digest_types()

        self.dialect = dialect
        self.digest_types = digest_types
        super().accept()


class CsvExportDialog(QDialog):
    """Modal dialog for exporting csv files

    :filepath: pathlib.Path to csv file

    """

    title = "CSV export"
    maxrows = 10

    def __init__(self, parent, csv_area):
        super().__init__(parent)

        self.parent = parent

        self.csv_area = csv_area

        self.dialect = self.default_dialect

        self.setWindowTitle(self.title)

        self.parameter_groupbox = CsvParameterGroupBox(self)
        self.csv_preview = QPlainTextEdit(self)
        self.csv_preview.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.parameter_groupbox)
        layout.addWidget(self.csv_preview)
        layout.addWidget(self.create_buttonbox())

        self.setLayout(layout)

        self.reset()

    @property
    def default_dialect(self):
        """Default dialect for export based on excel-tab"""

        dialect = csv.excel
        dialect.encoding = "utf-8"
        dialect.hasheader = False

        return dialect

    def reset(self):
        """Button event handler, resets parameter_groupbox and csv_preview"""

        self.parameter_groupbox.set_csvdialect(self.default_dialect)
        self.csv_preview.clear()

    def apply(self):
        """Button event handler, applies parameters to csv_preview"""

        top, left, bottom, right = self.csv_area
        table = self.parent.grid.table

        bottom = min(bottom-top, self.maxrows-1) + top

        code_array = self.parent.grid.model.code_array
        csv_data = code_array[top: bottom + 1, left: right + 1, table]

        adjust_csvdialect = self.parameter_groupbox.adjust_csvdialect
        dialect = adjust_csvdialect(self.default_dialect)

        str_io = io.StringIO()
        writer = csv.writer(str_io, dialect=dialect)
        writer.writerows(csv_data)

        self.csv_preview.setPlainText(str_io.getvalue())

    def accept(self):
        """Button event handler, starts csv import"""

        adjust_csvdialect = self.parameter_groupbox.adjust_csvdialect
        self.dialect = adjust_csvdialect(self.default_dialect)
        super().accept()

    def create_buttonbox(self):
        """Returns a QDialogButtonBox"""

        button_box = QDialogButtonBox(QDialogButtonBox.Reset
                                      | QDialogButtonBox.Apply
                                      | QDialogButtonBox.Ok
                                      | QDialogButtonBox.Cancel)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Reset).clicked.connect(self.reset)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply)

        return button_box


class TutorialDialog(QDialog):
    """Dialog for browsing the pyspread tutorial"""

    title = "pyspread tutorial"
    path = TUTORIAL_PATH / 'tutorial.md'
    baseurl = str(path.parent) + '/'

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle(self.title)

        self._create_widgets()
        self._layout()
        self.update_content()

    def _create_widgets(self):
        """Creates dialog browser"""

        self.browser = QTextBrowser(self)
        self.browser.setReadOnly(True)
        self.browser.setOpenExternalLinks(True)

    def _layout(self):
        """Dialog layout management"""

        layout = QHBoxLayout()
        layout.addWidget(self.browser)
        self.setLayout(layout)

    def update_content(self):
        """Update content of browser"""

        document = self.browser.document()
        document.setMetaInformation(QTextDocument.DocumentUrl,
                                    'file://' + str(TUTORIAL_PATH) + "/")
        with open(self.path) as helpfile:
            help_text = helpfile.read()

        help_html = markdown(help_text, extras=['metadata'])
        self.browser.setHtml(help_html)

    # Overrides

    def sizeHint(self):
        return QSize(1000, 800)


class ManualNavigator:
    """Navigation markdown text generator for manual"""

    filename2title = {
        "overview.md": "Overview",
        "basic_concepts.md": "Concepts",
        "workspace.md": "Workspace",
        "file_menu.md": "File",
        "edit_menu.md": "Edit",
        "view_menu.md": "View",
        "format_menu.md": "Format",
        "macro_menu.md": "Macro",
        "advanced_topics.md": "Advanced topics",
    }

    def __init__(self, path):
        self.path = path

    def __str__(self):
        return " | ".join(self.md_title(fn) for fn in self.filename2title)

    def md_title(self, filename):
        """Returns title for filename in markdown.

        The filename is bold if filename == self.filename.

        """

        if filename == self.path.name:
            tpl = "[**{}**]({})"
        else:
            tpl = "[{}]({})"

        return tpl.format(self.filename2title[filename],
                          self.path.parent / filename)


class ManualDialog(QDialog):
    """Dialog for browsing the pyspread manual"""

    title = "pyspread manual"
    path = MANUAL_PATH / 'overview.md'
    baseurl = str(MANUAL_PATH) + '/'

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle(self.title)

        self._create_widgets()
        self._layout()
        self.update_content()

        self.browser.sourceChanged.connect(self.on_update)

    def _create_widgets(self):
        """Creates dialog browser"""

        self.browser = QTextBrowser(self)
        self.browser.setReadOnly(True)
        self.browser.setOpenExternalLinks(True)

    def _layout(self):
        """Dialog layout management"""

        layout = QHBoxLayout()
        layout.addWidget(self.browser)
        self.setLayout(layout)

    def update_content(self):
        """Update content of browser"""

        document = self.browser.document()
        document.setMetaInformation(QTextDocument.DocumentUrl,
                                    'file://' + self.baseurl + "/")

        header_text = str(ManualNavigator(self.path)) + '\n \n-----------'
        header_html = markdown(header_text)

        footer_text = '-----------\n' + str(ManualNavigator(self.path))
        footer_html = markdown(footer_text)

        with open(self.path) as helpfile:
            help_text = helpfile.read()

        help_html = "".join([header_html,
                             markdown(help_text, extras=['metadata',
                                                         'code-friendly',
                                                         'fenced-code-blocks',
                                                         'tables']),
                             footer_html])
        self.browser.setHtml(help_html)

    def on_update(self, url):
        """Replaces html url with markdown file and adds proper path"""

        self.path = MANUAL_PATH / url.path()
        if self.path.suffix == ".html":
            self.path = self.path.with_suffix(".md")
        self.update_content()

    # Overrides

    def sizeHint(self):
        return QSize(1000, 800)


class PrintPreviewDialog(QPrintPreviewDialog):
    """Adds Mouse wheel functionality"""

    def __init__(self, printer):
        super().__init__(printer)
        self.toolbar = self.findChildren(QToolBar)[0]
        self.actions = self.toolbar.actions()
        self.widget = self.findChildren(QPrintPreviewWidget)[0]
        self.combo_zoom = self.toolbar.widgetForAction(self.actions[3])

    def wheelEvent(self, event):
        """Overrides mouse wheel event handler"""

        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                zoom_factor = self.widget.zoomFactor() / 1.1
            else:
                zoom_factor = self.widget.zoomFactor() * 1.1
            self.widget.setZoomFactor(zoom_factor)
            self.combo_zoom.setCurrentText(str(round(zoom_factor*100, 1))+"%")
        else:
            super().wheelEvent(event)
