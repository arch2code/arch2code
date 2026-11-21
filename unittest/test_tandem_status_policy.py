#!/usr/bin/env python3
"""make db accepts and resolves the tandem: status-compare policy, and rejects its misuse.

A Tandem run compares each status output of a leaf block. The tandem: key on the
row that defines such a port sets how: fatal, warn, final, off, or a level window
in ns. The rows that can define a leaf's status output are a status connection
(its src end), a connectionMaps entry with direction src, and a registerConnections
entry of an ro register, whose registers row may give the value for all of them.
The same rows of an ext register set how a Tandem run compares the value the
connected leaf publishes on its external_reg port.
An ro or ext register no registerConnections row connects stays inside its own
leaf, and the key on its registers row sets how the leaf's register-bus tee
compares firmware reads of it.

projectCreate persists the resolved policy per (block, port), and getBlockData
returns the block's map as tandemStatusPolicy, and the read table as
tandemRegisterReads. make db rejects an unknown value, a non-positive number, the
key on a port that is not a leaf's status output or ext register port, or on a
register no Tandem run reads, and a port or register whose defining rows
disagree, across instances or fan-out.
"""

import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    find_block,
    render_plain_block,
    render_router,
)
from pysrc.processYaml import projectOpen


def _arch(conn_extra='', fan_extra=None, second_extra='', map_extra='', rv_extra='', in_extra='',
          ro_reg_extra='', rw_reg_extra='', ro_rc_extra='', rw_rc_extra='', own_reg_extra='',
          wrap_out_extra='', leaf_ro_extra='', leaf_ext_extra='', leaf_rw_extra='', leaf_mem_extra='',
          ext_reg_extra='', ext_rc_extra='', wide_ext_extra=None, ext_tb_extra=None, leaf_arr_extra=None):
    """Each *_extra is appended inside one row's inline dict, e.g. ', tandem: warn'.
    A fan_extra adds a second row from uSrcA's statIf, which getBlockData rejects as a
    duplicate port, so only a case make db rejects uses it. A wide_ext_extra adds a
    64-bit ext register to regLeaf, which make db rejects as wider than the bus. An
    ext_tb_extra connects a second ext register to an instance of rtlOnly, which has
    hasMdl: false. A leaf_arr_extra adds an ro array register of four elements to regLeaf."""
    tbInst = '' if ext_tb_extra is None else "    uRegTb:     { container: regOwner, instanceType: rtlOnly }\n"
    tbReg = '' if ext_tb_extra is None else (
        '    - { register: extTb, regType: ext, block: regOwner, structure: cfgRegSt, desc: "ext to tb" }\n')
    tbRc = '' if ext_tb_extra is None else (
        "    - { register: extTb, block: regOwner, instance: uRegTb" + ext_tb_extra + " }\n")
    wide = '' if wide_ext_extra is None else (
        '    - { register: wideExt, regType: ext, block: regLeaf, structure: wideRegSt, desc: "wide ext"'
        + wide_ext_extra + ' }\n')
    arr = '' if leaf_arr_extra is None else (
        '    - { register: leafArr, regType: ro, block: regLeaf, structure: cfgRegSt, count: 4, desc: "leaf ro array"'
        + leaf_arr_extra + ' }\n')
    fan = '' if fan_extra is None else (
        "    - { interface: statIf, src: uSrcA, dst: uSinkB" + fan_extra + " }\n")
    preamble = APB_PREAMBLE.replace('structures:\n', """structures:
    wideRegSt:
        lo: { varType: apbDataT, generator: register, desc: "low word" }
        hi: { varType: apbDataT, generator: register, desc: "high word" }
""", 1) + """    statIf:
        desc: "status"
        interfaceType: status
        structures:
            - { structure: cfgRegSt, structureType: data_t }
    rvIf:
        desc: "rdy_vld"
        interfaceType: rdy_vld
        structures:
            - { structure: cfgRegSt, structureType: data_t }
"""
    return (preamble + """
blocks:
""" + render_plain_block('top', '        hasRtl: false\n') + render_router('apbDecode', 'top')
            + render_plain_block('srcLeaf') + render_plain_block('sinkLeaf') + render_plain_block('regSink')
            + render_plain_block('wrap')
            + render_plain_block('regOwner') + render_plain_block('tbSrc', '        hasRtl: false\n')
            + render_plain_block('regLeaf') + """    rtlOnly:
        desc: "RTL-only block"
        hasMdl: false

instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uSrcA:      { container: top, instanceType: srcLeaf }
    uSrcB:      { container: top, instanceType: srcLeaf }
    uSinkA:     { container: top, instanceType: sinkLeaf }
    uSinkB:     { container: top, instanceType: sinkLeaf }
    uTbSrc:     { container: top, instanceType: tbSrc }
    uWrap:      { container: top, instanceType: wrap }
    uInner:     { container: wrap, instanceType: srcLeaf }
    uRegOwner:  { container: top, instanceType: regOwner, addressGroup: top }
    uRegLeaf:   { container: regOwner, instanceType: regSink }
    uOwnLeaf:   { container: top, instanceType: regLeaf, addressGroup: top }
""" + tbInst + """
connections:
    - { interface: statIf, src: uSrcA, dst: uSinkA""" + conn_extra + """ }
""" + fan + """    - { interface: statIf, src: uSrcB, dst: uSinkB, dstport: statB""" + second_extra + """ }
    - { interface: rvIf, src: uSrcA, dst: uSinkA""" + rv_extra + """ }
    - { interface: statIf, src: uTbSrc, dst: uSinkA, dstport: tbIn""" + in_extra + """ }
    - { interface: statIf, src: uWrap, dst: uSinkB, dstport: wrapIn""" + wrap_out_extra + """ }

connectionMaps:
    - { interface: statIf, block: wrap, direction: src, instance: uInner""" + map_extra + """ }

registers:
    - { register: roReg,  regType: ro, block: regOwner, structure: cfgRegSt, desc: "ro" """ + ro_reg_extra + """ }
    - { register: rwReg,  regType: rw, block: regOwner, structure: cfgRegSt, desc: "rw" """ + rw_reg_extra + """ }
    - { register: ownReg, regType: ro, block: regOwner, structure: cfgRegSt, desc: "internal" """ + own_reg_extra + """ }
    - { register: leafRo, regType: ro, block: regLeaf, structure: cfgRegSt, desc: "leaf ro" """ + leaf_ro_extra + """ }
    - { register: leafRw, regType: rw, block: regLeaf, structure: cfgRegSt, desc: "leaf rw" """ + leaf_rw_extra + """ }
    - { register: leafExt, regType: ext, block: regLeaf, structure: cfgRegSt, desc: "leaf ext" """ + leaf_ext_extra + """ }
    - { register: leafMem, regType: memory, block: regLeaf, structure: cfgRegSt, addressStruct: apbAddrSt, wordLines: 8, desc: "leaf memory" """ + leaf_mem_extra + """ }
    - { register: extReg, regType: ext, block: regOwner, structure: cfgRegSt, desc: "connected ext" """ + ext_reg_extra + """ }
""" + wide + arr + tbReg + """
registerConnections:
    - { register: roReg, block: regOwner, instance: uRegLeaf""" + ro_rc_extra + """ }
    - { register: rwReg, block: regOwner, instance: uRegLeaf""" + rw_rc_extra + """ }
    - { register: extReg, block: regOwner, instance: uRegLeaf""" + ext_rc_extra + """ }
""" + tbRc)


