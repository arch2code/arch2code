#!/usr/bin/env python3
"""A composed root's firmware header must compile when two child projects
declare the same structure name.

Each context's firmware declarations are emitted into their own namespace nested
under `fw_ns`, folded back into `fw_ns` by a using-directive. The root's header
textually includes every child's header, so with one flat namespace the second
child's `struct pixelSt` was a redefinition. Firmware that opens `namespace
fw_ns` still reads an unambiguous name unqualified.
"""

import os
import shutil
import subprocess
import sys

from _addrgroup_qual_helpers import (
    CHILD_A_PROJECT_NAME,
    CHILD_A_TOP,
    CHILD_B_PROJECT_NAME,
    CHILD_B_TOP,
    ROOT_PROJECT_NAME,
    base_dir,
    build_db,
    cleanup,
    copy_fixture,
    db_for_project,
    edit_fixture_yaml,
    generate,
    newmodule,
)

COMMON_PROJECT_NAME = 'commonProj'

# Per project: the firmware header its top context owns.
PROJECT_HEADERS = [
    (COMMON_PROJECT_NAME, os.path.join('common', 'fw', 'include', 'sharedTypesIncludesFW.h')),
    (CHILD_A_PROJECT_NAME, os.path.join('childA', 'fw', 'include', 'childATopIncludesFW.h')),
    (CHILD_B_PROJECT_NAME, os.path.join('childB', 'fw', 'include', 'childBTopIncludesFW.h')),
    (ROOT_PROJECT_NAME, os.path.join('root', 'fw', 'include', 'rootTopIncludesFW.h')),
]

SAME_STRUCT = ('structures:\n'
               '    pixelSt:\n'
               '        value: { varType: apbCfgT, desc: "same struct name in both children" }\n'
               '\n'
               'registers:\n')

# Firmware in the style of a hand-written fw/src file: opens fw_ns and names a
# unique shared type unqualified, and names each child's copy qualified.
PROBE = """#include "rootTopIncludesFW.h"
namespace fw_ns {
static apbCfgSt sharedProbe;
static {nsA}::pixelSt childAProbe;
static {nsB}::pixelSt childBProbe;
int probe() { return sharedProbe.value + childAProbe.value + childBProbe.value; }
}
int main() { return fw_ns::probe(); }
"""


HEADER_INCLUDES_BEGIN = '// GENERATED_CODE_BEGIN --template=structures --section=headerIncludes'
TYPES_BEGIN = '// GENERATED_CODE_BEGIN --template=includes --section=types'
USER_IN_WRAPPER = 'static int userInWrapper = 1;'
USER_BLOCK = ['namespace fw_ns {', 'inline constexpr int userCalibration = 42;', '}']


def _fail(msg):
    print(f"FAIL: {msg}")
    return False


def _context_namespace(text, relPath):
    names = {line.split('::', 1)[1].split(' ', 1)[0]
             for line in text.splitlines()
             if line.startswith('namespace fw_ns::') and line.rstrip().endswith('{')}
    if len(names) != 1:
        raise AssertionError(f"{relPath} opens {sorted(names)} context namespaces, expected one")
    return names.pop()


def _insert_after_end(lines, beginPrefix, newLines):
    begin = next(i for i, line in enumerate(lines) if line.startswith(beginPrefix))
    end = next(i for i in range(begin, len(lines)) if lines[i].startswith('// GENERATED_CODE_END'))
    lines[end + 1:end + 1] = newLines


def _legacy_shape(text):
    """The header with the old scaffold's `namespace fw_ns {` block opened after
    the headerIncludes region and closed before the include guard's #endif, and a
    user line inside that block between the types and enums regions."""
    lines = text.splitlines()
    guard = max(i for i, line in enumerate(lines) if line.startswith('#endif'))
    lines[guard:guard] = ['} // end of namespace fw_ns']
    _insert_after_end(lines, TYPES_BEGIN, [USER_IN_WRAPPER])
    _insert_after_end(lines, HEADER_INCLUDES_BEGIN, ['namespace fw_ns {'])
    return '\n'.join(lines) + '\n'


def _migrated_shape(text):
    """What migrating `_legacy_shape(text)` yields: the scaffold block is gone and
    the user line keeps its fw_ns scope in a block of its own."""
    lines = text.splitlines()
    _insert_after_end(lines, TYPES_BEGIN,
                      ['namespace fw_ns {', USER_IN_WRAPPER, '} // namespace fw_ns'])
    return '\n'.join(lines) + '\n'


def _user_block_shape(text):
    """A current-format header with a user-authored fw_ns block after the
    headerIncludes region, where the old scaffold opened its block."""
    lines = text.splitlines()
    _insert_after_end(lines, HEADER_INCLUDES_BEGIN, USER_BLOCK)
    return '\n'.join(lines) + '\n'


