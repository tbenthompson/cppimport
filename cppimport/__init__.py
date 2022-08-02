"""
See CONTRIBUTING.md for a description of the project structure and the internal logic.
"""
import ctypes
import logging
import os

from cppimport.find import _check_first_line_contains_cppimport

try:
    from ._version import version as __version__
    from ._version import version_tuple
except ImportError:
    __version__ = "unknown version"
    version_tuple = (0, 0, "unknown version")

settings = dict(
    force_rebuild=False,  # `force_rebuild` with multiple processes is not supported
    file_exts=[".cpp", ".c"],
    rtld_flags=ctypes.RTLD_LOCAL,
    lock_suffix=".lock",
    lock_timeout=10 * 60,
    remove_strict_prototypes=True,
    release_mode=os.getenv("CPPIMPORT_RELEASE_MODE", "0").lower()
    in ("true", "yes", "1"),
)
_logger = logging.getLogger("cppimport")


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
        build_safely,
        is_build_needed,
        load_module,
        setup_module_data,
        try_load,
    )

    filepath = os.path.abspath(filepath)
    if fullname is None:
        fullname = os.path.splitext(os.path.basename(filepath))[0]
    module_data = setup_module_data(fullname, filepath)
    # The call to try_load is necessary here because there are times when the
    # only evidence a rebuild is needed comes from attempting to load an
    # existing extension module. For example, if the extension was built on a
    # different architecture or with different Python headers and will produce
    # an error when loaded, then the load will fail. In that situation, we will
    # need to rebuild.
    if is_build_needed(module_data) or not try_load(module_data):
        build_safely(filepath, module_data)
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

    # Search through sys.path to find a file that matches the module
    filepath = find_module_cpppath(fullname)
    return build_filepath(filepath, fullname=fullname)


def build_filepath(filepath, fullname=None):
    """
    `build_filepath` builds a extension module like `build` but allows
    to directly specify a file path.

    Parameters
    ----------
    filepath : the filepath to the C++ file to build.
    fullname : the name of the module to build.

    Returns
    -------
    ext_path : the path to the compiled extension.
    """
    from cppimport.importer import (
        build_safely,
        is_build_needed,
        load_module,
        setup_module_data,
    )

    filepath = os.path.abspath(filepath)
    if fullname is None:
        fullname = os.path.splitext(os.path.basename(filepath))[0]
    module_data = setup_module_data(fullname, filepath)
    if is_build_needed(module_data):
        build_safely(filepath, module_data)
    load_module(module_data)
    # Return the path to the built module
    return module_data["ext_path"]


def build_all(root_directory):
    """
    `build_all` builds a extension module like `build` for each eligible (that is,
    containing the "cppimport" header) source file within the given `root_directory`.

    Parameters
    ----------
    root_directory : the root directory to search for cpp source files in.
    """
    for directory, _, files in os.walk(root_directory):
        for file in files:
            if (
                not file.startswith(".")
                and os.path.splitext(file)[1] in settings["file_exts"]
            ):
                full_path = os.path.join(directory, file)
                if _check_first_line_contains_cppimport(full_path):
                    _logger.info(f"Building: {full_path}")
                    build_filepath(full_path)


######## BACKWARDS COMPATIBILITY #########
# Below here, we pay penance for mistakes.
# TODO: Add DeprecationWarning

"""
For backwards compatibility, support this alias for the imp function
"""
cppimport = imp


def force_rebuild(to=True):
    settings["force_rebuild"] = to


def turn_off_strict_prototypes():
    pass  # turned off by default.


def set_rtld_flags(flags):
    settings["rtld_flags"] = flags
