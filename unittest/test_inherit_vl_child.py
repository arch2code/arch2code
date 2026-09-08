#!/usr/bin/env python3
"""One parameterized leaf type used at ordinary and containerParam sites.

The ordinary site keeps the leaf's `solo` Config. Each containerParam site
derives a concrete child Config from its container's active Config.

The suite scaffolds, generates, verilates and RUNS, because nothing else in the
corpus swaps a verilated child into a multi-variant container and the swap only
resolves when the factory is asked. Exactly one instance is verilated per run
(`--vlInst`), so the two container variants are two runs, in the manner of
ip_test's `run-vl-ip0` / `run-vl-ip1`.

Having verilated once, it also gates the verilate step's dependencies: an edit to
design RTL must reach the Verilated object and the run, and a rebuild after no
edit must verilate nothing.
"""

import glob
import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from pysrc.processYaml import projectOpen


FIXTURE = os.path.join(test_dir, 'fixtures', 'inherit-vl-child')
# Bounded at 8 so this suite does not oversubscribe the cores the parallel
# runner is already fanning other suites across.
BUILD_JOBS = '8'

# What each container variant resolves. The two differ in both, and neither
# matches the leaf's own decoy variant (algorithm 3).
DEFAULT_ALGO, DEFAULT_WIDTH = 1, 8
ALT_ALGO, ALT_WIDTH = 6, 10
SAMPLE_COUNT = 4
# The leaf swapped for its verilated wrapper, one per container instance. It is
# the LAST leaf in its chain, so what the checker reads back is what the
# VERILATED leaf stamped. Its model twin logs every sample it forwards, so the
# absence of that line is what proves the swap took effect.
SWAPPED_LEAF = {'def': 'tb.vliTop.uWrap.uContDef.uLeafB',
                'alt': 'tb.vliTop.uWrap.uContAlt.uLeafB'}


def copy_fixture(project):
    shutil.copytree(
        FIXTURE, project,
        ignore=shutil.ignore_patterns('*.db', '*.db-*', '.gen', 'build'))


def toolchain_env():
    """The SystemC toolchain variables the arch2code makefiles require."""
    env = os.environ.copy()
    for var in ('SYSTEMC_INCLUDE', 'SYSTEMC_LIBDIR', 'BOOST_INCLUDE', 'LD_BOOST'):
        if not env.get(var):
            raise RuntimeError(f"{var} is not set; the SystemC toolchain variables "
                               f"the arch2code makefiles require must be set to run "
                               f"this suite")
    if shutil.which('verilator') is None:
        raise RuntimeError("verilator is not on PATH; this suite verilates its "
                           "fixture and cannot run without it")
    env['NO_COLOR'] = '1'
    return env


def make(target, project, env, *, directory=None, jobs=None, extra=()):
    """Run one make target against the temp project copy.

    REPO_ROOT names the copy rather than the committed fixture; A2C_ROOT names
    the builder under test. Both are command-line overrides, so they win over
    the git-toplevel defaults the fixture makefiles carry for in-place use.
    """
    cmd = ['make', '-C', directory or project,
           f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}']
    if jobs:
        cmd.append(f'-j{jobs}')
    cmd.extend(extra)
    cmd.append(target)
    return subprocess.run(cmd, capture_output=True, text=True, timeout=3600, env=env)


def generate_and_build(project, env):
    """Scaffold, generate and build the copy with both verilated DUTs."""
    cleaned = make('clean', project, env, jobs=BUILD_JOBS)
    if cleaned.returncode != 0:
        raise RuntimeError(f"make clean failed:\n{cleaned.stdout}\n{cleaned.stderr}")
    for target in ('db', 'newmodule', 'gen'):
        jobs = BUILD_JOBS
        result = make(target, project, env, jobs=jobs)
        if result.returncode != 0:
            raise RuntimeError(f"make {target} failed:\n{result.stdout}\n{result.stderr}")

    rundir = os.path.join(project, 'rundir')
    built = make('all', project, env, directory=rundir, jobs=BUILD_JOBS,
                 extra=('VL_DUT=1',))
    if built.returncode != 0:
        raise RuntimeError(
            f"the verilated build failed (rc={built.returncode}). A bare class-template "
            f"name in the wrapper's BFM or hdl_if declarations is the wrapper taking "
            f"its shape from the instantiated variant set:\n{built.stdout}\n{built.stderr}")
    return rundir


