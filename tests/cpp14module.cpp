/* cppimport
compiler_args = ['-std=c++14']
*/
#include <pybind11/pybind11.h>

namespace py = pybind11;

// Use auto instead of int to check C++14
auto add(int i, int j) {
    return i + j;
}

PYBIND11_PLUGIN(cpp14module) {
    pybind11::module m("cpp14module", "auto-compiled c++ extension");
    m.def("add", &add);
    return m.ptr();
}
