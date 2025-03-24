"""
Compressedbuf read/write support.

Mainly used for NWSync file storage; but also used in sqlite files such as
nwsync storage and string/blob compression in campaign sqlite databases.

Binary Format
=============

+-------------------+-------------------+--------------------------------------+
| Field             | Size (bytes)      | Description                          |
+===================+===================+======================================+
| Magic             | 4                 | `FileMagic`                          |
+-------------------+-------------------+--------------------------------------+
| Header Version    | 4                 | Format version (currently always 3)  |
+-------------------+-------------------+--------------------------------------+
| Algorithm         | 4                 | `Algorithm`                          |
+-------------------+-------------------+--------------------------------------+
| Uncompressed Size | 4                 | Size of the uncompressed data        |
+-------------------+-------------------+--------------------------------------+
| Algorithm Version | 4 (if ZLIB/ZSTD)  | Version of the compression algorithm |
|                   |                   | (currently always 1)                 |
+-------------------+-------------------+--------------------------------------+
| Dictionary        | 4 (if ZSTD)       | Dictionary ID (currently always 0)   |
+-------------------+-------------------+--------------------------------------+
| Compressed Data   | Variable          | The compressed data                  |
+-------------------+-------------------+--------------------------------------+
"""

from enum import IntEnum
from typing import BinaryIO
import zlib

import pyzstd

from ._shared import FileMagic


class Algorithm(IntEnum):
    NONE = 0
    ZLIB = 1
    """Deprecated, use ZSTD instead."""
    ZSTD = 2


_VERSION = 3
_ZLIB_VERSION = 1
_ZSTD_VERSION = 1


def read(
    file: BinaryIO, expect_magic: FileMagic = None
) -> tuple[bytes, int, Algorithm]:
    """
    Decompresses the given binary file using the specified algorithm.

    Args:
        file: The binary file to decompress.
        expect_magic: The expected file magic. If provided,
            the file magic read from the file must match this value.

    Returns:
        A tuple containing the decompressed data, the file magic, and the algorithm used.

    Raises:
        ValueError: If the stream is invalid, or the magic number does not
            match the expected value, or if an unsupported algorithm is encountered.
    """

    magic = file.read(4)
    if expect_magic is not None and magic != expect_magic:
        raise ValueError(f"invalid magic: {magic}")

    header_version = int.from_bytes(file.read(4), "little")
    if header_version != _VERSION:
        raise ValueError(f"invalid header version: {header_version}")

    algorithm = int.from_bytes(file.read(4), "little")
    uncompressed_size = int.from_bytes(file.read(4), "little")

    if uncompressed_size == 0:
        return (b"", magic, algorithm)

    if algorithm == Algorithm.NONE:
        return (file.read(uncompressed_size), magic, algorithm)

    elif algorithm == Algorithm.ZLIB:
        vers = int.from_bytes(file.read(4), "little")
        if vers != _ZLIB_VERSION:
            raise ValueError(f"invalid zlib header version: {vers}")
        return (zlib.decompress(file.read()), magic, algorithm)

    elif algorithm == Algorithm.ZSTD:
        vers = int.from_bytes(file.read(4), "little")
        if vers != _ZSTD_VERSION:
            raise ValueError(f"invalid zstd header version: {vers}")
        dictionary = int.from_bytes(file.read(4), "little")
        if dictionary != 0:
            raise ValueError("dictionaries are not supported")

        return (pyzstd.decompress(file.read()), magic, algorithm)

    else:
        raise ValueError("Unsupported algorithm")


def write(file: BinaryIO, magic: FileMagic, data: bytes, alg=Algorithm.ZSTD):
    """
    Compresses the given data and writes it to the specified file using the specified algorithm.

    Args:
        file: The file object to write the compressed data to.
        magic: The file magic to write.
        data: The data to be compressed.
        alg (Algorithm, optional): The compression algorithm to use. Defaults to Algorithm.ZSTD.

    Raises:
        ValueError: If an unsupported algorithm is specified.
    """

    file.write(magic)
    file.write(_VERSION.to_bytes(4, "little"))
    file.write(alg.to_bytes(4, "little"))
    file.write(len(data).to_bytes(4, "little"))

    if alg == Algorithm.NONE:
        file.write(data)

    elif alg == Algorithm.ZLIB:
        file.write(_ZLIB_VERSION.to_bytes(4, "little"))
        file.write(zlib.compress(data))

    elif alg == Algorithm.ZSTD:
        file.write(_ZSTD_VERSION.to_bytes(4, "little"))
        file.write((0).to_bytes(4, "little"))  # dictionary
        file.write(pyzstd.compress(data))

    else:
        raise ValueError("Unsupported algorithm")