RESULTS = []


def accept(label, expected, **rows):
    """make db succeeds and getBlockData gives each block the expected policy map."""
    try:
        db_path, project_path, arch_paths = build_database(_arch(**rows))
    except RuntimeError as exc:
        print(f"FAIL: {label}: {exc}")
        RESULTS.append(False)
        return
    try:
        prj = projectOpen(db_path)
        got = {block: prj.getBlockData(find_block(prj, block)[0])['tandemStatusPolicy']
               for block in ('srcLeaf', 'sinkLeaf', 'regSink', 'wrap', 'regOwner')}
        ok = got == expected
        print(f"{'PASS' if ok else 'FAIL'}: {label}" + ('' if ok else f": expected {expected}, got {got}"))
        RESULTS.append(ok)
    finally:
        cleanup([project_path, db_path] + arch_paths)


def accept_reads(label, expected, **rows):
    """make db succeeds and regLeaf's read table holds the expected {register: policy}, or is None."""
    try:
        db_path, project_path, arch_paths = build_database(_arch(**rows))
    except RuntimeError as exc:
        print(f"FAIL: {label}: {exc}")
        RESULTS.append(False)
        return
    try:
        prj = projectOpen(db_path)
        reads = prj.getBlockData(find_block(prj, 'regLeaf')[0])['tandemRegisterReads']
        got = None if reads is None else {reg['register']: reg['policy'] for reg in reads['registers']}
        ok = got == expected and (reads is None or reads['port'] == 'apbReg')
        print(f"{'PASS' if ok else 'FAIL'}: {label}" + ('' if ok else f": expected {expected}, got {reads}"))
        RESULTS.append(ok)
    finally:
        cleanup([project_path, db_path] + arch_paths)


