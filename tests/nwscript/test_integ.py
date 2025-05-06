import io

from nwn.nwscript.comp import Compiler
from nwn.nwscript.vm import Script, VM
from nwn.nwscript import langspec


class DefaultScriptImpl:
    def TestCall(self, i: int) -> int:
        return i + 21


def test_compile_and_execute():
    nw_script = "int TestCall(int v);"
    test_script = """
    int add(int a, int b)
    {
        return TestCall(a) + TestCall(b);
    }

    void main()
    {
        int result = add(21, 42);
    }
    """

    def resolver(filename):
        print(filename)
        if filename == "nwscript.nss":
            return nw_script
        if filename == "test_script.nss":
            return test_script
        assert False
        return None

    with io.StringIO(nw_script) as nws:
        spec = langspec.read(nws)

    compiler = Compiler(resolver)
    ncs_bytes, ndb_text = compiler.compile("test_script")
    assert ncs_bytes
    assert ndb_text

    script = Script(io.BytesIO(ncs_bytes), io.StringIO(ndb_text))
    vm = VM(script=script, spec=spec, impl=DefaultScriptImpl())

    assert vm.call("add", 5, 3) == 50
    vm.run()