def check_mixed_instance_orders(env):
    """Inherited and ordinary sites keep one registrar in either YAML order."""
    ok = True
    inherited = (
        '    uLeafA:      { container: vliCont,   instanceType: vliLeaf,   '
        'instGroup: top, inheritContainerParam: true }\n'
        '    uLeafB:      { container: vliCont,   instanceType: vliLeaf,   '
        'instGroup: top, inheritContainerParam: true }\n')
    ordinary = (
        '    uLeafOrd:    { container: vliCont,   instanceType: vliLeaf,   '
        'instGroup: top, variant: solo }\n')
    for name, ordered in (('inherited-first', inherited + ordinary),
                          ('ordinary-first', ordinary + inherited)):
        tmp = tempfile.mkdtemp(prefix=f'inherit_order_{name}_', dir=test_dir)
        try:
            project = os.path.join(tmp, 'vli')
            copy_fixture(project)
            yaml = os.path.join(project, 'yaml', 'vliCont.yaml')
            with open(yaml) as f:
                text = f.read()
            start = text.index('    uLeafA:      { container: vliCont')
            end = text.index('    # The same child type at an ordinary site.', start)
            text = text[:start] + ordered + text[end:]
            with open(yaml, 'w') as f:
                f.write(text)
            for target in ('db', 'newmodule'):
                result = make(target, project, env)
                if result.returncode != 0:
                    print(f"  FAIL ({name}): make {target} failed\n"
                          f"{result.stdout}\n{result.stderr}")
                    ok = False
                    break
            else:
                registrar = os.path.join(
                    project, 'registrar', 'vliLeafRegistrar.cppm')
                with open(registrar) as f:
                    body = f.read()
                body = body.replace(
                    '--block=vliLeaf --parent=vliCont',
                    '--block=vliLeaf --parent=vliTop')
                with open(registrar, 'w') as f:
                    f.write(body)
                result = make('gen', project, env)
                if result.returncode != 0:
                    print(f"  FAIL ({name}): make gen rejected an existing "
                          f"child registrar with a retired pair owner\n"
                          f"{result.stdout}\n{result.stderr}")
                    ok = False
                    continue
                prj = projectOpen(os.path.join(project, 'vlInh.db'))
                pairKey = (prj.getQualBlock('vliCont'), prj.getQualBlock('vliLeaf'))
                pair = prj.registrarPairs[pairKey]
                variants = [entry['variant'] for entry in pair['modelRegistrations']]
                matches = [name for name in os.listdir(os.path.dirname(registrar))
                           if name == os.path.basename(registrar)]
                if variants != ['solo'] or len(matches) != 1:
                    print(f"  FAIL ({name}): model variants={variants}, "
                          f"registrar count={len(matches)}")
                    ok = False
                else:
                    with open(registrar) as f:
                        body = f.read()
                    if '"solo"' not in body:
                        print(f"  FAIL ({name}): registrar omits ordinary variant solo")
                        ok = False
                    else:
                        print(f"  PASS ({name}): one registrar retains ordinary "
                              "variant solo")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    return ok


