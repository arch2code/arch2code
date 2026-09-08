#!/usr/bin/env python3
"""Coverage for the clock domain of a generated register-decode tree.

A generated router and a generated `<block>_regs` handler are register-bus
endpoints, so they inherit the domain of the authored bus feed that reaches the
primary router rather than the domain of the block whose registers they serve.
The feed is the only input to that inheritance, so the first four cases author it
in a different place each: at the router instance, at the router's container
boundary, at the instance of the router's container block, and nowhere at all.

The fifth reaches the served leaf's register and memory from two other blocks, so
the leaf carries both its bus domain and theirs. The sixth is a composed build
whose child project does not declare the assembler's bus clock, which is what
forces every propagated clock to be respelled in the receiving row's own project.

Assertions are on the stored synthesised rows and on the derivation they drive,
never on the build merely succeeding: a build that synthesises nothing at all
succeeds too.

Fixtures are written OUTSIDE the repository working tree: git does not track
empty directories, so a fixture left under unittest/ is a stray directory
`git status` never reports. Cleanup deliberately does not suppress errors.
"""

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from _addrctl_helpers import APB_PREAMBLE, render_leaf, render_plain_block, render_router

# The assembler declares a second clock for the register bus; the composed child
# below declares only its own default, so a propagated `apbClk` cannot be spelled
# in the child's project.
ASSEMBLER_CLOCKS = """
clocks:
    clk:    { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    apbClk: { desc: "the register-bus clock", period: 4, timeUnit: ns }
    objClk: { desc: "the clock of the logic reaching a register or memory", period: 3, timeUnit: ns }
"""

CHILD_CLOCKS = """
clocks:
    clk: { desc: "the child's only clock", default: true, period: 1, timeUnit: ns }
"""

# One reset per clock: a block that authors no resets: list takes the reset of
# each domain it carries, and a generated handler or router - which can never
# author one - is exactly such a block. The assembler's three clocks therefore
# need three resets, while the child declares only its own default domain.
ASSEMBLER_RESETS = """
resets:
    rst_n:    { desc: "the default reset", default: true, clock: clk }
    apbRst_n: { desc: "the register-bus reset", clock: apbClk }
    objRst_n: { desc: "the reset of the logic reaching a register or memory", clock: objClk }
"""

CHILD_RESETS = """
resets:
    rst_n: { desc: "the child's only reset", default: true, clock: clk }
"""

PROJECT_TAIL = """
instanceGroups:
    top:
        varType: inst_top
        enumPrefix: INST_TOP_

addressObjects:
    memories:  { alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true }
    registers: { alignment: 8, sortDescending: true }
"""

ROUTER = render_router('apbDecode', 'top')
REGISTER = ("registers:\n"
            "    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, "
            "desc: \"leafA configuration\" }\n")

# Feed authored straight at the router instance: the standalone reusable-IP shape,
# whose APB master stub drives the router's upstream port directly.
FEED_AT_ROUTER = f"""include:
    - shared.yaml

blocks:
{render_plain_block('top')}{render_plain_block('cpu')}{ROUTER}{render_leaf('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode, clock: apbClk }}

{REGISTER}"""

# Feed authored as the boundary connectionMap that bridges the DUT's inherited
# upstream port inward to the router: the assembler shape. The outer master
# connection deliberately states no clock, so the case also pins which row the
# inheritance reads - the one that reaches the router, not the one behind it.
FEED_AT_BOUNDARY_MAP = f"""include:
    - shared.yaml

blocks:
{render_plain_block('top')}{render_plain_block('cpu')}{render_plain_block('dut')}{ROUTER}{render_leaf('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uDut:       {{ container: top, instanceType: dut }}
    uAPBDecode: {{ container: dut, instanceType: apbDecode }}
    uLeafA:     {{ container: dut, instanceType: leafA, addressGroup: top }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uDut }}

connectionMaps:
    - {{ interface: apbReg, block: dut, direction: dst, instance: uAPBDecode, clock: apbClk }}

{REGISTER}"""

