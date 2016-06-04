import os
import hashlib

import cppimport.find

# I use .${filename}.cppimporthash as the checksum file for each module.
def get_checksum_filepath(filepath):
    return os.path.join(
        os.path.dirname(filepath),
        '.' + os.path.basename(filepath) + '.cppimporthash'
    )

def calc_cur_checksum(file_lst):
    text = b""
    for filepath in file_lst:
        text += open(filepath, 'r').read().encode('utf-8')
    return hashlib.md5(text).hexdigest()

# Use a checksum to see if the file has been changed since the last compilation
def checksum(filepath, deps, dependency_dirs):
    checksum_filepath = get_checksum_filepath(filepath)

    dep_filepaths = [
        cppimport.find.find_file_in_folders(d, dependency_dirs)
        for d in deps
    ] + [filepath]
    cur_checksum = calc_cur_checksum(dep_filepaths)

    if os.path.exists(checksum_filepath):
        saved_checksum = open(checksum_filepath, 'r').read()
        if saved_checksum == cur_checksum:
            return True, (checksum_filepath, cur_checksum)
    return False, (checksum_filepath, cur_checksum)
