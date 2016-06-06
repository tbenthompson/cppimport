<%
setup_pybind11(cfg)
cfg['sources'] = ['extra_sources1.cpp']
%>

int square(int x);

int square_sum(int x, int y) {
    return square(x) + square(y);
}
