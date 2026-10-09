#!/usr/bin/env python3
"""`make migrate` exit status reflects what is still pending after every phase.

The orphan sweep runs first and reports each legacy testbench `.h/.cpp` pair as
TODO_PORT. The `--port-tb` phase of the same target then ports those pairs, so a
project whose only TODOs are such pairs must finish with exit 0. A TODO that no
later phase resolves must still exit 1.

The project is the hier-layout fixture as committed at LEGACY_COMMIT, extracted
with `git archive`, with its three legacy testbench fileMap overrides removed.
That is the shape the fixture had before it was migrated: legacy
Testbench/External pairs and a single-region Config.cpp. Each case runs the
real `make migrate`.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = 'unittest/fixtures/hier-layout'
# The last commit whose hier-layout fixture still has the legacy tb form.
LEGACY_COMMIT = '69b06851'
TB_OVERRIDES = ('testBench ', 'tbConfig ', 'tbExternal ')
TB_DIR = os.path.join('core', 'tb', 'core')
# make exits 2 whenever a recipe fails; the recipe's own status is in this line.
RECIPE_TODO = 'migrate] Error 1'
# The note printed after a first sweep that reported anything, as one line.
NOTE = ('Later phases of this run may resolve TODO items reported above. '
        'A TODO_PHASE_FAILED item above needs a fix and a re-run.')
# make also echoes the recipe line that prints this header, but that line
# starts with `echo`, so only the printed header starts a line.
PENDING_HEADER = re.compile(r'^=== pending after all phases.*$', re.M)

PASS = 0
FAIL = 0


def check(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS: {msg}")
    else:
        FAIL += 1
        print(f"  FAIL: {msg}")


def extract_legacy_fixture():
    """The fixture at LEGACY_COMMIT in a temp dir, minus the legacy tb
    overrides."""
    work = tempfile.mkdtemp(prefix='migrate_exit_status_', dir=test_dir)
    try:
        archive = subprocess.run(
            ['git', '-C', base_dir, 'archive', LEGACY_COMMIT, FIXTURE],
            capture_output=True, check=True)
        subprocess.run(['tar', '-x', '-C', work, '--strip-components=3'],
                       input=archive.stdout, check=True)
        projectFile = os.path.join(work, 'prj', 'yaml', 'hierProject.yaml')
        with open(projectFile) as f:
            lines = f.read().splitlines(keepends=True)
        kept = [ln for ln in lines if not ln.lstrip().startswith(TB_OVERRIDES)]
        assert len(lines) - len(kept) == len(TB_OVERRIDES), \
            f"the fixture at {LEGACY_COMMIT} does not carry the three legacy tb overrides"
        with open(projectFile, 'w') as f:
            f.write(''.join(kept))
    except BaseException:
        shutil.rmtree(work, ignore_errors=True)
        raise
    return work


def pending_tail(out):
    """Output after the final read-only sweep's header, or None if it never ran."""
    match = PENDING_HEADER.search(out)
    return out[match.end():] if match else None


def migrate(work):
    # The fixture's makefiles name their roots from the git top level, which
    # for a temp dir under unittest/ is the live builder checkout. Point both
    # roots at the copy on the command line so sub-makes inherit them.
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run(
        ['make', '-C', work, f'A2C_ROOT={base_dir}', f'REPO_ROOT={work}', 'migrate'],
        capture_output=True, text=True, timeout=1800, env=env)


def tb(work, name):
    return os.path.join(work, TB_DIR, name)


