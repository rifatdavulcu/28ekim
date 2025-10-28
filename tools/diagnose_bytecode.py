# Diagnostic script: compile each .py file and recursively disassemble code objects
# to detect code objects that cause dis.get_instructions to raise IndexError.

import os
import sys
import dis
import traceback

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
exclude_dirs = {'.git', '__pycache__', 'build', 'dist'}
problem_files = []


def iter_code_objects(code):
    # yield the code object and recurse into co_consts for nested code objects
    yield code
    for const in code.co_consts:
        if isinstance(const, type(code)):
            yield from iter_code_objects(const)


for dirpath, dirnames, filenames in os.walk(root):
    # skip excluded dirs
    dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
    for fn in filenames:
        if not fn.endswith('.py'):
            continue
        path = os.path.join(dirpath, fn)
        rel = os.path.relpath(path, root)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                src = f.read()
        except Exception as e:
            print(f"[SKIP READ ERROR] {rel}: {e}")
            continue
        try:
            code = compile(src, path, 'exec')
        except Exception as e:
            print(f"[COMPILE ERROR] {rel}: {e}")
            problem_files.append((rel, 'compile', str(e)))
            continue
        try:
            for c in iter_code_objects(code):
                # calling dis.get_instructions to emulate modulegraph util behavior
                list(dis.get_instructions(c))
        except Exception as e:
            tb = traceback.format_exc()
            print(f"[DISASSEMBLE ERROR] {rel}: {e}\n{tb}")
            problem_files.append((rel, type(e).__name__, str(e)))

if not problem_files:
    print('\nNo problems detected by static disassembly test.')
    sys.exit(0)
else:
    print('\nProblematic files summary:')
    for p in problem_files:
        print(' -', p)
    sys.exit(2)
