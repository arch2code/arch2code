#!/usr/bin/env python3
"""Coverage for the clock domain of a generated register-decode tree: the
bus clock and reset of routers, handlers, served leaves and passthrough
containers, and the diagnostics when they disagree.

A router or a synthesised `<block>_regs` handler does not inherit its domain
from a clock: literal stamped onto a synthesised connection; clocks are
block-scoped, and the project-scoped `clock:` fields that mechanism depended
on do not exist: a router's own domain is bound like any other instance, by an
ordinary `clocks:`/`resets:` map on the router instance itself, and a
handler's domain follows automatically - the leaf's own declared
`registerPorts:` clock for a reusable IP, or for a top-down leaf whichever
of its clocks the instance map binds to the bus.

Assertions are on the derived clock set per block (`blockClocksResets`,
which a block's own declaration and its instances' binds produce) and on
diagnostics, never on the build merely succeeding: a build that synthesises
nothing at all succeeds too.

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

import yaml

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from _addrctl_helpers import APB_PREAMBLE, render_leaf, render_plain_block, render_router
from pysrc.processYaml import projectOpen

PROJECT_TAIL = """
instanceGroups:
    top:
        varType: inst_top
        enumPrefix: INST_TOP_

addressObjects:
    memories:  { alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true }
    registers: { alignment: 8, sortDescending: true }
