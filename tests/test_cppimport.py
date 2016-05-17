import os
import sys
import copy
import subprocess
import contextlib
import cppimport
import cppimport.import_hook as cppimp
cppimport.set_quiet(False)

@contextlib.contextmanager
def appended(filename, text):
    orig = open(filename, 'r').read()
    open(filename, 'a').write(text)
    try:
        yield
    finally:
        open(filename, 'w').write(orig)

def subprocess_check(test_code, returncode = 0):
    p = subprocess.Popen([
        'python', '-c', test_code
    ], cwd = os.path.dirname(__file__))
    p.wait()
    assert(p.returncode == returncode)

def test_find_module_cpppath():
    mymodule_loc = cppimp.find_module_cpppath("mymodule")
    mymodule_dir = os.path.dirname(mymodule_loc)
    assert(os.path.basename(mymodule_loc) == "mymodule.cpp")

    apackage_path = os.path.join(mymodule_dir, 'apackage', 'mymodule.cpp')
    apackage2_path = os.path.join(mymodule_dir, 'apackage', 'inner', 'mymodule.cpp')
    assert(cppimp.find_module_cpppath("apackage.mymodule") == apackage_path)
    assert(cppimp.find_module_cpppath("apackage.inner.mymodule") == apackage2_path)

def module_tester(mod, cheer = False):
    assert(mod.add(1,2) == 3)
    if cheer:
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

def test_with_file_in_syspath():
    orig_sys_path = copy.copy(sys.path)
    sys.path.append(os.path.join(os.path.dirname(__file__), 'mymodule.cpp'))
    import mymodule
    sys.path = orig_sys_path

def test_rebuild_after_failed_compile():
    import mymodule
    test_code = 'import cppimport;import mymodule;assert(mymodule.add(1,2) == 3)'
    with appended('tests/mymodule.cpp', ";asdf;"):
        subprocess_check(test_code, 1)
    subprocess_check(test_code, 0)

def test_rebuild_header_after_change():
    import mymodule
    add_to_thing = """
        struct Thing {
            void cheer() {
                std::cout << "WAHHOOOO" << std::endl;
            }
        };
        #define THING_DEFINED
        """
    test_code = 'import cppimport;import mymodule;mymodule.Thing().cheer()'
    with appended('tests/thing.h', add_to_thing):
        subprocess_check(test_code)

def test_compiler_flags():
    import cpp14module
    assert(cpp14module.add(1,2) == 3)
