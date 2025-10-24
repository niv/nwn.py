import logging

from nwn.nwscript import ndb
from nwn.nwscript.asm import Opcode, Auxcode, read_instr
from nwn.nwscript.langspec import LanguageSpec
from nwn.nwscript import Object, VMType
from nwn.types import Vector

from .._types import _VMClosure
from ._stack import Stack
from ._script import Script

_logger = logging.getLogger(__name__)


class _ScriptExecutionEnd(Exception):
    pass


class VM:
    """
    VM Script Executor for running NWScript bytecode.

    Supports the following type mappings:

    - int <> int (32 bit on the nwscript side)
    - float <> float (32 bit on the nwscript side)
    - str <> string: in the current encoding (get_nwn_encoding())
    - Object <> object
    - Vector <> vector
    - Location <> location
    - custom structs <> dict: unset keys will push the type default value; \
        extra keys are ignored.
    - Engine structure support is very preliminary and incomplete
    """

    def __init__(self, script: Script, spec: LanguageSpec, impl):
        """
        Create a new VM.

        You need one VM per script. You can reuse spec and impl between them.

        The implementation must be a class that has the methods that correspond to
        the VM command names. The methods must accept the same number of arguments
        as the VM command expects, mapped to the corresponding python types.

        After creating the VM, you can call the `run` method to execute the
        script, or use call() or proxy() to call NWScript functions directly.

        Args:
            script: The script to run.
            spec: The language spec your script was compiled against.
            impl: The implementation of the script.
        """
        self._spec = spec
        self._impl = impl

        self._script = script
        self._ncs = script.ncs
        self._ndb = script.ndb

        self._stack = Stack()
        self._ret: list = []
        self._object_self = Object.INVALID

        # TODO: these should probably also move into stack.py
        self._bp = 0
        self._save_ip = 0
        self._save_bp = 0
        self._save_sp = 0

        # Super janky, doesn't really work yet.
        self._stop_before_main = False

    @property
    def object_self(self):
        """
        Return the object ID that the script is running on. Defaults to INVALID.
        """
        return self._object_self

    @object_self.setter
    def object_self(self, v):
        """
        Set/change the object ID that the script is running on.

        Changing this will affect the OBJECT_SELF constant in the script.
        """
        self._object_self = v

    @property
    def impl(self):
        """
        Return the implementation object that this VM was created with.
        """
        return self._impl

    @property
    def spec(self):
        """
        Return the language spec that this VM was created with.
        """
        return self._spec

    @property
    def sp(self):
        """
        Get the current stack pointer.
        """
        return self._stack.sp

    @sp.setter
    def sp(self, v):
        """
        Set the current stack pointer. Currently used internally.
        """
        self._stack.sp = v

    @property
    def ip(self):
        """
        Return the current instruction pointer (offset into bytecode).
        """
        return self._ncs.tell()

    @ip.setter
    def ip(self, v):
        """
        Manually set the instruction pointer.

        Currently used internally. Must set on a instruction boundary.
        """
        self._ncs.seek(v)

    def _exec(self, i):
        """
        Execute a single instruction.
        """

        # NB: ip has already incremented at this point
        this_ip = self.ip - 2 - i.extra_len

        if i.op == Opcode.NO_OPERATION:
            pass

        elif i.op == Opcode.JMP:
            _logger.debug("JMP %d+%d -> %d", this_ip, i.extra[0], this_ip + i.extra[0])
            self.ip = this_ip + i.extra[0]
            return

        elif i.op == Opcode.JSR:
            if (
                self._stop_before_main
                and this_ip + i.extra[0]
                == self._ndb.function_by_name("main").b_start - 8 - 4 - 1
            ):
                self._stop_before_main = False
                _logger.debug("Stopping before main (UNTESTED)")
                self._stack.pop_int()  # bp
                raise _ScriptExecutionEnd()

            self._ret.append(self.ip)
            self.ip = this_ip + i.extra[0]
            return

        elif i.op == Opcode.JZ:
            if self._stack.pop_int() == 0:
                _logger.debug(
                    "JZ %d+%d -> %d", this_ip, i.extra[0], this_ip + i.extra[0]
                )
                self.ip = this_ip + i.extra[0]
                return

        elif i.op == Opcode.JNZ:
            if self._stack.pop_int() != 0:
                self.ip += i.extra[0]
                return

        elif i.op == Opcode.RET:
            if len(self._ret) == 0:
                raise _ScriptExecutionEnd()
            self.ip = self._ret.pop()
            return

        elif i.op == Opcode.SAVE_BASE_POINTER:
            self._stack.push_int(self._bp)
            self._bp = self.sp

        elif i.op == Opcode.RESTORE_BASE_POINTER:
            self._bp = self._stack.pop_int()

        elif i.op == Opcode.RUNSTACK_ADD:
            if i.aux == Auxcode.TYPE_INTEGER:
                self._stack.push_int(0)
            elif i.aux == Auxcode.TYPE_FLOAT:
                self._stack.push_float(0.0)
            elif i.aux == Auxcode.TYPE_STRING:
                self._stack.push_string("")
            elif i.aux == Auxcode.TYPE_OBJECT:
                self._stack.push_object(Object.INVALID)
            else:
                raise NotImplementedError(f"RUNSTACK_ADD {i.aux}")

        elif i.op in [Opcode.RUNSTACK_COPY, Opcode.RUNSTACK_COPY_BASE]:
            stack_loc = (self._bp if i.op == Opcode.RUNSTACK_COPY_BASE else self.sp) - (
                -1 * i.extra[0]
            ) // 4
            copy_size = i.extra[1] // 4

            for j in range(copy_size):
                self._stack.assign(stack_loc + j, self.sp + j)

        elif i.op in [Opcode.ASSIGNMENT, Opcode.ASSIGNMENT_BASE]:
            stack_loc = (self._bp if i.op == Opcode.ASSIGNMENT_BASE else self.sp) - (
                -1 * i.extra[0]
            ) // 4
            copy_size = i.extra[1] // 4

            for j in range(copy_size):
                self._stack.assign(self.sp - copy_size + j, stack_loc + j)

        elif i.op == Opcode.CONSTANT:
            if i.aux == Auxcode.TYPE_INTEGER:
                self._stack.push_int(i.extra[0])
            elif i.aux == Auxcode.TYPE_FLOAT:
                self._stack.push_float(i.extra[0])
            elif i.aux == Auxcode.TYPE_STRING:
                self._stack.push_string(i.extra[0])
            elif i.aux == Auxcode.TYPE_OBJECT:
                match i.extra[0]:
                    case 0:  # SELF
                        self._stack.push_object(self._object_self)
                    case 1:  # INVALID
                        self._stack.push_object(Object.INVALID)
                    case _:
                        raise NotImplementedError(f"CONSTANT OBJECT {i.extra[0]}")
            else:
                raise NotImplementedError(f"CONSTANT {i.aux}")

        elif i.op == Opcode.MODIFY_STACK_POINTER:
            stack_loc = -1 * i.extra[0] // 4
            self._stack.set_stack_pointer(self.sp - stack_loc)

        elif i.op in [
            Opcode.INCREMENT,
            Opcode.DECREMENT,
            Opcode.INCREMENT_BASE,
            Opcode.DECREMENT_BASE,
        ]:
            stack_loc = (
                self._bp
                if i.op in [Opcode.INCREMENT_BASE, Opcode.DECREMENT_BASE]
                else self.sp
            ) - (-1 * i.extra[0] // 4)
            delta = 1 if i.op in [Opcode.INCREMENT, Opcode.INCREMENT_BASE] else -1

            self._stack.adjust(stack_loc, delta)

        elif i.op == Opcode.NEGATION:
            if i.aux == Auxcode.TYPE_INTEGER:
                self._stack.push_int(-1 * self._stack.pop_int())
            elif i.aux == Auxcode.TYPE_FLOAT:
                self._stack.push_float(-1 * self._stack.pop_float())
            else:
                raise NotImplementedError()

        elif i.op in [
            Opcode.EQUAL,
            Opcode.NOT_EQUAL,
            Opcode.LT,
            Opcode.GT,
            Opcode.LEQ,
            Opcode.GEQ,
        ]:
            # We can probably have the op logic here instead of the stack,
            # then we can turn the stack into a thinner wrapper for perf

            b = self._stack.pop()
            a = self._stack.pop()
            if i.op == Opcode.EQUAL:
                self._stack.push_int_bool(a == b)
            elif i.op == Opcode.NOT_EQUAL:
                self._stack.push_int_bool(a != b)
            elif i.op == Opcode.LT:
                self._stack.push_int_bool(a < b)
            elif i.op == Opcode.GT:
                self._stack.push_int_bool(a > b)
            elif i.op == Opcode.LEQ:
                self._stack.push_int_bool(a <= b)
            elif i.op == Opcode.GEQ:
                self._stack.push_int_bool(a >= b)
            else:
                raise NotImplementedError()

        elif i.op == Opcode.LOGICAL_OR:
            assert i.aux == Auxcode.TYPETYPE_INTEGER_INTEGER
            b = self._stack.pop_int() != 0
            a = self._stack.pop_int() != 0
            self._stack.push_int_bool(a or b)

        elif i.op == Opcode.LOGICAL_AND:
            assert i.aux == Auxcode.TYPETYPE_INTEGER_INTEGER
            b = self._stack.pop_int() != 0
            a = self._stack.pop_int() != 0
            self._stack.push_int_bool(a and b)

        elif i.op == Opcode.INCLUSIVE_OR:
            assert i.aux == Auxcode.TYPETYPE_INTEGER_INTEGER
            b = self._stack.pop_int()
            a = self._stack.pop_int()
            self._stack.push_int(a | b)

        elif i.op == Opcode.BOOLEAN_AND:
            assert i.aux == Auxcode.TYPETYPE_INTEGER_INTEGER
            b = self._stack.pop_int()
            a = self._stack.pop_int()
            self._stack.push_int(a & b)

        elif i.op == Opcode.EXCLUSIVE_OR:
            assert i.aux == Auxcode.TYPETYPE_INTEGER_INTEGER
            b = self._stack.pop_int()
            a = self._stack.pop_int()
            self._stack.push_int(a ^ b)

        elif i.op == Opcode.BOOLEAN_NOT:
            self._stack.push_int_bool(not self._stack.pop_int_bool())

        elif i.op == Opcode.ONES_COMPLEMENT:
            self._stack.push_int(~self._stack.pop_int())

        elif i.op == Opcode.SHIFT_LEFT:
            b = self._stack.pop_int()
            a = self._stack.pop_int()
            self._stack.push_int(a << b)

        elif i.op == Opcode.SHIFT_RIGHT:
            b = self._stack.pop_int()
            a = self._stack.pop_int()
            self._stack.push_int(a >> b)

        elif i.op == Opcode.USHIFT_RIGHT:
            b = self._stack.pop_int()
            a = self._stack.pop_int()
            self._stack.push_int(a >> b)

        elif i.op == Opcode.ADD:
            b = self._stack.pop()
            a = self._stack.pop()
            self._stack.push(a + b)

        elif i.op == Opcode.SUB:
            b = self._stack.pop()
            a = self._stack.pop()
            self._stack.push(a - b)

        elif i.op == Opcode.MUL:
            b = self._stack.pop()
            a = self._stack.pop()
            self._stack.push(a * b)

        elif i.op == Opcode.DIV:
            b = self._stack.pop()
            a = self._stack.pop()
            self._stack.push(a / b)

        elif i.op == Opcode.MODULUS:
            assert i.aux == Auxcode.TYPETYPE_INTEGER_INTEGER
            b = self._stack.pop_int()
            a = self._stack.pop_int()
            self._stack.push_int(a % b)

        elif i.op == Opcode.DE_STRUCT:
            size_orig = i.extra[0] // 4
            start = i.extra[1] // 4
            size = i.extra[2] // 4

            if size + start < size_orig:
                self.sp -= size_orig
                self.sp += size + start
                self._stack.set_stack_pointer(self.sp)

            if start > 0:
                for j in range(self.sp - size - start, self.sp - start):
                    self._stack.assign(j + start, j)

                self.sp -= start
                self._stack.set_stack_pointer(self.sp)

        elif i.op == Opcode.STORE_IP:
            self._save_ip = self.ip + i.aux.value

        elif i.op == Opcode.STORE_STATE:
            self._save_ip = self.ip + i.aux.value
            self._save_bp = i.extra[0]
            self._save_sp = i.extra[1]

        elif i.op == Opcode.EXECUTE_COMMAND:
            cmd = i.extra[0]
            argc = i.extra[1]

            if cmd >= len(self._spec.functions):
                raise ValueError(f"Command {cmd} not implemented")

            vmcmd = self._spec.functions[cmd]

            if not hasattr(self._impl, vmcmd.name):
                raise ValueError(f"Method {vmcmd.name} not implemented")

            if argc != len(vmcmd.args):
                raise ValueError(f"Expected {len(vmcmd.name)} arguments, got {argc}")

            method = getattr(self._impl, vmcmd.name)

            if not callable(method):
                raise TypeError(f"Method {vmcmd.name} is not a callable")

            args = []
            for expect in vmcmd.args:
                if expect.ty != VMType.ACTION:
                    args.append(self._stack.pop_vmtype(expect.ty))
                else:
                    args.append(
                        _VMClosure(ip=self._save_ip, sp=self._save_sp, bp=self._save_bp)
                    )

            rv = method(*args)

            _logger.debug("CMD %s(%s) -> %s", vmcmd.name, args, rv)

            if vmcmd.return_type != VMType.VOID:
                self._stack.push_vmtype(vmcmd.return_type, rv)

        else:
            raise NotImplementedError(f"Opcode {i.op} not implemented")

        assert self.ip >= 0
        assert self.sp >= 0

    def run(self, from_start=True):
        """
        Start running code.

        Args:
            from_start: If True, start from the beginning of the script.
        """

        if len(self._ret) > 0:
            raise ValueError("In the middle of some execution context?")

        if from_start:
            self.ip = 0
            self._stack.set_stack_pointer(0)

        _logger.debug("RUN ip=%d sp=%d", self.ip, self.sp)

        while True:
            i = read_instr(self._ncs)

            _logger.debug(
                "INSTR %7d +%-4d %-20s %-20s (%s)",
                self.ip - (2 + i.extra_len),
                self.sp,
                i.op.name,
                i.aux.name,
                i.extra,
            )

            try:
                self._exec(i)
            except _ScriptExecutionEnd:
                _logger.debug("DONE")
                break

    def proxy(self):
        """
        Return a proxy object that can directly invoke NWScript functions
        from the python side.

        This will only work if NDB information is present.
        """

        parent = self

        class Proxy:
            def __getattr__(self, name):
                def fn(*args):
                    return parent.call(name, *args)

                return fn

        return Proxy()

    def _push_ndb_type(self, ty, value=None):
        match ty:
            case ndb.ScalarType.VOID:
                pass
            case ndb.ScalarType.INT:
                self._stack.push_int(value)
            case ndb.ScalarType.FLOAT:
                self._stack.push_float(value)
            case ndb.ScalarType.STRING:
                self._stack.push_string(value)
            case ndb.ScalarType.OBJECT:
                self._stack.push_object(value)
            case ndb.ScalarType.EFFECT:
                self._stack.push_vmtype(VMType.EFFECT, value)
            case ndb.StructRef(struct_id):
                # Structs are not actually a real datatype in nwscript bytecode:
                # they are pushed/popped as individual stack elements.
                # The python representation is always a dict of field name -> value;
                # except for the builtin "vector" struct, which is a NamedTuple.
                struct = self._ndb.structs[struct_id]
                for lbl, fty in struct.fields:
                    # The code here works for both tuples and dicts.
                    lval = (
                        (value[lbl] if isinstance(value, dict) else getattr(value, lbl))
                        if value is not None
                        else None
                    )
                    self._push_ndb_type(fty, lval)
            case _:
                raise NotImplementedError(f"Type {ty} not implemented")

    def _pop_ndb_type(self, ty, idx=-1):
        match ty:
            case ndb.ScalarType.VOID:
                return None
            case ndb.ScalarType.INT:
                return self._stack.pop_int(idx)
            case ndb.ScalarType.FLOAT:
                return self._stack.pop_float(idx)
            case ndb.ScalarType.STRING:
                return self._stack.pop_string(idx)
            case ndb.ScalarType.OBJECT:
                return self._stack.pop_object(idx)
            case ndb.ScalarType.EFFECT:
                return self._stack.pop_vmtype(VMType.EFFECT)
            case ndb.StructRef(struct_id):
                struct = self._ndb.structs[struct_id]
                values = {
                    lbl: self._pop_ndb_type(fty, idx) for lbl, fty in struct.fields
                }
                # Special case: the builtin "vector" is a NamedTuple as per _types;
                # This is the only one that is not dict.
                if struct.label == "vector":
                    return Vector(**values)
                return values
            case _:
                raise NotImplementedError(f"Type {ty} not implemented")

    def call(self, fn, *args):
        """
        Call a NWScript function.

        This will only work if NDB information is present.

        Args:
            fn: The function name.
            args: The arguments to the function.

        Raises:
            ValueError: If the function is not found, or if the number of arguments
                does not match the function signature.
        """

        assert self._ndb
        if len(self._ret) > 0:
            raise ValueError(f"Ret stack not empty {self._ret}")

        f = self._ndb.function_by_name(fn)

        if f.b_start >= 0xFFFFFFFF:
            raise ValueError(f"Function {fn} was elided out")
        self.ip = f.b_start - 8 - 4 - 1

        _logger.debug("CALL fn=%s", fn)

        self._push_ndb_type(f.ret_type)

        if len(args) != len(f.args):
            raise ValueError(f"Expected {len(f.args)} arguments, got {len(args)}")

        for arg, argtype in zip(args, f.args):
            self._push_ndb_type(argtype, arg)

        self.run(from_start=False)

        return self._pop_ndb_type(f.ret_type, 0)