def _compile(work, nsByHeader):
    probe = os.path.join(work, 'probe.cpp')
    with open(probe, 'w') as f:
        f.write(PROBE.replace('{nsA}', nsByHeader[PROJECT_HEADERS[1][1]])
                     .replace('{nsB}', nsByHeader[PROJECT_HEADERS[2][1]]))
    includeDirs = [os.path.dirname(os.path.join(work, relPath)) for _, relPath in PROJECT_HEADERS]
    includeDirs.append(os.path.join(base_dir, 'common', 'systemc'))
    cmd = ['clang++', '-std=c++23', '-fsyntax-only', '-Wall', '-Wextra', '-Wno-unused-variable', probe]
    cmd += [f'-I{d}' for d in includeDirs]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def _run():
    print("composed build: two children declaring struct pixelSt, root fw header compiles")
    work = copy_fixture('fw_ns_')
    try:
        for relPath in (CHILD_A_TOP, CHILD_B_TOP):
            edit_fixture_yaml(work, relPath, 'registers:\n', SAME_STRUCT)
        db, built = build_db(work)
        if built.returncode != 0:
            return _fail(f"composed database build failed:\n{built.stdout}\n{built.stderr}")

        headers = dict()
        for projectName, relPath in PROJECT_HEADERS:
            projectDb = db_for_project(work, db, projectName)
            made = newmodule(projectDb)
            if made.returncode != 0:
                return _fail(f"--newmodule under {projectName} failed:\n{made.stdout}\n{made.stderr}")
            path = os.path.join(work, relPath)
            gen = generate(projectDb, path)
            if gen.returncode != 0:
                return _fail(f"generating {relPath} failed:\n{gen.stdout}\n{gen.stderr}")
            with open(path) as f:
                headers[relPath] = f.read()

        nsByHeader = {relPath: _context_namespace(text, relPath) for relPath, text in headers.items()}
        for relPath, text in headers.items():
            own = nsByHeader[relPath]
            if f'namespace fw_ns {{ using namespace {own}; }}' not in text:
                return _fail(f"{relPath} does not fold {own} into fw_ns:\n{text}")
        if len(set(nsByHeader.values())) != len(nsByHeader):
            return _fail(f"context namespaces are not distinct: {nsByHeader}")
        for relPath in (PROJECT_HEADERS[1][1], PROJECT_HEADERS[2][1]):
            if 'struct pixelSt {' not in headers[relPath]:
                return _fail(f"{relPath} lacks struct pixelSt:\n{headers[relPath]}")

        compiled = _compile(work, nsByHeader)
        if compiled.returncode != 0:
            return _fail(f"root firmware header does not compile:\n{compiled.stderr}")

        # A header still carrying the old scaffold's `namespace fw_ns {` block
        # around its regions is warned about at database time and migrated in
        # place by newmodule, both under the project that owns it; user text
        # inside that block survives with its fw_ns scope.
        rootRel = PROJECT_HEADERS[3][1]
        rootPath = os.path.join(work, rootRel)
        with open(rootPath, 'w') as f:
            f.write(_legacy_shape(headers[rootRel]))
        db, built = build_db(work)
        if built.returncode != 0:
            return _fail(f"database build with a legacy header failed:\n{built.stdout}\n{built.stderr}")
        if 'scaffold-owned namespace fw_ns block' not in built.stdout + built.stderr:
            return _fail(f"no legacy firmware header warning at database time:\n{built.stdout}\n{built.stderr}")
        rootDb = db_for_project(work, db, ROOT_PROJECT_NAME)
        made = newmodule(rootDb)
        if made.returncode != 0:
            return _fail(f"--newmodule with a legacy header failed:\n{made.stdout}\n{made.stderr}")
        gen = generate(rootDb, rootPath)
        if gen.returncode != 0:
            return _fail(f"regenerating the migrated header failed:\n{gen.stdout}\n{gen.stderr}")
        with open(rootPath) as f:
            migrated = f.read()
        if migrated != _migrated_shape(headers[rootRel]):
            return _fail(f"migrated {rootRel} is not the fresh header plus the user line:\n{migrated}")
        compiled = _compile(work, nsByHeader)
        if compiled.returncode != 0:
            return _fail(f"migrated root firmware header does not compile:\n{compiled.stderr}")

        # A current-format header whose user region holds its own fw_ns block is
        # not the legacy shape: no warning, and newmodule and gen leave it intact.
        userBlock = _user_block_shape(headers[rootRel])
        with open(rootPath, 'w') as f:
            f.write(userBlock)
        db, built = build_db(work)
        if built.returncode != 0:
            return _fail(f"database build with a user fw_ns block failed:\n{built.stdout}\n{built.stderr}")
        if 'scaffold-owned namespace fw_ns block' in built.stdout + built.stderr:
            return _fail(f"user fw_ns block reported as legacy:\n{built.stdout}\n{built.stderr}")
        rootDb = db_for_project(work, db, ROOT_PROJECT_NAME)
        made = newmodule(rootDb)
        if made.returncode != 0:
            return _fail(f"--newmodule with a user fw_ns block failed:\n{made.stdout}\n{made.stderr}")
        gen = generate(rootDb, rootPath)
        if gen.returncode != 0:
            return _fail(f"regenerating a header with a user fw_ns block failed:\n{gen.stdout}\n{gen.stderr}")
        with open(rootPath) as f:
            kept = f.read()
        if kept != userBlock:
            return _fail(f"{rootRel} with a user fw_ns block was changed:\n{kept}")

        print("PASS")
        return True
    finally:
        cleanup(work)


def run_all_tests():
    if shutil.which('clang++') is None:
        print("SKIP: clang++ not found")
        return 0
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
