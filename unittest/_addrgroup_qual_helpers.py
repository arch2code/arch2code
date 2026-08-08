"""Shared harness for the composed `addressGroup` project-qualification tests.

The `AddressGroups` registry is keyed on (owning projectName, group name), so a
group name is owned by the project owning the declaring YAML file and two
independently authored projects may each name their group `top`. That is a
composition property, and the flat single-file `_addrctl_helpers.make_project()`
cannot express a composed project, so these tests copy the committed
`fixtures/addrgroup-qualification` tree into a temp directory (the
`test_nested_ownership.py` pattern) and build it there. The copy is what keeps
projectCreate's generated build manifest and `--newmodule` scaffolds out of the
committed fixture.

Fixture topology: root project `rootProj` pulls three sub-projects through its
projectFiles: slot - `commonProj` (shared register-bus definitions),
`childAProj` and `childBProj` (two sibling IPs). All three of rootProj,
childAProj and childBProj declare an address group named `top` with a distinct
varType / enumPrefix, and the root router is the dispatch-tree root with each
child's router nested beneath it.
"""

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

FIXTURE = os.path.join(test_dir, 'fixtures', 'addrgroup-qualification')
ARCH2CODE = os.path.join(base_dir, 'arch2code.py')

ROOT_PROJECT_FILE = os.path.join('root', 'yaml', 'rootProject.yaml')
CHILD_A_TOP = os.path.join('childA', 'yaml', 'childATop.yaml')
CHILD_B_TOP = os.path.join('childB', 'yaml', 'childBTop.yaml')
ROOT_TOP = os.path.join('root', 'yaml', 'rootTop.yaml')

ROOT_PROJECT_NAME = 'rootProj'
CHILD_A_PROJECT_NAME = 'childAProj'
CHILD_B_PROJECT_NAME = 'childBProj'

DB_NAME = 'addrgroup-qualification.db'


def copy_fixture(prefix):
    """Copy the committed fixture into a fresh temp tree under unittest/ and
    return its path. Inside unittest/ so the makefile scaffolds newModule lays
    down resolve the repo root the same way a real project does."""
    work = tempfile.mkdtemp(prefix=prefix, dir=test_dir)
    shutil.copytree(FIXTURE, work, dirs_exist_ok=True)
    return work


def edit_fixture_yaml(work, relPath, old, new):
    """Apply one anchored replacement to a copied fixture file. Fails loudly if
    the anchor is absent, so a fixture edit can never silently no-op and leave a
    negative test asserting against the unmodified topology."""
    path = os.path.join(work, relPath)
    with open(path) as f:
        text = f.read()
    if old not in text:
        raise AssertionError(
            f"fixture edit anchor not found in {relPath}: {old!r}")
    with open(path, 'w') as f:
        f.write(text.replace(old, new, 1))


def _run(args, timeout=180):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run([sys.executable, ARCH2CODE] + args,
                          capture_output=True, text=True, timeout=timeout,
                          cwd=base_dir, env=env)


def build_db(work):
    """Build the composed database from the root project. Returns
    (db_path, completed_process); the caller asserts on the return code."""
    db = os.path.join(work, DB_NAME)
    project = os.path.join(work, ROOT_PROJECT_FILE)
    return db, _run(['--yaml', project, '--db', db])


def db_for_project(work, db, projectName):
    """Copy the composed database and flip the persisted PROJECTNAME.

    Generated files are owned by the project owning their context, and both the
    `--newmodule` scaffold and the generators skip a file the running project
    does not own. A child-owned artifact is therefore produced by a run whose
    PROJECTNAME is that child, against the SAME composed database - which is
    what keeps the composed address-group registry in scope.
    """
    copy = os.path.join(work, f'{projectName}.db')
    shutil.copy(db, copy)
    conn = sqlite3.connect(copy)
    conn.execute("UPDATE _config SET value=? WHERE item='PROJECTNAME'",
                 (projectName,))
    conn.commit()
    conn.close()
    return copy


def newmodule(db):
    return _run(['--db', db, '-r', '--newmodule'])


def generate(db, filePath):
    return _run(['--db', db, '-r', '--systemc', '--file', filePath])


def instance_address_rows(db):
    """Return {(context, instance): (addressGroup, addressID)} for every
    instance row that carries an address group."""
    conn = sqlite3.connect(db)
    rows = {
        (context, instance): (group, addressID)
        for instance, context, group, addressID
        in conn.execute('SELECT instance, _context, addressGroup, addressID '
                        'FROM instances')
        if group
    }
    conn.close()
    return rows


def cleanup(work):
    shutil.rmtree(work, ignore_errors=True)
