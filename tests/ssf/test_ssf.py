from io import BytesIO

from nwn.ssf import read, write, Entry


def test_read():
    with open("tests/ssf/c_cat.ssf", "rb") as file:
        entries = read(file)

    assert entries[1] == Entry(resref="c_cat_bat1", strref=0xFFFFFFFF)
    assert len(entries) == 49


def test_write_and_read():
    with open("tests/ssf/c_cat.ssf", "rb") as file:
        original_entries = read(file)

    memory_file = BytesIO()
    write(memory_file, original_entries)
    memory_file.seek(0)

    read_entries = read(memory_file)

    assert original_entries == read_entries
