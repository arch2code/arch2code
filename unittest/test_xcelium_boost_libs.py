#!/usr/bin/env python3
"""The Xcelium link reads BOOST_LIBS, so USE_XCELIUM=1 keeps the LD_BOOST check.

Dry runs in a private copy of examples/simple_ip, with LD_BOOST and BOOST_LIBS
taken from the test alone, never from the caller's shell:
- neither set: make stops with "LD_BOOST is not set";
- BOOST_LIBS set, LD_BOOST unset: no error, and XRUN_LD_LIBS carries the
  caller's BOOST_LIBS;
- LD_BOOST set, BOOST_LIBS unset: XRUN_LD_LIBS carries the default Boost link
  inputs, -L joined to LD_BOOST.

The dry runs pass placeholder XCELIUM_TOOLS and XRUN_GCC_VERS, so they need
no Xcelium install.
"""

import os
import re
import subprocess
import sys

from test_file_prefix import copy_simple_ip
from _tmp_helpers import remove_tree

XRUN_ARGS = ['USE_XCELIUM=1', 'XCELIUM_TOOLS=/hook/xcelium', 'XRUN_GCC_VERS=hook']
PRINT_LIBS = 'pxl: ; @echo "XRUN_LD_LIBS=[$(XRUN_LD_LIBS)]"'


def dryRun(rundir, boost):
    e = os.environ.copy()
    e['NO_COLOR'] = '1'
    e.pop('LD_BOOST', None)
    e.pop('BOOST_LIBS', None)
    e.update(boost)
    return subprocess.run(['make', '-C', rundir, '--no-print-directory', '-n', *XRUN_ARGS,
                           '--eval', PRINT_LIBS, 'pxl'],
                          capture_output=True, text=True, timeout=3600, env=e)


def xrunLdLibs(result):
    found = re.findall(r'XRUN_LD_LIBS=\[([^\]]*)\]', result.stdout)
    return found[0].split() if len(found) == 1 else None


def main():
    work = copy_simple_ip()
    try:
        rundir = os.path.join(work, 'rundir')
        failures = []

        result = dryRun(rundir, {})
        if result.returncode == 0 or 'LD_BOOST is not set' not in result.stderr:
            failures.append(f"neither set: make did not stop on LD_BOOST "
                            f"(exit {result.returncode}):\n{result.stdout}{result.stderr}")

        result = dryRun(rundir, {'BOOST_LIBS': '-lboost_program_options -L/x'})
        libs = xrunLdLibs(result)
        if result.returncode != 0 or libs is None or '-Wld,-L/x' not in libs:
            failures.append(f"BOOST_LIBS set: XRUN_LD_LIBS lacks -Wld,-L/x "
                            f"(exit {result.returncode}):\n{result.stdout}{result.stderr}")

        result = dryRun(rundir, {'LD_BOOST': '/x'})
        libs = xrunLdLibs(result)
        if (result.returncode != 0 or libs is None or '-Wld,-L' in libs
                or '-Wld,-lboost_program_options -Wld,-L/x' not in ' '.join(libs)):
            failures.append(f"LD_BOOST set: XRUN_LD_LIBS is not the default Boost link "
                            f"(exit {result.returncode}):\n{result.stdout}{result.stderr}")

        if failures:
            for failure in failures:
                print(f"FAIL: {failure}")
            print("SOME TESTS FAILED")
            return 1
        print("PASS: USE_XCELIUM=1 requires LD_BOOST unless BOOST_LIBS is set, "
              "and XRUN_LD_LIBS carries the Boost link inputs")
        print("ALL TESTS PASSED")
        return 0
    finally:
        remove_tree(work)


if __name__ == '__main__':
    sys.exit(main())
