#!/usr/bin/env python3
"""Which value the emitted artifacts carry when two integrators each declare
variants of one reusable IP.

A variant is identified by (block, variant, declaring project). Two integrators
over one IP therefore hold two distinct bindings of one label, and each must
restate the whole parameter set because a consumer cannot borrow another
project's declaration. That is design intent, not an authoring mistake.

The in-memory nested view `data['parameters'][block]['variants'][variant]
['params']` is keyed by bare parameter name and carries no project axis, so it
holds one of the two bindings and the last one parsed decides which. An
emission path reading it emits the other integrator's value with no diagnostic,
which puts the SystemC Config and the Verilated SV top of one build at two
different numbers. Every value-consuming path must select a descriptor instead.

The other shape is two projects each declaring a label of their own over one IP,
so the closure holds several labels for one block with a single declarer each.
Nothing collapses, but the label a project never declared still reaches its
build, and a path that enumerated the project-blind view would emit an artifact
from it.

Fixture: `fixtures/variant-two-integrators`, three projects.
- xviLeaf declares the leaf and no variant.
- xviMid includes the leaf root and instantiates it twice: at the shared label
  v0 binding XVI_GAIN 7, and at vMid, which only xviMid declares, binding 5.
- xviTop does the same at v0 binding 3 and at its own vTop binding 9, and its
  closure references xviMid.
XVI_GAIN sizes nothing, so the divergence reaches no layout check. XVI_WIDTH is
held at 8 everywhere, so the payload is identical either way.

The fixture is authored so xviTop's own binding of v0 is the one the collapse
drops, and so xviMid's vMid reaches xviTop's build at a value xviTop never
bound. The two premise cells assert both, because otherwise every later
assertion passes whether or not the emission path consults the declaring
project.

XVI_GAIN also drives behaviour: the leaf scales each sample by it, in the model
and in the RTL alike. The last cell builds and runs both integrators' designs
and reads the payload back out at the sinks, so an emitted number that no
artifact consumes fails there even when every text assertion above passes.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectOpen

FIXTURE = os.path.join(test_dir, 'fixtures', 'variant-two-integrators')
LEAF_KEY = 'xviLeaf/../../../ipLeaf/yaml/xviLeaf.yaml'
# What each integrator binds XVI_GAIN to on the shared label v0, and on the
# label only it declares, in its own design file.
TOP_GAIN, MID_GAIN = 3, 7
TOP_OWN_GAIN, MID_OWN_GAIN = 9, 5
# The leaf IP's own dflt binding, which no integrator instantiates. It exists so
# the leaf's standalone Verilated wrapper top has its parameters bound.
LEAF_GAIN = 1
BUILD_JOBS = '8'
# Tags the stimulus blocks drive, and the mask the leaf wraps its product with.
SAMPLE_TAGS = (1, 2, 3, 4)
PIXEL_MASK = 0xFF
# Each sink and the gain of the leaf feeding it, per integrator.
TOP_SINKS = {'tb.xviTop.uTopSnk': TOP_GAIN,
             'tb.xviTop.uTopOwnSnk': TOP_OWN_GAIN}
MID_SINKS = {'tb.xviMidTop.uMid.uMidSnk': MID_GAIN,
             'tb.xviMidTop.uMid.uMidOwnSnk': MID_OWN_GAIN}
# xviMid's testbench top and its two leaf instances. One Verilated run selects
# one instance, so the pair covers both of xviMid's bindings as RTL.
MID_TB_TOP = 'xviMidTop'
MID_LEAVES = ('tb.xviMidTop.uMid.uMidLeaf', 'tb.xviMidTop.uMid.uMidOwnLeaf')
OBSERVED = re.compile(r'^\w+:(\S+) observed tag (\d+) data (\d+)$', re.M)
# Build output only. The fixture commits its implementation files with their
# user regions filled, so every source directory travels into the copy and
# `make gen` refills the generated regions in place.
GENERATED = shutil.ignore_patterns(
    '*.db', '*.db-*', '.gen', 'build', 'compile_commands.json')


def copy_fixture(prefix):
    work = tempfile.mkdtemp(prefix=prefix, dir=test_dir)
    shutil.copytree(FIXTURE, work, dirs_exist_ok=True, ignore=GENERATED)
    return work


def make(work, target, subdir='top', extra=()):
    """Run one make target against a directory of the temp copy.

    FIXTURE_ROOT names the copy and A2C_ROOT the builder under test. Both are
    command-line overrides, so they win over the git-toplevel defaults the
    fixture makefiles carry for an in-place run and both reach the sub-project
    makes the top recurses into.
    """
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run(
        ['make', '-C', os.path.join(work, subdir), f'-j{BUILD_JOBS}',
         f'FIXTURE_ROOT={work}', f'A2C_ROOT={base_dir}', *extra, target],
        capture_output=True, text=True, timeout=1800, env=env)


def build(work):
    """Build and generate the copy. Returns None on success, else a message."""
    for target in ('db', 'newmodule', 'gen'):
        result = make(work, target)
        if result.returncode != 0:
            return (f"make {target} failed (rc={result.returncode})\n"
                    f"{result.stdout}\n{result.stderr}")
    return None


def close_db():
    """Release the open database so the temp tree can be removed."""
    if g.db is not None:
        g.db.close()
        g.db = None


def read(work, *parts):
    with open(os.path.join(work, *parts)) as f:
        return f.read()


def mismatches(work, checks):
    """One message per artifact whose emitted XVI_GAIN is not the number the
    declaring project bound. Each check pairs a file with a pattern capturing
    the gain at one emission site, so a failure names the number found and a
    wrong binding is recognisable as the other integrator's."""
    problems = list()
    for parts, pattern, expected in checks:
        found = re.findall(pattern, read(work, *parts))
        if found == [str(expected)]:
            continue
        problems.append(f"{os.path.join(*parts)}: expected XVI_GAIN "
                        f"{expected}, found {', '.join(found) or 'no match'}")
    return problems


