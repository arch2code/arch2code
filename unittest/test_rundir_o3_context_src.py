#!/usr/bin/env python3
"""The builder compiles the generated context files at -O3 with no rundir help.

Works on a private copy of examples/simple_ip whose root renames its includeFW
fileMap entry to Fw, so no context file matches the old '*Includes*' names.
The rundir Makefile is deleted and re-scaffolded by newmodule. Checks:
- the scaffolded rundir Makefile has no EXTRA_O3_CPP_SRC line;
- in the dry-run compile commands, under Clang and under GCC, every context
  module (A2C_CPP_CONTEXT_MODULE_FILES) compiles its object at -O3 while Clang
  precompiles its PCM without -O3, every firmware context .cpp
  (A2C_CPP_CONTEXT_SRC_FILES) compiles at -O3, and no other module does;
- EXTRA_O3_CPP_SRC naming the context sources again, as older rundir Makefiles
  do, draws no make warning;
- with the original rundir Makefile, which carries the old EXTRA_O3_CPP_SRC
  filter, the SystemC model builds with the same -O3 compiles and runs, and
  run-vl passes.
"""

import os
import shlex
import sys

from test_file_prefix import (PROJECT_FILES, copy_simple_ip, edit, make, point_repo_root,
                              remove, run)

# Context sources named twice in O3_CPP_SRC, as an older rundir Makefile does.
DUPLICATE_O3 = 'EXTRA_O3_CPP_SRC=$(A2C_CPP_CONTEXT_SRC_FILES)'


def makeLists(rundir, *args):
    # The manifest lists, with the builder's own PCM path for each module.
    printer = (
        'printLists: ; '
        '$(foreach f,$(A2C_CPP_CONTEXT_MODULE_FILES),'
        '$(info contextModule $(f) $(call cpp_module_pcm,$(f))))'
        '$(foreach f,$(filter-out $(A2C_CPP_CONTEXT_MODULE_FILES),$(CPP_MODULE_SRC)),'
        '$(info otherModule $(f) $(call cpp_module_pcm,$(f))))'
        '$(foreach f,$(A2C_CPP_CONTEXT_SRC_FILES),$(info contextSrc $(f)))@:')
    result = run(['make', '-C', rundir, '--no-print-directory', '--eval', printer,
                  'printLists', *args])
    if result.returncode != 0:
        raise AssertionError(f"printLists failed:\n{result.stdout}\n{result.stderr}")
    lists = {'contextModule': {}, 'otherModule': {}, 'contextSrc': []}
    for line in result.stdout.splitlines():
        fields = line.split(' ')
        if fields[0] in ('contextModule', 'otherModule'):
            lists[fields[0]][fields[1]] = fields[2]
        elif fields[0] == 'contextSrc':
            lists['contextSrc'].append(fields[1])
    return lists


def compileCommands(output):
    # Compiler invocations from make's echoed recipes, as token lists.
    commands = []
    for line in output.splitlines():
        tokens = shlex.split(line)
        if tokens and os.path.basename(tokens[0]) in ('clang++', 'g++'):
            commands.append(tokens)
    return commands


def compileOf(commands, source):
    # The one command whose -c operand is `source`.
    hits = [c for c in commands if '-c' in c and c[c.index('-c') + 1] == source]
    if len(hits) != 1:
        raise AssertionError(f"expected one compile of {source}, found {len(hits)}")
    return hits[0]


def precompileOf(commands, source):
    hits = [c for c in commands if '--precompile' in c and source in c]
    if len(hits) != 1:
        raise AssertionError(f"expected one precompile of {source}, found {len(hits)}")
    return hits[0]


def checkFlags(label, output, lists, gcc):
    # Returns the failures for one compile log.
    failures = []
    commands = compileCommands(output)

    def expect(tokens, want, what):
        if ('-O3' in tokens) != want:
            failures.append(f"{label}: {what} {'lacks' if want else 'carries'} -O3")

    if not lists['contextModule'] or not lists['contextSrc'] or not lists['otherModule']:
        failures.append(f"{label}: a manifest list is empty: {lists}")
    for kind, want in (('contextModule', True), ('otherModule', False)):
        for src, pcm in lists[kind].items():
            if gcc:
                expect(compileOf(commands, src), want, f"module object of {src}")
            else:
                expect(compileOf(commands, pcm), want, f"module object of {src}")
                expect(precompileOf(commands, src), False, f"module precompile of {src}")
    for src in lists['contextSrc']:
        expect(compileOf(commands, src), True, f"firmware context source {src}")
    makeWarnings = [line for line in output.splitlines()
                    if 'given more than once' in line or 'overriding recipe' in line]
    if makeWarnings:
        failures.append(f"{label}: make warned:\n" + '\n'.join(makeWarnings))
    return failures


def dryRun(rundir, *args):
    result = run(['make', '-C', rundir, '-n', 'compdb-capture', *args])
    if result.returncode != 0:
        raise AssertionError(f"make -n failed:\n{result.stdout}\n{result.stderr}")
    return result.stdout + result.stderr


def main():
    work = copy_simple_ip()
    try:
        edit(os.path.join(work, PROJECT_FILES['.']),
             '        includeFW: { name: "IncludesFW",', '        includeFW: { name: "Fw",')
        fw = os.path.join(work, 'fw')
        for ext in ('h', 'cpp'):
            os.rename(os.path.join(fw, f'simple_ipIncludesFW.{ext}'),
                      os.path.join(fw, f'simple_ipFw.{ext}'))
        rundir = os.path.join(work, 'rundir')
        rundirMakefile = os.path.join(rundir, 'Makefile')
        with open(rundirMakefile) as f:
            originalMakefile = f.read()
        os.remove(rundirMakefile)
        run(['make', '-C', work, 'clean'])
        make(work, 'newmodule')
        point_repo_root(work)
        make(work, 'gen')

        failures = []
        with open(rundirMakefile) as f:
            if 'EXTRA_O3_CPP_SRC' in f.read():
                failures.append("the scaffolded rundir Makefile sets EXTRA_O3_CPP_SRC")

        lists = makeLists(rundir)
        if os.path.join(fw, 'simple_ipFw.cpp') not in lists['contextSrc']:
            failures.append(f"fw/simple_ipFw.cpp is not a context source: {lists['contextSrc']}")
        failures += checkFlags('clang dry run', dryRun(rundir), lists, gcc=False)
        failures += checkFlags('gcc dry run', dryRun(rundir, 'USE_GCC=1'),
                               makeLists(rundir, 'USE_GCC=1'), gcc=True)
        failures += checkFlags('clang dry run, context sources in EXTRA_O3_CPP_SRC',
                               dryRun(rundir, DUPLICATE_O3), lists, gcc=False)

        # The original Makefile carries the old EXTRA_O3_CPP_SRC filter and the
        # run-vl target.
        with open(rundirMakefile, 'w') as f:
            f.write(originalMakefile)
        point_repo_root(work)
        build = make(rundir, DUPLICATE_O3)
        failures += checkFlags('model build', build, lists, gcc=False)
        make(rundir, 'run')
        make(rundir, 'run-vl')

        if failures:
            for failure in failures:
                print(f"FAIL: {failure}")
            print("SOME TESTS FAILED")
            return 1
        print(f"PASS: {len(lists['contextModule'])} context modules and "
              f"{len(lists['contextSrc'])} firmware context sources compile at -O3, "
              f"{len(lists['otherModule'])} other modules do not; the model and run-vl pass")
        print("ALL TESTS PASSED")
        return 0
    finally:
        remove(work)


if __name__ == '__main__':
    sys.exit(main())
