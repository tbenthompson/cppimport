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
