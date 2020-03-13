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

File hashing services

**Provides**

 * :func:`genkey` - Generates hash key
 * :func:`sign` - Returns a signature for a given file
 * :func:`verify` - Verifies file against signature

"""

import ast

from hashlib import blake2b
from hmac import compare_digest
import secrets


def genkey(nbytes=64):
    """Returns a new signature key of nbytes

    64 bytes is recommended for BLAKE2b

    """

    return secrets.token_bytes(nbytes)


def sign(data, key):
    """Returns signature for file"""

    if not key:
        raise ValueError("No signature key defined")

    if not isinstance(key, bytes):
        key = ast.literal_eval(key)

    signature = blake2b(digest_size=64, key=key)
    signature.update(data)

    return signature.hexdigest().encode('utf-8')


def verify(data, signature, key):
    """Verifies a signature, returns True if successful else False"""

    if not isinstance(key, bytes):
        key = ast.literal_eval(key)

    data_signature = sign(data, key)
    return compare_digest(data_signature, signature)
