import os
import re
import sys
import shutil
import tempfile
import sysconfig
import distutils.file_util
import traceback
import contextlib
import hashlib

import cppimport.config
from cppimport.config import quiet_print
import cppimport.build_module

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

# I use .${filename}.cppimporthash as the checksum file for each module.
def get_checksum_filepath(filepath):
    return os.path.join(
        os.path.dirname(filepath),
        '.' + os.path.basename(filepath) + '.cppimporthash'
    )

def calc_cur_checksum(*file_lst):
    text = b""
    for filepath in file_lst:
        text += open(filepath, 'r').read().encode('utf-8')
    return hashlib.md5(text).hexdigest()

# Use a checksum to see if the file has been changed since the last compilation
def checksum_match(filepath, deps):
    checksum_filepath = get_checksum_filepath(filepath)

    cur_checksum = calc_cur_checksum(filepath, *deps)

    if os.path.exists(checksum_filepath):
        saved_checksum = open(checksum_filepath, 'r').read()
        if saved_checksum == cur_checksum:
            return True, (checksum_filepath, cur_checksum)
    return False, (checksum_filepath, cur_checksum)

def get_module_name(full_module_name):
    return full_module_name.split('.')[-1]

def get_user_include_dirs(filepath):
    return [
        os.path.dirname(filepath)
    ]

def get_extension_suffix():
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
    if ext_suffix is None:
        ext_suffix = sysconfig.get_config_var('SO')
    return ext_suffix

def delete_existing_extension(ext_path):
    try:
        os.remove(ext_path)
    except OSError:
        pass

def if_bad_checksum_build(full_module_name, filepath):
    ext_name = get_module_name(full_module_name) + get_extension_suffix()
    ext_path = os.path.join(os.path.dirname(filepath), ext_name)
    #TODO:
    deps = []
    checksum_good, checksum_save = checksum_match(filepath, deps)

    use_existing_extension = not cppimport.config.should_force_rebuild and \
        checksum_good and \
        os.path.exists(ext_path)

    if use_existing_extension:
        quiet_print("Matching checksum for " + filepath + " --> not compiling")
    else:
        quiet_print("Compiling " + filepath)
        delete_existing_extension(ext_path)
        cppimport.build_module.build_module(full_module_name, filepath)
        open(checksum_save[0], 'w').write(checksum_save[1])

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

def imp(fullname):
    # Search through sys.path to find a C++ file that matches the module
    filepath = find_module_cpppath(fullname)

    if filepath is None or not os.path.exists(filepath):
        raise ImportError(
            "Couldn't find a file matching the module name " + str(fullname)
        )

    if_bad_checksum_build(fullname, filepath)
    return __import__(fullname)
