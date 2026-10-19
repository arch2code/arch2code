#!/usr/bin/env python3
"""Every interface type flagged `uvmAgent: true` ships its UVM agent package
and its X/Z checker.

A hasUvm block may use only interface types that carry the flag
(`validateUvmBlocks` in pysrc/processYaml.py), and the UVM testbench imports
`<type>_uvm_pkg` for each of them. The package is a hand-written companion in
the definition's own directory, so a flag without one passes `make db` and
fails only when a simulator compiles the testbench.

The HDL wrapper instantiates `<type>_xcheck` for every port of a flagged type.
VCS analyses it from the `interfaces/*/*_xcheck.sv` wildcard in a2c-vcs.mk and
Xcelium finds it through the `-y` directories in a2c.f, which match a module
to its file by name. A checker in a misnamed file, or in a directory a2c.f does
not search, fails only when a simulator elaborates the wrapper.

The simulators compile the agents from common/systemVerilog/uvm/a2c_uvm.f, so
that file must list every flagged type's package, after a2c_clk_if.sv and
a2c_uvm_pkg.sv, which the agents import.

A Pro type takes the same checks against Pro's lists: a2cPro.mk adds
pro/common/systemVerilog/uvm/a2cPro_uvm.f to A2C_LAYER_UVM_F_FILES, which
compiles after a2c_uvm.f, and pro/common/systemVerilog/a2cPro.f, whose -y
directories Xcelium searches, to A2C_LAYER_HDL_F_FILES.

Definitions are discovered by walking the shipped interface trees, so a newly
flagged type is checked without anyone adding it to a list.
"""

import os
import re
import sys

import yaml


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

UVM_DOT_F = os.path.join(base_dir, 'common', 'systemVerilog', 'uvm', 'a2c_uvm.f')
A2C_DOT_F = os.path.join(base_dir, 'common', 'systemVerilog', 'a2c.f')
# Every agent package imports these, so they come before the first agent.
SHARED = ('a2c_clk_if.sv', 'a2c_uvm_pkg.sv')

pro_dir = os.path.join(os.path.dirname(base_dir), 'pro')
# Each shipped interface tree, with the list its agent packages compile from
# and the list whose -y directories reach its checkers. pro is a separate
# repository, absent from a base-only checkout.
INTERFACE_ROOTS = (
    (os.path.join(base_dir, 'interfaces'), UVM_DOT_F, A2C_DOT_F),
    (os.path.join(pro_dir, 'interfaces'),
     os.path.join(pro_dir, 'common', 'systemVerilog', 'uvm', 'a2cPro_uvm.f'),
     os.path.join(pro_dir, 'common', 'systemVerilog', 'a2cPro.f')),
)


def flagged_definitions():
    """(interface type, definition file, agent list, checker list) for every
    flagged shipped type."""
    found = list()
    for root, uvmDotF, hdlDotF in INTERFACE_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for name in sorted(filenames):
                if not name.endswith('.yaml'):
                    continue
                path = os.path.join(dirpath, name)
                with open(path) as f:
                    content = yaml.safe_load(f)
                for intfType, definition in (content.get('interface_defs') or {}).items():
                    if definition.get('uvmAgent'):
                        found.append((intfType, path, uvmDotF, hdlDotF))
    return found


def run_all_tests():
    flagged = flagged_definitions()
    if not flagged:
        print("FAIL: no shipped interface definition carries uvmAgent: true; "
              "the discovery walk found nothing to check")
        return 1
    missing = list()
    for intfType, path, _uvmDotF, _hdlDotF in flagged:
        pkg = os.path.join(os.path.dirname(path), f'{intfType}_uvm_pkg.sv')
        if os.path.isfile(pkg):
            print(f"  PASS: {intfType} ({os.path.relpath(path, base_dir)}) ships {os.path.basename(pkg)}")
        else:
            missing.append((intfType, path, pkg))
    for intfType, path, pkg in missing:
        print(f"  FAIL: interface type '{intfType}' ({path}) declares uvmAgent: true "
              f"but {pkg} does not exist. The UVM testbench imports {intfType}_uvm_pkg "
              f"for every port of this type. Add the agent package beside the "
              f"definition, or remove the flag.")
    if missing:
        print(f"\nFAIL: {len(missing)} flagged interface type(s) without an agent package")
        return 1
    print(f"\nPASS: all {len(flagged)} flagged interface types ship their agent package")
    absent = sorted({(dotF, intfType, role) for intfType, _path, uvmDotF, hdlDotF in flagged
                     for dotF, role in ((uvmDotF, 'agent package'), (hdlDotF, 'X/Z checker directory'))
                     if not os.path.isfile(dotF)})
    for dotF, intfType, role in absent:
        print(f"  FAIL: {dotF} does not exist. A flagged type's {role} must be named in its "
              f"interface root's list, and '{intfType}' is flagged. Restore the list, or "
              f"remove the flag.")
    if absent:
        print(f"\nFAIL: {len(absent)} list(s) for flagged interface types are missing")
        return 1
    return check_dot_f(flagged) | check_xcheck(flagged)


