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

**Provides**

* :class:`Module`
* :class:`DependenciesDialog`
* :class:`InstallPackageDialog`

"""


try:
    from dataclasses import dataclass
except ImportError:
    # Python 3.6 compatibility
    from pyspread.lib.dataclasses import dataclass
import os

try:
    from pkg_resources import get_distribution, DistributionNotFound
except ImportError:
    get_distribution = None
from PyQt5.QtCore import QProcess, QSize
from PyQt5.QtGui import QColor, QTextCursor
from PyQt5.QtWidgets import (
        QDialog, QButtonGroup, QVBoxLayout, QHBoxLayout, QTreeWidgetItem,
        QToolButton, QGroupBox, QTreeWidget, QCheckBox, QLineEdit,
        QPlainTextEdit, QWidget, QPushButton)

try:
    from packaging import version
except ImportError:
    # We fall back to local library to remove the dependency
    try:
        from pyspread.lib.packaging import version
    except ImportError:
        from lib.packaging import version
try:
    from pyspread.lib.attrdict import AttrDict
except ImportError:
    from lib.attrdict import AttrDict


@dataclass
class Module:
    """Module checker"""

    name: str
    description: str
    required_version: str  # The minimum version number that is required

    @property
    def version(self) -> version:
        """Currently installed version number, False if not installed"""

        if get_distribution is None:
            return
        try:
            return version.parse(get_distribution(self.name).version)
        except DistributionNotFound:
            return False

    def is_installed(self) -> bool:
        """True if the module is installed"""

        __version = self.version

        return bool(__version) if __version is not None else None

# Required dependencies
# ---------------------

# Required dependencies are checked by the cli


REQUIRED_DEPENDENCIES = [
    Module(name="numpy",
           description="Fundamental package for scientific computing",
           required_version=version.parse("1.1")),
    Module(name="PyQt5",
           description="Python bindings for the Qt application framework",
           required_version=version.parse("5.10")),
]

# Optional dependencies
# ---------------------


OPTIONAL_DEPENDENCIES = [
    Module(name="matplotlib",
           description="Create charts",
           required_version=version.parse("1.1.1")),
    Module(name="pyenchant",
           description="Spell checker",
           required_version=version.parse("1.1")),
]

PIP_MODULE = Module(name="pip", description="pip installer",
                    required_version=version.parse("17.0"))

# Not yet implemented modules
#    Module(name="xlrd",
#           description="Load Excel files",
#           required_version="0.9.2"),
#    Module(name="xlwt",
#           description="Save Excel files",
#           required_version="0.9.2"),


class DependenciesDialog(QDialog):
    """Dependencies dialog for python dependencies"""

    column = AttrDict(zip(("button", "status", "name", "version",
                           "required_version", "description"), range(6)))
    column_headers = ("", "Status", "Package", "Version", "Required",
                      "Description")

    def __init__(self, parent: QWidget = None):
        """
        :param parent: Parent widget

        """

        super().__init__(parent)

        self.setWindowTitle("Installer")

        # Button group for install buttons
        self.buttGroup = QButtonGroup()
        self.buttGroup.buttonClicked.connect(self.on_butt_install)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.mainLayout)

        self.tree = QTreeWidget()
        self.mainLayout.addWidget(self.tree, 4)

        self.tree.setHeaderLabels(self.column_headers)
        self.tree.setRootIsDecorated(False)
        self.tree.setSelectionMode(QTreeWidget.NoSelection)

        self.update_load()

    def sizeHint(self) -> QSize:
        """Overloaded method"""

        return QSize(700, 200)

    def update_load(self):

        self.tree.clear()

        for idx, module in enumerate(OPTIONAL_DEPENDENCIES):
            item = QTreeWidgetItem()
            item.setText(self.column.name, module.name)
            version = module.version if module.version else "Not installed"
            item.setText(self.column.version, str(version))
            item.setText(self.column.required_version,
                         str(module.required_version))
            item.setText(self.column.description, module.description)
            self.tree.addTopLevelItem(item)

            if module.is_installed():
                color = "#DBFEAC"
                status = "Installed"
            elif module.is_installed() is None:
                color = "#666666"
                status = "pkg_resources is missing"
            else:
                status = "Not installed"
                color = "#F3FFBB"
                butt = QToolButton()
                butt.setText("Install")
                butt.setEnabled(PIP_MODULE.is_installed())
                self.tree.setItemWidget(item, self.column.button, butt)
                self.buttGroup.addButton(butt, idx)

            item.setText(self.column.status, status)
            item.setBackground(self.column.status, QColor(color))

    def on_butt_install(self, butt: QPushButton):
        """One of install buttons pressed

        :param butt: The pressed button

        """

        butt.setDisabled(True)
        idx = self.buttGroup.id(butt)

        dial = InstallPackageDialog(self, module=OPTIONAL_DEPENDENCIES[idx])
        dial.exec_()
        self.update_load()


class InstallPackageDialog(QDialog):
    """Shows a dialog to execute command"""

    line_str = "-" * 56

    def __init__(self, parent=None, module=None):
        """
        :param parent: Parent widget
        :param module: Module to be installed

        """

        super().__init__(parent)

        self.module = module

        self.setWindowTitle("Install Package")
        self.setMinimumWidth(600)

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.on_read_standard)
        self.process.readyReadStandardError.connect(self.on_read_error)
        self.process.finished.connect(self.on_finished)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.mainLayout)

        self.groupBox = QGroupBox()
        self.groupBox.setTitle("Shell Command")
        self.groupBoxLayout = QHBoxLayout()
        self.groupBox.setLayout(self.groupBoxLayout)
        self.mainLayout.addWidget(self.groupBox)

        self.buttSudo = QCheckBox()
        self.buttSudo.setText("sudo")
        self.groupBoxLayout.addWidget(self.buttSudo, 0)
        self.buttSudo.toggled.connect(self.update_cmd_line)
        self.buttSudo.setVisible(os.name != "nt")

        self.txtCommand = QLineEdit()
        self.groupBoxLayout.addWidget(self.txtCommand, 10)

        self.buttExecute = QPushButton()
        self.buttExecute.setText("Execute")
        self.groupBoxLayout.addWidget(self.buttExecute, 0)
        self.buttExecute.clicked.connect(self.on_butt_execute)

        self.txtStdOut = QPlainTextEdit()
        self.mainLayout.addWidget(self.txtStdOut)

        self.txtStdErr = QPlainTextEdit()
        self.mainLayout.addWidget(self.txtStdErr)

        self.update_cmd_line()

    def update_cmd_line(self, *unused):
        """Update the commend line considering sudo button state"""

        cmd = ""
        if self.buttSudo.isChecked():
            cmd += "pkexec  "

        cmd += "pip3 install {modulename}".format(modulename=self.module.name)

        self.txtCommand.setText(cmd)

    def on_butt_execute(self):
        """Execute button event handler"""

        self.buttSudo.setDisabled(True)
        self.buttExecute.setDisabled(True)

        self.txtStdOut.setPlainText("")
        self.txtStdErr.setPlainText("")
        self.process.start(self.txtCommand.text())

    def on_read_standard(self):
        """Stdout read event handler"""

        msg_tpl = "{}\n{}\n{}"
        msg = msg_tpl.format(self.txtStdOut.toPlainText(),
                             self.line_str,
                             self.process.readAllStandardOutput())

        self.txtStdOut.setPlainText(msg)
        self.txtStdOut.moveCursor(QTextCursor.End)

    def on_read_error(self):
        """Stderr read event handler"""

        msg_tpl = "{}\n{}\n{}"
        msg = msg_tpl.format(self.txtStdErr.toPlainText(),
                             self.line_str,
                             self.process.readAllStandardError())

        self.txtStdErr.setPlainText(msg)
        self.txtStdErr.moveCursor(QTextCursor.End)

    def on_finished(self):
        """Execution finished event handler"""

        self.buttSudo.setDisabled(False)
        self.buttExecute.setDisabled(False)
