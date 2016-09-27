import os
import sys

import cppimport.config

def find_file_in_folders(filename, paths):
    for d in paths:
        if not os.path.exists(d):
            continue

        if os.path.isfile(d):
            continue

        for f in os.listdir(d):
            if f == filename:
                return os.path.join(d, f)
    return None

def find_matching_path_dirs(moduledir):
    if moduledir is '':
        return sys.path

    ds = []
    for dir in sys.path:
        test_path = os.path.join(dir, moduledir)
        if os.path.exists(test_path) and os.path.isdir(test_path):
            ds.append(test_path)
    return ds

def find_module_cpppath(modulename):
    modulepath_without_ext = modulename.replace('.', os.sep)
    moduledir = os.path.dirname(modulepath_without_ext + '.throwaway')
    matching_dirs = find_matching_path_dirs(moduledir)
    matching_dirs = [os.getcwd() if d == '' else d for d in matching_dirs]

    for ext in cppimport.config.file_exts:
        modulefilename = os.path.basename(modulepath_without_ext + ext)
        outfilename = find_file_in_folders(modulefilename, matching_dirs)
        if outfilename is not None:
            return outfilename

    return None


def find_module_path(module_name: str, search_path: str = None) -> str:
    """
    Find the module path (pyd / so), while accounting for platform/arch naming
    :param module_name: The name of the module
    :param search_path: The path to search in. If None, searches system path.
    :return: The full path to the library or None if not found.
    """

    # Use importlib if python 3.4+, else imp
    if sys.version_info[0] > 3 or (sys.version_info[0] == 3 and sys.version_info[1] >= 4):

        from importlib.machinery import FileFinder, ExtensionFileLoader, EXTENSION_SUFFIXES
        file_finder = FileFinder(search_path, (ExtensionFileLoader, EXTENSION_SUFFIXES))

        # The search caches must be cleared to guaranteed find dynamically created modules
        file_finder.invalidate_caches()
        result = file_finder.find_spec(module_name)
        return None if not result else result.origin
    else:
        from imp import find_module  # Deprecated in 3.4
        try:
            result = find_module(module_name, [search_path])
        except ImportError:
            result = None

        return None if not result else result[1]
