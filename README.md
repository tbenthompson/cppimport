##### If you've used cppimport version 0.0.\*, some new features for you! Compiler arguments, multiple source files, bug fixes! Read on.

# Import C or C++ files directly from Python!
Let's try it out. First, if you're on Linux or OS X, install with the terminal command `pip install cppimport`.

Most cppimport users combine it with [pybind11](https://github.com/pybind/pybind11), but you can use a range of methods to create your Python extensions. Raw C extensions, Boost.Python, SWIG all work. Let's look at a simple C++ extension:

```c++
#include <pybind11/pybind11.h>

namespace py = pybind11;

int square(int x) {
    return x * x;
}


PYBIND11_MODULE(somecode, m) {
    m.def("square", &square);
}
/*
<%
setup_pybind11(cfg)
%>
*/
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

# I want things to be even easier! (Python import hook)

Add a comment containing the string "cppimport" on the first line of the file. This MUST be on the first line. This is explained further down.

```c++
// cppimport
```

Then import the file using the import hook:
```python
>>> import cppimport.import_hook
>>> import somecode #This will pause for a moment to compile the module
>>> somecode.square(9)
81
```

# What's actually going on?

**The technical description:** cppimport looks for a C or C++ source file that matches the requested module. If such a file exists, the file is first run through the Mako templating system. The compilation options produced by the Mako pass are then use to compile the file as a Python extension. The extension (shared library) that is produced is placed in the same folder as the C++ source file. Then, the extension is loaded.

**Simpler language please:** Sometimes Python just isn't fast enough. Or you have existing code in a C++ library. So, you write a Python *extension module*, a library of compiled code. I recommend [pybind11](https://github.com/pybind/pybind11) for C++ to Python bindings or [cffi](https://cffi.readthedocs.io/en/latest/) for C to Python bindings. I've done this a lot over the years. But, I discovered that my productivity goes through the floor when my development process goes from *Edit -> Test* in just Python to *Edit -> Compile -> Test* in Python plus C++. So, `cppimport` combines the process of compiling and importing an extension in Python so that you can type `modulename = cppimport.imp("modulename")` and not have to worry about multiple steps. Internally, `cppimport` looks for a file `modulename.cpp`. If one is found, it's run through the Mako templating system to gather compiler options, then it's compiled and loaded as an extension module.

Note that because of the Mako pre-processing, the comments around the configuration block may be omitted.  Putting the configuration block at the end of the file, while optional, ensures that line numbers remain correct in compilation error messages.

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

### Why does the import hook need "cppimport" on the first line of the .cpp file?
Modifying the Python import system is a global modification and thus affects all imports from any other package. As a result, to avoid accidentally breaking another package, the import hook uses an "opt in" system where C and C++ files can specify they are meant to be used with cppimport by having a comment including the phrase "cppimport" on the first line of the file. 

### Windows?
I've used `cppimport` with MinGW-w64 and Python 3.6 and had good success. I've also had reports that `cppimport` works on Windows with Python 3.6 and Visual C++ 2015 Build Tools. The main challenge is making sure that distutils is aware of your available compilers. Try out the suggestion [here](https://stackoverflow.com/questions/3297254/how-to-use-mingws-gcc-compiler-when-installing-python-package-using-pip).

# cppimport uses the MIT License