"""

REGISTER = ("registers:\n"
            "    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, "
            "desc: \"leafA configuration\" }\n")

ROUTER = render_router('apbDecode', 'top')

# 'top' declares clk (default) and apbClk, each with its own reset, so an
# ordinary instance map can bind the router (and, for the reusable-IP leaf,
# nothing further - registerPorts: with no clock: takes the leaf's own
# default) onto the non-default domain. A design's clocks/resets exist on
# the BLOCK that carries them; the project's own clocks:/resets:
# are the testbench's, bound to the design only through the top instance,
# so 'top' must declare them itself for a design fixture to use them at all.
TOP_TWO_CLOCKS = """    top:
        desc: "design top"
        hasMdl: true
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
"""

# The router bound onto 'top's non-default clock by an ordinary instance map,
# the only way a router's own domain is set.
FEED_ON_NON_DEFAULT_CLOCK = f"""include:
    - shared.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{ROUTER}{render_leaf('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{REGISTER}"""

# No instance map at all: the router and the reusable-IP leaf both stay on
# 'top's default clock, the shape every addressBlock: fixture in unittest/
# already covers.
NO_MAP = f"""include:
    - shared.yaml

blocks:
{render_plain_block('top')}{ROUTER}{render_leaf('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}

{REGISTER}"""

# A reusable-IP leaf's instance map disagrees with the router: the router is
# bound onto apbClk, but leafA (registerPorts: with no clock:, so its own
# default clock) is left on 'top's clk instead: a register bus tree is one
# domain throughout.
FEED_MISMATCH = f"""include:
    - shared.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{ROUTER}{render_leaf('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{REGISTER}"""

# A reusable IP whose registerPorts: names its own clock: explicitly
# (block-local) and whose instance map renames THAT clock onto the router's
# own bus clock. The router-to-leaf dispatch connection must not carry this
# block-local name as its container-scoped clock:, or the connection clock:
# check would reject it once the map renames it away from 'regClk'.
REG_CLK_LEAF = render_leaf('leafB', extra_block_lines=(
    "        clocks:\n"
    "            regClk: { }\n"
    "            clk:    { default: true }\n"
    "        resets:\n"
    "            rst_n:    { clock: clk }\n"
    "            regRst_n: { clock: regClk }\n"), port_extra=', clock: regClk')

REG_CLK_REGISTER = ("registers:\n"
                    "    - { register: cfgB, regType: rw, block: leafB, structure: cfgRegSt, "
                    "desc: \"leafB configuration\" }\n")

REG_CLK_RENAME = f"""include:
    - shared.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{ROUTER}{REG_CLK_LEAF}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uLeafB:     {{ container: top, instanceType: leafB, addressGroup: top,
                  clocks: {{ regClk: apbClk }}, resets: {{ regRst_n: apbRst_n }} }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{REG_CLK_REGISTER}"""

# The routed leaf's register and memory reached from two other blocks, each
# declaring and binding its OWN clock (nothing is derived onto a block from a
# connection); the leaf itself carries both its bus domain and theirs. leafA
# additionally declares objClk so its memory (whose clock: must name one of
# the OWNING block's clocks)
# can be put in the same domain as the memory accessor reaching it.
_LEAFA_TWO_CLOCKS = ("        clocks:\n"
                    "            clk:    { default: true }\n"
                    "            objClk: { }\n")
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
    top:
        desc: "design top"
        hasMdl: true
        clocks:
            clk:    {{ default: true }}
            objClk: {{ }}
        resets:
            rst_n:    {{ clock: clk }}
            objRst_n: {{ clock: objClk }}
{render_plain_block('cpu')}{ROUTER}{render_leaf('leafA', extra_block_lines=_LEAFA_TWO_CLOCKS)}
    regAccessor:
        desc: "reaches leafA's register"
        hasMdl: true
        clocks:
            objClk: {{ }}
        resets:
            objRst_n: {{ clock: objClk }}
    memAccessor:
        desc: "reaches leafA's memory"
        hasMdl: true
        clocks:
            objClk: {{ }}
        resets:
            objRst_n: {{ clock: objClk }}
instances:
    uTop:         {{ container: top, instanceType: top }}
    uCPU:         {{ container: top, instanceType: cpu }}
    uAPBDecode:   {{ container: top, instanceType: apbDecode }}
    uLeafA:       {{ container: top, instanceType: leafA, addressGroup: top }}
    uRegAccessor: {{ container: top, instanceType: regAccessor }}
    uMemAccessor: {{ container: top, instanceType: memAccessor }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{REGISTER}
memories:
    - {{ memory: tbl, block: leafA, structure: memSt, addressStruct: memAddrSt, wordLines: TBL_WORDS, ports: [p], clock: objClk, desc: "leafA table" }}

registerConnections:
    - {{ register: cfgA, block: leafA, instance: uRegAccessor }}

memoryConnections:
    - {{ memory: tbl, block: leafA, instance: uMemAccessor, port: p }}
"""

# A TOP-DOWN leaf (no registerPorts:): owns its own register directly, and
# infers its register-bus port from the serving router. 'sampler' declares
# two clocks; its instance map binds clkCap, not the default clk, onto the
# router's own apbClk - so the register port is clkCap.
SAMPLER_BLOCK = """    sampler:
        desc: "top-down leaf; owns a register, authors no registerPorts:"
        hasMdl: true
        clocks:
            clk:    { default: true }
            clkCap: { }
        resets:
            rst_n:    { clock: clk }
            rstCap_n: { clock: clkCap }
"""

SAMPLER_REGISTER = ("registers:\n"
                    "    - { register: cfgS, regType: rw, block: sampler, structure: cfgRegSt, "
                    "desc: \"sampler configuration\" }\n")

# A passthrough container: no addressBlock:, no registerPorts:. It
# resolves its register bus top-down like a leaf, through the
# `resolveBlock` path `_servingRouterBusNets` takes for its inner
# consumer.
WRAP_BLOCK = """    wrap:
        desc: "router-less passthrough container"
        hasMdl: true
        clocks:
            clk:    { default: true }
            clkW:   { }
        resets:
            rst_n:    { clock: clk }
            rstW_n:   { clock: clkW }
"""


def _passthrough_sampler_design(wrap_map, sampler_map):
    """wrap (router-less passthrough container, served by uAPBDecode) holds
    sampler (a top-down leaf) as its own single register consumer; sampler's
    register bus is resolved through wrap's, not directly against the
    router."""
    return f"""include:
    - shared.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{ROUTER}{WRAP_BLOCK}{SAMPLER_BLOCK}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uWrap:      {{ container: top, instanceType: wrap, addressGroup: top,
                  {wrap_map} }}
    uSampler:   {{ container: wrap, instanceType: sampler,
                  {sampler_map} }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{SAMPLER_REGISTER}"""


PASSTHROUGH_SAMPLER = _passthrough_sampler_design(
    "clocks: { clkW: apbClk },\n                  resets: { rstW_n: apbRst_n }",
    "clocks: { clkCap: clkW },\n                  resets: { rstCap_n: rstW_n }")


def _sampler_design(sampler_map):
    return f"""include:
    - shared.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{ROUTER}{SAMPLER_BLOCK}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uSampler:   {{ container: top, instanceType: sampler, addressGroup: top,
                  {sampler_map} }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{SAMPLER_REGISTER}"""


# The tie: two of sampler's own clock ports both bound to apbClk. Declaration
# order picks clk (declared first), even though clkCap also resolves.
TIE_BLOCK = """    sampler:
        desc: "two clock ports bound to one container clock"
        hasMdl: true
        clocks:
            clk:    { default: true }
            clkCap: { }
        resets:
            rst_n:    { clock: clk }
            rstCap_n: { clock: clkCap }
"""


# A container ('ipBlock') that instantiates the router and its served leaf as
# siblings, itself declared as a routed leaf (registerPorts:) so the register-
# decode post-parse pass forwards the CPU's connection on inward to the actual
# router instance nested one level down (config/postParseRegisterPorts.py's
# nested-router dispatch). ipBlock's own two clocks let its own uAPBDecode/
# uLeafA instances rename onto its non-default apbClk, proving the register-
# decode walk (`_resolveRouterBusClockReset`/`_resolveRegisterHandlerBinds`)
# still finds the router and its served leaf when they sit one container level
# below the design root, not just at it (the shape every other fixture here
# uses).
IPBLOCK_TWO_CLOCKS = """        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
"""

FEED_AT_CONTAINER_INSTANCE = f"""include:
    - shared.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{render_leaf('ipBlock', port_name='apbReg', extra_block_lines=IPBLOCK_TWO_CLOCKS)}{ROUTER}{render_leaf('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uIp:        {{ container: top, instanceType: ipBlock }}
    uAPBDecode: {{ container: ipBlock, instanceType: apbDecode,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uLeafA:     {{ container: ipBlock, instanceType: leafA, addressGroup: top,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uIp, dstport: apbReg }}

{REGISTER}"""

# The composed assembler: the routed leaf is owned by the child project below.
# The respelling case becomes an explicit-map case: clocks are block-scoped,
# not project-scoped, so uLeafIp's own instance map binds it to the
# assembler's apbClk the same ordinary way any other instance map does - no
# project-scoped clock name
# needs to be shared with (or respelled by) the child project at all.
COMPOSED_ASSEMBLER = f"""include:
    - shared.yaml
    - ../ip/yaml/childIp.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{ROUTER}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uLeafIp:    {{ container: top, instanceType: leafIp, addressGroup: top,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}
"""

# The child project's own file. Its register is what makes this pass
# synthesise a handler and a handler bind into this file's own context.
COMPOSED_CHILD = f"""include:
    - ../../yaml/shared.yaml

blocks:
{render_leaf('leafIp')}
registers:
    - {{ register: cfgIp, regType: rw, block: leafIp, structure: cfgRegSt, desc: "leafIp configuration" }}
"""


def _deriveProjectDomains(design, blockName='top'):
    """A project `clocks:`/`resets:` section mirroring `blockName`'s own
    EFFECTIVE input clocks/resets by name: the testbench
    binds the top block by name match, so a fixture's project file needs a
    same-named entry for everything the top block's own declaration has -
    including the implicit clk/rst_n a block with no clocks:/resets: gets
    - or an input clock/reset the block declares has nothing to bind to.
    `default: true` is derived from the block's own
    declaration - its default clock, and the reset marked default (or the
    sole candidate) ON that clock - never merely "declared first": a fixture
    whose first declared reset happens to sit on a non-default clock would
    otherwise mark a default reset that does not belong to the default
    clock, which every project requires.
    """
    blockRow = yaml.safe_load(design)['blocks'][blockName]
    clocks = blockRow.get('clocks') or {'clk': {}}
    resets = blockRow.get('resets')
    inputClockNames = [name for name, row in clocks.items()
                       if (row or {}).get('direction', 'input') == 'input']
    defaultClock = next((name for name in inputClockNames if (clocks[name] or {}).get('default')),
                        inputClockNames[0] if len(inputClockNames) == 1 else None)
    if resets is None:
        resets = {'rst_n': {'clock': defaultClock}} if defaultClock else {}
    candidates = [name for name, row in resets.items()
                 if not (row or {}).get('async')
                 and (row or {}).get('direction', 'input') != 'output'
                 and ((row or {}).get('clock') or defaultClock) == defaultClock]
    markedDefault = [name for name in candidates if (resets[name] or {}).get('default')]
    if len(markedDefault) == 1:
        defaultReset = markedDefault[0]
    elif len(candidates) == 1:
        defaultReset = candidates[0]
    elif not resets:
        defaultReset = None
    else:
        raise ValueError(
            f"_deriveProjectDomains: block '{blockName}' declares "
            f"{len(resets)} reset(s) ({', '.join(resets)}) but none sits "
            f"on its default clock '{defaultClock}' unambiguously "
            f"(candidates: {candidates or 'none'}); the fixture needs a "
            f"single reset there to mark default: true on - 'declared "
            f"first' is not a substitute.")
    lines = ['clocks:']
    for name, row in clocks.items():
        row = row or {}
        if row.get('direction') == 'output':
            continue
        lines.append(f"    {name}: {{ desc: \"{name}\", default: "
                     f"{'true' if name == defaultClock else 'false'}, period: 1, timeUnit: ns }}")
    lines.append('')
    lines.append('resets:')
    for name, row in resets.items():
        row = row or {}
        if row.get('direction') == 'output' or row.get('async'):
            continue
        clock = row.get('clock') or defaultClock
        lines.append(f"    {name}: {{ desc: \"{name}\", default: "
                     f"{'true' if name == defaultReset else 'false'}, clock: {clock} }}")
    return '\n'.join(lines) + '\n'


def _make_fixture(design, top_instance='uTop', child=None, files=None):
    """Write a design fixture into a fresh temp dir outside the repo tree.

    `child` adds a second project owning its own arch file, instantiated by
    the assembler, so a synthesised handler lands in the child's own context.
    `files` ({name: content}) are written into the fixture's yaml/ directory
    alongside top.yaml, replacing shared.yaml when named.

    Returns (fixture_dir, project_path, db_path).
    """
    fixture = tempfile.mkdtemp(prefix='regclk_')
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(design)
    for name, content in (files or {}).items():
        with open(os.path.join(fixture, 'yaml', name), 'w') as f:
            f.write(content)

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
                f"topInstance: {top_instance}\n"
                "\n"
                "projectFiles:\n"
                f"{''.join(projectFiles)}"
                "\n"
                f"{_deriveProjectDomains(design)}"
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


def _instanceBinds(db_path):
    """{instance name: {child port: container net}}, read straight from
    instanceClockResetBinds - the container net each instance's own clock and
    reset ports resolved to, whatever the binding rule (map, name match or
    fallback). A block's own declared clock NAMES never change with how it is
    instantiated, so this is the only place "which clock a router
    or handler instance actually runs on" is observable."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        instances = {r['instanceKey']: r['instance']
                    for r in conn.execute('select instance, instanceKey from instances')}
        binds = {name: {} for name in instances.values()}
        for row in conn.execute('select instanceKey, childPort, parentSignal '
                                'from instanceClockResetBinds'):
            binds[instances[row['instanceKey']]][row['childPort']] = row['parentSignal']
        return binds
    finally:
        conn.close()


def _registerBusPort(db_path, block_name):
    """The port name persisted on every one of a block's own
    blockClocksResets rows (BlockDomains.registerBusPort): a served leaf's
    or passthrough container's own port carrying the register bus."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        blockKey = conn.execute(
            'select blockKey from blocks where block = ?', (block_name,)).fetchone()['blockKey']
        row = conn.execute(
            'select registerBusPort from blockClocksResets '
            'where blockKey = ? limit 1', (blockKey,)).fetchone()
        return row['registerBusPort']
    finally:
        conn.close()


def _registerBusDomain(db_path, block_name):
    """(registerClock, registerReset) persisted on every one of a block's own
    blockClocksResets rows (clockTree.py's register-bus resolution): a router's or a
    synthesised `<block>_regs` handler's own bus clock/reset, a block-level
    fact rather than a per-instance bind, so it is not exposed through
    instanceClockResetBinds."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        blockKey = conn.execute(
            'select blockKey from blocks where block = ?', (block_name,)).fetchone()['blockKey']
        row = conn.execute(
            'select registerClock, registerReset from blockClocksResets '
            'where blockKey = ? limit 1', (blockKey,)).fetchone()
        return row['registerClock'], row['registerReset']
    finally:
        conn.close()


def _connectionMaps(db_path):
    """{instance: (block, portName, instancePortName, interfaceKey)} for every
    connectionMaps row: which boundary port of which block feeds which inner
    port, and the qualified interface it carries."""
    conn = sqlite3.connect(db_path)
    try:
        return {row[0]: row[1:] for row in conn.execute(
            'select instance, block, portName, instancePortName, interfaceKey '
            'from connectionMaps')}
    finally:
        conn.close()


def _case(label, design, expected, child=None):
    """Build one fixture and assert every instance's binds in `expected` (a
    {instance name: {child port: container net}} subset)."""
    fixture, project_path, db_path = _make_fixture(design, child=child)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        binds = _instanceBinds(db_path)
        failed = False
        for instance, ports in expected.items():
            for port, net in ports.items():
                got = binds.get(instance, {}).get(port)
                if got != net:
                    print(f"FAIL: {label}: instance '{instance}' port "
                          f"'{port}' binds to {got!r}, expected {net!r}")
                    failed = True
        print(f"{'FAIL' if failed else 'PASS'}: {label}")
        return not failed
    finally:
        shutil.rmtree(fixture)


def _expect_diagnostic(label, design, needles, forbidden=(), files=None):
    """Build `design` and assert it fails with every one of `needles` in the
    output and none of `forbidden`. `files` ({name: content}) are written
    into the fixture's yaml/ directory alongside top.yaml."""
    fixture, project_path, db_path = _make_fixture(design, files=files)
    try:
        code, output = _build(project_path, db_path)
    finally:
        shutil.rmtree(fixture)
    if code == 0:
        print(f"FAIL: {label}: build succeeded; it must fail.\n{output}")
        return False
    if 'Traceback' in output:
        print(f"FAIL: {label}: the build crashed instead of reporting a "
              f"diagnostic.\n{output}")
        return False
    for needle in needles:
        if needle not in output:
            print(f"FAIL: {label}: diagnostic does not mention {needle!r}.\n{output}")
            return False
    for needle in forbidden:
        if needle in output:
            print(f"FAIL: {label}: diagnostic mentions {needle!r}.\n{output}")
            return False
    print(f"PASS: {label}")
    return True


# A reusable-IP leaf whose registerPorts: names a reset the block does not
# declare, and a router whose addressBlock: names a clock it does not
# declare: both are the schema's blockClock/blockReset combo foreign key
# (the existence check), reported in the parser's "not valid in context" form.
_BAD_RESET_LEAF = render_leaf('leafB', extra_block_lines=(
    "        clocks:\n"
    "            clk: { default: true }\n"
    "        resets:\n"
    "            rst_n: { clock: clk }\n"), port_extra=', reset: noSuchReset')

REGISTER_PORT_BAD_RESET = f"""include:
    - shared.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{ROUTER}{_BAD_RESET_LEAF}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafB:     {{ container: top, instanceType: leafB, addressGroup: top }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{REG_CLK_REGISTER}"""

_BAD_CLOCK_ROUTER = render_router('apbDecode', 'top', extra_block_lines=(
    "        clocks:\n"
    "            clk: { default: true }\n")) + "            clock: noSuchClock\n"

ROUTER_BAD_CLOCK = f"""include:
    - shared.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{_BAD_CLOCK_ROUTER}{render_leaf('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{REGISTER}"""


def run_register_port_reset_undeclared_rejected():
    return _expect_diagnostic(
        "a reusable-IP leaf's registerPorts: reset: naming a reset the block "
        "does not declare is rejected",
        REGISTER_PORT_BAD_RESET,
        ('leafB', 'regs', 'noSuchReset', 'not valid in context'))


def run_router_addressblock_clock_undeclared_rejected():
    return _expect_diagnostic(
        "a router's addressBlock: clock: naming a clock the block does not "
        "declare is rejected",
        ROUTER_BAD_CLOCK,
        ('apbDecode', 'noSuchClock', 'not valid in context'))


def run_no_map_default_clock():
    return _case(
        "with no instance map, the router and its leaf stay on the default clock",
        NO_MAP,
        {'uAPBDecode': {'clk': 'clk'}, 'u_leafA_regs': {'clk': 'clk'}})


def run_router_bound_to_non_default_clock():
    # The router's ports keep their declared names, so its declared clk/rst_n
    # are the child ports bound onto the container's apbClk/apbRst_n.
    return _case(
        "an ordinary instance map binds the router (and its served reusable-IP "
        "leaf's own default clock) onto a non-default clock",
        FEED_ON_NON_DEFAULT_CLOCK,
        {'uAPBDecode': {'clk': 'apbClk', 'rst_n': 'apbRst_n'}})


def run_reusable_ip_bus_mismatch_rejected():
    return _expect_diagnostic(
        "a reusable-IP leaf whose registerPorts: clock does not sit on the "
        "router's actual bus clock is rejected",
        FEED_MISMATCH,
        ('leafA', 'clk', 'A register port must run on the register bus clock'))


def run_reusable_ip_register_port_clock_rename():
    """A reusable IP's registerPorts: clock: (block-local), renamed
    onto the bus by an ordinary instance map, builds clean and the handler
    binds through it - the router-to-leaf dispatch connection states no
    clock: of its own (config/postParseRegisterPorts.py), so there is
    nothing for the connection clock: check to reject against the renamed
    name."""
    label = ("a reusable IP's registerPorts: clock:, renamed by an ordinary "
             "instance map, builds clean and the handler binds through it")
    fixture, project_path, db_path = _make_fixture(REG_CLK_RENAME)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        failed = False
        got = _instanceBinds(db_path).get('uLeafB', {}).get('regClk')
        if got != 'apbClk':
            print(f"FAIL: {label}: instance 'uLeafB' port 'regClk' binds to "
                  f"{got!r}, expected 'apbClk'")
            failed = True
        leafBus = _registerBusDomain(db_path, 'leafB')
        if leafBus != ('regClk', 'regRst_n'):
            print(f"FAIL: {label}: leafB's bus clock/reset is {leafBus}, "
                  f"expected ('regClk', 'regRst_n')")
            failed = True
        print(f"{'FAIL' if failed else 'PASS'}: {label}")
        return not failed
    finally:
        shutil.rmtree(fixture)


def run_object_access_keeps_its_own_domain():
    return _case(
        "logic reaching a register or memory keeps its own domain",
        OBJECT_ACCESS,
        {'uRegAccessor': {'objClk': 'objClk'}, 'uMemAccessor': {'objClk': 'objClk'}})


def run_feed_at_container_instance():
    """The router instantiated inside a container block ('ipBlock'), with its
    served leaf as a sibling: the register-decode walk
    (`_resolveRouterBusClockReset`, `_resolveRegisterHandlerBinds`) must find
    them one container level below the design root, not just at it. Both
    instances are mapped onto ipBlock's own non-default apbClk, so the
    router's and the handler's own bus clock/reset (a block-level fact, not
    a per-instance bind) are asserted directly."""
    label = ("a router and its served leaf, nested inside a container "
             "instance, still resolve their bus clock/reset")
    fixture, project_path, db_path = _make_fixture(FEED_AT_CONTAINER_INSTANCE)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        failed = False
        binds = _instanceBinds(db_path)
        # Both instances bind their own declared 'clk' port onto apbClk.
        got = binds.get('uAPBDecode', {}).get('clk')
        if got != 'apbClk':
            print(f"FAIL: {label}: instance 'uAPBDecode' port 'clk' "
                  f"binds to {got!r}, expected 'apbClk'")
            failed = True
        got = binds.get('uLeafA', {}).get('clk')
        if got != 'apbClk':
            print(f"FAIL: {label}: instance 'uLeafA' port 'clk' "
                  f"binds to {got!r}, expected 'apbClk'")
            failed = True
        # The router's own bus clock/reset is the CONTAINER's (ipBlock's own)
        # net name: its instance is one level below the
        # design root, and this is the fact that walk must still resolve.
        routerBus = _registerBusDomain(db_path, 'apbDecode')
        if routerBus != ('apbClk', 'apbRst_n'):
            print(f"FAIL: {label}: apbDecode's bus clock/reset is {routerBus}, "
                  f"expected ('apbClk', 'apbRst_n')")
            failed = True
        # The handler's own bus clock/reset mirrors leafA's own registerPorts:
        # selection - leafA's OWN clock/reset port NAME,
        # unaffected by how leafA's instance is renamed outward.
        handlerBus = _registerBusDomain(db_path, 'leafA_regs')
        if handlerBus != ('clk', 'rst_n'):
            print(f"FAIL: {label}: leafA_regs's bus clock/reset is "
                  f"{handlerBus}, expected ('clk', 'rst_n')")
            failed = True
        print(f"{'FAIL' if failed else 'PASS'}: {label}")
        return not failed
    finally:
        shutil.rmtree(fixture)


def run_composed_child_respells_the_clock():
    """The respelling case becomes an explicit-map case: a composed child's
    own instance (uLeafIp, of a block declared in a second project) binds
    through an ordinary instance map like any other - clocks are
    block-scoped, not project-scoped, so no clock name needs to be shared
    with the child project at all."""
    label = "a composed child's instance binds through an explicit instance map"
    fixture, project_path, db_path = _make_fixture(
        COMPOSED_ASSEMBLER, child=COMPOSED_CHILD)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        failed = False
        got = _instanceBinds(db_path).get('uLeafIp', {}).get('clk')
        if got != 'apbClk':
            print(f"FAIL: {label}: instance 'uLeafIp' port 'clk' binds to "
                  f"{got!r}, expected 'apbClk'")
            failed = True
        # leafIp authors no registerPorts: clock: of its own, so its bus is
        # its own default clock/reset port NAME - and the
        # handler synthesised into the CHILD project's own context mirrors it.
        leafBus = _registerBusDomain(db_path, 'leafIp')
        if leafBus != ('clk', 'rst_n'):
            print(f"FAIL: {label}: leafIp's bus clock/reset is {leafBus}, "
                  f"expected ('clk', 'rst_n')")
            failed = True
        handlerBus = _registerBusDomain(db_path, 'leafIp_regs')
        if handlerBus != ('clk', 'rst_n'):
            print(f"FAIL: {label}: leafIp_regs's bus clock/reset is "
                  f"{handlerBus}, expected ('clk', 'rst_n')")
            failed = True
        print(f"{'FAIL' if failed else 'PASS'}: {label}")
        return not failed
    finally:
        shutil.rmtree(fixture)


# A never-instantiated harness container of the child project, holding a
# memory accessor on another clock than the memory it accesses.
COMPOSED_CHILD_HARNESS = f"""include:
    - ../../yaml/shared.yaml

types:
    ipDataT: {{ width: 8, desc: "payload word" }}
    ipAddrT: {{ width: 3, desc: "memory address" }}

structures:
    ipMemSt:
        data: {{ varType: ipDataT, desc: "memory payload" }}
    ipMemAddrSt:
        address: {{ varType: ipAddrT, desc: "memory address" }}

blocks:
{render_leaf('leafIp')}    ipHarness:
        desc: "the child project's own harness, instantiated by no one here"
        hasMdl: false
        clocks:
            clk:  {{ default: true }}
            clkB: {{ }}
        resets:
            rst_n:  {{ clock: clk }}
            rstB_n: {{ clock: clkB }}
    ipMemOwner: {{ desc: "owns a memory on its default clock", hasMdl: false }}
    ipAccessor: {{ desc: "hardware accessor of the memory", hasMdl: false }}

instances:
    hMemOwner: {{ container: ipHarness, instanceType: ipMemOwner }}
    hAccessor: {{ container: ipHarness, instanceType: ipAccessor,
                 clocks: {{ clk: clkB }}, resets: {{ rst_n: rstB_n }} }}

memories:
    - {{ memory: ipTbl, block: ipMemOwner, structure: ipMemSt, addressStruct: ipMemAddrSt,
        wordLines: 4, ports: [p], desc: "table" }}

memoryConnections:
    - {{ memory: ipTbl, block: ipMemOwner, instance: hAccessor, port: p }}

registers:
    - {{ register: cfgIp, regType: rw, block: leafIp, structure: cfgRegSt, desc: "leafIp configuration" }}
"""


def run_child_harness_accessor_domain_not_checked():
    """A memory accessor's domain is checked in every container the root
    project declares, but a container the child project declares and this
    build never instantiates is the child's own build's to check, so its
    cross-domain accessor does not fail the root build."""
    label = "a child project's uninstantiated harness accessor is not checked by the root build"
    fixture, project_path, db_path = _make_fixture(
        COMPOSED_ASSEMBLER, child=COMPOSED_CHILD_HARNESS)
    try:
        code, output = _build(project_path, db_path)
    finally:
        shutil.rmtree(fixture)
    if code != 0:
        print(f"FAIL: {label}\n{output}")
        return False
    print(f"PASS: {label}")
    return True


def run_child_harness_accessor_without_default_clock_rejected():
    """Whether an accessor's block has a default clock depends only on the
    block, so it is checked even for an accessor in a child project's
    uninstantiated harness, which the domain match skips."""
    label = ("a child project's uninstantiated harness accessor with no default "
             "clock is rejected")
    child = COMPOSED_CHILD_HARNESS.replace(
        '    ipAccessor: { desc: "hardware accessor of the memory", hasMdl: false }',
        '    ipAccessor:\n'
        '        desc: "hardware accessor of the memory"\n'
        '        hasMdl: false\n'
        '        clocks:\n'
        '            clkO: { direction: output }').replace(
        "clocks: { clk: clkB }, resets: { rst_n: rstB_n } }",
        "clocks: { clkO: ~ } }")
    fixture, project_path, db_path = _make_fixture(COMPOSED_ASSEMBLER, child=child)
    try:
        code, output = _build(project_path, db_path)
    finally:
        shutil.rmtree(fixture)
    needles = ("Instance 'hAccessor' of block 'ipAccessor' accesses memory 'ipTbl' "
               "of block 'ipMemOwner', but 'ipAccessor' has no default clock (every "
               "declared clock is direction: output). A memory accessor takes its "
               "block's default clock. Give 'ipAccessor' an input clock.",
               "Found 1 Error.")
    if code == 0 or 'Traceback' in output or any(n not in output for n in needles):
        print(f"FAIL: {label}\n{output}")
        return False
    print(f"PASS: {label}")
    return True


def run_top_down_leaf_register_port_selection():
    # childPort reads 'clkCap' (the selected register clock), not the
    # handler's own raw implicit 'clk': the handler's ports are named after
    # the leaf nets they bind to.
    return _case(
        "a top-down leaf's register port is the clock its map binds to the bus, "
        "not the block default",
        _sampler_design("clocks: { clkCap: apbClk },\n"
                        "                  resets: { rstCap_n: apbRst_n }"),
        {'u_sampler_regs': {'clkCap': 'clkCap'}})


def run_top_down_leaf_tie_by_declaration_order():
    design = f"""include:
    - shared.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{ROUTER}{TIE_BLOCK}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uSampler:   {{ container: top, instanceType: sampler, addressGroup: top,
                  clocks: {{ clk: apbClk, clkCap: apbClk }},
                  resets: {{ rst_n: apbRst_n, rstCap_n: apbRst_n }} }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{SAMPLER_REGISTER}"""
    return _case(
        "two leaf clock ports bound to the same container clock resolve to "
        "the first declared (tie)",
        design,
        {'u_sampler_regs': {'clk': 'clk'}})


def run_top_down_leaf_no_clock_match_rejected():
    return _expect_diagnostic(
        "a top-down leaf none of whose clock ports is bound to the bus clock "
        "is rejected",
        _sampler_design("clocks: { clk: clk, clkCap: clk },\n"
                        "                  resets: { rst_n: rst_n, rstCap_n: rst_n }"),
        ('sampler', "none of its declared clock ports is bound to the register bus's clock"))


def run_top_down_leaf_no_reset_match_rejected():
    # apbClk carries two resets, apbRst_n marked default (the selected reset)
    # and apbRst2_n not: clkCap correctly resolves to the bus clock, but its
    # own reset is bound to apbRst2_n, a reset of the right clock (clock
    # membership is satisfied) yet not the bus's SELECTED one.
    design = f"""include:
    - shared.yaml

blocks:
    top:
        desc: "design top"
        hasMdl: true
        clocks:
            clk:    {{ default: true }}
            apbClk: {{ }}
        resets:
            rst_n:     {{ clock: clk }}
            apbRst_n:  {{ clock: apbClk, default: true }}
            apbRst2_n: {{ clock: apbClk }}
{render_plain_block('cpu')}{ROUTER}{SAMPLER_BLOCK}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uSampler:   {{ container: top, instanceType: sampler, addressGroup: top,
                  clocks: {{ clkCap: apbClk }},
                  resets: {{ rstCap_n: apbRst2_n }} }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{SAMPLER_REGISTER}"""
    return _expect_diagnostic(
        "a top-down leaf none of whose reset ports is bound to the bus's "
        "selected reset is rejected",
        design,
        ('sampler', "none of its declared reset ports is bound to the register bus's selected reset"))


def run_top_down_leaf_instances_disagree_rejected():
    """Two instances of the same top-down leaf resolving to different
    clock/reset pairs is rejected: the leaf module is generated once."""
    design = f"""include:
    - shared.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{ROUTER}{SAMPLER_BLOCK}
instances:
    uTop:        {{ container: top, instanceType: top }}
    uCPU:        {{ container: top, instanceType: cpu }}
    uAPBDecode:  {{ container: top, instanceType: apbDecode,
                   clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uSamplerA:   {{ container: top, instanceType: sampler, addressGroup: top,
                   clocks: {{ clk: apbClk, clkCap: apbClk }},
                   resets: {{ rst_n: apbRst_n, rstCap_n: apbRst_n }} }}
    uSamplerB:   {{ container: top, instanceType: sampler, addressGroup: top,
                   clocks: {{ clk: clk, clkCap: apbClk }},
                   resets: {{ rst_n: rst_n, rstCap_n: apbRst_n }} }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{SAMPLER_REGISTER}"""
    return _expect_diagnostic(
        "two instances of a top-down leaf resolving to different clock/reset "
        "pairs is rejected",
        design,
        ('sampler', 'uSamplerA', 'uSamplerB',
         'Every instance must use the same clock/reset pair for its register port'))


def run_register_bus_reset_missing_rejected():
    """A router's register bus clock must have a selected input reset. The
    router declares resets: {} (no reset at all), so its bus clock has no
    reset to select, which is reported at the router before the leaf it
    serves looks for that reset."""
    design = f"""include:
    - shared.yaml

blocks:
{render_plain_block('top')}{render_plain_block('cpu')}
    apbDecodeNR:
        desc: "Router with no resets at all"
        hasMdl: true
        resets: {{}}
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
{render_leaf('leafA')}
instances:
    uTop:         {{ container: top, instanceType: top }}
    uCPU:         {{ container: top, instanceType: cpu }}
    uAPBDecodeNR: {{ container: top, instanceType: apbDecodeNR }}
    uLeafA:       {{ container: top, instanceType: leafA, addressGroup: top }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecodeNR }}

{REGISTER}"""
    return _expect_diagnostic(
        "a router declaring resets: {} has no reset for its register bus "
        "clock",
        design,
        ('apbDecodeNR', "has no selected reset and addressBlock: names no reset:"))


def run_router_addressblock_reset_override_not_duplicated():
    """A router declaring more than one reset on its bus clock, with
    addressBlock: reset: naming the NON-default one as the bus reset, runs
    its flops on that named port (busResetPort) - not
    block_data['defaultReset'] (the block's own marked default, 'rst_n'
    here) - and keeps each declared reset once, each bound by its own
    name."""
    design = f"""include:
    - shared.yaml

blocks:
    top:
        desc: "design top"
        hasMdl: true
        clocks:
            clk: {{ default: true }}
        resets:
            rst_n:    {{ default: true, clock: clk }}
            rstBus_n: {{ clock: clk }}
{render_plain_block('cpu')}
    apbDecodeRR:
        desc: "Router: addressBlock: reset: names the non-default reset"
        hasMdl: true
        clocks:
            clk: {{ default: true }}
        resets:
            rst_n:    {{ default: true, clock: clk }}
            rstBus_n: {{ clock: clk }}
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
            reset: rstBus_n
{render_leaf('leafA')}
instances:
    uTop:         {{ container: top, instanceType: top }}
    uCPU:         {{ container: top, instanceType: cpu }}
    uAPBDecodeRR: {{ container: top, instanceType: apbDecodeRR }}
    uLeafA:       {{ container: top, instanceType: leafA, addressGroup: top }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecodeRR }}

{REGISTER}"""
    label = ("a router's addressBlock: reset: override selects the named "
             "reset, not the block's own default, and every declared reset "
             "keeps its own name")
    fixture, project_path, db_path = _make_fixture(design)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        prj = projectOpen(db_path)
        routerKey = next(key for key, row in prj.data['blocks'].items()
                         if row['block'] == 'apbDecodeRR')
        view = prj.getBlockData(routerKey)
        names = [row['reset'] for row in view['resets']]
        failed = False
        if view['busResetPort'] != 'rstBus_n':
            print(f"FAIL: {label}: the router's bus reset port is "
                  f"{view['busResetPort']!r}, expected 'rstBus_n'")
            failed = True
        if names != ['rst_n', 'rstBus_n']:
            print(f"FAIL: {label}: the router declares resets {names}, "
                  f"expected ['rst_n', 'rstBus_n']")
            failed = True
        binds = _instanceBinds(db_path)['uAPBDecodeRR']
        if binds != {'clk': 'clk', 'rst_n': 'rst_n', 'rstBus_n': 'rstBus_n'}:
            print(f"FAIL: {label}: instance 'uAPBDecodeRR' binds {binds}, "
                  f"expected each port bound by its own name")
            failed = True
        print(f"{'FAIL' if failed else 'PASS'}: {label}")
        return not failed
    finally:
        shutil.rmtree(fixture)


def run_reusable_ip_authored_reset_mismatch_rejected():
    """For a reusable IP, registerPorts: reset: authors a reset that is
    not bound to the same container reset as the serving router's own bus
    reset. leafE names 'regRst2_n' explicitly (its own clock regClk agrees
    with the bus, so the register port clock check passes), but its instance map puts
    regRst2_n on 'top's apbRst2_n, not the router's own selected
    apbRst_n - a second reset on the SAME container clock as the bus reset,
    so this isolates the bus reset check from clock membership and from the
    missing-reset check (a reset exists, just the wrong one)."""
    design = """include:
    - shared.yaml

blocks:
    top:
        desc: "design top"
        hasMdl: true
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:     { clock: clk, default: true }
            apbRst_n:  { clock: apbClk, default: true }
            apbRst2_n: { clock: apbClk }
""" + render_plain_block('cpu') + ROUTER + """    leafE:
        desc: "Routed leaf block 'leafE'"
        hasMdl: true
        clocks:
            clk:    { default: true }
            regClk: { }
        resets:
            rst_n:     { clock: clk }
            regRst_n:  { clock: regClk, default: true }
            regRst2_n: { clock: regClk }
        registerPorts:
            regs: { interface: apbReg, clock: regClk, reset: regRst2_n }

instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode,
                  clocks: { clk: apbClk }, resets: { rst_n: apbRst_n } }
    uLeafE:     { container: top, instanceType: leafE, addressGroup: top,
                  clocks: { regClk: apbClk },
                  resets: { regRst_n: apbRst_n, regRst2_n: apbRst2_n } }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cfgE, regType: rw, block: leafE, structure: cfgRegSt, desc: "leafE configuration" }
"""
    return _expect_diagnostic(
        "a reusable IP's authored registerPorts: reset: not bound to the "
        "router's own bus reset is rejected",
        design,
        ('leafE', 'regRst2_n', "A register port's reset must be the register bus reset"))


# A container whose default clock is literally named 'regClk', and a served
# leaf declaring 'regClk' (default, so also its own registerPorts: clock, the
# reusable-IP rule-1 default) and 'auxClk', explicitly mapped onto 'regClk'
# too: both leaf clocks resolve to the SAME container net 'regClk'. This is
# chosen so the container net's own NAME happens to equal the leaf's
# registerClock PORT NAME string, which is exactly the coincidence
# clockTree.rows()' childPort rename must not be fooled by: registerClock is
# a leaf's own port name, not a container net, so comparing it against `net`
# (a net of THIS container) is only meaningful for a router or a handler
# child, never a served leaf.
TOP_REGCLK_DEFAULT = """    top:
        desc: "design top"
        hasMdl: true
        clocks:
            regClk: { default: true }
            sysClk: { }
        resets:
            regRst_n: { clock: regClk }
            sysRst_n: { clock: sysClk }
"""

LEAF_C = """    leafC:
        desc: "Routed leaf block 'leafC'"
        hasMdl: true
        clocks:
            regClk: { default: true }
            auxClk: { }
        registerPorts:
            regs: { interface: apbReg }
"""

REG_CLK_COINCIDENCE_REGISTER = (
    "registers:\n"
    "    - { register: cfgC, regType: rw, block: leafC, structure: cfgRegSt, "
    "desc: \"leafC configuration\" }\n")

REG_CLK_COINCIDENCE = f"""include:
    - shared.yaml

blocks:
{TOP_REGCLK_DEFAULT}{render_plain_block('cpu')}{ROUTER}{LEAF_C}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafC:     {{ container: top, instanceType: leafC, addressGroup: top,
                  clocks: {{ auxClk: regClk }} }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{REG_CLK_COINCIDENCE_REGISTER}"""


def run_served_leaf_registerclock_name_coincidence_not_renamed():
    return _case(
        "a served leaf's own clock port keeps its own name even when it "
        "resolves to a container net spelled the same as the leaf's own "
        "registerClock port name",
        REG_CLK_COINCIDENCE,
        {'uLeafC': {'regClk': 'regClk', 'auxClk': 'regClk'}})


def run_passthrough_container_resolves_bus_clock():
    label = ("a router-less passthrough container and the leaf behind it "
             "both resolve their register bus")
    fixture, project_path, db_path = _make_fixture(PASSTHROUGH_SAMPLER)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        failed = False
        wrapBus = _registerBusDomain(db_path, 'wrap')
        if wrapBus != ('clkW', 'rstW_n'):
            print(f"FAIL: {label}: wrap's bus clock/reset is {wrapBus}, "
                  f"expected ('clkW', 'rstW_n')")
            failed = True
        samplerBus = _registerBusDomain(db_path, 'sampler_regs')
        if samplerBus != ('clkCap', 'rstCap_n'):
            print(f"FAIL: {label}: sampler_regs's bus clock/reset is "
                  f"{samplerBus}, expected ('clkCap', 'rstCap_n')")
            failed = True
        got = _instanceBinds(db_path).get('u_sampler_regs', {}).get('clkCap')
        if got != 'clkCap':
            print(f"FAIL: {label}: instance 'u_sampler_regs' port 'clkCap' "
                  f"binds to {got!r}, expected 'clkCap'")
            failed = True
        print(f"{'FAIL' if failed else 'PASS'}: {label}")
        return not failed
    finally:
        shutil.rmtree(fixture)


def run_passthrough_inner_leaf_bus_mismatch_rejected():
    design = _passthrough_sampler_design(
        "clocks: { clkW: apbClk },\n                  resets: { rstW_n: apbRst_n }",
        "clocks: { clkCap: clk },\n                  resets: { rstCap_n: rst_n }")
    return _expect_diagnostic(
        "a leaf behind a passthrough container whose clock does not sit on "
        "the container's own resolved bus clock is rejected",
        design,
        ('sampler', "none of its declared clock ports is bound to the register bus's clock"))


def run_passthrough_container_bus_mismatch_rejected():
    design = _passthrough_sampler_design(
        "clocks: { clkW: clk },\n                  resets: { rstW_n: rst_n }",
        "clocks: { clkCap: clkW },\n                  resets: { rstCap_n: rstW_n }")
    return _expect_diagnostic(
        "a passthrough container whose clock does not sit on the router's "
        "actual bus clock is rejected",
        design,
        ('wrap', "none of its declared clock ports is bound to the register bus's clock"))


# A reusable-IP passthrough container: registerPorts: { regs: ... }, owns
# no registers of its own, and hosts a top-down inner leaf. The container is
# the inner leaf's nearest authored boundary, so the leaf's own port takes the
# container's key 'regs'; the leaf's synthesised handler takes that same
# name as its port.
WRAP_IP_BLOCK = render_leaf('wrapIP')

PASSTHROUGH_REUSABLE_IP_SAMPLER = f"""include:
    - shared.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{ROUTER}{WRAP_IP_BLOCK}{SAMPLER_BLOCK}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uWrapIP:    {{ container: top, instanceType: wrapIP, addressGroup: top,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uSampler:   {{ container: wrapIP, instanceType: sampler,
                  clocks: {{ clkCap: clk }}, resets: {{ rstCap_n: rst_n }} }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{SAMPLER_REGISTER}"""


def run_passthrough_reusable_ip_container_inner_leaf_port():
    """The top-down leaf behind a reusable-IP passthrough container takes
    the container's registerPorts: key as its port name, its handler takes
    the same name, and both blocks resolve their register clock/reset
    through the container."""
    label = ("the top-down leaf behind a reusable-IP passthrough container "
             "takes the container's register-bus port name")
    fixture, project_path, db_path = _make_fixture(PASSTHROUGH_REUSABLE_IP_SAMPLER)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        failed = False
        containerPort = _registerBusPort(db_path, 'wrapIP')
        if containerPort != 'regs':
            print(f"FAIL: {label}: wrapIP's registerBusPort is "
                  f"{containerPort!r}, expected 'regs'")
            failed = True
        leafPort = _registerBusPort(db_path, 'sampler')
        if leafPort != 'regs':
            print(f"FAIL: {label}: sampler's registerBusPort is "
                  f"{leafPort!r}, expected 'regs'")
            failed = True
        handlerMap = _connectionMaps(db_path)['u_sampler_regs']
        expectedMap = ('sampler', 'regs', 'regs', 'apbReg/../../yaml/shared.yaml')
        if handlerMap != expectedMap:
            print(f"FAIL: {label}: u_sampler_regs's connectionMap is "
                  f"{handlerMap}, expected {expectedMap}")
            failed = True
        containerBus = _registerBusDomain(db_path, 'wrapIP')
        leafBus = _registerBusDomain(db_path, 'sampler')
        if leafBus != containerBus:
            print(f"FAIL: {label}: sampler's register clock/reset {leafBus} "
                  f"does not match wrapIP's {containerBus}")
            failed = True
        print(f"{'FAIL' if failed else 'PASS'}: {label}")
        return not failed
    finally:
        shutil.rmtree(fixture)


def run_passthrough_container_instances_disagree_rejected():
    """Two instances of a passthrough container that resolve to different
    clock/reset pairs are rejected; the container's registerClock is
    a block-level fact."""
    design = f"""include:
    - shared.yaml

blocks:
{TOP_TWO_CLOCKS}{render_plain_block('cpu')}{ROUTER}{WRAP_BLOCK}{SAMPLER_BLOCK}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode,
                  clocks: {{ clk: apbClk }}, resets: {{ rst_n: apbRst_n }} }}
    uWrapA:     {{ container: top, instanceType: wrap, addressGroup: top,
                  clocks: {{ clk: apbClk, clkW: apbClk }},
                  resets: {{ rst_n: apbRst_n, rstW_n: apbRst_n }} }}
    uWrapB:     {{ container: top, instanceType: wrap, addressGroup: top,
                  clocks: {{ clk: clk, clkW: apbClk }},
                  resets: {{ rst_n: rst_n, rstW_n: apbRst_n }} }}
    uSampler:   {{ container: wrap, instanceType: sampler,
                  clocks: {{ clkCap: clkW }}, resets: {{ rstCap_n: rstW_n }} }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{SAMPLER_REGISTER}"""
    return _expect_diagnostic(
        "two instances of a passthrough container resolving to different "
        "clock/reset pairs is rejected",
        design,
        ('wrap', 'Every instance must use the same clock/reset pair for its register port'))


# Two serving routers: 'outerDecode' in 'top' and 'innerDecode' nested in
# 'mid', with registerDecoderPort `outer_decoder_port` and
# `inner_decoder_port`, both on interface 'apbReg'. The reused block has one
# instance under each router. With `reuse_wrap`, that block is the
# router-less passthrough 'wrap' holding leafA; otherwise it is leafA
# itself. Neither authors registerPorts:.
def _two_router_reuse_design(outer_decoder_port, inner_decoder_port, reuse_wrap):
    if reuse_wrap:
        reused_blocks = render_plain_block('wrap') + render_plain_block('leafA')
        reused_instances = (
            "    uWrapTop:   { container: top, instanceType: wrap, addressGroup: top }\n"
            "    uWrapMid:   { container: mid, instanceType: wrap, addressGroup: mid }\n"
            "    uLeafA:     { container: wrap, instanceType: leafA }\n")
    else:
        reused_blocks = render_plain_block('leafA')
        reused_instances = (
            "    uLeafATop:  { container: top, instanceType: leafA, addressGroup: top }\n"
            "    uLeafAMid:  { container: mid, instanceType: leafA, addressGroup: mid }\n")
    outer_router = render_router(
        'outerDecode', 'top', register_decoder_port=outer_decoder_port)
    inner_router = render_router(
        'innerDecode', 'mid', register_decoder_port=inner_decoder_port,
        address_increment='0x1000', max_address_spaces=4)
    return f"""include:
    - shared.yaml

blocks:
{render_plain_block('top')}{render_plain_block('mid')}{render_plain_block('cpu')}{outer_router}{inner_router}{reused_blocks}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uOuter:     {{ container: top, instanceType: outerDecode }}
    uMid:       {{ container: top, instanceType: mid, addressGroup: top }}
    uInner:     {{ container: mid, instanceType: innerDecode }}
{reused_instances}
connections:
    - {{ interface: apbReg, src: uCPU, dst: uOuter }}

{REGISTER}"""


APB_REG_KEY = 'apbReg/../../yaml/shared.yaml'


def run_passthrough_reused_under_disagreeing_routers_takes_interface_name():
    """The routers offer 'wrap' and leafA the names 'outerDecoder' and
    'innerDecoder', so both blocks take the interface name 'apbReg'; each
    router's dispatch keeps its own source port."""
    return _expect_register_bus_maps(
        "a passthrough reused under two routers with different "
        "registerDecoderPort takes the interface name as its port",
        _two_router_reuse_design('outerDecoder', 'innerDecoder', True),
        {'uLeafA': ('wrap', 'apbReg', 'apbReg', APB_REG_KEY),
         'u_leafA_regs': ('leafA', 'apbReg', 'apbReg', APB_REG_KEY)},
        {'wrap': 'apbReg', 'leafA': 'apbReg'},
        connections={'uWrapTop': ('uOuter', 'outerDecoder_uWrapTop', 'apbReg'),
                     'uWrapMid': ('uInner', 'innerDecoder_uWrapMid', 'apbReg')},
        swap=('uWrapTop', 'uWrapMid'))


def run_leaf_reused_under_disagreeing_routers_takes_interface_name():
    return _expect_register_bus_maps(
        "a plain leaf reused under two routers with different "
        "registerDecoderPort takes the interface name as its port",
        _two_router_reuse_design('outerDecoder', 'innerDecoder', False),
        {'u_leafA_regs': ('leafA', 'apbReg', 'apbReg', APB_REG_KEY)},
        {'leafA': 'apbReg'},
        connections={'uLeafATop': ('uOuter', 'outerDecoder_uLeafATop', 'apbReg'),
                     'uLeafAMid': ('uInner', 'innerDecoder_uLeafAMid', 'apbReg')},
        swap=('uLeafATop', 'uLeafAMid'))


def _two_router_reuse_agreeing_builds(reuse_wrap, block):
    label = (f"'{block}' reused under two routers that agree on "
             f"registerDecoderPort builds")
    fixture, project_path, db_path = _make_fixture(
        _two_router_reuse_design('apbReg', 'apbReg', reuse_wrap))
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        port = _registerBusPort(db_path, block)
        if port != 'apbReg':
            print(f"FAIL: {label}: {block}'s registerBusPort is {port!r}, "
                  f"expected 'apbReg'")
            return False
        print(f"PASS: {label}")
        return True
    finally:
        shutil.rmtree(fixture)


def run_passthrough_reused_under_agreeing_routers_builds():
    return _two_router_reuse_agreeing_builds(True, 'wrap')


def run_leaf_reused_under_agreeing_routers_builds():
    return _two_router_reuse_agreeing_builds(False, 'leafA')


# A passthrough wrapper authoring registerPorts: on its own interface
# 'ipReg', holding plain leaf 'leafA' that infers its register binding.
IP_REG_INTERFACE = """    ipReg:
        desc: "IP-local APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
"""

IP_REG_WRAP = f"""blocks:
{render_leaf('wrapIP', interface='ipReg')}{render_plain_block('leafA')}"""

IP_REG_TOP_INSTANCES = f"""{render_plain_block('top')}{render_plain_block('cpu')}{ROUTER}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uWrapIP:    {{ container: top, instanceType: wrapIP, addressGroup: top }}
"""

IP_REG_CONNECTIONS = """
connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }
"""


def _registerBusWiring(db_path):
    """Every connections and connectionMaps row and every block's
    registerBusPort, as sorted tuples, so two builds of one design compare
    independent of row order."""
    conn = sqlite3.connect(db_path)
    try:
        return (
            sorted(conn.execute(
                'select src, srcport, dst, dstport, interfaceKey, interfaceName '
                'from connections')),
            sorted(conn.execute(
                'select block, portName, instance, instancePortName, interfaceKey '
                'from connectionMaps')),
            sorted(conn.execute(
                'select distinct blocks.block, blockClocksResets.registerBusPort '
                'from blockClocksResets join blocks '
                'on blocks.blockKey = blockClocksResets.blockKey'), key=repr),
        )
    finally:
        conn.close()


def _swapInstanceLines(design, first, second):
    """`design` with the declarations of instances `first` and `second`
    exchanged."""
    lines = design.split('\n')
    a = next(i for i, line in enumerate(lines) if line.startswith(f"    {first}:"))
    b = next(i for i, line in enumerate(lines) if line.startswith(f"    {second}:"))
    lines[a], lines[b] = lines[b], lines[a]
    return '\n'.join(lines)


def _expect_register_bus_maps(label, design, maps, ports, files=None,
                              connections=None, swap=None):
    """Build `design` and assert the connectionMaps rows of the instances in
    `maps` ({instance: (block, portName, instancePortName, interfaceKey)}),
    the registerBusPort of the blocks in `ports` ({block: port}) and the
    connections into the instances in `connections` ({dst: (src, srcport,
    dstport)}). With `swap` (two instance names), also build `design` with
    those two instances declared in the other order and assert the
    register-bus wiring is identical. `files` ({name: content}) are written
    into the fixture's yaml/ directory alongside top.yaml."""
    fixture, project_path, db_path = _make_fixture(design, files=files)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        failed = False
        gotMaps = _connectionMaps(db_path)
        for instance, expected in maps.items():
            if gotMaps.get(instance) != expected:
                print(f"FAIL: {label}: connectionMap into '{instance}' is "
                      f"{gotMaps.get(instance)}, expected {expected}")
                failed = True
        for block, expected in ports.items():
            got = _registerBusPort(db_path, block)
            if got != expected:
                print(f"FAIL: {label}: {block}'s registerBusPort is {got!r}, "
                      f"expected {expected!r}")
                failed = True
        wiring = _registerBusWiring(db_path)
        gotConnections = {dst: (src, srcport, dstport)
                          for src, srcport, dst, dstport, _key, _name in wiring[0]}
        for dst, expected in (connections or {}).items():
            if gotConnections.get(dst) != expected:
                print(f"FAIL: {label}: connection into '{dst}' is "
                      f"{gotConnections.get(dst)}, expected {expected}")
                failed = True
    finally:
        shutil.rmtree(fixture)
    if swap is not None:
        fixture, project_path, db_path = _make_fixture(
            _swapInstanceLines(design, *swap), files=files)
        try:
            code, output = _build(project_path, db_path)
            if code != 0:
                print(f"FAIL: {label}: with {swap[0]} and {swap[1]} swapped\n{output}")
                return False
            swapped = _registerBusWiring(db_path)
        finally:
            shutil.rmtree(fixture)
        for name, got, expected in zip(
                ('connections', 'connectionMaps', 'registerBusPort'), swapped, wiring):
            if got != expected:
                print(f"FAIL: {label}: {name} rows change when {swap[0]} and "
                      f"{swap[1]} are swapped: {got}, expected {expected}")
                failed = True
    print(f"{'FAIL' if failed else 'PASS'}: {label}")
    return not failed


def _inner_leaf_follows_authored_boundary(label, design, ipRegFile, files=None):
    """The wrapper's inner connectionMap and the leaf's handler connectionMap
    both carry the wrapper's own port 'regs' on its interface 'ipReg',
    declared in `ipRegFile`, and the handler's port takes that name."""
    ipRegKey = f'ipReg/../../yaml/{ipRegFile}'
    return _expect_register_bus_maps(
        label, design,
        {'uLeafA': ('wrapIP', 'regs', 'regs', ipRegKey),
         'u_leafA_regs': ('leafA', 'regs', 'regs', ipRegKey)},
        {'leafA': 'regs'},
        files=files)


def run_passthrough_authored_boundary_inner_leaf_cross_file():
    """The wrapper and its leaf live in child.yaml, which cannot see the
    router's 'apbReg' declared in the including top.yaml."""
    shared = APB_PREAMBLE[:APB_PREAMBLE.index('interfaces:')]
    child = f"""include:
    - shared.yaml

interfaces:
{IP_REG_INTERFACE}
{IP_REG_WRAP}
instances:
    uLeafA:     {{ container: wrapIP, instanceType: leafA }}

{REGISTER}"""
    design = f"""include:
    - shared.yaml
    - child.yaml

interfaces:
    apbReg:
        desc: "APB register bus"
        interfaceType: apb
        structures:
            - {{ structure: apbAddrSt, structureType: addr_t }}
            - {{ structure: apbDataSt, structureType: data_t }}

blocks:
{IP_REG_TOP_INSTANCES}{IP_REG_CONNECTIONS}"""
    return _inner_leaf_follows_authored_boundary(
        "an inferring leaf behind an authored passthrough boundary in "
        "another file takes the boundary's interface",
        design, 'child.yaml', files={'shared.yaml': shared, 'child.yaml': child})


def run_passthrough_authored_boundary_inner_leaf_single_file():
    design = f"""include:
    - shared.yaml

interfaces:
{IP_REG_INTERFACE}
{IP_REG_WRAP}{IP_REG_TOP_INSTANCES}    uLeafA:     {{ container: wrapIP, instanceType: leafA }}
{IP_REG_CONNECTIONS}

{REGISTER}"""
    return _inner_leaf_follows_authored_boundary(
        "an inferring leaf behind an authored passthrough boundary in "
        "the same file takes the boundary's interface",
        design, 'top.yaml')


def _authored_wrapper_two_router_design(inner_decoder_port, leaf_block):
    """The authored wrapper 'wrapIP' holding `leaf_block` (leafA), with one
    wrapper instance under each of routers 'uOuter' (registerDecoderPort
    'apbReg') and 'uInner' (`inner_decoder_port`)."""
    inner_router = render_router(
        'innerDecode', 'mid', register_decoder_port=inner_decoder_port,
        address_increment='0x1000', max_address_spaces=4)
    return f"""include:
    - shared.yaml

blocks:
{render_plain_block('top')}{render_plain_block('mid')}{render_plain_block('cpu')}{render_router('outerDecode', 'top')}{inner_router}{render_leaf('wrapIP')}{leaf_block}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uOuter:     {{ container: top, instanceType: outerDecode }}
    uMid:       {{ container: top, instanceType: mid, addressGroup: top }}
    uInner:     {{ container: mid, instanceType: innerDecode }}
    uWrapTop:   {{ container: top, instanceType: wrapIP, addressGroup: top }}
    uWrapMid:   {{ container: mid, instanceType: wrapIP, addressGroup: mid }}
    uLeafA:     {{ container: wrapIP, instanceType: leafA }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uOuter }}

{REGISTER}"""


def run_authored_wrapper_under_disagreeing_routers_names_leaf_port():
    """The wrapper, not either router, is the plain leaf's nearest boundary
    under both routers, so the leaf and its handler take the wrapper's port
    'regs' whichever router is found first."""
    return _expect_register_bus_maps(
        "a plain leaf behind an authored wrapper reused under two routers "
        "with different registerDecoderPort takes the wrapper's port name",
        _authored_wrapper_two_router_design(
            'customDecoder', render_plain_block('leafA')),
        {'uLeafA': ('wrapIP', 'regs', 'regs', APB_REG_KEY),
         'u_leafA_regs': ('leafA', 'regs', 'regs', APB_REG_KEY)},
        {'leafA': 'regs'},
        connections={'uWrapTop': ('uOuter', 'apbReg_uWrapTop', 'regs'),
                     'uWrapMid': ('uInner', 'customDecoder_uWrapMid', 'regs')},
        swap=('uWrapTop', 'uWrapMid'))


def run_registerports_leaf_under_disagreeing_routers_names_handler_port():
    """A leaf declaring registerPorts: names its handler's port after its
    own key 'regs', so routers with different registerDecoderPort serve it
    alike."""
    return _expect_register_bus_maps(
        "a leaf declaring registerPorts: behind an authored wrapper reused "
        "under two routers with different registerDecoderPort names its "
        "handler's port after its own key",
        _authored_wrapper_two_router_design(
            'customDecoder', render_leaf('leafA')),
        {'uLeafA': ('wrapIP', 'regs', 'regs', APB_REG_KEY),
         'u_leafA_regs': ('leafA', 'regs', 'regs', APB_REG_KEY)},
        {'leafA': 'regs'},
        connections={'uWrapTop': ('uOuter', 'apbReg_uWrapTop', 'regs'),
                     'uWrapMid': ('uInner', 'customDecoder_uWrapMid', 'regs')},
        swap=('uWrapTop', 'uWrapMid'))


def run_authored_wrapper_under_agreeing_routers_names_inner_port():
    """Routers agreeing on registerDecoderPort 'apbReg': the authored
    wrapper, not either router, is the plain leaf's nearest boundary, so
    the leaf and its handler take the wrapper's port 'regs'."""
    return _expect_register_bus_maps(
        "a plain leaf behind an authored wrapper reused under two routers "
        "agreeing on registerDecoderPort takes the wrapper's port name",
        _authored_wrapper_two_router_design('apbReg', render_plain_block('leafA')),
        {'uLeafA': ('wrapIP', 'regs', 'regs', APB_REG_KEY),
         'u_leafA_regs': ('leafA', 'regs', 'regs', APB_REG_KEY)},
        {'leafA': 'regs'},
        swap=('uWrapTop', 'uWrapMid'))


def _two_boundary_design(wrapA, wrapB, interfaces=''):
    """One router serving authored wrappers 'wrapA' and 'wrapB', each
    holding an instance of the same plain leaf 'leafA'."""
    return f"""include:
    - shared.yaml
{interfaces}
blocks:
{render_plain_block('top')}{render_plain_block('cpu')}{ROUTER}{wrapA}{wrapB}{render_plain_block('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uWrapA:     {{ container: top, instanceType: wrapA, addressGroup: top }}
    uWrapB:     {{ container: top, instanceType: wrapB, addressGroup: top }}
    uLeafA1:    {{ container: wrapA, instanceType: leafA }}
    uLeafA2:    {{ container: wrapB, instanceType: leafA }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{REGISTER}"""


def run_leaf_behind_boundaries_with_different_interfaces_rejected():
    interfaces = ("\ninterfaces:\n"
                  + IP_REG_INTERFACE.replace('ipReg:', 'ipRegA:')
                  + IP_REG_INTERFACE.replace('ipReg:', 'ipRegB:'))
    design = _two_boundary_design(
        render_leaf('wrapA', interface='ipRegA'),
        render_leaf('wrapB', interface='ipRegB'), interfaces)
    return _expect_diagnostic(
        "a plain leaf behind two authored boundaries on different "
        "interfaces is rejected, naming each boundary once",
        design,
        ("Block 'leafA' declares no registerPorts: and infers its "
         "register-bus interface from the nearest authored boundary of each "
         "instance, but its instances infer different interfaces",
         "the registerPorts: boundary of block 'wrapA' supplies interface "
         "'ipRegA' (file ../../yaml/top.yaml)",
         "the registerPorts: boundary of block 'wrapB' supplies interface "
         "'ipRegB' (file ../../yaml/top.yaml)",
         "Give the boundaries the same registerPorts: interface, or use a "
         "separate block per boundary: a block has one register port type.",
         'Found 1 Error.'),
        forbidden=("router 'uAPBDecode'",))


def run_leaf_behind_boundaries_with_different_port_names_takes_interface_name():
    """The boundaries offer leafA the names 'regsA' and 'regsB' on one
    interface, so leafA and its handler take the interface name 'apbReg';
    each boundary's inner map feeds it from that boundary's own port."""
    design = _two_boundary_design(
        render_leaf('wrapA', port_name='regsA'),
        render_leaf('wrapB', port_name='regsB'))
    return _expect_register_bus_maps(
        "a plain leaf behind two authored boundaries on one interface with "
        "different port names takes the interface name as its port",
        design,
        {'uLeafA1': ('wrapA', 'regsA', 'apbReg', APB_REG_KEY),
         'uLeafA2': ('wrapB', 'regsB', 'apbReg', APB_REG_KEY),
         'u_leafA_regs': ('leafA', 'apbReg', 'apbReg', APB_REG_KEY)},
        {'leafA': 'apbReg'},
        connections={'uWrapA': ('uAPBDecode', 'apbReg_uWrapA', 'regsA'),
                     'uWrapB': ('uAPBDecode', 'apbReg_uWrapB', 'regsB')},
        swap=('uLeafA1', 'uLeafA2'))


def run_three_level_chain_follows_authored_wrapper():
    """router > authored wrapper > plain container > plain leaf: the plain
    container and the leaf both take the wrapper's port and interface."""
    design = f"""include:
    - shared.yaml

interfaces:
{IP_REG_INTERFACE}
blocks:
{render_plain_block('top')}{render_plain_block('cpu')}{ROUTER}{render_leaf('wrapIP', interface='ipReg')}{render_plain_block('mid')}{render_plain_block('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uWrapIP:    {{ container: top, instanceType: wrapIP, addressGroup: top }}
    uMid:       {{ container: wrapIP, instanceType: mid }}
    uLeafA:     {{ container: mid, instanceType: leafA }}
{IP_REG_CONNECTIONS}
{REGISTER}"""
    ipRegKey = 'ipReg/../../yaml/top.yaml'
    return _expect_register_bus_maps(
        "a plain container and plain leaf chained behind an authored "
        "wrapper both take the wrapper's port and interface",
        design,
        {'uMid': ('wrapIP', 'regs', 'regs', ipRegKey),
         'uLeafA': ('mid', 'regs', 'regs', ipRegKey),
         'u_leafA_regs': ('leafA', 'regs', 'regs', ipRegKey)},
        {'mid': 'regs', 'leafA': 'regs'})


def run_innermost_authored_boundary_wins():
    """router > authored outer wrapper > authored inner wrapper > plain
    leaf: the leaf takes the inner wrapper's port and interface."""
    design = f"""include:
    - shared.yaml

interfaces:
{IP_REG_INTERFACE}
blocks:
{render_plain_block('top')}{render_plain_block('cpu')}{ROUTER}{render_leaf('wrapOuter', port_name='outerRegs')}{render_leaf('wrapInner', port_name='innerRegs', interface='ipReg')}{render_plain_block('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uWrapOuter: {{ container: top, instanceType: wrapOuter, addressGroup: top }}
    uWrapInner: {{ container: wrapOuter, instanceType: wrapInner }}
    uLeafA:     {{ container: wrapInner, instanceType: leafA }}
{IP_REG_CONNECTIONS}
{REGISTER}"""
    ipRegKey = 'ipReg/../../yaml/top.yaml'
    return _expect_register_bus_maps(
        "a plain leaf behind two nested authored boundaries takes the "
        "inner boundary's port and interface",
        design,
        {'uLeafA': ('wrapInner', 'innerRegs', 'innerRegs', ipRegKey),
         'u_leafA_regs': ('leafA', 'innerRegs', 'innerRegs', ipRegKey)},
        {'leafA': 'innerRegs'})


def run_inferred_interface_shadowed_in_leaf_file_rejected():
    """The wrapper's 'ipReg' is declared in wrap.yaml; the leaf's own file
    leaf.yaml declares a different 'ipReg', so the inferred name would
    resolve to the wrong interface where the leaf's handler is emitted."""
    wrap = f"""include:
    - shared.yaml

interfaces:
{IP_REG_INTERFACE}
blocks:
{render_leaf('wrapIP', interface='ipReg')}"""
    leaf = f"""include:
    - shared.yaml

interfaces:
{IP_REG_INTERFACE}
blocks:
{render_plain_block('leafA')}
{REGISTER}"""
    design = f"""include:
    - shared.yaml
    - wrap.yaml
    - leaf.yaml

blocks:
{IP_REG_TOP_INSTANCES}    uLeafA:     {{ container: wrapIP, instanceType: leafA }}
{IP_REG_CONNECTIONS}"""
    return _expect_diagnostic(
        "an inferred interface name that resolves to a different interface "
        "in the leaf's own file is rejected",
        design,
        ("Block 'leafA' declares no registerPorts: and infers register-bus "
         "interface 'ipReg' declared in file ../../yaml/wrap.yaml, but in "
         "file ../../yaml/leaf.yaml, where its register-bus rows are "
         "synthesised, that name resolves to the interface declared in file "
         "../../yaml/leaf.yaml.",
         "declare registerPorts: on block 'leafA'.",
         'Found 1 Error.'),
        files={'wrap.yaml': wrap, 'leaf.yaml': leaf})



# wrap.yaml declares 'ipReg' and the authored wrapper 'wrapIP' on it; the
# plain leaf 'leafA' behind it infers 'ipReg'.
IP_REG_WRAP_FILE = f"""include:
    - shared.yaml

interfaces:
{IP_REG_INTERFACE}
blocks:
{render_leaf('wrapIP', interface='ipReg')}"""

# leaf.yaml sees wrap.yaml's 'ipReg', so the leaf's own handler rows resolve.
IP_REG_LEAF_FILE = f"""include:
    - shared.yaml
    - wrap.yaml

blocks:
{render_plain_block('leafA')}
{REGISTER}"""


def _wrapped_leaf_top(interfaces=''):
    """top.yaml declaring instance 'uLeafA' inside 'wrapIP'; its passthrough
    connectionMap is synthesised here."""
    return f"""include:
    - shared.yaml
    - wrap.yaml
    - leaf.yaml
{interfaces}
blocks:
{IP_REG_TOP_INSTANCES}    uLeafA:     {{ container: wrapIP, instanceType: leafA }}
{IP_REG_CONNECTIONS}"""


def run_inferred_interface_shadowed_in_instance_file_rejected():
    """The leaf's own file resolves 'ipReg' to the wrapper's interface, but
    top.yaml, which declares instance 'uLeafA' and so receives its
    passthrough connectionMap, declares a different 'ipReg'."""
    interfaces = ("\ninterfaces:\n"
                  + IP_REG_INTERFACE.replace('IP-local APB register bus', 'top-local shadow'))
    return _expect_diagnostic(
        "an inferred interface name that resolves to a different interface "
        "in the file declaring the inner instance is rejected",
        _wrapped_leaf_top(interfaces),
        ("Block 'leafA' declares no registerPorts: and infers register-bus "
         "interface 'ipReg' declared in file ../../yaml/wrap.yaml, but in "
         "file ../../yaml/top.yaml, where its register-bus rows are "
         "synthesised, that name resolves to the interface declared in file "
         "../../yaml/top.yaml.",
         'Found 1 Error.'),
        files={'wrap.yaml': IP_REG_WRAP_FILE, 'leaf.yaml': IP_REG_LEAF_FILE})


def run_inferred_interface_not_visible_in_instance_file_rejected():
    """router > wrapIP > mid > mid2 > leafA: mid.yaml declares the plain
    containers and instance 'uMid2' but sees no 'ipReg', so the
    passthrough connectionMap into 'uMid2' cannot name it."""
    mid = f"""include:
    - shared.yaml

blocks:
{render_plain_block('mid')}{render_plain_block('mid2')}
instances:
    uMid2:      {{ container: mid, instanceType: mid2 }}
"""
    leaf = f"""include:
    - shared.yaml
    - wrap.yaml
    - mid.yaml

blocks:
{render_plain_block('leafA')}
instances:
    uLeafA:     {{ container: mid2, instanceType: leafA }}

{REGISTER}"""
    design = f"""include:
    - shared.yaml
    - wrap.yaml
    - mid.yaml
    - leaf.yaml

blocks:
{IP_REG_TOP_INSTANCES}    uMid:       {{ container: wrapIP, instanceType: mid }}
{IP_REG_CONNECTIONS}"""
    return _expect_diagnostic(
        "an inferred interface name not visible in the file declaring the "
        "inner instance is rejected",
        design,
        ("Block 'mid2' declares no registerPorts: and infers register-bus "
         "interface 'ipReg' declared in file ../../yaml/wrap.yaml, but in "
         "file ../../yaml/mid.yaml, where its register-bus rows are "
         "synthesised, no interface of that name is visible.",
         'Found 1 Error.'),
        files={'wrap.yaml': IP_REG_WRAP_FILE, 'mid.yaml': mid, 'leaf.yaml': leaf})


def run_inferred_interface_through_include_builds():
    """top.yaml sees the wrapper's 'ipReg' only through its include of
    wrap.yaml, which is the same interface."""
    return _inner_leaf_follows_authored_boundary(
        "an inferred interface visible through an include in the file "
        "declaring the inner instance builds",
        _wrapped_leaf_top(), 'wrap.yaml',
        files={'wrap.yaml': IP_REG_WRAP_FILE, 'leaf.yaml': IP_REG_LEAF_FILE})


def run_inferred_interface_through_diamond_include_builds():
    """'ipReg' lives in ifc.yaml, included by wrap.yaml and leaf.yaml, both
    included by top.yaml: every file resolves it to the one interface."""
    ifc = f"""include:
    - shared.yaml

interfaces:
{IP_REG_INTERFACE}"""
    wrap = f"""include:
    - shared.yaml
    - ifc.yaml

blocks:
{render_leaf('wrapIP', interface='ipReg')}"""
    leaf = f"""include:
    - shared.yaml
    - ifc.yaml

blocks:
{render_plain_block('leafA')}
{REGISTER}"""
    return _inner_leaf_follows_authored_boundary(
        "an inferred interface reached through a diamond include builds",
        _wrapped_leaf_top(), 'ifc.yaml',
        files={'ifc.yaml': ifc, 'wrap.yaml': wrap, 'leaf.yaml': leaf})


def _mixed_source_design(wrap_interface, leaf_block):
    """'leafA' served directly by router 'uAPBDecode' (instance
    'uLeafDirect') and also behind the authored wrapper 'wrapIP' on
    `wrap_interface` (instance 'uLeafA')."""
    return f"""include:
    - shared.yaml

interfaces:
{IP_REG_INTERFACE}
blocks:
{render_plain_block('top')}{render_plain_block('cpu')}{ROUTER}{render_leaf('wrapIP', interface=wrap_interface)}{leaf_block}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uWrapIP:    {{ container: top, instanceType: wrapIP, addressGroup: top }}
    uLeafDirect: {{ container: top, instanceType: leafA, addressGroup: top }}
    uLeafA:     {{ container: wrapIP, instanceType: leafA }}
{IP_REG_CONNECTIONS}
{REGISTER}"""


# The router's interface as the disagreement lists it.
MIXED_ROUTER_SOURCE = ("router 'uAPBDecode' (block 'apbDecode') supplies "
                       "interface 'apbReg' (file ../../yaml/shared.yaml)")


def run_leaf_under_router_and_boundary_different_interfaces_rejected():
    return _expect_diagnostic(
        "a plain leaf served by a router and by an authored boundary on "
        "another interface is rejected, naming the router's interface",
        _mixed_source_design('ipReg', render_plain_block('leafA')),
        (MIXED_ROUTER_SOURCE,
         "the registerPorts: boundary of block 'wrapIP' supplies interface "
         "'ipReg' (file ../../yaml/top.yaml)",
         "Make the registerPorts: boundary of block 'wrapIP' use interface "
         "'apbReg', the upstreamPort interface of router 'uAPBDecode', or "
         "use a separate block per boundary: a block has one register port type.",
         'Found 1 Error.'),
        forbidden=('Give the boundaries the same registerPorts: interface',))


def run_leaf_under_router_and_boundary_different_port_names_takes_interface_name():
    """The router offers leafA 'apbReg' and the boundary offers 'regs' on
    the same interface, so leafA takes the interface name 'apbReg'."""
    return _expect_register_bus_maps(
        "a plain leaf served by a router and by an authored boundary on "
        "the same interface with another port name takes the interface name",
        _mixed_source_design('apbReg', render_plain_block('leafA')),
        {'uLeafA': ('wrapIP', 'regs', 'apbReg', APB_REG_KEY),
         'u_leafA_regs': ('leafA', 'apbReg', 'apbReg', APB_REG_KEY)},
        {'leafA': 'apbReg'},
        connections={'uLeafDirect': ('uAPBDecode', 'apbReg_uLeafDirect', 'apbReg'),
                     'uWrapIP': ('uAPBDecode', 'apbReg_uWrapIP', 'regs')},
        swap=('uLeafDirect', 'uLeafA'))


def run_registerports_leaf_under_router_and_boundary_builds():
    return _expect_register_bus_maps(
        "a leaf declaring registerPorts: served by a router and by an "
        "authored boundary builds",
        _mixed_source_design('apbReg', render_leaf('leafA')),
        {'uLeafA': ('wrapIP', 'regs', 'regs', APB_REG_KEY),
         'u_leafA_regs': ('leafA', 'regs', 'regs', APB_REG_KEY)},
        {'leafA': 'regs'},
        swap=('uLeafDirect', 'uLeafA'))


def run_leaf_under_routers_with_different_interfaces_rejected():
    """Two routers agreeing on registerDecoderPort but on different
    upstreamPort interfaces, with no authored boundary to change."""
    inner_router = render_router(
        'innerDecode', 'mid', upstream_port='ipReg',
        address_increment='0x1000', max_address_spaces=4)
    design = f"""include:
    - shared.yaml

interfaces:
{IP_REG_INTERFACE}
blocks:
{render_plain_block('top')}{render_plain_block('mid')}{render_plain_block('cpu')}{render_router('outerDecode', 'top')}{inner_router}{render_plain_block('leafA')}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uOuter:     {{ container: top, instanceType: outerDecode }}
    uMid:       {{ container: top, instanceType: mid, addressGroup: top }}
    uInner:     {{ container: mid, instanceType: innerDecode }}
    uLeafATop:  {{ container: top, instanceType: leafA, addressGroup: top }}
    uLeafAMid:  {{ container: mid, instanceType: leafA, addressGroup: mid }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uOuter }}

{REGISTER}"""
    return _expect_diagnostic(
        "a plain leaf served by two routers on different interfaces is "
        "rejected without boundary advice",
        design,
        ("router 'uOuter' (block 'outerDecode') supplies interface "
         "'apbReg' (file ../../yaml/shared.yaml)",
         "router 'uInner' (block 'innerDecode') supplies interface "
         "'ipReg' (file ../../yaml/top.yaml)",
         "Use a separate block per boundary: a block has one register port type.",
         'Found 1 Error.'),
        forbidden=('Give the boundaries', 'Make the registerPorts: boundary'))

def _run():
    print("=" * 72)
    print("TESTING GENERATED REGISTER-DECODE CLOCK DOMAIN")
    print("=" * 72)
    results = [runner() for runner in (
        run_no_map_default_clock,
        run_router_bound_to_non_default_clock,
        run_reusable_ip_bus_mismatch_rejected,
        run_reusable_ip_register_port_clock_rename,
        run_object_access_keeps_its_own_domain,
        run_feed_at_container_instance,
        run_composed_child_respells_the_clock,
        run_child_harness_accessor_domain_not_checked,
        run_child_harness_accessor_without_default_clock_rejected,
        run_top_down_leaf_register_port_selection,
        run_top_down_leaf_tie_by_declaration_order,
        run_top_down_leaf_no_clock_match_rejected,
        run_top_down_leaf_no_reset_match_rejected,
        run_top_down_leaf_instances_disagree_rejected,
        run_register_bus_reset_missing_rejected,
        run_router_addressblock_reset_override_not_duplicated,
        run_reusable_ip_authored_reset_mismatch_rejected,
        run_served_leaf_registerclock_name_coincidence_not_renamed,
        run_register_port_reset_undeclared_rejected,
        run_router_addressblock_clock_undeclared_rejected,
        run_passthrough_container_resolves_bus_clock,
        run_passthrough_inner_leaf_bus_mismatch_rejected,
        run_passthrough_container_bus_mismatch_rejected,
        run_passthrough_reusable_ip_container_inner_leaf_port,
        run_passthrough_container_instances_disagree_rejected,
        run_passthrough_reused_under_disagreeing_routers_takes_interface_name,
        run_leaf_reused_under_disagreeing_routers_takes_interface_name,
        run_passthrough_reused_under_agreeing_routers_builds,
        run_leaf_reused_under_agreeing_routers_builds,
        run_passthrough_authored_boundary_inner_leaf_cross_file,
        run_passthrough_authored_boundary_inner_leaf_single_file,
        run_authored_wrapper_under_disagreeing_routers_names_leaf_port,
        run_registerports_leaf_under_disagreeing_routers_names_handler_port,
        run_authored_wrapper_under_agreeing_routers_names_inner_port,
        run_leaf_behind_boundaries_with_different_interfaces_rejected,
        run_leaf_behind_boundaries_with_different_port_names_takes_interface_name,
        run_three_level_chain_follows_authored_wrapper,
        run_innermost_authored_boundary_wins,
        run_inferred_interface_shadowed_in_leaf_file_rejected,
        run_inferred_interface_shadowed_in_instance_file_rejected,
        run_inferred_interface_not_visible_in_instance_file_rejected,
        run_inferred_interface_through_include_builds,
        run_inferred_interface_through_diamond_include_builds,
        run_leaf_under_router_and_boundary_different_interfaces_rejected,
        run_leaf_under_router_and_boundary_different_port_names_takes_interface_name,
        run_registerports_leaf_under_router_and_boundary_builds,
        run_leaf_under_routers_with_different_interfaces_rejected,
    )]
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
