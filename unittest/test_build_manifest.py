#!/usr/bin/env python3
"""T2a.1 proof gate: the projectCreate-derived build directory set
(.gen/build.mk) reproduces today's makefile glob set for functional projects.

The rundir makefiles discover build inputs by globbing fixed functional roots:
  C++ : find_cpp_source_directories(base model registrar fw tb)
  SV  : find over (rtl, verif). The verilated wrappers live under the `verif`
        segment: functional layout nests them in a `verif/vl_wrap/` subdir,
        hierarchical layout places them directly under each node's `verif/`.
        Walking the `verif` root recurses into either.
T2a.2 will replace those globs with the generated manifest, so before deleting
anything we prove the manifest covers the same directories. The only tolerated
deltas are the project ORPHANS the makefiles pick up only because their glob
root is a parent of a fileMap segment:
  - fw/src           : hand-authored integration firmware (fwIpMain), no fileMap
                       entry; the C++ glob root `fw` recurses into it.
  - verif/vl_wrap    : the verilated entry (vl_wrap aggregator + sc_main); the
                       manifest carries it as A2C_VL_WRAP_ENTRY / a wrap dir.
Any other missing directory (the build compiles files the manifest would drop)
is a fail.

The manifest may also list dirs the glob does not (a parameterizable block whose
trampoline/source has not been scaffolded by `make newmodule` yet - the manifest
derives intent from the fileMap, the glob only sees files already on disk). Every
manifest dir lives within a glob-scanned subtree, so such an "extra" dir is
necessarily empty on disk and its `wildcard $(dir)/*` compiles nothing - harmless
for T2a.2. The gate confirms each extra dir holds no source files; a non-empty
extra would mean the role->root mapping misroutes and is a fail.

Run from anywhere; regenerates each example (clean + db + gen) so both the
manifest and the on-disk generated files are current.

Because this suite is the one that runs the real generator over every example, it
also gates the CONTENT of the generated regions whose include baseline is a
recorded decision: the tb External's `tbExternalModuleHeader` global module
fragment, the block and context module units' global module fragments, and the
`<block>Config.cpp` prerequisites region. See REGION_GATE_* below.
"""
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # builder/base
EXAMPLES_DIR = os.path.join(BASE_DIR, 'examples')
sys.path.insert(0, BASE_DIR)
from pysrc.processYaml import projectCreate  # noqa: E402

# pySocket: not migrated to yamlFormat: 2 (same skip as functional_layout_regression.sh).
SKIP = {'pySocket'}

# C++ and SV glob roots the makefiles use today (a2c-systemc.mk PRJ_SRC_DIRS and
# a2c-common.mk SV_GEN_FILES roots). The `verif` root covers the verilated
# wrappers in both layouts: functional nests them under verif/vl_wrap/, while
# hierarchical places them directly under each node's verif/ (the vl_wrap
# segment path is `verif`); os.walk recurses into either.
CPP_GLOB_ROOTS = ('base', 'model', 'registrar', 'fw', 'tb')
SV_GLOB_ROOTS = ('rtl', 'verif')

CPP_EXTS = ('.cpp', '.h', '.cppm')
SV_EXTS = ('.sv', '.svh')


def find_source_dirs(repo_root, roots, exts):
    found = set()
    for root in roots:
        base = os.path.join(repo_root, root)
        for dirpath, _dirs, files in os.walk(base, followlinks=True):
            if any(f.endswith(exts) for f in files):
                found.add(os.path.abspath(dirpath))
    return found


# Directory names that mark a project root: any functional glob root carries a
# project's own source tree. A composed example nests one root per sub-project.
PROJECT_ROOT_MARKERS = set(CPP_GLOB_ROOTS) | {r.split('/')[0] for r in SV_GLOB_ROOTS}


