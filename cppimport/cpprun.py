import time
import os
import sys
import argparse

import cppimport

footer = """
<%
import pybind11
cfg['compiler_args'] = ['-std=c++11']
cfg['include_dirs'] = [pybind11.get_include(), pybind11.get_include(True)]
%>
#include <pybind11/pybind11.h>
PYBIND11_PLUGIN(${fullname}) {
    pybind11::module m("${fullname}", "");
    m.def("main", main);
    return m.ptr();
}
"""


def cpp_run():
    parser = argparse.ArgumentParser(description='Run a C++ file with cppimport')
    parser.add_argument('filename', help = 'The file to run.')
    parser.add_argument(
        '--add_main_caller', '-m',
        action = 'store_true',
        help = 'Add a pybind11 function that will call your main()'
    )
    parser.add_argument(
        '--verbose', '-v',
        action = 'store_true',
        help = 'Tell me everything!'
    )
    args = parser.parse_args()

    if args.verbose:
        cppimport.set_quiet(False)

    filename = args.filename
    filedir = os.path.dirname(filename)
    filebasename = os.path.basename(filename)
    module_name, file_extension = os.path.splitext(filebasename)

    if args.add_main_caller:
        cpprun_dir = '.cpprunfiles'
        if not os.path.exists(cpprun_dir):
            os.makedirs(cpprun_dir)
        src = os.path.join(cpprun_dir, filebasename)
        open(src, 'w').write(open(filename, 'r').read() + footer)
        sys.path.append(cpprun_dir)
    else:
        sys.path.append(filedir)

    module = cppimport.imp(module_name)

    if args.verbose:
        print("Launching!")
    module.main()


if __name__ == '__main__':
    cpp_run()
