/* cppimport
compiler_args = ['-std=c++11']
*/
#include <pybind11/pybind11.h>

namespace py = pybind11;

int add(int i, int j) {
    return i + j;
}

PYBIND11_PLUGIN(mymodule) {
    pybind11::module m("mymodule", "auto-compiled c++ extension");
    m.def("add", &add);
    return m.ptr();
}
