from dataclasses import dataclass, field
from typing import Any

from nwn.nwscript import Object, VMType


@dataclass(order=True)
class _Elem:
    # The only reason this is here is basically because we want to
    # support None as a construction value
    type: VMType = field(compare=False)
    value: Any

    def __post_init__(self):
        expect_type = self.type.python_type()

        if expect_type is None:
            # As a convenience, we allow returning None from the VM
            # We must never GIVE the VM a None, though
            raise TypeError(f"Cannot stack type {self.type}")

        if self.value is None:
            self.value = expect_type()

        elif not isinstance(self.value, expect_type):
            raise TypeError(f"Value {self.value} is not of type {expect_type}")

        if isinstance(self.value, int):
            self.value = (self.value + 2**31) % (2**32) - 2**31

    def __str__(self):
        return f"{self.type.value} {repr(self.value)}"

    def adjust(self, delta):
        if isinstance(self.value, int) and isinstance(delta, int):
            self.value += delta
            self.value = (self.value + 2**31) % (2**32) - 2**31
        elif isinstance(self.value, float) and isinstance(delta, float):
            self.value += delta
        else:
            raise NotImplementedError()

    # Any Int/Float pair auto-coerces to float
    def _op(self, other, op):
        if any(t == VMType.FLOAT for t in [self.type, other.type]):
            return _Elem(VMType.FLOAT, op(float(self.value), float(other.value)))
        if self.type != other.type:
            raise TypeError(f"Op invalid on {self.type} and {other.type}")
        return _Elem(self.type, op(self.value, other.value))

    def __add__(self, other):
        return self._op(other, lambda a, b: a + b)

    def __sub__(self, other):
        return self._op(other, lambda a, b: a - b)

    def __mul__(self, other):
        return self._op(other, lambda a, b: a * b)

    def __truediv__(self, other):
        def mydiv(a, b):
            if isinstance(a, int) and isinstance(b, int):
                return a // b
            else:
                return a / b

        return self._op(other, mydiv)


class Stack:
    """
    A stack as used by the NWN VM.

    You usually do not need to use this directly, but rather use the
    VM class, which uses this internally.
    """

    def __init__(self):
        self._stack = []
        self._sp = 0

    @property
    def sp(self):
        return self._sp

    @sp.setter
    def sp(self, value):
        assert value >= 0
        assert value <= len(self._stack)
        self._sp = value

    # TODO: this should go away (use self.sp property, but needs careful vetting)
    def set_stack_pointer(self, p: int):
        self._sp = p
        self._stack = self._stack[: self.sp]

    def adjust(self, idx, delta):
        self._stack[idx].adjust(delta)

    def assign(self, src: int, dst: int):
        assert src >= 0, f"src: {src}"
        assert dst >= 0, f"dst: {dst}"
        if dst >= len(self._stack):
            self._stack.append(self._stack[src])
            self._sp += 1
        else:
            self._stack[dst] = self._stack[src]

    def push(self, e: _Elem):
        assert isinstance(e, _Elem)
        self._stack.append(e)
        self._sp += 1

    def pop(self, idx=-1) -> _Elem:
        assert self._sp > 0
        self._sp -= 1
        r = self._stack.pop(idx)
        return r

    def push_vmtype(self, ty: VMType, value: Any):
        assert ty != VMType.VECTOR  # TODO
        assert ty != VMType.ACTION
        self.push(_Elem(ty, value))

    def pop_vmtype(self, ty: VMType, idx=-1) -> Any:
        assert ty != VMType.VECTOR  # TODO
        assert ty != VMType.ACTION
        test = self.pop(idx)
        if test.type != ty:
            raise TypeError(f"Expected {ty}, got {test.type}")
        return test.value

    def push_int(self, v: int):
        self.push_vmtype(VMType.INT, v)

    def push_int_bool(self, v: bool):
        self.push_int(1 if v else 0)

    def push_float(self, v: float):
        self.push_vmtype(VMType.FLOAT, v)

    def push_string(self, v: str):
        self.push_vmtype(VMType.STRING, v)

    def push_object(self, v: Object):
        self.push_vmtype(VMType.OBJECT, v)

    def pop_int(self, idx=-1) -> int:
        return self.pop_vmtype(VMType.INT, idx)

    def pop_int_bool(self, idx=-1) -> bool:
        return bool(self.pop_int(idx))

    def pop_float(self, idx=-1) -> float:
        return self.pop_vmtype(VMType.FLOAT, idx)

    def pop_string(self, idx=-1) -> str:
        return self.pop_vmtype(VMType.STRING, idx)

    def pop_object(self, idx=-1) -> Object:
        return self.pop_vmtype(VMType.OBJECT, idx)
