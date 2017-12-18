import os
import sys

import cppimport.config

def check_contains_cppimport(filepath):
    with open(filepath, 'r') as f:
        return 'cppimport' in f.readline()

def find_file_in_folders(filename, paths, opt_in):
    for d in paths:
        if not os.path.exists(d):
            continue

        if os.path.isfile(d):
            continue

        for f in os.listdir(d):
            if f != filename:
                continue
            filepath = os.path.join(d, f)
            if opt_in and not check_contains_cppimport(filepath):
                continue
            return filepath
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

def _find_module_cpppath(modulename, opt_in = False):
    modulepath_without_ext = modulename.replace('.', os.sep)
    moduledir = os.path.dirname(modulepath_without_ext + '.throwaway')
    matching_dirs = find_matching_path_dirs(moduledir)
    matching_dirs = [os.getcwd() if d == '' else d for d in matching_dirs]
    matching_dirs = [
        d if os.path.isabs(d) else os.path.join(os.getcwd(), d) for d in matching_dirs
    ]

    for ext in cppimport.config.file_exts:
        modulefilename = os.path.basename(modulepath_without_ext + ext)
        outfilename = find_file_in_folders(modulefilename, matching_dirs, opt_in)
        if outfilename is not None:
            return outfilename

    return None

def find_module_cpppath(modulename, opt_in = False):
    filepath = _find_module_cpppath(modulename, opt_in)
    if filepath is None:
        raise ImportError(
            'Couldn\'t find a file matching the module name: ' +
            str(modulename) +
            '  (note: opt_in = ' + str(opt_in) + ')'
        )
    return filepath
