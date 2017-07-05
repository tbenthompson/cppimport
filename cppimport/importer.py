import os
import sys
import sysconfig

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

def should_rebuild(module_data):
    module_path = cppimport.find.find_module_path(module_data['fullname'], module_data['filedirname'])
    return (not module_path or
            not os.path.exists(module_path) or
            cppimport.config.should_force_rebuild or
            not cppimport.checksum.is_checksum_current(module_data))

def template_and_build(filepath, module_data):
    # Don't import until here to reduce startup time.
    import cppimport.templating as templating
    import cppimport.build_module as build_module
    quiet_print("Compiling " + filepath)
    templating.run_templating(module_data)
    build_module.build_module(module_data)
    cppimport.checksum.checksum_save(module_data)

def imp_from_filepath(filepath, fullname = None):
    if fullname is None:
        fullname = os.path.splitext(os.path.basename(filepath))[0]
    module_data = setup_module_data(fullname, filepath)
    if should_rebuild(module_data):
        template_and_build(filepath, module_data)
        return __import__(fullname)
    else:
        quiet_print("Matching checksum for " + filepath + " --> not compiling")
        try:
            return __import__(fullname)
        except ImportError as e:
            quiet_print(
                "ImportError during import with matching checksum. Trying to rebuild.")
            template_and_build(filepath, module_data)
            return __import__(fullname)

def imp(fullname):
    # Search through sys.path to find a file that matches the module
    filepath = cppimport.find.find_module_cpppath(fullname)
    if filepath is None or not os.path.exists(filepath):
        raise ImportError(
            "Couldn't find a file matching the module name " + str(fullname)
        )
    return imp_from_filepath(filepath, fullname)

def cppimport_impl(fullname):
    # Search through sys.path to find a file that matches the module
    out_module = imp(fullname)
    sub_module_names = fullname.split('.')[1:]
    for sub_name in sub_module_names:
        out_module = getattr(out_module, sub_name)
    return out_module
