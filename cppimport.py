import sys
import os
import setuptools
import pybind11
import mako

template = """
#include <pybind11/pybind11.h>

${code}

name py = pybind11

PYBIND11_PLUGIN(${module_name}) {
    py::module m("${module_name}", "auto-compiled c++ extension");

    m.def("add", &add);

    return m.ptr();
}
"""

class CppFinder(object):
    def __init__(self):
        pass

    def find_module(self, fullname, path = None):
        ext = '.cpp'
        filename = fullname + ext
        if not os.path.exists(filename):
            return None
        temp_filename = 'build/' + filename
        with open(filename, 'r') as f:
            with open(temp_filename, 'w') as f_tmp:
                f_tmp.write(f.read())
        ext = setuptools.Extension(
            fullname,
            sources = [temp_filename],
            language = 'c++',
            include_dirs = [pybind11.get_include()],
            extra_compile_args = ['-std=c++11']
        )
        setuptools.setup(
            name = fullname,
            ext_modules = [ext],
            script_args = ['-q', 'build_ext', '--inplace']
        )
        return None

sys.meta_path.insert(0, CppFinder())
