/*
<%
import pybind11
cfg['compiler_args'] = ['-std=c++11']
cfg['include_dirs'] = [pybind11.get_include(), pybind11.get_include(True)]
%>
*/
#include <pybind11/pybind11.h>
#include "thing.h"

namespace py = pybind11;

int add(int i, int j) {
    return i + j;
}

PYBIND11_PLUGIN(mymodule) {
    pybind11::module m("mymodule", "auto-compiled c++ extension");
    m.def("add", &add);
#ifdef THING_DEFINED
    py::class_<Thing>(m, "Thing")
        .def(py::init<>())
        .def("cheer", &Thing::cheer);
#endif
    return m.ptr();
}
