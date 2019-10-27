#!/usr/bin/env python
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


from setuptools import setup
from setuptools.command.test import test as TestCommand
import sys

from src import VERSION


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ""

    def run_tests(self):
        import shlex

        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


setup(
    name='pyspread',
    version=VERSION,
    description='Python spreadsheet',
    long_description='Pyspread is a non-traditional spreadsheet application'
    ' that is based on and written in the programming language Python.',
    license='GPL v3 :: GNU General Public License',
    keywords=['spreadsheet', 'pyspread'],
    author='Martin Manns',
    author_email='mmanns@gmx.net',
    url='http://manns.github.io/pyspread/',
    requires=['numpy (>=1.1)', 'PyQt5 (>=5.11.3)', 'matplotlib (>=1.1.1)'],
#    extras_require = {
#        'GPG': ['gnupg>=0.3.0'],
#        'SVG': [],  # May require python_rsvg if not shipped with pyCairo
#        'XLS': ['xlrd>=0.9.1', 'xlwt>=0.7.5'],
#        'code_completion': ['jedi>=0.8'],
#        'basemap': ['basemap>=1.0.7'],
#    },
    tests_require=["pytest"],
    cmdclass={"pytest": PyTest},
    packages=['pyspread'],
    scripts=['src/pyspread.py'],
    cmdclass={'test': PyTest},
    package_data={'pyspread': [
            '*.py',
            '../pyspread.sh',
            '../pyspread.bat',
            '../runtests.py',
            'src/*.py',
            'src/pyspread',
            'src/*/*.py',
            'src/*/test/*.py',
            'src/*/test/*.pys*',
            'src/*/test/*.sig',
            'src/*/test/*.csv',
            'src/*/test/*.xls',
            'src/*/test/*.txt',
            'src/*/test/*.svg',
            'src/*/test/*.pys*',
            'share/icons/*.svg',
            'share/icons/*.ico',
            'share/icons/actions/*.svg',
            'share/icons/status/*.svg',
            'doc/help/*.html',
            'doc/help/images/*.png',
            'share/templates/*/*.py',
            'COPYING',
            'thanks',
            'faq',
            '*.1',
            'authors',
            '../pyspread.pth',
            '../README',
            '../changelog'
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: GTK',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Operating System :: Microsoft',
        'Programming Language :: Python :: 3.7',
        'Topic :: Office/Business :: Financial :: Spreadsheet',
    ],
)
