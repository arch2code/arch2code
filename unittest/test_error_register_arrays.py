#!/usr/bin/env python3
"""make db rejects a register array, or a registerConnections row for one, that
the generator cannot build.

A register with count: is an array of count elements, and a registerConnections
row with index: hands one element of it to an instance. make db rejects:
- a count that is not an integer of at least 1, that is a block parameter or a
  parameterizable constant, or that sits on a regType: memory register;
- an index on a register without count, an index outside [0, count), and a
  parameterizable index constant;
- two rows giving one register to one instance;
- instances of one child block that take a register in different forms, with
  index and without, or an instance of that block left out;
- an ro or ext element, or an ro or ext scalar, with more than one consumer,
  and an ro or ext array element no row covers;
- a child block that takes one register port name from two owners whose
  registers differ in regType, structure, count or form. When two structures
  share a name, the diagnostic names the file declaring each;
- REG_<BLOCK>_<REG>_STRIDE or _COUNT equal to the define of another register
  or regAccess memory of the block;
- an element name <reg>_<k> that is the name of another register or regAccess
  memory of the block, or of a port of a block that takes the whole array.

Each diagnostic names the file, the register, the block and the fix. An rw
array whose whole and index rows go to different child blocks builds, as does
an index named by a constant, one register port fed alike by two owners, and
an owner port named like an element of an array the owner uses itself.
"""

import os
import shutil
import sys
import tempfile

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_plain_block,
    render_router,
    run_arch2code,
    test_dir,
)


PREAMBLE = APB_PREAMBLE.replace(
    'constants:\n', 'constants:\n    N_FIXED: { value: 2, desc: "array size" }\n', 1)


def _arch(registers, connections, *, ip_params='', memories='', owner_param=False):
    """owner_param gives block owner the parameter N_PARAM and binds it in
    variant v0 of uOwner."""
    owner_lines = '        params: [N_PARAM]\n' if owner_param else ''
    variant = ', variant: v0' if owner_param else ''
    parameters = '\nparameters:\n    owner:\n        v0:\n            N_PARAM: 2\n' if owner_param else ''
    return (PREAMBLE.replace('structures:\n', ip_params + 'structures:\n', 1).rstrip() + """

blocks:
""" + render_plain_block('top') + render_router('apbDecode', 'top')
            + render_leaf('owner', extra_block_lines=owner_lines)
            + render_plain_block('childA') + render_plain_block('childB') + parameters + f"""
instances:
    uTop:       {{ container: top, instanceType: top }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uOwner:     {{ container: top, instanceType: owner, addressGroup: top{variant} }}
    uA0:        {{ container: owner, instanceType: childA }}
    uA1:        {{ container: owner, instanceType: childA }}
    uB:         {{ container: owner, instanceType: childB }}

registers:
""" + registers + ("\nregisterConnections:\n" + connections if connections else "") + memories)


def _two_owner_arch(reg_x, reg_y, conn_x, conn_y, structure_y='cfgRegSt'):
    """childA is instanced in both ownerX and ownerY, and each owner gives it a
    register named cfg."""
    return PREAMBLE.rstrip() + """

blocks:
""" + render_plain_block('top') + render_router('apbDecode', 'top') + render_leaf('ownerX') \
        + render_leaf('ownerY', port_name='regsY') + render_plain_block('childA') + f"""
instances:
    uTop:       {{ container: top, instanceType: top }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uX:         {{ container: top, instanceType: ownerX, addressGroup: top }}
    uY:         {{ container: top, instanceType: ownerY, addressGroup: top }}
    uAx0:       {{ container: ownerX, instanceType: childA }}
    uAx1:       {{ container: ownerX, instanceType: childA }}
    uAy:        {{ container: ownerY, instanceType: childA }}

registers:
    - {{ register: cfg, block: ownerX, structure: cfgRegSt, {reg_x}, desc: "x" }}
    - {{ register: cfg, block: ownerY, structure: {structure_y}, {reg_y}, desc: "y" }}

registerConnections:
    - {{ register: cfg, block: ownerX, instance: uAx0{conn_x[0]} }}
    - {{ register: cfg, block: ownerX, instance: uAx1{conn_x[1]} }}
    - {{ register: cfg, block: ownerY, instance: uAy{conn_y} }}
"""


