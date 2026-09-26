#!/usr/bin/env python3
"""A child project can rename many of its fileMap entries at once.

Works on a private copy of examples/simple_ip. The ip child gives a new name to
each entry in NAME_OVERRIDES. The user renames every existing ip file to its new
name, and migrate relabels the RTL endmodule labels. Then ip and the composing
root generate, every SV module and package is named like its file, every file
either manifest lists exists, no ip file keeps its old name, the root's
firmware includes ip's renamed header, and the root's model and Verilated runs
pass. The renamed SC wrapper header still declares `ip_hdl_sc_wrapper`, and
both projects' VlRegistrars for ip include that header and build that class.
"""

import os
import re
import sys

from test_file_prefix import (PROJECT_FILES, check_sv_names_and_run, copy_simple_ip,
                              currentArtifactRows, edit, make, open_db, remove, run)


# fileMap entry -> the new name ip gives it. Every other field keeps the base
# config/project.yaml value, which the override repeats.
NAME_OVERRIDES = {
    'blockBase':    ('Ports', 'ext: {cppm: "cppm"}, cond: {hasMdl: true, hasTb: true}, mode: block, basePath: base'),
    'blockModule':  ('Mdl', 'ext: {cppm: "cppm"}, cond: {hasMdl: true}, mode: block, basePath: model'),
    'blockRegistrar': ('Reg', 'ext: {cppm: "cppm"}, cond: {hasOwnParams: true}, condAnd: {hasMdl: true}, '
                              'mode: registrar, basePath: registrar, requiresRegistrations: true'),
    'blockVlRegistrar': ('VlReg', 'ext: {src: "cpp"}, cond: {hasVl: true}, mode: registrar, basePath: registrar'),
    'configModule': ('Cfgm', 'ext: {cppm: "cppm"}, condAnd: {hasOwnParams: true}, mode: registrar, '
                             'basePath: registrar, ownerQualified: true'),
    'rtlModule':    ('_rtl', 'ext: {sv: "sv"}, cond: {hasRtl: true}, mode: block, basePath: rtl'),
    'vlSvWrap':     ('_svw', 'ext: {sv: "sv"}, cond: {hasVl: true}, mode: block, basePath: vl_wrap, variant: true'),
    'vlSvWrapBody': ('_svwb', 'ext: {svh: "svh"}, cond: {hasOwnParams: true}, condAnd: {hasVl: true}, '
                              'mode: block, basePath: vl_wrap, variant: false'),
    'vlScWrap':     ('_scw', 'ext: {hdr: "h"}, cond: {hasVl: true}, mode: block, basePath: vl_wrap'),
    'testBench':    ('Tb', 'ext: {cppm: "cppm"}, cond: {hasTb: true}, blockDir: true, mode: block, '
                           'basePath: tb, dutVariant: true'),
    'tbConfig':     ('TbCfg', 'ext: {src: "cpp"}, cond: {hasTb: true}, blockDir: true, mode: block, '
                              'basePath: tb, dutVariant: true'),
    'tbExternal':   ('Ext', 'ext: {cppm: "cppm"}, cond: {hasTb: true}, blockDir: true, mode: block, '
                            'basePath: tb, dutVariant: true'),
    'include':      ('Types', 'ext: {cppm: "cppm"}, cond: {smartInclude: true}, mode: context, basePath: model'),
    'includeFW':    ('Fw', 'ext: {hdr: "h", src: "cpp"}, cond: {smartInclude: true}, mode: context, '
                           'basePath: fwInc'),
    'package':      ('_pkg', 'ext: {sv: "sv"}, cond: {smartInclude: true}, mode: context, basePath: rtl'),
}

MANIFEST_FILE_VARIABLES = ('A2C_CPP_MODULE_FILES', 'A2C_CPP_CONTEXT_MODULE_FILES',
                           'A2C_CPP_CONTEXT_SRC_FILES', 'A2C_SV_FILES',
                           'A2C_SV_DEP_FILES', 'A2C_SC_GEN_FILES', 'A2C_PY_GEN_FILES',
                           'A2C_SV_GEN_FILES', 'A2C_RTL_DOT_F', 'A2C_CPP_EXCLUDE_FILES')


def row_key(row, ext):
    return (row['fileType'], row['blockKey'], row['anchorKey'], row['variant'],
            row['context'], ext)


def ip_files(work):
    # ip's own artifacts, by the row that names them, from ip's standalone build.
    directory = os.path.join(work, 'ip')
    run(['make', '-C', directory, 'clean'])
    make(directory, 'db')
    return {row_key(row, ext): path
            for row in currentArtifactRows(open_db(work, 'ip')) if row['owner'] == 'ip'
            for ext, path in row['files'].items()}


