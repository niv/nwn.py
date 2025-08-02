import os
import glob
import json

import pytest

from nwn.gff import read, struct_to_json, struct_from_json


def cmp_approx(a, b: dict) -> bool:
    if isinstance(a, dict) and isinstance(b, dict):
        return all(cmp_approx(a[k], b[k]) for k in a if k in b)
    if isinstance(a, float) and isinstance(b, float):
        return a == pytest.approx(b)
    return a == b


def gff_corpus_files():
    files = glob.glob("tests/gff/corpus/*")
    return [f for f in files if os.path.isfile(f) if not f.endswith(".json")]


def json_corpus_files():
    files = glob.glob("tests/gff/corpus/*.json")
    return [f for f in files if os.path.isfile(f)]


def test_corpus_files():
    assert gff_corpus_files(), "No test files found in tests/gff/corpus directory"
    assert json_corpus_files(), "No JSON test files found in tests/gff/corpus directory"


@pytest.mark.parametrize("file_name", gff_corpus_files())
def test_rewrite(file_name):
    with open(file_name, "rb") as f:
        data, ty = read(f)
        nwndata = struct_to_json(data, ty)
        assert nwndata["__data_type"] == ty.decode("utf-8")
        rtt, rtt_ty = struct_from_json(nwndata)
        assert cmp_approx(data, rtt)
        assert rtt_ty == ty


@pytest.mark.parametrize("file_name", json_corpus_files())
def test_json_corpus_files(file_name):
    with open(file_name, "r") as f:
        json_data = json.load(f)
    with open(os.path.splitext(file_name)[0], "rb") as f:
        gff_data, gff_ty = read(f)

    transformed_data, transformed_ty = struct_from_json(json_data)
    assert cmp_approx(transformed_data, gff_data)
    assert transformed_ty == gff_ty
