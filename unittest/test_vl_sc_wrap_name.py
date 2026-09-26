#!/usr/bin/env python3
"""Renaming the vlScWrap fileMap entry renames the header, not the class.

Works on a private copy of examples/ip_test. With vlScWrap named _sc_wrap in
the ip child's fileMap, ip's wrapper header is ip_sc_wrap.h and still declares
class ip_hdl_sc_wrapper. The VlRegistrars that build the wrapper include the
renamed header and instantiate ip_hdl_sc_wrapper, and the Verilated run passes
for ip on its own and for the composing root.
"""

import os
import re
import shutil
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir
from test_file_prefix import edit, make, remove, run


SOURCE = os.path.join(base_dir, 'examples', 'ip_test')
# Project dirs (relative to the copy) that ip_test's make chain enters.
PROJECTS = ('.', 'ip', 'bridge', 'common')
SC_WRAP_ENTRY = ('        vlScWrap: { name: "_sc_wrap", ext: {hdr: "h"}, cond: {hasVl: true}, '
                 'mode: block, basePath: vl_wrap, langDomain: sc, desc: "SystemC Verilated wrapper" }\n')


def copy_ip_test():
    work = tempfile.mkdtemp(prefix='vl_sc_wrap_', dir=test_dir)
    shutil.copytree(SOURCE, work, dirs_exist_ok=True, ignore=shutil.ignore_patterns(
        'build', '.gen', '*.db', '*.db-*', 'compile_commands.json'))
    # Each Makefile names its project root from the git top level; point it at
    # the copy instead.
    for project in PROJECTS:
        root = os.path.normpath(os.path.join(work, project))
        for relpath in ('Makefile', 'rundir/Makefile', 'include/make/shared.mk'):
            path = os.path.join(root, relpath)
            if not os.path.exists(path):
                continue
            with open(path) as f:
                lines = f.read().splitlines(keepends=True)
            (hit,) = [i for i, line in enumerate(lines) if line.startswith('REPO_ROOT = ')]
            lines[hit] = f'REPO_ROOT = {root}\n'
            with open(path, 'w') as f:
                f.write(''.join(lines))
    return work


def main():
    work = copy_ip_test()
    try:
        ip = os.path.join(work, 'ip')
        edit(os.path.join(ip, 'prj', 'yaml', 'ipProject.yaml'),
             '    fileMap:\n', '    fileMap:\n' + SC_WRAP_ENTRY)
        # The user renames the wrapper header, which holds user code, to its new name.
        os.rename(os.path.join(ip, 'verif', 'ip_hdl_sc_wrapper.h'),
                  os.path.join(ip, 'verif', 'ip_sc_wrap.h'))
        for directory in (ip, work):
            run(['make', '-C', directory, 'clean'])
            make(directory, 'newmodule')
            make(directory, 'gen')
        ok = True
        with open(os.path.join(ip, 'verif', 'ip_sc_wrap.h')) as f:
            if not re.search(r'^class ip_hdl_sc_wrapper\b', f.read(), re.M):
                print("FAIL: ip/verif/ip_sc_wrap.h does not declare class ip_hdl_sc_wrapper")
                ok = False
        registrars = [os.path.join(ip, 'registrar', 'ipVlRegistrar.cpp'),
                      os.path.join(work, 'bridge', 'registrar', 'ipVlRegistrar.cpp'),
                      os.path.join(work, 'top', 'registrar', 'ipVlRegistrar.cpp')]
        for path in registrars:
            with open(path) as f:
                text = f.read()
            if '#include "ip_sc_wrap.h"' not in text or 'make_shared<ip_hdl_sc_wrapper<' not in text:
                print(f"FAIL: {path} does not include ip_sc_wrap.h and build ip_hdl_sc_wrapper")
                ok = False
        for label, rundir in (('standalone ip', os.path.join(ip, 'rundir')),
                              ('composed root', os.path.join(work, 'rundir'))):
            runLog = make(rundir, 'run-vl')
            if 'No error' not in runLog:
                print(f"FAIL: the {label} Verilated run did not finish cleanly:\n{runLog[-3000:]}")
                ok = False
        if not ok:
            print("SOME TESTS FAILED")
            return 1
        print("PASS: with vlScWrap named _sc_wrap, ip_sc_wrap.h declares ip_hdl_sc_wrapper, "
              "the registrars include it and build that class, and the Verilated runs of ip "
              "and the composing root pass")
        print("ALL TESTS PASSED")
        return 0
    finally:
        remove(work)


if __name__ == '__main__':
    sys.exit(main())
