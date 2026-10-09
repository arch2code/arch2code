#!/usr/bin/env python3
"""`make synthf` and `make lint` in a project's rtl directory.

A synthesis tool needs one ordered file list with no Verilator switches. Copies
examples/hierVlDemo, whose testbench package imports the shared-types package,
so rtl.f compile order is the reverse of alphabetical order. Checks:
- `make synthf` writes .gen/synth.f: one existing absolute path per line, no
  tool switches, the rtl.f packages first in rtl.f order, then the modules;
- with 2000 module paths totalling over 128 KiB, more than one shell argument
  can hold, synth.f still lists every path;
- in a copy of examples/ip_test, synth.f lists exactly the rtl.f packages and
  leaves out ipTop_package.sv, a child project's package outside the compile
  closure;
- `make lint` with an HDL_TOP_MODULE that has no Verilator wrapper stops with a
  message naming the block, instead of running verilator with an empty
  --top-module that swallows the next argument.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir


FIXTURE = os.path.join(base_dir, 'examples', 'hierVlDemo')
MULTI_FIXTURE = os.path.join(base_dir, 'examples', 'ip_test')
COPY_IGNORE = shutil.ignore_patterns('rundir', '.gen', '*.db', '*.db-*', 'compile_commands.json')


DUMMY_MODULES = 2000


def make(project, *args):
    result = subprocess.run(['make', '-C', os.path.join(project, 'rtl'), '--no-print-directory',
                             f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}', *args],
                            capture_output=True, text=True, timeout=600,
                            env=dict(os.environ, NO_COLOR='1'))
    return result, result.stdout + result.stderr


def rtlDotFPackages(rtlDotF):
    # The package lines of rtl.f, resolved against the rtl.f directory.
    rtlDir = os.path.dirname(rtlDotF)
    with open(rtlDotF) as f:
        lines = [l.strip() for l in f]
    return [os.path.normpath(os.path.join(rtlDir, l)) for l in lines
            if l and not l.startswith(('+', '-', '//'))]


def main():
    failures = []

    def check(ok, message):
        print(f"{'PASS' if ok else 'FAIL'}: {message}")
        if not ok:
            failures.append(message)

    with tempfile.TemporaryDirectory(prefix='make_synthf_') as tmp:
        project = os.path.join(tmp, 'hierVlDemo')
        shutil.copytree(FIXTURE, project, symlinks=True, ignore=COPY_IGNORE)

        result, output = make(project, 'synthf')
        synthF = os.path.join(project, '.gen', 'synth.f')
        if result.returncode != 0 or not os.path.isfile(synthF):
            print(f"FAIL: make synthf did not write {synthF}:\n{output}")
            return 1
        with open(synthF) as f:
            lines = f.read().splitlines()
        print(f"synth.f:\n  " + "\n  ".join(lines))

        switches = [l for l in lines if l.startswith(('-', '+'))]
        check(not switches, f"synth.f carries no tool switches: {switches}")
        bad = [l for l in lines if not (os.path.isabs(l) and os.path.isfile(l))]
        check(not bad, f"every synth.f line is an existing absolute path: {bad}")

        packages = rtlDotFPackages(os.path.join(project, 'rtl', 'rtl.f'))
        names = [os.path.basename(p) for p in packages]
        check(names == ['hierVlSharedTypes_package.sv', 'hierVlDemo_tb_package.sv'],
              f"rtl.f lists the imported package first: {names}")
        check(lines[:len(packages)] == packages,
              f"synth.f opens with the rtl.f packages in rtl.f order: {lines[:len(packages)]}")
        modules = lines[len(packages):]
        check(os.path.join(project, 'rtl', 'hierVlDemo.sv') in modules,
              f"the hierVlDemo module follows the packages: {modules}")
        check(not any(l.endswith('_package.sv') for l in modules),
              f"no package follows a module: {modules}")
        check(not any('hdl_sv_wrapper' in l for l in lines),
              f"synth.f names no Verilator wrapper: {lines}")

        result, output = make(project, 'HDL_TOP_MODULE=hierVlDemo_tb', 'lint')
        check(result.returncode != 0
              and "HDL_TOP_MODULE 'hierVlDemo_tb' has no Verilator wrapper" in output
              and '(available: hierVlDemo)' in output,
              f"lint with an unwrapped HDL top stops with a message naming it:\n{output.strip()[-600:]}")
        check('--top-module  -F' not in output and '--top-module -F' not in output,
              "lint never runs verilator with an empty --top-module")

        # A make command-line variable is one argv string with the same cap, so
        # the long module list comes from a second makefile.
        dummyDir = os.path.join(tmp, 'd' * 120)
        dummies = [os.path.join(dummyDir, f'dummyModule{i:05d}.sv') for i in range(DUMMY_MODULES)]
        extraMk = os.path.join(tmp, 'longModules.mk')
        with open(extraMk, 'w') as f:
            f.write('A2C_SV_FILES := ' + ' '.join(dummies) + '\n')
        result, output = make(project, '-f', 'Makefile', '-f', extraMk, 'synthf')
        lines = []
        if result.returncode == 0:
            with open(synthF) as f:
                lines = f.read().splitlines()
        check(lines[len(packages):] == dummies,
              f"synth.f lists all {DUMMY_MODULES} module paths ({sum(map(len, dummies))} bytes), "
              f"got {len(lines)} synth.f lines:\n{output.strip()[-400:]}")

        multi = os.path.join(tmp, 'ip_test')
        shutil.copytree(MULTI_FIXTURE, multi, symlinks=True, ignore=COPY_IGNORE)
        result, output = make(multi, 'synthf')
        synthF = os.path.join(multi, '.gen', 'synth.f')
        if result.returncode != 0 or not os.path.isfile(synthF):
            print(f"FAIL: make synthf did not write {synthF}:\n{output}")
            return 1
        with open(synthF) as f:
            lines = f.read().splitlines()
        synthPackages = [l for l in lines if l.endswith('_package.sv')]
        packages = rtlDotFPackages(os.path.join(multi, 'top', 'rtl', 'rtl.f'))
        check(synthPackages == packages and lines[:len(packages)] == packages,
              f"ip_test synth.f lists exactly the rtl.f packages, first and in order:\n"
              f"  synth.f {synthPackages}\n  rtl.f   {packages}")
        dropped = os.path.join(multi, 'ip', 'rtl', 'ipTop_package.sv')
        check(os.path.isfile(dropped) and dropped not in lines,
              f"ip_test synth.f leaves out {os.path.basename(dropped)}, outside the compile closure")

    if failures:
        print("SOME TESTS FAILED")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == '__main__':
    sys.exit(main())
