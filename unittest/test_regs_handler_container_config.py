#!/usr/bin/env python3
"""A parameterized register owner instantiated at a variant, and the handler its
registers actually live in.

A block that owns firmware-accessible registers does not hold them itself. The
register-bus post-parse pass synthesises a `<block>_regs` handler block, gives it
the owner's parameter list, and instantiates it inside the owner. When that
synthesised instance names no Config, the handler freezes at the block's default
Config while the owner runs at whatever variant its site binds. Every parameter
value the handler compiles against then comes from the declaring constants rather
than from the instance, and the handler is where the registers live.

The fixture is that shape and nothing more. `rcvLeaf` declares `RCV_CFG_GAIN`,
owns the `cfg` register, and is instantiated once at variant `tuned`, which binds
12 where the constant declares 1. `rcvLeaf` reports its own gain next to the gain
its handler resolved and fails the run when they differ, which is the whole defect
in one line, `gain 12 handler gain 1`.

The suite copies the authored fixture to a temp tree, scaffolds and generates it,
then BUILDS AND RUNS the model. A static check would not see this. The generated
sources compile either way, because the handler is self-consistent at whichever
Config it was given.

What stops the run passing by coincidence:

- `rcvCpu` writes 0xABC to cfg over APB through the router and reads it back,
  asserting the value. That exercises the register path the handler serves, so a
  handler that elaborated but decoded nothing fails here rather than reporting a
  pass.
- The generated testbench asserts the run reached end of test, which `rcvCpu`
  votes for only after its readback.

Two emitted facts are asserted as well, so a failure separates the emitter from
the run. The container's handler member is typed by `Config`, and no handler
trampoline is emitted, because an all-container-typed child earns no registration,
`hasRegistrations` goes false, and the `requiresRegistrations` fileMap gate
suppresses the file.

The register payload here is a fixed-width type on purpose. A register whose
payload field is a parameterizable type cannot be generated today. The structure
emitter spells the field's `_setValue` cast without its Config argument and masks
with the width the declaring constant carries, so such a register neither compiles
nor tracks its Config. That is a separate defect from the one this suite guards.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from pysrc.processYaml import projectOpen


FIXTURE = os.path.join(test_dir, 'fixtures', 'regs-container-variant')
# Bounded so the suite stays polite in the parallel runner's isolated lane,
# which already fans suites across the cores.
BUILD_JOBS = '8'

# The variant binds 12; the block's RCV_CFG_GAIN constant declares 1.
TUNED_GAIN = 12
# Written and read back over APB. Fits the register's fixed-width payload.
CFG_VALUE = 0xabc


def toolchain_env():
    """The SystemC toolchain variables the arch2code makefiles require."""
    env = os.environ.copy()
    for var in ('SYSTEMC_INCLUDE', 'SYSTEMC_LIBDIR', 'BOOST_INCLUDE', 'LD_BOOST'):
        if not env.get(var):
            raise RuntimeError(f"{var} is not set; the SystemC toolchain variables "
                               f"the arch2code makefiles require must be set to run "
                               f"this suite")
    env['NO_COLOR'] = '1'
    return env


def make(target, project, env, *, directory=None, jobs=None):
    """Run one make target against the temp project copy.

    REPO_ROOT names the copy rather than the committed fixture; A2C_ROOT names
    the builder under test. Both are command-line overrides, so they win over
    the git-toplevel defaults the fixture makefiles carry for in-place use.
    """
    cmd = ['make', '-C', directory or project,
           f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}']
    if jobs:
        cmd.append(f'-j{jobs}')
    cmd.append(target)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=1800, env=env)


def generate_and_run(project, env):
    """Scaffold, generate, build and run the copy. Returns the run's output."""
    for target, jobs in (('db', None), ('newmodule', None), ('gen', BUILD_JOBS)):
        result = make(target, project, env, jobs=jobs)
        if result.returncode != 0:
            raise RuntimeError(f"make {target} failed:\n{result.stdout}\n{result.stderr}")

    rundir = os.path.join(project, 'rundir')
    built = make('all', project, env, directory=rundir, jobs=BUILD_JOBS)
    if built.returncode != 0:
        raise RuntimeError(f"model build failed:\n{built.stdout}\n{built.stderr}")

    ran = make('run', project, env, directory=rundir)
    if ran.returncode != 0:
        raise AssertionError(
            f"the model run failed (rc={ran.returncode}). A gain mismatch here is "
            f"the synthesised handler instance naming no Config, so the handler "
            f"froze at the block's default:\n{ran.stdout}\n{ran.stderr}")
    return ran.stdout


def check_run(output):
    """The handler resolved its container's variant, and cfg round-tripped."""
    ok = True
    for expected, what in (
            (f"gain {TUNED_GAIN} handler gain {TUNED_GAIN}",
             "the handler resolved its container's variant"),
            (f"cfg readback 0x{CFG_VALUE:x}",
             "cfg round-tripped over the register bus"),
    ):
        if expected in output:
            print(f"  PASS: {what}")
        else:
            print(f"  FAIL: run did not report '{expected}' ({what})")
            ok = False
    return ok


def check_emitted(project):
    """The container types the handler by Config and owns no trampoline for it."""
    ok = True
    with open(os.path.join(project, 'model', 'rcvLeaf.cppm')) as f:
        container = f.read()
    if 'std::shared_ptr<rcvLeaf_regsBase<Config>>' in container:
        print("  PASS: the container's handler member is typed by Config")
    else:
        print("  FAIL: the container's handler member is not typed by Config")
        ok = False
    trampoline = os.path.join(project, 'registrar', 'rcvLeaf_regsRegistrar.cppm')
    if os.path.exists(trampoline):
        print("  FAIL: a handler trampoline was emitted; a container-typed child "
              "earns no registration")
        ok = False
    else:
        print("  PASS: no handler trampoline was emitted")
    db = os.path.join(project, 'rcvTest.db')
    prj = projectOpen(db)
    pair = (prj.getQualBlock('rcvLeaf'), prj.getQualBlock('rcvLeaf_regs'))
    if prj.registrarPairs[pair]['hasModelRegistrations']:
        print("  FAIL: the persisted pair requirement retained the handler trampoline")
        ok = False
    else:
        print("  PASS: the persisted pair requirement suppresses the handler trampoline")
    manifestFiles = {os.path.basename(path)
                     for path in prj.config.getConfig('BUILDMANIFEST')['scGenFiles']}
    if 'rcvLeaf_regsRegistrar.cppm' in manifestFiles:
        print("  FAIL: the build manifest retained the suppressed handler trampoline")
        ok = False
    else:
        print("  PASS: the build manifest omits the suppressed handler trampoline")
    return ok


def run_all_tests():
    env = toolchain_env()
    tmp = tempfile.mkdtemp(prefix='regs_container_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'rcv')
        shutil.copytree(FIXTURE, project)
        output = generate_and_run(project, env)
        ok = check_run(output)
        ok = check_emitted(project) and ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("\nPASS: the register handler takes the Config of the block whose "
              "registers it holds")
        return 0
    print("\nFAIL: the register handler did not follow its container's Config")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