def override_names(work):
    lines = ''.join(f'        {fileType}: {{ name: "{name}", {rest}, desc: "renamed {fileType}" }}\n'
                    for fileType, (name, rest) in NAME_OVERRIDES.items())
    path = os.path.join(work, 'ip', PROJECT_FILES['ip'])
    edit(path, '        includeFW: { name: "IncludesFW", ext: {hdr: "h", src: "cpp"}, '
               'cond: {smartInclude: true}, mode: context, basePath: fwInc, '
               'desc: "yaml based fw include file" }\n', lines)


def manifest_files(directory):
    with open(os.path.join(directory, '.gen', 'build.mk')) as f:
        lines = f.read().splitlines()
    files = list()
    for line in lines:
        variable, _, value = line.partition(' := ')
        if variable in MANIFEST_FILE_VARIABLES or variable.startswith('A2C_VL_SV_'):
            files.extend(value.split())
    return files


def check_sc_wrapper_class(work, after):
    # Each database keys ip's block its own way, so its VlRegistrar rows are
    # matched through that database's row for the renamed header.
    (header,) = [path for key, path in after.items() if key[0] == 'vlScWrap']
    ok = True
    with open(header) as f:
        if not re.search(r'^class ip_hdl_sc_wrapper\b', f.read(), re.M):
            print(f"FAIL: {header} does not declare class ip_hdl_sc_wrapper")
            ok = False
    include = f'#include "{os.path.basename(header)}"'
    registrars = list()
    for project in ('ip', '.'):
        rows = currentArtifactRows(open_db(work, project))
        (blockKey,) = [row['blockKey'] for row in rows
                       if row['fileType'] == 'vlScWrap' and row['files']['hdr'] == header]
        registrars += [row['files']['src'] for row in rows
                       if row['fileType'] == 'blockVlRegistrar' and row['blockKey'] == blockKey]
    if len(registrars) != 2:
        print(f"FAIL: expected ip's and the root's VlRegistrar for ip, found {registrars}")
        ok = False
    for path in registrars:
        with open(path) as f:
            text = f.read()
        if include not in text or 'make_shared<ip_hdl_sc_wrapper<' not in text:
            print(f"FAIL: {path} does not include {os.path.basename(header)} and build "
                  f"ip_hdl_sc_wrapper")
            ok = False
    return ok


def main():
    work = copy_simple_ip()
    try:
        ip = os.path.join(work, 'ip')
        before = ip_files(work)
        override_names(work)
        after = ip_files(work)
        ok = True
        if set(before) != set(after):
            print(f"FAIL: renaming changed which artifacts ip has: "
                  f"{sorted(set(before) ^ set(after))}")
            ok = False
        renamed = {before[key]: after[key] for key in before
                   if key in after and before[key] != after[key]}
        renamedKinds = {key[0] for key in before if key in after and before[key] != after[key]}
        if renamedKinds != set(NAME_OVERRIDES):
            print(f"FAIL: the overrides renamed only {sorted(renamedKinds)}")
            ok = False
        for old, new in renamed.items():
            if os.path.exists(old):
                os.rename(old, new)
        edit(os.path.join(work, 'fw', 'src', 'fwSimpleMain.h'),
             '#include "ipIncludesFW.h"', '#include "ipFw.h"')
        make(ip, 'migrate')
        for directory in (ip, work):
            run(['make', '-C', directory, 'clean'])
            make(directory, 'newmodule')
            make(directory, 'gen')
        left = sorted(old for old in renamed if os.path.exists(old))
        if left:
            print(f"FAIL: ip files keep their old names: {left}")
            ok = False
        for directory in (ip, work):
            missing = [path for path in manifest_files(directory) if not os.path.exists(path)]
            if missing:
                print(f"FAIL: the manifest of {os.path.relpath(directory, work)} lists files "
                      f"that do not exist: {missing}")
                ok = False
        ok = check_sc_wrapper_class(work, after) and ok
        ok = check_sv_names_and_run(work, 'renamed ip fileMap entries') and ok
        runLog = make(os.path.join(work, 'rundir'), 'run')
        if 'No error' not in runLog:
            print(f"FAIL: the root's model run did not finish cleanly:\n{runLog[-3000:]}")
            ok = False
        if not ok:
            print("SOME TESTS FAILED")
            return 1
        print(f"PASS: with {len(NAME_OVERRIDES)} ip fileMap entries renamed, ip and the root "
              f"generate, SV names match their files, both manifests list only existing files, "
              f"the renamed SC wrapper header declares ip_hdl_sc_wrapper, and the root's model and Verilated runs pass")
        print("ALL TESTS PASSED")
        return 0
    finally:
        remove(work)


if __name__ == '__main__':
    sys.exit(main())
