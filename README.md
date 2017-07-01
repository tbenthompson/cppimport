##### If you've used cppimport version 0.0.*, some new features for you! Compiler arguments, multiple source files, bug fixes! Read on.

# Import C or C++ files directly from Python!
Let's try it out. First, if you're on Linux or OS X, install with the terminal command `pip install cppimport`.

Here's a simple C++ extension using [pybind11](https://github.com/pybind/pybind11):
```c++
/*
<%
setup_pybind11(cfg)
%>
*/
#include <pybind11/pybind11.h>

namespace py = pybind11;

int square(int x) {
    return x * x;
}

PYBIND11_PLUGIN(somecode) {
    pybind11::module m("somecode", "auto-compiled c++ extension");
    m.def("square", &square);
    return m.ptr();
}
```

Save this code as `somecode.cpp`.

Open a python interpreter and run these lines [\[1\]](#notes):
```python
>>> import cppimport
>>> somecode = cppimport.imp("somecode") #This will pause for a moment to compile the module
>>> somecode.square(9)
81
```

I'm a big fan of the workflow that this enables, where you can edit both C++ files and Python and recompilation happens transparently.

# What's actually going on?

**The technical description:** cppimport looks for a C or C++ source file that matches the requested module. If such a file exists, the file is first run through the Mako templating system. The compilation options produced by the Mako pass are then use to compile the file as a Python extension. The extension (shared library) that is produced is placed in the same folder as the C++ source file. Then, the extension is loaded.

**Simpler language please:** Sometimes Python just isn't fast enough. Or you have existing code in a C++ library. So, you write a Python *extension module*, a library of compiled code. I recommend [pybind11](https://github.com/pybind/pybind11) for C++ to Python bindings or [cffi](https://cffi.readthedocs.io/en/latest/) for C to Python bindings. I've done this a lot over the years. But, I discovered that my productivity goes through the floor when my development process goes from *Edit -> Test* in just Python to *Edit -> Compile -> Test* in Python plus C++. So, `cppimport` combines the process of compiling and importing an extension in Python so that you can type `modulename = cppimport.imp("modulename")` and not have to worry about multiple steps. Internally, `cppimport` looks for a file `modulename.cpp`. If one is found, it's run through the Mako templating system to gather compiler options, then it's compiled and loaded as an extension module.

Note that because of the Mako pre-processing, the comments around the configuration block may be omitted.

### Recompilation only happens when necessary:
Compilation should only happen the first time the module is imported. The C++ source is compared with a checksum on each import to determine if the file has changed. Additional dependencies (header files!) can be tracked by adding to the Mako header:
```
cfg['dependencies'] = ['file1.h', 'file2.h']
```

### I need to set the compiler or linker args!
```
cfg['linker_args'] = ['...']
cfg['compiler_args'] = ['...']
cfg['libraries'] = ['...']
cfg['include_dirs'] = ['...']
```

For example, to use C++11, add:
```
<%
cfg['compiler_args'] = ['-std=c++11']
%>
```

### I want multiple source files for one extension!
```
cfg['sources'] = ['...']
```

### I need more output!
Calling `cppimport.set_quiet(False)` will result in output that will be helpful in debugging compile errors.

### Sometimes I need to force a rebuild even when the checksum matches
Call `cppimport.force_rebuild()` before running `cppimport.imp(...)`.

### I want incremental compiles on extensions with multiple sources.

(For the uninitiated, incremental compilation involves only recompiling those source files that have changed or include headers that have changed.)

cppimport is built on top of the setuptools and distutils, the standard library for python packaging and distribution. Unfortunately, setuptools does not support incremental compilation. I recommend following the suggestions on [this SO answer](http://stackoverflow.com/questions/11013851/speeding-up-build-process-with-distutils). That is:

1. Use ccache to (massively) reduce the cost of rebuilds
2. Enable parallel compilation. This can be done with `cfg['parallel'] = True` in the C++ file's configuration header.

### I need information about filepaths in my module configuration code!
The module name is available as the `fullname` variable and the C++ module file is available as `filepath`.
For example,
```
<%
module_dir = os.path.dirname(filepath)
%>
```

### Windows?
I don't know if `cppimport` works on Windows. If you're on Windows, try it out and I'll happily accept a pull request for any issues that you fix.

# cppimport uses the MIT License
