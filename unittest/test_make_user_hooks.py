#!/usr/bin/env python3
"""Each EXTRA_* user hook set in shared.mk reaches its own tool command only.

Works on a private copy of examples/simple_ip whose include/make/shared.mk
appends one distinct value to every tool hook. Checks:
- EXTRA_GEN_OPTS on the db build, every gen call and newmodule of the project,
  including the --vlBoundary call that gen makes under USE_VCS and USE_XCELIUM;
- VERILATOR_USER_OPTS and EXTRA_VERILATOR_OPTS on lint and on every model
  verilate, EXTRA_LINT_OPTS on lint only, EXTRA_VL_OPTS on the verilates only;
- the verilator hooks sit after the builder options, in the order
  VERILATOR_USER_OPTS, EXTRA_VERILATOR_OPTS, then EXTRA_LINT_OPTS or
  EXTRA_VL_OPTS;
- EXTRA_CXX_FLAGS sits after every builder C++ flag, including the
  A2C_LAYER_CXX_FLAGS and the VL_DUT=1 additions;
- a command-line VERILATOR_USER_OPTS or EXTRA_CXX_FLAGS replaces the project's
  value, and a command-line EXTRA_CXX_FLAGS keeps the layer's;
- EXTRA_VL_CFLAGS inside the single quoted -CFLAGS argument of each verilate;
- EXTRA_VL_LIB_OBJS, named under $(A2C_VL_BUILD_DIR), added to the archive and
  ordered after every verilate, in the verilation sub-make that reads only
  shared.mk;
- a rundir Makefile scaffolded by newmodule keeps the EXTRA_CPP_SRC,
  EXTRA_CPP_INCLUDES and EXTRA_LD_FLAGS that shared.mk sets, so they reach
  the C++ compile and the link;
- the HDL hooks (A2C_LAYER_HDL_F_FILES, then the EXTRA_HDL_* hooks, each list
  behind -F) after a2c.f and before the project's rtl.f on lint, every per-top
  verilate, the vlogan RTL analysis and the xrun DUT library, never on the
  Verilator runtime build or a vlogan -sc_model;
- under USE_VCS=1: EXTRA_VLOGAN_OPTS on both vlogan stages,
  EXTRA_VCS_LIB_SV_FILES after the layer's library files, EXTRA_VCS_OPTS and
  the layer's then the project's link flags on the vcs link;
- under USE_XCELIUM=1: EXTRA_XRUN_OPTS before -makelib, EXTRA_XRUN_LIB_OPTS
  inside the DUT library after the HDL hooks, the layer's then the project's
  link flags on the link, EXTRA_XRUN_R_OPTS in the run script;
- each hook's value in the parse-time stamp that records its command, and the
  HDL files and lists as prerequisites of the verilate, the vlogan analysis and
  the xrun snapshot;
- make help-hooks prints every value and lists every EXTRA_* variable the
  builder makefiles read.

The simulator dry runs pass placeholder VCS_HOME, XCELIUM_TOOLS and
XRUN_GCC_VERS, so they need neither tool. USE_GCC is dropped from the
environment, so the compile commands are clang++ whatever the caller's shell
selects.
"""

import glob
import os
import re
import shlex
import sys

from test_file_prefix import copy_simple_ip, make, point_repo_root, run
from _tmp_helpers import remove_tree

