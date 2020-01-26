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


from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import sys

from src import VERSION


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = "--capture=sys"

    def run_tests(self):
        import shlex

        # import here, cause outside the eggs aren't loaded
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args))
        sys.exit(errno)


setup(
    name='pyspread',
    version=VERSION,
    packages=find_packages(),
    package_dir={'': '.'},
    scripts=['pyspread.sh'],
    include_package_data=True,
    description='Python spreadsheet',
    long_description='Pyspread is a non-traditional spreadsheet application'
    ' that is based on and written in the programming language Python.',
    license='GPL v3 :: GNU General Public License',
    keywords=['spreadsheet', 'pyspread'],
    author='Martin Manns',
    author_email='mmanns@gmx.net',
    url='https://pyspread.gitlab.io/',
    project_urls={
        "Bug Tracker": "https://gitlab.com/pyspread/pyspread/issues",
        "Documentation": "https://pyspread.gitlab.io/docs.html",
        "Source Code": "https://gitlab.com/pyspread/pyspread",
    },
    requires=['numpy (>=1.1)', 'PyQt5 (>=5.11.3)'],
    extras_require={
        'matplotlib': ['matplotlib (>=1.1.1)'],
        'pyenchant': ['pyenchant (>=1.1)'],
    },
    tests_require=["pytest"],
    cmdclass={"pytest": PyTest},
    classifiers=[
        'Development Status :: 3 - Alpha',
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
