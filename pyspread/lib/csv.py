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
csv
===

Provides
--------

 * sniff: Sniffs CSV dialect and header info
 * get_first_line
 * csv_digest_gen
 * cell_key_val_gen
 * Digest: Converts any object to target type as good as possible
 * CsvInterface
 * TxtGenerator

"""

import ast
import csv
from dateutil.parser import parse


def sniff(filepath, sniff_size):
    """Sniffs CSV dialect and header info

    :filepath: pathlib.Path: Path of file to sniff
    :sniffsize: int: Maximum no. bytes to use for sniffing

    Returns a csv.Dialect object with additional attrinbute has_header

    """

    with open(filepath, newline='') as csvfile:
        csv_str = csvfile.read(sniff_size)

    dialect = csv.Sniffer().sniff(csv_str)
    setattr(dialect, "hasheader", csv.Sniffer().has_header(csv_str))

    return dialect


def get_header(csvfile, dialect):
    """Returns List of first line items of file filepath"""

    csvfile.seek(0)
    csvreader = csv.reader(csvfile, dialect=dialect)
    for header in csvreader:
        break

    csvfile.seek(0)
    return header


def csv_reader(csvfile, dialect, digest_types=None):
    """Generator of digested values from csv file in filepath

    Parameters
    ----------
    csvfile:filelike
    \tCsv file to read
    dialect: Object
    \tCsv dialect
    digest_types: tuple of types
    \tTypes of data for each col

    """

    csvreader = csv.reader(csvfile, dialect=dialect)

    if hasattr(dialect, "hasheader") and dialect.hasheader:
        # Ignore first line
        for line in csvreader:
            break

    for line in csvreader:
        yield line


# Type conversion functions

def convert(string, digest_type):
    """Main type conversion functgion for csv import"""

    if digest_type is None:
        digest_type = 'repr'

    try:
        return str(typehandlers[digest_type](string))

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
    'repr': repr,
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