def discover_project_roots(example_root):
    """Composition-aware root set: the example root plus every nested
    child-project root. A child-project root is a subdir that carries its own
    functional glob tree (its own base/model/... beside a project file), which
    is how a composed example embeds a sub-project. Discovered generically so
    single-project examples yield only the example root (glob set unchanged)."""
    roots = [example_root]
    for dirpath, dirs, _files in os.walk(example_root):
        # Prune build/cache mirrors so generated copies are not seen as roots.
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'rundir']
        if dirpath == example_root:
            continue
        if any(d in PROJECT_ROOT_MARKERS for d in dirs):
            roots.append(os.path.abspath(dirpath))
    return roots


def parse_manifest(mk_path):
    vals = {}
    with open(mk_path) as f:
        for line in f:
            m = re.match(r'^(A2C_\w+)\s*:=\s*(.*)$', line.rstrip('\n'))
            if m:
                vals[m.group(1)] = m.group(2).split()
    return vals


def is_known_orphan(repo_root, d):
    rel = os.path.relpath(d, repo_root)
    parts = rel.split(os.sep)
    # fwIpMain integration firmware lives in fw/src (no fileMap entry).
    if rel == 'fw/src':
        return True
    # A composed child project's own verilated entry (its nested verif/vl_wrap
    # sc_main + aggregator) is standalone-only; the composed sim runs a single
    # top entry, so the child entry dir is on disk but absent from the manifest.
    # The top project's own verif/vl_wrap IS carried, so exclude only a nested one.
    if len(parts) > 2 and parts[-2:] == ['verif', 'vl_wrap']:
        return True
    return False


# The tb External's global-module-fragment region, and the baseline
# templates/systemc/testbench.py::ext_module_header must emit into it. A header
# belongs in the region only when a GENERATED line names a symbol from it:
# systemc.h for sc_module, logging.h for the generated `logBlock log_;` member,
# instanceFactory.h for `createInstance` in the generated ctor init list. The
# region also carries DB-directed entries (channel, per-context Config and thunker
# headers), so it is asserted by membership, not equality.
#
# workerThread.h must NOT be there: no generated line names a `worker*` symbol, so
# a stimulus thread's prerequisite is USER content, owned by the `// user #includes
# here` slot below the region - which is where the testbench-family migration
# relocates it, and where two examples carry it today. If the template re-emitted
# it, every migrated External would include it twice and the migration's relocation
# would be wrong.
GEN_BEGIN = '// GENERATED_CODE_BEGIN'
GEN_END = '// GENERATED_CODE_END'

EXT_GMF_MARKER = f'{GEN_BEGIN} --template=moduleScaffold --section=tbExternalModuleHeader'
EXT_GMF_REQUIRED = ('#include "systemc.h"', '#include "logging.h"',
                    '#include "instanceFactory.h"')
EXT_GMF_FORBIDDEN = ('#include "workerThread.h"',)

# The block module unit's global module fragment
# (moduleScaffold::blockModuleHeader). Same rule: systemc.h for the SC_MODULE
# class and its sc_ port types, logging.h for the generated `logBlock log_;`. The
# region also carries DB-directed dependency headers (channels, Config), so it is
# asserted by membership.
#
# The three forbidden headers must NOT be there: no generated line in a block
# `.cppm` names a Q_ASSERT macro, a std::<algorithm> call or a bitTwiddling
# symbol, so a block body that uses one owns the include in its `// user #includes
# here` slot. Re-emitting them would double every relocated copy and make the
# baseline unfalsifiable.
BLOCK_GMF_MARKER = f'{GEN_BEGIN} --template=moduleScaffold --section=blockModuleHeader'
BLOCK_GMF_REQUIRED = ('#include "systemc.h"', '#include "logging.h"')
BLOCK_GMF_FORBIDDEN = ('#include "bitTwiddling.h"', '#include "q_assert.h"',
                       '#include <algorithm>')

