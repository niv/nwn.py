from io import BytesIO
from hashlib import sha1

import pytest

from nwn.nwsync import read, write, Manifest, ManifestEntry, NWSYNC_MANIFEST_VERSION


def test_read_rewrite():
    with open(
        "tests/nwsync/root/manifests/3cf66c49bff6188f0b4ce8d0ea3fae945237a357", "rb"
    ) as f:
        mf = read(f)

        assert mf.version == NWSYNC_MANIFEST_VERSION

        entries = [
            ManifestEntry(
                sha1=b"\x1dJ\xbc\xd8\xde\x80\xb4\r\xe2\xfe\xe0U\xd1\xcf\xd1Ha\xaa\x812",
                size=719,
                resref="x3_it_rubygem.uti",
            ),
            ManifestEntry(
                sha1=b'1N\x13SG\x87RJ9\xcc\xf8\x1c\xe7\xbf:\xb0\xc3*e"',
                size=625,
                resref="fs.shd",
            ),
            ManifestEntry(
                sha1=b"E\x18\x01.\x1b6^P@\x01\xdb\xc9A bO\x15\xb8\xbb\xd5",
                size=446,
                resref="lorem.txt",
            ),
            ManifestEntry(
                sha1=b"\\Z\xc2\x9e\x87\xeb\x9c\xd0(\x1a1\xf9\xc3k\xad|\xd1\xfa\x85\xf3",
                size=866,
                resref="ipsum.txt",
            ),
            ManifestEntry(
                sha1=b"\x86\x9f\xa0\xad:\xeb\xd1\xcb\x8d\xfe\xc9\x0b_F\xce4c\xd4\xad\x1e",
                size=721,
                resref="skyboxes.2da",
            ),
            ManifestEntry(
                sha1=b"E\x18\x01.\x1b6^P@\x01\xdb\xc9A bO\x15\xb8\xbb\xd5",
                size=446,
                resref="lorem2.txt",
            ),
        ]

        assert mf.entries == entries

        bio = BytesIO()
        write(bio, mf)
        bio.seek(0)
        sha1_hash_1 = sha1(bio.read()).hexdigest()
        bio.seek(0)
        mf2 = read(bio)
        assert mf2.entries == entries

        bio2 = BytesIO()
        write(bio2, mf2)
        bio2.seek(0)
        sha1_hash_2 = sha1(bio2.read()).hexdigest()

        assert sha1_hash_1 == sha1_hash_2


def test_repository_path():
    entry = ManifestEntry(
        sha1=b"\x1dJ\xbc\xd8\xde\x80\xb4\r\xe2\xfe\xe0U\xd1\xcf\xd1Ha\xaa\x812",
        size=719,
        resref="x3_it_rubygem.uti",
    )

    assert entry.repository_path == "1d/4a/1d4abcd8de80b40de2fee055d1cfd14861aa8132"


def test_encoding():
    win1252_resref = "mus_bat_som_núrn.wav"  # utf-8

    entry = ManifestEntry(
        sha1=b"\x00" * 20,
        size=1,
        resref=win1252_resref,
    )

    manifest = Manifest(entries=[entry])
    bio = BytesIO()
    write(bio, manifest)
    bio.seek(0)
    read_manifest = read(bio)

    assert read_manifest.entries[0].resref == win1252_resref


def test_invalid_resref_length():
    entries = [ManifestEntry(sha1=b"a" * 20, size=100, resref="toolongresrefname.txt")]
    manifest = Manifest(entries=entries)

    buf = BytesIO()
    with pytest.raises(ValueError, match="Resref invalid: "):
        write(buf, manifest)


def test_manifest_sort_order():
    entries = [
        ManifestEntry(sha1=b"b" * 20, size=100, resref="test2.txt"),
        ManifestEntry(sha1=b"a" * 20, size=100, resref="test1.txt"),
        ManifestEntry(sha1=b"a" * 20, size=100, resref="test2.txt"),
    ]
    manifest = Manifest(entries=entries)

    buf = BytesIO()
    write(buf, manifest)

    buf.seek(8)

    entry_count = int.from_bytes(buf.read(4), "little")
    mapping_count = int.from_bytes(buf.read(4), "little")

    assert entry_count == 2
    assert mapping_count == 1

    first_sha1 = buf.read(20)
    assert first_sha1 == b"a" * 20

    buf.seek(4, 1)

    first_resref = buf.read(16).decode("windows-1252").rstrip("\0")
    assert first_resref == "test1"

    buf.seek(2, 1)

    second_sha1 = buf.read(20)
    assert second_sha1 == b"b" * 20

    buf.seek(4, 1)
    second_resref = buf.read(16).decode("windows-1252").rstrip("\0")
    assert second_resref == "test2"

    buf.seek(2, 1)

    mapping_index = int.from_bytes(buf.read(4), "little")
    assert mapping_index == 0

    mapping_resref = buf.read(16).decode("windows-1252").rstrip("\0")
    assert mapping_resref == "test2"
