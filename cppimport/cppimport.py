import sys
import os
import shutil
import tempfile
import setuptools
import pybind11
import traceback
import contextlib
import mako.template
import hashlib

template = """
${code}

PYBIND11_PLUGIN(${module_name}) {
    pybind11::module m("${module_name}", "auto-compiled c++ extension");
    pyexport(m);
    return m.ptr();
}
"""

quiet = True


@contextlib.contextmanager
def stdchannel_redirected(stdchannel, dest_filename):
    """
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


def setup_plugin(module_name, filepath, tempdir):
    with open(filepath, 'r') as f:
        code = f.read()

    tmpl_args = dict()
    tmpl_args['code'] = code
    tmpl_args['module_name'] = module_name

    plugin_code = mako.template.Template(template).render(**tmpl_args)

    temp_filename = os.path.join(tempdir, filename)
    with open(temp_filename, 'w') as f_tmp:
        f_tmp.write(plugin_code)

    return temp_filename

def checksum_match(filepath):
    checksum_filepath = '.' + filepath + '.cppimporthash'
    cur_checksum = hashlib.md5(
        open(filepath, 'r').read().encode('utf-8')
    ).hexdigest()
    if os.path.exists(checksum_filepath):
        saved_checksum = open(checksum_filepath, 'r').read()
        if saved_checksum == cur_checksum:
            return True
    open(checksum_filepath, 'w').write(cur_checksum)
    return False

def build_plugin(module_name, filepath):
    build_path = tempfile.mkdtemp()

    if checksum_match(filepath):
        if not quiet:
            print("Matching checksum for " + filepath + " --> not compiling")
        return
    print("Compiling " + filepath)

    temp_filepath = setup_plugin(module_name, filepath, build_path)
    ext = setuptools.Extension(
        module_name,
        sources = [temp_filepath],
        language = 'c++',
        include_dirs = [pybind11.get_include()],
        extra_compile_args = ['-std=c++11']
    )

    args = ['build_ext', '--inplace']
    args.append('--build-temp=' + build_path)
    args.append('--build-lib=' + build_path)

    if quiet:
        args.append('-q')

    setuptools_args = dict(
        name = module_name,
        ext_modules = [ext],
        script_args = args
    )

    if quiet:
        with stdchannel_redirected(sys.stdout, os.devnull):
            with stdchannel_redirected(sys.stderr, os.devnull):
                setuptools.setup(**setuptools_args)
    else:
        setuptools.setup(**setuptools_args)

    shutil.rmtree(build_path)

class CppFinder(object):
    def __init__(self):
        pass

    def find_module(self, fullname, path = None):
        ext = '.cpp'
        filepath = fullname.replace('.', os.sep) + ext
        print(filepath)
        if not os.path.exists(filepath):
            return None
        try:
            build_plugin(fullname, filepath)
        except Exception as e:
            print(traceback.format_exc())
        return None

sys.meta_path.insert(0, CppFinder())
