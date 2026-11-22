#!/usr/bin/env python3
"""USE_QUESTA=1 builds the Questa flow of a2c-questa.mk and nothing else.

Dry runs in a private copy of examples/simple_ip, with a placeholder
QUESTA_HOME, so they need no Questa install. Checks:
- USE_VCS, USE_XCELIUM and USE_QUESTA are exclusive, in every pair;
- USE_QUESTA=1 without QUESTA_HOME stops with "QUESTA_HOME is not set";
- without BOOST_LIBS and LD_BOOST it stops with "LD_BOOST is not set", and
  with LD_BOOST alone sccom -link takes the default Boost link inputs;
- every C++ compile carries -DQUESTA -DMTI_SYSTEMC -DDONT_USE_MTI_EXIT -fPIC,
  and -DQUESTA_DUT under VL_DUT only, never -DVERILATOR or the Xcelium
  defines; it reads Questa's SystemC, with the builder's systemc.h shim
  directory ahead of Questa's include directory, and maps each sysc/<dir>/
  that holds a copy of a top-level Questa header to the top for __FILE__;
- there is no native link and no verilator command, and the build tree is
  build_questa;
- gen writes the boundary files (--vlBoundary);
- vlog compiles a2c.f and the project's rtl.f into a2c_dut; sccom compiles the
  sc_main stub and links every object, each once, with the Boost link inputs
  into a2c_sc;
- the parse-time records of the vlog, sccom -link, vopt and vsim arguments do
  not change when a hook holds only blanks;
- QUESTA_PTRARRAY_COPY=1 compiles against a copy of Questa's include
  directory whose ptrarray.h defines m_default_init_size in the class, maps
  the copy's paths for __FILE__, and stops on an unexpected ptrarray.h; unset,
  it compiles against the install;
- vopt elaborates a2c_sc.sc_main into the topology's own library with the
  testbench arguments as -sc_arg, the topology's dots spelled __;
- the run script exports SALT_LICENSE_SERVER, passes each argument as -sc_arg
  and runs the topology's design with vsim, whose -do script quits with code 1
  on an error or break before run -all, searching the libraries vopt did;
- the run script, written by the dry run's own command around a stub vsim,
  passes the output, the arguments and a non-zero exit code through, exits 0
  on a clean log, and exits 1 when vsim exits 0 but printed a "# ** Error",
  "# ** Error (suppressible)", "# ** Fatal" or "# ** Failure" line (the
  negative controls);
- VL_DUT= builds without -DQUESTA_DUT, vlog and -L a2c_dut, and
  questa_snapshots refuses it;
- questa_snapshots builds run_model, then one sub-make per topology.
"""

import os
import re
import shlex
import shutil
import subprocess
import sys
import time

from test_file_prefix import copy_simple_ip, make, run
from _tmp_helpers import remove_tree

QUESTA_HOME = '/hook/questa'
LICENCE = '1717@hook-a:1717@hook-b'
QUESTA_ARGS = ['USE_QUESTA=1', f'QUESTA_HOME={QUESTA_HOME}', 'BOOST_LIBS=-lboost_program_options -L/hook/boost']
DEFINES = ['-DQUESTA', '-DMTI_SYSTEMC', '-DDONT_USE_MTI_EXIT', '-fPIC']
FOREIGN = ['-DVERILATOR', '-DXCELIUM', '-DXCELIUM_DUT', '-DVCS', '-DVCS_DUT']


def env():
    e = os.environ.copy()
    e['NO_COLOR'] = '1'
    e['SALT_LICENSE_SERVER'] = LICENCE
    e['BOOST_INCLUDE'] = '/hook/boost/include'
    for name in ('USE_GCC', 'USE_VCS', 'USE_XCELIUM', 'USE_QUESTA', 'QUESTA_HOME', 'VL_DUT',
                 'LD_BOOST', 'BOOST_LIBS'):
        e.pop(name, None)
    return e


