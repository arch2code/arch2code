#!/usr/bin/env python3
"""A child project's own fileMap names its artifacts inside a composing root.

Works on private copies of examples/simple_ip, whose root composes the child
projects ip and common. Each check changes ip's fileMap; the includeFW checks
also change the root's:
- svFilePrefix ip_ with rtlModule named _impl: ip's RTL is ip_<block>_impl.sv
  with module ip_<block>_impl, standalone and composed. The root instantiates
  ip_ip_impl, its manifest lists only SV files that exist, and the root's
  Verilated run passes;
- configModule named Cfg: ip's Config modules are ipCfg.cppm and
  ip_ipRegsCfg.cppm, the root's manifest compiles those files, and the root's
  Verilated run passes;
- includeFW in ip's fileMap only, named Fw: the root accepts it, ip's
  firmware headers are ipFw.h and ipTopFw.h, the root's manifest compiles
  ip/fw, and the root's Verilated run passes with firmware that includes ipFw.h;
- includeFW in the root's fileMap only: ip gets no firmware artifact.
"""

import os
import re
import sys

from test_file_prefix import (PROJECT_FILES, check_sv_names_and_run, copy_simple_ip,
                              currentArtifactRows, edit, make, open_db, remove, run,
                              set_prefixes)


# ip's RTL blocks, each with a user-owned rtl/<block>.sv.
IP_RTL_BLOCKS = ('ip', 'ipRegs', 'ipStdDecode', 'ipStdDriver', 'ipStdMaster', 'ipStdTop')

RTL_IMPL_ENTRY = ('        rtlModule: { name: "_impl", ext: {sv: "sv"}, cond: {hasRtl: true}, '
                  'mode: block, basePath: rtl, desc: "RTL implementation file" }\n')
CONFIG_ENTRY = ('        configModule: { name: "Cfg", ext: {cppm: "cppm"}, condAnd: {hasOwnParams: true}, '
                'mode: registrar, basePath: registrar, ownerQualified: true, '
                'desc: "Config module" }\n')
INCLUDE_FW_ENTRY = ('includeFW: { name: "IncludesFW", ext: {hdr: "h", src: "cpp"}, '
                    'cond: {smartInclude: true}, mode: context, basePath: fwInc, '
                    'desc: "yaml based fw include file" }\n')


def add_ip_entry(work, entry):
    edit(os.path.join(work, 'ip', PROJECT_FILES['ip']), '    fileMap:\n', '    fileMap:\n' + entry)


def regenerate(work):
    # ip first, as each project generates only its own files.
    for directory in (os.path.join(work, 'ip'), work):
        run(['make', '-C', directory, 'clean'])
        make(directory, 'newmodule')
        make(directory, 'gen')


def manifest_values(work, variable):
    with open(os.path.join(work, '.gen', 'build.mk')) as f:
        (line,) = [l for l in f.read().splitlines() if l.startswith(f'{variable} :=')]
    return line.split(':=', 1)[1].split()


def names_match_standalone(work, label):
    standalone, composed = open_db(work, 'ip'), open_db(work, '.')
    ok = True
    for blockKey, name in standalone.blockSvModuleName.items():
        if blockKey in composed.blockSvModuleName and composed.blockSvModuleName[blockKey] != name:
            print(f"FAIL: {label}: ip block {blockKey} is {name} standalone but "
                  f"{composed.blockSvModuleName[blockKey]} composed")
            ok = False
    return ok


def check_child_rtl_prefix_and_name():
    work = copy_simple_ip()
    try:
        ip = os.path.join(work, 'ip')
        set_prefixes(work, 'ip', {'sv': 'ip_'})
        add_ip_entry(work, RTL_IMPL_ENTRY)
        # The user renames each RTL file to its new name; migrate relabels it.
        for block in IP_RTL_BLOCKS:
            os.rename(os.path.join(ip, 'rtl', f'{block}.sv'),
                      os.path.join(ip, 'rtl', f'ip_{block}_impl.sv'))
        make(ip, 'migrate')
        regenerate(work)
        ok = True
        with open(os.path.join(ip, 'rtl', 'ip_ip_impl.sv')) as f:
            if not re.search(r'^module ip_ip_impl\b', f.read(), re.M):
                print("FAIL: ip/rtl/ip_ip_impl.sv does not declare module ip_ip_impl")
                ok = False
        with open(os.path.join(work, 'rtl', 'simple_ip.sv')) as f:
            if not re.search(r'^ip_ip_impl #\(', f.read(), re.M):
                print("FAIL: the root's simple_ip.sv does not instantiate ip_ip_impl")
                ok = False
        svFiles = manifest_values(work, 'A2C_SV_FILES')
        if os.path.join(ip, 'rtl', 'ip_ip_impl.sv') not in svFiles:
            print(f"FAIL: the root manifest's A2C_SV_FILES lacks ip/rtl/ip_ip_impl.sv: {svFiles}")
            ok = False
        missing = [path for path in svFiles if not os.path.exists(path)]
        if missing:
            print(f"FAIL: the root manifest lists SV files that do not exist: {missing}")
            ok = False
        ok = names_match_standalone(work, 'ip_ / _impl') and ok
        ok = check_sv_names_and_run(work, 'ip_ / _impl') and ok
        if ok:
            print("PASS: with ip at svFilePrefix ip_ and rtlModule _impl, the root instantiates "
                  "ip_ip_impl, lists only existing SV files, and the Verilated run passes")
        return ok
    finally:
        remove(work)


