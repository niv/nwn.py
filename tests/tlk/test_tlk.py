from io import BytesIO


from nwn.tlk import read, write
from nwn.types import Language


def test_tlk():
    with open("tests/tlk/ossian.tlk", "rb") as f:
        entries, lang = read(f)

    assert lang == Language.ENGLISH
    assert len(entries) == 191
    assert entries[0] == "BadStrref"
    assert entries[0].text == "BadStrref"
    assert entries[0].sound_length == 0
    assert entries[0].sound_resref == ""
    # 1 is not defined in the tlk
    assert entries[1] == ""
    assert entries[1].text == ""
    assert entries[1].sound_length == 0
    assert entries[1].sound_resref == ""
    assert entries[2] == "Seagull"
    assert entries[2].text == "Seagull"


def test_write_tlk():
    with open("tests/tlk/ossian.tlk", "rb") as f:
        original_tlk, _ = read(f)

    buffer = BytesIO()
    write(buffer, original_tlk, Language.ENGLISH)
    buffer.seek(0)

    written_tlk, _ = read(buffer)

    assert original_tlk == written_tlk
