#!/usr/bin/env python3
"""A copied or moved project tree rebuilds its database instead of using the old one.

The database and the build manifest store absolute paths, and a copy made with
preserved mtimes (rsync -a, cp -a) carries a database that looks newer than its
YAML. Builds a private copy of examples/helloWorld and checks:
- in a second copy with preserved mtimes, `make db` rebuilds the database. The
  rebuilt database and its manifest name the copy only, and a second `make db`
  is a no-op;
- a manifest in the old format, with no recorded root, rebuilds the database
  once and then leaves it alone;
- after the first copy is moved away, `make db` there rebuilds instead of
  stopping on the old manifest's YAML paths;
- after a move whose first rebuild fails on bad YAML, restoring the YAML lets
  `make db` rebuild;
- built against a private builder that is then moved, `make db` with the new
  builder path rebuilds instead of stopping on the old builder's YAML paths;
- a project whose root is not REPO_ROOT warns on every make that its manifest
  stays stale, both when REPO_ROOT is overridden and when dirs: root changes
  after a good build has left a manifest behind.
"""

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir


FIXTURE = os.path.join(base_dir, 'examples', 'helloWorld')
DB = 'helloWorld.db'
TB_YAML = os.path.join('arch', 'yaml', 'helloWorld_tb.yaml')
COPIED = ('templates', 'pysrc', 'config', 'arch2code.py')
NOT_LINKED = ('examples', 'unittest', '.git', '__pycache__')


def make(project, *args, builder=base_dir):
    result = subprocess.run(['make', '-C', project, '--no-print-directory',
                             f'REPO_ROOT={project}', f'A2C_ROOT={builder}', *args],
                            capture_output=True, text=True, timeout=600,
                            env=dict(os.environ, NO_COLOR='1'))
    return result, result.stdout + result.stderr


