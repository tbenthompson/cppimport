# Contributing 

When contributing to this repository, feel free to add an issue or pull request! There really aren't any rules, but if you're mean, I'll be sad. I'm happy to collaborate on pull requests if you would like. There's no need to submit a perfect, finished product.

To install in development mode and run the tests:
```
git clone git@github.com:tbenthompson/cppimport.git 
cd cppimport
conda env create
conda activate cppimport
pre-commit install
pip install --no-use-pep517 --disable-pip-version-check -e .
pytests
```

# Architecture

## Entrypoints:

The main entrypoint for cppimport is the `cppimport.import_hook` module, which interfaces with the Python importing system to allow things like `import mycppfilename`. For a C++ file to be a valid import target, it needs to have the word `cppimport` in its first line. Without this first line constraint, it is possible for the importing system to cause imports in other Python packages to fail. Before adding the first-line constraint, the cppimport import_hook had the unfortunate consequence of breaking some scipy modules that had adjacent C and C++ files in the directory tree.

There is an alternative, and more explicit interface provided by the `imp`, `imp_from_filepath` and `build` functions here.
* `imp` does exactly what the import hook does except via a function so that instead of `import foomodule` we would do `foomodule = imp('foomodule')`.
* `imp_from_filepath` is even more explicit, allowing the user to pass a C++ filepath rather than a modulename. For example, `foomodule = imp('../cppcodedir/foodmodule.cpp')`. This is rarely necessary but can be handy for debugging.
* `build` is similar to `imp` except that the library is only built and not actually loaded as a Python module.

`imp`, `imp_from_filepath` and `build` are in the `__init__.py` to separate external facing API from the guts of the package that live in internal submodules. 

## What happens when we import a C++ module.

1. First the `cppimport.find.find_module_cpppath` function is used to find a C++ file that matches the desired module name.
2. Next, we determine if there's already an existing compiled extension that we can use. If there is, the `cppimport.importer.is_build_needed` function is used to determine if the extension is up to date with the current code. If the extension is up to date, we attempt to load it. If the extension is loaded successfully, we return the module and we're done! However, if for whichever reason, we can't load an existing extension, we need to build the extension, a process directed by `cppimport.importer.template_and_build`.
3. The first step of building is to run the C++ file through the Mako templating system with the `cppimport.templating.run_templating` function. The main purpose of this is to allow users to embed configuration information into their C++ file. Without some sort of similar mechanism, there would be no way of passing information to build system because the `import modulename` statement can't carry information. The templating serves a secondary benefit in that simple code generation can be performed if needed. However, most users probably stick to a simple header or footer similar to the one demonstrated in the README. 
4. Next, we use setuptools to build the C++ extension using `cppimport.build_module.build_module`. This function calls setuptools with the appropriate arguments to build the extension in place next to the C++ file in the directory tree.
5. Next, we call `cppimport.checksum.checksum_save` to add a hash of the appended contents of all relevant source and header files. This checksum is appended to the end of the `.so` or `.dylib` file. This seems legal according to specifications and, in practice, causes no problems.
6. Finally, the compiled and loaded extension module is returned to the user.

## Useful links

* PEP 302 that made this possible: https://www.python.org/dev/peps/pep-0302/ 
* The gory details of Python importing: https://docs.python.org/3/reference/import.html
