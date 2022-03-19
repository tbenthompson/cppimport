import importlib
import logging
import os
import sys
import sysconfig

import cppimport
from cppimport.build_module import build_module
from cppimport.checksum import checksum_save, is_checksum_valid
from cppimport.templating import run_templating

logger = logging.getLogger(__name__)


def template_and_build(filepath, module_data):
    logger.debug(f"Compiling {filepath}.")
    run_templating(module_data)
    build_module(module_data)
    checksum_save(module_data)


def setup_module_data(fullname, filepath):
    module_data = dict()
    module_data["fullname"] = fullname
    module_data["filepath"] = filepath
    module_data["filedirname"] = os.path.dirname(module_data["filepath"])
    module_data["filebasename"] = os.path.basename(module_data["filepath"])
    module_data["ext_name"] = get_module_name(fullname) + get_extension_suffix()
    module_data["ext_path"] = os.path.join(
        os.path.dirname(filepath), module_data["ext_name"]
    )
    return module_data


def get_module_name(full_module_name):
    return full_module_name.split(".")[-1]


def get_extension_suffix():
    ext_suffix = sysconfig.get_config_var("EXT_SUFFIX")
    if ext_suffix is None:
        ext_suffix = sysconfig.get_config_var("SO")
    return ext_suffix


def _actually_load_module(module_data):
    module_data["module"] = importlib.import_module(module_data["fullname"])


def load_module(module_data):
    if hasattr(sys, "getdlopenflags"):
        # It can be useful to set rtld_flags to RTLD_GLOBAL. This allows
        # extensions that are loaded later to share the symbols from this
        # extension. This is primarily useful in a project where several
        # interdependent extensions are loaded but it's undesirable to combine
        # the multiple extensions into a single extension.
        old_flags = sys.getdlopenflags()
        new_flags = old_flags | cppimport.settings["rtld_flags"]
        sys.setdlopenflags(new_flags)
        _actually_load_module(module_data)
        sys.setdlopenflags(old_flags)
    else:
        _actually_load_module(module_data)


def is_build_needed(module_data):
    if cppimport.settings["force_rebuild"]:
        return True
    if cppimport.settings["release_mode"]:
        logger.debug(
            f"Release mode is enabled. Thus, file {module_data['filepath']} is "
            f"not being compiled."
        )
        return False
    if not is_checksum_valid(module_data):
        return True
    logger.debug(f"Matching checksum for {module_data['filepath']} --> not compiling")
    return False


def try_load(module_data):
    try:
        load_module(module_data)
        return True
    except ImportError as e:
        logger.info(
            f"ImportError during import with matching checksum: {e}. Trying to rebuild."
        )
        return False
