#!/usr/bin/env python3
"""seedRepro.py runs one simulation twice and compares the A2C_DIGEST lines.

With the same seed the command passes only when both runs pass, both print
digests, and every digest line matches. With --differ the second run takes
the other seed in the command's seed option, and the command passes only
when the lines differ. A run passes when it exits with status 0, prints a UVM
report summary, and has no UVM_ERROR or UVM_FATAL report or count, before or
after the summary. A paired port whose two lanes count different items fails the
run, and so do digests that all count none. Both runs' output goes
to stdout, and the last line is the verdict. Each case runs seedRepro.py over
a stand-in simulator whose environment says what it prints.
"""

import os
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
SEED_REPRO = os.path.join(base_dir, 'seedRepro.py')

# Prints two digest lines, port a then port b. Each digest is SIM_A or SIM_B,
# or the seed when that is unset, and b's adds the count of runs before this
# one when SIM_UNSTABLE is set. The seed is the value after --seed,
# -svseed or +ntb_random_seed=. SIM_ERRORS, SIM_EXIT, SIM_NO_SUMMARY and
# SIM_NO_DIGEST break the run in their own way, as SIM_LATE_ERROR does with
# a UVM_ERROR after the summary. SIM_ITEMS sets every digest's item count.
# With SIM_DUAL set, b also has a model lane line, of SIM_MODEL_ITEMS items.
# b's lines carry paired=SIM_PAIRED, 1 when that is unset; a's carry paired=0.
SIM = r'''#!/bin/sh
seed=""
while [ $# -gt 0 ]; do
    case $1 in
        --seed|-svseed) seed=$2; shift ;;
        --seed=*) seed=${1#--seed=} ;;
        +ntb_random_seed=*) seed=${1#+ntb_random_seed=} ;;
    esac
    shift
done
b=${SIM_B:-$seed}
if [ -n "$SIM_UNSTABLE" ]; then
    n=$(cat runs.txt 2>/dev/null || echo 0); echo $((n + 1)) > runs.txt; b=$((b + n))
fi
if [ -z "$SIM_NO_DIGEST" ]; then
    echo "UVM_INFO env.sv(1) @ 90: uvm_test_top.env.a_digest [A2C_DIGEST] A2C_DIGEST a DUT paired=0 items=${SIM_ITEMS:-4} digest=$(printf %016x ${SIM_A:-$seed})"
    echo "UVM_INFO env.sv(1) @ 90: uvm_test_top.env.b_digest [A2C_DIGEST] A2C_DIGEST b DUT paired=${SIM_PAIRED:-1} items=${SIM_ITEMS:-4} digest=$(printf %016x $b)"
    [ -n "$SIM_DUAL" ] && echo "UVM_INFO env.sv(1) @ 90: uvm_test_top.env.b_digest [A2C_DIGEST] A2C_DIGEST b model paired=${SIM_PAIRED:-1} items=${SIM_MODEL_ITEMS:-${SIM_ITEMS:-4}} digest=$(printf %016x $b)"
fi
if [ -z "$SIM_NO_SUMMARY" ]; then
    echo "--- UVM Report Summary ---"
    echo "UVM_ERROR :    ${SIM_ERRORS:-0}"
    echo "UVM_FATAL :    0"
    echo "[A2C_DIGEST]     2"
fi
[ -n "$SIM_LATE_ERROR" ] && echo "UVM_ERROR @ 100: uvm_test_top [LATE] reported after the summary"
exit ${SIM_EXIT:-0}
'''

