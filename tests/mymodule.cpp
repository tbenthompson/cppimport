#include <pybind11/pybind11.h>
#include <iostream>

namespace py = pybind11;

int add(int i, int j) {
    return i + j;
}

struct Thing {
    void cheer() {
        std::cout << "WAHHOOOO" << std::endl;
    }
};

void pyexport(py::module& m) {
    m.def("add", &add);
    py::class_<Thing>(m, "Thing")
        .def(py::init<>())
        .def("cheer", &Thing::cheer);
}
