<%
setup_pybind11(cfg)
cfg['sources'] = ['extra_sources1.cpp']
%>
#include <pybind11/pybind11.h>

int square(int x);

int square_sum(int x, int y) {
    return square(x) + square(y);
}

PYBIND11_MODULE(extra_sources, m) {
    m.def("square_sum", &square_sum);
}