def check_child_config_module_name():
    work = copy_simple_ip()
    try:
        registrar = os.path.join(work, 'ip', 'registrar')
        add_ip_entry(work, CONFIG_ENTRY)
        regenerate(work)
        ok = True
        present = sorted(name for name in os.listdir(registrar) if 'Cfg' in name or 'Config' in name)
        if present != ['ipCfg.cppm', 'ip_ipRegsCfg.cppm']:
            print(f"FAIL: ip/registrar holds the Config modules {present}")
            ok = False
        moduleFiles = manifest_values(work, 'A2C_CPP_MODULE_FILES')
        if os.path.join(registrar, 'ipCfg.cppm') not in moduleFiles:
            print("FAIL: the root manifest's A2C_CPP_MODULE_FILES lacks ip/registrar/ipCfg.cppm")
            ok = False
        missing = [path for path in moduleFiles if not os.path.exists(path)]
        if missing:
            print(f"FAIL: the root manifest lists module files that do not exist: {missing}")
            ok = False
        ok = check_sv_names_and_run(work, 'configModule Cfg') and ok
        if ok:
            print("PASS: with ip's configModule named Cfg, the root compiles ipCfg.cppm and "
                  "the Verilated run passes")
        return ok
    finally:
        remove(work)


def fw_rows(work):
    # Every includeFW artifact the composed root's database names, by owner.
    rows = currentArtifactRows(open_db(work, '.'))
    fwFiles = dict()
    for row in rows:
        if row['fileType'] == 'includeFW':
            fwFiles.setdefault(row['owner'], set()).update(row['files'].values())
    return fwFiles


def check_child_only_entry_kind_accepted():
    # The root drops includeFW, and ip keeps it under the name Fw. The root's
    # firmware, compiled in the root's build, includes ip's renamed header.
    work = copy_simple_ip()
    try:
        ip = os.path.join(work, 'ip')
        edit(os.path.join(work, PROJECT_FILES['.']), '        ' + INCLUDE_FW_ENTRY, '')
        edit(os.path.join(ip, PROJECT_FILES['ip']), 'name: "IncludesFW"', 'name: "Fw"')
        edit(os.path.join(work, 'fw', 'src', 'fwSimpleMain.h'),
             '#include "ipIncludesFW.h"', '#include "ipFw.h"')
        # The user removes the firmware files neither project generates any more.
        for stem in ('fw/simple_ipIncludesFW', 'ip/fw/ipIncludesFW', 'ip/fw/ipTopIncludesFW'):
            for ext in ('h', 'cpp'):
                os.remove(os.path.join(work, f'{stem}.{ext}'))
        regenerate(work)
        ok = True
        present = sorted(os.listdir(os.path.join(ip, 'fw')))
        if present != ['ipFw.cpp', 'ipFw.h', 'ipTopFw.cpp', 'ipTopFw.h']:
            print(f"FAIL: ip/fw holds {present}")
            ok = False
        fwFiles = fw_rows(work)
        expected = {os.path.join(ip, 'fw', name) for name in present}
        if fwFiles.get('ip') != expected or 'simple_ip' in fwFiles:
            print(f"FAIL: the composed root names the firmware artifacts {fwFiles}")
            ok = False
        if os.path.join(ip, 'fw') not in manifest_values(work, 'A2C_SC_SRC_DIRS'):
            print("FAIL: the root manifest's A2C_SC_SRC_DIRS lacks ip/fw")
            ok = False
        ok = check_sv_names_and_run(work, 'ip-only includeFW Fw') and ok
        if ok:
            print("PASS: with includeFW in ip's fileMap only, named Fw, the root compiles "
                  "ip/fw/ipFw.h and the Verilated run passes")
        return ok
    finally:
        remove(work)


def check_root_only_entry_kind_skips_child():
    work = copy_simple_ip()
    try:
        # includeFW is ip's only fileMap entry.
        edit(os.path.join(work, 'ip', PROJECT_FILES['ip']),
             '    fileMap:\n        ' + INCLUDE_FW_ENTRY, '')
        run(['make', '-C', work, 'clean'])
        make(work, 'db')
        fwFiles = fw_rows(work)
        if 'ip' in fwFiles or 'simple_ip' not in fwFiles:
            print(f"FAIL: with includeFW in the root's fileMap only, the firmware "
                  f"artifacts are {fwFiles}")
            return False
        print("PASS: with includeFW in the root's fileMap only, ip has no firmware artifact")
        return True
    finally:
        remove(work)


def main():
    checks = (check_child_only_entry_kind_accepted, check_root_only_entry_kind_skips_child,
              check_child_rtl_prefix_and_name, check_child_config_module_name)
    failed = [check.__name__ for check in checks if not check()]
    if failed:
        print(f"SOME TESTS FAILED: {', '.join(failed)}")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == '__main__':
    sys.exit(main())
