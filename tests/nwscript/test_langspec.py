from nwn.nwscript.langspec import read, Constant, Function, FunctionArg
from nwn.nwscript._types import VMType


def test_simple():
    # This is kind of under-testing, but I haven't yet
    # gotten around to splitting out the parsing logic.

    with open("tests/nwscript/nwscript.nss") as f:
        spec = read(f)

    # This is just what EE 37-15 has.
    # This test will obviously fail when passing in any other nwscript.nss.
    assert len(spec.constants) == 6201
    assert len(spec.functions) == 1187
    assert spec.constants[0].name == "NUM_INVENTORY_SLOTS"
    assert spec.functions[0].name == "Random"

    assert spec.constants[-1] == Constant(
        ty=VMType.INT,
        name="SPELL_FAILURE_TYPE_ARCANE",
        value=1,
    )

    assert spec.functions[-1] == Function(
        id=1186,
        return_type=VMType.VOID,
        name="SetBodyBag",
        args=[
            FunctionArg(ty=VMType.OBJECT, name="oObject", default=None),
            FunctionArg(ty=VMType.INT, name="nBodyBag", default=None),
        ],
        doc=["Sets the creature or placeable body bag type (bodybag.2da entry)"],
    )

    # Ensure constants are dereferenced correctly
    assert spec.functions[-3].args[1] == FunctionArg(
        ty=VMType.INT,
        name="bSmoothed",
        default=True,
    )
    assert spec.functions[-4].args[2].default == -1
