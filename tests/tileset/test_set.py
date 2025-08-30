import glob
import os

import pytest

from nwn.tileset import read_set


def tileset_corpus_files():
    files = glob.glob("tests/tileset/corpus/*")
    return [f for f in files if os.path.isfile(f) if not f.endswith(".json")]


def test_corpus_files():
    assert (
        tileset_corpus_files()
    ), "No test files found in tests/tileset/corpus directory"


@pytest.mark.parametrize("file_name", tileset_corpus_files())
def test_read_corpus(file_name):
    with open(file_name) as f:
        result = read_set(f)
    assert result is not None


def test_read_set():
    with open("tests/tileset/corpus/tcn01.set") as f:
        result = read_set(f)

    assert result.name == "TCN01"
    assert result.transition == 4

    assert result.grass

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
