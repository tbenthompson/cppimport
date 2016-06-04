import os
import sys
import mako.template
import mako.runtime
import mako.exceptions
import mako.lookup

if sys.version_info[0] == 2:
    import StringIO as io
else:
    import io

def get_rendered_source_filepath(filepath):
    dirname = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    return os.path.join(dirname, '.rendered.' + filename)

def run_templating(module_data):
    module_data['cfg'] = dict()
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