def observations(output, sinks):
    """One message per sink whose samples do not carry the gain its own project
    bound. A sink that reported nothing is a mismatch too, so a design that
    never ran cannot pass this quietly."""
    seen = dict()
    for instance, tag, data in OBSERVED.findall(output):
        seen.setdefault(instance, dict())[int(tag)] = int(data)
    problems = list()
    for instance, gain in sinks.items():
        expected = {tag: (tag * gain) & PIXEL_MASK for tag in SAMPLE_TAGS}
        got = seen.get(instance, dict())
        if got != expected:
            problems.append(f"{instance}: expected {expected} at XVI_GAIN "
                            f"{gain}, observed {got or 'no samples'}")
    return problems


def header(name):
    print(f"\n{'='*70}\nTest: {name}\n{'='*70}")


def test_collapse_drops_the_building_project():
    """The premise. Both bindings survive in the flat table at differing values,
    and the project-blind nested view holds the OTHER integrator's."""
    header("the project-blind nested view drops the building project's binding")
    work = copy_fixture('xvi_premise_')
    try:
        failure = make(work, 'db')
        if failure.returncode != 0:
            print(f"  FAIL: make db failed\n{failure.stdout}\n{failure.stderr}")
            return False
        prj = projectOpen(os.path.join(work, 'top', 'xviTop.db'))
        declared = {row['projectName']: row['value']
                    for row in prj.data['parametersvariantsparams'].values()
                    if row['blockKey'] == LEAF_KEY and row['variant'] == 'v0'
                    and row['param'] == 'XVI_GAIN'}
        if declared != {'xviTop': TOP_GAIN, 'xviMid': MID_GAIN}:
            print(f"  FAIL: fixture no longer states the premise; declared v0 "
                  f"XVI_GAIN bindings are {declared} rather than one from each "
                  f"integrator at differing values")
            return False
        collapsed = prj.data['parameters'][LEAF_KEY]['variants']['v0']['params']
        row = collapsed['XVI_GAIN']
        if (row['projectName'], row['value']) != ('xviMid', MID_GAIN):
            print(f"  FAIL: fixture no longer states the premise; the nested "
                  f"view holds {row['projectName']}'s {row['value']}, so an "
                  f"emission path reading it would emit the building project's "
                  f"own value by accident and every later cell would pass "
                  f"vacuously")
            return False
        print(f"  PASS: both bindings declared ({declared}); the nested view "
              f"holds xviMid's {MID_GAIN}")
        return True
    finally:
        close_db()
        shutil.rmtree(work, ignore_errors=True)