def _instance_port_arch():
    """owner gives arr whole to uB and maps its own port side to uB's port
    arr_1, which is the name of arr's element 1."""
    return PREAMBLE.rstrip() + """
    cfgStream:
        desc: "cfg stream"
        interfaceType: rdy_vld
        structures:
            - { structure: cfgRegSt, structureType: data_t }

blocks:
""" + render_plain_block('top') + render_router('apbDecode', 'top') + render_leaf('owner') \
        + render_plain_block('childB') + render_plain_block('srcBlk') + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uOwner:     { container: top, instanceType: owner, addressGroup: top }
    uX:         { container: top, instanceType: srcBlk }
    uB:         { container: owner, instanceType: childB }

connections:
    - { interface: cfgStream, src: uX, dst: uOwner, dstport: side }

connectionMaps:
    - { interface: cfgStream, block: owner, port: side, direction: dst, instance: uB, instancePort: arr_1 }

registers:
    - { register: arr, regType: rw, block: owner, structure: cfgRegSt, count: 2, desc: "array" }

registerConnections:
    - { register: arr, block: owner, instance: uB }
"""


def _owner_port_arch():
    """owner uses arr itself, with no registerConnections row, and takes a
    connection on its own port arr_1, the name of arr's element 1."""
    return PREAMBLE.rstrip() + """
    cfgStream:
        desc: "cfg stream"
        interfaceType: rdy_vld
        structures:
            - { structure: cfgRegSt, structureType: data_t }

blocks:
""" + render_plain_block('top') + render_router('apbDecode', 'top') + render_leaf('owner') \
        + render_plain_block('srcBlk') + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uOwner:     { container: top, instanceType: owner, addressGroup: top }
    uX:         { container: top, instanceType: srcBlk }

connections:
    - { interface: cfgStream, src: uX, dst: uOwner, dstport: arr_1 }

registers:
    - { register: arr, regType: rw, block: owner, structure: cfgRegSt, count: 2, desc: "array" }
"""


def _reg(name, reg_type='rw', extra=''):
    return (f'    - {{ register: {name}, regType: {reg_type}, block: owner, '
            f'structure: cfgRegSt{extra}, desc: "register {name}" }}\n')


def _conn(reg, inst, index=None):
    idx = '' if index is None else f', index: {index}'
    return f'    - {{ register: {reg}, block: owner, instance: {inst}{idx} }}\n'


def _run_same_named_structures():
    """ownerX and ownerY each declare their own structure pSt, in x.yaml and
    y.yaml, and give childA a register cfg of it. The diagnostic names both
    files, since the two structures print alike by name."""
    leaf = "        value: { varType: cfgT, generator: register }\n"
    owner = """include:
    - common.yaml

structures:
    pSt:
""" + leaf + """
blocks:
%s
instances:
    u%s0: { container: %s, instanceType: childA }

registers:
    - { register: cfg, regType: rw, block: %s, structure: pSt, count: 2, desc: "cfg" }

registerConnections:
    - { register: cfg, block: %s, instance: u%s0 }
"""
    files = {
        'common.yaml': APB_PREAMBLE + "\nblocks:\n" + render_plain_block('childA'),
        'x.yaml': owner % (render_leaf('ownerX'), 'X', 'ownerX', 'ownerX', 'ownerX', 'X'),
        'y.yaml': owner % (render_leaf('ownerY', port_name='regsY'), 'Y', 'ownerY', 'ownerY', 'ownerY', 'Y'),
        'top.yaml': "include:\n    - x.yaml\n    - y.yaml\n\nblocks:\n" + render_plain_block('top')
                    + render_router('apbDecode', 'top') + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uX:         { container: top, instanceType: ownerX, addressGroup: top }
    uY:         { container: top, instanceType: ownerY, addressGroup: top }
""",
    }
    return _run_project(
        "two same-named structures from different files on one child block's port is rejected", files,
        ["block 'childA' takes register port 'cfg' from two owners that disagree",
         "structure 'pSt' declared in x.yaml", "structure 'pSt' declared in y.yaml",
         "These are two different structures named 'pSt'."])


