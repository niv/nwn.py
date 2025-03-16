import nwn.gff as gff


def test_read():
    with open("tests/gff/x3_it_rubygem.uti", "rb") as f:
        root, file_type = gff.read(f)
        assert file_type == "UTI "
        assert root.Tag == "X3_IT_RUBYGEM"

        assert root.PaletteID == 54
        assert isinstance(root.PaletteID, gff.Byte)
