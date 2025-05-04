import logging
import os
from unittest.mock import Mock

import pytest

from nwn.nwscript.vm import Script, VM
from nwn.nwscript import Object, Effect
from nwn.nwscript import langspec


def pytest_configure():
    logging.basicConfig(level=logging.DEBUG)


# We abuse PrintInteger() to trigger asserts
def _nwassert(vm, cond):
    if not cond:
        # TODO: get the line number
        raise AssertionError(f"NWN Assertion failed ip={vm.ip} sp={vm.sp}")


# pylint: disable=all


class DefaultImpl:
    def Random(self, nMaxInteger: int) -> int:
        return 0

    def PrintString(self, sString: str) -> None:
        pass

    def PrintFloat(self, fFloat: float, nWidth=18, nDecimals=9):
        pass

    def FloatToString(self, fFloat: float, nWidth: int = 18, nDecimals: int = 9) -> str:
        return ""

    def PrintInteger(self, nInteger: int):
        pass

    def PrintObject(self, oObject: Object):
        pass

    def AssignCommand(self, oActionSubject: Object, aActionToAssign):
        pass

    def DelayCommand(self, fSeconds: float, aActionToDelay):
        pass

    def ExecuteScript(self, sScript, oTarget=Object.SELF):
        pass

    def GetIsReactionTypeFriendly(self, oTarget: Object, oSource=Object.SELF) -> bool:
        return False

    def GetHitDice(self, oCreature: Object) -> int:
        return 0

    def GetEffectType(self, eEffect: Effect, bAllTypes=False) -> int:
        return eEffect.type

    def EffectSlow(self) -> Effect:
        return Effect(37)


# pylint: enable=all


@pytest.fixture
def test_vm(request):
    script_name = str(request.node.fspath)
    base = os.path.basename(script_name).replace("test_", "")
    base = base.replace(".py", "")
    base_dir = os.path.dirname(script_name)
    script_name = base_dir + "/corpus/" + base

    with open("tests/nwscript/nwscript.nss", "r") as nws:
        spec = langspec.read(nws)

    vmi = DefaultImpl()
    mo = Mock(spec=vmi, wraps=vmi)
    script = Script.from_compiled(script_name)
    vm = VM(script, spec, mo)
    mo.PrintInteger.side_effect = lambda x: _nwassert(vm, x)
    return vm