def _run_duplicate_across_files():
    """extra.yaml includes main.yaml and repeats main.yaml's row giving
    register arr to instance uB, with another index."""
    main = _arch(_reg('arr', extra=', count: 4'),
                 _conn('arr', 'uA0', 0) + _conn('arr', 'uA1', 1) + _conn('arr', 'uB', 0))
    extra = "include:\n    - main.yaml\n\nregisterConnections:\n" + _conn('arr', 'uB', 1)
    return _run_project(
        "a registerConnections row repeated in another file is rejected",
        {'main.yaml': main, 'extra.yaml': extra},
        ["extra.yaml", "register 'arr'", "instance 'uB'", "repeats the entry at main.yaml"])


def _run_project(label, files, needles):
    """Build the named files as one project in a temporary directory and
    expect make db to reject it with every needle in the diagnostic."""
    project_dir = tempfile.mkdtemp(prefix='regarray_', dir=test_dir)
    try:
        for name, content in files.items():
            with open(os.path.join(project_dir, name), 'w') as f:
                f.write(content)
        project = os.path.join(project_dir, 'project.yaml')
        with open(project, 'w') as f:
            f.write("yamlFormat: 2\nprojectName: regarray\ntopInstance: uTop\n\ndirs:\n    root: .\n\n"
                    "addressObjects:\n    registers:\n        alignment: 8\n\nprojectFiles:\n"
                    + ''.join(f"    - {name}\n" for name in files))
        result = run_arch2code(project, os.path.join(project_dir, 'project.db'))
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            print(f"FAIL: {label}: arch2code.py succeeded unexpectedly")
            return False
        missing = [n for n in needles if n not in combined]
        if missing:
            print(f"FAIL: {label}: diagnostic lacks {missing}\n{combined}")
            return False
        print(f"PASS: {label}")
        return True
    finally:
        shutil.rmtree(project_dir)


def _run_case(label, arch, expect_success, needles=(), block='owner', absent=()):
    label = f"{label} {'builds' if expect_success else 'is rejected'}"
    try:
        result = build_database(arch, expect_success=expect_success)
    except RuntimeError as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    db_path, project_path, arch_paths = result[:3]
    try:
        if not expect_success:
            combined = result[3].stdout + result[3].stderr
            missing = [n for n in [os.path.basename(arch_paths[0]), f"block '{block}'", *needles]
                       if n not in combined]
            if 'Duplicate flat key' in combined:
                missing.append("no internal 'Duplicate flat key' error")
            missing += [f"no '{n}'" for n in absent if n in combined]
            if missing:
                print(f"FAIL: {label}: diagnostic lacks {missing}\n{combined}")
                return False
        print(f"PASS: {label}")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


IP_PARAMS = """ipParameters:
    constants:
        N_PARAM: { value: 2, maxValue: 4, desc: "parameterizable array size" }

"""


