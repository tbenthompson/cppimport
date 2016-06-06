import os
import sys
import sysconfig

import cppimport.config
import cppimport.checksum
import cppimport.find

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

def should_rebuild(module_data):
    return (not os.path.exists(module_data['ext_path']) or
            cppimport.config.should_force_rebuild or
            not cppimport.checksum.is_checksum_current(module_data))

def imp(fullname):
    # Search through sys.path to find a file that matches the module
    filepath = cppimport.find.find_module_cpppath(fullname)

    if filepath is None or not os.path.exists(filepath):
        raise ImportError(
            "Couldn't find a file matching the module name " + str(fullname)
        )

    module_data = setup_module_data(fullname, filepath)
    quiet_print = cppimport.config.quiet_print
    if should_rebuild(module_data):
        # Don't import until here to reduce startup time.
        import cppimport.templating as templating
        import cppimport.build_module as build_module
        quiet_print("Compiling " + filepath)
        templating.run_templating(module_data)
        build_module.build_module(module_data)
        cppimport.checksum.checksum_save(module_data)
    else:
        quiet_print("Matching checksum for " + filepath + " --> not compiling")
    return __import__(fullname)
