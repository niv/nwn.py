from io import StringIO

import pytest

from nwn import twoda

BASIC = """2DA V2.0

    COL1     COL2
0   1        2
3   "3 4"    5
1   ****     6
9   7
"""


def test_missing_magic():
    with pytest.raises(ValueError):
        _ = twoda.read(StringIO(""))


def test_invalid_magic():
    with pytest.raises(ValueError):
        _ = twoda.read(StringIO("2DA V1.0\n"))


def test_missing_newline():
    with pytest.raises(ValueError):
        _ = twoda.read(StringIO("2DA V2.0\nABC"))


def test_missing_headers():
    with pytest.raises(ValueError):
        _ = twoda.read(StringIO("2DA V2.0\n\n"))


def test_twoda_basic():
    tda = twoda.read(StringIO(BASIC))
    assert tda._columns == ["COL1", "COL2"]
    rows = [row for row in tda]
    assert len(rows) == 4
    assert rows[0] == {"COL1": "1", "COL2": "2"}
    assert rows[1] == {"COL1": "3 4", "COL2": "5"}
    assert rows[2] == {"COL1": None, "COL2": "6"}
    assert rows[3] == {"COL1": "7", "COL2": None}


def test_twoda_writer():
    columns = ["COL1", "COL2"]
    data = [
        {"COL1": "1", "COL2": "2"},
        {"COL1": "3 4", "COL2": "5"},
        {"COL1": None, "COL2": "6"},
        {"COL1": "7", "COL2": None},
    ]
    f = StringIO()
    w = twoda.write(f, columns)
    for row in data:
        w.add_row(row)
    f.seek(0)
    r = twoda.read(f)
    assert r.columns == columns
    for i, row in enumerate(r):
        assert row == data[i]