def dryRun(directory, *args):
    return subprocess.run(['make', '-C', directory, '--no-print-directory', '-n', *args],
                          capture_output=True, text=True, timeout=3600, env=env())


def tool(output, name):
    found = []
    for line in output.replace('\\\n', ' ').splitlines():
        for part in re.split(r'\s*(?:&&|;)\s*', line):
            words = part.split()
            if words and os.path.basename(words[0]) == name:
                found.append(shlex.split(part))
    return found


def compiles(output):
    return [c for c in tool(output, 'clang++') if '-c' in c or '--precompile' in c]


STUB_VSIM = """#!/bin/sh
for a; do echo "arg[$a]"; done
case "$A2C_STUB" in
  pass) echo '# ** Note: (vsim-3812) Design is being optimized...'; echo '# Errors: 0, Warnings: 1'; exit 0 ;;
  error) echo '# ** Error: (vsim-8315) negative control: $error from the RTL'; exit 0 ;;
  suppressible) echo '# ** Error (suppressible): (vsim-12003) negative control'; exit 0 ;;
  fatal) echo '# ** Fatal: negative control: $fatal'; exit 0 ;;
  failure) echo '# ** Failure: negative control: assertion of severity failure'; exit 0 ;;
  rc3) echo '# ** Note: quit -code 3'; exit 3 ;;
esac
"""


# A stand-in for Questa's ptrarray.h with the lines the copy edits: the
# pointer specialization's static member, declared in the class and defined
# out of class.
FAKE_PTRARRAY = """template <typename T>
class ptrarray
{
  static  int m_default_init_size;
};
template <typename T>
class ptrarray<T*>
{
  static      int m_default_init_size;   // default initial size
};
template <typename T>
int ptrarray<T*>::m_default_init_size = 16;
"""


def checkPtrarrayCopy(rundir, work):
    """QUESTA_PTRARRAY_COPY=1 compiles against a copy of a stand-in Questa
    include directory whose ptrarray.h defines the member in the class, maps the
    copy's paths to Questa's for __FILE__, and stops on an unexpected
    ptrarray.h; QUESTA_PTRARRAY_COPY unset compiles against the install."""
    problems = []
    fake = os.path.join(work, 'fakeQuestaCopy')
    inc = os.path.join(fake, 'include', 'systemc')
    os.makedirs(os.path.join(inc, 'sysc', 'kernel'), exist_ok=True)
    for rel, text in (('ptrarray.h', FAKE_PTRARRAY), ('sc_event.h', ''), ('sysc/kernel/sc_event.h', '')):
        with open(os.path.join(inc, rel), 'w') as f:
            f.write(text)
    args = [a for a in QUESTA_ARGS if not a.startswith('QUESTA_HOME=')] + [f'QUESTA_HOME={fake}']
    copy = os.path.join(rundir, 'build_questa', 'questa_systemc')
    off = compiles(dryRun(rundir, 'all', *args).stdout)
    if not off or any(f'-isystem{copy}' in c for c in off) or os.path.exists(copy):
        problems.append("QUESTA_PTRARRAY_COPY unset still uses or writes the copy")
    on = dryRun(rundir, 'all', *args, 'QUESTA_PTRARRAY_COPY=1')
    cxx = compiles(on.stdout)
    sources = [c for c in cxx if '--precompile' in c or c[c.index('-c') + 1].endswith('.cpp')]
    if on.returncode != 0 or not sources or any(f'-isystem{copy}' not in c or f'-isystem{inc}' in c for c in sources):
        problems.append(f"QUESTA_PTRARRAY_COPY=1 does not compile against {copy} (exit {on.returncode}):\n{on.stderr}")
    maps = {w for c in cxx for w in c if w.startswith('-fmacro-prefix-map=')}
    for m in (f'-fmacro-prefix-map={copy}/={inc}/', f'-fmacro-prefix-map={copy}/sysc/kernel/={inc}/'):
        if m not in maps:
            problems.append(f"QUESTA_PTRARRAY_COPY=1 lacks {m}: {sorted(maps)}")
    hdr = os.path.join(copy, 'ptrarray.h')
    text = open(hdr).read() if os.path.isfile(hdr) else ''
    if 'static constexpr int m_default_init_size = 16;' not in text or 'ptrarray<T*>::m_default_init_size' in text \
            or text.count('m_default_init_size') != 2 or os.path.islink(hdr) \
            or os.path.realpath(os.path.join(copy, 'sc_event.h')) != os.path.join(inc, 'sc_event.h'):
        problems.append(f"the copy's ptrarray.h is not the stand-in with the member in the class:\n{text}")
    with open(os.path.join(inc, 'ptrarray.h'), 'w') as f:
        f.write(FAKE_PTRARRAY.replace('= 16;', '= 32;'))
    shutil.rmtree(copy)
    bad = dryRun(rundir, 'all', *args, 'QUESTA_PTRARRAY_COPY=1')
    if bad.returncode == 0 or 'could not be written' not in bad.stderr or os.path.exists(copy):
        problems.append(f"an unexpected ptrarray.h does not stop QUESTA_PTRARRAY_COPY=1:\n{bad.stderr}")
    return problems


