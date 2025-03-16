from nwn.tileset import read_set


def test_read_set():
    with open("tests/tileset/tcn01.set") as f:
        result = read_set(f)

    assert result.name == "TCN01"
    assert result.transition == 4

    assert result.grass.grass == 1

    assert len(result.terrains) == 5
    assert result.terrains[0].name == "cobble"

    assert len(result.crossers) == 4
    assert result.crossers[0].name == "wall"

    assert len(result.primary_rules) == 76
    assert result.primary_rules[0].placed == "cobble"

    assert len(result.tiles) == 408

    assert len(result.groups) == 89
    assert result.groups[0].name == "WallGate"
    assert result.groups[0].tiles == [42]
