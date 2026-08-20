#!/usr/bin/env python3
"""A database build that fails leaves nothing behind for the next build to reuse.

arch2code writes the sqlite database as it runs, so a run that errors part way
through has already created the file. Without `.DELETE_ON_ERROR:` make keeps
that partial database, and because it is newer than the YAML that produced it
every later `make` considers the db target up to date: the db stage is skipped,
generation runs against a truncated database, and the build exits 0. The
original hard error is reported once and never again.

Both projects are copied into a private tempdir and built with REPO_ROOT
overridden on the make command line, so no shared examples/ tree is touched.
"""

import glob
import os
import shutil
import subprocess
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # builder/base
EXAMPLES_DIR = os.path.join(BASE_DIR, 'examples')

# A deliberate-failure fixture: its payload layouts disagree across a connection,
# which projectCreate rejects after it has already opened the database.
FAILING_EXAMPLE = os.path.join(EXAMPLES_DIR, 'xprojParam', 'cpLayoutBad')

BUILDING_EXAMPLE = os.path.join(EXAMPLES_DIR, 'simple')
BUILDING_DB = 'simple.db'


def _stage(example, tmp):
    """Copy an example to a private root, minus any build state it carries."""
    root = os.path.join(tmp, 'proj')
    # A copied-in database would already be newer than its YAML, which is the
    # very state these checks are about; both checks go vacuous without this.
    shutil.copytree(example, root,
                    ignore=shutil.ignore_patterns('.gen', '*.db'))
    return root


def _make_db(root):
    """Run `make db` against the staged copy. Returns (returncode, output)."""
    # REPO_ROOT on the command line overrides the assignment in the project's
    # shared.mk, redirecting every derived path at the staged copy. A2C_ROOT
    # stays on the real builder so the generator and system YAML resolve.
    proc = subprocess.run(
        ['make', 'db', f'A2C_ROOT={BASE_DIR}', f'REPO_ROOT={root}'],
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return proc.returncode, proc.stdout


def _check_failed_build_leaves_no_database():
    print("db failure: the partial database does not survive the failed build")
    with tempfile.TemporaryDirectory() as tmp:
        root = _stage(FAILING_EXAMPLE, tmp)
        # Asserted over every *.db rather than one expected name, which would
        # pass trivially if the fixture's PROJECTNAME ever changed.
        surviving = lambda: glob.glob(os.path.join(root, '*.db'))

        rc, output = _make_db(root)
        assert rc != 0, \
            f"the fixture must fail at the db stage; make exited 0:\n{output}"
        assert not surviving(), \
            ("a failed db build left its partial database behind; the next "
             f"build will treat it as up to date: {surviving()}")

        # The defect was never the first build - it was the second one reporting
        # success against what the first left behind.
        rc, output = _make_db(root)
        assert rc != 0, \
            ("a repeated db build reported success after the first one failed; "
             f"the failure is being hidden:\n{output}")
        assert not surviving(), \
            f"the repeated failed build left a database behind: {surviving()}"

    print("PASS: failed db build leaves no database, and does not go quiet")
    return True


def _check_successful_build_keeps_its_database():
    print("db success: a clean build still keeps its database")
    with tempfile.TemporaryDirectory() as tmp:
        root = _stage(BUILDING_EXAMPLE, tmp)
        dbPath = os.path.join(root, BUILDING_DB)

        rc, output = _make_db(root)
        assert rc == 0, f"the db build should succeed; got rc={rc}:\n{output}"
        assert os.path.exists(dbPath), \
            "a successful db build must leave its database in place"

    print("PASS: successful db build keeps its database")
    return True


def run_all_tests():
    ok = (_check_failed_build_leaves_no_database()
          and _check_successful_build_keeps_its_database())
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
