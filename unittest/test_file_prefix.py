#!/usr/bin/env python3
"""Project filename prefixes: svFilePrefix, scFilePrefix and fwFilePrefix.

Each project's prefix goes in front of its own generated filenames. An SV
module or package is named like its file, so the SV prefix renames the design
units too. C++ class, module and namespace names never change.

Works on private copies of examples/simple_ip, a root that composes two child
projects (ip and common) with RTL, Verilated wrappers, firmware headers and
parameterized registrars:
- omitted keys and "" give the same database and build manifest;
- each language's prefix, set alone on ip, renames only that language's files;
- the tree origin/main generated migrates project by project (common, ip, then
  the root), the root leaves its children's files alone, and the root's
  Verilated build runs, with no prefix and with ip and the root prefixed; the
  prefixed run also keeps the user code in the moved files and ip spells the
  same names standalone and composed;
- main's legacy testbench .h/.cpp pairs, which never had a prefix, are ported
  into the prefixed .cppm files;
- a file present at both its unprefixed and prefixed names halts migrate
  before newmodule, and the unprefixed file survives;
- an unprefixed name that is also another artifact's current name halts
  migrate before any file moves, both after a block is added and from main;
- a project whose files already sit at their prefixed names migrates again
  with no TODO, even when one file's unprefixed name is another's current file;
- a prefix that makes two projects' blocks or packages share an SV name is
  rejected naming both projects, and so are two blocks that share a C++ name
  while their SV names differ;
- a block foo_package beside a context foo fails make db, because SV modules
  and packages share one namespace and one file stem;
- an svFilePrefix or scFilePrefix holding '$', and a block whose SV name
  holds '$', fail make db;
- make db rejects two Config declarations sharing one name, a block named
  like another block's Verilated wrapper, a package name that is not an SV
  identifier and an RTL block named like an SV keyword;
- model-only blocks emit no SV module, so their names never collide with one;
- the orphan sweep never deletes a file that is another artifact's current
  file, and reports it;
- a vlSvWrapBody entry with its own name gives the body file and module that
  name, and the variant top includes it;
- a new project file lists the three keys as comments.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

from _addrctl_helpers import base_dir, test_dir
import pysrc.arch2codeGlobals as g
from pysrc import checkSvNames, migrateFilePrefix, migrateOrphans
from pysrc.artifactPaths import currentArtifactRows
from pysrc.newProject import projectFileTemplate
from pysrc.processYaml import projectOpen


SOURCE = os.path.join(base_dir, 'examples', 'simple_ip')
NESTED_FIXTURE = os.path.join(test_dir, 'fixtures', 'nested-ownership')
# Project dir (relative to the copy) -> its project file.
PROJECT_FILES = {
    '.': 'prj/yaml/project.yaml',
    'ip': 'prj/yaml/ipProject.yaml',
    'common': 'prj/yaml/commonProject.yaml',
}
PREFIX_KEYS = {'sv': 'svFilePrefix', 'sc': 'scFilePrefix', 'fw': 'fwFilePrefix'}
MARKER = 'FILE_PREFIX_USER_MARKER'
# origin/main before filename prefixes; migrate must take its projects as input.
MAIN_COMMIT = 'd7897c62'


def env():
    e = os.environ.copy()
    e['NO_COLOR'] = '1'
    return e


def run(cmd, cwd=None):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=3600,
                          env=env(), cwd=cwd)


def make(directory, *targets):
    result = run(['make', '-C', directory, '-j8', *targets])
    if result.returncode != 0:
        raise AssertionError(f"make {' '.join(targets)} failed in {directory}:\n"
                             f"{result.stdout}\n{result.stderr}")
    return result.stdout + result.stderr


def copy_simple_ip():
    work = tempfile.mkdtemp(prefix='file_prefix_', dir=test_dir)
    shutil.copytree(SOURCE, work, dirs_exist_ok=True, ignore=shutil.ignore_patterns(
        'build', '.gen', '*.db', '*.db-*', 'compile_commands.json'))
    point_repo_root(work)
    return work


def extract_main_simple_ip():
    # examples/simple_ip as origin/main generated it, before filename prefixes.
    work = tempfile.mkdtemp(prefix='file_prefix_main_', dir=test_dir)
    archive = subprocess.run(['git', '-C', base_dir, 'archive', MAIN_COMMIT, 'examples/simple_ip'],
                             capture_output=True, check=True)
    subprocess.run(['tar', '-x', '-C', work, '--strip-components=2'],
                   input=archive.stdout, check=True)
    point_repo_root(work)
    return work


def point_repo_root(work):
    # Each Makefile names its project root from the git top level; point it at
    # the copy instead.
    for project in PROJECT_FILES:
        root = os.path.normpath(os.path.join(work, project))
        for relpath in ('Makefile', 'rundir/Makefile', 'rtl/Makefile',
                        'include/make/shared.mk'):
            path = os.path.join(root, relpath)
            if not os.path.exists(path):
                continue
            with open(path) as f:
                lines = f.read().splitlines(keepends=True)
            hits = [i for i, line in enumerate(lines) if line.startswith('REPO_ROOT = ')]
            if len(hits) != 1:
                raise AssertionError(f"{path} has no single REPO_ROOT assignment")
            lines[hits[0]] = f'REPO_ROOT = {root}\n'
            with open(path, 'w') as f:
                f.write(''.join(lines))


def remove(work):
    # An open database file on NFS leaves a .nfs placeholder that keeps its
    # directory from being removed, so the last connection is closed first.
    if g.db is not None:
        g.db.close()
        g.db = None
    shutil.rmtree(work)


def set_prefixes(work, project, prefixes):
    # Top-level keys appended after the rest of the project file.
    path = os.path.join(work, project, PROJECT_FILES[project])
    with open(path, 'a') as f:
        f.write('\n')
        for kind, value in prefixes.items():
            f.write(f'{PREFIX_KEYS[kind]}: "{value}"\n')


def db_path(work, project):
    (name,) = [n for n in os.listdir(os.path.join(work, project))
               if n.endswith('.db') and not n.startswith('.')]
    return os.path.join(work, project, name)


def open_db(work, project):
    return projectOpen(db_path(work, project))


def rebuild_db(work, project):
    directory = os.path.join(work, project)
    run(['make', '-C', directory, 'clean'])
    make(directory, 'db')


def name_facts(prj):
    # Everything the prefix can reach: the name maps, every artifact path and
    # the manifest written for make.
    rows = currentArtifactRows(prj)
    with open(os.path.join(prj.config.getConfig('DIRS')['root'], '.gen', 'build.mk')) as f:
        manifest = f.read()
    return {
        'svModules': prj.blockSvModuleName,
        'svPackages': prj.contextSvPackageName,
        'cppModules': prj.blockModuleName,
        'cppContexts': prj.contextModuleIdentity,
        'files': sorted(p for row in rows for p in row['files'].values()),
        'manifest': manifest,
    }


def expected_kind(row):
    # The spec, restated independently of artifactPaths.fileNamePrefix.
    fileDef = row['fileDef']
    if row['mode'] == 'project':
        return None
    if {'sv', 'svh'} & set(fileDef['ext'].values()):
        return 'sv'
    if fileDef['basePath'] == 'fwInc':
        return 'fw'
    return 'sc'


def check_omitted_equals_empty():
    work = copy_simple_ip()
    try:
        rebuild_db(work, '.')
        omitted = name_facts(open_db(work, '.'))
        for project in PROJECT_FILES:
            set_prefixes(work, project, {'sv': '', 'sc': '', 'fw': ''})
        rebuild_db(work, '.')
        empty = name_facts(open_db(work, '.'))
        for key in omitted:
            if omitted[key] != empty[key]:
                print(f"FAIL: '{key}' differs between omitted prefix keys and \"\"")
                return False
        print("PASS: omitted prefix keys and \"\" give identical names, paths and manifest")
        return True
    finally:
        remove(work)


def check_each_language_alone():
    work = copy_simple_ip()
    try:
        rebuild_db(work, '.')
        baseline = name_facts(open_db(work, '.'))
        ok = True
        for kind in ('sv', 'sc', 'fw'):
            prefix = f'solo{kind}_'
            project = os.path.join(work, 'ip', PROJECT_FILES['ip'])
            with open(project) as f:
                original = f.read()
            set_prefixes(work, 'ip', {kind: prefix})
            rebuild_db(work, '.')
            prj = open_db(work, '.')
            renamed = 0
            for row in currentArtifactRows(prj):
                for path in row['files'].values():
                    base = os.path.basename(path)
                    want = row['owner'] == 'ip' and expected_kind(row) == kind
                    if base.startswith(prefix) != want:
                        print(f"FAIL: {kind} prefix alone: {path} "
                              f"{'lacks' if want else 'carries'} '{prefix}'")
                        ok = False
                    renamed += want
            if renamed == 0:
                print(f"FAIL: {kind} prefix alone renamed no ip artifact")
                ok = False
            if prj.blockModuleName != baseline['cppModules'] \
                    or prj.contextModuleIdentity != baseline['cppContexts']:
                print(f"FAIL: {kind} prefix alone changed a C++ module identity")
                ok = False
            ipBlocks = {k for k, r in prj.data['blocks'].items()
                        if prj.contextOwningProject[r['_context']] == 'ip'}
            for blockKey, name in prj.blockSvModuleName.items():
                want = f'{prefix}{baseline["svModules"][blockKey]}' \
                    if kind == 'sv' and blockKey in ipBlocks else baseline['svModules'][blockKey]
                if name != want:
                    print(f"FAIL: {kind} prefix alone gave SV module {name}, expected {want}")
                    ok = False
            with open(project, 'w') as f:
                f.write(original)
            if ok:
                print(f"PASS: {kind}FilePrefix alone renames only ip's {kind} files "
                      f"({renamed} files) and leaves C++ names alone")
        return ok
    finally:
        remove(work)


def add_marker(path, before):
    # A user line just before the first line that equals `before`.
    with open(path) as f:
        lines = f.read().splitlines(keepends=True)
    (index,) = [i for i, line in enumerate(lines) if line.strip() == before][:1]
    lines.insert(index, f'// {MARKER}\n')
    with open(path, 'w') as f:
        f.write(''.join(lines))


def export_module_lines(path):
    with open(path) as f:
        return [line for line in f if line.startswith('export module')]


def tree_digest(directory):
    # Every source file below directory with its content, build output aside.
    digest = dict()
    for root, dirs, names in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in ('.gen', 'build', 'obj_dir')]
        for name in names:
            if name.endswith(('.db', '.log')):
                continue
            path = os.path.join(root, name)
            with open(path, 'rb') as f:
                digest[os.path.relpath(path, directory)] = f.read()
    return digest


def migrate_composed(work, beforeRoot):
    """Migrate each project from its own directory, children first. Returns
    False and prints why when root migrate touched a child's file or left
    manual items other than the known one."""
    for project in ('common', 'ip'):
        run(['make', '-C', os.path.join(work, project), '-j8', 'migrate'])
    beforeRoot()
    children = {project: tree_digest(os.path.join(work, project)) for project in ('common', 'ip')}
    # The first migrate exits 1 while it reports the testbench ports it then
    # performs, so its exit code is not the verdict; the dry-run reports are.
    run(['make', '-C', work, '-j8', 'migrate'])
    ok = True
    for project, digest in children.items():
        after = tree_digest(os.path.join(work, project))
        changed = sorted(p for p in digest.keys() | after.keys() if digest.get(p) != after.get(p))
        if changed:
            print(f"FAIL: the root migrate changed {project}'s files: {changed}")
            ok = False
    # simple_ip's root always asks for a decision on ip/tb/ip, prefix or not.
    expected = {'common': set(), 'ip': set(),
                '.': {(migrateOrphans.TODO_UNMANIFESTED_SRC_DIR, os.path.join('ip', 'tb', 'ip'))}}
    for project, want in expected.items():
        prj = open_db(work, project)
        orphans = migrateOrphans.sweepOrphans(prj)
        moves = migrateFilePrefix.moveRenamedFiles(prj)
        manual = {(item.kind, item.location) for item in orphans.manual + moves.manual}
        if manual != want or moves.applied:
            print(f"FAIL: after migrate, {project} still reports {sorted(manual)} "
                  f"and {len(moves.applied)} pending move(s)")
            ok = False
    make(work, 'gen')
    return ok


def check_sv_names_and_run(work, label):
    ok = True
    for project in PROJECT_FILES:
        checked, _, mismatches = checkSvNames.checkProject(os.path.join(work, project))
        for line in mismatches:
            print(f"FAIL: {label}: {project}: {line}")
            ok = False
        if checked == 0:
            print(f"FAIL: {label}: no SV file checked in {project}")
            ok = False
    runLog = make(os.path.join(work, 'rundir'), 'run-vl')
    if 'No error' not in runLog:
        print(f"FAIL: {label}: the root's Verilated run did not finish cleanly:\n{runLog[-3000:]}")
        ok = False
    return ok


def check_main_migrate_without_prefix():
    work = extract_main_simple_ip()
    try:
        ok = migrate_composed(work, lambda: None)
        ok = check_sv_names_and_run(work, 'no prefix') and ok
        if ok:
            print(f"PASS: main's ({MAIN_COMMIT}) simple_ip migrates child by child, the root "
                  f"leaves ip and common alone, and the Verilated run passes")
        return ok
    finally:
        remove(work)


def check_main_migrate_with_prefixes():
    work = extract_main_simple_ip()
    try:
        ip = os.path.join(work, 'ip')
        userFiles = {
            'rtl/ipStdDriver.sv': ('rtl/ipv_ipStdDriver.sv', 'endmodule: ip_ipStdDriver'),
            'model/ipStdDriver.cppm': ('model/ipc_ipStdDriver.cppm', None),
            'verif/ip_hdl_sc_wrapper.h': ('verif/ipc_ip_hdl_sc_wrapper.h', None),
            'fw/ipIncludesFW.cpp': ('fw/ipf_ipIncludesFW.cpp', None),
        }
        # main's firmware sources include their header outside the generated
        # regions, so the user renames that include, as for any user include.
        for stem in ('ipIncludesFW', 'ipTopIncludesFW'):
            edit(os.path.join(ip, 'fw', f'{stem}.cpp'), f'"{stem}.h"', f'"ipf_{stem}.h"')
        for old, (_new, before_line) in userFiles.items():
            path = os.path.join(ip, old)
            if before_line:
                add_marker(path, before_line)
            else:
                with open(path, 'a') as f:
                    f.write(f'// {MARKER}\n')
        set_prefixes(work, 'ip', {'sv': 'ipv_', 'sc': 'ipc_', 'fw': 'ipf_'})
        set_prefixes(work, '.', {'sv': 'top_'})

        def renameFwInclude():
            # The root's firmware includes ip's header by name.
            edit(os.path.join(work, 'fw', 'src', 'fwSimpleMain.h'),
                 '"ipIncludesFW.h"', '"ipf_ipIncludesFW.h"')

        ok = migrate_composed(work, renameFwInclude)
        for old, (new, _before) in userFiles.items():
            oldPath, newPath = os.path.join(ip, old), os.path.join(ip, new)
            if os.path.exists(oldPath) or not os.path.exists(newPath):
                print(f"FAIL: migrate did not move {old} to {new}")
                ok = False
                continue
            with open(newPath) as f:
                if MARKER not in f.read():
                    print(f"FAIL: migrate lost the user line in {new}")
                    ok = False
        with open(os.path.join(ip, 'rtl', 'ipv_ipStdDriver.sv')) as f:
            if 'endmodule: ipv_ipStdDriver' not in f.read():
                print("FAIL: the user endmodule label was not relabelled to ipv_ipStdDriver")
                ok = False
        unprefixed = os.path.join(SOURCE, 'ip', 'model', 'ipStdDriver.cppm')
        if export_module_lines(os.path.join(ip, 'model', 'ipc_ipStdDriver.cppm')) \
                != export_module_lines(unprefixed):
            print("FAIL: scFilePrefix changed the C++ module declaration")
            ok = False
        if not os.path.exists(os.path.join(ip, 'rtl', 'rtl.f')):
            print("FAIL: project-mode rtl/rtl.f was renamed")
            ok = False
        with open(os.path.join(work, 'rtl', 'top_simple_ip.sv')) as f:
            topRtl = f.read()
        if not re.search(r'^\s*module top_simple_ip\b', topRtl, re.M) \
                or not re.search(r'^ipv_ip\b', topRtl, re.M):
            print("FAIL: the root module is not top_simple_ip instantiating ipv_ip")
            ok = False
        standalone, composed = open_db(work, 'ip'), open_db(work, '.')
        for blockKey, name in standalone.blockSvModuleName.items():
            if composed.blockSvModuleName.get(blockKey, name) != name:
                print(f"FAIL: ip block {blockKey} is {name} standalone but "
                      f"{composed.blockSvModuleName[blockKey]} composed")
                ok = False
        ok = check_sv_names_and_run(work, 'prefixed') and ok
        if ok:
            print(f"PASS: main's ({MAIN_COMMIT}) simple_ip with ip at ipv_/ipc_/ipf_ under a top_ "
                  f"root migrates with user code intact, keeps its C++ names, and the "
                  f"Verilated run passes")
        return ok
    finally:
        remove(work)


def check_main_migrate_ports_legacy_tb_with_prefix():
    # main's ip testbench is a legacy External and Testbench .h/.cpp pair, and
    # its External holds a hand-written stimulusThread. Those files never had a
    # prefix, so migrate must find them at their bare names.
    work = extract_main_simple_ip()
    try:
        set_prefixes(work, 'ip', {'sc': 'ipc_'})
        run(['make', '-C', os.path.join(work, 'common'), '-j8', 'migrate'])
        result = run(['make', '-C', os.path.join(work, 'ip'), '-j8', 'migrate'])
        output = result.stdout + result.stderr
        tb = os.path.join(work, 'ip', 'tb', 'ip')
        ok = True
        left = [name for name in ('ipExternal.h', 'ipExternal.cpp', 'ipTestbench.h',
                                  'ipTestbench.cpp') if os.path.exists(os.path.join(tb, name))]
        if left:
            print(f"FAIL: migrate left the legacy testbench files {left} in tb/ip")
            ok = False
        external = os.path.join(tb, 'ipc_ipExternal.cppm')
        with open(external) as f:
            text = f.read()
        for line in ('SC_THREAD(stimulusThread);', 'payload.word[0] = 0xDEADBEEFCAFEBABEULL;',
                     'eot_.setEndOfTest(true);'):
            if line not in text:
                print(f"FAIL: {os.path.basename(external)} lacks the ported user line {line!r}")
                ok = False
        with open(os.path.join(tb, 'ipc_ipTestbench.cppm')) as f:
            if '// GENERATED_CODE_PARAM --block=ip --variant=variant0' not in f.read():
                print("FAIL: ipc_ipTestbench.cppm does not carry main's --variant=variant0")
                ok = False
        if not ok:
            print(output[-3000:])
        else:
            print("PASS: with scFilePrefix set, migrate ports main's legacy External and "
                  "Testbench pairs into ipc_ipExternal.cppm and ipc_ipTestbench.cppm")
        return ok
    finally:
        remove(work)


def run_nested(mutate):
    work = tempfile.mkdtemp(prefix='file_prefix_collision_', dir=test_dir)
    try:
        shutil.copytree(NESTED_FIXTURE, work, dirs_exist_ok=True)
        mutate(work)
        db = os.path.join(work, 'root.db')
        result = run([sys.executable, os.path.join(base_dir, 'arch2code.py'),
                      '--yaml', os.path.join(work, 'root', 'yaml', 'rootProject.yaml'),
                      '--db', db])
        return result.returncode, result.stdout + result.stderr
    finally:
        remove(work)


def edit(path, old, new):
    with open(path) as f:
        text = f.read()
    if old not in text:
        raise AssertionError(f"{path} lacks {old!r}")
    with open(path, 'w') as f:
        f.write(text.replace(old, new))


def check_collisions():
    childProject = os.path.join('child', 'yaml', 'childProject.yaml')
    childLeaf = os.path.join('child', 'yaml', 'childLeaf.yaml')
    rootTop = os.path.join('root', 'yaml', 'rootTop.yaml')

    def blockCollision(work):
        # Child RTL block 'Leaf' under prefix 'root' is spelled like root's 'rootLeaf'.
        edit(os.path.join(work, childLeaf), 'childLeafBlock', 'Leaf')
        edit(os.path.join(work, childLeaf), 'hasRtl: false', 'hasRtl: true')
        edit(os.path.join(work, rootTop), 'desc: "root-owned leaf block"\n        hasMdl: true\n'
             '        hasRtl: false', 'desc: "root-owned leaf block"\n        hasMdl: true\n'
             '        hasRtl: true')
        with open(os.path.join(work, childProject), 'a') as f:
            f.write('\nsvFilePrefix: root\n')

    def packageCollision(work):
        # Child context 'Top' under prefix 'root' is spelled like rootTop.yaml's
        # package, which its type makes rootTop.yaml emit.
        with open(os.path.join(work, childLeaf), 'a') as f:
            f.write('\nincludeName: Top\n')
        with open(os.path.join(work, rootTop), 'a') as f:
            f.write('\ntypes:\n    rootT: { width: 4, desc: "gives rootTop.yaml a package" }\n')
        with open(os.path.join(work, childProject), 'a') as f:
            f.write('\nsvFilePrefix: root\n')

    def cppBlockCollision(work):
        # Block 'bar' of project 'foo' and block 'foo_bar' of project 'foo_bar'
        # both get the C++ name 'foo_bar'; their SV names stay 'bar' and 'foo_bar'.
        edit(os.path.join(work, 'root', 'yaml', 'rootProject.yaml'),
             'projectName: rootProj', 'projectName: foo')
        edit(os.path.join(work, rootTop), 'rootLeaf', 'bar')
        edit(os.path.join(work, childProject), 'childProj', 'foo_bar')
        edit(os.path.join(work, childLeaf), 'childLeafBlock', 'foo_bar')

    ok = True
    rootBlocks = ("'rootProj'", "'childProj'")
    cases = (
        (blockCollision, "SystemVerilog module or package name 'rootLeaf'", rootBlocks, 'block SV'),
        (packageCollision, "SystemVerilog module or package name 'rootTop_package'", rootBlocks,
         'package SV'),
        (cppBlockCollision, "C++ module name 'foo_bar'",
         ("'bar' (project 'foo')", "'foo_bar' (project 'foo_bar')"), 'block C++'),
    )
    for mutate, expected, owners, label in cases:
        returncode, output = run_nested(mutate)
        if returncode == 0:
            print(f"FAIL: a {label} name collision built cleanly")
            ok = False
        elif expected not in output or not all(owner in output for owner in owners):
            print(f"FAIL: the {label} collision diagnostic does not name '{expected}' and "
                  f"{', '.join(owners)}:\n{output}")
            ok = False
        else:
            print(f"PASS: a {label} name collision is rejected naming both owning projects")
    return ok


def run_db(files, projectFile):
    # make db's projectCreate on a project written from {relpath: text}.
    work = tempfile.mkdtemp(prefix='file_prefix_db_', dir=test_dir)
    try:
        for relpath, text in files.items():
            path = os.path.join(work, relpath)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(text)
        result = run([sys.executable, os.path.join(base_dir, 'arch2code.py'),
                      '--yaml', os.path.join(work, projectFile),
                      '--db', os.path.join(work, 'test.db')])
        return result.returncode, result.stdout + result.stderr
    finally:
        remove(work)


def expect_db_failure(label, files, projectFile, expected):
    returncode, output = run_db(files, projectFile)
    if returncode == 0:
        print(f"FAIL: {label}: make db succeeded")
        return False
    if 'Traceback' in output:
        print(f"FAIL: {label}: make db raised instead of reporting:\n{output[-3000:]}")
        return False
    missing = [text for text in expected if text not in output]
    if missing:
        print(f"FAIL: {label}: the diagnostic lacks {missing}:\n{output[-3000:]}")
        return False
    print(f"PASS: {label} fails make db naming {', '.join(expected[1:])}")
    return True


def single_project(projectName, design, designFile='design.yaml'):
    return {
        'yaml/project.yaml': f"""yamlFormat: 2
