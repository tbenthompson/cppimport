import os

def make_absolute(this_dir, s):
    if os.path.isabs(s):
        return s
    else:
        return os.path.join(this_dir, s)
