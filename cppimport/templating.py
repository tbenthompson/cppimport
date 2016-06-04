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

def run_templating(filepath):
    data = dict()
    data['cfg'] = dict()
    buf = io.StringIO()
    ctx = mako.runtime.Context(buf, **data)

    lookup = mako.lookup.TemplateLookup(directories=[os.path.dirname(filepath)])
    tmpl = mako.template.Template(filename = filepath, lookup = lookup)

    try:
        rendered_src = tmpl.render_context(ctx)
    except:
        print(mako.exceptions.text_error_template().render())

    rendered_src_filepath = get_rendered_source_filepath(filepath)
    open(rendered_src_filepath, 'w').write(buf.getvalue())

    return rendered_src_filepath, data['cfg']