projectName: {projectName}
projectFiles:
    - {designFile}
topInstance: uTop
dirs:
    root: ..
""",
        f'yaml/{designFile}': design,
    }


def check_config_name_collision():
    # Consumer foo declares variants of lib's bar and foo_bar. Both Configs
    # would be foo_bar (foo_barVariantConfig.cppm, foo_barV0Config).
    files = {
        'lib/yaml/libProject.yaml': """projectName: libp
projectFiles:
    - lib.yaml
dirs:
    root: ..
fileGeneration:
    template: none
""",
        'lib/yaml/lib.yaml': """ipParameters:
    constants:
        LIB_W: { value: 8, maxValue: 32, desc: "width" }
blocks:
    bar: { desc: "parameterized bar", params: [LIB_W] }
    foo_bar: { desc: "parameterized foo_bar", params: [LIB_W] }
""",
        'top/yaml/fooProject.yaml': """yamlFormat: 2
projectName: foo
projectFiles:
    - ../../lib/yaml/libProject.yaml
    - fooTop.yaml
topInstance: uTop
dirs:
    root: ..
""",
        'top/yaml/fooTop.yaml': """include:
    - ../../lib/yaml/lib.yaml
blocks:
    top: { desc: "top", hasRtl: false }
instances:
    uTop: { container: top, instanceType: top }
    uBar: { container: top, instanceType: bar, variant: v0 }
    uFooBar: { container: top, instanceType: foo_bar, variant: v0 }
