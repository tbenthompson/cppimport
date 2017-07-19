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

def turn_off_strict_prototypes():
    import distutils.sysconfig
    cfg_vars = distutils.sysconfig.get_config_vars()
    for key, value in cfg_vars.items():
        if type(value) == str:
            cfg_vars[key] = value.replace("-Wstrict-prototypes", "")
