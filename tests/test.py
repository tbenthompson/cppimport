import io
import os
import sys
import cppimport
import cppimport.import_hook as cppimp
cppimport.set_quiet(False)

def test_redirected_stream():
    sys.stderr = io.StringIO()
    with cppimp.stdchannel_redirected("stdout") as s:
        with cppimp.stdchannel_redirected("stderr"):
            print("EEEP!")
    assert(s.getvalue() == 'EEEP!\n')

def test_find_module_cpppath():
    mymodule_loc = cppimp.find_module_cpppath("mymodule")
    mymodule_dir = os.path.dirname(mymodule_loc)
    assert(os.path.basename(mymodule_loc) == "mymodule.cpp")

    apackage_path = os.path.join(mymodule_dir, 'apackage', 'mymodule.cpp')
    apackage2_path = os.path.join(mymodule_dir, 'apackage', 'inner', 'mymodule.cpp')
    assert(cppimp.find_module_cpppath("apackage.mymodule") == apackage_path)
    assert(cppimp.find_module_cpppath("apackage.inner.mymodule") == apackage2_path)

def module_tester(mod):
    assert(mod.add(1,2) == 3)
    mod.Thing().cheer()

def test_mymodule():
    import mymodule
    module_tester(mymodule)

def test_package_mymodule():
    import apackage.mymodule
    module_tester(apackage.mymodule)

def test_inner_package_mymodule():
    import apackage.inner.mymodule
    module_tester(apackage.inner.mymodule)

if __name__ == '__main__':
    test_redirected_stream()
    test_find_module_cpppath()
    test_mymodule()
    test_package_mymodule()
    test_inner_package_mymodule()
