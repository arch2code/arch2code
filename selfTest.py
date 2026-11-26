#!/usr/bin/env python3
"""Check that this machine can build and run an arch2code project.

Reports the tools, Python packages and environment variables a new project's
build reads, then creates a throwaway project in a temporary directory and runs
it through the README's getting-started flow. Prints one pass/fail table and
exits non-zero when any row fails. A failed project step keeps the temporary
directory and prints the step's log.

usage: selfTest.py <builder root>
"""
import importlib
import importlib.metadata
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

PROJECT = 'selftest'

# --newproject answers: name, firmware, RTL, copyright.
NEWPROJECT_ANSWERS = f"{PROJECT}\nn\ny\nCopyright arch2code selftest\n"

# The "A first design change" snippet from readme.md, inserted above blocks:.
DESIGN_CHANGE = """constants:
  DATA_WIDTH: {value: 32, desc: "Data bus width"}

types:
  data_t: {width: DATA_WIDTH, desc: "Data word"}

"""

# requirements.txt names whose import name differs.
IMPORT_NAMES = {'pyyaml': 'yaml', 'junit-xml': 'junit_xml'}

LOG_TAIL_LINES = 40


def firstLine(argv):
    result = subprocess.run(argv, capture_output=True, text=True)
    lines = (result.stdout or result.stderr).splitlines()
    return lines[0] if lines else "no version output"


def checkTool(rows, name, argv):
    if shutil.which(argv[0]) is None:
        rows.append((f"tool: {name}", False, f"{argv[0]} not found" + ("" if os.sep in argv[0] else " on PATH")))
    else:
        rows.append((f"tool: {name}", True, firstLine(argv)))


def checkHeader(rows, name, cxx, includeVar, header, versionOf):
    """Preprocess one header with the build's include paths and report its version macros."""
    # The include paths of CPP_INCLUDES in a2c-systemc.mk, which leaves out /usr/include
    # because -isystem on it breaks #include_next.
    includeDir = os.environ.get(includeVar)
    flags = [f"-isystem{includeDir}"] if includeDir and includeDir != '/usr/include' else []
    result = subprocess.run([cxx, '-x', 'c++', '-E', '-dM', '-H', '-'] + flags + ['-I/usr/local/include'],
                            input=f"#include <{header}>\n", capture_output=True, text=True)
    if result.returncode != 0:
        rows.append((f"tool: {name}", False, f"cannot include <{header}>"))
        return
    macros = dict(re.findall(r'^#define (\w+) (.*)$', result.stdout, re.M))
    # -H lists each included header; the first line is the one included above.
    path = result.stderr.splitlines()[0].removeprefix('. ')
    rows.append((f"tool: {name}", True, f"{versionOf(macros)} ({path})"))


def checkTools(rows):
    # a2c-common.mk picks the compiler: g++ under USE_GCC, else A2C_CLANG or clang++.
    cxx = 'g++' if os.environ.get('USE_GCC') else (os.environ.get('A2C_CLANG') or 'clang++')
    checkTool(rows, 'make', ['make', '--version'])
    checkTool(rows, 'git', ['git', '--version'])
    rows.append(("tool: python3", True, f"{sys.version.split()[0]} ({sys.executable})"))
    checkTool(rows, 'C++ compiler', [cxx, '--version'])
    checkTool(rows, 'verilator', ['verilator', '--version'])
    if shutil.which(cxx) is None:
        return
    checkHeader(rows, 'SystemC', cxx, 'SYSTEMC_INCLUDE', 'sysc/kernel/sc_ver.h',
                lambda m: f"{m['SC_VERSION_MAJOR']}.{m['SC_VERSION_MINOR']}.{m['SC_VERSION_PATCH']}")
    checkHeader(rows, 'Boost', cxx, 'BOOST_INCLUDE', 'boost/version.hpp',
                lambda m: m['BOOST_LIB_VERSION'].strip('"').replace('_', '.'))


def checkPythonPackages(rows, builder):
    with open(os.path.join(builder, 'requirements.txt')) as f:
        names = [re.match(r'[A-Za-z0-9_.-]+', line.strip()).group(0)
                 for line in f if line.strip() and not line.startswith('#')]
    for name in names:
        try:
            module = importlib.import_module(IMPORT_NAMES.get(name, name))
        except ImportError as e:
            rows.append((f"python: {name}", False, f"cannot import: {e}"))
            continue
        try:
            detail = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            detail = f"no package metadata, imported from {module.__file__}"
        rows.append((f"python: {name}", True, detail))


def checkPathVar(rows, var):
    value = os.environ.get(var)
    if not value:
        rows.append((f"env: {var}", False, "not set"))
    elif not os.path.isdir(value):
        rows.append((f"env: {var}", False, f"{value} does not exist"))
    else:
        rows.append((f"env: {var}", True, value))


