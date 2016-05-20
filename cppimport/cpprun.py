import os
import sys
import tempfile
import mako.template
import argparse
import cppimport
cppimport.install()

tmpl = """
${code}
#include <pybind11/pybind11.h>
namespace py = pybind11;
PYBIND11_PLUGIN(runnable) {
    py::module m("runnable", "");
    m.def("main", main);
    return m.ptr();
}
"""

def cpp_run():
    parser = argparse.ArgumentParser(description='Run a C++ file with cppimport')
    parser.add_argument('filename', help = 'The file to run.')
    parser.add_argument('--verbose', '-v', action = 'store_true', help = 'Tell me everything!')
    args = parser.parse_args()

    if args.verbose:
        cppimport.set_quiet(False)

    filename = args.filename

    code = open(filename, 'r').read()
    main = mako.template.Template(tmpl).render(code = code)

    cpprun_dir = '.cpprunfiles'
    if not os.path.exists(cpprun_dir):
        os.makedirs(cpprun_dir)
    src = os.path.join(cpprun_dir, 'runnable.cpp')
    open(src, 'w').write(main)

    sys.path.append(cpprun_dir)
    import runnable
    sys.path.remove(cpprun_dir)

    if args.verbose:
        print("Launching!")
    runnable.main()


if __name__ == '__main__':
    cpp_run()
