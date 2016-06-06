import os
import sys

def get_rendered_source_filepath(filepath):
    dirname = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    return os.path.join(dirname, '.rendered.' + filename)

def setup_pybind11(cfg):
    import pybind11
    cfg['include_dirs'] = (
        cfg.get('include_dirs', []) +
        [pybind11.get_include(), pybind11.get_include(True)]
    )
    cfg['compiler_args'] = (
        cfg.get('compiler_args', []) +
        ['-std=c++11']
    )

def run_templating(module_data):
    import mako.template
    import mako.runtime
    import mako.exceptions
    import mako.lookup

    if sys.version_info[0] == 2:
        import StringIO as io
    else:
        import io

    module_data['cfg'] = dict()
    module_data['setup_pybind11'] = setup_pybind11
    buf = io.StringIO()
    ctx = mako.runtime.Context(buf, **module_data)

    filepath = module_data['filepath']
    lookup = mako.lookup.TemplateLookup(directories=[os.path.dirname(filepath)])
    tmpl = mako.template.Template(filename = filepath, lookup = lookup)

    try:
        rendered_src = tmpl.render_context(ctx)
    except:
        print(mako.exceptions.text_error_template().render())

    rendered_src_filepath = get_rendered_source_filepath(filepath)
    open(rendered_src_filepath, 'w').write(buf.getvalue())
    module_data['rendered_src_filepath'] = rendered_src_filepath