def dbStrings(path):
    # Every text value in every table of the database.
    con = sqlite3.connect(path)
    try:
        values = []
        for (table,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            for row in con.execute(f'SELECT * FROM "{table}"'):
                values.extend(v for v in row if isinstance(v, str))
        return values
    finally:
        con.close()


def mtime(path):
    return os.stat(path).st_mtime_ns if os.path.exists(path) else None


def privateBuilder(builder):
    os.makedirs(builder)
    for name in os.listdir(base_dir):
        src = os.path.join(base_dir, name)
        if name in COPIED and os.path.isdir(src):
            shutil.copytree(src, os.path.join(builder, name),
                            ignore=shutil.ignore_patterns('__pycache__'))
        elif name in COPIED:
            shutil.copy2(src, os.path.join(builder, name))
        elif name not in NOT_LINKED:
            os.symlink(src, os.path.join(builder, name))


def main():
    failures = []

    def check(ok, message):
        print(f"{'PASS' if ok else 'FAIL'}: {message}")
        if not ok:
            failures.append(message)

    with tempfile.TemporaryDirectory(prefix='make_relocated_') as tmp:
        first = os.path.join(tmp, 'first')
        second = os.path.join(tmp, 'second')
        shutil.copytree(FIXTURE, first, symlinks=True, ignore=shutil.ignore_patterns(
            'rundir', '.gen', '*.db', '*.db-*', 'compile_commands.json'))
        result, output = make(first, 'db')
        if result.returncode != 0:
            print(f"FAIL: make db failed in the first copy:\n{output}")
            return 1
        firstPaths = [v for v in dbStrings(os.path.join(first, DB)) if first in v]
        check(bool(firstPaths), f"the first copy's database names {first} ({len(firstPaths)} values)")

        shutil.copytree(first, second, symlinks=True, copy_function=shutil.copy2)
        dbBefore = mtime(os.path.join(second, DB))
        result, output = make(second, 'db')
        check(result.returncode == 0 and mtime(os.path.join(second, DB)) != dbBefore,
              f"make db in the copy rebuilds the database:\n{output.strip()}")

        stale = [v for v in dbStrings(os.path.join(second, DB)) if first in v]
        check(not stale, f"the copy's database names no path in the first copy: {stale[:3]}")
        own = [v for v in dbStrings(os.path.join(second, DB)) if second in v]
        check(bool(own), f"the copy's database names {second} ({len(own)} values)")
        with open(os.path.join(second, '.gen', 'build.mk')) as f:
            manifest = f.read()
        check(first not in manifest and second in manifest,
              "the copy's build manifest names the copy, not the first tree")

        dbBefore = mtime(os.path.join(second, DB))
        result, output = make(second, 'db')
        check(result.returncode == 0 and mtime(os.path.join(second, DB)) == dbBefore,
              f"a second make db in the copy is a no-op:\n{output.strip()}")

        buildMk = os.path.join(second, '.gen', 'build.mk')
        with open(buildMk) as f:
            lines = f.read().splitlines(keepends=True)
        stamp = os.stat(buildMk)
        with open(buildMk, 'w') as f:
            f.write(''.join(l for l in lines if not l.startswith('A2C_MANIFEST_REPO_ROOT')))
        os.utime(buildMk, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        dbBefore = mtime(os.path.join(second, DB))
        result, output = make(second, 'db')
        dbAfter = mtime(os.path.join(second, DB))
        check(result.returncode == 0 and dbAfter != dbBefore,
              f"an old-format manifest rebuilds the database:\n{output.strip()}")
        result, output = make(second, 'db')
        check(result.returncode == 0 and mtime(os.path.join(second, DB)) == dbAfter
              and 'warning' not in output.lower(),
              f"the make db after that is a no-op:\n{output.strip()}")

        moved = os.path.join(tmp, 'moved')
        os.rename(first, moved)
        result, output = make(moved, 'db')
        check(result.returncode == 0,
              f"make db in a moved tree rebuilds instead of stopping:\n{output.strip()}")
        if result.returncode == 0:
            stale = [v for v in dbStrings(os.path.join(moved, DB)) if first in v]
            check(not stale, f"the moved tree's database names no path at the old location: {stale[:3]}")

        again = os.path.join(tmp, 'again')
        os.rename(moved, again)
        tbYaml = os.path.join(again, TB_YAML)
        with open(tbYaml) as f:
            goodYaml = f.read()
        with open(tbYaml, 'w') as f:
            f.write(goodYaml + '\n: [unclosed\n')
        result, output = make(again, 'db')
        check(result.returncode != 0, "the first rebuild after a move fails on the bad YAML")
        with open(tbYaml, 'w') as f:
            f.write(goodYaml)
        result, output = make(again, 'db')
        check(result.returncode == 0,
              f"with the YAML restored, make db rebuilds the moved tree:\n{output.strip()}")
        if result.returncode == 0:
            stale = [v for v in dbStrings(os.path.join(again, DB)) if moved in v]
            check(not stale, f"that database names no path at the previous location: {stale[:3]}")

        builderA = os.path.join(tmp, 'builderA')
        builderB = os.path.join(tmp, 'builderB')
        privateBuilder(builderA)
        project = os.path.join(tmp, 'ownBuilder')
        shutil.copytree(FIXTURE, project, symlinks=True, ignore=shutil.ignore_patterns(
            'rundir', '.gen', '*.db', '*.db-*', 'compile_commands.json'))
        result, output = make(project, 'db', builder=builderA)
        if result.returncode != 0:
            print(f"FAIL: make db against the private builder failed:\n{output}")
            return 1
        os.rename(builderA, builderB)
        result, output = make(project, 'db', builder=builderB)
        check(result.returncode == 0,
              f"make db after the builder moves rebuilds instead of stopping:\n{output.strip()}")
        if result.returncode == 0:
            stale = [v for v in dbStrings(os.path.join(project, DB)) if builderA in v]
            check(not stale, f"that database names no path in the old builder: {stale[:3]}")

        # REPO_ROOT names a directory the project's dirs: root does not, so the
        # manifest lands elsewhere and this root never gets one.
        elsewhere = os.path.join(tmp, 'elsewhere')
        shutil.copytree(os.path.join(project, 'include'), os.path.join(elsewhere, 'include'))
        for attempt in (1, 2):
            result = subprocess.run(
                ['make', '-C', project, '--no-print-directory', f'REPO_ROOT={elsewhere}',
                 f'A2C_ROOT={builderB}', f'A2C_PRJ_YAML={project}/arch/yaml/project.yaml', 'db'],
                capture_output=True, text=True, timeout=600, env=dict(os.environ, NO_COLOR='1'))
            output = result.stdout + result.stderr
            check('stale' in output and 'warning' in output.lower(),
                  f"make {attempt} with a root that is not REPO_ROOT warns that the manifest "
                  f"stays stale:\n{output.strip()}")

        rootChange = os.path.join(tmp, 'rootChange')
        shutil.copytree(FIXTURE, rootChange, symlinks=True, ignore=shutil.ignore_patterns(
            'rundir', '.gen', '*.db', '*.db-*', 'compile_commands.json'))
        result, output = make(rootChange, 'db')
        check(result.returncode == 0 and 'stays stale' not in output,
              f"a good build of the rootChange copy does not warn:\n{output.strip()}")
        projectYaml = os.path.join(rootChange, 'arch', 'yaml', 'project.yaml')
        with open(projectYaml) as f:
            text = f.read()
        otherRoot = os.path.join(tmp, 'otherRoot')
        os.makedirs(otherRoot)
        with open(projectYaml, 'w') as f:
            f.write(text.replace('  root: ../..', f'  root: {otherRoot}', 1))
        result, output = make(rootChange, 'db')
        check('stays stale' in output and 'warning' in output.lower(),
              f"after dirs: root moves to another directory, make db warns that the manifest "
              f"stays stale:\n{output.strip()}")

    if failures:
        print("SOME TESTS FAILED")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == '__main__':
    sys.exit(main())