def checkRunScript(rundir, work, binary):
    """Writes the run script with the dry run's own printf command, vsim being
    a stub, and runs it once per stub behaviour."""
    problems = []
    stub = os.path.join(work, 'stub_vsim')
    with open(stub, 'w') as f:
        f.write(STUB_VSIM)
    os.chmod(stub, 0o755)
    out = dryRun(rundir, 'all', *QUESTA_ARGS, f'VSIM={stub}').stdout.replace('\\\n', ' ')
    writers = [line for line in out.splitlines()
               if line.lstrip().startswith("printf '%s\\n' '#!/bin/sh'") and f'> {binary}' in line]
    if len(writers) != 1:
        return [f"no single run-script printf in the dry run: {writers}"]
    script = os.path.join(work, 'run_script_under_test')
    subprocess.run(['sh', '-c', writers[0].replace(f'> {binary}', f'> {script}')], check=True)
    os.chmod(script, 0o755)
    want = {'pass': 0, 'rc3': 3, 'error': 1, 'suppressible': 1, 'fatal': 1, 'failure': 1}
    for mode, rc in want.items():
        e = env()
        e['A2C_STUB'] = mode
        r = subprocess.run([script, 'simple_ip', 'a b'], capture_output=True, text=True, env=e, timeout=60)
        if r.returncode != rc:
            problems.append(f"run script with a vsim that reports {mode!r} exits {r.returncode}, "
                            f"not {rc}:\n{r.stdout}{r.stderr}")
        if 'arg[a b]' not in r.stdout or 'arg[-sc_arg]' not in r.stdout or 'a2c_vsim_rc=' in r.stdout:
            problems.append(f"run script ({mode}) does not pass vsim's output and arguments "
                            f"through as given:\n{r.stdout}")
    return problems


