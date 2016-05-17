/* cppimport
compiler_args = ['-std=c++14']
*/
#include <pybind11/pybind11.h>

namespace py = pybind11;

// Use auto instead of int to check C++14
auto add(int i, int j) {
    return i + j;
}

void pyexport(py::module& m) {
    m.def("add", &add);
}
