#!/usr/bin/env python3
"""T2a.1 proof gate: the projectCreate-derived build directory set
(.gen/build.mk) reproduces today's makefile glob set for functional projects.

The rundir makefiles discover build inputs by globbing fixed functional roots:
  C++ : find_cpp_source_directories(base model registrar fw tb)
  SV  : find over (rtl, verif/vl_wrap)
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
"""
import os
import re
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # builder/base
EXAMPLES_DIR = os.path.join(BASE_DIR, 'examples')
sys.path.insert(0, BASE_DIR)
from config.createBuildManifest import _projectScopedSegment  # noqa: E402

# pySocket: not migrated to yamlFormat: 2 (same skip as functional_layout_regression.sh).
# mixed: excluded pending its registrar->module migration (blockFRegistrar.cpp lacks --parent).
SKIP = {'pySocket', 'mixed'}

# C++ and SV glob roots the makefiles use today (a2c-systemc.mk PRJ_SRC_DIRS and
# a2c-common.mk SV_GEN_FILES roots).
CPP_GLOB_ROOTS = ('base', 'model', 'registrar', 'fw', 'tb')
SV_GLOB_ROOTS = ('rtl', 'verif/vl_wrap')

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
        return False, ['generation failed']
    mk = os.path.join(exdir, '.gen', 'build.mk')
    if not os.path.isfile(mk):
        return False, ['.gen/build.mk not emitted']
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
    orphans = sorted(os.path.relpath(d, repo_root) for d in missing if is_known_orphan(repo_root, d))
    anticipated = sorted(os.path.relpath(d, repo_root) for d in extra)
    return (not problems), problems, orphans, anticipated


def check_hierarchical_vl_wrap_path():
    layout = {
        'mode': 'hierarchical',
        'prj': '/tmp/demo/prj',
        'segments': {
            'vl_wrap': {'path': 'verif'},
        },
    }
    vl_dir = _projectScopedSegment(layout, 'vl_wrap')
    return vl_dir == '/tmp/demo/prj/verif'


def main():
    failures = []
    if not check_hierarchical_vl_wrap_path():
        print('  [FAIL ] hierarchical-vl path')
        print('           - vl_wrap manifest path must be under prj/verif')
        failures.append('hierarchical-vl path')
    else:
        print('  [OK   ] hierarchical-vl path')
    for name in discover_examples():
        ok, problems, *rest = check_example(name)
        orphans = rest[0] if rest else []
        anticipated = rest[1] if len(rest) > 1 else []
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
    if failures:
        print(f'FAIL: manifest dir set diverges from glob for: {", ".join(failures)}')
        return 1
    print('PASS: manifest reproduces the functional glob dir set (orphans excepted).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
