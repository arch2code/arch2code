#!/usr/bin/env python3
"""A parameterized child reached at a variant by one site and at no variant by
another.

The registration key the SystemC factory looks a child up under is
(blockType, variant, projectName). A site naming no variant asks for the empty
variant and expects the child at its DEFAULT Config, so the child's trampoline
registrar has to make that registration whenever any site binds no variant --
including when a SIBLING site binds one. Registering only the bound labels
leaves the variant-less site with no key to find: the exact lookup misses, no
container-supplied factory answers for a plain child, and the empty-variant
fallback repeats the same miss, so elaboration aborts on
"Attempted to create an instance ... of an unregistered block type".

The fixture is that shape and nothing more: `rdvCont` holds `uLeafVar` at
variant `tuned` and `uLeafDef` at no variant, both of `rdvLeaf`. The suite
copies the authored fixture to a temp tree, scaffolds and generates it, then
BUILDS AND RUNS the model, because the defect is invisible to every static
check -- the generated sources compile perfectly either way and the missing
registration is only discovered when the factory is asked.

What stops the run passing by coincidence:

- Each leaf logs the algorithm its own Config resolved, and the two are asserted
  BY NAME here: `uLeafVar` must resolve 5 (the variant's binding) and `uLeafDef`
  must resolve 1 (the constant's declared value, i.e. the default Config). A
  registration made under the empty variant naming the wrong Config would
  elaborate, so the numbers are what prove each site got its own type.
- Both leaves receive four samples through their bound ports and assert every
  payload, and the generated testbench `final()` asserts the run reached end of
  test. A child whose cast yielded a null pointer, or a run that aborted early,
  fails those rather than reporting a pass.

The container declares the leaf's parameter itself. That is not decoration: the
SystemVerilog instance-parameter path (`_resolveSvInstanceParams`) has no
spelling for a variant-less site whose container declares no matching parameter,
so a params-less container raises KeyError before generation completes.

The same two sites exist a second time on `rdvQuiet`, a hasVl block, because the
verilated `_verif` keys are a separate registration set with the same
requirement -- and a stricter one: instanceFactory nulls the container-supplied
factory for every non-model mode, so a verilated site has nothing but the
registration to find. `rdvQuiet` is portless so that verilating one of its sites
never holds up the sample stream the rdvLeaf sites carry; the run has to reach
end of test on its own either way. Each `--vlInst` case asserts that the named
site's model report line is GONE (the wrapper served it) while every other site
still reports its own algorithm.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'registrar-default-variant')
# Bounded so the suite stays polite in the parallel runner's isolated lane,
# which already fans suites across the cores.
BUILD_JOBS = '8'

# Per site: the algorithm its Config must resolve. A site naming the variant
# resolves the variant's binding; one naming nothing takes its block's default
# Config, which carries the constant's declared value.
EXPECTED_ALGO = {'uLeafVar': 5, 'uLeafDef': 1, 'uQuietVar': 5, 'uQuietDef': 1}

# The hasVl sites, by the hierarchy name `--vlInst` selects them with.
VL_SITES = {'uQuietVar': 'tb.rdvTop.uCont.uQuietVar',
            'uQuietDef': 'tb.rdvTop.uCont.uQuietDef'}


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


def make(target, project, env, *, directory=None, jobs=None, overrides=None):
    """Run one make target against the temp project copy.

    REPO_ROOT names the copy rather than the committed fixture; A2C_ROOT names
    the builder under test. Both are command-line overrides, so they win over
    the git-toplevel defaults the fixture makefiles carry for in-place use.
    """
    cmd = ['make', '-C', directory or project,
           f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}']
    if jobs:
        cmd.append(f'-j{jobs}')
    cmd.extend(overrides or [])
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
            f"the model run failed (rc={ran.returncode}). An unregistered block "
            f"type here is the registrar omitting the empty-variant "
            f"registration:\n{ran.stdout}\n{ran.stderr}")
    return ran.stdout


def check_registrar(project):
    """Both trampolines carry both registrations.

    Asserted as well as the runs so a failure separates the emitter from the
    factory instead of only reporting an aborted elaboration.
    """
    ok = True
    for stub, label in ((os.path.join('registrar', 'rdvLeafRegistrar.cppm'), 'model'),
                        (os.path.join('registrar', 'rdvQuietVlRegistrar.cpp'), 'verilated')):
        with open(os.path.join(project, stub)) as f:
            text = f.read()
        for key, what in (('"tuned", "rdvTest"', 'the bound variant'),
                          ('"", "rdvTest"', 'the empty variant')):
            if key in text:
                print(f"  PASS: {label} registrar registers {what}")
            else:
                print(f"  FAIL: {label} registrar does not register {what} "
                      f"({key} absent)")
                ok = False
    return ok


def check_vl_run(project, env, site):
    """One verilated site: the run completes and the wrapper served that site.

    A missing `_verif` key aborts elaboration on "unregistered block type", so a
    non-zero return code is the defect. The named site reporting no algorithm is
    what proves the wrapper -- not the model class -- answered for it.
    """
    rundir = os.path.join(project, 'rundir')
    ran = make('run-vl', project, env, directory=rundir,
               overrides=['VL_DUT=1', f'VL_INST={VL_SITES[site]}'])
    if ran.returncode != 0:
        print(f"  FAIL: verilating {site} did not run (rc={ran.returncode})\n"
              f"{ran.stdout}\n{ran.stderr}")
        return False
    ok = True
    for instance, algo in sorted(EXPECTED_ALGO.items()):
        reported = f"{instance} resolved algorithm {algo}" in ran.stdout
        if instance == site:
            if reported:
                print(f"  FAIL: verilating {site} still reported the model's "
                      f"algorithm, so the model class answered for it")
                ok = False
            else:
                print(f"  PASS: verilating {site} replaced its model")
        elif not reported:
            print(f"  FAIL: verilating {site} lost '{instance} resolved "
                  f"algorithm {algo}'")
            ok = False
    return ok


def check_run(output):
    """Both sites elaborated, and each resolved its own Config."""
    ok = True
    for instance, algo in sorted(EXPECTED_ALGO.items()):
        expected = f"{instance} resolved algorithm {algo}"
        if expected in output:
            print(f"  PASS: {expected}")
        else:
            print(f"  FAIL: run did not report '{expected}'")
            ok = False
    return ok


def run_all_tests():
    env = toolchain_env()
    tmp = tempfile.mkdtemp(prefix='registrar_default_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'rdv')
        shutil.copytree(FIXTURE, project)
        output = generate_and_run(project, env)
        ok = check_registrar(project)
        ok = check_run(output) and ok
        # The verilated flavour shares the fixture but not the object files, so
        # it is a second build of the same sources with -DVERILATOR.
        built = make('all', project, env, directory=os.path.join(project, 'rundir'),
                     jobs=BUILD_JOBS, overrides=['VL_DUT=1'])
        if built.returncode != 0:
            raise RuntimeError(f"verilated build failed:\n{built.stdout}\n{built.stderr}")
        for site in sorted(VL_SITES):
            ok = check_vl_run(project, env, site) and ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("\nPASS: a child bound at a variant and at no variant serves both sites")
        return 0
    print("\nFAIL: the variant-less site did not resolve its own Config")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
