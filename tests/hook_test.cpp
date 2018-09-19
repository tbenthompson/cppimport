/*cppimport*/
<%
setup_pybind11(cfg)
%>
#include <pybind11/pybind11.h>

PYBIND11_MODULE(hook_test, m) {
    m.def("sub", [] (int i, int j) { return i - j; } );
}
