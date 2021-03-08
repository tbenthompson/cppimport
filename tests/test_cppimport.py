import contextlib
import copy
import logging
import os
import subprocess
import sys

import cppimport
import cppimport.build_module
import cppimport.templating
from cppimport.find import find_module_cpppath

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
root_logger.addHandler(handler)


@contextlib.contextmanager
def appended(filename, text):
    with open(filename, "r") as f:
        orig = f.read()
    with open(filename, "a") as f:
        f.write(text)
    try:
        yield
    finally:
        with open(filename, "w") as f:
            f.write(orig)


def subprocess_check(test_code, returncode=0):
    p = subprocess.run(
        ["python", "-c", test_code],
        cwd=os.path.dirname(__file__),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print(p.stdout.decode("utf-8"))
    print(p.stderr.decode("utf-8"))
    assert p.returncode == returncode


def test_find_module_cpppath():
    mymodule_loc = find_module_cpppath("mymodule")
    mymodule_dir = os.path.dirname(mymodule_loc)
    assert os.path.basename(mymodule_loc) == "mymodule.cpp"

    apackage = find_module_cpppath("apackage.mymodule")
    apackage_correct = os.path.join(mymodule_dir, "apackage", "mymodule.cpp")
    assert apackage == apackage_correct

    inner = find_module_cpppath("apackage.inner.mymodule")
    inner_correct = os.path.join(mymodule_dir, "apackage", "inner", "mymodule.cpp")
    assert inner == inner_correct


def test_get_rendered_source_filepath():
    rendered_path = cppimport.templating.get_rendered_source_filepath("abc.cpp")
    assert rendered_path == ".rendered.abc.cpp"


def module_tester(mod, cheer=False):
    assert mod.add(1, 2) == 3
    if cheer:
        mod.Thing().cheer()


def test_mymodule():
    mymodule = cppimport.imp("mymodule")
    module_tester(mymodule)


def test_mymodule_build():
    cppimport.build("mymodule")
    import mymodule

    module_tester(mymodule)


def test_mymodule_from_filepath():
    mymodule = cppimport.imp_from_filepath("tests/mymodule.cpp")
    module_tester(mymodule)


def test_package_mymodule():
    mymodule = cppimport.imp("apackage.mymodule")
    module_tester(mymodule)


def test_inner_package_mymodule():
    mymodule = cppimport.imp("apackage.inner.mymodule")
    module_tester(mymodule)


def test_with_file_in_syspath():
    orig_sys_path = copy.copy(sys.path)
    sys.path.append(os.path.join(os.path.dirname(__file__), "mymodule.cpp"))
    cppimport.imp("mymodule")
    sys.path = orig_sys_path


def test_rebuild_after_failed_compile():
    cppimport.imp("mymodule")
    test_code = """
import cppimport; mymodule = cppimport.imp("mymodule");assert(mymodule.add(1,2) == 3)
"""
    with appended("tests/mymodule.cpp", ";asdf;"):
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
    cppimport.imp("mymodule")
    test_code = """
import cppimport;
mymodule = cppimport.imp("mymodule");
assert(not hasattr(mymodule, 'Thing'))
"""
    with appended("tests/thing2.h", add_to_thing):
        subprocess_check(test_code)


def test_rebuild_header_after_change():
    cppimport.imp("mymodule")
    test_code = """
import cppimport;
mymodule = cppimport.imp("mymodule");
mymodule.Thing().cheer()
"""
    with appended("tests/thing.h", add_to_thing):
        subprocess_check(test_code)
    assert open("tests/thing.h", "r").read() == ""


def test_raw_extensions():
    raw_extension = cppimport.imp("raw_extension")
    assert raw_extension.add(1, 2) == 3


def test_extra_sources_and_parallel():
    cppimport.settings["force_rebuild"] = True
    mod = cppimport.imp("extra_sources")
    cppimport.settings["force_rebuild"] = False
    assert mod.square_sum(3, 4) == 25


def test_import_hook():
    import cppimport.import_hook

    # Force rebuild to make sure we're not just reloading the already compiled
    # module from disk
    cppimport.force_rebuild(True)
    import hook_test

    cppimport.force_rebuild(False)
    hook_test