parameters:
    bar:
        v0: { LIB_W: 8 }
    foo_bar:
        v0: { LIB_W: 16 }
""",
    }
    return expect_db_failure(
        "two Configs project foo declares under one name", files, 'top/yaml/fooProject.yaml',
        ["Config struct and file stem 'foo_bar'",
         "block 'bar' as declared by project 'foo'",
         "block 'foo_bar' as declared by project 'foo'"])


def check_wrapper_module_collision():
    # leaf's Verilated wrapper and block leaf_hdl_sv_wrapper both declare
    # module leaf_hdl_sv_wrapper.
    design = """blocks:
    top: { desc: "top", hasRtl: false }
    leaf: { desc: "Verilated leaf", hasVl: true }
    leaf_hdl_sv_wrapper: { desc: "ordinary block named like leaf's wrapper" }
instances:
    uTop: { container: top, instanceType: top }
    uLeaf: { container: top, instanceType: leaf }
    uWrap: { container: top, instanceType: leaf_hdl_sv_wrapper }
"""
    return expect_db_failure(
        "a block named like a Verilated wrapper", single_project('wrapclash', design),
        'yaml/project.yaml',
        ["SystemVerilog module or package name 'leaf_hdl_sv_wrapper'",
         "the Verilated wrapper of block 'leaf' (project 'wrapclash')",
         "block 'leaf_hdl_sv_wrapper' (project 'wrapclash')"])


def check_module_package_shared_name():
    # Block foo_package and context foo's package both write rtl/foo_package.sv
    # and declare one Verilator design-unit name.
    design = """include:
    - foo.yaml
