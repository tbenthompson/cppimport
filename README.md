# cppimport - Import C++ directly from Python! 

<p align=center>
    <a target="_blank" href="https://www.python.org/downloads/" title="Python version"><img src="https://img.shields.io/badge/python-%3E=_3.7-green.svg"></a>
    <a target="_blank" href="https://pypi.org/project/cppimport/" title="PyPI version"><img src="https://img.shields.io/pypi/v/cppimport?logo=pypi"></a>
    <a target="_blank" href="https://pypi.org/project/cppimport/" title="PyPI"><img src="https://img.shields.io/pypi/dm/cppimport"></a>
    <a target="_blank" href="LICENSE" title="License: MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg"></a>
    <a target="_blank" href="https://github.com/tbenthompson/cppimport/actions" title="Test Status"><img src="https://github.com/tbenthompson/cppimport/actions/workflows/test.yml/badge.svg"></a>
    <a target="_blank" href="https://codecov.io/gh/tbenthompson/cppimport" title="Code coverage"><img src="https://codecov.io/gh/tbenthompson/cppimport/branch/main/graph/badge.svg?token=GWpX62xMt5"/></a>
</a>

</p>

## Contributing and architecture

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on the internals of `cppimport` and how to get involved in development.

## Installation

Install with `pip install cppimport`.

## A quick example

Save the C++ code below as `somecode.cpp`.
```c++
// cppimport
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

Then open a Python interpreter and import the C++ extension:
```python
>>> import cppimport.import_hook
>>> import somecode #This will pause for a moment to compile the module
>>> somecode.square(9)
81
```

Hurray, you've called some C++ code from Python using a combination of `cppimport` and [`pybind11`](https://github.com/pybind/pybind11).  

I'm a big fan of the workflow that this enables, where you can edit both C++ files and Python and recompilation happens transparently! It's also handy for quickly whipping together an optimized version of a slow Python function.

## An explanation 

Okay, now that I've hopefully convinced you on how exciting this is, let's get into the details of how to do this yourself. First, the comment at top is essential to opt in to cppimport. Don't forget this! (See below for an explanation of why this is necessary.)
```c++
// cppimport
```

The bulk of the file is a generic, simple [pybind11](https://github.com/pybind/pybind11) extension. We include the `pybind11` headers, then define a simple function that squares `x`, then export that function as part of a Python extension called `somecode`.

Finally at the end of the file, there's a section I'll call the "configuration block":
```
<%
setup_pybind11(cfg)
%>
```
This region surrounded by `<%` and `%>` is a [Mako](https://www.makotemplates.org/) code block. The region is evaluated as Python code during the build process and provides configuration info like compiler and linker flags to the cppimport build system. 

Note that because of the Mako pre-processing, the comments around the configuration block may be omitted.  Putting the configuration block at the end of the file, while optional, ensures that line numbers remain correct in compilation error messages.

## Building for production
In production deployments you usually don't want to include a c/c++ compiler, all the sources and compile at runtime. Therefore, a simple cli utility for pre-compiling all source files is provided. This utility may, for example, be used in CI/CD pipelines. 

Usage is as simple as

```commandline
python -m cppimport build
```

This will build all `*.c` and `*.cpp` files in the current directory (and it's subdirectories) if they are eligible to be imported (i.e. contain the `// cppimport` comment in the first line).

Alternatively, you may specifiy one or more root directories or source files to be built:

```commandline
python -m cppimport build ./my/directory/ ./my/single/file.cpp
```
_Note: When specifying a path to a file, the header check (`// cppimport`) is skipped for that file._

### Fine-tuning for production
To further improve startup performance for production builds, you can opt-in to skip the checksum and compiled binary existence checks during importing by either setting the environment variable `CPPIMPORT_RELEASE_MODE` to `true` or setting the configuration from within Python:
```python
cppimport.settings['release_mode'] = True
```
**Warning:** Make sure to have all binaries pre-compiled when in release mode, as importing any missing ones will cause exceptions. 

## Frequently asked questions

### What's actually going on?

Sometimes Python just isn't fast enough. Or you have existing code in a C or C++ library. So, you write a Python *extension module*, a library of compiled code. I recommend [pybind11](https://github.com/pybind/pybind11) for C++ to Python bindings or [cffi](https://cffi.readthedocs.io/en/latest/) for C to Python bindings. I've done this a lot over the years. But, I discovered that my productivity is slower when my development process goes from *Edit -> Test* in just Python to *Edit -> Compile -> Test* in Python plus C++. So, `cppimport` combines the process of compiling and importing an extension in Python so that you can just run `import foobar` and not have to worry about multiple steps. Internally, `cppimport` looks for a file `foobar.cpp`. Assuming one is found, it's run through the Mako templating system to gather compiler options, then it's compiled and loaded as an extension module.