def dot_f_entries(dotF):
    """The resolved paths a .f list names, relative to its own directory."""
    fDir = os.path.dirname(dotF)
    with open(dotF) as f:
        return [os.path.realpath(os.path.join(fDir, line.strip())) for line in f if line.strip()]


def check_dot_f(flagged):
    """Each flagged type's agent list names its package, and a2c_uvm.f lists
    the shared files before every agent package it names."""
    problems = list()
    agentPositions = list()
    for intfType, path, uvmDotF, _hdlDotF in flagged:
        entries = dot_f_entries(uvmDotF)
        pkg = os.path.realpath(os.path.join(os.path.dirname(path), f'{intfType}_uvm_pkg.sv'))
        if pkg not in entries:
            problems.append(f"{uvmDotF} does not list {pkg}. The simulators compile the "
                            f"agents from this file, so a testbench with a '{intfType}' port "
                            f"would not find {intfType}_uvm_pkg. Add the package to it.")
        elif uvmDotF == UVM_DOT_F:
            agentPositions.append(entries.index(pkg))
    entries = dot_f_entries(UVM_DOT_F)
    for name in SHARED:
        shared = os.path.realpath(os.path.join(os.path.dirname(UVM_DOT_F), name))
        if shared not in entries:
            problems.append(f"{UVM_DOT_F} does not list {name}, which every agent imports.")
        elif agentPositions and entries.index(shared) > min(agentPositions):
            problems.append(f"{UVM_DOT_F} lists {name} after an agent package. Every agent "
                            f"imports it, so it must come first.")
    for problem in problems:
        print(f"  FAIL: {problem}")
    if problems:
        print(f"\nFAIL: the agent lists are missing or misorder {len(problems)} file(s)")
        return 1
    print(f"PASS: a2c_uvm.f lists {', '.join(SHARED)} first, and the agent lists name "
          f"all {len(flagged)} agent packages")
    return 0


def check_xcheck(flagged):
    """Each flagged type ships <type>_xcheck.sv declaring module <type>_xcheck,
    in a directory its checker list searches with -y."""
    problems = list()
    for intfType, path, _uvmDotF, hdlDotF in flagged:
        fDir = os.path.dirname(hdlDotF)
        with open(hdlDotF) as f:
            searched = [os.path.realpath(os.path.join(fDir, line.split(None, 1)[1].strip()))
                        for line in f if line.startswith('-y ')]
        module = f'{intfType}_xcheck'
        checker = os.path.join(os.path.dirname(path), f'{module}.sv')
        if not os.path.isfile(checker):
            problems.append(f"interface type '{intfType}' ({path}) declares uvmAgent: true "
                            f"but {checker} does not exist. The HDL wrapper instantiates "
                            f"{module} for every port of this type. Add the checker beside "
                            f"the definition, or remove the flag.")
            continue
        with open(checker) as f:
            declared = re.findall(r'^\s*module\s+(\w+)', f.read(), re.MULTILINE)
        if declared != [module]:
            problems.append(f"{checker} declares {declared or 'no module'}, not exactly "
                            f"'{module}'. Xcelium finds the checker by its file name, so "
                            f"the file must declare that one module.")
        if os.path.realpath(os.path.dirname(checker)) not in searched:
            problems.append(f"{hdlDotF} has no -y for {os.path.dirname(checker)}, so "
                            f"Xcelium cannot find {module}. Add the directory to it.")
    for problem in problems:
        print(f"  FAIL: {problem}")
    if problems:
        print(f"\nFAIL: {len(problems)} X/Z checker problem(s)")
        return 1
    print(f"PASS: all {len(flagged)} flagged interface types ship an X/Z checker their list's -y can find")
    return 0


if __name__ == '__main__':
    sys.exit(run_all_tests())