def check_emitted(project):
    """The wrapper is a reusable template and the trampoline covers both variants."""
    ok = True
    prj = projectOpen(os.path.join(project, 'vlInh.db'))
    drvRegistrar = os.path.join(project, 'registrar', 'vliDrvRegistrar.cppm')
    if not os.path.exists(drvRegistrar):
        print("  FAIL: ordinary model registrar lost its child-named scaffold")
        ok = False
    else:
        with open(drvRegistrar) as f:
            drvText = f.read()
        if '"vliDrv_model"' not in drvText:
            print("  FAIL: ordinary model registrar has no vliDrv_model registration")
            ok = False
        elif '"drvDef", "vlInh"' not in drvText:
            print("  FAIL: ordinary model registration lost its project-owned factory key")
            ok = False
        else:
            print("  PASS: ordinary model registration keeps its scaffold and project key")
    leafKey = prj.getQualBlock('vliLeaf')
    inheritedPair = (prj.getQualBlock('vliCont'), leafKey)
    ordinaryPair = (prj.getQualBlock('vliWrap'), leafKey)
    if not prj.registrarPairs[inheritedPair]['hasModelRegistrations']:
        print("  FAIL: same-parent ordinary site did not retain its model registrar")
        ok = False
    else:
        print("  PASS: same-parent ordinary site retains the model registrar")
    if not prj.registrarPairs[ordinaryPair]['hasModelRegistrations']:
        print("  FAIL: ordinary parent-child pair lost its model registrar")
        ok = False
    else:
        print("  PASS: ordinary parent-child pair keeps its model registrar")
    inheritedView = prj.getRegistrarConfigView(leafKey, inheritedPair[0])
    ordinaryView = prj.getRegistrarConfigView(leafKey, ordinaryPair[0])
    if inheritedView['registeredVariants'] != ['solo']:
        print(f"  FAIL: mixed pair selected model variants "
              f"{inheritedView['registeredVariants']}, expected ['solo']")
        ok = False
    elif ordinaryView['registeredVariants'] != ['solo']:
        print(f"  FAIL: ordinary pair selected variants "
              f"{ordinaryView['registeredVariants']}, expected ['solo']")
        ok = False
    else:
        print("  PASS: both parent-child pairs retain only their ordinary variant")
    with open(os.path.join(project, 'verif', 'vliLeaf_hdl_sc_wrapper.h')) as f:
        wrapper = f.read()
    for expected, what in (
            ('template <typename DUT_T, typename Config>',
             "the wrapper is a DUT_T/Config class template"),
            ('public vliLeafBase<Config> {',
             "its base class binds the template parameter, not a pinned Config"),
            ('push_ack_src_bfm<vliSt<Config>, sc_bv<vliSt<Config>::_bitWidth>>',
             "the BFM payload keeps its template argument"),
            ('push_ack_hdl_if<sc_bv<vliSt<Config>::_bitWidth>>',
             "the hdl_if payload keeps its template argument"),
    ):
        if expected in wrapper:
            print(f"  PASS: {what}")
        else:
            print(f"  FAIL: the emitted wrapper does not carry '{expected}' ({what})")
            ok = False

    # The container-sourced pair owns one collision-free top per concrete parent
    # Config. The ordinary site under the other parent gets a different stem.
    expectedValues = {'default': (DEFAULT_ALGO, DEFAULT_WIDTH),
                      'alt': (ALT_ALGO, ALT_WIDTH),
                      'solo': (3, DEFAULT_WIDTH)}
    for registration in inheritedView['verifRegistrations']:
        variant = registration['variant']
        algo, width = expectedValues[variant]
        if registration['pairSpecific'] != (variant in ('default', 'alt')):
            print(f"  FAIL: '{variant}' pairSpecific="
                  f"{registration['pairSpecific']}")
            ok = False
        if variant == 'solo' and registration['fileStub'] != 'vliLeaf_solo':
            print(f"  FAIL: ordinary variant moved to "
                  f"{registration['fileStub']}")
            ok = False
        path = os.path.join(
            project, 'verif',
            f'{registration["physicalFileStub"]}_hdl_sv_wrapper.sv')
        if not os.path.exists(path):
            print(f"  FAIL: no concrete SV top for '{variant}'")
            ok = False
            continue
        with open(path) as f:
            top = f.read()
        for decl in (f'localparam VLI_ALGO = {algo}', f'localparam VLI_WIDTH = {width}'):
            if decl in top:
                print(f"  PASS: the concrete '{variant}' top elaborates at "
                      f"'{decl}'")
            else:
                print(f"  FAIL: the '{variant}' top does not carry '{decl}'")
                ok = False
    registrarPath = os.path.join(project, 'registrar', 'vliLeafVlRegistrar.cpp')
    with open(registrarPath) as f:
        registrar = f.read()
    if '"solo", "vlInh"' not in registrar:
        print("  FAIL: ordinary VL registration lost its project-owned factory key")
        ok = False
    else:
        print("  PASS: ordinary VL registration keeps its project-owned factory key")
    configs = {
        'default': 'vlInh_vliLeafSourcedConfig<vlInh_vliContDefaultConfig>',
        'alt': 'vlInh_vliLeafSourcedConfig<vlInh_vliContAltConfig>',
        'solo': 'vlInh_vliLeafSoloConfig',
    }
    for registration in inheritedView['verifRegistrations']:
        variant = registration['variant']
        target = (
            f'vliLeaf_hdl_sc_wrapper<{registration["dutClass"]}, '
            f'{configs[variant]}>')
        key = f'"{variant}", "{registration["factoryProject"]}"'
        if target in registrar and key in registrar:
            print(f"  PASS: the aggregate trampoline registers '{variant}' as {target}")
        else:
            print(f"  FAIL: the aggregate trampoline has no '{variant}' registration "
                  f"of '{target}'")
            ok = False
    registrarFiles = [
        name for name in os.listdir(os.path.join(project, 'registrar'))
        if name.endswith('vliLeafVlRegistrar.cpp')]
    if registrarFiles != ['vliLeafVlRegistrar.cpp']:
        print(f"  FAIL: expected one stable child registrar, found {registrarFiles}")
        ok = False
    else:
        print("  PASS: two parents share one child-named VL registrar")
    return ok


