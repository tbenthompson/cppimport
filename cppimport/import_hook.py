import os
import re
import sys
import shutil
import string
import tempfile
import sysconfig
import distutils.file_util
import traceback
import contextlib
import hashlib

import setuptools
import setuptools.command.build_ext
import pybind11

@contextlib.contextmanager
def stdchannel_redirected(stdchannel, dest_filename):
    """
    From:
    http://marc-abramowitz.com/archives/2013/07/19/python-context-manager-for-redirected-stdout-and-stderr/
    A context manager to temporarily redirect stdout or stderr

    e.g.:

    with stdchannel_redirected(sys.stderr, os.devnull):
        if compiler.has_function('clock_gettime', libraries=['rt']):
            libraries.append('rt')
    """
    try:
        oldstdchannel = os.dup(stdchannel.fileno())
        dest_file = open(dest_filename, 'w')
        os.dup2(dest_file.fileno(), stdchannel.fileno())

        yield
    finally:
        if oldstdchannel is not None:
            os.dup2(oldstdchannel, stdchannel.fileno())
        if dest_file is not None:
            dest_file.close()


quiet = True
should_force_rebuild = False

def set_quiet(to):
    global quiet
    quiet = to

def force_rebuild():
    global should_force_rebuild
    should_force_rebuild = True

def quiet_print(*args, **kwargs):
    global quiet
    if not quiet:
        print(*args, **kwargs)


# Subsitute in the module code and module name into a bare bones
# pybind11 plugin
def template_plugin(module_name, filepath, tempdir):
    with open(filepath, 'r') as f:
        code = f.read()

    tmpl_args = dict()
    tmpl_args['code'] = code
    tmpl_args['module_name'] = module_name

    template = """$code

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

    return temp_filename

# I use .${filename}.cppimporthash as the checksum file for each module.
def get_checksum_filepath(filepath):
    return os.path.join(
        os.path.dirname(filepath),
        '.' + os.path.basename(filepath) + '.cppimporthash'
    )

def extract_includes(filepath):
    lines = open(filepath, 'r').read()
    regex = '\"(.+?)\"'
    includes = []
    for l in lines.split('\n'):
        if l.startswith('#include'):
            m = re.findall(regex, l)
            if len(m) > 0:
                assert(len(m) == 1)
                includes.append(m[0])
    return includes

def find_file_in_folders(filename, paths):
    for d in paths:
        if not os.path.exists(d):
            continue

        if os.path.isfile(d):
            continue

        for f in os.listdir(d):
            if f == filename:
                return os.path.join(d, f)
    return None

def calc_cur_checksum(filepath):
    text = open(filepath, 'r').read().encode('utf-8')

    include_files = extract_includes(filepath)
    user_include_dirs = get_user_include_dirs(filepath)
    for f in include_files:
        inc_filepath = find_file_in_folders(f, user_include_dirs)
        text += open(inc_filepath, 'r').read().encode('utf-8')
    return hashlib.md5(text).hexdigest()

# Use a checksum to see if the file has been changed since the last compilation
def checksum_match(filepath):
    checksum_filepath = get_checksum_filepath(filepath)

    cur_checksum = calc_cur_checksum(filepath)

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

def get_module_name(full_module_name):
    return full_module_name.split('.')[-1]

def get_ext_dir(filepath):
    return os.path.dirname(filepath)

def get_user_include_dirs(filepath):
    return [
        get_ext_dir(filepath)
    ]

def run_config(temp_filepath):
    lines = open(temp_filepath, 'r').read().split('\n')
    config_match = [i for i in range(len(lines)) if lines[i]]
    first_line = None
    for i in range(len(lines)):
        if lines[i].startswith('/* cppimport'):
            first_line = i
            break
    if first_line is not None:
        last_line = None
        for i in range(first_line, len(lines)):
            if lines[i].startswith('*/'):
                last_line = i
        assert(last_line is not None)
        print(first_line, last_line)
        code = lines[(first_line + 1):last_line]
        data = dict()
        data['config'] = ''
        exec('\n'.join(code), data)
        return data
    return dict()

def build_module(full_module_name, filepath):
    build_path = tempfile.mkdtemp()
    temp_filepath = template_plugin(
        get_module_name(full_module_name), filepath, build_path
    )

    cfg = run_config(temp_filepath)

    system_include_dirs = [
        pybind11.get_include(),
        pybind11.get_include(True)
    ]

    ext = ImportCppExt(
        get_ext_dir(filepath),
        full_module_name,
        sources = [temp_filepath],
        language = 'c++',
        include_dirs = system_include_dirs + get_user_include_dirs(filepath),
        extra_compile_args = [
            '-std=c++11', '-Wall', '-Werror'
        ] + cfg['compiler_args']
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
        with stdchannel_redirected(sys.stdout, os.devnull):
            with stdchannel_redirected(sys.stderr, os.devnull):
                setuptools.setup(**setuptools_args)
    else:
        setuptools.setup(**setuptools_args)

    shutil.rmtree(build_path)

def get_extension_suffix():
    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
    if ext_suffix is None:
        ext_suffix = sysconfig.get_config_var('SO')
    return ext_suffix

def if_bad_checksum_build(full_module_name, filepath):
    ext_name = get_module_name(full_module_name) + get_extension_suffix()
    ext_path = os.path.join(get_ext_dir(filepath), ext_name)

    checksum_good, checksum_save = checksum_match(filepath)

    use_existing_extension = not should_force_rebuild and \
        checksum_good and \
        os.path.exists(ext_path)

    if use_existing_extension:
        quiet_print("Matching checksum for " + filepath + " --> not compiling")
    else:
        quiet_print("Compiling " + filepath)
        build_module(full_module_name, filepath)
        open(checksum_save[0], 'w').write(checksum_save[1])

def find_matching_path_dirs(moduledir):
    if moduledir is '':
        return sys.path

    ds = []
    for dir in sys.path:
        test_path = os.path.join(dir, moduledir)
        if os.path.exists(test_path) and os.path.isdir(test_path):
            ds.append(test_path)
    return ds

def find_module_cpppath(modulename):
    ext = '.cpp'
    modulepath = modulename.replace('.', os.sep) + ext
    moduledir = os.path.dirname(modulepath)
    modulefilename = os.path.basename(modulepath)
    matching_dirs = find_matching_path_dirs(moduledir)
    matching_dirs = [os.getcwd() if d == '' else d for d in matching_dirs]
    return find_file_in_folders(modulefilename, matching_dirs)

class CppFinder(object):
    def __init__(self):
        pass

    def find_module(self, fullname, path = None):
        # Search through sys.path to find a C++ file that matches the module
        filepath = find_module_cpppath(fullname)

        if filepath is None or not os.path.exists(filepath):
            return

        try:
            if_bad_checksum_build(fullname, filepath)
        except Exception as e:
            print(traceback.format_exc())

# Add the import hook.
sys.meta_path.insert(0, CppFinder())