def test_ported_tb_pairs_exit_clean():
    print("test_ported_tb_pairs_exit_clean")
    work = extract_legacy_fixture()
    try:
        result = migrate(work)
        out = result.stdout + result.stderr
        check(result.returncode == 0,
              f"first make migrate exits 0 once --port-tb resolves the sweep's "
              f"TODO_PORT pairs (got {result.returncode})")
        check('TODO_PORT' in out,
              "the sweep reported the legacy tb pairs as TODO_PORT")
        check(NOTE in out,
              "the target prints the note on later phases and TODO_PHASE_FAILED")
        for name in ('coreTestbench.h', 'coreTestbench.cpp',
                     'coreExternal.h', 'coreExternal.cpp'):
            check(not os.path.exists(tb(work, name)), f"legacy {name} is gone")
        for name in ('coreTestbench.cppm', 'coreExternal.cppm'):
            check(os.path.exists(tb(work, name)), f"{name} is scaffolded")
        with open(tb(work, 'coreConfig.cpp')) as f:
            check('--template=tbConfig --section=class' in f.read(),
                  "coreConfig.cpp carries the three-section form")
        if result.returncode != 0:
            print(out[-4000:])
        again = migrate(work)
        check(again.returncode == 0,
              f"a second make migrate also exits 0 (got {again.returncode})")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_unresolved_port_still_exits_one():
    """The External PARAM split is a TODO the porter refuses, so the legacy
    pair stays and the target exits 1 (shape from test_migrate_tb_port)."""
    print("test_unresolved_port_still_exits_one")
    work = extract_legacy_fixture()
    try:
        cpp = tb(work, 'coreExternal.cpp')
        with open(cpp) as f:
            text = f.read()
        old = '// GENERATED_CODE_PARAM --block=hier_tb --excludeInst=u_core'
        assert old in text
        with open(cpp, 'w') as f:
            f.write(text.replace(old, '// GENERATED_CODE_PARAM --block=hier_tb'))
        result = migrate(work)
        out = result.stdout + result.stderr
        check(result.returncode != 0 and RECIPE_TODO in out,
              f"make migrate fails with recipe status 1 while the External "
              f"port is refused (got make {result.returncode})")
        check('TODO_PORT_PARAM_SPLIT' in out, "the porter reports the PARAM split")
        check(os.path.exists(cpp), "the refused legacy External is left on disk")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_unresolved_sweep_item_still_exits_one():
    """A user #include of a header the sweep deleted is a TODO that no later
    phase resolves. Both sweeps report it, and the recipe discards the first
    sweep's exit 1, so this pins that the final read-only sweep still fails
    the target. The shape is the hierarchical retired-sibling case from
    test_migrate_orphans."""
    print("test_unresolved_sweep_item_still_exits_one")
    work = extract_legacy_fixture()
    try:
        model = os.path.join(work, 'core', 'model')
        with open(os.path.join(model, 'coreVariantConfig.h'), 'w') as f:
            f.write('// GENERATED_CODE_BEGIN\n')
        with open(os.path.join(model, 'consumer.cpp'), 'w') as f:
            f.write('#include "coreVariantConfig.h"\nint main(){return 0;}\n')
        result = migrate(work)
        out = result.stdout + result.stderr
        check(result.returncode != 0 and RECIPE_TODO in out,
              f"make migrate fails with recipe status 1 while the include "
              f"site remains (got make {result.returncode})")
        tail = pending_tail(out)
        check(tail is not None and 'TODO_USER_INCLUDE' in tail and 'consumer.cpp' in tail,
              "the final read-only sweep reports the include site")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def test_failed_sweep_write_still_exits_one():
    """A sweep phase whose write raises leaves its edit undone, and the final
    read-only sweep cannot see that. A read-only core.sv with a stale endmodule
    label makes the end-label re-stamp raise on its write. The project is
    migrated once first, so gen renders core.sv unchanged and does not write it.
    Root writes a read-only file anyway, so the case is skipped under root;
    test_sweep_phase_failure_code_survives covers the recipe either way."""
    print("test_failed_sweep_write_still_exits_one")
    if os.geteuid() == 0:
        print("  SKIP: running as root, which can write a read-only file")
        return
    work = extract_legacy_fixture()
    sv = os.path.join(work, 'core', 'rtl', 'core.sv')
    try:
        first = migrate(work)
        assert first.returncode == 0, first.stdout + first.stderr
        with open(sv) as f:
            text = f.read()
        assert text.rstrip().endswith('endmodule: core')
        with open(sv, 'w') as f:
            f.write(text.replace('endmodule: core', 'endmodule: stale_core'))
        os.chmod(sv, 0o444)
        result = migrate(work)
        out = result.stdout + result.stderr
        check('TODO_PHASE_FAILED' in out, "the re-stamp phase failure is reported")
        check(result.returncode != 0 and RECIPE_TODO in out,
              f"make migrate fails with recipe status 1 while the re-stamp is "
              f"undone (got make {result.returncode})")
        with open(sv) as f:
            check('endmodule: stale_core' in f.read(), "the stale label is still there")
    finally:
        shutil.rmtree(work, ignore_errors=True)


# Stands in for migrateYaml.py: the writing --sweep reports a phase failure,
# every other mode is clean.
STUB_MIGRATE = """#!/usr/bin/env python3
import sys
sys.exit(3 if '--sweep' in sys.argv and '--write' in sys.argv else 0)
"""


def stub_builder_root(root):
    """A builder root whose entries link to the real one, except migrateYaml.py,
    which is STUB_MIGRATE."""
    os.makedirs(root)
    for name in os.listdir(base_dir):
        if name not in ('migrateYaml.py', '.git'):
            os.symlink(os.path.join(base_dir, name), os.path.join(root, name))
    stub = os.path.join(root, 'migrateYaml.py')
    with open(stub, 'w') as f:
        f.write(STUB_MIGRATE)
    os.chmod(stub, 0o755)
    return root


def test_sweep_phase_failure_code_survives():
    """The recipe keeps the first sweep's exit 3 when it resets rc for exit 1,
    so the target exits 1 even when every later phase is clean.
    Root-independent: the phase failure comes from a stub, not from a file
    permission."""
    print("test_sweep_phase_failure_code_survives")
    work = tempfile.mkdtemp(prefix='migrate_exit_status_', dir=test_dir)
    try:
        fixture = os.path.join(base_dir, FIXTURE)
        # Authored input and the build harness only; newmodule scaffolds the
        # rest in its current form, so the stubbed porters have nothing to do.
        for rel in ('Makefile', 'include', 'prj', os.path.join('core', 'yaml'),
                    os.path.join('leaf', 'yaml')):
            src = os.path.join(fixture, rel)
            dst = os.path.join(work, rel)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        root = stub_builder_root(os.path.join(work, 'a2c'))
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            ['make', '-C', work, f'A2C_ROOT={root}', f'REPO_ROOT={work}', 'migrate'],
            capture_output=True, text=True, timeout=1800, env=env)
        out = result.stdout + result.stderr
        check(pending_tail(out) is not None, "every phase ran to the final sweep")
        check(result.returncode != 0 and RECIPE_TODO in out,
              f"make migrate ends with recipe status 1 after a first-sweep "
              f"exit 3 (got make {result.returncode})")
        if RECIPE_TODO not in out:
            print(out[-3000:])
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_all_tests():
    test_ported_tb_pairs_exit_clean()
    test_unresolved_port_still_exits_one()
    test_unresolved_sweep_item_still_exits_one()
    test_failed_sweep_write_still_exits_one()
    test_sweep_phase_failure_code_survives()
    print(f"\nResult: {'PASS' if FAIL == 0 else 'FAIL'} "
          f"({PASS} checks, {FAIL} failures)")
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
