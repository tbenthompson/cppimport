/*
<%
import pybind11
cfg['compiler_args'] = ['-std=c++11']
cfg['include_dirs'] = [pybind11.get_include(), pybind11.get_include(True)]
%>
*/
#include <pybind11/pybind11.h>
#include <iostream>

int main() {
    std::cout << "HI!" << std::endl;
}

PYBIND11_PLUGIN(free_module) {
    pybind11::module m("free_module", "auto-compiled c++ extension");
    m.def("main", &main);
    return m.ptr();
}
