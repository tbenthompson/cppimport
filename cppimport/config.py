quiet = True
should_force_rebuild = False
file_exts = ['.cpp', '.c']

def set_quiet(to):
    global quiet
    quiet = to

def force_rebuild():
    global should_force_rebuild
    should_force_rebuild = True

def quiet_print(a):
    global quiet
    if not quiet:
        print(a)