HOOK_VALUES = {
    'EXTRA_GEN_OPTS': '--debug',
    'VERILATOR_USER_OPTS': '-DHOOK_USER',
    'EXTRA_VERILATOR_OPTS': '-DHOOK_VERILATOR',
    'EXTRA_LINT_OPTS': '-DHOOK_LINT',
    'EXTRA_VL_OPTS': '-DHOOK_VL',
    'EXTRA_VL_CFLAGS': '-DHOOK_CFLAG',
    'EXTRA_VL_LIB_OBJS': '$(A2C_VL_BUILD_DIR)/obj_dir/hook/hook.o',
    'EXTRA_HDL_INCDIRS': '/hook/inc',
    'EXTRA_HDL_DEFINES': 'HOOK_DEF',
    'EXTRA_VLOGAN_OPTS': '-DHOOK_VLOGAN',
    'EXTRA_VCS_OPTS': '-DHOOK_VCS',
    'EXTRA_XRUN_OPTS': '-DHOOK_XRUN',
    'EXTRA_XRUN_LIB_OPTS': '-DHOOK_XLIB',
    'EXTRA_XRUN_R_OPTS': '+hook_r',
}
# Hooks naming files, which the build lists as prerequisites; created in the
# copy under hookSrc/.
HOOK_FILES = {
    'EXTRA_HDL_FILES': 'vip.sv',
    'EXTRA_HDL_F_FILES': 'vip.f',
    'EXTRA_VCS_LIB_SV_FILES': 'lib.sv',
}
LINT_ONLY = {'-DHOOK_LINT'}
VL_ONLY = {'-DHOOK_VL'}
BOTH = {'-DHOOK_USER', '-DHOOK_VERILATOR'}
CPP_INCLUDE = '-I/hook/include'
# What a builder layer (a2cPro) adds; the test plays that layer from shared.mk.
LAYER_VALUES = {
    'A2C_LAYER_CXX_FLAGS': '-DHOOK_LAYER_CXX',
    'A2C_LAYER_LD_FLAGS': '-lhook_layer_ld',
}
LAYER_HOOK_FILES = {
    'A2C_LAYER_HDL_F_FILES': 'layer.f',
    'A2C_LAYER_VCS_LIB_SV_FILES': 'layerLib.sv',
}
# Placeholder tool settings: a dry run needs the variables, not the tools.
VCS_ARGS = ['USE_VCS=1', 'VCS_HOME=/hook/vcs']
XRUN_ARGS = ['USE_XCELIUM=1', 'XCELIUM_TOOLS=/hook/xcelium', 'XRUN_GCC_VERS=hook']
CXX_HOOK = '-DHOOK_CXX'
# Command-line overrides of hooks the project also sets.
CMDLINE = ['VERILATOR_USER_OPTS=-DHOOK_CMDLINE', 'EXTRA_CXX_FLAGS=-DHOOK_CXX_CMDLINE']
# The last builder option of each verilator command, then the hooks in order.
LINT_ORDER = ['--no-timing', '--lint-only', '-DHOOK_USER', '-DHOOK_VERILATOR', '-DHOOK_LINT']
VL_ORDER = ['--no-timing', '-MMD', '-DHOOK_USER', '-DHOOK_VERILATOR', '-DHOOK_VL']
# Builder C++ flags the VL_DUT=1 build appends late, then the project's hook.
CXX_ORDER = ['-DHOOK_LAYER_CXX', '-DVERILATOR', '-Wno-sign-compare', CXX_HOOK]
LD_FLAG = '-lhook_ld'
LAYER_LD_FLAG = '-lhook_layer_ld'
VERILATOR_HOOKS = {'-DHOOK_USER', '-DHOOK_VERILATOR', '-DHOOK_LINT', '-DHOOK_VL'}
VCS_HOOKS = {'-DHOOK_VLOGAN', '-DHOOK_VCS'}
XRUN_HOOKS = {'-DHOOK_XRUN', '-DHOOK_XLIB', '+hook_r'}


def dryRun(directory, *args):
    result = run(['make', '-C', directory, '--no-print-directory', '-n', *args])
    if result.returncode != 0:
        raise AssertionError(f"make -n {' '.join(args)} failed in {directory}:\n"
                             f"{result.stdout}\n{result.stderr}")
    return result.stdout


def commands(output, tool):
    # Echoed recipe lines whose first word is `tool`, as token lists.
    found = []
    for line in output.splitlines():
        words = line.split()
        if words and os.path.basename(words[0]) == tool:
            found.append(shlex.split(line))
    return found


def checkVerilator(label, cmds, want, notWant):
    failures = []
    if not cmds:
        return [f"{label}: no verilator command"]
    for tokens in cmds:
        missing = want - set(tokens)
        leaked = notWant & set(tokens)
        if missing:
            failures.append(f"{label}: verilator lacks {sorted(missing)}")
        if leaked:
            failures.append(f"{label}: verilator carries {sorted(leaked)}")
    return failures


def checkOrder(label, cmds, order):
    # Every command carries each of `order` once, in that sequence.
    if not cmds:
        return [f"{label}: no command"]
    failures = []
    for tokens in cmds:
        found = [tokens.index(t) if tokens.count(t) == 1 else None for t in order]
        if None in found or found != sorted(found):
            failures.append(f"{label}: expected {order} once each in this order, got "
                            f"{[t for t in tokens if t in order]}")
    return failures


