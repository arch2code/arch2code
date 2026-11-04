#!/usr/bin/env python3
"""Every translation unit that imports a2c.endOfTest sees one endOfTestState.

endOfTestState::GetInstance() keeps the singleton in a function-local static.
In a named module a member defined in its class is not implicitly inline, and
clang 17 at -O2 inlined GetInstance() into each importer with a private copy of
that static: a keystone build carried 15 copies, voters registered in one and
the watchdog read another, and every run stopped with "No end-of-test voter".
Declaring GetInstance() inline makes the static one entity across translation
units.

The probe compiles the module and three translation units at -O2. Two units
each register a voter through their own endOfTest object; the third reads the
count. All three must report the same instance address and two voters.
"""

import os
import shutil
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
COMMON_SC = os.path.join(base_dir, 'common', 'systemc')

CXX = os.environ.get('CXX_FOR_TESTS', 'clang++')
STD = '-std=c++23'
OPT = '-O2'

TU = """
#include <systemc.h>
import a2c.endOfTest;
void *{name}_register()
{{
    static endOfTest voter(true);
    return &endOfTestState::GetInstance();
}}
"""

MAIN = """
#include <systemc.h>
#include <cstdio>
import a2c.endOfTest;
void *tuA_register();
void *tuB_register();
int sc_main(int, char *[])
{
    void *a = tuA_register();
    void *b = tuB_register();
    void *m = &endOfTestState::GetInstance();
    const int voters = endOfTestState::GetInstance().registeredVoters();
    std::printf("same=%d voters=%d\\n", (a == b && b == m) ? 1 : 0, voters);
    return (a == b && b == m && voters == 2) ? 0 : 1;
}
"""

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def run(cmd, cwd):
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)


def test_end_of_test_single_instance():
    sc_inc = os.environ.get('SYSTEMC_INCLUDE')
    sc_lib = os.environ.get('SYSTEMC_LIBDIR')
    if not sc_inc or not sc_lib:
        check(False, "SYSTEMC_INCLUDE and SYSTEMC_LIBDIR must be set, as they are for any build here")
        return
    tmp = tempfile.mkdtemp(prefix='a2c_eot_single_')
    try:
        flags = [STD, OPT, '-DSC_CPLUSPLUS=201703L', '-DSC_INCLUDE_DYNAMIC_PROCESSES', f'-I{sc_inc}']
        pcm = os.path.join(tmp, 'a2c.endOfTest.pcm')
        steps = [[CXX] + flags + ['--precompile', '-x', 'c++-module',
                                  os.path.join(COMMON_SC, 'endOfTest.cppm'), '-o', pcm],
                 [CXX, STD, OPT, '-c', pcm, '-o', os.path.join(tmp, 'endOfTest.o')]]
        sources = {'tuA.cpp': TU.format(name='tuA'), 'tuB.cpp': TU.format(name='tuB'), 'main.cpp': MAIN}
        for name, text in sources.items():
            with open(os.path.join(tmp, name), 'w') as f:
                f.write(text)
            steps.append([CXX] + flags + [f'-fmodule-file=a2c.endOfTest={pcm}', '-c', name,
                                          '-o', name[:-4] + '.o'])
        steps.append([CXX, '-o', 'probe', 'endOfTest.o', 'tuA.o', 'tuB.o', 'main.o',
                      f'-L{sc_lib}', '-lsystemc', '-pthread'])
        for cmd in steps:
            r = run(cmd, tmp)
            if r.returncode != 0:
                check(False, f"build step succeeds: {' '.join(cmd)}\n{r.stderr.strip()}")
                return
        r = subprocess.run([os.path.join(tmp, 'probe')], capture_output=True, text=True, timeout=60,
                           env=dict(os.environ, LD_LIBRARY_PATH=sc_lib))
        out = r.stdout + r.stderr
        check('same=1' in out, f"every translation unit sees the same endOfTestState ({out.strip()})")
        check('voters=2' in out, f"both voters land in that one instance ({out.strip()})")
        check(r.returncode == 0, f"the probe exits with status 0 (got {r.returncode})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    test_end_of_test_single_instance()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
