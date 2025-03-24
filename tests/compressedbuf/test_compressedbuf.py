import io

import pytest

from nwn.compressedbuf import (
    write,
    read,
    Algorithm,
)

from nwn._shared import FileMagic


MAGIC_NWSYNC_MANIFEST = FileMagic(b"NSYM")
MAGIC_NWSYNC_FILE = FileMagic(b"NSYC")


def test_make_magic():
    assert FileMagic("NSYM") == MAGIC_NWSYNC_MANIFEST
    assert FileMagic("NSYC") == MAGIC_NWSYNC_FILE


def test_decompress_none():
    data = b"test data"
    file = io.BytesIO()
    write(file, MAGIC_NWSYNC_FILE, data, Algorithm.NONE)
    file.seek(0)
    decompressed_data, magic, alg = read(file, MAGIC_NWSYNC_FILE)
    assert decompressed_data == data
    assert magic == MAGIC_NWSYNC_FILE
    assert alg == Algorithm.NONE


def test_decompress_zlib():
    data = b"test data"
    file = io.BytesIO()
    write(file, MAGIC_NWSYNC_FILE, data, Algorithm.ZLIB)
    file.seek(0)
    decompressed_data, magic, alg = read(file, MAGIC_NWSYNC_FILE)
    assert decompressed_data == data
    assert magic == MAGIC_NWSYNC_FILE
    assert alg == Algorithm.ZLIB


def test_decompress_zstd():
    data = b"test data"
    file = io.BytesIO()
    write(file, MAGIC_NWSYNC_FILE, data, Algorithm.ZSTD)
    file.seek(0)
    decompressed_data, magic, alg = read(file, MAGIC_NWSYNC_FILE)
    assert decompressed_data == data
    assert magic == MAGIC_NWSYNC_FILE
    assert alg == Algorithm.ZSTD


def test_invalid_magic():
    file = io.BytesIO(b"BADM" + b"\x00" * 12)
    with pytest.raises(ValueError, match="invalid magic"):
        read(file, MAGIC_NWSYNC_FILE)


def test_invalid_header_version():
    file = io.BytesIO(MAGIC_NWSYNC_FILE + b"\x00" * 12)
    with pytest.raises(ValueError, match="invalid header version"):
        read(file, MAGIC_NWSYNC_FILE)


def test_invalid_algorithm():
    file = io.BytesIO(
        MAGIC_NWSYNC_FILE
        + (3).to_bytes(4, "little")
        + (99).to_bytes(4, "little")
        + (10).to_bytes(4, "little")
    )
    with pytest.raises(ValueError, match="Unsupported algorithm"):
        read(file, MAGIC_NWSYNC_FILE)


def test_lorem():
    with open("tests/lorem.txt", "rb") as f:
        expect = f.read()
    with open("tests/compressedbuf/lorem.zstd", "rb") as f:
        mag = FileMagic("TEST")
        decompressed_data, magic, alg = read(f, mag)
        assert magic == mag
        assert alg == Algorithm.ZSTD
        assert decompressed_data == expect
