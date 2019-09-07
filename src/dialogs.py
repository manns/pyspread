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

dialogs
-------

Modal dialogs for pyspread

 * DiscardChangesDialog
 * ApproveWarningDialog
 * DataEntryDialog
 * GridShapeDialog
 * (FileDialogBase)
 * FileOpenDialog
 * FileSaveDialog
 * ImageFileOpenDialog
 * ChartDialog

"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QDialog, QLineEdit
from PyQt5.QtWidgets import QLabel, QFormLayout, QVBoxLayout, QGroupBox
from PyQt5.QtWidgets import QDialogButtonBox, QSplitter, QTextBrowser
from PyQt5.QtGui import QIntValidator, QImageWriter

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
except ImportError:
    Figure = None

from lib.spelltextedit import SpellTextEdit
from actions import ChartDialogActions
from toolbar import ChartTemplatesToolBar
from icons import PYSPREAD_PATH

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

    """

    def __init__(self, parent, title, labels, initial_data=None,
                 groupbox_title=None, validator=None):
        super(QDialog, self).__init__(parent)

        self.labels = labels
        self.groupbox_title = groupbox_title
        self.validator = validator

        if initial_data is None:
            self.initial_data = [""] * len(labels)
        else:
            if len(initial_data) != len(labels):
                raise ValueError("Length of labels and initial_data not equal")
            self.initial_data = initial_data

        self.editors = []

        layout = QVBoxLayout(self)
        layout.addWidget(self.create_form())
        layout.addWidget(self.create_buttonbox())
        self.setLayout(layout)

        self.setWindowTitle(title)

    @property
    def data(self):
        """Executes the dialog and returns a tuple of strings

        Returns None if the dialog is canceled

        """

        result = self.exec_()

        if result == QDialog.Accepted:
            data = tuple(editor.text() for editor in self.editors)
            if all(data):
                return data
            # At least one field was empty or contained no number

    def create_form(self):
        """Returns form inside a QGroupBox"""

        form_group_box = QGroupBox()
        if self.groupbox_title:
            form_group_box.setTitle(self.groupbox_title)
        form_layout = QFormLayout()

        for label, initial_value in zip(self.labels, self.initial_data):
            editor = QLineEdit(str(initial_value))
            editor.setAlignment(Qt.AlignRight)
            if self.validator:
                editor.setValidator(self.validator)
            form_layout.addRow(QLabel(label), editor)
            self.editors.append(editor)

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

    def __init__(self, parent, shape):
        title = "Create a new grid"
        groupbox_title = "Grid shape"
        validator = QIntValidator()
        validator.setBottom(0)  # Do not allow negative values
        labels = ["Number of rows", "Number of columns", "Number of tables"]
        super(GridShapeDialog, self).__init__(parent, title, labels, shape,
                                              groupbox_title, validator)

    @property
    def shape(self):
        """Executes the dialog and returns an int tuple rows, columns, tables

        Returns None if the dialog is canceled

        """

        data = self.data
        if data is not None:
            return tuple(map(int, data))


class PreferencesDialog(QDialog):
    """Modal dialog for entering pyspread preferences"""

    def __init__(self, parent):
        super(PreferencesDialog, self).__init__(parent)

        self.settings = parent.settings

        layout = QVBoxLayout(self)
        layout.addWidget(self.create_form())
        layout.addWidget(self.create_buttonbox())
        self.setLayout(layout)

        self.setWindowTitle("Preferences")

    @property
    def data(self):
        """Executes the dialog and returns a dict containing preferences data

        Returns None if the dialog is canceled

        """

        result = self.exec_()

        if result == QDialog.Accepted:
            try:
                unredo = int(self.unredo_edit.text())
                timeout = int(self.timeout_edit.text())
                max_result_length = int(self.max_result_length_edit.text())
            except ValueError:
                # At least one field was empty or contained no number
                return

            return {"unredo": unredo,
                    "timeout": timeout,
                    "max_result_length": max_result_length}

    def create_form(self):
        """Returns form inside a QGroupBox"""

        form_group_box = QGroupBox("Global settings")
        form_layout = QFormLayout()

        validator = QIntValidator()
        validator.setBottom(0)  # Do not allow negative values

        self.unredo_edit = QLineEdit(str(self.settings.max_unredo))
        self.unredo_edit.setAlignment(Qt.AlignRight)
        self.unredo_edit.setValidator(validator)
        form_layout.addRow(QLabel("Number of undo steps"), self.unredo_edit)

        self.timeout_edit = QLineEdit(str(self.settings.timeout))
        self.timeout_edit.setAlignment(Qt.AlignRight)
        self.timeout_edit.setValidator(validator)
        form_layout.addRow(QLabel("Cell calculation timeout [s]"),
                           self.timeout_edit)

        self.max_result_length_edit = \
            QLineEdit(str(self.settings.max_result_length))
        self.max_result_length_edit.setAlignment(Qt.AlignRight)
        self.max_result_length_edit.setValidator(validator)
        form_layout.addRow(QLabel("Maximum length of cell result strings"),
                           self.max_result_length_edit)

        form_group_box.setLayout(form_layout)

        return form_group_box

    def create_buttonbox(self):
        """Returns a QDialogButtonBox with Ok and Cancel"""

        button_box = QDialogButtonBox(QDialogButtonBox.Ok
                                      | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        return button_box


class FileDialogBase:
    """Base class for modal file dialogs

    The choosen filename is stored in the filepath attribute
    The choosen name filter is stored in the chosen_filter attribute
    If the dialog is aborted then both filepath and chosen_filter are None

    _get_filepath must be overloaded

    """

    title = "Choose file"
    name_filter = "Pyspread uncompressed (*.pysu);;" + \
                  "Pyspread compressed (*.pys)"
    filepath = None
    chosen_filter = None

    def __init__(self, main_window):
        self.main_window = main_window
        self.filepath, self.chosen_filter = self._get_filepath()


class FileOpenDialog(FileDialogBase):
    """Modal dialog for choosing a pyspread file"""

    title = "Open"

    def _get_filepath(self):
        """Returns (filepath, chosen_filter) from modal user dialog"""

        path = self.main_window.application_states.last_file_input_path
        filepath, chosen_filter = \
            QFileDialog.getOpenFileName(self.main_window, self.title,
                                        str(path), self.name_filter)
        return filepath, chosen_filter


class FileSaveDialog(FileDialogBase):
    """Modal dialog for choosing a pyspread save file"""

    title = "Save"

    def _get_filepath(self):
        """Returns (filepath, chosen_filter) from modal user dialog"""

        path = self.main_window.application_states.last_file_output_path
        filepath, chosen_filter = \
            QFileDialog.getSaveFileName(self.main_window, self.title,
                                        str(path), self.name_filter)
        return filepath, chosen_filter


class ImageFileOpenDialog(FileDialogBase):
    """Modal dialog for inserting an image"""

    title = "Insert image"

    img_formats = QImageWriter.supportedImageFormats()
    img_format_strings = ("*." + fmt.data().decode('utf-8')
                          for fmt in img_formats)
    img_format_string = " ".join(img_format_strings)
    name_filter = "Images ({})".format(img_format_string) + ";;" \
                  "Scalable Vector Graphics (*.svg *.svgz)"

    def _get_filepath(self):
        """Returns (filepath, chosen_filter) from modal user dialog"""

        path = self.main_window.application_states.last_file_input_path
        filepath, chosen_filter = \
            QFileDialog.getOpenFileName(self.main_window,
                                        self.title,
                                        str(path),
                                        self.name_filter)
        return filepath, chosen_filter


class ChartDialog(QDialog):
    """The chart dialog"""

    def __init__(self, parent):
        if Figure is None:
            raise ModuleNotFoundError

        super(ChartDialog, self).__init__(parent)

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
