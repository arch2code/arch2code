#!/usr/bin/env python3
"""Generation and rejection checks for memory port assignment.

A memory's memoryType fixes what each of its ports allows, and regAccess
puts the register handler on one of them. These checks build a small design
with one memory per memoryType, without regAccess and with each firmware
access mode (true, ro, wo), render the
owning blocks' RTL and assert on the generated memory_if declarations and
memory instances: the PORTA_READ_ONLY / PORTB_WRITE_ONLY parameters, which
port carries <memory>_reg, the ports: list filling the block-side ports in
order, and the single clock bind. Rejection fixtures cover regAccess on a
memoryType with no read/write port, and memories that list more ports than
are left for the block once the register handler takes its port.

Fixtures are written outside the repository working tree, the same way
test_clock_reset_emission.py writes its own.
"""

import difflib
import os
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from _addrctl_helpers import APB_PREAMBLE, render_leaf, render_plain_block, render_router
from pysrc.memoryPortAccess import MEMORY_PORT_ACCESS, memoryRegisterPort

ARCH2CODE = os.path.join(base_dir, 'arch2code.py')

PROJECT = """yamlFormat: 2
projectName: memPorts
topInstance: uTop

projectFiles:
    - ../../yaml/shared.yaml
    - ../../yaml/top.yaml

dirs:
    root: ../..

instanceGroups:
    top:
        varType: inst_top
        enumPrefix: INST_TOP_

addressObjects:
    memories:  { alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true }
    registers: { alignment: 8, sortDescending: true }

fileGeneration:
    layout: hierarchical
    template: $a2c/templates/fileGen/fileGen.py
"""

DESIGN = """include:
    - shared.yaml

constants:
    TBL_WORDS: {{ value: 8, desc: "memory wordlines" }}

types:
    memAddrT: {{ width: 3, desc: "memory address" }}

structures:
    memAddrSt:
        address: {{ varType: memAddrT, generator: address, desc: "memory address" }}
    memSt:
        data: {{ varType: cfgT, generator: memory, desc: "memory payload" }}

blocks:
{blocks}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}
    uRd:        {{ container: top, instanceType: rd }}
    uWr:        {{ container: top, instanceType: wr }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

registers:
    - {{ register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "leafA configuration" }}

memories:
{memories}
memoryConnections:
{memoryConnections}"""

BLOCKS = (render_plain_block('top') + render_plain_block('cpu')
          + render_router('apbDecode', 'top') + render_leaf('leafA')
          + render_plain_block('rd') + render_plain_block('wr'))


def _mem(name, block, extra):
    return (f"    - {{ memory: {name}, block: {block}, structure: memSt, addressStruct: memAddrSt, "
            f"wordLines: TBL_WORDS, desc: \"{name}\"{extra} }}\n")


# Firmware-accessible memories live on the routed leaf, block-only ones on
# the container, where memoryConnections reach the uRd/uWr instances.
LEAF_MEMORIES = (
    _mem('spReg', 'leafA', ', memoryType: singlePort, regAccess: true')
    + _mem('dpReg', 'leafA', ', memoryType: dualPort, regAccess: true, ports: [p]')
    + _mem('dpRegBare', 'leafA', ', regAccess: true')
    + _mem('rRwReg', 'leafA', ', memoryType: portRportRW, regAccess: true, ports: [p]')
    + _mem('rwWReg', 'leafA', ', memoryType: portRWportW, regAccess: true, ports: [p]')
    + _mem('rwWLocalReg', 'leafA', ', memoryType: portRWportW, regAccess: true, local: true, ports: [p]')
    # Every memoryType with ro and with wo, which regAccess: true never selects.
    + _mem('dpRo', 'leafA', ', memoryType: dualPort, regAccess: ro, ports: [p]')
    + _mem('dpWo', 'leafA', ', memoryType: dualPort, regAccess: wo, ports: [p]')
    + _mem('rRwRo', 'leafA', ', memoryType: portRportRW, regAccess: ro, ports: [p]')
    + _mem('rRwWo', 'leafA', ', memoryType: portRportRW, regAccess: wo, ports: [p]')
    + _mem('rwWRo', 'leafA', ', memoryType: portRWportW, regAccess: ro, ports: [p]')
    + _mem('rwWWo', 'leafA', ', memoryType: portRWportW, regAccess: wo, ports: [p]')
    + _mem('rWRo', 'leafA', ', memoryType: portRportW, regAccess: ro, ports: [p]')
    + _mem('rWWo', 'leafA', ', memoryType: portRportW, regAccess: wo, ports: [p]')
    + _mem('spRo', 'leafA', ', memoryType: singlePort, regAccess: ro')
    + _mem('spWo', 'leafA', ', memoryType: singlePort, regAccess: wo'))


