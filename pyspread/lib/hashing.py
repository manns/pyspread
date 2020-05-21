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


def genkey(nbytes: int = 64) -> bytes:
    """Returns a random byte sting that may be used as signature key

    :param nbytes: Length of key
    :return: Random byte string of length nbytes

    """

    return secrets.token_bytes(nbytes)


def sign(data: bytes, key: bytes) -> bytes:
    """Returns signature for file using blake2b

    Note: 64 bytes is the maximum that is supported in Python's BLAKE2b

    :param data: Data to be signed
    :param key: Signature key, len(key) <= 64
    :return: File signature hexdigest, encoded in utf-8

    """

    if not key:
        raise ValueError("No signature key defined")

    if not isinstance(key, bytes):
        key = ast.literal_eval(key)

    if len(key) > blake2b.MAX_KEY_SIZE:
        raise Warning("Key is too long and has been truncated")
        key = key[:blake2b.MAX_KEY_SIZE]

    signature = blake2b(digest_size=64, key=key)
    signature.update(data)

    return signature.hexdigest().encode('utf-8')


def verify(data: bytes, signature: bytes, key: bytes) -> bool:
    """Verifies a signature

    :param data: Data to be verified
    :param signature: Signature for verification
    :param key: Signature key, len(key) <= 64
    :return: True if verification was successful else False

    """

    data_signature = sign(data, key)
    return compare_digest(data_signature, signature)
