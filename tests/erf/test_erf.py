from io import BytesIO
from datetime import date
import hashlib

from nwn.erf import Reader, Writer
from nwn._shared import Language


def test_reader():
    expect_date = date(2025, 3, 15)
    with open("tests/erf/test.hak", "rb") as f:
        reader = Reader(f)
        print(reader.build_date)
        assert reader.build_date == expect_date
        assert len(reader.filenames) > 0
        assert reader.filenames[0] == "skyboxes.2da"
        assert (
            hashlib.sha1(reader.read_file("skyboxes.2da")).hexdigest()
            == "869fa0ad3aebd1cb8dfec90b5f46ce3463d4ad1e"
        )


def test_write_read():
    payload = b"Hello, World!"

    file = BytesIO()

    with Writer(file) as w:
        w.add_localized_string(Language.ENGLISH, "Test.")
        w.add_file("test.txt", payload)

    data = file.getvalue()
    reader = Reader(BytesIO(data))
    assert reader.build_date == date.today()
    assert len(reader.localized_strings) == 1
    assert reader.localized_strings[Language.ENGLISH] == "Test."
    assert reader.localized_strings[0] == "Test."
    assert reader.read_file("test.txt") == payload
