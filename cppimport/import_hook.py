import sys
import os
import shutil
import tempfile
import sysconfig
import setuptools
import setuptools.command.build_ext
import distutils.file_util
import pybind11
import traceback
import contextlib
import mako.template
import hashlib

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

def set_quiet(to):
    global quiet
    quiet = to

template = """
${code}

PYBIND11_PLUGIN(${module_name}) {
    pybind11::module m("${module_name}", "auto-compiled c++ extension");
    pyexport(m);
    return m.ptr();
}
"""


def setup_plugin(module_name, filepath, tempdir):
    with open(filepath, 'r') as f:
        code = f.read()

    tmpl_args = dict()
    tmpl_args['code'] = code
    tmpl_args['module_name'] = module_name

    plugin_code = mako.template.Template(template).render(**tmpl_args)

    temp_filename = os.path.join(tempdir, module_name + '.cpp')
    with open(temp_filename, 'w') as f_tmp:
        f_tmp.write(plugin_code)

    return temp_filename

def get_checksum_filepath(filepath):
    return os.path.join(
        os.path.dirname(filepath),
        '.' + os.path.basename(filepath) + '.cppimporthash'
    )

def checksum_match(filepath):
    checksum_filepath = get_checksum_filepath(filepath)
    cur_checksum = hashlib.md5(
        open(filepath, 'r').read().encode('utf-8')
    ).hexdigest()
    if os.path.exists(checksum_filepath):
        saved_checksum = open(checksum_filepath, 'r').read()
        if saved_checksum == cur_checksum:
            return True
    open(checksum_filepath, 'w').write(cur_checksum)
    return False

class ImportCppExt(setuptools.Extension):
    def __init__(self, libdest, *args, **kwargs):
        self.libdest = libdest
        setuptools.Extension.__init__(self, *args, **kwargs)

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

def build_plugin(full_module_name, filepath):
    build_path = tempfile.mkdtemp()
    module_name = full_module_name.split('.')[-1]
    dir_name = os.path.dirname(filepath)

    ext_suffix = sysconfig.get_config_var('EXT_SUFFIX')
    ext_path = os.path.join(dir_name, module_name + ext_suffix)

    if checksum_match(filepath) and os.path.exists(ext_path):
        if not quiet:
            print("Matching checksum for " + filepath + " --> not compiling")
        return

    print("Compiling " + filepath)

    temp_filepath = setup_plugin(module_name, filepath, build_path)

    ext = ImportCppExt(
        dir_name,
        full_module_name,
        sources = [temp_filepath],
        language = 'c++',
        include_dirs = [pybind11.get_include()],
        extra_compile_args = [
            '-std=c++11', '-Wall', '-Werror'
        ]
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
        for f in os.listdir(d):
            if f == modulefilename:
                return os.path.join(d, f)
    return None

class CppFinder(object):
    def __init__(self):
        pass

    def find_module(self, fullname, path = None):
        filepath = find_module_cpppath(fullname)

        if filepath is None or not os.path.exists(filepath):
            return

        try:
            build_plugin(fullname, filepath)
        except Exception as e:
            print(traceback.format_exc())

sys.meta_path.insert(0, CppFinder())
