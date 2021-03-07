import contextlib
import distutils
import distutils.sysconfig
import io
import logging
import os
import shutil
import tempfile

import setuptools
import setuptools.command.build_ext

import cppimport
from cppimport.filepaths import make_absolute

logger = logging.getLogger(__name__)


def build_module(module_data):
    _handle_strict_prototypes()

    build_path = tempfile.mkdtemp()

    full_module_name = module_data["fullname"]
    filepath = module_data["filepath"]
    cfg = module_data["cfg"]

    module_data["abs_include_dirs"] = [
        make_absolute(module_data["filedirname"], d)
        for d in cfg.get("include_dirs", [])
    ] + [os.path.dirname(filepath)]
    module_data["abs_library_dirs"] = [
        make_absolute(module_data["filedirname"], d)
        for d in cfg.get("library_dirs", [])
    ]
    module_data["dependency_dirs"] = module_data["abs_include_dirs"] + [
        module_data["filedirname"]
    ]
    module_data["extra_source_filepaths"] = [
        make_absolute(module_data["filedirname"], s) for s in cfg.get("sources", [])
    ]

    ext = ImportCppExt(
        os.path.dirname(filepath),
        full_module_name,
        language="c++",
        sources=(
            module_data["extra_source_filepaths"]
            + [module_data["rendered_src_filepath"]]
        ),
        include_dirs=module_data["abs_include_dirs"],
        extra_compile_args=cfg.get("extra_compile_args", []),
        extra_link_args=cfg.get("extra_link_args", []),
        library_dirs=module_data["abs_library_dirs"],
        libraries=cfg.get("libraries", []),
    )

    args = [
        "build_ext",
        "--inplace",
        "--build-temp=" + build_path,
        "--build-lib=" + build_path,
        "-v",
    ]

    setuptools_args = dict(
        name=full_module_name,
        ext_modules=[ext],
        script_args=args,
        cmdclass={"build_ext": BuildImportCppExt},
    )

    # Monkey patch in the parallel compiler if requested.
    # TODO: this will still cause problems if there is multithreaded code
    # interacting with distutils. Ideally, we'd just subclass CCompiler
    # instead.
    if cfg.get("parallel"):
        old_compile = distutils.ccompiler.CCompiler.compile
        distutils.ccompiler.CCompiler.compile = _parallel_compile

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        with contextlib.redirect_stderr(f):
            setuptools.setup(**setuptools_args)
    logger.debug(f"Setuptools/compiler output: {f.getvalue()}")

    # Remove the parallel compiler to not corrupt the outside environment.
    if cfg.get("parallel"):
        distutils.ccompiler.CCompiler.compile = old_compile

    shutil.rmtree(build_path)


def _handle_strict_prototypes():
    if not cppimport.settings["remove_strict_prototypes"]:
        return

    cfg_vars = distutils.sysconfig.get_config_vars()
    for key, value in cfg_vars.items():
        if type(value) == str:
            cfg_vars[key] = value.replace("-Wstrict-prototypes", "")


class ImportCppExt(setuptools.Extension):
    """
    Subclass setuptools.Extension to add self.libdest specifying where the shared
    library should be placed after being compiled with BuildImportCppExt.
    """

    def __init__(self, libdest, *args, **kwargs):
        self.libdest = libdest
        setuptools.Extension.__init__(self, *args, **kwargs)


class BuildImportCppExt(setuptools.command.build_ext.build_ext):
    """
    Subclass setuptools build_ext to put the compiled shared library in the
    appropriate place in the source tree from the ImportCppExt.libdest value.
    """

    def copy_extensions_to_source(self):
        for ext in self.extensions:
            fullname = self.get_ext_fullname(ext.name)
            filename = self.get_ext_filename(fullname)
            src_filename = os.path.join(self.build_lib, filename)
            dest_filename = os.path.join(ext.libdest, os.path.basename(filename))

            distutils.file_util.copy_file(
                src_filename, dest_filename, verbose=self.verbose, dry_run=self.dry_run
            )


# Patch for parallel compilation with distutils
# From: http://stackoverflow.com/questions/11013851/speeding-up-build-process-with-distutils # noqa: E501
def _parallel_compile(
    self,
    sources,
    output_dir=None,
    macros=None,
    include_dirs=None,
    debug=0,
    extra_preargs=None,
    extra_postargs=None,
    depends=None,
):

    # these lines are copied directly from distutils.ccompiler.CCompiler
    macros, objects, extra_postargs, pp_opts, build = self._setup_compile(
        output_dir, macros, include_dirs, sources, depends, extra_postargs
    )
    cc_args = self._get_cc_args(pp_opts, debug, extra_preargs)

    # Determine the number of compilation threads. Unless there are special
    # circumstances, this is the number of cores on the machine
    N = 1
    try:
        import multiprocessing
        import multiprocessing.pool

        N = multiprocessing.cpu_count()
    except (ImportError, NotImplementedError):
        pass

    def _single_compile(obj):
        try:
            src, ext = build[obj]
        except KeyError:
            return
        self._compile(obj, src, ext, cc_args, extra_postargs, pp_opts)

    # imap is evaluated on demand, converting to list() forces execution
    list(multiprocessing.pool.ThreadPool(N).imap(_single_compile, objects))
    return objects
