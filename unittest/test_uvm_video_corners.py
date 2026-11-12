#!/usr/bin/env python3
"""The video corners are named in four places that no compiler ties together.

`a2c_video_cfg::corner_names()` in a2c_video_pkg.sv is what the A2C_CFG fatal
for an unknown corner lists. `a2c_video_corner_tests` in a2c_video_macros.svh
defines one test per corner. The corner table of specs/SIMULATOR_INTEGRATION.md
says which corners only a clocked or only a handshaked stream carries. The
loopback runs the tests its `// LB_TESTS` lines name, because
run_loopback.sh cannot see the classes a macro defines.

A corner added to the macro and missed in an LB_TESTS line is compiled and
never run, and the loopback still passes. So the check is that the four agree:
the macro and corner_names() list the same corners in the same order, the
spec's table has a row for each, and each loopback family's LB_TESTS line
lists, in that order, every corner its stream carries and no other.
"""

import os
import re
import sys

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

UVM_DIR = os.path.join(base_dir, 'common', 'systemVerilog', 'uvm')
PKG = os.path.join(UVM_DIR, 'a2c_video_pkg.sv')
MACROS = os.path.join(UVM_DIR, 'a2c_video_macros.svh')
LB_TESTS = os.path.join(UVM_DIR, 'loopback', 'a2c_video_lb_tests.svh')
SPEC = os.path.join(base_dir, 'specs', 'SIMULATOR_INTEGRATION.md')

# The loopback families with corner tests, by the stream their input carries:
# a is raw, fv and lv levels; b is axi4_stream and c rdy_vld, both handshaked.
# Each family runs once with fixed blanking and once with random (_rb_).
FAMILIES = {'a': 'clocked', 'b': 'handshaked', 'c': 'handshaked'}


def read(path):
    with open(path) as f:
        return f.read()


def corner_names():
    m = re.search(r'function void corner_names\(.*?\);\s*names\s*=\s*\'\{(.*?)\};', read(PKG), re.S)
    return re.findall(r'"(\w+)"', m.group(1)) if m else []


def macro_corners():
    m = re.search(r'`define a2c_video_corner_tests\(T\)(.*?)(?:\n\s*\n|`endif)', read(MACROS), re.S)
    return re.findall(r'`a2c_video_corner_test\(T,\s*(\w+)\)', m.group(1)) if m else []


def spec_kinds():
    """Corner -> 'clocked', 'handshaked' or 'both', from the spec's table."""
    kinds = dict()
    m = re.search(r'^\| Corner \|.*?\n((?:\|.*\n)+)', read(SPEC), re.M)
    if not m:
        return kinds
    for row in m.group(1).splitlines():
        cell = re.match(r'\|\s*`(\w+)`\s*\|(.*)\|\s*$', row)
        if not cell:
            continue
        text = cell.group(2)
        kinds[cell.group(1)] = ('clocked' if 'clocked only' in text
                                else 'handshaked' if 'handshaked only' in text else 'both')
    return kinds


def lb_lines():
    """LB_TESTS line prefix -> its corners, for the corner-test families."""
    lines = dict()
    for line in read(LB_TESTS).splitlines():
        m = re.match(r'\s*// LB_TESTS (lb_vid_[a-z]+(?:_rb)?_test)_\w+', line)
        if not m:
            continue
        prefix = m.group(1)
        lines[prefix] = [t[len(prefix) + 1:] for t in line.split()[2:]]
    return lines


def run_all_tests():
    problems = list()
    names = corner_names()
    macro = macro_corners()
    kinds = spec_kinds()
    if not names:
        problems.append(f"no corner_names() list found in {PKG}")
    if macro != names:
        problems.append(f"{MACROS} defines the corners {macro}, but corner_names() in {PKG} "
                        f"returns {names}; list the same corners in the same order in both")
    for c in names:
        if c not in kinds:
            problems.append(f"the corner table of {SPEC} has no row for corner {c}")
    for c in kinds:
        if c not in names:
            problems.append(f"the corner table of {SPEC} has a row for {c}, which corner_names() does not return")
    lines = lb_lines()
    for fam, stream in FAMILIES.items():
        want = [c for c in names if kinds.get(c, 'both') in ('both', stream)]
        for prefix in (f'lb_vid_{fam}_test', f'lb_vid_{fam}_rb_test'):
            got = lines.get(prefix)
            if got is None:
                problems.append(f"{LB_TESTS} has no LB_TESTS line for {prefix}_<corner>")
            elif got != want:
                problems.append(f"the LB_TESTS line of {prefix} lists {got}, but a {stream} stream carries "
                                f"{want}; a corner left out is defined and never run")
    for prefix in lines:
        if not any(prefix in (f'lb_vid_{f}_test', f'lb_vid_{f}_rb_test') for f in FAMILIES):
            problems.append(f"{LB_TESTS} has an LB_TESTS line for {prefix}, a family this check does not know; "
                            f"add it to FAMILIES with its stream kind")
    for problem in problems:
        print(f"  FAIL: {problem}")
    if problems:
        print(f"\nFAIL: {len(problems)} video corner list problem(s)")
        return 1
    print(f"PASS: the macro, corner_names() and the spec list the same {len(names)} corners, and the "
          f"{len(lines)} LB_TESTS lines list every corner their stream carries")
    return 0


if __name__ == '__main__':
    sys.exit(run_all_tests())