def test_a_label_only_the_other_integrator_declared_reaches_this_build():
    """The premise for distinctly-named labels. xviTop's closure holds four
    labels of one block, and one of them is xviMid's own vMid at a value xviTop
    never bound, so a path enumerating the project-blind view would hand xviTop
    an artifact for a label it never declared."""
    header("a label only the other integrator declared reaches this build")
    work = copy_fixture('xvi_labels_')
    try:
        failure = make(work, 'db')
        if failure.returncode != 0:
            print(f"  FAIL: make db failed\n{failure.stdout}\n{failure.stderr}")
            return False
        prj = projectOpen(os.path.join(work, 'top', 'xviTop.db'))
        declared = {(row['variant'], row['projectName']): row['value']
                    for row in prj.data['parametersvariantsparams'].values()
                    if row['blockKey'] == LEAF_KEY
                    and row['param'] == 'XVI_GAIN'}
        expected = {('v0', 'xviTop'): TOP_GAIN, ('v0', 'xviMid'): MID_GAIN,
                    ('vTop', 'xviTop'): TOP_OWN_GAIN,
                    ('vMid', 'xviMid'): MID_OWN_GAIN,
                    ('dflt', 'xviLeaf'): LEAF_GAIN}
        if declared != expected:
            print(f"  FAIL: fixture no longer states the premise; declared "
                  f"XVI_GAIN bindings are {declared} rather than {expected}, "
                  f"so the build no longer sees one label per integrator "
                  f"alongside the shared one")
            return False
        nested = prj.data['parameters'][LEAF_KEY]['variants']
        offered = {label: (entry['params']['XVI_GAIN']['projectName'],
                           entry['params']['XVI_GAIN']['value'])
                   for label, entry in nested.items()}
        if offered.get('vMid') != ('xviMid', MID_OWN_GAIN):
            print(f"  FAIL: fixture no longer states the premise; the nested "
                  f"view offers {offered} rather than a vMid slot holding "
                  f"xviMid's {MID_OWN_GAIN}, so nothing foreign is on offer "
                  f"and the emission cell would pass vacuously")
            return False
        print(f"  PASS: xviTop's closure offers {sorted(offered)}; vMid is "
              f"xviMid's {MID_OWN_GAIN} and xviTop declares no binding of it")
        return True
    finally:
        close_db()
        shutil.rmtree(work, ignore_errors=True)


