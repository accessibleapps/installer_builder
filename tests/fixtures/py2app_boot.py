# _run from py2app/bootstrap/boot_app.py as emitted in the observed QCast build.
import sys


def _run():
    global __file__
    import os
    import site

    sys.frozen = "macosx_app"
    base = os.environ["RESOURCEPATH"]
    argv0 = os.path.basename(os.environ["ARGVZERO"])
    script = SCRIPT_MAP.get(argv0, DEFAULT_SCRIPT)
    path = os.path.join(base, script)
    sys.argv[0] = __file__ = path
    if sys.version_info[0] == 2:
        with open(path, "rU") as fp:
            source = fp.read() + "\n"
    else:
        with open(path, "rb") as fp:
            encoding = guess_encoding(fp)
        with open(path, "r", encoding=encoding) as fp:
            source = fp.read() + "\n"
        BOM = b"\xef\xbb\xbf".decode("utf-8")
        if source.startswith(BOM):
            source = source[1:]
    exec(compile(source, path, "exec"), globals(), globals())


DEFAULT_SCRIPT = "main.pyw"
SCRIPT_MAP = {}
_run()
