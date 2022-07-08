import hashlib
import json
import logging
import struct

from cppimport.filepaths import make_absolute

_TAG = b"cppimport"
_FMT = struct.Struct("q" + str(len(_TAG)) + "s")

logger = logging.getLogger(__name__)


def is_checksum_valid(module_data):
    """
    Load the saved checksum from the extension file check if it matches the
    checksum computed from current source files.
    """
    deps, old_checksum = _load_checksum_trailer(module_data)
    if old_checksum is None:
        return False  # Already logged error in load_checksum_trailer.
    try:
        return old_checksum == _calc_cur_checksum(deps, module_data)
    except OSError as e:
        logger.info(
            "Checksummed file not found while checking cppimport checksum "
            "(%s); rebuilding." % e
        )
        return False


def _load_checksum_trailer(module_data):
    try:
        with open(module_data["ext_path"], "rb") as f:
            f.seek(-_FMT.size, 2)
            json_len, tag = _FMT.unpack(f.read(_FMT.size))
            if tag != _TAG:
                logger.info(
                    "The extension is missing the trailer tag and thus is missing"
                    " its checksum; rebuilding."
                )
                return None, None
            f.seek(-(_FMT.size + json_len), 2)
            json_s = f.read(json_len)
    except FileNotFoundError:
        logger.info("Failed to find compiled extension; rebuilding.")
        return None, None
    except OSError:
        logger.info("Checksum trailer invalid. Rebuilding.")
        return None, None

    try:
        deps, old_checksum = json.loads(json_s)
    except ValueError:
        logger.info(
            "Failed to load checksum trailer info from already existing "
            "compiled extension; rebuilding."
        )
        return None, None
    return deps, old_checksum


def checksum_save(module_data):
    """
    Calculate the module checksum and then write it to the end of the shared
    object.
    """
    dep_filepaths = (
        [
            make_absolute(module_data["filedirname"], d)
            for d in module_data["cfg"].get("dependencies", [])
        ]
        + module_data["extra_source_filepaths"]
        + [module_data["filepath"]]
    )
    cur_checksum = _calc_cur_checksum(dep_filepaths, module_data)
    _save_checksum_trailer(module_data, dep_filepaths, cur_checksum)


def _save_checksum_trailer(module_data, dep_filepaths, cur_checksum):
    # We can just append the checksum to the shared object; this is effectively
    # legal (see e.g. https://stackoverflow.com/questions/10106447).
    dump = json.dumps([dep_filepaths, cur_checksum]).encode("ascii")
    dump += _FMT.pack(len(dump), _TAG)
    with open(module_data["ext_path"], "ab", buffering=0) as file:
        file.write(dump)


def _calc_cur_checksum(file_lst, module_data):
    text = b""
    for filepath in file_lst:
        with open(filepath, "rb") as f:
            text += f.read()
    return hashlib.md5(text).hexdigest()