# The context types module unit's global module fragment
# (moduleScaffold::moduleHeader). An #include is legal only there, so it carries
# every header the whole file needs - but derived, not assumed: systemc.h always
# (its sc types and the uint*_t even a struct-less context's typedefs need), and
# the struct-feature set only when the context actually declares structures. A
# struct-less context is the case that pins the derivation: its `structures`
# region renders empty, and it must carry systemc.h and nothing the struct
# regions would have needed.
#
# bitTwiddling.h is required WITH structures (codeMapping's fw_pack is inline in
# module mode) but is NOT forbidden without them: the emitter also gates it on the
# clog2 fact, which is independent of the structure set and which this test cannot
# observe, so a struct-less context declaring a log2-derived width legitimately
# carries it.
CTX_GMF_MARKER = f'{GEN_BEGIN} --template=moduleScaffold --section=moduleHeader'
CTX_STRUCTURES_MARKER = f'{GEN_BEGIN} --template=structures'
CTX_GMF_REQUIRED = ('#include "systemc.h"',)
CTX_GMF_STRUCT_REQUIRED = ('#include "logging.h"', '#include <algorithm>',
                           '#include "q_assert.h"', '#include "bitTwiddling.h"')
CTX_GMF_STRUCTLESS_FORBIDDEN = ('#include "logging.h"', '#include <algorithm>',
                                '#include "q_assert.h"')

# The `<block>Config.cpp` prerequisites region
# (testbench.py::tb_config_prerequisites). `<string>` is named directly by the
# generated registration lambda; the two factory headers and the endOfTest import
# are named or are the scaffolded bodies' prerequisites. systemc.h must NOT be
# there: no generated line names a SystemC symbol, and instanceFactory.h supplies
# it transitively for the scaffolded bodies.
TBCFG_MARKER = f'{GEN_BEGIN} --template=tbConfig --section=prerequisites'
TBCFG_REQUIRED = ('#include <string>', '#include "instanceFactory.h"',
                  '#include "testBenchConfigFactory.h"', 'import a2c.endOfTest;')
TBCFG_FORBIDDEN = ('#include "systemc.h"',)


def gen_region(path, marker):
    """The stripped lines of the generated region whose begin line IS `marker`, or
    None if the file carries no such region. Matched whole so a bare region command
    cannot also match a `--section=` variant of the same template."""
    region = []
    inside = False
    with open(path) as fh:
        for line in fh:
            s = line.strip()
            if inside:
                if s == GEN_END:
                    return region
                region.append(s)
            elif s == marker:
                inside = True
    return region if inside else None


def authored_files(repo_root, suffix):
    """Authored-tree files ending in `suffix`; build/cache mirrors skipped."""
    for dirpath, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'rundir']
        for name in sorted(files):
            if name.endswith(suffix):
                yield os.path.join(dirpath, name)


def _assertRegion(problems, rel, label, region, required, forbidden):
    missing = [h for h in required if h not in region]
    if missing:
        problems.append(f'{rel}: {label} region missing ' + ', '.join(missing))
    present = [h for h in forbidden if h in region]
    if present:
        problems.append(f'{rel}: {label} region emits user-slot content ' +
                        ', '.join(present))