blocks:
    top: { desc: "top" }
    foo_package: { desc: "RTL block named like context foo's package" }
instances:
    uTop: { container: top, instanceType: top }
    uFoo: { container: top, instanceType: foo_package }
"""
    files = single_project('svns', design)
    files['yaml/foo.yaml'] = """constants:
    FOO_W: { value: 4, desc: "gives the context a package" }
"""
    return expect_db_failure(
        "a block foo_package beside a context foo", files, 'yaml/project.yaml',
        ["SystemVerilog module or package name 'foo_package'",
         "the module of block 'foo_package' (project 'svns')",
         "the package of context 'foo.yaml' (project 'svns')"])


def check_dollar_prefix():
    design = """blocks:
    top: { desc: "top" }
instances:
    uTop: { container: top, instanceType: top }
"""
    ok = True
    for key in ('svFilePrefix', 'scFilePrefix'):
        files = single_project('dollarprefix', design)
        files['yaml/project.yaml'] += f'{key}: "a$"\n'
        ok = expect_db_failure(
            f"{key} a$", files, 'yaml/project.yaml',
            [f"{key} 'a$' in project",
             "may contain only letters, digits and '_'",
             "the prefix ends up in filenames"]) and ok
    return ok


def check_dollar_module_name():
    design = """blocks:
    top: { desc: "top", hasRtl: false }
    a$b: { desc: "RTL block whose SV name holds a dollar" }
