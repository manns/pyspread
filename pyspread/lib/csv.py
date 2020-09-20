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

"""

**Provides**

 * :func:`sniff`: Sniffs CSV dialect and header info
 * :func:`get_header`
 * :func:`csv_reader`
 * :func:`convert`
 * :func:`date`
 * :func:`datetime`
 * :func:`time`
 * :func:`make_object`
 * :dict:`typehandlers`

"""

import ast
import csv
from dateutil.parser import parse
from pathlib import Path
from typing import TextIO, Iterable, List


def sniff(filepath: Path, sniff_size: int) -> csv.Dialect:
    """Sniffs CSV dialect and header info

    :param filepath: Path of file to sniff
    :param sniff_size: Maximum no. bytes to use for sniffing
    :return: csv.Dialect object with additional attribute `has_header`

    """

    with open(filepath, newline='', encoding='utf-8') as csvfile:
        csv_str = csvfile.read(sniff_size)

    dialect = csv.Sniffer().sniff(csv_str)
    setattr(dialect, "hasheader", csv.Sniffer().has_header(csv_str))

    return dialect


def get_header(csvfile: TextIO, dialect: csv.Dialect) -> List[str]:
    """Returns list of first line items of file filepath"""

    csvfile.seek(0)
    csvreader = csv.reader(csvfile, dialect=dialect)
    for header in csvreader:
        break

    csvfile.seek(0)
    return header


def csv_reader(csvfile: TextIO, dialect: csv.Dialect) -> Iterable[str]:
    """Generator of str values from csv file in filepath, ignores header

    :param csvfile: Csv file to read
    :param dialect: Csv dialect

    """

    csvreader = csv.reader(csvfile, dialect=dialect)
    try:
        ignore_header = dialect.hasheader and not dialect.keepheader
    except AttributeError:
        try:
            ignore_header = dialect.hasheader
        except AttributeError:
            ignore_header = False

    if ignore_header:
        for line in csvreader:
            break

    for line in csvreader:
        yield line


# Type conversion functions

def convert(string: str, digest_type: str) -> str:
    """Main type conversion function for csv import

    :param string: String to be digested
    :param digest_type: Name of digetsion function
    :return: Converted string

    """

    if digest_type is None:
        digest_type = 'repr'

    try:
        return repr(typehandlers[digest_type](string))

    except Exception:
        return repr(string)


def date(obj):
    """Makes a date from comparable types"""

    return parse(obj).date()


def datetime(obj):
    """Makes a datetime from comparable types"""

    return parse(obj)


def time(obj):
    """Makes a time from comparable types"""

    return parse(obj).time()


def make_object(obj):
    """Parses the object with ast.literal_eval"""

    return ast.literal_eval(obj)


typehandlers = {
    'object': ast.literal_eval,
    'repr': lambda x: x,
    'bool': bool,
    'int': int,
    'float': float,
    'complex': complex,
    'str': str,
    'bytes': bytes,
    'date': date,
    'datetime': datetime,
    'time': time,
}
