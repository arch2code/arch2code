#!/usr/bin/env python3
"""make db accepts and resolves the tandem: status-compare policy, and rejects its misuse.

A Tandem run compares each status output of a leaf block. The tandem: key on the
row that defines such a port sets how: fatal, warn, final, off, or a level window
in ns. The rows that can define a leaf's status output are a status connection
(its src end), a connectionMaps entry with direction src, and a registerConnections
entry of an ro register, whose registers row may give the value for all of them.

projectCreate persists the resolved policy per (block, port), and getBlockData
returns the block's map as tandemStatusPolicy. make db rejects an unknown value, a
non-positive number, the key on a port that is not a leaf's status output, and a
port whose defining rows disagree, across instances or fan-out.
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
          wrap_out_extra=''):
    """Each *_extra is appended inside one row's inline dict, e.g. ', tandem: warn'.
    A fan_extra adds a second row from uSrcA's statIf, which getBlockData rejects as a
    duplicate port, so only a case make db rejects uses it."""
    fan = '' if fan_extra is None else (
        "    - { interface: statIf, src: uSrcA, dst: uSinkB" + fan_extra + " }\n")
    preamble = APB_PREAMBLE + """    statIf:
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
            + render_plain_block('srcLeaf') + render_plain_block('sinkLeaf') + render_plain_block('wrap')
            + render_plain_block('regOwner') + render_plain_block('tbSrc', '        hasRtl: false\n') + """
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
    uRegLeaf:   { container: regOwner, instanceType: sinkLeaf }

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

registerConnections:
    - { register: roReg, block: regOwner, instance: uRegLeaf""" + ro_rc_extra + """ }
    - { register: rwReg, block: regOwner, instance: uRegLeaf""" + rw_rc_extra + """ }
""")


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
               for block in ('srcLeaf', 'sinkLeaf', 'wrap', 'regOwner')}
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


NONE = {'srcLeaf': {}, 'sinkLeaf': {}, 'wrap': {}, 'regOwner': {}}


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
           policy(sinkLeaf={'roReg': 'final'}), ro_rc_extra=', tandem: final')
    accept("tandem: on an ro registers row applies to its registerConnections ports",
           policy(sinkLeaf={'roReg': 'off'}), ro_reg_extra=', tandem: off')
    accept("the same tandem: on the registers row and its registerConnections row",
           policy(sinkLeaf={'roReg': 'warn'}), ro_reg_extra=', tandem: warn', ro_rc_extra=', tandem: warn')

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
                                             "status input"], rw_rc_extra=', tandem: fatal')
    reject("an rw registers row", ["register 'rwReg' of block 'regOwner'", "regType: rw"],
           rw_reg_extra=', tandem: fatal')
    reject("an ro register that no registerConnections row connects",
           ["register 'ownReg' of block 'regOwner'", "no registerConnections row connects"],
           own_reg_extra=', tandem: fatal')
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
