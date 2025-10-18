from io import BytesIO
from datetime import date
import hashlib

from nwn.erf import Reader, Writer
from nwn._shared import Language, Gender, GenderedLanguage


def test_reader():
    expect_date = date(2025, 3, 15)
    with open("tests/erf/test.hak", "rb") as f:
        reader = Reader(f)
        assert reader.build_date == expect_date
        assert len(reader.filenames) > 0
        assert reader.filenames[0] == "skyboxes.2da"
        assert (
            hashlib.sha1(reader.read_file("skyboxes.2da")).hexdigest()
            == "869fa0ad3aebd1cb8dfec90b5f46ce3463d4ad1e"
        )
        assert reader.file_type == b"HAK "

        assert reader.filemap["skyboxes.2da"] == Reader.Entry(
            resref="skyboxes",
            restype=2017,
            offset=224,
            disk_size=721,
            uncompressed_size=721,
        )
        assert reader.filemap["skyboxes.2da"].filename == "skyboxes.2da"


def test_reader_from_path():
    reader = Reader("tests/erf/test.hak")
    assert len(reader.filenames) > 0


def test_write_read():
    payload = b"Hello, World!"

    file = BytesIO()

    english_male = GenderedLanguage(Language.ENGLISH, Gender.MALE)

    with Writer(file, file_type="HI") as w:
        w.add_localized_string(english_male, "Test.")
        w.add_file_data("test.txt", payload)

    data = file.getvalue()
    reader = Reader(BytesIO(data))
    assert reader.build_date == date.today()
    assert len(reader.localized_strings) == 1
    assert reader.localized_strings[english_male] == "Test."
    assert reader.read_file("test.txt") == payload
    assert reader.file_type == b"HI  "
