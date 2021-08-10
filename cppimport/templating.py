import io
import logging
import os

import mako.exceptions
import mako.lookup
import mako.runtime
import mako.template

logger = logging.getLogger(__name__)


def run_templating(module_data):
    module_data["cfg"] = BuildArgs(
        sources=[],
        include_dirs=[],
        extra_compile_args=[],
        libraries=[],
        library_dirs=[],
        extra_link_args=[],
        dependencies=[],
        parallel=False,
    )
    module_data["setup_pybind11"] = setup_pybind11
    buf = io.StringIO()
    ctx = mako.runtime.Context(buf, **module_data)

    filepath = module_data["filepath"]
    try:
        template_dirs = [os.path.dirname(filepath)]
        lookup = mako.lookup.TemplateLookup(directories=template_dirs)
        tmpl = lookup.get_template(module_data["filebasename"])
        tmpl.render_context(ctx)
    except:  # noqa: E722
        logger.exception(mako.exceptions.text_error_template().render())
        raise

    rendered_src_filepath = get_rendered_source_filepath(filepath)

    with open(rendered_src_filepath, "w", newline="") as f:
        f.write(buf.getvalue())

    module_data["rendered_src_filepath"] = rendered_src_filepath


class BuildArgs(dict):
    """
    This exists for backwards compatibility with old configuration key names.
    TODO: Add deprecation warnings to allow removing this sometime in the future.
    """

    _key_mapping = {
        "compiler_args": "extra_compile_args",
        "linker_args": "extra_link_args",
    }

    def __getitem__(self, key):
        return super(BuildArgs, self).__getitem__(self._key_mapping.get(key, key))

    def __setitem__(self, key, value):
        super(BuildArgs, self).__setitem__(self._key_mapping.get(key, key), value)


def setup_pybind11(cfg):
    import pybind11

    cfg["include_dirs"] += [pybind11.get_include(), pybind11.get_include(True)]
    # Prefix with c++11 arg instead of suffix so that if a user specifies c++14
    # (or later!) then it won't be overridden.
    cfg["compiler_args"] = ["-std=c++11", "-fvisibility=hidden"] + cfg["compiler_args"]


def get_rendered_source_filepath(filepath):
    dirname = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    return os.path.join(dirname, ".rendered." + filename)