def run_all_tests():
    cases = [
        # count itself
        ("count 0", _arch(_reg('arr', extra=', count: 0'), ''), False,
         ["register 'arr'", "count: 0", "at least 1"]),
        ("a parameterizable count constant",
         _arch(_reg('arr', extra=', count: N_PARAM'), '', ip_params=IP_PARAMS), False,
         ["register 'arr'", "count: N_PARAM, a parameterizable constant"]),
        ("a block parameter count",
         _arch(_reg('arr', extra=', count: N_PARAM'), '', ip_params=IP_PARAMS, owner_param=True), False,
         ["register 'arr'", "count: N_PARAM, a parameter of block 'owner'"]),
        ("count on a regType: memory register",
         _arch(_reg('mem', 'memory', ', wordLines: 4, addressStruct: apbAddrSt, count: 2'), ''), False,
         ["register 'mem'", "regType: memory register and sets count", "remove count"]),
        # index
        ("index on a register without count",
         _arch(_reg('scalar'), _conn('scalar', 'uA0', 0) + _conn('scalar', 'uA1', 1)), False,
         ["register 'scalar'", "instance 'uA0'", "declares no count"]),
        ("index 2 on a two-element array",
         _arch(_reg('arr', extra=', count: N_FIXED'), _conn('arr', 'uA0', 0) + _conn('arr', 'uA1', 2)), False,
         ["register 'arr'", "instance 'uA1'", "index must be an integer from 0 to 1"]),
        ("a parameterizable index constant",
         _arch(_reg('arr', extra=', count: 4'), _conn('arr', 'uB', 'N_PARAM'), ip_params=IP_PARAMS), False,
         ["register 'arr'", "instance 'uB'", "index: N_PARAM, a parameterizable constant"]),
        ("a duplicate registerConnections row",
         _arch(_reg('arr', extra=', count: 4'), _conn('arr', 'uB', 0) + _conn('arr', 'uB', 1)), False,
         ["register 'arr'", "instance 'uB'", "repeats the entry", "Remove one of the two entries"]),
        # rule 1: one form per child block, every instance included
        ("index and whole rows within one child block",
         _arch(_reg('arr', extra=', count: 4'), _conn('arr', 'uA0', 0) + _conn('arr', 'uA1')), False,
         ["register 'arr'", "block 'childA'", "two forms", "an index, or none"]),
        ("an array connected to one of two instances of a block",
         _arch(_reg('arr', extra=', count: 4'), _conn('arr', 'uA0', 0)), False,
         ["register 'arr'", "block 'childA'", "uA1", "add a registerConnections row for uA1"]),
        ("a scalar connected to one of two instances of a block",
         _arch(_reg('scalar'), _conn('scalar', 'uA1')), False,
         ["register 'scalar'", "block 'childA'", "uA0", "add a registerConnections row for uA0"]),
        # rule 2: an ro or ext element has one consumer
        ("an ro element given to two instances",
         _arch(_reg('arr', 'ro', ', count: 2'), _conn('arr', 'uA0', 0) + _conn('arr', 'uA1', 0)), False,
         ["register 'arr'", "element 0 goes to instances uA0, uA1", "Give element 0 to one instance"]),
        ("an ro array with an element no row covers",
         _arch(_reg('arr', 'ro', ', count: 3'), _conn('arr', 'uA0', 0) + _conn('arr', 'uA1', 2)), False,
         ["register 'arr'", "element(s) 1 of the ro array have no index row"]),
        ("a whole ext array given to two instances",
         _arch(_reg('arr', 'ext', ', count: 2'), _conn('arr', 'uA0') + _conn('arr', 'uA1')), False,
         ["register 'arr'", "uA0, uA1 each take the whole ext array"]),
        ("an ext array given whole to one block and by element to another",
         _arch(_reg('arr', 'ext', ', count: 2'), _conn('arr', 'uB') + _conn('arr', 'uA0', 0) + _conn('arr', 'uA1', 1)),
         False, ["register 'arr'", "takes the whole ext array", "takes an element of it"]),
        ("a scalar ro register given to two instances",
         _arch(_reg('status', 'ro'), _conn('status', 'uA0') + _conn('status', 'uA1')), False,
         ["register 'status'", "uA0, uA1 each take the ro register", "Connect it to one instance"]),
        ("a scalar ext register given to two blocks",
         _arch(_reg('cmd', 'ext'), _conn('cmd', 'uB') + _conn('cmd', 'uA0') + _conn('cmd', 'uA1')), False,
         ["register 'cmd'", "uB, uA0, uA1 each take the ext register"]),
        # one register port per child block, whichever owner feeds it
        ("an ro element and a whole rw array on one child block's port",
         _two_owner_arch('regType: ro, count: 2', 'regType: rw, count: 4', (', index: 0', ', index: 1'), ''), False,
         ["block 'childA' takes register port 'cfg' from two owners that disagree",
          "block 'ownerX' gives it one element of a 2-element array, regType ro",
          "block 'ownerY' gives it a whole 4-element array, regType rw"], 'childA'),
        ("one child block's port fed one element by one owner and the whole array by another",
         _two_owner_arch('regType: rw, count: 2', 'regType: rw, count: 2', (', index: 0', ', index: 1'), ''), False,
         ["block 'ownerX' gives it one element of a 2-element array, regType rw",
          "block 'ownerY' gives it a whole 2-element array, regType rw"], 'childA'),
        ("one child block's port fed arrays of two structures",
         _two_owner_arch('regType: rw, count: 2', 'regType: rw, count: 2', ('', ''), '', structure_y='apbDataSt'),
         False, ["takes register port 'cfg' from two owners that disagree",
                 "structure 'cfgRegSt'", "structure 'apbDataSt'"], 'childA', ["declared in"]),
        ("one child block's port fed a scalar by one owner and an array by another",
         _two_owner_arch('regType: rw', 'regType: rw, count: 2', ('', ''), ''), False,
         ["block 'ownerX' gives it a scalar", "block 'ownerY' gives it a whole 2-element array"], 'childA'),
        # firmware define names
        ("an array whose _STRIDE define is another register's define",
         _arch(_reg('arr', extra=', count: 2') + _reg('ARR_stride'), ''), False,
         ["register 'arr'", "REG_OWNER_ARR_STRIDE", "register 'ARR_stride'", "Rename one of them"]),
        ("an array whose _COUNT define is a regAccess memory's define",
         _arch(_reg('arr', extra=', count: 2'), '', memories="""
memories:
    - { memory: arr_count, block: owner, structure: cfgRegSt, addressStruct: apbAddrSt, wordLines: 4, regAccess: rw, desc: "table" }
"""), False, ["register 'arr'", "REG_OWNER_ARR_COUNT", "memory 'arr_count'"]),
        # element names
        ("an array element named like another register",
         _arch(_reg('arr', extra=', count: 2') + _reg('arr_1'), ''), False,
         ["array register 'arr'", "element 1 'arr_1'", "register 'arr_1'", "Rename one of them"]),
        ("an array element named like a regAccess memory",
         _arch(_reg('arr', extra=', count: 2'), '', memories="""
memories:
    - { memory: arr_0, block: owner, structure: cfgRegSt, addressStruct: apbAddrSt, wordLines: 4, regAccess: rw, desc: "table" }
"""), False, ["array register 'arr'", "element 0 'arr_0'", "memory 'arr_0'"]),
        ("an array element named like a port of a block taking the whole array",
         _arch(_reg('arr', extra=', count: 2'), _conn('arr', 'uB'), memories="""
connections:
    - { interface: apbReg, src: uA0, dst: uB, dstport: arr_1 }
"""), False, ["array register 'arr'", "element 1 'arr_1'", "port 'arr_1' of block 'childB'"]),
        ("an array element named like a child's connectionMap port, on a block taking the whole array",
         _instance_port_arch(), False,
         ["array register 'arr'", "element 1 'arr_1'", "port 'arr_1' of block 'childB'"]),
        # accepted forms
        ("an rw array taken whole by one block and by element by another",
         _arch(_reg('arr', extra=', count: N_FIXED'), _conn('arr', 'uB') + _conn('arr', 'uA0', 1) + _conn('arr', 'uA1', 1)),
         True, []),
        ("an ro array split by element across one block's instances",
         _arch(_reg('arr', 'ro', ', count: 2'), _conn('arr', 'uA0', 1) + _conn('arr', 'uA1', 0)), True, []),
        ("a scalar ro register given to one instance",
         _arch(_reg('status', 'ro'), _conn('status', 'uB')), True, []),
        ("an index named by a constant",
         _arch(_reg('arr', extra=', count: 4'), _conn('arr', 'uB', 'N_FIXED')), True, []),
        ("one child block's port fed alike by two owners",
         _two_owner_arch('regType: rw, count: 2', 'regType: rw, count: 2', ('', ''), ''), True, []),
        ("a register named past the last element",
         _arch(_reg('arr', extra=', count: 2') + _reg('arr_2'), ''), True, []),
        ("an array register beside a memoryConnections row with no instance",
         _arch(_reg('arr', extra=', count: 2'), _conn('arr', 'uB'), memories="""
memories:
    - { memory: tbl, block: owner, structure: cfgRegSt, addressStruct: apbAddrSt, wordLines: 4, ports: [p0], desc: "table" }

memoryConnections:
    - { memory: tbl, block: owner, port: p0 }
"""), True, []),
        ("an owner port named arr_1 beside a form-1 arr", _owner_port_arch(), True, []),
        ("a count of 1",
         _arch(_reg('arr', 'ext', ', count: 1'), _conn('arr', 'uB')), True, []),
    ]
    results = [_run_case(*case) for case in cases] + [_run_same_named_structures(), _run_duplicate_across_files()]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
