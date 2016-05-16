#include <pybind11/pybind11.h>

namespace py = pybind11;

int add(int i, int j) {
    return i + j;
}

void pyexport(py::module& m) {
    m.def("add", &add);
}
