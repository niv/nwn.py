import pytest
from nwn.nwscript.comp import Compiler, CompilationError
from nwn.nwscript.comp import Optimization

TEST_FILES = {
    "nwscript.nss": """
int Nonsense(int n);
        """,
    "simple.nss": """
void main() {
    int i = 42;
}
        """,
    "with_include.nss": """
#include "included"

void main() {
    int i = GetIncludedValue();
}
        """,
    "included.nss": """
int GetIncludedValue() {
    return 42;
}
        """,
    "syntax_error.nss": """
void main() {
    int i = 42
    PrintString("Missing semicolon above");
}
        """,
}


def resolver(filename: str):
    return TEST_FILES.get(filename)


def test_compiler_initialization():
    comp = Compiler(resolver)
    assert comp is not None


def test_simple_compilation():
    comp = Compiler(resolver)
    ncs, ndb = comp.compile("simple")

    assert ncs is not None
    assert isinstance(ncs, bytes)
    assert len(ncs) > 0

    assert ndb is not None
    assert isinstance(ndb, str)
    assert len(ndb) > 0


def test_compilation_with_extension():
    comp = Compiler(resolver)
    ncs, ndb = comp.compile("simple.nss")

    assert ncs is not None
    assert len(ncs) > 0


def test_compilation_with_include():
    comp = Compiler(resolver)
    ncs, ndb = comp.compile("with_include")

    assert ncs is not None
    assert len(ncs) > 0


def test_compilation_include():
    with pytest.raises(CompilationError, match="NO FUNCTION MAIN IN SCRIPT"):
        comp = Compiler(resolver)
        comp.compile("included")


def test_compilation_error():
    with pytest.raises(CompilationError, match="ERROR: PARSING VARIABLE LIST"):
        comp = Compiler(resolver)
        comp.compile("syntax_error")


def test_debug_info_flag():
    comp_with_debug = Compiler(resolver, debug_info=True)
    ncs_with_debug, ndb_with_debug = comp_with_debug.compile("simple")
    assert ncs_with_debug
    assert ndb_with_debug
    comp_no_debug = Compiler(resolver, debug_info=False)
    ncs_no_debug, ndb_no_debug = comp_no_debug.compile("simple")
    assert ncs_no_debug
    assert not ndb_no_debug


def test_max_include_depth():
    include_files = {}

    for i in range(20):
        if i == 0:
            include_files[
                f"include_{i}.nss"
            ] = b"""
int GetValue() {
return 42;
}
            """
        else:
            include_files[f"include_{i}.nss"] = (
                f"""
#include "include_{i-1}"

int GetIncludedValue_{i}() {{
return GetValue() + {i};
}}
            """.encode(
                    "utf-8"
                )
            )

    include_files[
        "deep_include.nss"
    ] = b"""
#include "include_19"

void main() {
int i = GetIncludedValue_19();
}
    """

    include_files["nwscript.nss"] = TEST_FILES["nwscript.nss"]

    def depth_resolver(filename: str):
        return include_files.get(filename)

    comp_low_depth = Compiler(depth_resolver, max_include_depth=5)
    with pytest.raises(CompilationError, match="INCLUDE TOO MANY LEVELS"):
        comp_low_depth.compile("deep_include")

    comp_high_depth = Compiler(depth_resolver, max_include_depth=25)
    ncs, ndb = comp_high_depth.compile("deep_include")

    assert ncs is not None
    assert len(ncs) > 0


def test_multiple_compilations():
    comp = Compiler(resolver)

    ncs1, ndb1 = comp.compile("simple")
    assert ncs1 is not None
    ncs2, ndb2 = comp.compile("with_include")
    assert ncs2 is not None
    assert ncs1 != ncs2


def test_optimization_invalid_type():
    with pytest.raises(TypeError, match="Invalid optimizations type"):
        Compiler(resolver, optimizations="invalid")


def test_optimizations_are_applied():
    comp_no_opt = Compiler(resolver, optimizations=0)
    ncs_no_opt, _ = comp_no_opt.compile("simple")

    comp_all_opt = Compiler(resolver, optimizations=0xFFFFFFFF)
    ncs_all_opt, _ = comp_all_opt.compile("simple")

    assert len(ncs_all_opt) < len(ncs_no_opt)
    assert ncs_all_opt != ncs_no_opt
