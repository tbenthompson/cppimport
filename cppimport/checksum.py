import os
import pickle
import hashlib
import traceback

import cppimport.find
import cppimport.config
from cppimport.filepaths import make_absolute

# I use .${filename}.cppimporthash as the checksum file for each module.
def get_checksum_filepath(filepath):
    return os.path.join(
        os.path.dirname(filepath),
        '.' + os.path.basename(filepath) + '.cppimporthash'
    )

def calc_cur_checksum(file_lst, module_data):
    text = b""
    for filepath in file_lst:
        text += open(filepath, 'rb').read()
    return hashlib.md5(text).hexdigest()

# Use a checksum to see if the file has been changed since the last compilation
def is_checksum_current(module_data):
    try:
        checksum_filepath = get_checksum_filepath(module_data['filepath'])

        if not os.path.exists(checksum_filepath):
            return False

        try:
            with open(checksum_filepath, 'rb') as f:
                deps, old_checksum = pickle.load(f)
        except (ValueError, pickle.UnpicklingError) as e:
            cppimport.config.quiet_print(
                "Failed to load checksum due to exception" + traceback.format_exc()
            )
            return False

        cur_checksum = calc_cur_checksum(deps, module_data)
        if old_checksum != cur_checksum:
            return False
        return True
    except FileNotFoundError as e:
        print(e)
        print("Checksummed file not found while checking cppimport checksum. Rebuilding.")
        return False

def checksum_save(module_data):
    checksum_filepath = get_checksum_filepath(module_data['filepath'])

    dep_filepaths = (
        [
            make_absolute(module_data['filedirname'], d)
            for d in module_data['cfg'].get('dependencies', [])
        ] +
        module_data['extra_source_filepaths'] +
        [module_data['filepath']]
    )

    cur_checksum = calc_cur_checksum(dep_filepaths, module_data)
    pickle.dump((dep_filepaths, cur_checksum), open(checksum_filepath, 'wb'))
