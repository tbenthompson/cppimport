<%
setup_pybind11(cfg)
%>
#include <pybind11/pybind11.h>

PYBIND11_PLUGIN(hook_test) {
    pybind11::module m("hook_test", "auto-compiled c++ extension");
    m.def("sub", [] (int i, int j) { return i - j; } );
    return m.ptr();
}