# Mdir of the verilator runtime objects, which no design source feeds.
RUNTIME_MDIR = 'vl_dummy'


def verilated_object_stamps(rundir):
    """Modification time of every Verilated object, keyed by its top's Mdir."""
    pattern = os.path.join(rundir, 'build', 'vl', 'obj_dir', '*', 'V*__ALL.o')
    return {os.path.basename(os.path.dirname(o)): os.stat(o).st_mtime_ns
            for o in glob.glob(pattern)}


def check_rtl_edit_reverilates(project, rundir, env):
    """An edit to design RTL reaches the Verilated object and the run, and a
    rebuild after no edit verilates nothing. The pairing is the check.
    """
    ok = True
    leaf = os.path.join(project, 'rtl', 'vliLeaf.sv')
    before = verilated_object_stamps(rundir)
    if RUNTIME_MDIR not in before or len(before) < 2:
        print(f"  FAIL: expected {RUNTIME_MDIR} and at least one design top, "
              f"found {sorted(before)}")
        return False

    idle = make('all', project, env, directory=rundir, jobs=BUILD_JOBS,
                extra=('VL_DUT=1',))
    if idle.returncode != 0:
        print(f"  FAIL: the idle rebuild failed:\n{idle.stdout}\n{idle.stderr}")
        return False
    idled = verilated_object_stamps(rundir)
    if set(idled) != set(before):
        print(f"  FAIL: the set of Verilated tops changed across an idle rebuild: "
              f"{sorted(before)} -> {sorted(idled)}")
        return False
    churned = [t for t, m in idled.items() if before[t] != m]
    if churned:
        print(f"  FAIL: a rebuild with no edit re-verilated {sorted(churned)}")
        ok = False
    else:
        print("  PASS: a rebuild with no edit verilates nothing")

    with open(leaf) as f:
        original = f.read()
    edited = original.replace('inSt.data + (1 << (VLI_WIDTH - 3))',
                              'inSt.data + (1 << (VLI_WIDTH - 3)) + 1', 1)
    if edited == original:
        print("  FAIL: the leaf RTL no longer carries the expression this suite edits")
        return False
    with open(leaf, 'w') as f:
        f.write(edited)

    rebuilt = make('all', project, env, directory=rundir, jobs=BUILD_JOBS,
                   extra=('VL_DUT=1',))
    if rebuilt.returncode != 0:
        print(f"  FAIL: the rebuild after the RTL edit failed:"
              f"\n{rebuilt.stdout}\n{rebuilt.stderr}")
        return False
    after = verilated_object_stamps(rundir)
    if set(after) != set(before):
        print(f"  FAIL: the set of Verilated tops changed across the edit: "
              f"{sorted(before)} -> {sorted(after)}")
        return False
    stale = [t for t, m in after.items() if t != RUNTIME_MDIR and before[t] == m]
    if stale:
        print(f"  FAIL: the RTL edit did not re-verilate {sorted(stale)}")
        ok = False
    else:
        print("  PASS: the RTL edit re-verilated every design top")
    # The runtime objects are built from framework sources alone, so a design
    # edit must not reach them. This is the per-top scoping working.
    if before[RUNTIME_MDIR] != after[RUNTIME_MDIR]:
        print(f"  FAIL: the RTL edit re-verilated '{RUNTIME_MDIR}', which reads "
              f"no design source")
        ok = False
    else:
        print(f"  PASS: the RTL edit leaves '{RUNTIME_MDIR}' alone")

    # The edited arithmetic has to reach the simulation, not just the object
    # file: a stale wrapper is only a defect because the run then passes. The
    # checker's own payload assertion is the signal, so a link or startup failure
    # is not mistaken for the mismatch this edit provokes.
    ran = make('run-vl-def', project, env, directory=rundir, extra=('VL_DUT=1',))
    if 'Q_ASSERT' in ran.stdout and 'payload' in ran.stdout:
        print("  PASS: the edited RTL reaches the run, whose checker rejects the "
              "payload")
    else:
        print(f"  FAIL: the run did not report a payload mismatch against edited "
              f"RTL:\n{ran.stdout}\n{ran.stderr}")
        ok = False
    return ok


