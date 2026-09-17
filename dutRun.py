#!/usr/bin/env python3
"""Run a test on the simulator snapshot that matches its DUT topology.

VCS and Xcelium fix the SystemC topology of a snapshot at elaboration, so the
simulator flows build one snapshot per topology (vcs_snapshots, xrun_snapshots)
and a regression file keeps a single run command: it names the base binary and
the test's own --vlInst/--vlType/--vlTandem arguments select the snapshot
<base>_<topology>. The topology name follows DUT_TOPOLOGY in a2c-systemc.mk:
<inst>_<type>[_tandem], dots kept as-is since they are legal in file/target
names, and `model` for a test without --vlInst. A model test with --vlInst and
without --vlTandem is not a listed topology and runs on `model` as well.

usage: dutRun.py <base binary> <simulation arguments...>
"""
import os
import sys


def option(args, name):
    for i, arg in enumerate(args):
        if arg == name and i + 1 < len(args):
            return args[i + 1]
        if arg.startswith(name + '='):
            return arg[len(name) + 1:]
    return None


def topology(args):
    inst = option(args, '--vlInst')
    vlType = option(args, '--vlType') or 'verif'
    tandem = '--vlTandem' in args
    if inst is None or (vlType != 'verif' and not tandem):
        return 'model'
    return f"{inst}_{vlType}{'_tandem' if tandem else ''}"


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    base, args = sys.argv[1], sys.argv[2:]
    binary = f'{base}_{topology(args)}'
    if not os.access(binary, os.X_OK):
        sys.exit(f'dutRun: no snapshot {binary} for arguments {" ".join(args)}; '
                 f'build it with the vcs_snapshots or xrun_snapshots target')
    # simv warns RT_UO for every a2c option it does not know; the warnings are
    # harmless and a2c parses those options itself.
    os.execv(binary, [binary] + args)


if __name__ == '__main__':
    main()
