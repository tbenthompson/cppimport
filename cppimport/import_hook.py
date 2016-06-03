import sys
import os
import shutil
import string
import tempfile
import sysconfig
import distutils.file_util
import traceback
import contextlib
import hashlib
import re
import json

import setuptools
import setuptools.command.build_ext
import pybind11

if sys.version_info[0] == 2:
    import StringIO as io
else:
    import io

def merge(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        elif isinstance(value, list):
            destination.setdefault(key, [])
            destination[key] += value
        else:
            destination[key] = value

    return destination

@contextlib.contextmanager
def stdchannel_redirected(stdchannel):
    """
    Redirects stdout or stderr to a StringIO object. As of python 3.4, there is a
    standard library contextmanager for this, but backwards compatibility!
    """
    try:
        s = io.StringIO()
        old = getattr(sys, stdchannel)
        setattr(sys, stdchannel, s)
        yield s
    finally:
        setattr(sys, stdchannel, old)

quiet = True
should_force_rebuild = False

def set_quiet(to):
    global quiet
    quiet = to

def force_rebuild():
    global should_force_rebuild
    should_force_rebuild = True


# Subsitute in the module code and module name into a bare bones
# pybind11 plugin
def setup_plugin(module_name, filepath, tempdir):
    with open(filepath, 'r') as f:
        code = f.read()

    build = {}
    m = re.search('^//cppimport (.+)', code)
    if m:
        build = json.loads(m.group(1))

    tmpl_args = dict()
    tmpl_args['code'] = code
    tmpl_args['module_name'] = module_name

    template = """
    $code

    PYBIND11_PLUGIN($module_name) {
        pybind11::module m("$module_name", "auto-compiled c++ extension");
        pyexport(m);
        return m.ptr();
    }
    """
    plugin_code = string.Template(template).substitute(**tmpl_args)

    temp_filename = os.path.join(tempdir, module_name + '.cpp')
    with open(temp_filename, 'w') as f_tmp:
        f_tmp.write(plugin_code)

    return [build, temp_filename]

# I use .${filename}.cppimporthash as the checksum file for each module.
def get_checksum_filepath(filepath):
    return os.path.join(
        os.path.dirname(filepath),
        '.' + os.path.basename(filepath) + '.cppimporthash'
    )

# Use a checksum to see if the file has been changed since the last compilation
def checksum_match(filepath):
    checksum_filepath = get_checksum_filepath(filepath)
    cur_checksum = hashlib.md5(
        open(filepath, 'r').read().encode('utf-8')
    ).hexdigest()
    if os.path.exists(checksum_filepath):
        saved_checksum = open(checksum_filepath, 'r').read()
        if saved_checksum == cur_checksum:
            return True, (checksum_filepath, cur_checksum)
    return False, (checksum_filepath, cur_checksum)

# Subclass setuptools Extension to add a parameter specifying where the shared
# library should be placed after being compiled
class ImportCppExt(setuptools.Extension):
    def __init__(self, libdest, *args, **kwargs):
        self.libdest = libdest
        setuptools.Extension.__init__(self, *args, **kwargs)

# Subclass setuptools build_ext to put the compiled shared library in the
# appropriate place in the source tree.
class BuildImportCppExt(setuptools.command.build_ext.build_ext):
    def copy_extensions_to_source(self):
        for ext in self.extensions:
            fullname = self.get_ext_fullname(ext.name)
            filename = self.get_ext_filename(fullname)
            src_filename = os.path.join(self.build_lib, filename)
            dest_filename = os.path.join(ext.libdest, os.path.basename(filename))

            distutils.file_util.copy_file(
                src_filename, dest_filename,
                verbose = self.verbose, dry_run = self.dry_run
            )

# 1) Determine if the file has already been compiled into a shared lib by
# looking at a checksum.
# 2) build the plugin in a temporary directory while redirecting stdout.
# 3) The "--inplace" argument specifies that the file should be moved into the
# source tree, something handled by the BuildImportCppExt class
def build_plugin(full_module_name, filepath):
    build_path = tempfile.mkdtemp()
    module_name = full_module_name.split('.')[-1]
    dir_name = os.path.dirname(filepath)

    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
    if ext_suffix is None:
        ext_suffix = sysconfig.get_config_var('SO')

    ext_path = os.path.join(dir_name, module_name + ext_suffix)

    checksum_good, checksum_save = checksum_match(filepath)

    use_existing_extension = not should_force_rebuild and \
        checksum_good and \
        os.path.exists(ext_path)

    if use_existing_extension:
        if not quiet:
            print("Matching checksum for " + filepath + " --> not compiling")
        return

    if not quiet:
        print("Compiling " + filepath)

    [build, temp_filepath] = setup_plugin(module_name, filepath, build_path)

    params = {
        "sources": [temp_filepath],
        "language": 'c++',
        "include_dirs": [
            pybind11.get_include(),
            pybind11.get_include(True)
        ],
        "extra_compile_args": [
            '-std=c++11', '-Wall', '-Werror'
        ]
    }
    merge(build, params)
    ext = ImportCppExt(
        dir_name,
        full_module_name,
        **params
    )

    args = ['build_ext', '--inplace']
    args.append('--build-temp=' + build_path)
    args.append('--build-lib=' + build_path)

    if quiet:
        args.append('-q')
    else:
        args.append('-v')

    setuptools_args = dict(
        name = full_module_name,
        ext_modules = [ext],
        script_args = args,
        cmdclass = {
            'build_ext': BuildImportCppExt
        }
    )

    if quiet:
        with stdchannel_redirected("stdout"):
            with stdchannel_redirected("stderr"):
                setuptools.setup(**setuptools_args)
    else:
        setuptools.setup(**setuptools_args)

    shutil.rmtree(build_path)

    open(checksum_save[0], 'w').write(checksum_save[1])

def find_matching_path_dirs(moduledir):
    if moduledir is '':
        return sys.path

    ds = []
    for dir in sys.path:
        test_path = os.path.join(dir, moduledir)
        if os.path.exists(test_path):
            ds.append(test_path)
    return ds

def find_module_cpppath(modulename):
    ext = '.cpp'
    modulepath = modulename.replace('.', os.sep) + ext
    moduledir = os.path.dirname(modulepath)
    modulefilename = os.path.basename(modulepath)
    matching_path_dirs = find_matching_path_dirs(moduledir)
    for d in matching_path_dirs:
        if d == '':
            d = os.getcwd()

        if not os.path.exists(d):
            continue

        if os.path.isfile(d):
            continue

        for f in os.listdir(d):
            if f == modulefilename:
                return os.path.join(d, f)
    return None

class CppFinder(object):
    def __init__(self):
        pass

    def find_module(self, fullname, path = None):
        # Search through sys.path to find a C++ file that matches the module
        filepath = find_module_cpppath(fullname)

        if filepath is None or not os.path.exists(filepath):
            return

        try:
            build_plugin(fullname, filepath)
        except Exception as e:
            print(traceback.format_exc())

# Add the import hook.
sys.meta_path.insert(0, CppFinder())
