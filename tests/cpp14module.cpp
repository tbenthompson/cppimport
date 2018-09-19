/*
<%
import pybind11
cfg['compiler_args'] = ['-std=c++14']
cfg['include_dirs'] = [pybind11.get_include(), pybind11.get_include(True)]
%>
*/
#include <pybind11/pybind11.h>

namespace py = pybind11;

// Use auto instead of int to check C++14
auto add(int i, int j) {
    return i + j;
}

PYBIND11_MODULE(cpp14module, m) {
    m.def("add", &add);
}