# Feed authored at the instance of the router's container block. The container
# declares its register bus under registerPorts:, so its inward boundary map is
# the one this pass synthesises rather than an authored row, and the only authored
# feed is the master connection into the container instance.
#
# A non-register-bus stream into the same container instance is authored FIRST, in
# its own domain, so a search that did not filter on the interface being an
# address bus would pick it up instead.
FEED_AT_CONTAINER_INSTANCE = f"""include:
    - shared.yaml

structures:
    payloadSt:
        data: {{ varType: cfgT, desc: "stream payload" }}

interfaces:
    dataIf:
        desc: "a stream into the container that is not a register bus"
        interfaceType: push_ack
        structures:
            - {{ structure: payloadSt, structureType: data_t }}

blocks:
{render_plain_block('top')}{render_plain_block('cpu')}{render_plain_block('src')}{render_leaf('ipBlock', port_name='apbReg')}{ROUTER}{render_leaf('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uSrc:       {{ container: top, instanceType: src }}
    uIp:        {{ container: top, instanceType: ipBlock }}
    uAPBDecode: {{ container: ipBlock, instanceType: apbDecode }}
    uLeafA:     {{ container: ipBlock, instanceType: leafA, addressGroup: top }}

connections:
    - {{ interface: dataIf, src: uSrc, dst: uIp, dstport: dataIn, clock: objClk }}
    - {{ interface: apbReg, src: uCPU, dst: uIp, dstport: apbReg, clock: apbClk }}

{REGISTER}"""

# No authored feed at all, which is the shape of every addressBlock: fixture in
# unittest/: the decode tree has no bus domain to inherit.
NO_FEED = f"""include:
    - shared.yaml

blocks:
{render_plain_block('top')}{ROUTER}{render_leaf('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}

{REGISTER}"""

# A register and a memory of the routed leaf, each reached from a second block by
# its own connection-shaped section. The two accessors are deliberately separate
# blocks reached by exactly one section each and by nothing else, so a section
# missing from the derivation's walk costs a block its only domain.
OBJECT_ACCESS = f"""include:
    - shared.yaml

constants:
    TBL_WORDS: {{ value: 8, desc: "memory wordlines" }}

types:
    memAddrT: {{ width: 3, desc: "memory address" }}

structures:
    memSt:
        data: {{ varType: cfgT, desc: "memory payload" }}
    memAddrSt:
        address: {{ varType: memAddrT, desc: "memory address" }}

blocks:
{render_plain_block('top')}{render_plain_block('cpu')}{ROUTER}{render_leaf('leafA')}{render_plain_block('regAccessor')}{render_plain_block('memAccessor')}
instances:
    uTop:         {{ container: top, instanceType: top }}
    uCPU:         {{ container: top, instanceType: cpu }}
    uAPBDecode:   {{ container: top, instanceType: apbDecode }}
    uLeafA:       {{ container: top, instanceType: leafA, addressGroup: top }}
    uRegAccessor: {{ container: top, instanceType: regAccessor }}
    uMemAccessor: {{ container: top, instanceType: memAccessor }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode, clock: apbClk }}

{REGISTER}
memories:
    - {{ memory: tbl, block: leafA, structure: memSt, addressStruct: memAddrSt, wordLines: TBL_WORDS, ports: [p], desc: "leafA table" }}

registerConnections:
    - {{ register: cfgA, block: leafA, instance: uRegAccessor, clock: objClk }}

memoryConnections:
    - {{ memory: tbl, block: leafA, instance: uMemAccessor, port: p, clock: objClk }}
"""

# The composed assembler: the routed leaf is owned by the child project below.
COMPOSED_ASSEMBLER = f"""include:
    - shared.yaml
    - ../ip/yaml/childIp.yaml

blocks:
{render_plain_block('top')}{render_plain_block('cpu')}{ROUTER}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafIp:    {{ container: top, instanceType: leafIp, addressGroup: top }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode, clock: apbClk }}
"""

# The child project's own file. Its register is what makes this pass synthesise a
# handler and a handler bind INTO this file's context, which is the row that has
# to be respelled in the child's clocks.
COMPOSED_CHILD = f"""include:
    - ../../yaml/shared.yaml

blocks:
{render_leaf('leafIp')}
registers:
    - {{ register: cfgIp, regType: rw, block: leafIp, structure: cfgRegSt, desc: "leafIp configuration" }}
"""