def main():
    work = copy_simple_ip()
    try:
        rundir = os.path.join(work, 'rundir')
        a2c = run(['git', '-C', work, 'rev-parse', '--show-toplevel']).stdout.strip()
        shim = f'-I{a2c}/common/systemc/questa'
        failures = []
        make(work, 'db')

        for pair in (('USE_VCS=1', 'USE_QUESTA=1'), ('USE_XCELIUM=1', 'USE_QUESTA=1'),
                     ('USE_VCS=1', 'USE_XCELIUM=1')):
            result = dryRun(rundir, *pair, 'VCS_HOME=/hook', 'XCELIUM_TOOLS=/hook', 'XRUN_GCC_VERS=x',
                            f'QUESTA_HOME={QUESTA_HOME}', 'BOOST_LIBS=-lx', 'all')
            if result.returncode == 0 or 'USE_VCS, USE_XCELIUM and USE_QUESTA are exclusive' not in result.stderr:
                failures.append(f"{' '.join(pair)}: make did not stop on the exclusive switches "
                                f"(exit {result.returncode}):\n{result.stderr}")

        result = dryRun(rundir, 'USE_QUESTA=1', 'BOOST_LIBS=-lx', 'all')
        if result.returncode == 0 or 'QUESTA_HOME is not set' not in result.stderr:
            failures.append(f"no QUESTA_HOME: make did not stop (exit {result.returncode}):\n{result.stderr}")

        # sccom -link reads BOOST_LIBS, so USE_QUESTA keeps the LD_BOOST
        # check, as test_xcelium_boost_libs.py checks for USE_XCELIUM.
        noBoost = [a for a in QUESTA_ARGS if not a.startswith('BOOST_LIBS=')]
        result = dryRun(rundir, *noBoost, 'all')
        if result.returncode == 0 or 'LD_BOOST is not set' not in result.stderr:
            failures.append(f"neither BOOST_LIBS nor LD_BOOST: make did not stop on LD_BOOST "
                            f"(exit {result.returncode}):\n{result.stderr}")
        result = dryRun(rundir, *noBoost, 'LD_BOOST=/hook/ldboost', 'BOOST_LIBS=', 'all')
        links = [c for c in tool(result.stdout, 'sccom') if '-link' in c]
        if result.returncode != 0 or len(links) != 1 \
                or '-lboost_program_options -L/hook/ldboost' not in ' '.join(links[0]):
            failures.append(f"LD_BOOST set: sccom -link lacks the default Boost link "
                            f"(exit {result.returncode}):\n{links}\n{result.stderr}")

        gen = dryRun(work, 'gen', *QUESTA_ARGS)
        if gen.returncode != 0 or not [c for c in tool(gen.stdout, 'arch2code.py') if '--vlBoundary' in c]:
            failures.append(f"gen under USE_QUESTA does not write the boundary files:\n{gen.stdout}{gen.stderr}")

        result = dryRun(rundir, 'all', *QUESTA_ARGS)
        if result.returncode != 0:
            raise AssertionError(f"make -n all USE_QUESTA=1 failed:\n{result.stdout}\n{result.stderr}")
        out = result.stdout
        cxx = compiles(out)

        # The parse-time records hold each step's arguments without stray
        # blanks: a blank-only hook value leaves every record untouched, so
        # it reruns no step.
        records = [os.path.join(d, f) for d, _, files in os.walk(os.path.join(rundir, 'build_questa'))
                   for f in files if f in ('vlog_opts', 'sclink_opts', 'opts', 'r_opts')]
        before = {r: (os.stat(r).st_mtime_ns, open(r).read()) for r in records}
        time.sleep(1.1)
        blank = dryRun(rundir, 'all', *QUESTA_ARGS, 'EXTRA_LD_FLAGS= ', 'EXTRA_QUESTA_VLOG_OPTS= ',
                       'EXTRA_QUESTA_VOPT_OPTS= ', 'EXTRA_QUESTA_VSIM_OPTS= ')
        after = {r: (os.stat(r).st_mtime_ns, open(r).read()) for r in records}
        if len(records) != 4 or blank.returncode != 0 or before != after:
            failures.append(f"blank hook values rewrite the Questa records {sorted(records)}: "
                            f"{[r for r in records if before[r] != after.get(r)]}")
        if not cxx:
            failures.append("no C++ compile")
        for c in cxx:
            missing = [d for d in DEFINES + ['-DQUESTA_DUT'] if d not in c]
            leaked = [d for d in FOREIGN if d in c]
            if missing or leaked:
                failures.append(f"compile lacks {missing} or carries {leaked}: {' '.join(c)[:300]}")
                break
            # A module object compiles from its PCM, without include paths.
            if '--precompile' not in c and not c[c.index('-c') + 1].endswith('.cpp'):
                continue
            if f'-isystem{QUESTA_HOME}/include/systemc' not in c:
                failures.append(f"compile does not read Questa's SystemC: {' '.join(c)[:300]}")
                break
            if shim not in c or f'-I{QUESTA_HOME}/include' not in c \
                    or c.index(shim) > c.index(f'-I{QUESTA_HOME}/include'):
                failures.append(f"compile does not put {shim} ahead of -I{QUESTA_HOME}/include")
                break
        binary = os.path.join(rundir, 'build_questa', 'run_simple_ip_verif')
        links = [c for c in tool(out, 'clang++') if '-o' in c and '-c' not in c and '--precompile' not in c]
        if links or tool(out, 'verilator'):
            failures.append(f"USE_QUESTA runs a native link or verilator: {links}")

        vlogs = tool(out, 'vlog')
        a2cF = os.path.join(a2c, 'common', 'systemVerilog', 'a2c.f')
        rtlF = os.path.join(work, 'rtl', 'rtl.f')
        if len(vlogs) != 1 or vlogs[0][vlogs[0].index('-work') + 1] != 'a2c_dut' \
                or a2cF not in vlogs[0] or rtlF not in vlogs[0] \
                or vlogs[0].index(a2cF) > vlogs[0].index(rtlF):
            failures.append(f"vlog does not compile a2c.f then rtl.f into a2c_dut: {vlogs}")

        sccoms = tool(out, 'sccom')
        stub = os.path.join(a2c, 'common', 'systemc', 'questa', 'questa_sc_main.cpp')
        if len(sccoms) != 2 or stub not in sccoms[0] or '-link' not in sccoms[1] \
                or '-lboost_program_options' not in sccoms[1] or '-L/hook/boost' not in sccoms[1] \
                or not any(w.endswith('.o') for w in sccoms[1]) \
                or any(c[c.index('-work') + 1] != 'a2c_sc' for c in sccoms):
            failures.append(f"sccom does not compile the stub and link the objects into a2c_sc: {sccoms}")

        vopts = tool(out, 'vopt')
        want = ['-work', 'a2c_opt_simple_ip_verif', '-L', 'a2c_dut', '-L', 'a2c_sc', 'a2c_sc.sc_main',
                '-sc_arg', 'simple_ip', '-sc_arg', '--vlInst', '-o', 'opt_simple_ip_verif']
        if len(vopts) != 1 or [w for w in want if w not in vopts[0]]:
            failures.append(f"vopt lacks {want}: {vopts}")

        script = [line for line in out.splitlines() if '-lib a2c_opt' in line and 'vsim' in line]
        scriptText = '\n'.join(script)
        for piece in ('-lib a2c_opt_simple_ip_verif -L a2c_dut -L a2c_sc opt_simple_ip_verif "$@" -do "onerror {quit -code 1}; onbreak {quit -code 1}; run -all"',
                      '-batch', '-scasyncupdate'):
            if piece not in scriptText:
                failures.append(f"run script lacks {piece!r}: {script}")
        if f'export SALT_LICENSE_SERVER="{LICENCE}"' not in out or 'set -- "$@" -sc_arg "$a"' not in out:
            failures.append("run script does not export SALT_LICENSE_SERVER or pass -sc_arg")
        if f'> {binary}' not in out:
            failures.append(f"run script is not written to {binary}")

        # The run script itself, written by the dry run's command with a stub
        # vsim: it passes vsim's output and exit code through, keeps an argument
        # with a space whole, and fails a run whose output has an HDL $error,
        # $fatal or assertion failure line although vsim exits 0.
        failures += checkRunScript(rundir, work, binary)

        # A source both in a project source directory and on EXTRA_CPP_SRC is
        # one object on the link, as the native link's $^ lists it.
        twice = os.path.join(work, 'fw', 'src', 'fwSimpleMain.cpp')
        dup = dryRun(rundir, 'all', *QUESTA_ARGS, f'EXTRA_CPP_SRC={twice}')
        objs = [w for c in tool(dup.stdout, 'sccom') if '-link' in c for w in c if w.endswith('.o')]
        mine = [o for o in objs if o.endswith('fwSimpleMain.o')]
        if dup.returncode != 0 or len(mine) != 1 or len(objs) != len(set(objs)):
            failures.append(f"sccom -link does not name each object once: {mine}")

        # A header Questa ships both at the top of include/systemc and under
        # sysc/<dir>/ gets that directory mapped to the top for __FILE__; a
        # directory without such a copy gets no map.
        fake = os.path.join(work, 'fakeQuesta')
        inc = os.path.join(fake, 'include', 'systemc')
        for rel in ('sc_event.h', 'sysc/kernel/sc_event.h', 'sysc/utils/only_here.h'):
            os.makedirs(os.path.dirname(os.path.join(inc, rel)), exist_ok=True)
            open(os.path.join(inc, rel), 'w').close()
        mapped = dryRun(rundir, 'all', *[a for a in QUESTA_ARGS if not a.startswith('QUESTA_HOME=')],
                        f'QUESTA_HOME={fake}')
        maps = {w for c in compiles(mapped.stdout) for w in c if w.startswith('-fmacro-prefix-map=')}
        if maps != {f'-fmacro-prefix-map={inc}/sysc/kernel/={inc}/'}:
            failures.append(f"Questa header maps are {sorted(maps)}")

        failures += checkPtrarrayCopy(rundir, work)

        dotted = dryRun(rundir, 'all', *QUESTA_ARGS, 'VL_INST=a.b')
        if 'opt_a__b_verif' not in dotted.stdout or 'a2c_opt_a__b_verif' not in dotted.stdout:
            failures.append(f"VL_INST=a.b does not spell the dot __: {tool(dotted.stdout, 'vopt')}")

        model = dryRun(rundir, 'all', *QUESTA_ARGS, 'VL_DUT=')
        if model.returncode != 0:
            failures.append(f"VL_DUT= dry run failed:\n{model.stderr}")
        else:
            if any('-DQUESTA_DUT' in c for c in compiles(model.stdout)) or tool(model.stdout, 'vlog') \
                    or any('a2c_dut' in c for c in tool(model.stdout, 'vopt')):
                failures.append("VL_DUT= still compiles the DUT for Questa")
        refuse = dryRun(rundir, 'questa_snapshots', *QUESTA_ARGS, 'VL_DUT=')
        if refuse.returncode == 0 or 'questa_snapshots builds the DUT snapshots' not in refuse.stderr:
            failures.append(f"questa_snapshots with VL_DUT= did not stop:\n{refuse.stderr}")

        snaps = dryRun(rundir, 'questa_snapshots', *QUESTA_ARGS,
                       'DUT_TOPOLOGIES=simple_ip:verif,model:tandem')
        subs = [line for line in snaps.stdout.splitlines() if re.search(r'make\S* .*VL_INST=', line)]
        wanted = ['VL_INST= ', 'VL_INST=simple_ip VL_TYPE=verif VL_TANDEM=0',
                  'VL_INST=simple_ip VL_TYPE=model VL_TANDEM=1']
        if snaps.returncode != 0 or [w for w in wanted if not any(w in s for s in subs)]:
            failures.append(f"questa_snapshots does not make run_model and each topology:\n{subs}\n{snaps.stderr}")

        if failures:
            for failure in failures:
                print(f"FAIL: {failure}")
            print("SOME TESTS FAILED")
            return 1
        print(f"PASS: USE_QUESTA=1 builds the Questa flow ({len(cxx)} compiles, 1 vlog, 2 sccom, "
              f"1 vopt, run script); the switches are exclusive and VL_DUT= builds the model design")
        print("ALL TESTS PASSED")
        return 0
    finally:
        remove_tree(work)


if __name__ == '__main__':
    sys.exit(main())
