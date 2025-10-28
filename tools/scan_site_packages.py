"""
Scan site-packages and other sys.path entries for Python source files (.py)
and try to disassemble every code object. Report any file or code object
that causes dis.get_instructions to raise an exception (IndexError etc.).

Run from project root with the same Python interpreter used by PyInstaller.
"""
import sys
import os
import dis
import traceback
import types

IGNORED_DIRS = {"__pycache__", "bin", "Scripts", "site-packages", "dist-info", "egg-info"}


def iter_code_objects(code):
    yield code
    for const in getattr(code, "co_consts", ()):
        if isinstance(const, types.CodeType):
            yield from iter_code_objects(const)


def scan_file(path):
    try:
        with open(path, "rb") as f:
            source = f.read()
        # compile in 'exec' mode
        code = compile(source, path, 'exec')
    except Exception as e:
        return ("compile-error", path, repr(e))

    try:
        for co in iter_code_objects(code):
            # dis.get_instructions can raise when bytecode or constants are weird
            for _ in dis.get_instructions(co):
                pass
    except Exception as e:
        tb = traceback.format_exc()
        return ("dis-error", path, type(e).__name__, str(e), tb)
    return None


def main():
    checked = 0
    errors = []
    paths = []
    for p in sys.path:
        if not p:
            continue
        if not os.path.exists(p):
            continue
        # prefer site-packages, but include all entries
        paths.append(p)

    print("Scanning sys.path entries:")
    for p in paths:
        print(" -", p)

    for root in paths:
        for dirpath, dirnames, filenames in os.walk(root):
            # skip venv internals and common large dirs
            parts = set(dirpath.replace("\\", "/").split("/"))
            if parts & IGNORED_DIRS:
                # still descend into actual site-packages subdirs, so don't prune too aggressively
                pass
            for fn in filenames:
                if not fn.endswith('.py'):
                    continue
                path = os.path.join(dirpath, fn)
                checked += 1
                if checked % 5000 == 0:
                    print(f"Checked {checked} files...")
                res = scan_file(path)
                if res is not None:
                    errors.append(res)
                    print("Error in:", res[1], res[2:])
    print(f"Done. Files checked: {checked}. Problems found: {len(errors)}")
    if errors:
        print("Sample problems:")
        for e in errors[:10]:
            print(e)


if __name__ == '__main__':
    main()
