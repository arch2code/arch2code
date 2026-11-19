#!/usr/bin/env python3
"""Every channel on a register's path starts at the register's defaultValue.

The container that owns a register builds its channel at the register's
defaultValue. A leaf's <block>Channels class, which a Tandem wrapper and an
excluded-instance testbench use to stand in for that channel, must build its
channel for the port at the same value, or a read before the first write
returns 0 there and the default everywhere else. A status or external_reg
channel that carries no register takes no initial value.
"""

import sys
import types

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    find_block,
    render_plain_block,
    render_router,
)
from pysrc.processYaml import projectOpen
from templates.systemc import baseClassDecl, constructor

ARCH = APB_PREAMBLE + """    statIf:
        desc: "status"
        interfaceType: status
        structures:
            - { structure: cfgRegSt, structureType: data_t }
    extIf:
        desc: "external register"
        interfaceType: external_reg
        structures:
            - { structure: cfgRegSt, structureType: data_t }

blocks:
""" + render_plain_block('top', '        hasRtl: false\n') + render_router('apbDecode', 'top') \
    + render_plain_block('regOwner') + render_plain_block('leaf') + render_plain_block('peer') + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uRegOwner:  { container: top, instanceType: regOwner, addressGroup: top }
    uLeaf:      { container: regOwner, instanceType: leaf }
    uPeer:      { container: regOwner, instanceType: peer }

connections:
    - { interface: statIf, src: uPeer, dst: uLeaf, dstport: plainStat }
    - { interface: extIf, src: uPeer, dst: uLeaf, dstport: plainExt }

registers:
    - { register: rwReg,  regType: rw,  block: regOwner, structure: cfgRegSt, defaultValue: 0x42, desc: "rw" }
    - { register: extReg, regType: ext, block: regOwner, structure: cfgRegSt, defaultValue: 0x24, desc: "ext" }
    - { register: roReg,  regType: ro,  block: regOwner, structure: cfgRegSt, defaultValue: 0x17, desc: "ro" }

registerConnections:
    - { register: rwReg,  block: regOwner, instance: uLeaf }
    - { register: extReg, block: regOwner, instance: uLeaf }
    - { register: roReg,  block: regOwner, instance: uLeaf }
"""

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def channelArgs(lines, name, prefix):
    """The constructor argument list of channel `name` in rendered initializer lines."""
    for line in lines:
        entry = line.strip().lstrip(',')
        if entry.startswith(prefix):
            return entry
    return f"<no channel {name}>"


def test_channels_start_at_register_default():
    db_path, project_path, arch_paths = build_database(ARCH)
    try:
        prj = projectOpen(db_path)
        owner = prj.getBlockData(find_block(prj, 'regOwner')[0])
        ownerInit = constructor.render(types.SimpleNamespace(section='init', mode='module'), prj, owner).splitlines()
        check(channelArgs(ownerInit, 'rwReg', 'rwReg(').endswith('cfgRegSt::_packedSt(0x42))'),
              f"regOwner builds rwReg at 0x42 (got {channelArgs(ownerInit, 'rwReg', 'rwReg(')})")
        check(channelArgs(ownerInit, 'extReg', 'extReg(').endswith('cfgRegSt::_packedSt(0x24))'),
              f"regOwner builds extReg at 0x24 (got {channelArgs(ownerInit, 'extReg', 'extReg(')})")
        check(channelArgs(ownerInit, 'roReg', 'roReg(').endswith('cfgRegSt::_packedSt(0x17))'),
              f"regOwner builds roReg at 0x17 (got {channelArgs(ownerInit, 'roReg', 'roReg(')})")

        leaf = prj.getBlockData(find_block(prj, 'leaf')[0])
        decl = baseClassDecl.render(types.SimpleNamespace(mode='module', noExternalComments=True), prj, leaf)
        channels = decl[decl.index('class leafChannels'):].splitlines()
        expected = {
            'rwReg': 'rwReg(("rwReg"+name).c_str(), srcName, cfgRegSt::_packedSt(0x42))',
            'extReg': 'extReg(("extReg"+name).c_str(), srcName, cfgRegSt::_packedSt(0x24))',
            'roReg': 'roReg(("roReg"+name).c_str(), srcName, cfgRegSt::_packedSt(0x17))',
            'plainStat': 'plainStat(("plainStat"+name).c_str(), srcName)',
            'plainExt': 'plainExt(("plainExt"+name).c_str(), srcName)',
        }
        for name, want in expected.items():
            got = channelArgs(channels, name, f'{name}(("{name}"')
            check(got == want, f"leafChannels builds {name} as {want} (got {got})")
    finally:
        cleanup([project_path, db_path] + arch_paths)


if __name__ == '__main__':
    print("=" * 72)
    print("TESTING REGISTER CHANNEL INITIAL VALUES")
    print("=" * 72)
    test_channels_start_at_register_default()
    if FAILURES:
        print(f"\nRESULT: {len(FAILURES)} check(s) FAILED")
        sys.exit(1)
    print("\nRESULT: all register channel initial value checks passed")
    sys.exit(0)
