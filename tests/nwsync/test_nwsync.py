from io import BytesIO

from nwn.nwsync import read, write, ManifestEntry, NWSYNC_MANIFEST_VERSION


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
        mf2 = read(bio)
        assert mf2.entries == entries


def test_repository_path():
    entry = ManifestEntry(
        sha1=b"\x1dJ\xbc\xd8\xde\x80\xb4\r\xe2\xfe\xe0U\xd1\xcf\xd1Ha\xaa\x812",
        size=719,
        resref="x3_it_rubygem.uti",
    )

    assert entry.repository_path == "1d/4a/1d4abcd8de80b40de2fee055d1cfd14861aa8132"