instances:
    uTop: { container: top, instanceType: top }
    uAb: { container: top, instanceType: a$b }
"""
    return expect_db_failure(
        "an RTL block named a$b", single_project('dollarblock', design), 'yaml/project.yaml',
        ["SystemVerilog module name 'a$b'",
         "block 'a$b' (project 'dollarblock')",
         "'$' is not allowed even though SystemVerilog permits it"])


def expect_db_success(label, files, projectFile):
    returncode, output = run_db(files, projectFile)
    if returncode != 0:
        print(f"FAIL: {label}: make db failed:\n{output[-3000:]}")
        return False
    print(f"PASS: {label} passes make db")
    return True


def check_model_only_blocks_not_sv_names():
    # A model-only block emits no SV module, so its name cannot collide with one.
    wrapperTwin = """blocks:
    top: { desc: "top", hasRtl: false }
    leaf: { desc: "Verilated leaf", hasVl: true }
    leaf_hdl_sv_wrapper: { desc: "model-only block named like leaf's wrapper", hasRtl: false }
instances:
    uTop: { container: top, instanceType: top }
    uLeaf: { container: top, instanceType: leaf }
    uWrap: { container: top, instanceType: leaf_hdl_sv_wrapper }
"""
    ok = expect_db_success("a model-only block named like a Verilated wrapper",
                           single_project('wraptwin', wrapperTwin), 'yaml/project.yaml')
    twoCpus = {
        'lib/yaml/libProject.yaml': """projectName: libp