def check_region_content(repo_root):
    """Assert the include baseline of every generated region whose content is a
    recorded decision. Returns (problems, {gate: regions checked})."""
    problems = []
    counts = {'External GMF': 0, 'block GMF': 0, 'context GMF': 0,
              'tbConfig prerequisites': 0}

    for path in authored_files(repo_root, 'External.cppm'):
        rel = os.path.relpath(path, repo_root)
        region = gen_region(path, EXT_GMF_MARKER)
        if region is None:
            problems.append(f'{rel}: no {EXT_GMF_MARKER} region')
            continue
        counts['External GMF'] += 1
        _assertRegion(problems, rel, 'External GMF', region,
                      EXT_GMF_REQUIRED, EXT_GMF_FORBIDDEN)

    for path in authored_files(repo_root, '.cppm'):
        rel = os.path.relpath(path, repo_root)
        region = gen_region(path, BLOCK_GMF_MARKER)
        if region is not None:
            counts['block GMF'] += 1
            _assertRegion(problems, rel, 'block GMF', region,
                          BLOCK_GMF_REQUIRED, BLOCK_GMF_FORBIDDEN)
        region = gen_region(path, CTX_GMF_MARKER)
        if region is not None:
            counts['context GMF'] += 1
            # A struct-less context renders its `structures` region as one blank
            # line, so presence of the region is not the test - content is.
            hasStructures = any(gen_region(path, CTX_STRUCTURES_MARKER) or ())
            required = CTX_GMF_REQUIRED
            forbidden = ()
            if hasStructures:
                required += CTX_GMF_STRUCT_REQUIRED
            else:
                forbidden = CTX_GMF_STRUCTLESS_FORBIDDEN
            _assertRegion(problems, rel, 'context GMF', region,
                          required, forbidden)

    for path in authored_files(repo_root, 'Config.cpp'):
        rel = os.path.relpath(path, repo_root)
        region = gen_region(path, TBCFG_MARKER)
        if region is None:
            continue
        counts['tbConfig prerequisites'] += 1
        _assertRegion(problems, rel, 'tbConfig prerequisites', region,
                      TBCFG_REQUIRED, TBCFG_FORBIDDEN)

    return problems, counts


def discover_examples():
    out = []
    for name in sorted(os.listdir(EXAMPLES_DIR)):
        d = os.path.join(EXAMPLES_DIR, name)
        if name in SKIP:
            continue
        if os.path.isfile(os.path.join(d, 'Makefile')):
            out.append(name)
    return out


