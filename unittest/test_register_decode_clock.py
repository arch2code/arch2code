#!/usr/bin/env python3
"""Coverage for the clock domain of a generated register-decode tree
(spec-clock-reset-requirements.md §4.3, R25, V8, V25, V26).

A router or a synthesised `<block>_regs` handler does not inherit its domain
from a clock: literal stamped onto a synthesised connection; clocks are
block-scoped, and the project-scoped `clock:` fields that mechanism depended
on do not exist: a router's own domain is bound like any other instance, by an
ordinary `clocks:`/`resets:` map on the router instance itself, and a
handler's domain follows automatically - the leaf's own declared
`registerPorts:` clock for a reusable IP, or the R25 selection for a
top-down leaf.

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
import pysrc.intf_gen_utils as intf_gen_utils
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
# the BLOCK that carries them (spec R5); the project's own clocks:/resets:
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

# The router bound onto 'top's non-default clock by an ordinary instance map -
# the only mechanism a router's own domain uses now.
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
# default clock) is left on 'top's clk instead. V8 (spec §4.3, "a register
# bus tree is one domain throughout").
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
# (block-local, rule 1) and whose instance map renames THAT clock onto the
# router's own bus clock (item 2 regression: the router-to-leaf dispatch
# connection used to stamp this block-local name onto its own container-
# scoped clock:, which V13 then rejected as soon as the map renamed it away
# from the literal name 'regClk').
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
# declaring and binding its OWN clock (spec R5: nothing is derived onto a
# block from a connection any more); the leaf itself carries both its bus
# domain and theirs. leafA additionally declares objClk so its memory (V8
# requires the memory's own clock: to name one of the OWNING block's clocks)
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
# infers its register-bus port from the serving router (R25). 'sampler'
# declares two clocks; its instance map binds clkCap, not the default clk,
# onto the router's own apbClk - so the register port is clkCap (V8/R25).
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
# resolves its register bus top-down (R25) like a leaf, through the
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
    EFFECTIVE input clocks/resets by name (spec §4.8, R3): the testbench
    binds the top block by name match, so a fixture's project file needs a
    same-named entry for everything the top block's own declaration has -
    including the implicit clk/rst_n a block with no clocks:/resets: gets
    (spec R5) - or an input clock/reset the block declares has nothing to
    bind to (V10/V3). `default: true` is derived from the block's own
    declaration - its default clock, and the reset marked default (or the
    sole candidate) ON that clock - never merely "declared first": a fixture
    whose first declared reset happens to sit on a non-default clock would
    otherwise mark a default reset that does not belong to the default
    clock, which V23 requires (spec §4.1).
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
            f"first' is not a substitute (spec §4.1, V23).")
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


def _make_fixture(design, top_instance='uTop', child=None):
    """Write a design fixture into a fresh temp dir outside the repo tree.

    `child` adds a second project owning its own arch file, instantiated by
    the assembler, so a synthesised handler lands in the child's own context.

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
    instantiated (spec R5), so this is the only place "which clock a router
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
    blockClocksResets rows (clockTree.py's R25/rule-1 result): a router's or a
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


def _expect_diagnostic(label, design, needles):
    fixture, project_path, db_path = _make_fixture(design)
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
    print(f"PASS: {label}")
    return True


# A reusable-IP leaf whose registerPorts: names a reset the block does not
# declare, and a router whose addressBlock: names a clock it does not
# declare: both are the schema's blockClock/blockReset combo foreign key
# (V2's existence part), reported in the parser's "not valid in context" form.
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
    # childPort reads 'apbClk', not the router's own raw declared 'clk': the
    # router's own emitted module port is renamed to its bus clock/reset
    # (intf_gen_utils.py's bus_clock_reset_port_data), so the persisted bind
    # a container's own instantiation reads must use that same name (spec
    # §4.3 "Registers"/"Routers") - clockTree.py's rows() bakes the rename
    # in directly.
    return _case(
        "an ordinary instance map binds the router (and its served reusable-IP "
        "leaf's own default clock) onto a non-default clock",
        FEED_ON_NON_DEFAULT_CLOCK,
        {'uAPBDecode': {'apbClk': 'apbClk'}})


def run_reusable_ip_bus_mismatch_rejected():
    return _expect_diagnostic(
        "a reusable-IP leaf whose registerPorts: clock does not sit on the "
        "router's actual bus clock is rejected",
        FEED_MISMATCH,
        ('leafA', 'clk', 'V8'))


def run_reusable_ip_register_port_clock_rename():
    """A reusable IP's registerPorts: clock: (block-local, rule 1), renamed
    onto the bus by an ordinary instance map, builds clean and the handler
    binds through it - the router-to-leaf dispatch connection states no
    clock: of its own (config/postParseRegisterPorts.py), so there is
    nothing for V13 to falsely reject against the renamed name."""
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
        # uAPBDecode's own port reads 'apbClk' (its emitted module port is
        # renamed to its bus clock, spec §4.3 "Registers"/"Routers"); uLeafA
        # is an ordinary
        # reusable-IP instance, never renamed, so its own port stays 'clk'.
        got = binds.get('uAPBDecode', {}).get('apbClk')
        if got != 'apbClk':
            print(f"FAIL: {label}: instance 'uAPBDecode' port 'apbClk' "
                  f"binds to {got!r}, expected 'apbClk'")
            failed = True
        got = binds.get('uLeafA', {}).get('clk')
        if got != 'apbClk':
            print(f"FAIL: {label}: instance 'uLeafA' port 'clk' "
                  f"binds to {got!r}, expected 'apbClk'")
            failed = True
        # The router's own bus clock/reset is the CONTAINER's (ipBlock's own)
        # net name (spec §4.3 "Routers"): its instance is one level below the
        # design root, and this is the fact that walk must still resolve.
        routerBus = _registerBusDomain(db_path, 'apbDecode')
        if routerBus != ('apbClk', 'apbRst_n'):
            print(f"FAIL: {label}: apbDecode's bus clock/reset is {routerBus}, "
                  f"expected ('apbClk', 'apbRst_n')")
            failed = True
        # The handler's own bus clock/reset mirrors leafA's own registerPorts:
        # selection - leafA's OWN clock/reset port NAME (spec §4.3 rule 1),
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
        # its own default clock/reset port NAME (spec §4.3 rule 1) - and the
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


def run_top_down_leaf_register_port_selection():
    # childPort reads 'clkCap' (the selected register clock), not the
    # handler's own raw implicit 'clk': the handler's own emitted module
    # port is renamed the same way a router's is (spec §4.3
    # "Registers"/"Routers").
    return _case(
        "a top-down leaf's register port is the clock its map binds to the bus, "
        "not the block default (R25)",
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
        ('sampler', 'V8'))


def run_top_down_leaf_no_reset_match_rejected():
    # apbClk carries two resets, apbRst_n marked default (the selected reset)
    # and apbRst2_n not: clkCap correctly resolves to the bus clock, but its
    # own reset is bound to apbRst2_n, a reset of the right clock (V6 is
    # satisfied) yet not the bus's SELECTED one (V25).
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
        ('sampler', 'V25'))


