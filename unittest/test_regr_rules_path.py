#!/usr/bin/env python3
"""A regression's rules files are found next to the regression JSON that names them.

`run.rules` lists the log-analysis rules files for each test. A relative entry is
relative to the regression JSON, so the same regression gives the same verdicts
whichever directory the launcher is started from; an absolute entry is used as
written. A value given with `--attr run.rules=` or `--attr run.rules+=` is a
list of files like the one in the JSON, and resolves the same way.

Each case writes a regression and its rules files into one directory, launches
from another, and runs a test whose log carries a line only the rules file can
turn into a failure. The verdict therefore shows whether that file was loaded.
"""

import json
import os
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
LAUNCHER = os.path.join(base_dir, 'regrLauncher.py')

# Fails a run whose log contains the marker line.
RULES = {
    'name': 'probe',
    'description': 'flags the probe marker',
    'filters': {'marker': {'re': r'^PROBE_MARKER$', 'msg': 'probe marker seen', 'file': '', 'sev': 'error'}},
    'modifiers': {},
}

# Matches nothing, so a run under it alone passes on exit status.
NO_RULES = {'name': 'none', 'description': 'no filters', 'filters': {}, 'modifiers': {}}

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def launch(regrDir, rulesEntry, extraArgs=()):
    regression = {
        'session': {'name': 'rulesPath', 'jobs': 1, 'lrp': 0},
        'build': {'command': 'true', 'timeout': 10},
        'run': {'command': 'echo', 'args': 'PROBE_MARKER', 'timeout': 10, 'rules': [rulesEntry],
                'count': 1, 'seed': 0, 'labels': [], 'test_group': {'markerTest': {}}},
    }
    regrPath = os.path.join(regrDir, 'regr_probe.json')
    with open(regrPath, 'w') as fh:
        json.dump(regression, fh)
    with tempfile.TemporaryDirectory(prefix='a2c_regr_cwd_') as cwd:
        return subprocess.run([sys.executable, LAUNCHER, '--dir', os.path.join(cwd, 'regr'), regrPath,
                               *extraArgs],
                              capture_output=True, text=True, timeout=120, cwd=cwd)


def test_rules_path_resolution():
    with tempfile.TemporaryDirectory(prefix='a2c_regr_rules_') as regrDir:
        os.mkdir(os.path.join(regrDir, 'rules'))
        rulesPath = os.path.join(regrDir, 'rules', 'probe.json')
        with open(rulesPath, 'w') as fh:
            json.dump(RULES, fh)
        with open(os.path.join(regrDir, 'none.json'), 'w') as fh:
            json.dump(NO_RULES, fh)
        # label -> (rules entry in the JSON, extra launcher args)
        cases = {
            'relative to the regression JSON': ('rules/probe.json', ()),
            'absolute': (rulesPath, ()),
            '--attr run.rules= with one file': ('none.json', ('--attr', 'run.rules=rules/probe.json')),
            '--attr run.rules+= with one file': ('none.json', ('--attr', 'run.rules+=rules/probe.json')),
        }
        for label, (entry, extraArgs) in cases.items():
            run = launch(regrDir, entry, extraArgs)
            output = run.stdout + run.stderr
            before = len(FAILURES)
            check('Error' not in output, f"{label}: the launcher raises no error from another cwd")
            check(run.returncode == 1 and 'Run session completed with failures' in output,
                  f"{label}: rules/probe.json is applied, so the marker fails the run (exit {run.returncode})")
            if len(FAILURES) > before:
                print(output)


if __name__ == '__main__':
    test_rules_path_resolution()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