def regen(exdir):
    for tgt in ('clean', 'db', 'gen'):
        r = subprocess.run(['make', tgt], cwd=exdir,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode != 0 and tgt != 'clean':
            return False
    return True


def check_example(name):
    exdir = os.path.join(EXAMPLES_DIR, name)
    if not regen(exdir):
        return False, ['generation failed'], [], [], {}
    mk = os.path.join(exdir, '.gen', 'build.mk')
    if not os.path.isfile(mk):
        return False, ['.gen/build.mk not emitted'], [], [], {}
    man = parse_manifest(mk)
    repo_root = exdir

    glob_dirs = set()
    for proot in discover_project_roots(repo_root):
        glob_dirs |= find_source_dirs(proot, CPP_GLOB_ROOTS, CPP_EXTS)
        glob_dirs |= find_source_dirs(proot, SV_GLOB_ROOTS, SV_EXTS)
    manifest_dirs = set(man.get('A2C_SC_SRC_DIRS', []) +
                        man.get('A2C_SV_SRC_DIRS', []) +
                        man.get('A2C_VL_WRAP_DIRS', []))

    missing = glob_dirs - manifest_dirs       # build sees today, manifest omits
    extra = manifest_dirs - glob_dirs         # manifest anticipates (must be empty on disk)

    problems = []
    unexplained = [d for d in missing if not is_known_orphan(repo_root, d)]
    if unexplained:
        problems.append('missing (not a known orphan): ' +
                        ', '.join(sorted(os.path.relpath(d, repo_root) for d in unexplained)))
    # An extra dir is only a problem if it actually holds source files on disk;
    # since manifest dirs live within glob-scanned subtrees, a non-empty extra
    # means the role->root mapping misrouted.
    extra_nonempty = []
    for d in extra:
        if os.path.isdir(d) and any(f.endswith(CPP_EXTS + SV_EXTS) for f in os.listdir(d)):
            extra_nonempty.append(d)
    if extra_nonempty:
        problems.append('extra non-empty (misrouted): ' +
                        ', '.join(sorted(os.path.relpath(d, repo_root) for d in extra_nonempty)))
    # Content gate on the freshly generated include-baseline regions.
    regionProblems, regionCounts = check_region_content(repo_root)
    problems += regionProblems

    orphans = sorted(os.path.relpath(d, repo_root) for d in missing if is_known_orphan(repo_root, d))
    anticipated = sorted(os.path.relpath(d, repo_root) for d in extra)
    return (not problems), problems, orphans, anticipated, regionCounts


def check_hierarchical_vl_wrap_path():
    # The verilator-wrap (buildGroup 'vl') wrapper SOURCES are node-relative like
    # every other block segment: emission (expandNewModulePath) joins the bare
    # segment name onto each block's node dir -> <node>/verif. The whole-design
    # build-output dir is no longer a layout/manifest fact; it is make
    # infrastructure (rundir/build/vl driven by a2c-vl-build-entry.mk), so only
    # the node-relative source segment is asserted here.
    pc = object.__new__(projectCreate)
    dirMacros = {'root': '/tmp/demo'}
    fileGeneration = {
        'layout': 'hierarchical',
        'buildGroups': {'model': 'sc', 'vl_wrap': 'vl'},
        'fileMap': {
            'block': {'basePath': 'model'},
            'vlSvWrap': {'basePath': 'vl_wrap'},
        },
        'hierarchicalDirs': {
            'model': 'model',
            'vl_wrap': 'verif',
            'yaml': 'yaml',
            'prj': '$root/prj',
            'rundir': '$root/rundir',
            'include': '$root/include',
        },
    }
    layout = pc._buildLayoutFor(dirMacros, fileGeneration)
    return (layout['segments']['vl_wrap']['path'] == 'verif' and
            layout['segments']['model']['path'] == 'model')


def main():
    failures = []
    if not check_hierarchical_vl_wrap_path():
        print('  [FAIL ] hierarchical-vl path')
        print('           - vl_wrap source segment must be node-relative "verif" (build dir is make infra, not manifest)')
        failures.append('hierarchical-vl path')
    else:
        print('  [OK   ] hierarchical-vl path')
    examples = discover_examples()
    # Examples are disjoint trees (each has its own DB/.gen and builds in its
    # own cwd), so regenerate them concurrently. Cap workers to a quarter of the
    # CPUs (min 1): each `make` can itself use multiple cores, so an unbounded
    # fan-out would oversubscribe. Results are collected out of order then
    # printed in sorted example order for a deterministic report.
    max_workers = min(len(examples), max(1, (os.cpu_count() or 4) // 4))
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futs = {pool.submit(check_example, name): name for name in examples}
        for fut in as_completed(futs):
            results[futs[fut]] = fut.result()
    regionTotals = dict()
    for name in examples:
        ok, problems, orphans, anticipated, counts = results[name]
        for gate, n in counts.items():
            regionTotals[gate] = regionTotals.get(gate, 0) + n
        tag = 'OK   ' if ok else 'FAIL '
        notes = []
        if orphans:
            notes.append('orphans: ' + ', '.join(orphans))
        if anticipated:
            notes.append('anticipated(empty): ' + ', '.join(anticipated))
        note = (' [' + '; '.join(notes) + ']') if notes else ''
        print(f'  [{tag}] {name:<14}{note}')
        if not ok:
            for p in problems:
                print(f'           - {p}')
            failures.append(name)
    print()
    # A fileMap or naming change that stopped producing one of the gated artifacts
    # would leave that content gate silently asserting nothing, so require every
    # gate to have found regions.
    for gate, n in sorted(regionTotals.items()):
        if not n:
            print(f'  [FAIL ] {gate} regions: none found across the examples')
            failures.append(f'{gate} regions')
        else:
            print(f'  [OK   ] {gate} regions: {n} checked')
    if failures:
        print('FAIL: manifest dir set diverges from glob, or a generated region '
              f'content gate failed, for: {", ".join(failures)}')
        return 1
    print('PASS: manifest reproduces the functional glob dir set (orphans excepted).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