def test_emitted_artifacts_carry_the_declaring_project_value():
    """Every artifact xviTop emits for its own leaf instance carries xviTop's
    own binding, so the model and the RTL of one build agree."""
    header("emitted SV and Config carry the building project's own binding")
    work = copy_fixture('xvi_emitted_')
    try:
        failure = build(work)
        if failure:
            print(f"  FAIL: {failure}")
            return False
        problems = mismatches(work, [
            # The sub-block instantiation's #(...) override list.
            (('top', 'rtl', 'xviTop.sv'),
             r'xviLeaf #\(\.XVI_WIDTH\(8\), \.XVI_GAIN\((\d+)\)\) uTopLeaf \(',
             TOP_GAIN),
            # The per-variant Verilator top's localparam bindings.
            (('top', 'verif', 'xviTop_xviLeaf_v0_hdl_sv_wrapper.sv'),
             r'localparam XVI_GAIN = (\d+)', TOP_GAIN),
            # The SystemC Config the model is built against. This path already
            # selected a descriptor; it is here so the cell fails if the two
            # halves of one build ever disagree again.
            (('top', 'registrar', 'xviTop_xviLeafVariantConfig.cppm'),
             r'struct xviTop_xviLeafV0Config \{[^}]*XVI_GAIN = (\d+);',
             TOP_GAIN),
        ])
        for problem in problems:
            print(f"  FAIL: {problem}")
        if not problems:
            print("  PASS: RTL instantiation, Verilator top and Config all "
                  f"carry xviTop's XVI_GAIN {TOP_GAIN}")
        return not problems
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_other_integrator_keeps_its_own_binding():
    """xviMid's own build is unmoved across the same artifact set: the same
    label at its own value in the RTL, the Verilator top and the Config."""
    header("the other integrator's build keeps its own binding")
    work = copy_fixture('xvi_other_')
    try:
        failure = build(work)
        if failure:
            print(f"  FAIL: {failure}")
            return False
        problems = mismatches(work, [
            (('mid', 'rtl', 'xviMid.sv'),
             r'xviLeaf #\(\.XVI_WIDTH\(8\), \.XVI_GAIN\((\d+)\)\) uMidLeaf \(',
             MID_GAIN),
            (('mid', 'verif', 'xviMid_xviLeaf_v0_hdl_sv_wrapper.sv'),
             r'localparam XVI_GAIN = (\d+)', MID_GAIN),
            (('mid', 'registrar', 'xviMid_xviLeafVariantConfig.cppm'),
             r'struct xviMid_xviLeafV0Config \{[^}]*XVI_GAIN = (\d+);',
             MID_GAIN),
        ])
        for problem in problems:
            print(f"  FAIL: {problem}")
        if not problems:
            print("  PASS: xviMid's RTL instantiation, Verilator top and "
                  f"Config all carry its own XVI_GAIN {MID_GAIN}")
        return not problems
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_each_build_emits_only_the_label_it_declared():
    """Distinctly-named labels stay apart. Each integrator emits its own label
    at its own value across RTL, Verilator top and Config, and emits nothing
    for the label only the other integrator declared."""
    header("each build emits only the label its own project declared")
    work = copy_fixture('xvi_own_label_')
    try:
        failure = build(work)
        if failure:
            print(f"  FAIL: {failure}")
            return False
        problems = mismatches(work, [
            (('top', 'rtl', 'xviTop.sv'),
             r'xviLeaf #\(\.XVI_WIDTH\(8\), \.XVI_GAIN\((\d+)\)\) '
             r'uTopOwnLeaf \(', TOP_OWN_GAIN),
            (('top', 'verif', 'xviTop_xviLeaf_vTop_hdl_sv_wrapper.sv'),
             r'localparam XVI_GAIN = (\d+)', TOP_OWN_GAIN),
            (('top', 'registrar', 'xviTop_xviLeafVariantConfig.cppm'),
             r'struct xviTop_xviLeafVTopConfig \{[^}]*XVI_GAIN = (\d+);',
             TOP_OWN_GAIN),
            (('mid', 'rtl', 'xviMid.sv'),
             r'xviLeaf #\(\.XVI_WIDTH\(8\), \.XVI_GAIN\((\d+)\)\) '
             r'uMidOwnLeaf \(', MID_OWN_GAIN),
            (('mid', 'verif', 'xviMid_xviLeaf_vMid_hdl_sv_wrapper.sv'),
             r'localparam XVI_GAIN = (\d+)', MID_OWN_GAIN),
            (('mid', 'registrar', 'xviMid_xviLeafVariantConfig.cppm'),
             r'struct xviMid_xviLeafVMidConfig \{[^}]*XVI_GAIN = (\d+);',
             MID_OWN_GAIN),
        ])
        # A Verilator top for the other integrator's label means the build
        # enumerated a label its own project never declared.
        for parts in (('top', 'verif', 'xviTop_xviLeaf_vMid_hdl_sv_wrapper.sv'),
                      ('mid', 'verif', 'xviMid_xviLeaf_vTop_hdl_sv_wrapper.sv')):
            if os.path.exists(os.path.join(work, *parts)):
                problems.append(f"{os.path.join(*parts)}: emitted for a label "
                                f"the building project never declared")
        # The other integrator's value must not appear anywhere in the SystemC
        # Config or the RTL, under any struct or instance name.
        for parts, stray, owner in (
                (('top', 'registrar', 'xviTop_xviLeafVariantConfig.cppm'),
                 f'XVI_GAIN = {MID_OWN_GAIN};', 'xviMid'),
                (('top', 'rtl', 'xviTop.sv'),
                 f'.XVI_GAIN({MID_OWN_GAIN})', 'xviMid'),
                (('mid', 'registrar', 'xviMid_xviLeafVariantConfig.cppm'),
                 f'XVI_GAIN = {TOP_OWN_GAIN};', 'xviTop'),
                (('mid', 'rtl', 'xviMid.sv'),
                 f'.XVI_GAIN({TOP_OWN_GAIN})', 'xviTop')):
            if stray in read(work, *parts):
                problems.append(f"{os.path.join(*parts)}: carries {stray!r}, "
                                f"a value only {owner} bound")
        for problem in problems:
            print(f"  FAIL: {problem}")
        if not problems:
            print(f"  PASS: xviTop emits vTop at {TOP_OWN_GAIN} and xviMid "
                  f"emits vMid at {MID_OWN_GAIN}; neither build emits the "
                  f"other's label")
        return not problems
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_each_build_runs_at_the_gain_it_declared():
    """The emitted numbers are consumed, not merely emitted. Both integrators'
    designs are built and run, and every sample reaching a sink carries the gain
    that build's own project bound. xviMid's leaves are then re-run as Verilated
    RTL, so the model and the RTL of one build are held to the same numbers.
    xviTop's Verilated build cannot run: its manifest resolves xviMid's wrapper
    tops to the leaf IP's directory, where xviMid never scaffolds them."""
    header("each build runs at the gain its own project declared")
    work = copy_fixture('xvi_runtime_')
    try:
        failure = build(work)
        if failure:
            print(f"  FAIL: {failure}")
            return False
        problems = list()
        for project, sinks in (('top', TOP_SINKS), ('mid', MID_SINKS)):
            result = make(work, 'run', os.path.join(project, 'rundir'))
            output = result.stdout + result.stderr
            if result.returncode != 0:
                problems.append(f"{project} model run failed "
                                f"(rc={result.returncode})\n{output}")
                continue
            problems.extend(f"{project} model: {problem}"
                            for problem in observations(output, sinks))

        verilated = make(work, 'all', os.path.join('mid', 'rundir'),
                         extra=('VL_DUT=1',))
        if verilated.returncode != 0:
            problems.append(f"mid Verilated build failed "
                            f"(rc={verilated.returncode})\n"
                            f"{verilated.stdout}\n{verilated.stderr}")
        else:
            binary = os.path.join(work, 'mid', 'rundir', 'build', 'run')
            env = os.environ.copy()
            env['NO_COLOR'] = '1'
            for leaf in MID_LEAVES:
                result = subprocess.run(
                    [binary, MID_TB_TOP, '--vlInst', leaf],
                    capture_output=True, text=True, timeout=600, env=env)
                output = result.stdout + result.stderr
                if result.returncode != 0:
                    problems.append(f"mid run with {leaf} as RTL failed "
                                    f"(rc={result.returncode})\n{output}")
                    continue
                # The selected instance logs its own construction only when the
                # SystemC model is what got built, so its absence is the proof
                # the RTL carried the samples.
                if f"Instance {leaf} initialized." in output:
                    problems.append(f"{leaf} ran its SystemC model, so the RTL "
                                    f"never carried a sample")
                problems.extend(f"mid with {leaf} as RTL: {problem}"
                                for problem in observations(output, MID_SINKS))

        for problem in problems:
            print(f"  FAIL: {problem}")
        if not problems:
            print(f"  PASS: xviTop's sinks ran at XVI_GAIN {TOP_GAIN} and "
                  f"{TOP_OWN_GAIN}, xviMid's at {MID_GAIN} and {MID_OWN_GAIN} "
                  f"in the model and again with each leaf as Verilated RTL")
        return not problems
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_all_tests():
    print("\n" + "="*70)
    print("TWO INTEGRATORS DECLARING VARIANTS OF ONE REUSABLE IP")
    print("="*70)

    tests = [
        test_collapse_drops_the_building_project,
        test_a_label_only_the_other_integrator_declared_reaches_this_build,
        test_emitted_artifacts_carry_the_declaring_project_value,
        test_other_integrator_keeps_its_own_binding,
        test_each_build_emits_only_the_label_it_declared,
        test_each_build_runs_at_the_gain_it_declared,
    ]
    results = []
    for test_func in tests:
        try:
            results.append((test_func.__name__, test_func()))
        except Exception as e:
            print(f"\n  EXCEPTION in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    print("\n" + "="*70 + "\nTEST SUMMARY\n" + "="*70)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n  Passed: {passed}/{len(results)}")
    if passed == len(results):
        print("\n  ALL TESTS PASSED!")
        return 0
    print("\n  SOME TESTS FAILED")
    return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
