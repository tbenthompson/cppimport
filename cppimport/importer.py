import os
import sys
import sysconfig

import cppimport.config
import cppimport.build_module
import cppimport.checksum
import cppimport.templating
import cppimport.find

def get_module_name(full_module_name):
    return full_module_name.split('.')[-1]

def get_extension_suffix():
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
    if ext_suffix is None:
        ext_suffix = sysconfig.get_config_var('SO')
    return ext_suffix

def setup_module_data(fullname, filepath, rendered_src_filepath, cfg):
    module_data = dict()
    module_data['fullname'] = fullname
    module_data['filepath'] = filepath
    module_data['filedirname'] = os.path.dirname(module_data['filepath'])
    module_data['filebasename'] = os.path.basename(module_data['filepath'])
    module_data['ext_name'] = get_module_name(fullname) + get_extension_suffix()
    module_data['ext_path'] = os.path.join(
        os.path.dirname(filepath), module_data['ext_name']
    )
    module_data['rendered_src_filepath'] = rendered_src_filepath
    module_data['dependency_dirs'] = (
        cfg.get('include_dirs', []) + [module_data['filedirname']]
    )
    module_data['cfg'] = cfg
    return module_data

def should_rebuild(module_data):
    checksum_good, checksum = cppimport.checksum.checksum(module_data)

    if (not os.path.exists(module_data['ext_path']) or
            not checksum_good or
            cppimport.config.should_force_rebuild):
        return True, checksum

    return False, checksum

def imp(fullname):
    # Search through sys.path to find a file that matches the module
    filepath = cppimport.find.find_module_cpppath(fullname)

    if filepath is None or not os.path.exists(filepath):
        raise ImportError(
            "Couldn't find a file matching the module name " + str(fullname)
        )

    rendered_src_filepath, cfg = cppimport.templating.run_templating(filepath)
    module_data = setup_module_data(fullname, filepath, rendered_src_filepath, cfg)

    quiet_print = cppimport.config.quiet_print
    shd_rbld, checksum = should_rebuild(module_data)
    if shd_rbld:
        quiet_print("Compiling " + filepath)
        cppimport.build_module.build_module(module_data)
        cppimport.checksum.checksum_save(module_data['filepath'], checksum)
    else:
        quiet_print("Matching checksum for " + filepath + " --> not compiling")
    return __import__(fullname)
