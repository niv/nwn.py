from nwn import is_valid_resref


def test_is_valid_resref_valid():
    assert is_valid_resref("foo.txt")
    assert is_valid_resref("BAR.NSS")
    assert is_valid_resref("a123456789012345.tga")  # 16 chars
    assert is_valid_resref("x.tlk")


def test_is_valid_resref_invalid():
    assert not is_valid_resref("foo")  # no extension
    assert not is_valid_resref("foo.txt.bak")  # too many dots
    assert not is_valid_resref("foo/abc.txt")  # slash
    assert not is_valid_resref("foo\\abc.txt")  # backslash
    assert not is_valid_resref(".txt")  # empty name
    assert not is_valid_resref("a1234567890123456.txt")  # 17 chars
    assert not is_valid_resref("foo.invalidext")  # invalid extension
