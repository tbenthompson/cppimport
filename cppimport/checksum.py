import os
import pickle
import hashlib

import cppimport.find

# I use .${filename}.cppimporthash as the checksum file for each module.
def get_checksum_filepath(filepath):
    return os.path.join(
        os.path.dirname(filepath),
        '.' + os.path.basename(filepath) + '.cppimporthash'
    )

def calc_cur_checksum(file_lst, module_data):
    text = b""
    for filepath in file_lst:
        text += open(filepath, 'r').read().encode('utf-8')
    return hashlib.md5(text).hexdigest()

# Use a checksum to see if the file has been changed since the last compilation
def is_checksum_current(module_data):
    checksum_filepath = get_checksum_filepath(module_data['filepath'])

    if not os.path.exists(checksum_filepath):
        return False

    deps, old_checksum = pickle.load(open(checksum_filepath, 'rb'))
    cur_checksum = calc_cur_checksum(deps, module_data)
    if old_checksum != cur_checksum:
        return False
    return True

def checksum_save(module_data):
    checksum_filepath = get_checksum_filepath(module_data['filepath'])

    dependency_dirs = (
        module_data['cfg'].get('include_dirs', []) + [module_data['filedirname']]
    )
    dep_filepaths = [
        cppimport.find.find_file_in_folders(d, dependency_dirs)
        for d in module_data['cfg'].get('dependencies', [])
    ] + [module_data['filepath']]

    cur_checksum = calc_cur_checksum(dep_filepaths, module_data)
    pickle.dump((dep_filepaths, cur_checksum), open(checksum_filepath, 'wb'))
