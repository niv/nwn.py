import pytest

from nwn.nwscript import Object, Effect, Vector


def test_run(test_vm):
    test_vm.run()


def test_printstring(test_vm):
    test_vm.call("test_PrintString")
    test_vm.impl.PrintString.assert_called_with("LocalStr")


def test_call(test_vm):
    assert test_vm.call("return_int") == 42
    assert test_vm.call("return_int") == 42  # repeated must be OK


def test_const_globals_on_run(test_vm):
    assert test_vm.call("return_global_const_string") == "GlobalConstStr"


@pytest.mark.xfail(reason="Not implemented: BP save/restore seems broken")
def test_global_init_runs_on_call(test_vm):
    assert test_vm.call("return_global_string") == "GlobalStr"
    assert test_vm.call("return_global_init_string") == "GlobalInitStr"


def test_object_self(test_vm):
    test_vm.object_self = Object(0x1234)
    assert test_vm.call("return_object_self").id == 0x1234


def test_object_self_defaultarg(test_vm):
    test_vm.object_self = Object(0x1234)
    test_vm.call("call_GetIsReactionTypeFriendly")
    test_vm.impl.GetIsReactionTypeFriendly.assert_called_once_with(
        None, test_vm.object_self
    )


def test_object_invalid(test_vm):
    assert test_vm.call("return_object_invalid") == Object.INVALID


def test_mock(test_vm):
    test_vm.impl.GetHitDice.return_value = 42
    assert test_vm.call("test_mock") == 42
    test_vm.impl.GetHitDice.assert_called_once()


def test_nomock(test_vm):
    assert test_vm.impl.GetHitDice(None) == 0
    test_vm.run()
    test_vm.impl.GetHitDice.assert_called_once()


def test_struct_missingkey(test_vm):
    in1 = {"m_str": "hello", "m_int": 42}
    with pytest.raises(KeyError):
        test_vm.call("take_and_return_struct1", in1)


def test_struct_extrakey(test_vm):
    in1 = {"m_str": "hello", "m_int": 42, "m_flt": 3.14, "m_extra": 1}
    x = test_vm.call("take_and_return_struct1", in1)
    # extra keys are ok but are not passed through
    assert x == {"m_str": "hellohello", "m_int": 168, "m_flt": 6.28}


@pytest.mark.parametrize(
    "in1",
    [
        # TODO: test against all types
        {"m_str": "hello", "m_int": "42", "m_flt": 3.14},
        {"m_str": "hello", "m_int": 42.1, "m_flt": 3.14},
    ],
)
def test_struct_wrongtype(test_vm, in1):
    # in1 = {"m_str": "hello", "m_int": "42", "m_flt": 3.14}
    with pytest.raises(TypeError):
        test_vm.call("take_and_return_struct1", in1)


def test_struct1(test_vm):
    in1 = {"m_str": "hello", "m_int": 42, "m_flt": 3.14}
    # in2 = { "m_t1": in1, "m_obj": 5 }
    x = test_vm.call("take_and_return_struct1", in1)
    assert x == {"m_str": "hellohello", "m_int": 168, "m_flt": 6.28}


def test_struct2(test_vm):
    test_vm.object_self = Object(0x1234)
    in1 = {"m_str": "hello", "m_int": 42, "m_flt": 3.14}
    in2 = {"m_t1": in1, "m_obj": test_vm.object_self}
    x = test_vm.call("take_and_return_struct2", in2)
    assert x == {
        "m_t1": {"m_str": "hellohello", "m_int": 168, "m_flt": 6.28},
        "m_obj": test_vm.object_self,
    }


def test_return_effect(test_vm):
    eff = test_vm.call("return_effect")
    assert isinstance(eff, Effect)
    assert eff.type == 37


def test_take_effect_assert(test_vm):
    eff = Effect(36)
    with pytest.raises(AssertionError):
        test_vm.call("take_effect", eff)


def test_take_effect(test_vm):
    eff = Effect(37)
    test_vm.call("take_effect", eff)


def test_take_and_modify_vector(test_vm):
    v = Vector(1.0, 2.0, 3.0)
    v2 = test_vm.call("take_and_modify_vector", v)
    assert v == Vector(1.0, 2.0, 3.0)
    assert v2 == Vector(2.0, 2.0, 3.0)