def run_top_down_leaf_instances_disagree_rejected():
    """Two instances of the same top-down leaf resolving to different
    clock/reset pairs is rejected (V26): the leaf module is generated once."""
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
        ('sampler', 'uSamplerA', 'uSamplerB', 'V26'))


def run_register_bus_reset_missing_rejected():
    """V19: a block clock hosting a register bus must have a selected
    reset. The router itself declares resets: {} (no reset at all), so its
    bus clock resolves (registerClock) but has no reset to select
    (registerReset stays None) - its own reset port is simply unbound. A
    reusable-IP leaf's own resets: {} is not used for this: the leaf still
    needs its synthesised handler's implicit rst_n to fall back onto ONE of
    the leaf's own resets regardless (V11 fires first, cascading), so the
    router is the clean, isolated V19 case."""
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
        "clock (V19)",
        design,
        ('apbDecodeNR', 'V19'))


def run_router_addressblock_reset_override_not_duplicated():
    """intf_gen_utils.bus_clock_reset_port_data (item 4): a router
    declaring more than one reset on its bus clock, with addressBlock:
    reset: naming the NON-default one as the bus reset, must rename that
    named port to the bus name - not block_data['defaultReset'] (the
    block's own marked default, 'rst_n' here), which would rename the
    wrong row and leave two ports both named the bus reset."""
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
    label = ("a router's addressBlock: reset: override renames the named "
             "reset, not the block's own default, so the bus reset is not "
             "duplicated in the emitted port list")
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
        data = intf_gen_utils.bus_clock_reset_port_data(view, view['busClock'], view['busReset'])
        names = [row['reset'] for row in data['resets']]
        failed = False
        if names.count(view['busReset']) != 1:
            print(f"FAIL: {label}: bus reset {view['busReset']!r} appears "
                  f"{names.count(view['busReset'])} times in {names}, expected once")
            failed = True
        if 'rst_n' not in names:
            print(f"FAIL: {label}: the router's own default reset 'rst_n' "
                  f"is missing from {names}, it must keep its own name")
            failed = True
        print(f"{'FAIL' if failed else 'PASS'}: {label}")
        return not failed
    finally:
        shutil.rmtree(fixture)


def run_reusable_ip_authored_reset_mismatch_rejected():
    """V25 for a reusable IP: registerPorts: reset: authors a reset that is
    not bound to the same container reset as the serving router's own bus
    reset. leafE names 'regRst2_n' explicitly (its own clock regClk agrees
    with the bus, so V8's clock check passes), but its instance map puts
    regRst2_n on 'top's apbRst2_n, not the router's own selected
    apbRst_n - a second reset on the SAME container clock as the bus reset,
    so this isolates V25 from V6 (clock membership) and V19 (a reset
    exists, just the wrong one)."""
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
        ('leafE', 'regRst2_n', 'V25'))


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
        ('sampler', 'V8'))


def run_passthrough_container_bus_mismatch_rejected():
    design = _passthrough_sampler_design(
        "clocks: { clkW: clk },\n                  resets: { rstW_n: rst_n }",
        "clocks: { clkCap: clkW },\n                  resets: { rstCap_n: rstW_n }")
    return _expect_diagnostic(
        "a passthrough container whose clock does not sit on the router's "
        "actual bus clock is rejected",
        design,
        ('wrap', 'V8'))


# A reusable-IP passthrough container: registerPorts: { regs: ... }, owns
# no registers of its own, and hosts a top-down inner leaf. Its own
# boundary port is 'regs' (its authored registerPorts: key); the inner
# leaf's port is the one postParseRegisterPorts synthesises for it
# (REGAPB_PASSTHROUGH's innerPortName), the router's registerDecoderPort
# 'apbReg' - not the container's own key.
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
    """A reusable-IP passthrough container's own registerPorts: key and
    its inner leaf's synthesised port name are distinct; both resolve
    their register clock/reset through the container."""
    label = ("a reusable-IP passthrough container and the top-down leaf "
             "behind it keep separate register-bus port names")
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
        if leafPort != 'apbReg':
            print(f"FAIL: {label}: sampler's registerBusPort is "
                  f"{leafPort!r}, expected 'apbReg'")
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
    clock/reset pairs are rejected (V26); the container's registerClock is
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
        ('wrap', 'V26'))


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