### Does cppimport recompile every time a module is imported? 
No! Compilation should only happen the first time the module is imported. The C++ source is compared with a checksum on each import to determine if any relevant file has changed. Additional dependencies (e.g. header files!) can be tracked by adding to the Mako header:
```python
cfg['dependencies'] = ['file1.h', 'file2.h']
```
The checksum is computed by simply appending the contents of the extension C++ file together with the files in `cfg['sources']` and `cfg['dependencies']`. 

### How can I set compiler or linker args?

Standard distutils configuration options are valid:

```python
cfg['extra_link_args'] = ['...']
cfg['extra_compile_args'] = ['...']
cfg['libraries'] = ['...']
cfg['include_dirs'] = ['...']
```

For example, to use C++11, add:
```python
cfg['extra_compile_args'] = ['-std=c++11']
```

### How can I split my extension across multiple source files?

In the configuration block: 
```python
cfg['sources'] = ['extra_source1.cpp', 'extra_source2.cpp']
```

### cppimport isn't doing what I want, can I get more verbose output?
`cppimport` uses the standard Python logging tools. Please add logging handlers to either the root logger or the `"cppimport"` logger. For example, to output all debug level log messages:

```python
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
root_logger.addHandler(handler)
```

### How can I force a rebuild even when the checksum matches?

Set:
```python
cppimport.settings['force_rebuild'] = True
```

And if this is a common occurence, I would love to hear your use case and why the combination of the checksum, `cfg['dependencies']` and `cfg['sources']` is insufficient!

Note that `force_rebuild` does not work when importing the module concurrently.

### Can I import my model concurrently?

It's safe to use `cppimport` to import a module concurrently using multiple threads, processes or even machines!

Before building a module, `cppimport` obtains a lockfile preventing other processors from building it at the same time - this prevents clashes that can lead to failure.
Other processes will wait maximum 10 mins until the first process has built the module and load it. If your module does not build within 10 mins then it will timeout.
You can increase the timeout time in the settings:

```python
cppimport.settings['lock_timeout'] = 10*60 # 10 mins
```

You should not use `force_rebuild` when importing concurrently.

### How can I get information about filepaths in the configuration block?
The module name is available as the `fullname` variable and the C++ module file is available as `filepath`.
For example,
```
<%
module_dir = os.path.dirname(filepath)
%>
```

### How can I make compilation faster? 

In single file extensions, this is a fundamental issue with C++. Heavily templated code is often quite slow to compile. 

If your extension has multiple source files using the `cfg['sources']` capability, then you might be hoping for some kind of incremental compilation. For the uninitiated, incremental compilation involves only recompiling those source files that have changed. Unfortunately this isn't possible because cppimport is built on top of the setuptools and distutils and these standard library components do not support incremental compilation. 

I recommend following the suggestions on [this SO answer](http://stackoverflow.com/questions/11013851/speeding-up-build-process-with-distutils). That is:

1. Use `ccache` to reduce the cost of rebuilds
2. Enable parallel compilation. This can be done with `cfg['parallel'] = True` in the C++ file's configuration header.

As a further thought, if your extension has many source files and you're hoping to do incremental compiles, that probably indicates that you've outgrown `cppimport` and should consider using a more complete build system like CMake.

### Why does the import hook need "cppimport" on the first line of the .cpp file?
Modifying the Python import system is a global modification and thus affects all imports from any other package. As a result, when I first implemented `cppimport`, other packages (e.g. `scipy`) suddenly started breaking because import statements internal to those packages were importing C or C++ files instead of the modules they were intended to import. To avoid this failure mode, the import hook uses an "opt in" system where C and C++ files can specify they are meant to be used with cppimport by having a comment on the first line that includes the text "cppimport". 

As an alternative to the import hook, you can use `imp` or `imp_from_filepath`. The `cppimport.imp` and `cppimport.imp_from_filepath` performs exactly the same operation as the import hook but in a slightly more explicit way:
```
foobar = cppimport.imp("foobar")
foobar = cppimport.imp_from_filepath("src/foobar.cpp")
```
By default, these explicit function do not require the "cppimport" keyword on the first line of the C++ source file. 

### Windows?
The CI system does not run on Windows. A PR would be welcome adding further Windows support. I've used `cppimport` with MinGW-w64 and Python 3.6 and had good success. I've also had reports that `cppimport` works on Windows with Python 3.6 and Visual C++ 2015 Build Tools. The main challenge is making sure that distutils is aware of your available compilers. Try out the suggestion [here](https://stackoverflow.com/questions/3297254/how-to-use-mingws-gcc-compiler-when-installing-python-package-using-pip).

## cppimport uses the MIT License
