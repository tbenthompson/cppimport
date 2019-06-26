import os
import io
import sys
import copy
import subprocess
import contextlib

import cppimport
import cppimport.build_module
import cppimport.templating
import cppimport.import_hook
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

def test_redirected_stream():
    sys.stderr = io.StringIO()
    with cppimport.build_module.stdchannel_redirected("stdout") as s:
        with cppimport.build_module.stdchannel_redirected("stderr"):
            print("EEEP!")
    assert(s.getvalue() == 'EEEP!\n')

def test_find_module_cpppath():
    mymodule_loc = cppimport.find.find_module_cpppath("mymodule")
    mymodule_dir = os.path.dirname(mymodule_loc)
    assert(os.path.basename(mymodule_loc) == "mymodule.cpp")

    apackage = cppimport.find.find_module_cpppath("apackage.mymodule")
    apackage_correct = os.path.join(mymodule_dir, 'apackage', 'mymodule.cpp')
    assert(apackage == apackage_correct)

    inner = cppimport.find.find_module_cpppath("apackage.inner.mymodule")
    inner_correct = os.path.join(mymodule_dir, 'apackage', 'inner', 'mymodule.cpp')
    assert(inner == inner_correct)

def test_get_rendered_source_filepath():
    rendered_path = cppimport.templating.get_rendered_source_filepath('abc.cpp')
    assert(rendered_path == '.rendered.abc.cpp')

def module_tester(mod, cheer = False):
    assert(mod.add(1,2) == 3)
    if cheer:
        mod.Thing().cheer()

def test_mymodule():
    mymodule = cppimport.imp("mymodule")
    module_tester(mymodule)

def test_package_mymodule():
    mymodule = cppimport.imp("apackage.mymodule")
    module_tester(mymodule)

def test_inner_package_mymodule():
    mymodule = cppimport.imp("apackage.inner.mymodule")
    module_tester(mymodule)

def test_with_file_in_syspath():
    orig_sys_path = copy.copy(sys.path)
    sys.path.append(os.path.join(os.path.dirname(__file__), 'mymodule.cpp'))
    mymodule = cppimport.imp("mymodule")
    sys.path = orig_sys_path

def test_rebuild_after_failed_compile():
    mymodule = cppimport.imp("mymodule")
    test_code = '''
import cppimport; mymodule = cppimport.imp("mymodule");assert(mymodule.add(1,2) == 3)
'''
    with appended('tests/mymodule.cpp', ";asdf;"):
        subprocess_check(test_code, 1)
    subprocess_check(test_code, 0)

add_to_thing = """
#include <iostream>
struct Thing {
    void cheer() {
        std::cout << "WAHHOOOO" << std::endl;
    }
};
#define THING_DEFINED
"""

def test_no_rebuild_if_no_deps_change():
    mymodule = cppimport.imp("mymodule")
    test_code = '''
import cppimport;
mymodule = cppimport.imp("mymodule");
assert(not hasattr(mymodule, 'Thing'))
'''
    with appended('tests/thing2.h', add_to_thing):
        subprocess_check(test_code)

def test_rebuild_header_after_change():
    mymodule = cppimport.imp("mymodule")
    test_code = '''
import cppimport; cppimport.set_quiet(False); mymodule = cppimport.imp("mymodule"); mymodule.Thing().cheer()
'''
    with appended('tests/thing.h', add_to_thing):
        subprocess_check(test_code)

def test_raw_extensions():
    raw_extension = cppimport.imp("raw_extension")
    assert(raw_extension.add(1,2) == 3)

def test_extra_sources():
    mod = cppimport.imp("extra_sources")
    assert(mod.square_sum(3, 4) == 25)

# TODO: cpprun is incomplete and possibly not a good idea...
# def test_cpprun():
#     p = subprocess.Popen([
#         'cpprun', '-m', 'free_module.cpp'
#     ], cwd = os.path.dirname(__file__), stdout = subprocess.PIPE)
#     p.wait()
#     assert(b'HI!\n' == p.stdout.read())

def test_import_hook():
    # Force rebuild to make sure we're not just reloading the already compiled
    # module from disk
    cppimport.force_rebuild(True)
    import hook_test
    cppimport.force_rebuild(False)
