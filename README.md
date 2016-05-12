# Import C++ files directly from Python!

cppimport is a small import hook that determines whether there is a C++ source file that matches the requested module. If there is, the file is compiled as an extension and placed in the same folder as the C++ source file. The standard module loading capabilities of python then load the module.
