import json
import hashlib
import struct

import cppimport.find
import cppimport.config
from cppimport.filepaths import make_absolute


_TAG = b'cppimport'
_FMT = struct.Struct('q' + str(len(_TAG)) + 's')

def calc_cur_checksum(file_lst, module_data):
    text = b""
    for filepath in file_lst:
        try:
            with open(filepath, 'rb') as f:
                text += f.read()
        except OSError as e:
            cppimport.config.quiet_print(
                "Checksummed file not found while checking cppimport checksum "
                "(%s); rebuilding." % e)
            return None
    return hashlib.md5(text).hexdigest()

def load_checksum_trailer(module_data):
    try:
        with open(module_data['ext_path'], 'rb') as f:
            f.seek(-_FMT.size, 2)
            json_len, tag = _FMT.unpack(f.read(_FMT.size))
            if tag != _TAG:
                cppimport.config.quiet_print("Missing trailer tag")
                return None, None
            f.seek(-(_FMT.size + json_len), 2)
            json_s = f.read(json_len)
    except FileNotFoundError:
        cppimport.config.quiet_print("Failed to find compiled extension; rebuilding.")
        return None, None

    try:
        deps, old_checksum = json.loads(json_s)
    except ValueError:
        cppimport.config.quiet_print(
            "Failed to load checksum trailer info from already existing "
            "compiled extension; rebuilding.")
        return None, None
    return deps, old_checksum

# Use a checksum to see if the file has been changed since the last compilation
def is_checksum_current(module_data):
    deps, old_checksum = load_checksum_trailer(module_data)
    if old_checksum is None:
        return False  # Already logged error in load_checksum_trailer.
    return old_checksum == calc_cur_checksum(deps, module_data)

def save_checksum_trailer(module_data, dep_filepaths, cur_checksum):
    # We can just append the checksum to the shared object; this is effectively
    # legal (see e.g. https://stackoverflow.com/questions/10106447).
    dump = json.dumps([dep_filepaths, cur_checksum]).encode('ascii')
    dump += _FMT.pack(len(dump), _TAG)
    with open(module_data['ext_path'], 'ab') as file:
        file.write(dump)

def checksum_save(module_data):
    dep_filepaths = (
        [
            make_absolute(module_data['filedirname'], d)
            for d in module_data['cfg'].get('dependencies', [])
        ] +
        module_data['extra_source_filepaths'] +
        [module_data['filepath']]
    )
    cur_checksum = calc_cur_checksum(dep_filepaths, module_data)
    save_checksum_trailer(module_data, dep_filepaths, cur_checksum)
