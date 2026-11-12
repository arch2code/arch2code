#!/usr/bin/env python3
"""Run one simulation command twice and compare the A2C_DIGEST lines of the two runs.

Each run passes when it exits with status 0, its output holds a UVM report
summary, and it has no UVM_ERROR or UVM_FATAL report and no non-zero count of
either, before or after the summary. The command passes when both runs pass,
both print A2C_DIGEST lines with a transaction on at least one port and the
same item count on both lanes of every port that reports two with paired=1,
and the lines are the same in both runs. A port prints paired=1 when its
Mode B comparator paired every item of one lane with one of the other; one
that compares only some items, such as a status port under the stable
policy, or whose comparator an end-of-test cut left holding items, may see
more items on one lane in a correct run.
With --differ, the second run takes that seed in place of the command's own,
and the command passes only when the lines differ, which shows the digests
see the stimulus the seed draws.

The command must carry its seed as --seed N or --seed=N, or under the option
--seed-arg names. A regression file gives it the seed regrLauncher.py
resolved, so a seed of `random` is repeated as the value the launcher drew.
Both runs' output goes to stdout as it arrives, each after an A2C_SEED_REPRO
line naming its command, so the launcher's log keeps both, and keeps what a
run printed before a launcher timeout killed it. The verdict is the last line.

usage: seedRepro.py [--differ SEED] [--seed-arg OPTION] command...
"""
import argparse
import re
import subprocess
import sys

DIGEST = re.compile(r'\[A2C_DIGEST\] (A2C_DIGEST (\S+) (\S+) paired=([01]) items=(\d+) .*)$', re.MULTILINE)
SUMMARY = '--- UVM Report Summary ---'
# A report, which has no ' :' after the severity, or a summary count above 0.
UVM_FAILURE = re.compile(r'^UVM_(ERROR|FATAL)(?: (?!:)| :\s+[1-9])', re.MULTILINE)


def with_seed(command, option, seed):
    """command with the value of its first seed option replaced by seed."""
    for i, arg in enumerate(command):
        if arg == option and i + 1 < len(command):
            return command[:i + 1] + [seed] + command[i + 2:]
        if arg.startswith(option + '='):
            return command[:i] + [f'{option}={seed}'] + command[i + 1:]
    return None


def run(index, command):
    """Runs command, echoes its output, and returns (failure reason or None, digest lines)."""
    print(f"A2C_SEED_REPRO run {index}: {' '.join(command)}", flush=True)
    output = []
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          errors='replace') as proc:
        for line in proc.stdout:
            sys.stdout.write(line)
            output.append(line)
    sys.stdout.flush()
    text = ''.join(output)
    if proc.returncode != 0:
        return f'run {index} exited with status {proc.returncode}', []
    if SUMMARY not in text:
        return f'run {index} printed no UVM report summary', []
    failure = UVM_FAILURE.search(text)
    if failure:
        return f'run {index} reported UVM_{failure.group(1)}', []
    digests = DIGEST.findall(text)
    if not digests:
        return f'run {index} printed no A2C_DIGEST line', []
    # Digests that saw nothing match whatever the seed, so they prove nothing.
    if all(items == '0' for _, _, _, _, items in digests):
        return f'run {index} printed only digests of no transactions', []
    # A lane whose monitor feeds no digest hashes nothing, which a repeat of
    # the run cannot reveal.
    lanes = {}
    for _, port, lane, paired, items in digests:
        if paired == '1':
            lanes.setdefault(port, {})[lane] = items
    for port, counts in lanes.items():
        if len(counts) == 2 and counts['DUT'] != counts['model']:
            return f"run {index}: port {port} DUT lane saw {counts['DUT']} items, model lane {counts['model']}", []
    return None, [line for line, _, _, _, _ in digests]


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], allow_abbrev=False)
    parser.add_argument('--differ', metavar='SEED',
                        help='seed of the second run; the digests must then differ')
    parser.add_argument('--seed-arg', default='--seed', metavar='OPTION',
                        help='the option that carries the seed in the command (default --seed)')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('no command')
    second = command
    if args.differ is not None:
        second = with_seed(command, args.seed_arg, args.differ)
        if second is None:
            parser.error(f'the command has no {args.seed_arg} for --differ to replace')
        if second == command:
            parser.error(f'--differ {args.differ} is the seed the command already has')
    elif with_seed(command, args.seed_arg, '') is None:
        parser.error(f'the command has no {args.seed_arg}, so the two runs would not share a stated seed')

    failures = []
    digests = []
    for index, cmd in ((1, command), (2, second)):
        failure, lines = run(index, cmd)
        if failure:
            failures.append(failure)
        digests.append(lines)
    if failures:
        print(f"A2C_SEED_REPRO FAIL: {'; '.join(failures)}")
        sys.exit(1)
    for line in digests[0]:
        print(f'A2C_SEED_REPRO run 1 {line}')
    for line in digests[1]:
        print(f'A2C_SEED_REPRO run 2 {line}')
    same = digests[0] == digests[1]
    if args.differ is None and not same:
        print('A2C_SEED_REPRO FAIL: the same seed gave different digests')
        sys.exit(1)
    if args.differ is not None and same:
        print(f'A2C_SEED_REPRO FAIL: seed {args.differ} gave the same digests as the first run, '
              'so the digests do not follow the stimulus')
        sys.exit(1)
    print('A2C_SEED_REPRO PASS: ' + ('the digests differ' if args.differ is not None else 'the digests match'))


if __name__ == '__main__':
    main()
