import os
import sys
import sysconfig
import importlib

import cppimport.config
import cppimport.checksum
import cppimport.find

quiet_print = cppimport.config.quiet_print

def get_module_name(full_module_name):
    return full_module_name.split('.')[-1]

def get_extension_suffix():
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
    if ext_suffix is None:
        ext_suffix = sysconfig.get_config_var('SO')
    return ext_suffix

def setup_module_data(fullname, filepath):
    module_data = dict()
    module_data['fullname'] = fullname
    module_data['filepath'] = filepath
    module_data['filedirname'] = os.path.dirname(module_data['filepath'])
    module_data['filebasename'] = os.path.basename(module_data['filepath'])
    module_data['ext_name'] = get_module_name(fullname) + get_extension_suffix()
    module_data['ext_path'] = os.path.join(
        os.path.dirname(filepath), module_data['ext_name']
    )
    return module_data

def _load_module(module_data):
    module_data['module'] = importlib.import_module(module_data['fullname'])

def load_module(module_data):
    if hasattr(sys, 'getdlopenflags'):
        old_flags = sys.getdlopenflags()
        new_flags = old_flags | cppimport.config.rtld_flags
        sys.setdlopenflags(new_flags)
        _load_module(module_data)
        sys.setdlopenflags(old_flags)
    else:
        _load_module(module_data)

def check_checksum(module_data):
    if cppimport.config.should_force_rebuild:
        return False
    if not cppimport.checksum.is_checksum_current(module_data):
        return False
    quiet_print("Matching checksum for " + module_data['filepath'] + " --> not compiling")
    return True

def try_load(module_data):
    try:
        load_module(module_data)
        return True
    except ImportError:
        quiet_print(
            "ImportError during import with matching checksum. Trying to rebuild.")
        return False

def template_and_build(filepath, module_data):
    # Don't import until here to reduce startup time.
    import cppimport.templating as templating
    import cppimport.build_module as build_module
    quiet_print("Compiling " + filepath)
    templating.run_templating(module_data)
    build_module.build_module(module_data)
    if cppimport.config.quiet:
        os.remove(module_data["rendered_src_filepath"])
    cppimport.checksum.checksum_save(module_data)

def imp_from_filepath(filepath, fullname = None):
    if fullname is None:
        fullname = os.path.splitext(os.path.basename(filepath))[0]
    module_data = setup_module_data(fullname, filepath)
    if not check_checksum(module_data) or not try_load(module_data):
        template_and_build(filepath, module_data)
        load_module(module_data)
    return module_data['module']

def imp(fullname, opt_in = False):
    # Search through sys.path to find a file that matches the module
    filepath = cppimport.find.find_module_cpppath(fullname, opt_in)
    return imp_from_filepath(filepath, fullname)

def build(fullname):
    # Search through sys.path to find a file that matches the module
    filepath = cppimport.find.find_module_cpppath(fullname)
    module_data = setup_module_data(fullname, filepath)
    if not check_checksum(module_data):
        template_and_build(filepath, module_data)

    # Return the path to the built module
    return module_data['ext_path']