def segments(output, tool):
    # Shell commands, split at && || ; and line continuations, whose program
    # (after any VAR= prefixes) is `tool`, as token lists. A line naming `tool`
    # that does not tokenize fails the test instead of being skipped.
    found = []
    for line in output.replace('\\\n', ' ').splitlines():
        if not re.search(rf'(^|[\s/]){re.escape(tool)}(\s|$)', line):
            continue
        lexer = shlex.shlex(line, posix=True, punctuation_chars=';&|')
        lexer.whitespace_split = True
        try:
            tokens = list(lexer)
        except ValueError as error:
            raise AssertionError(f"cannot tokenize a line naming {tool}: {error}\n{line}")
        segment = []
        for token in tokens + [';']:
            if token not in ('&&', '||', ';'):
                segment.append(token)
                continue
            while segment and re.fullmatch(r'\w+=\S*', segment[0]):
                segment = segment[1:]
            if segment and os.path.basename(segment[0]) == tool:
                found.append(segment)
            segment = []
    return found


def checkTokens(label, cmds, want, notWant):
    if not cmds:
        return [f"{label}: no command"]
    failures = []
    for tokens in cmds:
        missing = set(want) - set(tokens)
        leaked = set(notWant) & set(tokens)
        if missing:
            failures.append(f"{label}: lacks {sorted(missing)}")
        if leaked:
            failures.append(f"{label}: carries {sorted(leaked)}")
    return failures


def checkFileLists(label, cmds, lists):
    # Each .f list hook reaches the command as `-F <list>`.
    failures = []
    for tokens in cmds:
        for path in lists:
            if path in tokens and tokens[tokens.index(path) - 1] != '-F':
                failures.append(f"{label}: {path} is not preceded by -F")
    return failures


def checkStamp(label, path, values):
    # The stamp file a make parse wrote holds every value, each as one word or
    # inside one quoted argument.
    if not os.path.isfile(path):
        return [f"{label}: no stamp {path}"]
    with open(path) as f:
        words = shlex.split(f.read())
    return [f"{label}: stamp {path} lacks {value}" for value in values
            if value not in words and not any(value in w.split() for w in words)]


def checkPrereqs(label, database, target, prereqs):
    # `target`'s rule in a make -p database names every prerequisite. The
    # database also prints target-specific variables as `target: NAME := value`.
    rules = [line for line in database.splitlines() if line.startswith(f'{target}:')
             and not re.match(r'\s*[\w.]+\s*[:+?]?=', line[len(target) + 1:])]
    if len(rules) != 1:
        return [f"{label}: expected one rule for {target}, found {len(rules)}"]
    names = rules[0].split()
    return [f"{label}: {target} does not depend on {p}" for p in prereqs if p not in names]


def single(label, pattern):
    paths = glob.glob(pattern)
    if len(paths) != 1:
        raise AssertionError(f"{label}: expected one match for {pattern}, found {paths}")
    return paths[0]


def cmdlineOrder(order):
    return ['-DHOOK_CMDLINE' if t == '-DHOOK_USER' else '-DHOOK_CXX_CMDLINE' if t == CXX_HOOK else t
            for t in order]


def cxxCommands(output, binary):
    # Every compile, precompile and module-object command, not the link.
    return [c for c in commands(output, 'clang++') if c[c.index('-o') + 1] != binary]


