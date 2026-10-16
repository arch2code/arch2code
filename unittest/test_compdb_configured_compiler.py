#!/usr/bin/env python3
"""compile_commands.json and .clangd follow the configured compiler.

A site names its Clang through A2C_CLANG, which can be a full path or a
versioned name such as clang++-20. Checks:
- gen_compile_commands.py, given the compiler with --compiler, keeps both the
  object compile and the module precompile from synthetic `make -n` lines,
  for each spelling;
- on a private copy of examples/helloWorld with A2C_CLANG exported, the
  `make -n clangd` recipe passes that compiler to gen_compile_commands.py and
  writes it as the .clangd Compiler.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir


FIXTURE = os.path.join(base_dir, 'examples', 'helloWorld')
SCRIPT = os.path.join(base_dir, 'pysrc', 'gen_compile_commands.py')
SPELLINGS = ('clang++', '/opt/llvm/bin/clang++', 'clang++-20', '/usr/lib/llvm-20/bin/clang++',
             '/usr/lib/llvm-20/bin/clang++-20')
SITE_CLANG = '/opt/llvm/bin/clang++'


def syntheticLines(cxx):
    return '\n'.join([
        'mkdir -p /b/model',
        f'{cxx} -m64 -std=c++23 -MMD --precompile -x c++-module /src/m.cppm -o /b/m.pcm',
        f'{cxx} -m64 -std=c++23 -c /b/m.pcm -o /b/m.module.o',
        f'{cxx} -m64 -std=c++23 -MMD -c /src/a.cpp -o /b/a.o',
        '/src/arch2code.py --db /src/p.db -r --systemc --file /src/a.cpp',
    ]) + '\n'


def main():
    failures = []

    def check(ok, message):
        print(f"{'PASS' if ok else 'FAIL'}: {message}")
        if not ok:
            failures.append(message)

    with tempfile.TemporaryDirectory(prefix='compdb_compiler_') as tmp:
        for cxx in SPELLINGS:
            captured = os.path.join(tmp, 'make-n.txt')
            output = os.path.join(tmp, 'compile_commands.json')
            with open(captured, 'w') as f:
                f.write(syntheticLines(cxx))
            result = subprocess.run([sys.executable, SCRIPT, captured, output,
                                     '--directory', '/b', '--compiler', cxx],
                                    capture_output=True, text=True)
            files = []
            if result.returncode == 0:
                with open(output) as f:
                    files = sorted(e['file'] for e in json.load(f))
            check(files == ['/src/a.cpp', '/src/m.cppm'],
                  f"--compiler {cxx} keeps the object compile and the module precompile (got {files})")

        project = os.path.join(tmp, 'helloWorld')
        shutil.copytree(FIXTURE, project, symlinks=True, ignore=shutil.ignore_patterns(
            'build', '.gen', '*.db', '*.db-*', 'compile_commands.json', '.clangd'))
        e = dict(os.environ, NO_COLOR='1', A2C_CLANG=SITE_CLANG)
        common = [f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}']
        db = subprocess.run(['make', '-C', project, *common, 'db'],
                            capture_output=True, text=True, timeout=600, env=e)
        if db.returncode != 0:
            print(f"FAIL: make db failed:\n{db.stdout}\n{db.stderr}")
            return 1
        result = subprocess.run(['make', '-C', os.path.join(project, 'rundir'), '--no-print-directory',
                                 *common, '-n', 'clangd'],
                                capture_output=True, text=True, timeout=600, env=e)
        lines = result.stdout.splitlines()
        # The recipe spans continuation lines up to its trailing redirect.
        start = result.stdout.find('gen_compile_commands.py')
        compdb = result.stdout[start:result.stdout.find('>/dev/null', start)] if start >= 0 else ''
        check(f'--compiler {SITE_CLANG}' in compdb,
              f"make -n clangd passes --compiler {SITE_CLANG} to gen_compile_commands.py: {compdb!r}")
        compiler = [l for l in lines if 'Compiler:' in l]
        check(compiler and f'Compiler: {SITE_CLANG}' in compiler[0],
              f"make -n clangd writes Compiler: {SITE_CLANG} into .clangd: {compiler}")

    if failures:
        print("SOME TESTS FAILED")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == '__main__':
    sys.exit(main())
