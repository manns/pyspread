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

* :class:`CommandLineParser`:

"""

from argparse import Action, ArgumentParser
from pathlib import Path
import sys

from __init__ import APP_NAME, VERSION
from installer import REQUIRED_DEPENDENCIES


class PathAction(Action):
    """Action that handles paths with spaces and provides a pathlib Path"""

    def __call__(self, parser, namespace, values, option_string=None):
        if values:
            setattr(namespace, self.dest, Path(" ".join(values)))
        else:
            setattr(namespace, self.dest, None)


class ArgumentParser(ArgumentParser):
    """Parser for the command line"""

    def __init__(self):

        self.check_mandatory_dependencies()

        description = "pyspread is a non-traditional spreadsheet that is " \
                      "based on and written in the programming language " \
                      "Python."

        # Override usage because of the PathAction fix for paths with spaces
        usage = "{} [-h] [--version] [file]".format(APP_NAME)

        super().__init__(prog=APP_NAME, description=description, usage=usage)

        self.add_argument('--version', action='version', version=VERSION)
        self.add_argument('file', action=PathAction, nargs="*",
                          help='open pyspread file in pys or pysu format')

    def check_mandatory_dependencies(self):
        """Checks mandatory dependencies and exits if they are not met"""

        # Check Python version
        major = sys.version_info.major
        minor = sys.version_info.minor
        micro = sys.version_info.micro
        if major < 3 or major == 3 and minor < 6:
            msg_tpl = "Python has version {}.{}.{} but ≥ 3.6 is required."
            msg = msg_tpl.format(major, minor, micro)
            self.dependency_error(msg)

        for module in REQUIRED_DEPENDENCIES:
            if not module.is_installed():
                msg_tpl = "Required module {} not found."
                msg = msg_tpl.format(module.name)
                self.dependency_error(msg)
            elif module.version < module.required_version:
                msg_tpl = "Module {} has version {} but {} is required."
                msg = msg_tpl.format(module.name, module.version,
                                     module.required_version)
                self.dependency_error(msg)
        try:
            import PyQt5.QtSvg
        except ImportError:
            msg = "Required module PyQt5.QtSvg not found."
            self.dependency_error(msg)

    def dependency_error(self, message):
        """Print dependency error message and quit"""

        sys.stderr.write('error: {}\n'.format(message))
        sys.exit(2)