def _make_fixture(design, child=None):
    """Write a design fixture into a fresh temp dir outside the repo tree.

    `child` adds a second project owning its own arch file, instantiated by the
    assembler, so synthesised rows land in two projects' contexts.

    Returns (fixture_dir, project_path, db_path).
    """
    fixture = tempfile.mkdtemp(prefix='regclk_')
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(design)

    projectFiles = ['    - ../../yaml/shared.yaml\n', '    - ../../yaml/top.yaml\n']
    if child is not None:
        os.makedirs(os.path.join(fixture, 'ip', 'prj', 'yaml'))
        os.makedirs(os.path.join(fixture, 'ip', 'yaml'))
        with open(os.path.join(fixture, 'ip', 'yaml', 'childIp.yaml'), 'w') as f:
            f.write(child)
        with open(os.path.join(fixture, 'ip', 'prj', 'yaml', 'childProject.yaml'), 'w') as f:
            f.write("yamlFormat: 2\n"
                    "projectName: childIp\n"
                    "\n"
                    "projectFiles:\n"
                    "    - ../../yaml/childIp.yaml\n"
                    f"{CHILD_CLOCKS}"
                    f"{CHILD_RESETS}"
                    "\n"
                    "dirs:\n"
                    "    root: ../..\n"
                    "\n"
                    # projectName + dirs + fileGeneration is the sentinel set that
                    # classifies a referenced file as a child project file.
                    "fileGeneration:\n"
                    "    template: $a2c/templates/fileGen/fileGen.py\n"
                    f"{PROJECT_TAIL}")
        projectFiles.insert(0, '    - ../../ip/prj/yaml/childProject.yaml\n')

    project_path = os.path.join(fixture, 'prj', 'yaml', 'project.yaml')
    with open(project_path, 'w') as f:
        f.write("yamlFormat: 2\n"
                "projectName: regClk\n"
                "topInstance: uTop\n"
                "\n"
                "projectFiles:\n"
                f"{''.join(projectFiles)}"
                f"{ASSEMBLER_CLOCKS}"
                f"{ASSEMBLER_RESETS}"
                "\n"
                "dirs:\n"
                "    root: ../..\n"
                f"{PROJECT_TAIL}")
    return fixture, project_path, os.path.join(fixture, 'project.db')


def _build(project_path, db_path):
    """Run one database build in a subprocess. Returns (returncode, output)."""
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    completed = subprocess.run(
        [sys.executable, os.path.join(base_dir, 'arch2code.py'),
         '--yaml', project_path, '--db', db_path],
        capture_output=True, text=True, timeout=300, env=env, cwd=test_dir)
    return completed.returncode, completed.stdout + completed.stderr