def _top_memories(rdWrOrder):
    ports = ', '.join(rdWrOrder)
    return (_mem('sp', 'top', ', memoryType: singlePort, ports: [p]')
            + _mem('dp', 'top', f', memoryType: dualPort, ports: [{ports}]')
            + _mem('dpBare', 'top', '')
            + _mem('rRw', 'top', f', memoryType: portRportRW, ports: [{ports}]')
            + _mem('rwW', 'top', f', memoryType: portRWportW, ports: [{ports}]')
            + _mem('rW', 'top', f', memoryType: portRportW, ports: [{ports}]')
            + _mem('rWLocal', 'top', f', memoryType: portRportW, local: true, ports: [{ports}]'))


def _memory_connections(reverse):
    rows = [f"    - {{ memory: {mem}, block: top, instance: {inst}, port: {port} }}\n"
            for mem in ('dp', 'rRw', 'rwW', 'rW')
            for inst, port in (('uRd', 'rd'), ('uWr', 'wr'))]
    return ''.join(reversed(rows) if reverse else rows)


def _design(leafMemories=LEAF_MEMORIES, rdWrOrder=('rd', 'wr'), reverseConnections=False):
    return DESIGN.format(blocks=BLOCKS,
                         memories=leafMemories + _top_memories(rdWrOrder),
                         memoryConnections=_memory_connections(reverseConnections))


def _arch2code(*args, cwd):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run([sys.executable, ARCH2CODE, *args],
                          capture_output=True, text=True, timeout=300,
                          cwd=cwd, env=env)


def _build(design):
    """Write the fixture and attempt its database build.

    Returns (fixture_dir, db_path, completed_process).
    """
    fixture = tempfile.mkdtemp(prefix='memports_')
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(PROJECT)
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(design)
    db = os.path.join(fixture, 'memPorts.db')
    built = _arch2code('--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'),
                       '--db', db, cwd=fixture)
    return fixture, db, built


