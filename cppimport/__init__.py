"""
See ARCHITECTURE.md for a description of the project structure and the internal logic.
"""
import os

from cppimport.config import (
    file_exts,
    force_rebuild,
    set_rtld_flags,
    turn_off_strict_prototypes,
)


def imp(fullname, opt_in=False):
    """
    `imp` is the explicit alternative to using cppimport.import_hook.

    Parameters
    ----------
    fullname : the name of the module to import.
    opt_in : should we require C++ files to opt in via adding "cppimport" to
             the first line of the file? This is on by default for the
             import hook, but is off by default for this function since the
             intent to import a C++ module is clearly specified.

    Returns
    -------
    module : the compiled and loaded Python extension module
    """
    from cppimport.find import find_module_cpppath

    # Search through sys.path to find a file that matches the module
    filepath = find_module_cpppath(fullname, opt_in)
    return imp_from_filepath(filepath, fullname)


def imp_from_filepath(filepath, fullname=None):
    """
    `imp_from_filepath` serves the same purpose as `imp` except allows
    specifying the exact filepath of the C++ file.

    Parameters
    ----------
    filepath : the filepath to the C++ file to build and import.
    fullname : the name of the module to import. This can be different from the
               module name inferred from the filepath if desired.

    Returns
    -------
    module : the compiled and loaded Python extension module
    """
    from cppimport.importer import (
        is_build_needed,
        load_module,
        setup_module_data,
        template_and_build,
        try_load,
    )

    if fullname is None:
        fullname = os.path.splitext(os.path.basename(filepath))[0]
    module_data = setup_module_data(fullname, filepath)
    if not is_build_needed(module_data) or not try_load(module_data):
        template_and_build(filepath, module_data)
        load_module(module_data)
    return module_data["module"]


def build(fullname):
    """
    `build` builds a extension module like `imp` but does not import the
    extension.

    Parameters
    ----------
    fullname : the name of the module to import.

    Returns
    -------
    ext_path : the path to the compiled extension.
    """
    from cppimport.find import find_module_cpppath
    from cppimport.importer import (
        is_build_needed,
        setup_module_data,
        template_and_build,
    )

    # Search through sys.path to find a file that matches the module
    filepath = find_module_cpppath(fullname)

    module_data = setup_module_data(fullname, filepath)
    if not is_build_needed(module_data):
        template_and_build(filepath, module_data)

    # Return the path to the built module
    return module_data["ext_path"]


"""
For backwards compatibility, support this alias for the imp function
"""
cppimport = imp
