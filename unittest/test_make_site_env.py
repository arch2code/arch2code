#!/usr/bin/env python3
"""A site environment picks the compiler and Boost link line without project edits.

Works on a private copy of examples/helloWorld and asks its rundir make for
CXX and LD_FLAGS. Checks:
- with nothing set, CXX is clang++ and the link line starts with the default
  Boost libraries on LD_BOOST;
- an exported A2C_CLANG names the compiler, while an exported CXX does not
  replace it and USE_GCC still selects g++;
- an exported BOOST_LIBS replaces the default Boost libraries and LD_BOOST is
  then not required; an empty BOOST_LIBS counts as unset; with neither set the
  build still stops on LD_BOOST;
- `BOOST_LIBS=` on the make command line keeps the default Boost libraries;
- an exported EXTRA_LD_FLAGS reaches the link line, because the scaffolded and
  committed rundir Makefiles append to it rather than assign it, and a stale
  A2C_SITE_EXTRA_LD_FLAGS left in the shell does not replace it;
- with a site EXTRA_LD_FLAGS and a project `+=`, the link command the build
  runs carries each flag once, and a site or project `$$ORIGIN` rpath and a
  quoted project flag reach it verbatim.
"""

import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir
from templates.fileGen import scaffold


FIXTURE = os.path.join(base_dir, 'examples', 'helloWorld')
# Every directory holding committed projects: examples, unittest fixtures, and
# pro's examples when present.
EXAMPLE_ROOTS = [os.path.join(base_dir, 'examples'),
                 os.path.join(base_dir, 'unittest', 'fixtures'),
                 os.path.join(base_dir, '..', 'pro', 'examples')]
SITE_VARS = ('A2C_CLANG', 'A2C_SITE_EXTRA_LD_FLAGS', 'BOOST_LIBS', 'CXX', 'EXTRA_LD_FLAGS', 'USE_GCC')
# Each make() stands for a make started from a shell, so an outer make running
# this suite must not pass its sub-make state down.
SUBMAKE_VARS = ('MAKELEVEL', 'MAKEFLAGS', 'MFLAGS', 'MAKEOVERRIDES')
PRINTER = 'printVars: ; $(info CXX=$(CXX))$(info LD_FLAGS=$(LD_FLAGS))@:'
LD_ASSIGN = re.compile(r'^EXTRA_LD_FLAGS\s*=', re.MULTILINE)


def baseEnv():
    e = {k: v for k, v in os.environ.items() if k not in SITE_VARS + SUBMAKE_VARS}
    e['NO_COLOR'] = '1'
    return e


def make(project, subdir, e, *args):
    return subprocess.run(['make', '-C', os.path.join(project, subdir), '--no-print-directory',
                           f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}', *args],
                          capture_output=True, text=True, timeout=600, env=e)


def printVars(project, e, *args):
    result = make(project, 'rundir', e, '--eval', PRINTER, 'printVars', *args)
    values = {}
    for line in result.stdout.splitlines():
        key, sep, value = line.partition('=')
        if sep and key in ('CXX', 'LD_FLAGS'):
            values[key] = value
    return result, values