def accept_array_reads(label):
    """tandem: warn on regLeaf's ro array register gives one read entry per element, named
    leafArr[k]. The fixture places leafArr at 0x20 with an 8-byte element stride."""
    try:
        db_path, project_path, arch_paths = build_database(_arch(leaf_arr_extra=', tandem: warn'))
    except RuntimeError as exc:
        print(f"FAIL: {label}: {exc}")
        RESULTS.append(False)
        return
    try:
        prj = projectOpen(db_path)
        expected = [{'register': f'leafArr[{k}]', 'offset': offset, 'size': 2, 'policy': 'warn'}
                    for k, offset in enumerate((32, 40, 48, 56))]
        got = prj.getBlockData(find_block(prj, 'regLeaf')[0])['tandemRegisterReads']['registers']
        ok = got == expected
        print(f"{'PASS' if ok else 'FAIL'}: {label}" + ('' if ok else f": expected {expected}, got {got}"))
        RESULTS.append(ok)
    finally:
        cleanup([project_path, db_path] + arch_paths)


def reject(label, needles, **rows):
    """make db fails and its diagnostic holds every needle."""
    try:
        result = build_database(_arch(**rows), expect_success=False)
    except RuntimeError as exc:
        print(f"FAIL: {label}: {exc}")
        RESULTS.append(False)
        return
    db_path, project_path, arch_paths, run = result
    try:
        combined = run.stdout + run.stderr
        missing = [n for n in needles if n not in combined]
        print(f"{'PASS' if not missing else 'FAIL'}: {label}"
              + ('' if not missing else f": diagnostic lacks {missing}\n{combined}"))
        RESULTS.append(not missing)
    finally:
        cleanup([project_path, db_path] + arch_paths)


NONE = {'srcLeaf': {}, 'sinkLeaf': {}, 'regSink': {}, 'wrap': {}, 'regOwner': {}}


def policy(**blocks):
    return dict(NONE, **blocks)