def check_run(which, output):
    """The inherited and ordinary sites each constructed at their own Config."""
    ok = True
    for expected, what in (
            (f"uChkDef checked {SAMPLE_COUNT} samples at algorithm {DEFAULT_ALGO} "
             f"width {DEFAULT_WIDTH}",
             "the default chain resolved its own container's algorithm and width"),
            (f"uChkAlt checked {SAMPLE_COUNT} samples at algorithm {ALT_ALGO} "
             f"width {ALT_WIDTH}",
             "the alt chain resolved its own container's algorithm and width"),
            (f"uChkSolo checked {SAMPLE_COUNT} samples at algorithm 3 "
             f"width {DEFAULT_WIDTH}",
             "the ordinary chain kept the leaf-owned solo Config"),
            ("uLeafSoloB forwarding tag 3 at algo 3 width 8",
             "the ordinary model leaf constructed and forwarded all samples"),
            ("No error", "the run reported no errors"),
    ):
        if expected in output:
            print(f"  PASS ({which}): {what}")
        else:
            print(f"  FAIL ({which}): run did not report '{expected}' ({what})")
            ok = False
    if f"{SWAPPED_LEAF[which]} forwarding" in output:
        print(f"  FAIL ({which}): {SWAPPED_LEAF[which]} still logged as a model; "
              f"the verilated wrapper was not swapped in")
        ok = False
    else:
        print(f"  PASS ({which}): {SWAPPED_LEAF[which]} ran as the verilated wrapper")
    for marker in ('Q_ASSERT', 'Fatal'):
        if marker in output:
            print(f"  FAIL ({which}): run reported {marker}")
            ok = False
    return ok


def run_all_tests():
    env = toolchain_env()
    tmp = tempfile.mkdtemp(prefix='inherit_vl_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'vli')
        copy_fixture(project)
        ok = check_mixed_instance_orders(env)
        rundir = generate_and_build(project, env)
        ok = check_emitted(project) and ok
        for which in ('def', 'alt'):
            ran = make(f'run-vl-{which}', project, env, directory=rundir,
                       extra=('VL_DUT=1',))
            if ran.returncode != 0:
                raise AssertionError(
                    f"the '{which}' verilated run failed (rc={ran.returncode}). A null "
                    f"child here is the trampoline binding a Config the container did "
                    f"not ask for:\n{ran.stdout}\n{ran.stderr}")
            ok = check_run(which, ran.stdout) and ok
        # Runs last: it leaves the copy's RTL edited and its build stale.
        ok = check_rtl_edit_reverilates(project, rundir, env) and ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("\nPASS: one parameterized leaf type builds and runs at its own "
              "variant and at two container-sourced Configs")
        return 0
    print("\nFAIL: the mixed ordinary and inherited leaf sites did not keep "
          "their own Config selections")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