def _generate(design):
    """Build the fixture and render top.sv and leafA.sv.

    Returns (fixture_dir, {relative path: emitted text}).
    """
    fixture, db, built = _build(design)
    if built.returncode != 0:
        raise AssertionError(f"database build failed:\n{built.stdout}\n{built.stderr}")
    made = _arch2code('--db', db, '-r', '--newmodule', cwd=fixture)
    if made.returncode != 0:
        raise AssertionError(f"newmodule failed:\n{made.stdout}\n{made.stderr}")
    emitted = dict()
    for rel in ('rtl/top.sv', 'rtl/leafA.sv'):
        gen = _arch2code('--db', db, '-r', '--systemVerilog',
                         '--file', os.path.join(fixture, rel), cwd=fixture)
        if gen.returncode != 0:
            raise AssertionError(f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
        with open(os.path.join(fixture, rel)) as f:
            emitted[rel] = f.read()
    return fixture, emitted


def _run_case(label, fn):
    try:
        fn()
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    print(f"PASS: {label}")
    return True


_INSTANCE = re.compile(r'^(memory_\w+) #\((.*)\) (u\w+) \($', re.M)


def _memory_instance(text, memory, where):
    """Returns (module, parameter text, [(port, signal)...]) of the memory's
    instance, in emitted order."""
    instName = 'u' + memory[0].upper() + memory[1:]
    for match in _INSTANCE.finditer(text):
        if match.group(3) != instName:
            continue
        body = text[match.end():text.index(');', match.end())]
        binds = re.findall(r'\.(\w+) \((\w+)\)', body)
        return match.group(1), match.group(2), binds
    raise AssertionError(f"{where} has no instance {instName}:\n{text}")


def _interfaces(text, memory):
    return re.findall(rf'memory_if #\(.*\) ({memory}(?:_\w+)?)\(\);', text)


# (file, memory, module, PORTA_READ_ONLY, PORTB_WRITE_ONLY, binds, clock)
# binds lists (port, signal) in emitted order, clocks excluded; a None
# parameter pair is a single-port memory, which takes neither.
EXPECTED = (
    ('rtl/leafA.sv', 'spReg', 'memory_sp', None, None, [('mem_port', 'spReg_reg')], 'clk'),
    ('rtl/leafA.sv', 'dpReg', 'memory_dp', 0, 0, [('mem_portA', 'dpReg_p'), ('mem_portB', 'dpReg_reg')], 'clk'),
    ('rtl/leafA.sv', 'dpRegBare', 'memory_dp', 0, 0, [('mem_portA', 'dpRegBare'), ('mem_portB', 'dpRegBare_reg')], 'clk'),
    ('rtl/leafA.sv', 'rRwReg', 'memory_dp', 1, 0, [('mem_portA', 'rRwReg_p'), ('mem_portB', 'rRwReg_reg')], 'clk'),
    ('rtl/leafA.sv', 'rwWReg', 'memory_dp', 0, 1, [('mem_portA', 'rwWReg_reg'), ('mem_portB', 'rwWReg_p')], 'clk'),
    ('rtl/leafA.sv', 'rwWLocalReg', 'memory_dp_ext', 0, 1,
     [('mem_portA', 'rwWLocalReg_reg'), ('mem_portB', 'rwWLocalReg_p'), ('mem', 'rwWLocalRegMem')], 'clk'),
    ('rtl/leafA.sv', 'dpRo', 'memory_dp', 0, 0, [('mem_portA', 'dpRo_p'), ('mem_portB', 'dpRo_reg')], 'clk'),
    ('rtl/leafA.sv', 'dpWo', 'memory_dp', 0, 0, [('mem_portA', 'dpWo_p'), ('mem_portB', 'dpWo_reg')], 'clk'),
    ('rtl/leafA.sv', 'rRwRo', 'memory_dp', 1, 0, [('mem_portA', 'rRwRo_reg'), ('mem_portB', 'rRwRo_p')], 'clk'),
    ('rtl/leafA.sv', 'rRwWo', 'memory_dp', 1, 0, [('mem_portA', 'rRwWo_p'), ('mem_portB', 'rRwWo_reg')], 'clk'),
    ('rtl/leafA.sv', 'rwWRo', 'memory_dp', 0, 1, [('mem_portA', 'rwWRo_reg'), ('mem_portB', 'rwWRo_p')], 'clk'),
    ('rtl/leafA.sv', 'rwWWo', 'memory_dp', 0, 1, [('mem_portA', 'rwWWo_p'), ('mem_portB', 'rwWWo_reg')], 'clk'),
    ('rtl/leafA.sv', 'rWRo', 'memory_dp', 1, 1, [('mem_portA', 'rWRo_reg'), ('mem_portB', 'rWRo_p')], 'clk'),
    ('rtl/leafA.sv', 'rWWo', 'memory_dp', 1, 1, [('mem_portA', 'rWWo_p'), ('mem_portB', 'rWWo_reg')], 'clk'),
    ('rtl/leafA.sv', 'spRo', 'memory_sp', None, None, [('mem_port', 'spRo_reg')], 'clk'),
    ('rtl/leafA.sv', 'spWo', 'memory_sp', None, None, [('mem_port', 'spWo_reg')], 'clk'),
    ('rtl/top.sv', 'sp', 'memory_sp', None, None, [('mem_port', 'sp_p')], 'clk'),
    ('rtl/top.sv', 'dp', 'memory_dp', 0, 0, [('mem_portA', 'dp_rd'), ('mem_portB', 'dp_wr')], 'clk'),
    ('rtl/top.sv', 'dpBare', 'memory_dp', 0, 0, [('mem_portA', 'dpBare'), ('mem_portB', 'dpBare_unused')], 'clk'),
    ('rtl/top.sv', 'rRw', 'memory_dp', 1, 0, [('mem_portA', 'rRw_rd'), ('mem_portB', 'rRw_wr')], 'clk'),
    ('rtl/top.sv', 'rwW', 'memory_dp', 0, 1, [('mem_portA', 'rwW_rd'), ('mem_portB', 'rwW_wr')], 'clk'),
    ('rtl/top.sv', 'rW', 'memory_dp', 1, 1, [('mem_portA', 'rW_rd'), ('mem_portB', 'rW_wr')], 'clk'),
    ('rtl/top.sv', 'rWLocal', 'memory_dp_ext', 1, 1,
     [('mem_portA', 'rWLocal_rd'), ('mem_portB', 'rWLocal_wr'), ('mem', 'rWLocalMem')], 'clk'),
)


def check_memory_instance(emitted, rel, memory, module, aRo, bWo, binds, clock):
    text = emitted[rel]
    gotModule, params, gotBinds = _memory_instance(text, memory, rel)
    if gotModule != module:
        raise AssertionError(f"{memory} instantiates {gotModule}, expected {module}")
    expectedParams = ".DEPTH(TBL_WORDS), .data_t(memSt)"
    if aRo is not None:
        expectedParams += f", .PORTA_READ_ONLY(1'b{aRo}), .PORTB_WRITE_ONLY(1'b{bWo})"
    if params != expectedParams:
        raise AssertionError(f"{memory} parameters are {params!r}, expected {expectedParams!r}")
    if gotBinds != binds + [('clk', clock)]:
        raise AssertionError(f"{memory} binds are {gotBinds}, expected {binds + [('clk', clock)]}")
    declared = _interfaces(text, memory)
    signals = [signal for port, signal in binds if port != 'mem']
    if declared != signals:
        raise AssertionError(f"{memory} declares memory_if {declared}, expected {signals} "
                             f"in A-then-B order")


def check_ports_order_is_ab_assignment(emitted, swapped):
    """Swapping each block-only memory's ports: list swaps its A/B
    assignment. The only lines that change are memory_if declarations and
    mem_portA/mem_portB binds."""
    for rel in ('rtl/top.sv', 'rtl/leafA.sv'):
        changed = [line for line in difflib.unified_diff(
                       emitted[rel].splitlines(), swapped[rel].splitlines(), lineterm='', n=0)
                   if line[:1] in '+-' and not line.startswith(('+++', '---'))]
        other = [line for line in changed
                 if not re.match(r'^[+-]\s*(memory_if #|\.mem_port[AB] )', line)]
        if other:
            raise AssertionError(f"{rel} with ports: [wr, rd] changes lines other than the "
                                 f"A/B assignment:\n" + '\n'.join(other))
    for memory in ('dp', 'rRw', 'rwW', 'rW', 'rWLocal'):
        _, _, binds = _memory_instance(swapped['rtl/top.sv'], memory, 'rtl/top.sv')
        if binds[:2] != [('mem_portA', f'{memory}_wr'), ('mem_portB', f'{memory}_rd')]:
            raise AssertionError(f"{memory} with ports: [wr, rd] binds {binds[:2]}, "
                                 f"expected wr on A and rd on B")


def _memory_section(text):
    """The memory_if declarations and memory instances. The child instance
    binds of memoryConnections follow row order and are outside this check."""
    return (re.findall(r'^\s*memory_if #.*$', text, re.M)
            + [text[m.start():text.index(');', m.end())] for m in _INSTANCE.finditer(text)])


def check_connection_order_does_not_change_memories(emitted, reordered):
    for rel in ('rtl/top.sv', 'rtl/leafA.sv'):
        if _memory_section(emitted[rel]) != _memory_section(reordered[rel]):
            raise AssertionError(f"{rel} memory declarations or instances change when the "
                                 f"memoryConnections rows are reversed")


# The register port per memoryType and firmware access mode. None is a mode
# no port of the memory allows; '' is a single-port memory's one port.
REGISTER_PORT_TABLE = {
    'dualPort':    {'rw': 'B', 'ro': 'B', 'wo': 'B'},
    'portRportRW': {'rw': 'B', 'ro': 'A', 'wo': 'B'},
    'portRWportW': {'rw': 'A', 'ro': 'A', 'wo': 'B'},
    'portRportW':  {'rw': None, 'ro': 'A', 'wo': 'B'},
    'singlePort':  {'rw': '', 'ro': '', 'wo': ''},
}


def check_register_port_table():
    wrong = [f"{memoryType}/{mode}: got {memoryRegisterPort(memoryType, mode)[0]!r}, expected {port!r}"
             for memoryType, modes in REGISTER_PORT_TABLE.items()
             for mode, port in modes.items()
             if memoryRegisterPort(memoryType, mode)[0] != port]
    wrong += [f"{memoryType}/no access: got a register port"
              for memoryType in REGISTER_PORT_TABLE
              if memoryRegisterPort(memoryType, False)[0] is not None]
    if wrong:
        raise AssertionError('; '.join(wrong))


def _expect_rejected(design, needles):
    fixture, db, built = _build(design)
    try:
        output = built.stdout + built.stderr
        if built.returncode == 0:
            raise AssertionError(f"database build succeeded; expected a rejection:\n{output}")
        if 'Traceback' in output:
            raise AssertionError(f"rejection is a traceback, not a diagnostic:\n{output}")
        for needle in needles:
            if needle not in output:
                raise AssertionError(f"diagnostic does not mention {needle!r}:\n{output}")
    finally:
        shutil.rmtree(fixture)


def run_regaccess_without_rw_port_rejected():
    _expect_rejected(
        _design(leafMemories=LEAF_MEMORIES + _mem('rWReg', 'leafA',
                                                  ', memoryType: portRportW, regAccess: true, ports: [p]')),
        ["memory 'rWReg'", "block 'leafA'", "has regAccess: rw, which needs a port that can both "
         "read and write, and no port of a portRportW memory does. Change memoryType or regAccess."])


# (memory, owning block, memory row fields, listed, available, fix): each
# lists more ports than the memory leaves for its block.
OVER_LISTED = (
    ('dpRegTwo', 'leafA', 'memoryType: dualPort, regAccess: true, ports: [rd, wr]', 2, 1,
     "List at most 1 port, or remove regAccess."),
    ('rRwRegTwo', 'leafA', 'memoryType: portRportRW, regAccess: true, ports: [rd, wr]', 2, 1,
     "List at most 1 port, or remove regAccess."),
    ('spRegOne', 'leafA', 'memoryType: singlePort, regAccess: true, ports: [q]', 1, 0,
     "Remove the ports list, or use a dual-port memoryType, or remove regAccess."),
    ('spTwo', 'top', 'memoryType: singlePort, ports: [a, b]', 2, 1,
     "List at most 1 port, or use a dual-port memoryType."),
    # Three ports do not fit a dual-port memory either, so the fix offers none.
    ('spThree', 'top', 'memoryType: singlePort, ports: [a, b, c]', 3, 1,
     "has 1 port. List at most 1 port."),
    ('dpThree', 'top', 'memoryType: dualPort, ports: [a, b, c]', 3, 2,
     "List at most 2 ports."),
)


def run_over_listed_ports_rejected(memory, block, fields, listed, available, fix):
    _expect_rejected(
        _design(leafMemories=LEAF_MEMORIES + _mem(memory, block, ', ' + fields)),
        [f"memory '{memory}' of block '{block}' lists {listed} port{'' if listed == 1 else 's'} (",
         f"but has {available} free.", fix])


def check_schema_memory_types_have_port_access():
    """Every memoryType the schema accepts has a MEMORY_PORT_ACCESS row."""
    with open(os.path.join(base_dir, 'config', 'schema.yaml')) as f:
        schema = yaml.safe_load(f)
    values = schema['memories']['memoryType']['_validate']['values']
    missing = [value for value in values if value not in MEMORY_PORT_ACCESS]
    if missing:
        raise AssertionError(f"config/schema.yaml accepts memoryType {missing}, which "
                             f"pysrc/memoryPortAccess.py MEMORY_PORT_ACCESS has no row for; "
                             f"add the port access of each")


def main():
    print("=" * 72)
    print("memory port assignment")
    print("=" * 72)
    ok = [_run_case("every schema memoryType has a port access row",
                    check_schema_memory_types_have_port_access),
          _run_case("the register port follows the selection rule for every memoryType and mode",
                    check_register_port_table)]
    fixture, emitted = _generate(_design())
    try:
        for rel, memory, module, aRo, bWo, binds, clock in EXPECTED:
            ok.append(_run_case(
                f"{memory} ({rel}) instantiates {module} with the expected parameters and ports",
                lambda rel=rel, memory=memory, module=module, aRo=aRo, bWo=bWo, binds=binds,
                clock=clock: check_memory_instance(emitted, rel, memory, module, aRo, bWo,
                                                   binds, clock)))
    finally:
        shutil.rmtree(fixture)

    swappedFixture, swapped = _generate(_design(rdWrOrder=('wr', 'rd')))
    try:
        ok.append(_run_case("ports: list order is the A/B assignment and nothing else",
                            lambda: check_ports_order_is_ab_assignment(emitted, swapped)))
    finally:
        shutil.rmtree(swappedFixture)

    reorderedFixture, reordered = _generate(_design(reverseConnections=True))
    try:
        ok.append(_run_case("memoryConnections row order does not change the memory ports",
                            lambda: check_connection_order_does_not_change_memories(emitted, reordered)))
    finally:
        shutil.rmtree(reorderedFixture)

    ok.append(_run_case("regAccess on portRportW, which has no read/write port, is rejected",
                        run_regaccess_without_rw_port_rejected))
    for row in OVER_LISTED:
        ok.append(_run_case(
            f"{row[0]} ({row[2]}) lists more ports than it has free and is rejected",
            lambda row=row: run_over_listed_ports_rejected(*row)))

    print()
    if all(ok):
        print("RESULT: all memory port assignment checks passed")
        return 0
    print(f"RESULT: {ok.count(False)} of {len(ok)} memory port assignment checks failed")
    return 1


if __name__ == '__main__':
    sys.exit(main())
