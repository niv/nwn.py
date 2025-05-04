from nwn.nwscript.vm import Stack
from nwn.nwscript import Object


def test_push_pop_int():
    stack = Stack()
    stack.push_int(42)
    assert stack.pop_int() == 42


def test_push_pop_float():
    stack = Stack()
    stack.push_float(3.14)
    assert stack.pop_float() == 3.14


def test_push_pop_string():
    stack = Stack()
    stack.push_string("hello")
    assert stack.pop_string() == "hello"


def test_push_pop_object():
    stack = Stack()
    obj = Object(1234)
    stack.push_object(obj)
    assert stack.pop_object() == obj


def test_push_pop_invalid_object():
    stack = Stack()
    stack.push_object(Object.INVALID)
    assert stack.pop_object() == Object.INVALID


def test_push_pop_none_object():
    stack = Stack()
    stack.push_object(None)
    assert stack.pop_object() is not None


def test_assign():
    stack = Stack()
    stack.push_int(10)
    stack.push_int(20)
    stack.assign(0, 1)
    assert stack.pop_int() == 10


def test_set_stack_pointer():
    stack = Stack()
    stack.push_int(10)
    stack.push_int(20)
    stack.set_stack_pointer(1)
    assert stack.sp == 1
    assert stack.pop_int() == 10
