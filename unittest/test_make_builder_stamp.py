#!/usr/bin/env python3
"""Editing a builder template, generator module or schema regenerates a project.

Builds a private copy of examples/helloWorld against a private builder outside
any git checkout: its templates/, pysrc/ and config/ are copies, the rest of
the builder is linked. git is unusable (GIT_DIR names no repository). After a
full `make gen`, checks:
- a second `make gen` runs no generator and leaves the builder stamp alone;
- a newer mtime on one builder template makes `make gen -n` regenerate;
- after a real `make gen` the next one is again a no-op;
- a file added under templates/ makes `make gen -n` regenerate;
- so does a newer config/*.py or arch2code.py, and a file under a pro/
  templates/ or config/ directory once pro is present.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time

from _addrctl_helpers import base_dir


FIXTURE = os.path.join(base_dir, 'examples', 'helloWorld')
STAMP = os.path.join('.gen', 'builder.stamp')
COPIED = ('templates', 'pysrc', 'config', 'arch2code.py')
NOT_LINKED = ('examples', 'unittest', '.git', '__pycache__')


def env():
    return dict(os.environ, NO_COLOR='1', GIT_DIR='/nonexistent')


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


def make(project, builder, *args):
    result = subprocess.run(['make', '-C', project, '--no-print-directory',
                             f'REPO_ROOT={project}', f'A2C_ROOT={builder}', *args],
                            capture_output=True, text=True, timeout=600, env=env())
    return result, result.stdout + result.stderr


def generatorRuns(output):
    return [l for l in output.splitlines() if 'arch2code.py' in l and '--file' in l]


def firstTemplate(builder):
    for dirpath, dirnames, filenames in sorted(os.walk(os.path.join(builder, 'templates'))):
        dirnames[:] = sorted(d for d in dirnames if d != '__pycache__')
        for name in sorted(filenames):
            if name.endswith('.py'):
                return os.path.join(dirpath, name)
    raise AssertionError("no template found")


def stampMtime(project):
    path = os.path.join(project, STAMP)
    return os.stat(path).st_mtime_ns if os.path.exists(path) else None


def main():
    failures = []

    def check(ok, message):
        print(f"{'PASS' if ok else 'FAIL'}: {message}")
        if not ok:
            failures.append(message)

    with tempfile.TemporaryDirectory(prefix='make_builder_stamp_') as tmp:
        builder = os.path.join(tmp, 'builder')
        privateBuilder(builder)
        template = firstTemplate(builder)
        project = os.path.join(tmp, 'helloWorld')
        shutil.copytree(FIXTURE, project, symlinks=True, ignore=shutil.ignore_patterns(
            'rundir', '.gen', '*.db', '*.db-*', 'compile_commands.json'))
        for target in ('db', 'gen'):
            result, output = make(project, builder, target)
            if result.returncode != 0:
                print(f"FAIL: make {target} failed:\n{output}")
                return 1

        before = stampMtime(project)
        result, output = make(project, builder, 'gen')
        check(result.returncode == 0 and not generatorRuns(output),
              f"an untouched second make gen runs no generator: {generatorRuns(output)}")
        check(before is not None and stampMtime(project) == before,
              f"an untouched make gen leaves {STAMP} alone")

        now = time.time() + 2
        os.utime(template, (now, now))
        result, output = make(project, builder, 'gen', '-n')
        runs = generatorRuns(output)
        check(result.returncode == 0 and runs,
              f"a newer {os.path.relpath(template, builder)} makes make gen -n regenerate "
              f"({len(runs)} generator runs)")

        result, output = make(project, builder, 'gen')
        check(result.returncode == 0 and generatorRuns(output),
              "make gen regenerates after the template change")
        before = stampMtime(project)
        result, output = make(project, builder, 'gen')
        check(result.returncode == 0 and not generatorRuns(output)
              and stampMtime(project) == before,
              f"the make gen after that is a no-op: {generatorRuns(output)}")

        probe = os.path.join(builder, 'templates', 'probe.txt')
        with open(probe, 'w') as f:
            f.write('probe\n')
        old = os.stat(os.path.join(builder, 'arch2code.py'))
        os.utime(probe, ns=(old.st_atime_ns, old.st_mtime_ns))
        result, output = make(project, builder, 'gen', '-n')
        runs = generatorRuns(output)
        check(result.returncode == 0 and runs,
              f"a file added under templates/ (with an old mtime) makes make gen -n regenerate "
              f"({len(runs)} generator runs)")

        def triggers(label, path):
            # A newer mtime on `path` regenerates; a real make gen then resets.
            now = time.time() + 4
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if not os.path.exists(path):
                open(path, 'w').close()
            os.utime(path, (now, now))
            result, output = make(project, builder, 'gen', '-n')
            runs = generatorRuns(output)
            check(result.returncode == 0 and runs,
                  f"{label} makes make gen -n regenerate ({len(runs)} generator runs)")
            make(project, builder, 'gen')

        make(project, builder, 'gen')
        triggers("a newer config/postParseChecks.py",
                 os.path.join(builder, 'config', 'postParseChecks.py'))
        triggers("a newer arch2code.py", os.path.join(builder, 'arch2code.py'))
        triggers("a file under pro/templates/",
                 os.path.join(builder, 'pro', 'templates', 'probe.py'))
        triggers("a file under pro/config/",
                 os.path.join(builder, 'pro', 'config', 'probe.yaml'))

    if failures:
        print("SOME TESTS FAILED")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == '__main__':
    sys.exit(main())