def run_all_tests():
    accept("no tandem: key leaves every block without a policy", NONE)
    # every row defining srcLeaf's statIf, one per instance, must agree
    both = dict(conn_extra=', tandem: {v}', second_extra=', tandem: {v}',
                map_extra=', tandem: {v}')
    for word in ('fatal', 'warn', 'final', 'off'):
        accept(f"tandem: {word} on every row defining srcLeaf's statIf",
               policy(srcLeaf={'statIf': word}), **{k: v.format(v=word) for k, v in both.items()})
    accept("tandem: 250 is a 250 ns level window", policy(srcLeaf={'statIf': 250.0}),
           **{k: v.format(v=250) for k, v in both.items()})
    accept("tandem: 12.5 is a 12.5 ns level window", policy(srcLeaf={'statIf': 12.5}),
           **{k: v.format(v=12.5) for k, v in both.items()})
    accept("tandem: on a registerConnections row of an ro register",
           policy(regSink={'roReg': 'final'}), ro_rc_extra=', tandem: final')
    accept("tandem: on an ro registers row applies to its registerConnections ports",
           policy(regSink={'roReg': 'off'}), ro_reg_extra=', tandem: off')
    accept("the same tandem: on the registers row and its registerConnections row",
           policy(regSink={'roReg': 'warn'}), ro_reg_extra=', tandem: warn', ro_rc_extra=', tandem: warn')
    for value, resolved in (('fatal', 'fatal'), ('warn', 'warn'), ('final', 'final'), ('off', 'off'),
                            ('250', 250.0)):
        accept(f"tandem: {value} on a connected ext registers row applies to its external_reg port",
               policy(regSink={'extReg': resolved}), ext_reg_extra=f', tandem: {value}')
    accept("tandem: on a registerConnections row of an ext register",
           policy(regSink={'extReg': 'final'}), ext_rc_extra=', tandem: final')
    accept("the same tandem: on an ext registers row and its registerConnections row",
           policy(regSink={'extReg': 'warn'}), ext_reg_extra=', tandem: warn', ext_rc_extra=', tandem: warn')
    accept_reads("a leaf with no tagged register has no read table", None)
    for value, resolved in (('fatal', 'fatal'), ('warn', 'warn'), ('final', 'final'), ('off', 'off'),
                            ('250', 250.0)):
        accept_reads(f"tandem: {value} on an ro registers row no registerConnections row connects",
                     {'leafRo': resolved}, leaf_ro_extra=f', tandem: {value}')
        accept_reads(f"tandem: {value} on an ext registers row no registerConnections row connects",
                     {'leafExt': resolved}, leaf_ext_extra=f', tandem: {value}')
    accept_reads("tandem: on an ro and an ext register of one leaf", {'leafRo': 'off', 'leafExt': 'warn'},
                 leaf_ro_extra=', tandem: off', leaf_ext_extra=', tandem: warn')
    accept_array_reads("tandem: warn on an ro array register covers each of its four elements")

    all_src = {k: v.format(v='fatal') for k, v in both.items()}
    reject("an unknown word", ["tandem: loud", "not a tandem status-compare policy"],
           **dict(all_src, conn_extra=', tandem: loud'))
    reject("a quoted number", ["tandem: 100", "not a tandem status-compare policy"],
           **dict(all_src, conn_extra=', tandem: "100"'))
    reject("a zero window", ["tandem: 0", "positive number of ns"], **dict(all_src, conn_extra=', tandem: 0'))
    reject("a negative window", ["tandem: -5", "positive number of ns"],
           **dict(all_src, conn_extra=', tandem: -5'))
    reject("a boolean", ["tandem: True", "not a tandem status-compare policy"],
           **dict(all_src, conn_extra=', tandem: true'))
    reject("a rdy_vld connection", ["connection rvIf from 'uSrcA' to 'uSinkA'", "of type rdy_vld"],
           rv_extra=', tandem: fatal')
    reject("a status input: the src block has hasRtl: false",
           ["connection statIf from 'uTbSrc' to 'uSinkA'", "block 'tbSrc'", "both hasMdl and hasRtl",
            "status input"], in_extra=', tandem: fatal')
    reject("a container's status output", ["connection statIf from 'uWrap' to 'uSinkB'", "contains instances (uInner)",
                                           "connectionMaps row"], wrap_out_extra=', tandem: fatal')
    reject("an rw registerConnections row", ["registerConnections entry for register 'rwReg'", "regType: rw",
                                             "Only an ro or ext register", "status input"], rw_rc_extra=', tandem: fatal')
    reject("an rw registers row", ["register 'rwReg' of block 'regOwner'", "regType: rw"],
           rw_reg_extra=', tandem: fatal')
    reject("an rw registers row of a leaf", ["register 'leafRw' of block 'regLeaf'", "regType: rw",
                                             "an ro or ext register", "read back the same data"],
           leaf_rw_extra=', tandem: warn')
    reject("a memory registers row of a leaf", ["register 'leafMem' of block 'regLeaf'", "regType: memory",
                                                "an ro or ext register", "always compares the reads of a memory register"],
           leaf_mem_extra=', tandem: warn')
    reject("an ext registers row and its registerConnections row that differ",
           ["register 'extReg'", "tandem: final", "tandem: warn", "Set it in one place"],
           ext_reg_extra=', tandem: warn', ext_rc_extra=', tandem: final')
    reject("a connected ext register with a bad value",
           ["registerConnections entry for register 'extReg'", "tandem: loud"], ext_rc_extra=', tandem: loud')
    reject("an ext register connected to a block that does not run in Tandem",
           ["registerConnections entry for register 'extTb'", "block 'rtlOnly'", "both hasMdl and hasRtl"],
           ext_tb_extra=', tandem: warn')
    reject("an ext register wider than the register bus",
           ["ext register 'wideExt' of block 'regLeaf'", "wider than the 32-bit register bus", "one bus access"],
           wide_ext_extra=', tandem: warn')
    reject("an ext register no registerConnections row connects, with a bad value",
           ["register 'leafExt' of block 'regLeaf'", "tandem: loud"], leaf_ext_extra=', tandem: loud')
    reject("an ro register no registerConnections row connects, owned by a container",
           ["register 'ownReg' of block 'regOwner'", "contains instances (uRegLeaf)", "firmware reads"],
           own_reg_extra=', tandem: fatal')
    reject("an ro register no registerConnections row connects, with a bad value",
           ["register 'leafRo' of block 'regLeaf'", "tandem: loud"], leaf_ro_extra=', tandem: loud')
    reject("a registers row and its registerConnections row that differ",
           ["register 'roReg'", "tandem: final", "tandem: warn", "Set it in one place"],
           ro_reg_extra=', tandem: warn', ro_rc_extra=', tandem: final')
    reject("two instances of a block that disagree",
           ["Port 'statIf' of block 'srcLeaf'", "from 'uSrcB' to 'uSinkB'", "tandem: warn",
            "to instance 'uInner'", "tandem: fatal"],
           **dict(all_src, second_extra=', tandem: warn'))
    reject("one instance set and another unset",
           ["Port 'statIf' of block 'srcLeaf'", "connectionMaps entry for port 'statIf' of block 'wrap'",
            "tandem: unset"], **dict(all_src, map_extra=''))
    reject("a fanned-out source port with different values",
           ["Port 'statIf' of block 'srcLeaf'", "from 'uSrcA' to 'uSinkA'", "from 'uSrcA' to 'uSinkB'",
            "tandem: 40", "tandem: 50"],
           **dict({k: v.format(v=40) for k, v in both.items()}, fan_extra=', tandem: 50'))
    return 0 if all(RESULTS) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
