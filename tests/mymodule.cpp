/*
<%
setup_pybind11(cfg)
cfg['dependencies'] = ['thing.h']
%>
*/
#include <pybind11/pybind11.h>
#include "thing.h"
#include "thing2.h"

namespace py = pybind11;

int add(int i, int j) {
    return i + j;
}

PYBIND11_MODULE(mymodule, m) {
    m.def("add", &add);
#ifdef THING_DEFINED
    #pragma message "stuff"
    py::class_<Thing>(m, "Thing")
        .def(py::init<>())
        .def("cheer", &Thing::cheer);
#endif
}