def main():
    # The C++ checks expect the default clang++ toolchain.
    os.environ.pop('USE_GCC', None)
    work = copy_simple_ip()
    try:
        hookSrc = os.path.join(work, 'hookSrc', 'hook.cpp')
        os.makedirs(os.path.dirname(hookSrc))
        open(hookSrc, 'w').close()
        hookFiles = {name: os.path.join(work, 'hookSrc', leaf)
                     for name, leaf in {**HOOK_FILES, **LAYER_HOOK_FILES}.items()}
        for path in hookFiles.values():
            open(path, 'w').close()
        shared = os.path.join(work, 'include', 'make', 'shared.mk')
        with open(shared, 'a') as f:
            f.write(''.join(f'{name} += {value}\n' for name, value in HOOK_VALUES.items()))
            f.write(''.join(f'{name} += {path}\n' for name, path in hookFiles.items()))
            f.write(f'EXTRA_CPP_SRC += {hookSrc}\nEXTRA_CPP_INCLUDES += {CPP_INCLUDE}\n'
                    f'EXTRA_LD_FLAGS += {LD_FLAG}\nEXTRA_CXX_FLAGS += {CXX_HOOK}\n')
            f.write(''.join(f'{name} += {value}\n' for name, value in LAYER_VALUES.items()))
        rundir = os.path.join(work, 'rundir')
        vlBuildDir = os.path.join(rundir, 'build', 'vl')
        hookObj = os.path.join(vlBuildDir, 'obj_dir', 'hook', 'hook.o')
        failures = []

        # The reused sub-projects build from their own shared.mk, without the hooks.
        rootDb = os.path.join(work, 'simple_ip.db')

        def genCalls(output):
            return [c for c in commands(output, 'arch2code.py') if c[c.index('--db') + 1] == rootDb]

        dbOutput = make(work, 'db')
        os.remove(os.path.join(rundir, 'Makefile'))
        newmoduleOutput = make(work, 'newmodule')
        point_repo_root(work)
        for target, output in (('db', dbOutput), ('gen', dryRun(work, 'gen')),
                               ('newmodule', newmoduleOutput)):
            calls = genCalls(output)
            lacking = [' '.join(c) for c in calls if '--debug' not in c]
            if not calls or lacking:
                failures.append(f"{target}: arch2code.py lacks EXTRA_GEN_OPTS: {lacking or 'no call'}")
        for flow, args in (('USE_VCS=1', VCS_ARGS), ('USE_XCELIUM=1', XRUN_ARGS)):
            boundary = [c for c in genCalls(dryRun(work, 'gen', *args)) if '--vlBoundary' in c]
            lacking = [' '.join(c) for c in boundary if '--debug' not in c]
            if not boundary or lacking:
                failures.append(f"gen {flow}: arch2code.py --vlBoundary lacks EXTRA_GEN_OPTS: "
                                f"{lacking or 'no call'}")

        a2cF = os.path.join(run(['git', '-C', work, 'rev-parse', '--show-toplevel']).stdout.strip(),
                            'common', 'systemVerilog', 'a2c.f')
        rtlF = os.path.join(work, 'rtl', 'rtl.f')
        layerF, vipSv, vipF = (hookFiles[n] for n in
                               ('A2C_LAYER_HDL_F_FILES', 'EXTRA_HDL_FILES', 'EXTRA_HDL_F_FILES'))
        hdl = [layerF, vipSv, vipF, '+incdir+/hook/inc', '+define+HOOK_DEF']
        lists = [layerF, vipF]
        # The HDL hooks sit between the builder's a2c.f and the project's rtl.f.
        hdlOrder = [a2cF, *hdl, rtlF]

        def isRuntime(tokens):
            return '--top' in tokens and tokens[tokens.index('--top') + 1] == 'vl_dummy'

        lint = commands(dryRun(os.path.join(work, 'rtl'), 'lint'), 'verilator')
        failures += checkVerilator('lint', lint, BOTH | LINT_ONLY, VL_ONLY | {'-DHOOK_CFLAG'})
        failures += checkOrder('lint', lint, LINT_ORDER + hdlOrder)
        failures += checkFileLists('lint', lint, lists)
        cmdlineLint = commands(dryRun(os.path.join(work, 'rtl'), 'lint', *CMDLINE), 'verilator')
        failures += checkOrder('lint, command-line override', cmdlineLint,
                               cmdlineOrder(LINT_ORDER) + hdlOrder)

        vl = dryRun(rundir, 'all', 'VL_DUT=1')
        vlStamp = os.path.join(vlBuildDir, 'verilate_opts')
        failures += checkStamp('verilate', vlStamp,
                               sorted(VERILATOR_HOOKS - LINT_ONLY) + ['-DHOOK_CFLAG'] + hdl)
        verilates = commands(vl, 'verilator')
        runtime = [t for t in verilates if isRuntime(t)]
        perTop = [t for t in verilates if not isRuntime(t)]
        failures += checkVerilator('model wrapping', verilates, BOTH | VL_ONLY, LINT_ONLY)
        failures += checkOrder('model wrapping', perTop, VL_ORDER + hdlOrder)
        failures += checkFileLists('model wrapping', perTop, lists)
        failures += checkOrder('Verilator runtime', runtime, VL_ORDER)
        failures += checkTokens('Verilator runtime', runtime, [], hdl + [a2cF, rtlF])
        binary = os.path.join(rundir, 'build', 'run')
        failures += checkOrder('C++ build', cxxCommands(vl, binary), CXX_ORDER)
        cmdlineVl = dryRun(rundir, 'all', 'VL_DUT=1', *CMDLINE)
        failures += checkOrder('model wrapping, command-line override',
                               [t for t in commands(cmdlineVl, 'verilator') if not isRuntime(t)],
                               cmdlineOrder(VL_ORDER) + hdlOrder)
        failures += checkStamp('verilate, command-line override', vlStamp, ['-DHOOK_CMDLINE'])
        failures += checkOrder('C++ build, command-line override',
                               cxxCommands(cmdlineVl, binary), cmdlineOrder(CXX_ORDER))
        for tokens in verilates:
            cflags = tokens[tokens.index('-CFLAGS') + 1]
            if not cflags.startswith('-std=') or not cflags.endswith(' -DHOOK_CFLAG'):
                failures.append(f"-CFLAGS argument does not end in EXTRA_VL_CFLAGS: {cflags!r}")
        compiles = [c for c in commands(vl, 'clang++') if '-c' in c and c[c.index('-c') + 1] == hookSrc]
        if len(compiles) != 1 or CPP_INCLUDE not in compiles[0]:
            failures.append(f"scaffolded rundir Makefile: EXTRA_CPP_SRC/EXTRA_CPP_INCLUDES "
                            f"from shared.mk do not reach the compile: {compiles}")
        links = [c for c in commands(vl, 'clang++') if '-o' in c and c[c.index('-o') + 1] == binary]
        if len(links) != 1 or LD_FLAG not in links[0]:
            failures.append(f"scaffolded rundir Makefile: EXTRA_LD_FLAGS from shared.mk "
                            f"does not reach the link: {links}")
        if f'echo "ADDMOD {hookObj}"' not in vl:
            failures.append(f"archive script does not ADDMOD {hookObj}")

        # The ordering rule and the verilate prerequisites, read from the
        # sub-make's own database.
        os.makedirs(vlBuildDir, exist_ok=True)
        database = run(['make', '-C', vlBuildDir, '-pq', '-f',
                        os.path.join(work, '..', '..', 'include', 'make', 'a2c-vl-build-entry.mk'),
                        'vlwrap', f'REPO_ROOT={work}']).stdout
        rules = [line for line in database.splitlines() if line.startswith(f'{hookObj}:')]
        tops = [t for t in verilates if '--Mdir' in t]
        mdirs = [t[t.index('--Mdir') + 1] for t in tops]
        if len(rules) != 1:
            failures.append(f"expected one rule for {hookObj}, found {rules}")
        else:
            missing = [m for m in mdirs if m not in rules[0]]
            if missing:
                failures.append(f"{hookObj} is not ordered after {missing}: {rules[0]}")
        for mdir in mdirs:
            if mdir == 'obj_dir/vl_dummy':
                continue
            top = os.path.basename(mdir)
            failures += checkPrereqs('verilate', database, f'{mdir}/V{top}__ALL.a',
                                     [layerF, vipSv, vipF, vlStamp])

        layerLib, lib = hookFiles['A2C_LAYER_VCS_LIB_SV_FILES'], hookFiles['EXTRA_VCS_LIB_SV_FILES']
        vcs = dryRun(rundir, 'all', *VCS_ARGS)
        vlogans = segments(vcs, 'vlogan')
        analysis = [t for t in vlogans if '-sc_model' not in t]
        shells = [t for t in vlogans if '-sc_model' in t]
        failures += checkOrder('vlogan RTL analysis', analysis,
                               ['-timescale=1ns/1ps', '-DHOOK_VLOGAN', *hdlOrder, layerLib, lib])
        failures += checkFileLists('vlogan RTL analysis', analysis, lists)
        failures += checkTokens('vlogan RTL analysis', analysis, [],
                                VERILATOR_HOOKS | XRUN_HOOKS | {'-DHOOK_VCS'})
        failures += checkOrder('vlogan -sc_model', shells, ['-timescale=1ns/1ps', '-DHOOK_VLOGAN'])
        failures += checkTokens('vlogan -sc_model', shells, [],
                                set(hdl) | XRUN_HOOKS | {'-DHOOK_VCS'})
        vcsLinks = segments(vcs, 'vcs')
        failures += checkOrder('vcs link', vcsLinks,
                               ['initial_driver_checks', '-DHOOK_VCS', LAYER_LD_FLAG, LD_FLAG])
        failures += checkTokens('vcs link', vcsLinks, [],
                                set(hdl) | VERILATOR_HOOKS | XRUN_HOOKS | {'-DHOOK_VLOGAN'})
        vcsStampDir = os.path.dirname(single('vcs', os.path.join(rundir, 'build', '*.build',
                                                                  'vcs', 'vlogan_opts')))
        failures += checkStamp('vlogan', os.path.join(vcsStampDir, 'vlogan_opts'),
                               ['-DHOOK_VLOGAN', *hdl, layerLib, lib])
        failures += checkStamp('vcs link', os.path.join(vcsStampDir, 'run_simple_ip_verif.elab_args'),
                               ['-DHOOK_VCS', LAYER_LD_FLAG, LD_FLAG])
        rtlStamp = os.path.join(vcsStampDir, 'rtl.vlogan')
        vcsDatabase = run(['make', '-C', rundir, '-pq', *VCS_ARGS, rtlStamp]).stdout
        failures += checkPrereqs('vlogan', vcsDatabase, rtlStamp, [layerF, vipSv, vipF, layerLib, lib])

        xcelium = dryRun(rundir, 'all', *XRUN_ARGS)
        snapshots = [t for t in segments(xcelium, 'xrun') if '-makelib' in t]
        failures += checkOrder('xrun snapshot', snapshots,
                               ['-gcc_vers', '-DHOOK_XRUN', '-makelib', a2cF, *hdl, '-DHOOK_XLIB',
                                rtlF, '-endlib', f'-Wld,{LAYER_LD_FLAG}', f'-Wld,{LD_FLAG}'])
        failures += checkFileLists('xrun snapshot', snapshots, lists)
        failures += checkTokens('xrun snapshot', snapshots, [],
                                VERILATOR_HOOKS | VCS_HOOKS | {'+hook_r'})
        # The run script carries the xrun -R command inside one quoted argument.
        simulations = [shlex.split(c) for c in re.findall(r"exec (\S*xrun -R [^']*)'", xcelium)]
        failures += checkOrder('xrun -R', simulations, ['-nolog', '+hook_r'])
        failures += checkTokens('xrun -R', simulations, [],
                                set(hdl) | {'-DHOOK_XRUN', '-DHOOK_XLIB'})
        xrunStampDir = os.path.dirname(single('xrun', os.path.join(
            rundir, 'build_xrun', '*.build', 'xrun', '*.d', 'opts')))
        failures += checkStamp('xrun snapshot', os.path.join(xrunStampDir, 'opts'),
                               ['-DHOOK_XRUN', '-DHOOK_XLIB', *hdl,
                                f'-Wld,{LAYER_LD_FLAG}', f'-Wld,{LD_FLAG}'])
        failures += checkStamp('xrun -R', os.path.join(xrunStampDir, 'r_opts'), ['+hook_r'])
        snapshot = os.path.join(xrunStampDir, 'snapshot')
        xrunDatabase = run(['make', '-C', rundir, '-pq', *XRUN_ARGS, snapshot]).stdout
        failures += checkPrereqs('xrun', xrunDatabase, snapshot, [layerF, vipSv, vipF])

        hooks = run(['make', '-C', rundir, '--no-print-directory', 'help-hooks']).stdout
        shownValues = {**HOOK_VALUES, **{name: hookFiles[name] for name in HOOK_FILES}}
        for name, value in shownValues.items():
            shown = hookObj if name == 'EXTRA_VL_LIB_OBJS' else value
            lines = [line for line in hooks.splitlines() if line.startswith(f'{name} ')]
            if len(lines) != 1 or not lines[0].endswith(f': {shown}'):
                failures.append(f"help-hooks does not show {name} = {shown}: {lines}")
        # Every EXTRA_* variable the builder makefiles read is a user hook.
        read = set()
        for path in glob.glob(os.path.join(os.path.dirname(a2cF), '..', '..', 'include', 'make', '*.mk')):
            with open(path) as f:
                read |= set(re.findall(r'\$\((EXTRA_\w+)', f.read()))
        listed = {line.split()[0] for line in hooks.splitlines() if line.startswith('EXTRA_')}
        failures += [f"help-hooks does not list {name}, which include/make reads"
                     for name in sorted(read - listed)]

        if failures:
            for failure in failures:
                print(f"FAIL: {failure}")
            print("SOME TESTS FAILED")
            return 1
        print(f"PASS: {len(shownValues)} hooks set in shared.mk reach only their own "
              f"commands ({len(verilates)} verilates, 1 lint, {len(vlogans)} vlogan, "
              f"{len(vcsLinks)} vcs, {len(snapshots)} xrun, {len(simulations)} xrun -R); "
              f"help-hooks lists all {len(read)} EXTRA_* variables include/make reads")
        print("ALL TESTS PASSED")
        return 0
    finally:
        remove_tree(work)


if __name__ == '__main__':
    sys.exit(main())
