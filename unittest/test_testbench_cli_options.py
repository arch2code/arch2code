#!/usr/bin/env python3
"""--param and the verbosity options either take effect or stop the run.

A testbench registers each --param key with a value that is both its default
and its maximum. A value given on the command line, up to that maximum, is the
user's explicit choice for that run, so it replaces the default. A key may be
given once, from the command line or the config file, so no precedence rule
between two values is needed.

Anything else is a mistyped option and the run exits with status 2: an
unregistered key, a key given twice, a value that is not a non-negative
integer, or a verbosity spelling the logger cannot decode. A run that simulated
with the default instead would report a pass for a configuration nobody asked
for. The messages name the accepted keys or spellings where there is a list.

The probe runs the shipped sc_main with a testbench that registers foo=3 and
zero=0 and prints the value of foo it sees.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from test_watchdog_no_terminator import buildProbe

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
FIXTURE = os.path.join(test_dir, 'fixtures', 'testbench-cli', 'testbench_cli_probe.cpp')
MAIN_CPP = os.path.join(base_dir, 'common', 'scmain', 'main.cpp')

LEVELS = ('low', 'medium', 'high', 'full')
NOT_INT = 'is not a non-negative integer'

# (args, config file text or None) -> (exit status, output that must be present, output that must be absent)
SCENARIOS = {
    ((), None): (0, ('foo=3',), ()),
    (('--param', 'foo,2'), None): (0, ('foo=2',), ('foo=3',)),
    (('--param', 'foo,0'), None): (0, ('foo=0',), ('foo=3',)),
    (('--param', 'foo,4'), None): (2, ('exceeds maximum value 3',), ('foo=', 'Ignoring')),
    (('--param', 'bar,1'), None): (2, ('bar', 'Valid parameters: foo'), ('foo=', 'Ignoring')),
    (('--param', 'zero,1'), None): (2, ('zero', 'cannot be set'), ('foo=',)),
    (('--param', 'foo'), None): (2, ('Invalid parameter format: foo', 'key,value'), ('foo=',)),
    (('--param', 'foo,'), None): (2, ('foo has no value',), ('foo=',)),
    (('--param', 'foo,5abc'), None): (2, ("'5abc' " + NOT_INT,), ('foo=',)),
    (('--param', 'foo,-1'), None): (2, ("'-1' " + NOT_INT,), ('foo=',)),
    (('--param', 'foo,1', '--param', 'foo,2'), None): (2, ('foo is given more than once',), ('foo=',)),
    (('--param', 'foo,2'), 'param = foo,1\n'): (2, ('foo is given more than once',), ('foo=',)),
    ((), 'param = foo,1\n'): (0, ('foo=1',), ()),
    (('--verbosity', 'BOGUS'), None): (2, ('BOGUS',) + LEVELS, ('foo=', 'Using default')),
    (('--verbosity', 'high'), None): (0, ('foo=3',), ('Invalid verbosity',)),
    (('--instVerbosity', 'BOGUS'), None): (2, ("Invalid instVerbosity 'BOGUS'",) + LEVELS, ('foo=',)),
    ((), 'blockVerbosity = harness BOGUS\n'): (2, ('BOGUS', 'harness') + LEVELS, ('foo=', 'Using default')),
    ((), 'blockVerbosity = harness full\n'): (0, ('foo=3',), ('Invalid block verbosity',)),
}

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_testbench_cli_options():
    scLibdir = os.environ.get('SYSTEMC_LIBDIR', '')
    tmpdir = tempfile.mkdtemp(prefix='a2c_testbench_cli_')
    try:
        # buildProbe writes the probe into tmpdir, so its quoted include of
        # main.cpp resolves to this copy of the file under test.
        shutil.copy(MAIN_CPP, tmpdir)
        with open(FIXTURE) as fh:
            binPath = buildProbe(tmpdir, fh.read())
        if not os.path.isfile(binPath):
            check(False, f"testbench CLI probe must build and link: {binPath}")
            return
        cfgPath = os.path.join(tmpdir, 'probe.cfg')
        for (args, cfg), (status, present, absent) in SCENARIOS.items():
            cmd = [binPath, 'paramProbe', '--scTimeLimit', '1000', *args]
            label = ' '.join(('paramProbe',) + args)
            if cfg is not None:
                with open(cfgPath, 'w') as fh:
                    fh.write(cfg)
                cmd += ['--config', cfgPath]
                label += f" with config {cfg.strip()!r}"
            run = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=tmpdir,
                                 env=dict(os.environ, LD_LIBRARY_PATH=scLibdir))
            output = run.stdout + run.stderr
            before = len(FAILURES)
            check(run.returncode == status, f"{label} exits with status {status} (got {run.returncode})")
            for needle in present:
                check(needle in output, f"{label} prints {needle!r}")
            for needle in absent:
                check(needle not in output, f"{label} does not print {needle!r}")
            if len(FAILURES) > before:
                print(output)
    finally:
        shutil.rmtree(tmpdir)


if __name__ == '__main__':
    test_testbench_cli_options()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
