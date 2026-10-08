#!/usr/bin/env python3
"""The verilator sub-build takes its job count from VL_JOBS and the outer jobserver.

Verilator 5 runs `make -j <N>` for --build only when it finds no jobserver in
MAKEFLAGS. Under a parallel outer make it defers to that jobserver, which the
child can reach only if the recipe is marked recursive; otherwise it falls back
to one job.

Drives one verilated-top rule of a2c-vl-wrap.mk from a scratch makefile, with a
stand-in `verilator` on PATH that records its arguments and whether the
jobserver named in MAKEFLAGS is open. Checks:
- with a serial outer make, `-j 4` by default and `-j 8` with VL_JOBS=8;
- with `make -j3`, the verilator process can reach the outer jobserver;
- the configured CXX reaches verilator's sub-make as CXX and LINK, and under
  USE_GCC no compiler override is passed;
- `make -n`, run directly, as a recursive `$(MAKE)` like the VL_DUT build, or
  set by `MAKEFLAGS += -n` in a makefile read before the rules, prints the
  verilate without running it.

The jobserver check relies on make 4.3, which closes the jobserver pipe fds
for a recipe without `+`. Make 4.4 can use a named fifo instead, which the
stand-in only checks for existence, so there the check may pass without `+`.
"""

import os
import re
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir


FAKE_VERILATOR = r'''#!/bin/bash
log="$(dirname "$0")/../verilator.log"
echo "ARGS $*" >> "$log"
# Verilator pastes each -MAKEFLAGS value into the shell command that runs its
# sub-make; record the words that sub-make receives.
prev=
for a in "$@"; do
  [ "$prev" = "-MAKEFLAGS" ] && (eval "set -- $a"; for w in "$@"; do echo "MAKEARG $w" >> "$log"; done)
  prev=$a
done
auth=$(printf '%s' "$MAKEFLAGS" | sed -n 's/.*--jobserver-auth=\([^ ]*\).*/\1/p')
case "$auth" in
  "") echo "JOBSERVER none" >> "$log" ;;
  fifo:*) [ -p "${auth#fifo:}" ] && echo "JOBSERVER open" >> "$log" || echo "JOBSERVER closed" >> "$log" ;;
  *) [ -e "/proc/$$/fd/${auth%%,*}" ] && echo "JOBSERVER open" >> "$log" || echo "JOBSERVER closed" >> "$log" ;;
esac
'''

TOP = 'top'


def runVerilate(work, *args, makefile='vl.mk'):
    # Returns (returncode, recorded ARGS line, recorded JOBSERVER state).
    log = os.path.join(work, 'verilator.log')
    if os.path.exists(log):
        os.remove(log)
    e = dict(os.environ, NO_COLOR='1', PATH=os.path.join(work, 'bin') + os.pathsep + os.environ['PATH'])
    e.pop('MAKEFLAGS', None)
    result = subprocess.run(['make', '-C', work, '--no-print-directory', '-f', makefile, *args,
                             f'obj_dir/{TOP}/V{TOP}__ALL.a'],
                            capture_output=True, text=True, timeout=120, env=e)
    lines = open(log).read().splitlines() if os.path.exists(log) else []
    argsLine = next((l[5:] for l in lines if l.startswith('ARGS ')), '')
    state = next((l.split()[1] for l in lines if l.startswith('JOBSERVER ')), '')
    runVerilate.makeArgs = [l[8:] for l in lines if l.startswith('MAKEARG ')]
    return result, argsLine, state


def jobs(argsLine):
    m = re.search(r'(?:^| )-j (\S+)', argsLine)
    return m.group(1) if m else None


def main():
    failures = []

    def check(ok, message):
        print(f"{'PASS' if ok else 'FAIL'}: {message}")
        if not ok:
            failures.append(message)

    with tempfile.TemporaryDirectory(prefix='make_vl_jobs_') as work:
        os.makedirs(os.path.join(work, 'bin'))
        fake = os.path.join(work, 'bin', 'verilator')
        with open(fake, 'w') as f:
            f.write(FAKE_VERILATOR)
        os.chmod(fake, 0o755)
        with open(os.path.join(work, 'vl.mk'), 'w') as f:
            f.write(f'REPO_ROOT = {work}\n'
                    'PROJECTNAME = vljobs\n'
                    f'A2C_ROOT = {base_dir}\n'
                    f'A2C_VL_TOPS = {TOP}\n'
                    f'A2C_VL_BUILD_DIR = {work}\n'
                    'include $(A2C_ROOT)/include/make/a2c-vl-wrap.mk\n')
        with open(os.path.join(work, 'outer.mk'), 'w') as f:
            f.write(f'obj_dir/{TOP}/V{TOP}__ALL.a:\n\t$(MAKE) -f vl.mk $@\n')
        with open(os.path.join(work, 'dryflag.mk'), 'w') as f:
            f.write('MAKEFLAGS += -n\ninclude vl.mk\n')

        result, argsLine, state = runVerilate(work)
        check(jobs(argsLine) == '4', f"serial make passes -j 4 by default (verilator {argsLine!r})")

        result, argsLine, state = runVerilate(work, 'VL_JOBS=8')
        check(jobs(argsLine) == '8', f"VL_JOBS=8 reaches the verilator command line (verilator {argsLine!r})")

        result, argsLine, state = runVerilate(work, '-j3')
        check(state == 'open',
              f"under make -j3 the verilator recipe can reach the outer jobserver (jobserver {state!r})")
        if not argsLine:
            print(f"make output:\n{result.stdout}\n{result.stderr}")

        result, argsLine, state = runVerilate(work, 'CXX=/x/clang++')
        makeArgs = runVerilate.makeArgs
        check(makeArgs == ['CXX=/x/clang++', 'LINK=/x/clang++'],
              f"CXX=/x/clang++ reaches verilator's sub-make as CXX and LINK (sub-make gets {makeArgs})")

        result, argsLine, state = runVerilate(work, '-n', 'USE_GCC=1')
        check('verilator' in result.stdout and '-MAKEFLAGS' not in result.stdout,
              f"under USE_GCC=1, make -n passes verilator no compiler override:\n{result.stdout.strip()}")

        for makefile in ('vl.mk', 'outer.mk'):
            for flags in (['-n'], ['-n', '-j3']):
                result, argsLine, state = runVerilate(work, *flags, makefile=makefile)
                check(not argsLine and 'verilator' in result.stdout,
                      f"make {' '.join(flags)} -f {makefile} prints the verilate without running it "
                      f"(verilator ran with {argsLine!r})")

        result, argsLine, state = runVerilate(work, makefile='dryflag.mk')
        check(not argsLine and 'verilator' in result.stdout,
              f"MAKEFLAGS += -n before the rules prints the verilate without running it "
              f"(verilator ran with {argsLine!r})")

    if failures:
        print("SOME TESTS FAILED")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == '__main__':
    sys.exit(main())
