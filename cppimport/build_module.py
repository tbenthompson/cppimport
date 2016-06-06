import os
import sys
import tempfile
import contextlib

import shutil
import distutils

import setuptools
import setuptools.command.build_ext
import cppimport.config

if sys.version_info[0] == 2:
    import StringIO as io
else:
    import io

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

def build_module(module_data):
    build_path = tempfile.mkdtemp()

    full_module_name = module_data['fullname']
    filepath = module_data['filepath']
    cfg = module_data['cfg']

    module_data['dependency_dirs'] = (
        module_data['cfg'].get('include_dirs', []) +
        [module_data['filedirname']]
    )
    module_data['extra_source_filepaths'] = [
        cppimport.find.find_file_in_folders(d, module_data['dependency_dirs'])
        for d in cfg.get('sources', [])
    ]

    ext = ImportCppExt(
        os.path.dirname(filepath),
        full_module_name,
        language = 'c++',
        sources = (
            module_data['extra_source_filepaths'] +
            [module_data['rendered_src_filepath']]
        ),
        include_dirs = cfg.get('include_dirs', []) + [os.path.dirname(filepath)],
        extra_compile_args = cfg.get('compiler_args', []),
        extra_link_args = cfg.get('linker_args', []),
        libraries = cfg.get('libraries', [])
    )

    args = ['build_ext', '--inplace']
    args.append('--build-temp=' + build_path)
    args.append('--build-lib=' + build_path)

    if cppimport.config.quiet:
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

    if cppimport.config.quiet:
        with stdchannel_redirected("stdout"):
            with stdchannel_redirected("stderr"):
                setuptools.setup(**setuptools_args)
    else:
        setuptools.setup(**setuptools_args)

    shutil.rmtree(build_path)
