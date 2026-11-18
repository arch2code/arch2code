#!/usr/bin/env python3
"""The UVM library lints, and its loopback testbench and the generated UVM
packages of examples/uvmMem, uvmRegs and uvmVideo parse, with no simulator
licence.

Verilator parses each against the open-source Accellera UVM 1.2 that
UVM_HOME names (its src/ holds uvm_pkg.sv); the VCS and Xcelium copies of
UVM encrypt some files, which Verilator cannot read. With UVM_HOME unset the
check is skipped.

The parse resolves macros, includes and package imports, so it finds syntax
errors, an undefined macro, a missing include and an import of an unknown
package, in hand-written and generated SV alike. The library, every package
a2c_uvm.f lists, also gets Verilator's full lint, which adds undeclared
names, wrong argument counts and type mismatches, in parameterized classes
too. The loopback and the generated packages stop at the parse, because the
lint rejects :: through a typedef of a parameterized class's type member,
which both simulators accept and every generated env package uses.

A generated test package imports the env package A2C_UVM_PKG names, so each
example parses on its own with that define set to its env package.

The agents' coverage subscribers exist only under A2C_UVM_COV, so the library
is parsed once with it defined and once without.
"""

import glob
import os
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)

UVM_DIR = os.path.join(base_dir, 'common', 'systemVerilog', 'uvm')
LOOPBACK_DIR = os.path.join(UVM_DIR, 'loopback')
EXAMPLES = ('uvmMem', 'uvmRegs', 'uvmVideo')


def uvm_src():
    """The src/ directory of UVM_HOME, or None with the reason."""
    home = os.environ.get('UVM_HOME')
    if not home:
        return None, 'UVM_HOME is not set'
    src = os.path.join(home, 'src')
    pkg = os.path.join(src, 'uvm_pkg.sv')
    if not os.path.isfile(pkg):
        return None, f'UVM_HOME {home} has no src/uvm_pkg.sv'
    return src, ''


def layer_sources(f_list):
    """The files a UVM .f list names, each agent package after its
    <type>_if.sv, as run_loopback.sh compiles them."""
    d = os.path.dirname(f_list)
    files = []
    for name in open(f_list).read().split():
        if name.endswith('_uvm_pkg.sv') and name != 'a2c_uvm_pkg.sv':
            files.append(os.path.join(d, name[:-len('_uvm_pkg.sv')] + '_if.sv'))
    return files + [os.path.join(d, name) for name in open(f_list).read().split()]


def protected_files(src):
    """UVM files under src that carry an encrypted block."""
    found = []
    for path in glob.glob(os.path.join(src, '**', '*.sv*'), recursive=True):
        with open(path, errors='replace') as f:
            if 'pragma protect' in f.read():
                found.append(path)
    return found


def parse(label, src, files, incdirs, defines=(), lint=False):
    """Whether Verilator parses, or with lint lints, UVM and files with no
    error; prints the verdict, and Verilator's errors on a failure."""
    cmd = ['verilator', '--lint-only'] + ([] if lint else ['--debug-exit-parse'])
    # IMPURE is a limit of Verilator's scheduler on a function that writes
    # outside its scope, not an SV error.
    cmd += ['--timing', '-Wno-fatal', '-Wno-lint', '-Wno-style', '-Wno-IMPURE', '+define+UVM_NO_DPI', f'+incdir+{src}']
    cmd += [f'+incdir+{d}' for d in incdirs] + [f'+define+{d}' for d in defines]
    cmd += [os.path.join(src, 'uvm_pkg.sv')] + list(files)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    errors = [line for line in (result.stdout + result.stderr).splitlines() if line.startswith('%Error')]
    if result.returncode != 0 or errors:
        print(f'FAIL: {label}: {"lint" if lint else "parse"} errors (verilator exit {result.returncode}):')
        for line in errors or (result.stdout + result.stderr).splitlines()[-20:]:
            print(f'    {line}')
        return False
    print(f'PASS: {label}: no {"lint" if lint else "parse"} error in {len(files)} files')
    return True


def prove_parse(src, library):
    """Whether the parse fails on a planted syntax error in a library
    package, so a pass is not an empty run."""
    with tempfile.TemporaryDirectory() as tmp:
        planted = os.path.join(tmp, 'planted_pkg.sv')
        with open(planted, 'w') as f:
            f.write('package planted_pkg;\n    import a2c_uvm_pkg::*;\n'
                    '    function automatic int f(); return 1 endfunction\nendpackage\n')
        cmd = ['verilator', '--lint-only', '--debug-exit-parse', '--timing', '-Wno-fatal',
               '+define+UVM_NO_DPI', f'+incdir+{src}', f'+incdir+{UVM_DIR}',
               os.path.join(src, 'uvm_pkg.sv')] + library + [planted]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode == 0 or 'planted_pkg.sv:3' not in result.stdout + result.stderr:
        print('FAIL: the parse passed a package with a missing semicolon')
        return False
    print('PASS: the parse fails on a planted syntax error')
    return True


def example_sources(name):
    """An example's RTL packages from its rtl.f, then its generated UVM env
    package, test package and testbench, and the env package's name."""
    root = os.path.join(base_dir, 'examples', name)
    rtl = os.path.join(root, 'rtl')
    files = []
    for line in open(os.path.join(rtl, 'rtl.f')):
        line = line.strip()
        if line and not line.startswith(('+', '//', '-')):
            files.append(os.path.join(rtl, line))
    uvm = os.path.join(root, 'uvm')
    env_pkg = os.path.join(uvm, f'{name}_uvm_pkg.sv')
    files += [env_pkg, os.path.join(uvm, f'{name}_uvm_test_pkg.sv'), os.path.join(uvm, f'{name}_uvm_tb.sv')]
    return files, f'{name}_uvm_pkg'


def main():
    src, why = uvm_src()
    if src is None:
        print(f'SKIP: {why}, so the UVM library is not linted and no UVM SV is parsed. Set UVM_HOME to an '
              f'unpacked Accellera UVM 1.2 release, the directory whose src/ holds uvm_pkg.sv.')
        print('ALL TESTS PASSED')
        return 0
    encrypted = protected_files(src)
    if encrypted:
        print(f'FAIL: UVM_HOME {os.path.dirname(src)} holds encrypted files, such as {encrypted[0]}, which '
              f'Verilator cannot parse; set it to an Accellera UVM 1.2 release')
        print('SOME TESTS FAILED')
        return 1
    library = layer_sources(os.path.join(UVM_DIR, 'a2c_uvm.f'))
    common = os.path.dirname(UVM_DIR)
    ok = prove_parse(src, library)
    ok = parse('the UVM library', src, library, [common, UVM_DIR], lint=True) and ok
    ok = parse('the UVM library and its loopback testbench', src,
               library + [os.path.join(LOOPBACK_DIR, 'a2c_uvm_loopback_tb.sv')],
               [common, UVM_DIR, LOOPBACK_DIR]) and ok
    ok = parse('the UVM library and its loopback testbench with A2C_UVM_COV', src,
               library + [os.path.join(LOOPBACK_DIR, 'a2c_uvm_loopback_tb.sv')],
               [common, UVM_DIR, LOOPBACK_DIR], ['A2C_UVM_COV']) and ok
    for name in EXAMPLES:
        files, env_pkg = example_sources(name)
        ok = parse(f'examples/{name} generated UVM packages', src, library + files,
                   [common, UVM_DIR], [f'A2C_UVM_PKG={env_pkg}']) and ok
    print('ALL TESTS PASSED' if ok else 'SOME TESTS FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
