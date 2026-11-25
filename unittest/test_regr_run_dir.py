#!/usr/bin/env python3
"""Each run command finds its own run directory in RL_RUN_DIR.

Every run starts in the directory the launcher runs from, so a run that writes
a file of its own, such as a UVM_COV=1 coverage database, needs the path of
its run_<rid> directory to keep parallel runs apart. The launcher puts it in
RL_RUN_DIR.

Two runs of one test each write a marker into RL_RUN_DIR; each marker must
land in that run's own run_<rid> directory, under the session's runs/ tree.
"""

import glob
import json
import os
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
LAUNCHER = os.path.join(base_dir, 'regrLauncher.py')

NO_RULES = {'name': 'none', 'description': 'no filters', 'filters': {}, 'modifiers': {}}


def main():
    with tempfile.TemporaryDirectory(prefix='a2c_regr_run_dir_') as work:
        with open(os.path.join(work, 'none.json'), 'w') as fh:
            json.dump(NO_RULES, fh)
        # The launcher expands $NAME in the command text when it queues the
        # run, so the run reads RL_RUN_DIR from a script.
        script = os.path.join(work, 'mark.sh')
        with open(script, 'w') as fh:
            fh.write('touch "$RL_RUN_DIR/marker"\n')
        regression = {
            'session': {'name': 'runDir', 'jobs': 2, 'lrp': 0},
            'build': {'command': 'true', 'timeout': 10},
            'run': {'command': f'sh {script}', 'args': '', 'timeout': 10,
                    'rules': ['none.json'], 'count': 2, 'seed': 0, 'labels': [],
                    'test_group': {'markerTest': {}}},
        }
        regrPath = os.path.join(work, 'regr_run_dir.json')
        with open(regrPath, 'w') as fh:
            json.dump(regression, fh)
        run = subprocess.run([sys.executable, LAUNCHER, '--dir', os.path.join(work, 'regr'), regrPath],
                             capture_output=True, text=True, timeout=120, cwd=work)
        # runs/run_<rid> is a symlink to runs/<test path>/run_<rid>.
        markers = sorted(m for m in glob.glob(os.path.join(work, 'regr', '*', 'runs', '**', 'marker'), recursive=True)
                         if not os.path.islink(os.path.dirname(m)))
        runDirs = sorted(os.path.dirname(m) for m in markers)
        ok = (run.returncode == 0 and len(markers) == 2 and len(set(runDirs)) == 2
              and all(os.path.basename(d).startswith('run_') for d in runDirs)
              and not os.path.exists(os.path.join(work, 'marker')))
        print(f"  {'PASS' if ok else 'FAIL'}: each of two runs writes its marker in its own run_<rid> directory "
              f"(exit {run.returncode}, markers {[os.path.relpath(m, work) for m in markers]})")
        if not ok:
            print(run.stdout + run.stderr)
            print("\n  SOME TESTS FAILED (1)")
            return 1
    print("\n  ALL TESTS PASSED!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