def _stored(db_path):
    """The stored register-bus wiring as three lookups.

    connections keyed (src, dst), connectionMaps keyed (block, instance), both
    giving (clock, clockKey); plus the derived clock set per block name.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        connections = {(r['src'], r['dst']): (r['clock'], r['clockKey'])
                       for r in conn.execute('select src, dst, clock, clockKey from connections')}
        maps = {(r['block'], r['instance']): (r['clock'], r['clockKey'])
                for r in conn.execute('select block, instance, clock, clockKey '
                                      'from connectionMaps')}
        blocks = {r['blockKey']: r['block']
                  for r in conn.execute('select block, blockKey from blocks')}
        derived = {name: [] for name in blocks.values()}
        for row in conn.execute("select blockKey, itemKey from blockClocksResets "
                                "where kind = 'clock' order by blockKey, orderIndex"):
            derived[blocks[row['blockKey']]].append(row['itemKey'])
        return connections, maps, derived
    finally:
        conn.close()


def _case(label, design, expected, child=None):
    """Build one fixture and assert every entry of `expected` against it.

    `expected` maps a description of one stored row to (lookup, key, value),
    where lookup names which of the three stored lookups to read.
    """
    fixture, project_path, db_path = _make_fixture(design, child=child)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        connections, maps, derived = _stored(db_path)
        lookups = {'connection': connections, 'map': maps, 'derived': derived}
        failed = False
        for what, (lookup, key, value) in expected.items():
            rows = lookups[lookup]
            if key not in rows:
                print(f"FAIL: {label}: {what}: no {lookup} row {key} was stored; "
                      f"stored keys are {sorted(rows)}")
                failed = True
                continue
            if rows[key] != value:
                print(f"FAIL: {label}: {what}: {lookup} row {key} carries "
                      f"{rows[key]}, expected {value}")
                failed = True
        print(f"{'FAIL' if failed else 'PASS'}: {label}")
        return not failed
    finally:
        shutil.rmtree(fixture)


def run_feed_at_router_instance():
    return _case(
        "a feed authored at the router instance sets the decode tree's domain",
        FEED_AT_ROUTER,
        {"the router-to-leaf dispatch":
            ('connection', ('uAPBDecode', 'uLeafA'), ('apbClk', 'apbClk/regClk')),
         "the leaf-to-handler bind":
            ('map', ('leafA', 'u_leafA_regs'), ('apbClk', 'apbClk/regClk')),
         # The handler and the router are bus endpoints, so the bus domain is the
         # only one they carry.
         "the generated handler's derived clocks":
            ('derived', 'leafA_regs', ['apbClk/regClk']),
         "the router's derived clocks":
            ('derived', 'apbDecode', ['apbClk/regClk'])})


def run_feed_at_boundary_map():
    return _case(
        "a feed authored as the router's boundary map sets the decode tree's domain",
        FEED_AT_BOUNDARY_MAP,
        {"the router-to-leaf dispatch":
            ('connection', ('uAPBDecode', 'uLeafA'), ('apbClk', 'apbClk/regClk')),
         "the leaf-to-handler bind":
            ('map', ('leafA', 'u_leafA_regs'), ('apbClk', 'apbClk/regClk')),
         # The row that reaches the router is what the tree inherits: the master
         # connection behind it states no clock and keeps the project default.
         "the master connection behind the boundary":
            ('connection', ('uCPU', 'uDut'), ('clk', 'clk/regClk')),
         "the DUT container spans both domains":
            ('derived', 'dut', ['clk/regClk', 'apbClk/regClk'])})


def run_feed_at_container_instance():
    return _case(
        "a feed authored at the router's container instance sets the tree's domain",
        FEED_AT_CONTAINER_INSTANCE,
        {"the synthesised container boundary map":
            ('map', ('ipBlock', 'uAPBDecode'), ('apbClk', 'apbClk/regClk')),
         "the router-to-leaf dispatch":
            ('connection', ('uAPBDecode', 'uLeafA'), ('apbClk', 'apbClk/regClk')),
         "the leaf-to-handler bind":
            ('map', ('leafA', 'u_leafA_regs'), ('apbClk', 'apbClk/regClk'))})


def run_no_feed():
    return _case(
        "a decode tree with no authored feed stays on the project default",
        NO_FEED,
        {"the router-to-leaf dispatch":
            ('connection', ('uAPBDecode', 'uLeafA'), ('clk', 'clk/regClk')),
         "the leaf-to-handler bind":
            ('map', ('leafA', 'u_leafA_regs'), ('clk', 'clk/regClk'))})


def run_object_access_keeps_its_own_domain():
    return _case(
        "logic reaching a register or memory keeps its own domain",
        OBJECT_ACCESS,
        {"the block reaching the register only":
            ('derived', 'regAccessor', ['objClk/regClk']),
         "the block reaching the memory only":
            ('derived', 'memAccessor', ['objClk/regClk']),
         # The served leaf carries both: the bus domain of its generated decode
         # and the domain of the logic that reaches its register and memory. That
         # crossing sits on the leaf's reg_rw / reg_ro wires, which is where it
         # belongs, and nothing reports it.
         "the served leaf's derived clocks":
            ('derived', 'leafA', ['apbClk/regClk', 'objClk/regClk']),
         "the generated handler stays on the bus domain":
            ('derived', 'leafA_regs', ['apbClk/regClk'])})


def run_composed_child_respells_the_clock():
    return _case(
        "a composed child respells the propagated clock in its own project",
        COMPOSED_ASSEMBLER,
        # The assembler's apbClk is not declared by the child, so the bind
        # synthesised into the child's file resolves to the child's own default
        # instead. Without that respelling the reference would not resolve and the
        # build would fail outright.
        {"the leaf-to-handler bind, owned by the child project":
            ('map', ('leafIp', 'u_leafIp_regs'), ('clk', 'clk/childIp')),
         "the generated handler's derived clocks":
            ('derived', 'leafIp_regs', ['clk/childIp']),
         "the router-to-leaf dispatch, owned by the assembler":
            ('connection', ('uAPBDecode', 'uLeafIp'), ('apbClk', 'apbClk/regClk'))},
        child=COMPOSED_CHILD)


def _run():
    print("=" * 72)
    print("TESTING GENERATED REGISTER-DECODE CLOCK DOMAIN")
    print("=" * 72)
    results = [runner() for runner in (
        run_feed_at_router_instance,
        run_feed_at_boundary_map,
        run_feed_at_container_instance,
        run_no_feed,
        run_object_access_keeps_its_own_domain,
        run_composed_child_respells_the_clock)]
    print()
    print("=" * 72)
    if all(results):
        print("RESULT: all register-decode clock domain checks passed")
        return 0
    print("RESULT: register-decode clock domain checks FAILED")
    return 1


def run_all_tests():
    return _run()


if __name__ == '__main__':
    sys.exit(_run())
