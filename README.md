# Import C++ files directly from Python!

cppimport is a small import hook that determines whether there is a C++ source file that matches the requested module. If there is, the file is compiled as a Python extension using [https://github.com/pybind/pybind11](pybind11) and placed in the same folder as the C++ source file. Python is then able to find the module and load it.