def checkEnvironment(rows):
    # a2c-systemc.mk stops the build when these are unset.
    for var in ('SYSTEMC_INCLUDE', 'SYSTEMC_LIBDIR', 'BOOST_INCLUDE'):
        checkPathVar(rows, var)
    # A non-empty BOOST_LIBS replaces the default link line that reads LD_BOOST.
    if not os.environ.get('BOOST_LIBS', '').strip():
        checkPathVar(rows, 'LD_BOOST')


def addDesignChange(designFile, log):
    with open(designFile) as f:
        text = f.read()
    head, sep, tail = text.partition('\nblocks:\n')
    if not sep:
        with open(log, 'w') as f:
            f.write(f"{designFile} has no blocks: line to insert above\n")
        return False
    with open(designFile, 'w') as f:
        f.write(head + '\n' + DESIGN_CHANGE + 'blocks:\n' + tail)
    with open(log, 'w') as f:
        f.write(f"Inserted above blocks: in {designFile}:\n{DESIGN_CHANGE}")
    return True


def runStep(argv, cwd, log, stdin=None):
    with open(log, 'w') as f:
        return subprocess.run(argv, cwd=cwd, input=stdin, stdout=f,
                              stderr=subprocess.STDOUT, text=True).returncode == 0


def createRepository(project, builder, log):
    """An empty git repository with builder/ linked to the builder under test."""
    if not runStep(['git', 'init'], project, log):
        return False
    os.symlink(builder, os.path.join(project, 'builder'))
    with open(log, 'a') as f:
        f.write(f"Linked {project}/builder -> {builder}\n")
    return True


def roundTrip(rows, builder, work):
    """Create a project in work and take it through the README flow. Returns the failing log, or None."""
    project = os.path.join(work, PROJECT)
    os.makedirs(project)
    os.makedirs(os.path.join(work, 'logs'))
    jobs = f"-j{os.cpu_count()}"

    steps = [
        ('create repository', 'repository',
         lambda log: createRepository(project, builder, log)),
        ('--newproject', 'newproject',
         lambda log: runStep(['./builder/arch2code.py', '--newproject'], project, log,
                             stdin=NEWPROJECT_ANSWERS)),
        ('first run', 'first-run',
         lambda log: runStep(['make', jobs, '-C', f"{project}/rundir", 'run'], project, log)),
        ('add DATA_WIDTH and data_t', 'design-change',
         lambda log: addDesignChange(os.path.join(project, 'yaml', f"{PROJECT}.yaml"), log)),
        ('make newmodule', 'newmodule',
         lambda log: runStep(['make', jobs, '-C', project, 'newmodule'], project, log)),
        ('make gen', 'gen',
         lambda log: runStep(['make', jobs, '-C', project, 'gen'], project, log)),
        ('build model', 'build',
         lambda log: runStep(['make', jobs, '-C', f"{project}/rundir"], project, log)),
        ('lint', 'lint',
         lambda log: runStep(['make', jobs, '-C', f"{project}/rtl", 'lint'], project, log)),
        ('second run', 'second-run',
         lambda log: runStep(['make', jobs, '-C', f"{project}/rundir", 'run'], project, log)),
    ]
    for i, (name, stem, step) in enumerate(steps):
        relLog = os.path.join('logs', f"{i + 1:02d}-{stem}.log")
        log = os.path.join(work, relLog)
        if not step(log):
            rows.append((f"step: {name}", False, relLog))
            rows.extend((f"step: {later}", None, "skipped") for later, _, _ in steps[i + 1:])
            return log
        rows.append((f"step: {name}", True, relLog))
    return None


def printTable(rows):
    width = max(len(check) for check, _, _ in rows)
    result = {True: 'PASS', False: 'FAIL', None: 'SKIP'}
    print(f"{'Check':<{width}}  Result  Detail")
    print(f"{'-' * width}  ------  {'-' * 6}")
    for check, ok, detail in rows:
        print(f"{check:<{width}}  {result[ok]:<6}  {detail}")


def main():
    builder = os.path.abspath(sys.argv[1])
    start = time.monotonic()
    rows = []
    checkTools(rows)
    checkPythonPackages(rows, builder)
    checkEnvironment(rows)

    work = tempfile.mkdtemp(prefix='a2c-selftest-')
    print(f"arch2code selftest of {builder}")
    print(f"Work directory {work}: project in {PROJECT}/, step logs in logs/")
    failedLog = roundTrip(rows, builder, work)

    print("")
    printTable(rows)
    print("")
    if failedLog:
        print(f"Kept {work}")
        with open(failedLog) as f:
            lines = f.read().splitlines()
        print(f"Last {LOG_TAIL_LINES} lines of {failedLog}:")
        print('\n'.join(lines[-LOG_TAIL_LINES:]))
        print("")
    else:
        shutil.rmtree(work)
        print(f"Removed {work}")

    failed = sum(1 for _, ok, _ in rows if ok is False)
    elapsed = time.monotonic() - start
    if failed:
        print(f"selftest FAILED: {failed} of {len(rows)} checks failed ({elapsed:.0f} s)")
        sys.exit(1)
    print(f"selftest PASSED: {len(rows)} checks ({elapsed:.0f} s)")


if __name__ == '__main__':
    main()