projectFiles:
    - lib.yaml
dirs:
    root: ..
fileGeneration:
    template: none
""",
        'lib/yaml/lib.yaml': """blocks:
    cpu: { desc: "model-only cpu of libp", hasRtl: false }
""",
        'top/yaml/topProject.yaml': """yamlFormat: 2
projectName: topp
projectFiles:
    - ../../lib/yaml/libProject.yaml
    - top.yaml
topInstance: uTop
dirs:
    root: ..
""",
        'top/yaml/top.yaml': """blocks:
    top: { desc: "top", hasRtl: false }
    cpu: { desc: "model-only cpu of topp", hasRtl: false }
instances:
    uTop: { container: top, instanceType: top }
    uCpu: { container: top, instanceType: cpu }
""",
    }
    return expect_db_success("two projects that each have a model-only block cpu",
                             twoCpus, 'top/yaml/topProject.yaml') and ok


def check_illegal_package_name():
    # data-types.yaml with no includeName would declare package data-types_package.
    design = """include:
    - data-types.yaml
blocks:
    top: { desc: "top" }
instances:
    uTop: { container: top, instanceType: top }
"""
    files = single_project('illegalpkg', design)
    files['yaml/data-types.yaml'] = """constants:
    DT_WIDTH: { value: 4, desc: "gives the context a package" }
"""
    return expect_db_failure(
        "a context from data-types.yaml", files, 'yaml/project.yaml',
        ["SystemVerilog package name 'data-types_package'",
         "data-types.yaml",
         "set includeName in that file or rename the file"])


def write_files(prefix, files):
    work = tempfile.mkdtemp(prefix=prefix, dir=test_dir)
    for relpath, text in files.items():
        path = os.path.join(work, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(text)
    return work


def arch2code(*args):
    result = run([sys.executable, os.path.join(base_dir, 'arch2code.py'), *args])
    if result.returncode != 0:
        raise AssertionError(f"arch2code.py {' '.join(args)} failed:\n"
                             f"{result.stdout}\n{result.stderr}")


def check_sweep_keeps_current_file():
    # Under svFilePrefix p_, context p_foo's legacy package name p_foo_package.sv
    # is the current file of block foo_package.
    design = """include:
    - fooTypes.yaml
blocks:
    top: { desc: "top" }
    foo_package: { desc: "RTL block named like the p_foo package" }
instances:
    uTop: { container: top, instanceType: top }
    uFoo: { container: top, instanceType: foo_package }
"""
    files = single_project('sweepguard', design)
    files['yaml/project.yaml'] += 'svFilePrefix: p_\n'
    files['yaml/fooTypes.yaml'] = """includeName: p_foo
constants:
    FOO_W: { value: 4, desc: "gives the context a package" }
"""
    work = write_files('file_prefix_sweep_', files)
    try:
        db = os.path.join(work, 'test.db')
        arch2code('--yaml', os.path.join(work, 'yaml', 'project.yaml'), '--db', db)
        arch2code('--db', db, '-r', '--newmodule')
        blockFile = os.path.join(work, 'rtl', 'p_foo_package.sv')
        with open(blockFile, 'a') as f:
            f.write(f'// {MARKER}\n')
        with open(blockFile, 'rb') as f:
            before = f.read()
        result = run([sys.executable, os.path.join(base_dir, 'migrateYaml.py'),
                      '--sweep', '--write', '--db', db])
        output = result.stdout + result.stderr
        arch2code('--db', db, '-r', '--newmodule')
        ok = True
        with open(blockFile, 'rb') as f:
            if f.read() != before:
                print("FAIL: the orphan sweep deleted or changed block foo_package's p_foo_package.sv")
                ok = False
        if result.returncode != 1 or not re.search(
                r'p_foo_package\.sv\s+TODO_CURRENT_ARTIFACT .*package file of context '
                r"'fooTypes\.yaml'.*rtlModule file of block 'foo_package'", output):
            print(f"FAIL: the sweep did not report p_foo_package.sv as a TODO "
                  f"(exit {result.returncode}):\n{output[-3000:]}")
            ok = False
        if ok:
            print("PASS: the orphan sweep keeps p_foo_package.sv, block foo_package's current "
                  "file and context p_foo's legacy package name, and reports it")
        return ok
    finally:
        remove(work)


def check_keyword_module_name():
    design = """blocks:
    top: { desc: "top", hasRtl: false }
    always: { desc: "RTL block named like an SV keyword" }
