#include <pybind11/pybind11.h>
#include "thing.h"

namespace py = pybind11;

int add(int i, int j) {
    return i + j;
}

void pyexport(py::module& m) {
    m.def("add", &add);
#ifdef THING_DEFINED
    py::class_<Thing>(m, "Thing")
        .def(py::init<>())
        .def("cheer", &Thing::cheer);
#endif
}