# (label, seedRepro.py options, simulator arguments, environment, exit status, last line)
CASES = [
    ('the same seed, digests equal', [], ['--seed', '7'], {}, 0,
     'A2C_SEED_REPRO PASS: the digests match'),
    ('the same seed, = form', [], ['--seed=0x1f', '--verbosity=low'], {}, 0,
     'A2C_SEED_REPRO PASS: the digests match'),
    ('the same seed, the second digest line differs', [], ['--seed', '7'], {'SIM_UNSTABLE': '1'}, 1,
     'A2C_SEED_REPRO FAIL: the same seed gave different digests'),
    ('the same seed, a run with a UVM_ERROR', [], ['--seed', '7'], {'SIM_ERRORS': '1'}, 1,
     'A2C_SEED_REPRO FAIL: run 1 reported UVM_ERROR; run 2 reported UVM_ERROR'),
    ('the same seed, a run that exits with status 3', [], ['--seed', '7'], {'SIM_EXIT': '3'}, 1,
     'A2C_SEED_REPRO FAIL: run 1 exited with status 3; run 2 exited with status 3'),
    ('the same seed, a UVM_ERROR after the summary', [], ['--seed', '7'], {'SIM_LATE_ERROR': '1'}, 1,
     'A2C_SEED_REPRO FAIL: run 1 reported UVM_ERROR; run 2 reported UVM_ERROR'),
    ('the same seed, both lanes of a port', [], ['--seed', '7'], {'SIM_DUAL': '1'}, 0,
     'A2C_SEED_REPRO PASS: the digests match'),
    ('the same seed, lanes of a port with different item counts', [], ['--seed', '7'],
     {'SIM_DUAL': '1', 'SIM_MODEL_ITEMS': '0'}, 1,
     'A2C_SEED_REPRO FAIL: run 1: port b DUT lane saw 4 items, model lane 0; '
     'run 2: port b DUT lane saw 4 items, model lane 0'),
    ('the same seed, lanes of an unpaired port with different item counts', [], ['--seed', '7'],
     {'SIM_DUAL': '1', 'SIM_MODEL_ITEMS': '3', 'SIM_PAIRED': '0'}, 0,
     'A2C_SEED_REPRO PASS: the digests match'),
    ('the same seed, no UVM report summary', [], ['--seed', '7'], {'SIM_NO_SUMMARY': '1'}, 1,
     'A2C_SEED_REPRO FAIL: run 1 printed no UVM report summary; run 2 printed no UVM report summary'),
    ('the same seed, no digest', [], ['--seed', '7'], {'SIM_NO_DIGEST': '1'}, 1,
     'A2C_SEED_REPRO FAIL: run 1 printed no A2C_DIGEST line; run 2 printed no A2C_DIGEST line'),
    ('the same seed, digests of no transactions', [], ['--seed', '7'], {'SIM_ITEMS': '0'}, 1,
     'A2C_SEED_REPRO FAIL: run 1 printed only digests of no transactions; '
     'run 2 printed only digests of no transactions'),
    ('two seeds, digests that follow the seed', ['--differ', '8'], ['--seed', '7'], {}, 0,
     'A2C_SEED_REPRO PASS: the digests differ'),
    ('two seeds, only the second digest line follows the seed', ['--differ', '8'], ['--seed', '7'],
     {'SIM_A': '5'}, 0, 'A2C_SEED_REPRO PASS: the digests differ'),
    ('two seeds, digests that ignore the seed', ['--differ', '8'], ['--seed', '7'], {'SIM_A': '5', 'SIM_B': '6'}, 1,
     'A2C_SEED_REPRO FAIL: seed 8 gave the same digests as the first run, so the digests do not follow the stimulus'),
    ('two seeds, -svseed', ['--seed-arg=-svseed', '--differ', '2'], ['-svseed', '1'], {}, 0,
     'A2C_SEED_REPRO PASS: the digests differ'),
    ('two seeds, +ntb_random_seed=', ['--seed-arg=+ntb_random_seed', '--differ', '2'], ['+ntb_random_seed=1'], {},
     0, 'A2C_SEED_REPRO PASS: the digests differ'),
]

# (label, seedRepro.py options, simulator arguments, text the error must hold)
REJECTED = [
    ('a command with no seed', [], ['+UVM_TESTNAME=t'], 'the command has no --seed'),
    ('--differ with no seed to replace', ['--differ', '2'], ['-svseed', '1'], 'the command has no --seed for --differ'),
    ('--differ with the command\'s own seed', ['--differ', '7'], ['--seed', '7'], 'is the seed the command already has'),
]


def seed_repro(work, opts, args, env):
    return subprocess.run([sys.executable, SEED_REPRO] + opts + ['--', os.path.join(work, 'sim')] + args,
                          capture_output=True, text=True, cwd=work, env={**os.environ, **env})


def run_all_tests():
    print("\n" + "=" * 70)
    print("seedRepro.py TWO-RUN DIGEST COMPARISON")
    print("=" * 70)
    ok = True
    with tempfile.TemporaryDirectory(prefix='seedrepro_', dir=test_dir) as work:
        sim = os.path.join(work, 'sim')
        with open(sim, 'w') as f:
            f.write(SIM)
        os.chmod(sim, 0o755)
        for label, opts, args, env, status, verdict in CASES:
            if os.path.exists(os.path.join(work, 'runs.txt')):
                os.remove(os.path.join(work, 'runs.txt'))
            result = seed_repro(work, opts, args, env)
            lines = result.stdout.splitlines()
            # Both runs' output is kept: two run headers and two summaries.
            kept = (sum(line.startswith('A2C_SEED_REPRO run ') and ': ' in line for line in lines) == 2
                    and ('SIM_NO_SUMMARY' in env or result.stdout.count('--- UVM Report Summary ---') == 2))
            if result.returncode != status or not lines or lines[-1] != verdict or not kept:
                print(f"  FAIL: {label}: exit {result.returncode}, last line {lines[-1:]}, both runs kept {kept}; "
                      f"expected exit {status} and {verdict!r}\n{result.stdout}{result.stderr}")
                ok = False
            else:
                print(f"  PASS: {label}")
        for label, opts, args, text in REJECTED:
            result = seed_repro(work, opts, args, {})
            if result.returncode != 2 or text not in result.stderr or result.stdout:
                print(f"  FAIL: {label}: exit {result.returncode}, stdout {result.stdout!r}, "
                      f"stderr {result.stderr!r}; expected a usage error naming {text!r}")
                ok = False
            else:
                print(f"  PASS: {label} is rejected")
    if ok:
        print("\nPASS: seedRepro.py passes and fails on the digests of its two runs")
        return 0
    print("\nFAIL")
    return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