instances:
    uTop: { container: top, instanceType: top }
    uAlways: { container: top, instanceType: always }
"""
    return expect_db_failure(
        "an RTL block named always", single_project('kwblock', design), 'yaml/project.yaml',
        ["SystemVerilog module name 'always'",
         "block 'always' (project 'kwblock')",
         "SystemVerilog keyword",
         "rename the block"])


BODY_ENTRY = ('        vlSvWrapBody: { name: "_body", ext: {svh: "svh"}, cond: {hasOwnParams: true}, '
              'condAnd: {hasVl: true}, mode: block, basePath: vl_wrap, variant: false, '
              'desc: "wrapper body under its own name" }\n')


def check_wrapper_body_name():
    # vlSvWrapBody named _body: ip's body is ip_body.svh, and the variant0 top
    # includes that file and instantiates the module it declares.
    work = copy_simple_ip()
    try:
        for project in ('ip', '.'):
            edit(os.path.join(work, project, PROJECT_FILES[project]),
                 '    fileMap:\n', '    fileMap:\n' + BODY_ENTRY)
        ip = os.path.join(work, 'ip')
        for directory in (ip, work):
            run(['make', '-C', directory, 'clean'])
            make(directory, 'newmodule')
            make(directory, 'gen')
        verif = os.path.join(ip, 'verif')
        ok = True
        if not os.path.exists(os.path.join(verif, 'ip_body.svh')) \
                or os.path.exists(os.path.join(verif, 'ip_hdl_sv_wrapper.svh')):
            print(f"FAIL: ip/verif holds {sorted(os.listdir(verif))}, not ip_body.svh alone")
            ok = False
        with open(os.path.join(verif, 'ip_body.svh')) as f:
            if not re.search(r'^module ip_body$', f.read(), re.M):
                print("FAIL: ip_body.svh does not declare module ip_body")
                ok = False
        with open(os.path.join(verif, 'ip_variant0_hdl_sv_wrapper.sv')) as f:
            top = f.read()
        if '`include "ip_body.svh"' not in top or not re.search(r'^\s*ip_body #\(', top, re.M):
            print("FAIL: ip_variant0_hdl_sv_wrapper.sv does not include ip_body.svh and "
                  "instantiate ip_body")
            ok = False
        ok = check_sv_names_and_run(work, 'vlSvWrapBody _body') and ok
        if ok:
            print("PASS: with vlSvWrapBody named _body, ip's variant top includes ip_body.svh "
                  "and the Verilated run passes")
        return ok
    finally:
        remove(work)


def check_scaffold_keys():
    text = projectFileTemplate.format(name='demo', copyright='c', fileMap='')
    ok = True
    for key, desc in (('svFilePrefix', 'Prefix for generated SystemVerilog filenames and matching module names'),
                      ('scFilePrefix', 'Prefix for generated SystemC filenames'),
                      ('fwFilePrefix', 'Prefix for generated firmware filenames')):
        line = f'# {key}: ""  # {desc}'
        if line not in text.splitlines():
            print(f"FAIL: the project scaffold lacks the line {line!r}")
            ok = False
    enabled = yaml.safe_load(text.replace('# svFilePrefix:', 'svFilePrefix:'))
    if enabled.get('svFilePrefix') != '':
        print("FAIL: uncommenting svFilePrefix does not give a valid empty prefix")
        ok = False
    if ok:
        print("PASS: a new project file lists the three prefix keys as comments")
    return ok


def check_prefix_conflict_halts_migrate():
    # With both names of one file present, migrate reports the conflict and
    # stops before newmodule, which would delete the unprefixed file as stale.
    work = copy_simple_ip()
    try:
        verif = os.path.join(work, 'ip', 'verif')
        old = os.path.join(verif, 'ip_hdl_sc_wrapper.h')
        with open(old, 'a') as f:
            f.write(f'// {MARKER}\n')
        with open(old, 'rb') as f:
            before = f.read()
        shutil.copy(old, os.path.join(verif, 'new_ip_hdl_sc_wrapper.h'))
        set_prefixes(work, 'ip', {'sc': 'new_'})
        result = run(['make', '-C', os.path.join(work, 'ip'), '-j8', 'migrate'])
        output = result.stdout + result.stderr
        ok = True
        if not os.path.exists(old):
            print("FAIL: migrate deleted ip_hdl_sc_wrapper.h while reporting the prefix conflict")
            ok = False
        else:
            with open(old, 'rb') as f:
                if f.read() != before:
                    print("FAIL: migrate changed ip_hdl_sc_wrapper.h while reporting the "
                          "prefix conflict")
                    ok = False
        if 'TODO: both' not in output or 'new_ip_hdl_sc_wrapper.h' not in output:
            print(f"FAIL: migrate did not report the prefix conflict:\n{output[-3000:]}")
            ok = False
        if result.returncode == 0 or not re.search(r'\bmigrate\] Error 2$', output, re.M):
            print(f"FAIL: migrate did not fail with the halt code 2 "
                  f"(make exit {result.returncode}):\n{output[-3000:]}")
            ok = False
        if re.search(r'arch2code\.py --db \S+ -r --newmodule', output) \
                or 'Removing stale' in output:
            print(f"FAIL: migrate ran newmodule after the prefix conflict:\n{output[-3000:]}")
            ok = False
        if ok:
            print("PASS: a prefix conflict halts migrate with code 2 before newmodule, and the "
                  "unprefixed file survives byte-identical")
        return ok
    finally:
        remove(work)


PREFIXED_TWIN_BLOCK = '''blocks:
    p_ipStdMaster:
        desc: "Named like ipStdMaster's svFilePrefix p_ file"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
'''


def add_prefixed_twin(work):
    # A block whose unprefixed file name is ipStdMaster's prefixed one.
    edit(os.path.join(work, 'ip', 'yaml', 'ipTop.yaml'), '\nblocks:\n', '\n' + PREFIXED_TWIN_BLOCK)


def migrate_halts(directory):
    # make migrate, expected to stop with the sweep's halt code 2.
    result = run(['make', '-C', directory, '-j8', 'migrate'])
    output = result.stdout + result.stderr
    if result.returncode == 0 or not re.search(r'\bmigrate\] Error 2$', output, re.M):
        print(f"FAIL: migrate did not fail with the halt code 2 "
              f"(make exit {result.returncode}):\n{output[-3000:]}")
        return False
    if 'TODO_FILE_PREFIX_CHAIN' not in output and 'cannot tell whose code' not in output:
        print(f"FAIL: migrate did not report the prefix chain:\n{output[-3000:]}")
        return False
    return True


def check_prefix_chain_after_new_block_halts():
    # ipStdMaster already sits at p_ipStdMaster.sv when block p_ipStdMaster is
    # added. Moving p_ipStdMaster.sv to p_p_ipStdMaster.sv would hand
    # ipStdMaster's code to the new block.
    work = copy_simple_ip()
    try:
        ip = os.path.join(work, 'ip')
        set_prefixes(work, 'ip', {'sv': 'p_'})
        run(['make', '-C', ip, '-j8', 'migrate'])
        if not os.path.exists(os.path.join(ip, 'rtl', 'p_ipStdMaster.sv')):
            print("FAIL: the first migrate did not move ipStdMaster.sv to p_ipStdMaster.sv")
            return False
        add_prefixed_twin(work)
        before = tree_digest(ip)
        ok = migrate_halts(ip)
        after = tree_digest(ip)
        changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
        if changed:
            print(f"FAIL: the halted migrate changed {changed}")
            ok = False
        if ok:
            print("PASS: migrate halts with code 2 and changes no file when a new block's "
                  "unprefixed name is another block's prefixed file")
        return ok
    finally:
        remove(work)


def check_prefix_chain_from_main_halts():
    # main holds both ipStdMaster.sv and p_ipStdMaster.sv; under p_ each moves
    # onto a name the other currently has or had.
    work = extract_main_simple_ip()
    try:
        ip = os.path.join(work, 'ip')
        rtl = os.path.join(ip, 'rtl')
        with open(os.path.join(rtl, 'ipStdMaster.sv')) as f:
            text = f.read()
        with open(os.path.join(rtl, 'p_ipStdMaster.sv'), 'w') as f:
            f.write(text.replace('ipStdMaster', 'p_ipStdMaster') + f'// {MARKER}\n')
        add_prefixed_twin(work)
        set_prefixes(work, 'ip', {'sv': 'p_'})
        run(['make', '-C', os.path.join(work, 'common'), '-j8', 'migrate'])
        before = tree_digest(rtl)
        ok = migrate_halts(ip)
        after = tree_digest(rtl)
        changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
        if changed:
            print(f"FAIL: the halted migrate changed rtl/{changed}")
            ok = False
        if ok:
            print("PASS: main's ipStdMaster.sv beside p_ipStdMaster.sv halts migrate with "
                  "code 2 and every rtl file is unchanged")
        return ok
    finally:
        remove(work)


def check_settled_prefixed_twin_migrates():
    # ipStdMaster sits at p_ipStdMaster.sv and block p_ipStdMaster at
    # p_p_ipStdMaster.sv. Both are in place, so migrate has nothing to move.
    work = copy_simple_ip()
    try:
        ip = os.path.join(work, 'ip')
        set_prefixes(work, 'ip', {'sv': 'p_'})
        add_prefixed_twin(work)
        make(ip, 'migrate')
        paths = [os.path.join(ip, 'rtl', name)
                 for name in ('p_ipStdMaster.sv', 'p_p_ipStdMaster.sv')]
        missing = [p for p in paths if not os.path.exists(p)]
        if missing:
            print(f"FAIL: the first migrate did not leave {missing}")
            return False
        before = dict()
        for path in paths:
            with open(path, 'rb') as f:
                before[path] = f.read()
        result = run(['make', '-C', ip, '-j8', 'migrate'])
        output = result.stdout + result.stderr
        ok = True
        if result.returncode != 0:
            print(f"FAIL: migrate of the settled project exited {result.returncode}:\n"
                  f"{output[-3000:]}")
            ok = False
        if 'TODO_FILE_PREFIX' in output or 'cannot tell whose code' in output \
                or 'TODO: both' in output:
            print(f"FAIL: migrate of the settled project reported a prefix TODO:\n"
                  f"{output[-3000:]}")
            ok = False
        for path in paths:
            with open(path, 'rb') as f:
                if f.read() != before[path]:
                    print(f"FAIL: migrate of the settled project changed {path}")
                    ok = False
        if ok:
            print("PASS: a project with ipStdMaster at p_ipStdMaster.sv and p_ipStdMaster at "
                  "p_p_ipStdMaster.sv migrates again and both files are unchanged")
        return ok
    finally:
        remove(work)


def main():
    checks = (check_scaffold_keys, check_collisions, check_omitted_equals_empty,
              check_each_language_alone, check_main_migrate_without_prefix,
              check_main_migrate_with_prefixes, check_prefix_conflict_halts_migrate,
              check_main_migrate_ports_legacy_tb_with_prefix,
              check_prefix_chain_after_new_block_halts, check_prefix_chain_from_main_halts,
              check_settled_prefixed_twin_migrates,
              check_config_name_collision, check_wrapper_module_collision,
              check_module_package_shared_name, check_dollar_prefix, check_dollar_module_name,
              check_illegal_package_name, check_model_only_blocks_not_sv_names,
              check_keyword_module_name, check_sweep_keeps_current_file,
              check_wrapper_body_name)
    failed = [check.__name__ for check in checks if not check()]
    if failed:
        print(f"SOME TESTS FAILED: {', '.join(failed)}")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == '__main__':
    sys.exit(main())