def main():
    failures = []

    def check(ok, message):
        print(f"{'PASS' if ok else 'FAIL'}: {message}")
        if not ok:
            failures.append(message)

    with tempfile.TemporaryDirectory(prefix='make_site_env_') as tmp:
        project = os.path.join(tmp, 'helloWorld')
        shutil.copytree(FIXTURE, project, symlinks=True, ignore=shutil.ignore_patterns(
            'build', '.gen', '*.db', '*.db-*', 'compile_commands.json'))
        base = baseEnv()
        ldBoost = base.get('LD_BOOST')
        if not ldBoost:
            print("FAIL: LD_BOOST is not set in the test environment")
            return 1
        db = make(project, '.', base, 'db')
        if db.returncode != 0:
            print(f"FAIL: make db failed:\n{db.stdout}\n{db.stderr}")
            return 1

        defaultBoost = (f"-lboost_program_options "
                        f"-L{ldBoost} -L{base['SYSTEMC_LIBDIR']} -ldl -lrt -lsystemc -pthread")
        result, values = printVars(project, base)
        check(result.returncode == 0 and values.get('CXX') == 'clang++',
              f"default compiler is clang++ (got {values.get('CXX')!r})")
        check(values.get('LD_FLAGS', '').startswith(defaultBoost),
              f"default link line starts with {defaultBoost!r} (got {values.get('LD_FLAGS')!r})")

        e = dict(base, A2C_CLANG='/x/clang++')
        result, values = printVars(project, e)
        check(result.returncode == 0 and values.get('CXX') == '/x/clang++',
              f"exported A2C_CLANG=/x/clang++ is the compiler (got {values.get('CXX')!r})")

        e = dict(base, CXX='g++')
        result, values = printVars(project, e)
        check(values.get('CXX') == 'clang++',
              f"an exported CXX=g++ does not replace clang++ (got {values.get('CXX')!r})")

        e = dict(base, A2C_CLANG='/x/clang++')
        result, values = printVars(project, e, 'USE_GCC=1')
        check(values.get('CXX') == 'g++',
              f"USE_GCC=1 selects g++ even with A2C_CLANG set (got {values.get('CXX')!r})")

        siteBoost = '-lboost_site_a -lboost_site_b -L/site/boost/lib'
        e = dict(base, BOOST_LIBS=siteBoost)
        del e['LD_BOOST']
        result, values = printVars(project, e)
        ldFlags = values.get('LD_FLAGS', '')
        check(result.returncode == 0,
              f"BOOST_LIBS set and LD_BOOST unset does not stop the build:\n{result.stderr.strip()}")
        check(ldFlags.startswith(f"{siteBoost} -L{base['SYSTEMC_LIBDIR']}")
              and '-lboost_program_options' not in ldFlags,
              f"BOOST_LIBS replaces the default Boost libraries (got {ldFlags!r})")

        e = dict(base, BOOST_LIBS='')
        result, values = printVars(project, e)
        check(values.get('LD_FLAGS', '').startswith(defaultBoost),
              f"an empty exported BOOST_LIBS keeps the default Boost libraries "
              f"(got {values.get('LD_FLAGS')!r})")

        result, values = printVars(project, base, 'BOOST_LIBS=')
        check(values.get('LD_FLAGS', '').startswith(defaultBoost),
              f"BOOST_LIBS= on the command line keeps the default Boost libraries "
              f"(got {values.get('LD_FLAGS')!r})")

        e = dict(base, BOOST_LIBS='')
        del e['LD_BOOST']
        result, values = printVars(project, e)
        check(result.returncode != 0 and 'LD_BOOST is not set' in result.stderr,
              f"an empty BOOST_LIBS with LD_BOOST unset stops on LD_BOOST "
              f"(rc {result.returncode}: {result.stderr.strip()!r})")

        e = dict(base)
        del e['LD_BOOST']
        result, values = printVars(project, e)
        check(result.returncode != 0 and 'LD_BOOST is not set' in result.stderr,
              f"neither BOOST_LIBS nor LD_BOOST set stops on LD_BOOST "
              f"(rc {result.returncode}: {result.stderr.strip()!r})")

        e = dict(base, EXTRA_LD_FLAGS='-no-pie -L/site/extra')
        result, values = printVars(project, e)
        check('-no-pie -L/site/extra' in values.get('LD_FLAGS', ''),
              f"an exported EXTRA_LD_FLAGS reaches the link line (got {values.get('LD_FLAGS')!r})")

        e = dict(base, EXTRA_LD_FLAGS='-lnew_site', A2C_SITE_EXTRA_LD_FLAGS='-lstale_site')
        result, values = printVars(project, e)
        ldFlags = values.get('LD_FLAGS', '').split()
        check('-lnew_site' in ldFlags and '-lstale_site' not in ldFlags,
              f"a stale A2C_SITE_EXTRA_LD_FLAGS in the shell does not replace the exported "
              f"EXTRA_LD_FLAGS (got {values.get('LD_FLAGS')!r})")

        rundirMakefile = os.path.join(project, 'rundir', 'Makefile')
        with open(rundirMakefile) as f:
            text = f.read()
        with open(rundirMakefile, 'w') as f:
            f.write(text.replace(
                'EXTRA_LD_FLAGS     +=',
                "EXTRA_LD_FLAGS     += -lproj_extra -Wl,-rpath,'$$ORIGIN/lib' -Wl,-rpath,'/opt/a b'"))
        e = dict(base, EXTRA_LD_FLAGS="-lsite_extra -Wl,-rpath,'$$ORIGIN/site'")
        gen = make(project, '.', e, 'gen')
        dry = make(project, 'rundir', e, '-n')
        links = [shlex.split(l) for l in dry.stdout.splitlines()
                 if ' -o ' in l and l.split(' -o ')[1].split()[0].endswith('/build/run')]
        argv = links[0] if len(links) == 1 else []
        check(gen.returncode == 0 and len(links) == 1,
              f"the dry run shows one link command (found {len(links)})")
        for flag in ('-lsite_extra', '-Wl,-rpath,$ORIGIN/site', '-lproj_extra', '-Wl,-rpath,$ORIGIN/lib',
                     '-Wl,-rpath,/opt/a b'):
            check(argv.count(flag) == 1,
                  f"the link command carries {flag!r} once (found {argv.count(flag)}; "
                  f"tail {argv[argv.index('-pthread') + 1:] if '-pthread' in argv else argv})")

    for hasFirmware in (False, True):
        text = scaffold.rundirMk({'projectName': 'p', 'hasFirmware': hasFirmware})
        check(not LD_ASSIGN.search(text) and 'EXTRA_LD_FLAGS     +=' in text,
              f"the scaffolded rundir Makefile (hasFirmware={hasFirmware}) appends to EXTRA_LD_FLAGS")

    assigning = []
    for root in EXAMPLE_ROOTS:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ('build', '.gen', 'obj_dir')]
            if os.path.basename(dirpath) == 'rundir' and 'Makefile' in filenames:
                path = os.path.join(dirpath, 'Makefile')
                with open(path) as f:
                    if LD_ASSIGN.search(f.read()):
                        assigning.append(os.path.relpath(path, base_dir))
    check(not assigning,
          "no committed rundir Makefile assigns EXTRA_LD_FLAGS, which would discard a site value"
          + (f": {assigning}" if assigning else ""))

    if failures:
        print("SOME TESTS FAILED")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == '__main__':
    sys.exit(main())
