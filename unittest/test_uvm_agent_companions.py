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

# pro is a separate repository, absent from a base-only checkout.
INTERFACE_ROOTS = (
    os.path.join(base_dir, 'interfaces'),
    os.path.join(os.path.dirname(base_dir), 'pro', 'interfaces'),
)


def flagged_definitions():
    """(interface type, definition file) for every flagged shipped type."""
    found = list()
    for root in INTERFACE_ROOTS:
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
                        found.append((intfType, path))
    return found


def run_all_tests():
    flagged = flagged_definitions()
    if not flagged:
        print("FAIL: no shipped interface definition carries uvmAgent: true; "
              "the discovery walk found nothing to check")
        return 1
    missing = list()
    for intfType, path in flagged:
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
    return check_dot_f(flagged) | check_xcheck(flagged)


def check_dot_f(flagged):
    """a2c_uvm.f lists the shared files, then every flagged type's package."""
    fDir = os.path.dirname(UVM_DOT_F)
    with open(UVM_DOT_F) as f:
        entries = [os.path.realpath(os.path.join(fDir, line.strip()))
                   for line in f if line.strip()]
    problems = list()
    agentPositions = list()
    for intfType, path in flagged:
        pkg = os.path.realpath(os.path.join(os.path.dirname(path), f'{intfType}_uvm_pkg.sv'))
        if pkg in entries:
            agentPositions.append(entries.index(pkg))
        else:
            problems.append(f"{UVM_DOT_F} does not list {pkg}. The simulators compile the "
                            f"agents from this file, so a testbench with a '{intfType}' port "
                            f"would not find {intfType}_uvm_pkg. Add the package to it.")
    for name in SHARED:
        shared = os.path.realpath(os.path.join(fDir, name))
        if shared not in entries:
            problems.append(f"{UVM_DOT_F} does not list {name}, which every agent imports.")
        elif agentPositions and entries.index(shared) > min(agentPositions):
            problems.append(f"{UVM_DOT_F} lists {name} after an agent package. Every agent "
                            f"imports it, so it must come first.")
    for problem in problems:
        print(f"  FAIL: {problem}")
    if problems:
        print(f"\nFAIL: a2c_uvm.f is missing or misorders {len(problems)} file(s)")
        return 1
    print(f"PASS: a2c_uvm.f lists {', '.join(SHARED)} and then all {len(flagged)} agent packages")
    return 0


def check_xcheck(flagged):
    """Each flagged type ships <type>_xcheck.sv declaring module <type>_xcheck,
    in a directory a2c.f searches with -y."""
    fDir = os.path.dirname(A2C_DOT_F)
    with open(A2C_DOT_F) as f:
        searched = [os.path.realpath(os.path.join(fDir, line.split(None, 1)[1].strip()))
                    for line in f if line.startswith('-y ')]
    problems = list()
    for intfType, path in flagged:
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
            problems.append(f"{A2C_DOT_F} has no -y for {os.path.dirname(checker)}, so "
                            f"Xcelium cannot find {module}. Add the directory to it.")
    for problem in problems:
        print(f"  FAIL: {problem}")
    if problems:
        print(f"\nFAIL: {len(problems)} X/Z checker problem(s)")
        return 1
    print(f"PASS: all {len(flagged)} flagged interface types ship an X/Z checker a2c.f can find")
    return 0


if __name__ == '__main__':
    sys.exit(run_all_tests())
