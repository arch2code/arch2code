#!/usr/bin/env python3
"""Coverage for clock and reset PORT EMISSION (plan-multi-clock-reset.md §5).

No shipped example declares a second clock domain on a block or a connection, so
the multi-domain spellings this suite asserts are otherwise unexercised: every
example's block module emits the single default `input clk, rst_n`, which is
byte-identical to what the generator emitted before the derived sets reached the
emitters.

One fixture is built and generated, then the emitted text is read back:
  - a leaf living wholly in a non-default domain, whose port list names neither
    `clk` nor `rst_n`;
  - a leaf in three domains authoring a reset in each, which is the only shape
    where the canonical order, the per-clock period/timeUnit, the per-reset
    release count, and the pairing of a reset with its OWN clock are all
    distinguishable;
  - a leaf in two domains that authors no resets: and therefore derives the reset
    of each;
  - the container instantiating all three, which must bind each child's OWN
    clock and reset port names;
  - a fourth leaf owned by a VENDORED CHILD PROJECT whose default clock and reset
    are named ipClk / ipRst_n. The two sides of a bind are two spellings of one
    domain, and within a single project they always coincide, so the composed
    child is the only shape in which the child's port name and the container's
    signal name are distinguishable at all.

A second fixture covers the two generators of a decode tree — the `<block>_regs`
register handler and the `apbDecode` router — built twice: with the register-bus
feed in a non-default domain and with no feed clock at all. A generated decode
tree inherits the feed's domain, so those two builds are the non-default-domain
and default-domain shapes of both generators, and each module must spell the same
clock in its port list and in every flop. The non-default-domain build is a real
one, not a shape that collapses to `clk`: its router and handler both declare
`clkSlow` and neither declares `clk` at all, so an emitter left on the bare macro
(which captures the identifier `clk`) fails there.

The flop macro library itself is checked as library content, discovered rather
than listed, so a family added to `common/systemVerilog/flops.sv` is covered
without editing this suite.

The port style belongs to the GENERATOR, not to the kind of module it emits: the
block module generator joins clocks and resets onto one `input`, the verilated SV
wrapper generator declares one per line, and `<block>_regs` is a third generator
declaring one per line in an RTL module. The two generators under test here are
therefore asserted with disjoint patterns, each named for the generator it
covers, so neither helper can be pointed at a third one. What is shared, and what
these cases really pin, is the ORDER.

Assertions are on emitted text, never on generation merely succeeding: a
generator that emits an empty port list succeeds too.

Fixtures are written OUTSIDE the repository working tree: git does not track
empty directories, so a fixture left under unittest/ is a stray directory
`git status` never reports. Cleanup deliberately does not suppress errors.
"""

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

from templates.systemc.module_hdl_wrapper import SC_TIME_UNIT
from _addrctl_helpers import (APB_PREAMBLE, render_leaf, render_plain_block,
                              render_router)

ARCH2CODE = os.path.join(base_dir, 'arch2code.py')
FLOPS_SV = os.path.join(base_dir, 'common', 'systemVerilog', 'flops.sv')

# Three clocks whose periods and units all differ, and one reset per clock, two of
# them with different release counts. A reset in every domain is now required of
# any project whose blocks span those domains: every block holds a reset in each
# clock it carries, whether it authors a resets: list or derives one, so a domain
# with no reset is an error either way. Declaration order is the record: the
# canonical order is the default first, then declaration order, so clk, clkSlow,
# clkPico is what a port list must read.
PROJECT = """yamlFormat: 2
projectName: emitTest
topInstance: top_tb

projectFiles:
    - ../../ip/prj/yaml/ipProject.yaml
    - ../../yaml/top.yaml

clocks:
    clk:     { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    clkSlow: { desc: "a slower, non-commensurate clock", period: 3, timeUnit: ns }
    clkPico: { desc: "a clock declared in a unit other than ns", period: 500, timeUnit: ps }

resets:
    rst_n:     { desc: "the default reset", default: true, clock: clk }
    rstSlow_n: { desc: "the slow-domain reset", clock: clkSlow, releaseCycles: 5 }
    rstPico_n: { desc: "the pico-domain reset", clock: clkPico }

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

# The child half of the composed fixture: a reusable leaf owned by another
# project whose default clock and reset are named ipClk / ipRst_n. Its own
# derived set is spelled in ITS project (name-else-default), so the assembler
# instantiating it has to bind ipClk / ipRst_n to its own clk / rst_n.
# No topInstance: the assembling project owns every instance.
IP_PROJECT = """yamlFormat: 2
projectName: emitIp

projectFiles:
    - ../../yaml/emitIp.yaml

clocks:
    ipClk: { desc: "the child project's default clock, named nothing the assembler declares", default: true, period: 7, timeUnit: ns }

resets:
    ipRst_n: { desc: "the child project's default reset", default: true, clock: ipClk }

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

IP_DESIGN = """types:
    ipDataT: { width: 8, desc: "payload word" }

structures:
    ipDataSt:
        data: { varType: ipDataT, desc: "payload word" }

interfaces:
    ipDataIf:
        desc: "child IP producer stream"
        interfaceType: push_ack
        structures:
            - { structure: ipDataSt, structureType: data_t }

blocks:
    ipLeaf:
        desc: "reusable producer owned by the child project"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        ports:
            ipOut: { interface: ipDataIf, direction: src }
"""

# The container generates RTL: its instantiation of each child is the emission
# site that has to bind the child's OWN clock and reset port names, and the
# module header and the child binds sit in ONE generated region, so nothing here
# can be patched by hand.
DESIGN = """include:
    - ../ip/yaml/emitIp.yaml

ipParameters:
  constants:
    depth: { value: 8, maxValue: 8, desc: "per-instance depth of the slow producer" }

types:
    dataT: { width: 8, desc: "payload word" }

structures:
    dataSt:
        data: { varType: dataT, desc: "payload word" }

interfaces:
    dataIf:
        desc: "producer to consumer stream"
        interfaceType: push_ack
        structures:
            - { structure: dataSt, structureType: data_t }

blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:    { desc: "container of the leaves", hasVl: false, hasMdl: false, hasTb: false, hasRtl: true }
    slowProd:
        desc: "producer living wholly in the slow domain, with the slow reset"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        params: [depth]
        resets: [rstSlow_n]
    fastProd:
        desc: "producer in three domains carrying a reset in each"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        clocks: [clkSlow, clkPico]
        resets: [rst_n, rstSlow_n, rstPico_n]
    cons:
        desc: "consumer reached from both domains, with the default reset"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true

instances:
    top_tb: { container: top_tb, instanceType: top_tb,   instGroup: top }
    u_dut:  { container: top_tb, instanceType: dut,      instGroup: top }
    uSlow:  { container: dut,    instanceType: slowProd, instGroup: top, variant: slowVariant }
    uFast:  { container: dut,    instanceType: fastProd, instGroup: top }
    uCons:  { container: dut,    instanceType: cons,     instGroup: top }
    uIpLeaf: { container: dut,   instanceType: ipLeaf,   instGroup: top }

connections:
    - { interface: dataIf, src: uSlow, srcport: out, dst: uCons, dstport: slowIn, clock: clkSlow }
    - { interface: dataIf, src: uFast, srcport: out, dst: uCons, dstport: fastIn }
    - { interface: ipDataIf, src: uIpLeaf, srcport: ipOut, dst: uCons, dstport: ipIn }

parameters:
    slowProd:
        slowVariant:
            depth: 8
"""

# The SV wrapper body per block. slowProd is parameterizable, so its body is the
# include-only .svh and a per-variant trampoline top wires the flattened ports
# through to it - a second emission site for the same clock/reset list.
SV_WRAPPER = {'slowProd': 'verif/slowProd_hdl_sv_wrapper.svh',
              'fastProd': 'verif/fastProd_hdl_sv_wrapper.sv',
              'cons': 'verif/cons_hdl_sv_wrapper.sv'}
SV_TRAMPOLINE = 'verif/slowProd_slowVariant_hdl_sv_wrapper.sv'

# Every generated file this suite reads, relative to the fixture root, keyed by
# the arch2code language switch that renders it.
CONTAINER = 'rtl/dut.sv'
# The child project scaffolds and renders through its OWN database, exactly as a
# vendored IP does in tree: the assembler's --newmodule does not scaffold another
# project's files. The standalone build is also what makes the assertion mean
# something - the leaf's port list has to be the same emitted standalone as the
# spelling the assembler binds, which is the phase-1 boundary rule.
IP_LEAF = 'ip/rtl/ipLeaf.sv'

GENERATED = {
    '--systemVerilog': ['rtl/top_package.sv',
                        'rtl/slowProd.sv', 'rtl/fastProd.sv', 'rtl/cons.sv',
                        CONTAINER,
                        *SV_WRAPPER.values(), SV_TRAMPOLINE],
    '--systemc': ['verif/slowProd_hdl_sc_wrapper.h',
                  'verif/fastProd_hdl_sc_wrapper.h',
                  'verif/cons_hdl_sc_wrapper.h'],
}


# ------------------------------------------------- <block>_regs fixture --
#
# The default reset is deliberately NOT named rst_n and the bus clock is not the
# default clock, so neither name in the handler's emitted text could have come
# from a literal in the template. The bus domain carries its own reset, which is
# the only reset a generated handler or router in that domain can take: neither
# can author a resets: list, so each takes the reset of the clock it carries.
REGS_PROJECT = """yamlFormat: 2
projectName: regsEmit
topInstance: uTop

projectFiles:
    - ../../yaml/shared.yaml
    - ../../yaml/top.yaml

clocks:
    clk:     { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    clkSlow: { desc: "the register-bus clock", period: 3, timeUnit: ns }

resets:
    rstMain_n: { desc: "the default reset, deliberately not spelled rst_n", default: true, clock: clk }
    rstBus_n:  { desc: "the register-bus reset, the only one in the bus domain", clock: clkSlow }

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

# The routed leaf carries a fixed-width and a parameterizable register, and a
# fixed-width and a parameterizable firmware-accessible memory, which is what it
# takes to reach every flop-emitting path the handler generator has: the direct
# per-segment register flop, the generate-guarded per-word flop shared by
# parameterizable registers and memories, the two memory access sequences, and
# the APB ready pipeline.
#
# regAccessor reaches the register from the DEFAULT domain, so the leaf spans two
# clocks while its handler spans one - which is what separates the handler's own
# derived set from its owning block's.
REGS_DESIGN = """include:
    - shared.yaml

ipParameters:
    constants:
        CFG_WIDTH: {{ value: 40, maxValue: 64, desc: "per-instance payload width" }}
    types:
        wideT:
            width: CFG_WIDTH
            maxBitwidth: 64
            desc: "parameterizable payload word"

constants:
    TBL_WORDS: {{ value: 8, desc: "memory wordlines" }}

types:
    memAddrT: {{ width: 3, desc: "memory address" }}

structures:
    memAddrSt:
        address: {{ varType: memAddrT, generator: address, desc: "memory address" }}
    memSt:
        data: {{ varType: wideT, generator: memory, desc: "parameterizable memory payload" }}
    fixedMemSt:
        data: {{ varType: cfgT, generator: memory, desc: "fixed-width memory payload" }}
    wideRegSt:
        value: {{ varType: wideT, generator: register, desc: "parameterizable register payload" }}

blocks:
{blocks}
instances:
    uTop:         {{ container: top, instanceType: top }}
    uCPU:         {{ container: top, instanceType: cpu }}
    uAPBDecode:   {{ container: top, instanceType: apbDecode }}
    uLeafA:       {{ container: top, instanceType: leafA, addressGroup: top, variant: wide }}
    uRegAccessor: {{ container: top, instanceType: regAccessor }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode{feed_clock} }}

registers:
    - {{ register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "leafA fixed-width configuration" }}
    - {{ register: cfgWide, regType: rw, block: leafA, structure: wideRegSt, desc: "leafA parameterizable configuration" }}

memories:
    - {{ memory: tbl, block: leafA, structure: memSt, addressStruct: memAddrSt, wordLines: TBL_WORDS, ports: [p], regAccess: true, desc: "leafA parameterizable table" }}
    - {{ memory: tblFixed, block: leafA, structure: fixedMemSt, addressStruct: memAddrSt, wordLines: TBL_WORDS, ports: [p], regAccess: true, desc: "leafA fixed-width table" }}

registerConnections:
    - {{ register: cfgA, block: leafA, instance: uRegAccessor }}

parameters:
    leafA:
        wide:
            CFG_WIDTH: 40
"""

REGS_HANDLER = 'rtl/leafA_regs.sv'
REGS_LEAF = 'rtl/leafA.sv'
# The generated router of the same decode tree. It is a second generator
# (templates/systemVerilog/apbDecodeModule.py) reading the same bus domain, and
# its own emission site for every flop in the dispatch path.
REGS_ROUTER = 'rtl/apbDecode.sv'


# --------------------------------------------------- clk-member fixture --
#
# Standalone and connection-free, so no cross-project name resolution can add
# `clk` to a block's set behind the fixture's back. The default clock is not
# named `clk`; the leaf authors `clk` as its SECOND clock (see
# check_alias_clk_member_not_first_skips_alias).
CLK_MEMBER_PROJECT = """yamlFormat: 2
projectName: clkMember
topInstance: leaf

projectFiles:
    - ../../yaml/top.yaml

clocks:
    mainClk: { desc: "default clock, not named clk", default: true, period: 1, timeUnit: ns }
    clk: { desc: "non-default clock literally named clk", period: 2, timeUnit: ns }
    periphClk: { desc: "periphLeaf's domain; a distinct alias RHS", period: 3, timeUnit: ns }

resets:
    rst_n:      { desc: "the default reset, clk domain", default: true, clock: mainClk }
    clkRst_n:   { desc: "the reset for the non-default clk domain", clock: clk }
    periphRst_n: { desc: "the reset for the periphClk domain", clock: periphClk }

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

CLK_MEMBER_DESIGN = """blocks:
    leaf:
        desc: "leaf carrying the default clock plus a second clock literally named clk, not first in canonical order"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks: [mainClk, clk]
    periphLeaf:
        desc: "leaf wholly in the periphClk domain, so its alias pins a clock value DIFFERENT from leaf's own domain"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks: [periphClk]

instances:
    leaf: { container: leaf, instanceType: leaf, instGroup: top }
"""

CLK_MEMBER_LEAF = 'rtl/leaf.sv'
CLK_MEMBER_PERIPH_LEAF = 'rtl/periphLeaf.sv'


def _arch2code(*args, cwd):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run([sys.executable, ARCH2CODE, *args],
                          capture_output=True, text=True, timeout=300,
                          cwd=cwd, env=env)


def _generate():
    """Build the fixture, scaffold it, render every file this suite reads.

    Returns (fixture_dir, {relative path: emitted text}).
    """
    fixture = tempfile.mkdtemp(prefix='clkemit_')
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    os.makedirs(os.path.join(fixture, 'ip', 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'ip', 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(PROJECT)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(DESIGN)
    with open(os.path.join(fixture, 'ip', 'prj', 'yaml', 'ipProject.yaml'), 'w') as f:
        f.write(IP_PROJECT)
    with open(os.path.join(fixture, 'ip', 'yaml', 'emitIp.yaml'), 'w') as f:
        f.write(IP_DESIGN)

    db = os.path.join(fixture, 'emit.db')
    built = _arch2code('--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'),
                       '--db', db, cwd=fixture)
    if built.returncode != 0:
        raise AssertionError(f"database build failed:\n{built.stdout}\n{built.stderr}")
    # --newmodule scaffolds the files; it does not fill the generated regions.
    made = _arch2code('--db', db, '-r', '--newmodule', cwd=fixture)
    if made.returncode != 0:
        raise AssertionError(f"newmodule failed:\n{made.stdout}\n{made.stderr}")

    ipDb = os.path.join(fixture, 'ip', 'emitIp.db')
    ipBuilt = _arch2code('--yaml', os.path.join(fixture, 'ip', 'prj', 'yaml',
                                                'ipProject.yaml'),
                         '--db', ipDb, cwd=fixture)
    if ipBuilt.returncode != 0:
        raise AssertionError(
            f"child project build failed:\n{ipBuilt.stdout}\n{ipBuilt.stderr}")
    ipMade = _arch2code('--db', ipDb, '-r', '--newmodule', cwd=fixture)
    if ipMade.returncode != 0:
        raise AssertionError(
            f"child project newmodule failed:\n{ipMade.stdout}\n{ipMade.stderr}")

    emitted = dict()
    for switch, paths in GENERATED.items():
        for rel in paths:
            gen = _arch2code('--db', db, '-r', switch,
                             '--file', os.path.join(fixture, rel), cwd=fixture)
            if gen.returncode != 0:
                raise AssertionError(
                    f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
            with open(os.path.join(fixture, rel)) as f:
                emitted[rel] = f.read()
    for rel in ('ip/rtl/emitIp_package.sv', IP_LEAF):
        gen = _arch2code('--db', ipDb, '-r', '--systemVerilog',
                         '--file', os.path.join(fixture, rel), cwd=fixture)
        if gen.returncode != 0:
            raise AssertionError(
                f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
        with open(os.path.join(fixture, rel)) as f:
            emitted[rel] = f.read()
    return fixture, emitted


def _build_regs(feed_clock, router_clocks=None):
    """Write the register-handler fixture and attempt its database build.

    feed_clock is the clock authored on the register-bus feed, or None to leave
    it unstated so the decode tree falls to the project default. router_clocks is
    an authored `clocks:` list on the ROUTER block, which is additive and so is
    the one way ordinary YAML can widen a router past its bus domain.

    The build result is RETURNED rather than asserted, so a case can require the
    build to fail.

    Returns (fixture_dir, db path, database build result).
    """
    fixture = tempfile.mkdtemp(prefix='regsemit_')
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    routerLines = f"        clocks: [{', '.join(router_clocks)}]\n" if router_clocks else ''
    blocks = (render_plain_block('top') + render_plain_block('cpu')
              + render_router('apbDecode', 'top', extra_block_lines=routerLines)
              + render_leaf('leafA',
                            extra_block_lines='        params: [CFG_WIDTH]\n')
              + render_plain_block('regAccessor'))
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(REGS_DESIGN.format(
            blocks=blocks,
            feed_clock=f", clock: {feed_clock}" if feed_clock else ""))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(REGS_PROJECT)

    db = os.path.join(fixture, 'regs.db')
    built = _arch2code('--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'),
                       '--db', db, cwd=fixture)
    return fixture, db, built


def _generate_regs(feed_clock):
    """Build the register-handler fixture and render the handler and its leaf.

    Returns (fixture_dir, {relative path: emitted text}).
    """
    fixture, db, built = _build_regs(feed_clock)
    if built.returncode != 0:
        raise AssertionError(f"database build failed:\n{built.stdout}\n{built.stderr}")
    made = _arch2code('--db', db, '-r', '--newmodule', cwd=fixture)
    if made.returncode != 0:
        raise AssertionError(f"newmodule failed:\n{made.stdout}\n{made.stderr}")

    emitted = dict()
    for rel in ('rtl/top_package.sv', REGS_LEAF, REGS_HANDLER, REGS_ROUTER):
        gen = _arch2code('--db', db, '-r', '--systemVerilog',
                         '--file', os.path.join(fixture, rel), cwd=fixture)
        if gen.returncode != 0:
            raise AssertionError(f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
        with open(os.path.join(fixture, rel)) as f:
            emitted[rel] = f.read()
    return fixture, emitted


def _generate_clk_member():
    """Build the clk-member fixture and render its two leaves.

    Returns (fixture_dir, {relative path: emitted text}).
    """
    fixture = tempfile.mkdtemp(prefix='clkmember_')
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(CLK_MEMBER_PROJECT)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(CLK_MEMBER_DESIGN)

    db = os.path.join(fixture, 'clkmember.db')
    built = _arch2code('--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'),
                       '--db', db, cwd=fixture)
    if built.returncode != 0:
        raise AssertionError(f"database build failed:\n{built.stdout}\n{built.stderr}")
    made = _arch2code('--db', db, '-r', '--newmodule', cwd=fixture)
    if made.returncode != 0:
        raise AssertionError(f"newmodule failed:\n{made.stdout}\n{made.stderr}")

    emitted = dict()
    for rel in (CLK_MEMBER_LEAF, CLK_MEMBER_PERIPH_LEAF):
        gen = _arch2code('--db', db, '-r', '--systemVerilog',
                         '--file', os.path.join(fixture, rel), cwd=fixture)
        if gen.returncode != 0:
            raise AssertionError(f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
        with open(os.path.join(fixture, rel)) as f:
            emitted[rel] = f.read()
    return fixture, emitted


def _run_case(label, fn):
    try:
        ok = fn()
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    print(f"{'PASS' if ok else 'FAIL'}: {label}")
    return ok


def _expect(text, needle, why, where):
    if needle not in text:
        raise AssertionError(f"{where} does not contain {needle!r}: {why}")
    return True


def _refute(text, needle, why, where):
    if needle in text:
        raise AssertionError(f"{where} contains {needle!r}: {why}")
    return True


# The two port styles, as DISJOINT patterns, so a case written for one cannot be
# satisfied by the other - a pattern admitting both would stop detecting a
# generator that adopted the wrong style, which is the confusion these two exist
# to catch. JOINED requires at least one comma; PER_LINE requires exactly one
# name. Every block holds at least one clock (the derivation floor) and at least
# one reset (one per clock it carries, or the list it authored), so the joined form
# always carries a comma and the two patterns can never both match the same port
# list. A flattened interface port matches neither: it always names a type.
JOINED_INPUT = re.compile(r'^input [A-Za-z_]\w*(?:, [A-Za-z_]\w*)+$')
PER_LINE_INPUT = re.compile(r'^input [A-Za-z_]\w*,?$')


def _strip(text):
    return [line.strip() for line in text.splitlines()]


# The two readers below are named for the GENERATOR whose style they enforce, not
# for the kind of module it emits. Neither is a rule about RTL modules or about
# SystemVerilog: `<block>_regs` is an RTL module declaring one clock/reset per
# line (templates/systemVerilog/moduleRegs.py), which the block-module reader
# would reject as wrongly styled.

def _block_module_input_line(text, where):
    """The one joined clock/reset `input` of a block module port list.

    The block module generator (intf_gen_utils.sv_clock_reset_input) joins them,
    and that is what this enforces - for that generator's output only."""
    joined = [line for line in _strip(text) if JOINED_INPUT.match(line)]
    perLine = [line for line in _strip(text) if PER_LINE_INPUT.match(line)]
    if perLine:
        raise AssertionError(
            f"{where} declares clocks/resets one per line ({perLine}); the block "
            f"module generator joins them onto one `input`")
    if len(joined) != 1:
        raise AssertionError(
            f"{where} has {len(joined)} joined `input` declarations, expected "
            f"exactly one ({joined})")
    return joined[0]


def _sv_wrapper_input_lines(text, where):
    """The per-line clock/reset `input` declarations of a verilated SV wrapper.

    The wrapper generator (intf_gen_utils.sv_clock_reset_input_lines) declares one
    per line, and that is what this enforces - for that generator's output only.
    Returned verbatim, commas included, so the trailing-comma placement that
    makes the port list legal SystemVerilog is part of what is asserted."""
    joined = [line for line in _strip(text) if JOINED_INPUT.match(line)]
    perLine = [line for line in _strip(text) if PER_LINE_INPUT.match(line)]
    if joined:
        raise AssertionError(
            f"{where} joins clocks/resets onto one `input` ({joined}); the "
            f"verilated SV wrapper generator declares them one per line")
    if not perLine:
        raise AssertionError(f"{where} declares no clock/reset `input` at all")
    return perLine


def _names(declarations):
    """The port names of either style, so the two can be compared for content."""
    return [word.strip(',') for line in declarations
            for word in line.removeprefix('input ').split(', ')]


# A child instantiation head: a module name, an optional parameter override list,
# the instance name, then the open paren the bind list follows.
_INSTANCE_HEAD = re.compile(r'^(\w+)\s+(?:#\(.*\)\s+)?(\w+) \($')
_BIND = re.compile(r'^\.(\w+) \((\w+)\)$')


def _instance_binds(text, where):
    """{instance name: [(port, signal), ...]} for every child instantiation.

    In emitted order and covering EVERY bind, interface binds included, so a case
    can assert both the clock/reset names and that they are the last ones - the
    order the child's port list declares them in."""
    binds = dict()
    current = None
    for line in _strip(text):
        head = _INSTANCE_HEAD.match(line)
        if head:
            current = head.group(2)
            binds[current] = list()
        elif current is not None:
            if line == ');':
                current = None
            elif line:
                bind = _BIND.match(line.rstrip(','))
                if not bind:
                    raise AssertionError(
                        f"{where} binds {line!r} on instance {current}, which is "
                        f"not a `.port (signal)` bind")
                binds[current].append(bind.groups())
    if not binds:
        raise AssertionError(f"{where} instantiates nothing at all")
    return binds


def _assert_instance_tail(binds, where, expected):
    """Each named instance's LAST binds are exactly the expected clock/reset pairs.

    Asserted as a tail rather than by searching, so an emitter that also left the
    old literal in place, or that put the clock/reset binds somewhere other than
    the end of the list, fails."""
    for instance, tail in expected.items():
        found = binds[instance][-len(tail):]
        if found != tail:
            raise AssertionError(
                f"{where} instance {instance} ends its bind list with {found}, "
                f"expected {tail}")
        if len(binds[instance]) != len(set(binds[instance])):
            raise AssertionError(
                f"{where} instance {instance} binds something twice: "
                f"{binds[instance]}")
    return True


# ------------------------------------------------------------ port lists --

def check_non_default_domain_port_list(emitted):
    """A leaf wholly in the slow domain names neither clk nor rst_n.

    The declared name is the emitted port name verbatim, so a block that no
    default-domain connection touches must not also carry the default clock."""
    line = _block_module_input_line(emitted['rtl/slowProd.sv'], 'slowProd module')
    if line != 'input clkSlow, rstSlow_n':
        raise AssertionError(f"slowProd port list is {line!r}, expected "
                             f"'input clkSlow, rstSlow_n'")
    return True


def check_multi_domain_port_list(emitted):
    """Three clocks and three resets on one `input`, clocks first, canonical order.

    Canonical order is the declaring project's declaration order with the default
    first, which is a churn-avoidance contract: a set-iteration order would
    reshuffle port lists on unrelated edits. The block authors its resets: in that
    same order, so what this pins is the CLOCKS-then-RESETS grouping and the
    absence of any interleaving."""
    line = _block_module_input_line(emitted['rtl/fastProd.sv'], 'fastProd module')
    if line != 'input clk, clkSlow, clkPico, rst_n, rstSlow_n, rstPico_n':
        raise AssertionError(
            f"fastProd port list is {line!r}, expected "
            f"'input clk, clkSlow, clkPico, rst_n, rstSlow_n, rstPico_n'")
    return True


def check_two_clock_port_list(emitted):
    """A block reached from two domains carries both clocks and BOTH resets.

    cons authors no resets:, so its set is derived from its clock set - one reset
    per domain it is reached from. It previously carried the project default reset
    alone, which left its clkSlow logic with a reset released on a clk edge."""
    line = _block_module_input_line(emitted['rtl/cons.sv'], 'cons module')
    if line != 'input clk, clkSlow, rst_n, rstSlow_n':
        raise AssertionError(f"cons port list is {line!r}, expected "
                             f"'input clk, clkSlow, rst_n, rstSlow_n'")
    return True


# -------------------------------------------------- default-domain alias --

def _generated_region(text, where):
    """The text of the moduleInterfacesInstances generated region alone.

    The alias is asserted to sit INSIDE this region, not merely anywhere in the
    file, so a hand-edit of the user region could never satisfy the case."""
    begin = text.find('GENERATED_CODE_BEGIN --template=moduleInterfacesInstances')
    end = text.find('GENERATED_CODE_END', begin)
    if begin == -1 or end == -1:
        raise AssertionError(f"{where} has no moduleInterfacesInstances generated region")
    return text[begin:end]


def check_alias_non_default_domain(emitted):
    """A leaf wholly in the slow domain aliases both clk and rst_n, inside the
    generated region, onto its own resolved clock and reset.

    slowProd's port list names neither clk nor rst_n, so this is the shape that
    proves the alias exists at all: without it, slowProd's hand-written RTL
    could not use the bare flop macro family."""
    text = emitted['rtl/slowProd.sv']
    region = _generated_region(text, 'slowProd module')
    for line in ('wire clk = clkSlow;', 'wire rst_n = rstSlow_n;'):
        _expect(region, line, "the alias names slowProd's own clock/reset",
                'slowProd generated region')
    return True


def check_alias_absent_default_domain(emitted):
    """A block already carrying clk and rst_n as members gets no alias at all.

    fastProd's set is [clk, clkSlow, clkPico] / [rst_n, rstSlow_n, rstPico_n],
    so both names are already real ports; an alias here would redeclare them."""
    text = emitted['rtl/fastProd.sv']
    _refute(text, 'wire clk =', 'fastProd already declares a port named clk',
            'fastProd module')
    _refute(text, 'wire rst_n =', 'fastProd already declares a port named rst_n',
            'fastProd module')
    return True


def check_alias_absent_multi_domain_clk_first(emitted):
    """A multi-domain block whose FIRST clock is clk emits no clk alias.

    cons's set is [clk, clkSlow] / [rst_n, rstSlow_n]; clk and rst_n are both
    already members, so neither alias line belongs here."""
    text = emitted['rtl/cons.sv']
    _refute(text, 'wire clk =', 'cons already declares a port named clk',
            'cons module')
    _refute(text, 'wire rst_n =', 'cons already declares a port named rst_n',
            'cons module')
    return True


def check_alias_reset_independent_of_clock(emitted):
    """The two alias decisions are independent: leafA's default reset is
    rstMain_n, not rst_n, while its clock IS named clk.

    So leafA aliases rst_n onto rstMain_n and emits no clk alias at all - proof
    that a project renaming only its reset does not also trigger a clock alias,
    and vice versa."""
    text = emitted[REGS_LEAF]
    region = _generated_region(text, 'leafA module')
    _expect(region, 'wire rst_n = rstMain_n;',
            "leafA's default reset is rstMain_n, not rst_n", 'leafA generated region')
    _refute(text, 'wire clk =', 'leafA already declares a port named clk',
            'leafA module')
    return True


def check_alias_clk_member_not_first_skips_alias(emitted):
    """A clock literally named `clk` skips the alias wherever it sits in the set.

    clkMember's leaf carries mainClk (the project's default, canonically first)
    then clk (authored second), so a rule keyed on POSITION rather than
    MEMBERSHIP would wrongly alias over the block's own clk port."""
    text = emitted[CLK_MEMBER_LEAF]
    _refute(text, 'wire clk =',
            "the leaf already declares a port named clk, even though it is "
            "not the block's first clock", 'clkMember leaf module')
    return True


def check_alias_value_is_not_a_shared_literal(emitted):
    """The alias RHS is the block's OWN clock/reset, not a fixed spelling that
    happens to satisfy every fixture.

    periphLeaf's only clock is periphClk, a name no other fixture's alias uses,
    so this is what pins the RHS to a per-block lookup rather than a literal
    that coincidentally matches slowProd's clkSlow everywhere else."""
    text = emitted[CLK_MEMBER_PERIPH_LEAF]
    region = _generated_region(text, 'periphLeaf module')
    for line in ('wire clk = periphClk;', 'wire rst_n = periphRst_n;'):
        _expect(region, line, "the alias names periphLeaf's own clock/reset",
                'periphLeaf generated region')
    return True


# ------------------------------------------------------ container binds --

def check_container_port_list(emitted):
    """The container carries the union of its children's respelled sets.

    This is what makes every bind below legal: a bound signal has to be a port of
    the container itself, and the containment union is what guarantees it. The
    child in the OTHER project contributes nothing new here - its ipClk / ipRst_n
    respell onto clk / rst_n, which the container already has.

    The container authors no resets:, so it derives one per clock it carries, and
    clkPico reaches it from uFast alone. Its list is therefore the union of what it
    derives and what its children hold, which here coincide."""
    line = _block_module_input_line(emitted[CONTAINER], 'dut module')
    if line != 'input clk, clkSlow, clkPico, rst_n, rstSlow_n, rstPico_n':
        raise AssertionError(
            f"dut port list is {line!r}, expected "
            f"'input clk, clkSlow, clkPico, rst_n, rstSlow_n, rstPico_n'")
    return True


def check_container_binds_child_port_names(emitted):
    """A container binds each child's OWN clock and reset port names.

    uSlow's module declares clkSlow and rstSlow_n and nothing else, so the
    literal `.clk`/`.rst_n` this emitter used to end every instantiation with
    named ports that child does not have - RTL that does not elaborate. uFast is
    the shape that pins the ORDER and the CARDINALITY together: three clocks then
    three resets, position for position against its port list, so dropping the
    resets or emitting them before the clocks is visible."""
    binds = _instance_binds(emitted[CONTAINER], 'dut module')
    return _assert_instance_tail(binds, 'dut module', {
        'uSlow': [('clkSlow', 'clkSlow'), ('rstSlow_n', 'rstSlow_n')],
        'uFast': [('clk', 'clk'), ('clkSlow', 'clkSlow'), ('clkPico', 'clkPico'),
                  ('rst_n', 'rst_n'), ('rstSlow_n', 'rstSlow_n'),
                  ('rstPico_n', 'rstPico_n')],
        'uCons': [('clk', 'clk'), ('clkSlow', 'clkSlow'), ('rst_n', 'rst_n'),
                  ('rstSlow_n', 'rstSlow_n')],
    })


def check_container_binds_are_the_child_port_lists(emitted):
    """Every bind names a port the child module actually declares, in its order.

    The two texts come from two separate generator runs over the same block, so
    comparing them is what pins the contract rather than restating one literal
    twice: the child's port list is the authority and the bind list has to be it,
    name for name and position for position."""
    binds = _instance_binds(emitted[CONTAINER], 'dut module')
    for instance, block in (('uSlow', 'slowProd'), ('uFast', 'fastProd'),
                            ('uCons', 'cons')):
        ports = _names([_block_module_input_line(emitted[f'rtl/{block}.sv'],
                                                 f'{block} module')])
        bound = [port for port, _signal in binds[instance][-len(ports):]]
        if bound != ports:
            raise AssertionError(
                f"dut binds {bound} on {instance} but {block} declares {ports}; "
                f"a bind naming a port the child does not have is an elaboration "
                f"error")
    return True


def check_container_binds_foreign_child(emitted):
    """The two sides of a bind are two spellings of ONE domain.

    Within a single project they always coincide, because a block's set is
    respelled into its own project and that is the container's project too. So
    the vendored child is the ONLY shape here in which the pair is visible at
    all: ipLeaf's port list is spelled in the clocks emitIp declares, the
    container drives the ones emitTest declares, and neither name appears on the
    other side. An emitter that bound the container's signal to the child's port
    name - the pair reversed - passes every single-project case and fails here."""
    line = _block_module_input_line(emitted[IP_LEAF], 'ipLeaf module')
    if line != 'input ipClk, ipRst_n':
        raise AssertionError(f"ipLeaf port list is {line!r}, expected "
                             f"'input ipClk, ipRst_n'; the fixture no longer "
                             f"separates the child's spelling from the parent's")
    binds = _instance_binds(emitted[CONTAINER], 'dut module')
    return _assert_instance_tail(binds, 'dut module', {
        'uIpLeaf': [('ipClk', 'clk'), ('ipRst_n', 'rst_n')],
    })


def check_container_binds_no_literal_clk(emitted):
    """No instantiation in the container binds a literal `.clk`/`.rst_n` pair
    that the child does not declare.

    uSlow and uIpLeaf have no port named clk or rst_n, so their presence anywhere
    in those two bind lists is the exact defect this step removes, stated as a
    refutation so a future emitter cannot satisfy the tail assertions above by
    appending the old literals after them."""
    binds = _instance_binds(emitted[CONTAINER], 'dut module')
    for instance in ('uSlow', 'uIpLeaf'):
        stale = [bind for bind in binds[instance] if bind[0] in ('clk', 'rst_n')]
        if stale:
            raise AssertionError(
                f"dut binds {stale} on {instance}, which declares no such port")
    return True


def check_wrapper_port_list_matches_module(emitted):
    """The verilated SV wrapper reconstructs the DUT, so its clock/reset port
    list must be the DUT's, name for name and position for position.

    Same list, different local style: the module joins, the wrapper declares one
    per line. Only the names and their order have to agree."""
    for block, wrap in SV_WRAPPER.items():
        module = _names([_block_module_input_line(emitted[f'rtl/{block}.sv'],
                                            f'{block} module')])
        wrapper = _names(_sv_wrapper_input_lines(emitted[wrap], f'{block} SV wrapper'))
        if module != wrapper:
            raise AssertionError(
                f"{block}: the module declares {module} but its wrapper declares "
                f"{wrapper}; the wrapper drives the module, so a mismatch is an "
                f"unbound port")
    return True


def check_wrapper_keeps_per_line_style(emitted):
    """The verilated SV wrapper declares one clock/reset per line, verbatim.

    This is the wrapper generator's own pre-existing style, and it is what makes
    the emission byte-identical to baseline for every single-clock project. The
    ordering rule is shared with the RTL module port list; the spelling is not."""
    expected = {'slowProd': ['input clkSlow,', 'input rstSlow_n'],
                'fastProd': ['input clk,', 'input clkSlow,', 'input clkPico,',
                             'input rst_n,', 'input rstSlow_n,',
                             'input rstPico_n'],
                'cons': ['input clk,', 'input clkSlow,', 'input rst_n,',
                         'input rstSlow_n']}
    for block, lines in expected.items():
        found = _sv_wrapper_input_lines(emitted[SV_WRAPPER[block]],
                                 f'{block} SV wrapper')
        if found != lines:
            raise AssertionError(
                f"{block} SV wrapper declares {found}, expected {lines}")
    return True


def check_wrapper_dut_bindings(emitted):
    """The wrapper binds every clock and reset it declares, in the same order."""
    expected = {'slowProd': ['.clkSlow(clkSlow)', '.rstSlow_n(rstSlow_n)'],
                'fastProd': ['.clk(clk)', '.clkSlow(clkSlow)', '.clkPico(clkPico)',
                             '.rst_n(rst_n)', '.rstSlow_n(rstSlow_n)',
                             '.rstPico_n(rstPico_n)'],
                'cons': ['.clk(clk)', '.clkSlow(clkSlow)', '.rst_n(rst_n)',
                         '.rstSlow_n(rstSlow_n)']}
    for block, binds in expected.items():
        text = emitted[SV_WRAPPER[block]]
        found = [b for b in re.findall(r'\.\w+\(\w+\)', text)
                 if b in set(binds)]
        if found != binds:
            raise AssertionError(
                f"{block} wrapper binds {found}, expected {binds}")
    return True


def check_variant_trampoline(emitted):
    """A parameterizable block's per-variant top declares and forwards the same
    clock/reset list as the canonical body it instantiates.

    The trampoline is its own emission site, and no shipped example exercises it
    with anything but the default domain, so its list is otherwise unasserted."""
    text = emitted[SV_TRAMPOLINE]
    lines = _sv_wrapper_input_lines(text, 'slowProd variant trampoline')
    if lines != ['input clkSlow,', 'input rstSlow_n']:
        raise AssertionError(f"the trampoline declares {lines}, expected "
                             f"['input clkSlow,', 'input rstSlow_n']")
    binds = ['.clkSlow(clkSlow)', '.rstSlow_n(rstSlow_n)']
    found = [b for b in re.findall(r'\.\w+\(\w+\)', text) if b in set(binds)]
    if found != binds:
        raise AssertionError(
            f"the trampoline forwards {found} to the canonical body, expected "
            f"{binds}; an unforwarded clock leaves the body's port undriven")
    return True


# --------------------------------------------------------- sc_clock / rst --

def check_sc_clock_per_declared_period(emitted):
    """One gated clock signal per resolved clock, each with its OWN half period
    from its declared period and unit.

    A single hardcoded half period is only meaningful while every clock runs at
    1 ns, which is the defect the declared period exists to fix. The clock is an
    sc_signal, not an sc_clock, because socket lockstep must be able to stop it."""
    text = emitted['verif/fastProd_hdl_sc_wrapper.h']
    for decl in ('sc_signal<bool> clk;', 'sc_signal<bool> clkSlow;',
                 'sc_signal<bool> clkPico;'):
        _expect(text, decl, 'each resolved clock is its own gated signal',
                'fastProd SC wrapper')
    for half in ('clk_half_(sc_time(1, SC_NS) / 2)',
                 'clkSlow_half_(sc_time(3, SC_NS) / 2)',
                 'clkPico_half_(sc_time(500, SC_PS) / 2)'):
        _expect(text, half, 'the period and the unit both come from the declaration',
                'fastProd SC wrapper')
    _refute(text, 'sc_clock', 'a free-running sc_clock cannot be gated',
            'fastProd SC wrapper')
    return True


def check_one_clock_thread_per_clock(emitted):
    """Each clock has its own generator thread over the one shared gated toggler,
    so every clock stops together under lockstep and each keeps its own period."""
    text = emitted['verif/fastProd_hdl_sc_wrapper.h']
    threads = re.findall(r'SC_THREAD\((clock_gen_\w+)\);', text)
    if sorted(threads) != sorted(['clock_gen_clk', 'clock_gen_clkSlow',
                                  'clock_gen_clkPico']):
        raise AssertionError(
            f"fastProd SC wrapper registers clock threads {threads}, expected one "
            f"per clock with a distinct name")
    for thunk in ('void clock_gen_clk() { clock_gen(clk, clk_half_); }',
                  'void clock_gen_clkSlow() { clock_gen(clkSlow, clkSlow_half_); }',
                  'void clock_gen_clkPico() { clock_gen(clkPico, clkPico_half_); }'):
        _expect(text, thunk, 'each thread toggles its own signal at its own half period',
                'fastProd SC wrapper')
    if text.count('socketSyncWaitClockEdge()') != 1:
        raise AssertionError(
            "fastProd SC wrapper must gate every clock through the one shared "
            "clock_gen body")
    return True


def check_reset_signal_per_reset(emitted):
    """One sc_signal<bool> per resolved reset, born released."""
    text = emitted['verif/fastProd_hdl_sc_wrapper.h']
    for decl in ('sc_signal<bool> rst_n;', 'sc_signal<bool> rstSlow_n;',
                 'sc_signal<bool> rstPico_n;'):
        _expect(text, decl, 'each resolved reset is its own signal',
                'fastProd SC wrapper')
    for init in ('rst_n("rst_n", true)', 'rstSlow_n("rstSlow_n", true)',
                 'rstPico_n("rstPico_n", true)'):
        _expect(text, init, "a reset is born released so the driver's first "
                "assertion is a real negedge", 'fastProd SC wrapper')
    return True


def check_release_counts_own_clock(emitted):
    """Each reset is released after its OWN releaseCycles edges of its OWN clock.

    fastProd is the shape that separates the two rules: rstSlow_n's clock
    (clkSlow) is not the block's first clock, and its count (5) is not the
    schema default, so an emitter that used the block's primary clock or one
    shared count is visible here and nowhere else."""
    text = emitted['verif/fastProd_hdl_sc_wrapper.h']
    for name, cycles, clock in (('rst_n', 3, 'clk'), ('rstSlow_n', 5, 'clkSlow')):
        driver = re.search(
            rf'void reset_driver_{name}\(\) \{{ reset_driver\({name}, (\w+), (\d+)\); \}}',
            text)
        if not driver:
            raise AssertionError(
                f"fastProd SC wrapper has no cycle-counting driver for {name}")
        if (driver.group(1), int(driver.group(2))) != (clock, cycles):
            raise AssertionError(
                f"{name} is released after {driver.group(2)} edges of "
                f"{driver.group(1)}, expected {cycles} edges of {clock}")
    if text.count('wait(clk.posedge_event());') != 1:
        raise AssertionError(
            "fastProd SC wrapper must count release edges in the one shared "
            "reset_driver body")
    return True


def check_release_is_not_absolute_time(emitted):
    """No wrapper waits an absolute time: that is the period-coupled release the
    cycle count replaces, and it deasserted after a single edge at period 10."""
    for rel, text in emitted.items():
        if rel.endswith('_hdl_sc_wrapper.h'):
            _refute(text, 'wait(5, SC_NS)',
                    'the release is counted in cycles of the reset clock', rel)
    return True


def check_one_driver_thread_per_reset(emitted):
    """Resets in different domains cannot share one thread: they are released
    at different times, so each needs its own SC_THREAD."""
    text = emitted['verif/fastProd_hdl_sc_wrapper.h']
    threads = re.findall(r'SC_THREAD\((reset_driver_\w+)\);', text)
    if sorted(threads) != sorted(['reset_driver_rst_n', 'reset_driver_rstSlow_n',
                                  'reset_driver_rstPico_n']):
        raise AssertionError(
            f"fastProd SC wrapper registers reset threads {threads}, expected one "
            f"per reset with a distinct name")
    return True


def check_sc_wrapper_binds_every_domain(emitted):
    """The verilated DUT carries a port per clock and reset, so the SC wrapper
    must bind all of them."""
    text = emitted['verif/slowProd_hdl_sc_wrapper.h']
    for bind in ('dut_hdl->clkSlow(clkSlow);', 'dut_hdl->rstSlow_n(rstSlow_n);'):
        _expect(text, bind, 'every declared domain reaches the DUT',
                'slowProd SC wrapper')
    _refute(text, 'dut_hdl->clk(clk);',
            'slowProd has no clk port, so binding one would not compile',
            'slowProd SC wrapper')
    return True


def check_bfm_binds_names_the_wrapper_declares(emitted):
    """A BFM's clock and reset both name a member of THIS wrapper.

    slowProd holds one of each and neither is the project default, so a literal
    `clk` / `rst_n` - or any name taken from somewhere other than this block's
    own resolved sets - would not compile here."""
    text = emitted['verif/slowProd_hdl_sc_wrapper.h']
    _expect(text, 'out_bfm.clk(clkSlow);',
            "the block's only clock is clkSlow", 'slowProd SC wrapper')
    _expect(text, 'out_bfm.rst_n(rstSlow_n);',
            "the block's only reset is rstSlow_n", 'slowProd SC wrapper')
    return True


def check_bfm_binds_its_own_connection_domain(emitted):
    """A BFM's clock AND reset are both the domain of the connection it drives.

    cons is the shape that separates that from the block's primary domain: it is
    reached from both domains, so its set is [clk, clkSlow] and slowIn's
    connection is in the SECOND one. Bindings taken from the set's first entry
    would clock slowIn's BFM from clk and hold it in reset off a clk edge - both
    are real members of this wrapper, so it still compiles and still runs, and the
    BFM simply drives the slow interface at the fast rate against a reset released
    in another domain. Nothing else in the toolchain reports that, which is why
    each is asserted on both ports and refuted on the wrong one."""
    text = emitted['verif/cons_hdl_sc_wrapper.h']
    for bind in ('slowIn_bfm.clk(clkSlow);', 'fastIn_bfm.clk(clk);',
                 'slowIn_bfm.rst_n(rstSlow_n);', 'fastIn_bfm.rst_n(rst_n);'):
        _expect(text, bind, "each BFM takes its own connection's clock and the "
                            'reset released on that clock', 'cons SC wrapper')
    _refute(text, 'slowIn_bfm.clk(clk);',
            "slowIn's connection is in the clkSlow domain, so binding clk "
            "clocks that BFM from the wrong domain",
            'cons SC wrapper')
    _refute(text, 'slowIn_bfm.rst_n(rst_n);',
            "rst_n is released on a clk edge, so binding it resets slowIn's BFM "
            "from the wrong domain - and it is the block's FIRST reset, which is "
            "what a reset taken per block rather than per port would give",
            'cons SC wrapper')
    # fastProd holds a reset in each of its three domains and its only connection
    # is in the default one, which is the FIRST of its set, so a BFM reset taken
    # from anywhere but the port's domain - the block's last reset, or the reset of
    # a clock the block merely carries - is visible here and not on cons.
    fast = emitted['verif/fastProd_hdl_sc_wrapper.h']
    _expect(fast, 'out_bfm.rst_n(rst_n);',
            "out's connection is in the clk domain and rst_n is the reset "
            'declared on clk', 'fastProd SC wrapper')
    _refute(fast, 'out_bfm.rst_n(rstSlow_n);',
            'rstSlow_n is released on clkSlow, which out does not run in',
            'fastProd SC wrapper')
    _refute(fast, 'out_bfm.rst_n(rstPico_n);',
            "rstPico_n is released on clkPico and is the block's LAST reset, so "
            'binding it is what a reset taken from the end of the set gives',
            'fastProd SC wrapper')
    return True


# ------------------------------------------------------- library contract --

def check_time_unit_map_covers_schema():
    """Every timeUnit the schema admits has an sc_time spelling.

    Library content, so it is checked here rather than on every generator run: a
    unit added to the schema with no spelling would otherwise fail only in the
    project unlucky enough to author it."""
    with open(os.path.join(base_dir, 'config', 'schema.yaml')) as f:
        schema = yaml.safe_load(f)
    declared = set(schema['clocks']['timeUnit']['_validate']['values'])
    missing = declared - set(SC_TIME_UNIT)
    if missing:
        raise AssertionError(
            f"clocks.timeUnit admits {sorted(missing)} with no SC_TIME_UNIT "
            f"spelling, so a project authoring one fails at generation")
    return True


_DEFINE = re.compile(r'^`define (\w+)\((.*?)\)\s*(.*)$')
_BRANCH_OPEN = re.compile(r'^`ifn?def\s+(\w+)')


def _flops_sections():
    """flops.sv split into its ASIC branch, its FPGA (`else`) branch, and the
    text outside both.

    Split by tracking `ifdef nesting rather than by line number, so the inner
    `ifndef RST does not end the branch and a moved branch is still found."""
    with open(FLOPS_SV) as f:
        lines = f.read().splitlines()
    sections = {'ASIC': [], 'FPGA': [], 'outer': []}
    depth, asicDepth, current = 0, None, 'outer'
    for line in lines:
        opened = _BRANCH_OPEN.match(line)
        if opened:
            depth += 1
            if opened.group(1) == 'ASIC':
                asicDepth, current = depth, 'ASIC'
                continue
        elif line.startswith('`else') and depth == asicDepth:
            current = 'FPGA'
            continue
        elif line.startswith('`endif'):
            if depth == asicDepth:
                asicDepth, current = None, 'outer'
            depth -= 1
            if current == 'outer':
                continue
        sections[current].append(line)
    if not sections['ASIC'] or not sections['FPGA']:
        raise AssertionError(
            f"{FLOPS_SV} has no `ifdef ASIC / `else pair; the two reset flows are "
            f"what the branch split exists to hold")
    return sections


def _flops_defines(lines):
    """{macro name: (argument list, body)} for every parameterized `define."""
    out = dict()
    for index, line in enumerate(lines):
        found = _DEFINE.match(line)
        if found:
            args = [a.strip() for a in found.group(2).split(',')]
            # A body continued with a trailing backslash spans further lines.
            body, cursor = found.group(3), index
            while lines[cursor].endswith('\\'):
                cursor += 1
                body += '\n' + lines[cursor]
            out[found.group(1)] = (args, body)
    return out


def check_flops_clk_variant_per_family():
    """Every flop family defined in a branch is the clock-parameterized variant,
    and every family exists in BOTH branches.

    The families are discovered from the file, not listed here: a family added to
    one branch only, or added without a _CLK form, fails without this case being
    edited. The two branches are the two reset flows, and a design that compiles
    the other one must find the same macro set."""
    sections = _flops_sections()
    asic = _flops_defines(sections['ASIC'])
    fpga = _flops_defines(sections['FPGA'])
    bare = sorted(name for name in list(asic) + list(fpga)
                  if not name.endswith('_CLK'))
    if bare:
        raise AssertionError(
            f"{bare} are defined inside a reset-flow branch without a _CLK form; "
            f"a branch holds the parameterized bodies only")
    onlyOne = sorted(set(asic) ^ set(fpga))
    if onlyOne:
        raise AssertionError(
            f"{onlyOne} exist in only one reset-flow branch, so a design "
            f"compiling the other one has no such flop")
    if not asic:
        raise AssertionError("flops.sv defines no flop family at all")
    differ = sorted(name for name in asic if asic[name][0] != fpga[name][0])
    if differ:
        raise AssertionError(
            f"{differ} take different arguments in the two reset-flow branches, "
            f"so one call site cannot serve both")
    # Every parameterized macro takes the clock first, wherever it is defined:
    # the bodies in the branches and the _INST wrappers outside them.
    everywhere = dict(asic, **_flops_defines(sections['outer']))
    everywhere.update(fpga)
    wrong = sorted(f"{name}{tuple(args)}" for name, (args, _) in everywhere.items()
                   if name.endswith('_CLK') and args[0] != 'clkSig')
    if wrong:
        raise AssertionError(
            f"{wrong} do not take the clock 'clkSig' as their first argument")
    return True


def check_flops_bare_macro_is_an_alias():
    """Each bare macro is a one-line alias onto its _CLK form passing `clk`.

    This is what keeps one body per family. A bare macro carrying its own
    always_ff is a second definition of what a flop is, and the two can then
    silently diverge; the argument-for-argument comparison also kills an alias
    that reorders or drops one."""
    sections = _flops_sections()
    outer = _flops_defines(sections['outer'])
    # Every _CLK macro anywhere is expected to have a bare alias: the flop bodies
    # live in the branches, the _INST wrappers outside them. The ASIC branch
    # stands for both; check_flops_clk_variant_per_family pins that they agree.
    everything = dict(outer, **_flops_defines(sections['ASIC']))
    variants = {name for name in everything if name.endswith('_CLK')}
    # The pairing is a bijection, checked in both directions: a variant with no
    # alias breaks an existing single-clock call site, and an alias with no
    # variant is a macro that expands to an undefined one.
    unpaired = sorted({f"{name}_CLK" for name in outer
                       if not name.endswith('_CLK')} ^ variants)
    if unpaired:
        raise AssertionError(
            f"{unpaired} has no counterpart; every flop macro exists both as a "
            f"bare alias and as a _CLK variant")
    for variant in sorted(variants):
        family = variant[:-len('_CLK')]
        args, body = outer[family]
        expected = f"`{variant}(clk, {', '.join(args)})"
        if ' '.join(body.split()) != expected:
            raise AssertionError(
                f"`{family}` expands to {body!r}, expected exactly {expected!r}; "
                f"a bare macro that is not a pure alias is a second flop body")
    # One body per family per branch: counted, so a duplicated body fails even if
    # it is spelled somewhere this case does not read.
    with open(FLOPS_SV) as f:
        bodies = f.read().count('always_ff @(posedge')
    expected = len(_flops_defines(sections['ASIC'])) + len(_flops_defines(sections['FPGA']))
    if bodies != expected:
        raise AssertionError(
            f"flops.sv holds {bodies} always_ff bodies for {expected} "
            f"clock-parameterized macros; each family has exactly one body per "
            f"reset-flow branch")
    return True


# --------------------------------------------------- <block>_regs handler --

_FLOP_CALL = re.compile(r'`(\w+)\s*\(\s*([^,)]*)')


def _flop_calls(text):
    """Every flop-macro invocation in emitted RTL, as (macro name, first arg)."""
    return [(m.group(1), m.group(2).strip())
            for m in _FLOP_CALL.finditer(text)
            if m.group(1).startswith(('DFF', 'SCFF'))]


def _flops_clk_families():
    """Every clock-parameterized macro flops.sv defines, discovered not listed.

    An emitter naming a family the library does not define produces RTL that does
    not preprocess, and a family renamed in flops.sv has to move its call sites
    with it; both are caught by comparing against the file instead of a literal."""
    sections = _flops_sections()
    defined = dict(_flops_defines(sections['outer']),
                   **_flops_defines(sections['ASIC']))
    return {name for name in defined if name.endswith('_CLK')}


def _assert_flops_clocked_by(text, clock, where):
    """Every flop uses the parameterized macro with `clock` as its first argument."""
    calls = _flop_calls(text)
    if not calls:
        raise AssertionError(f"{where} emits no flop macro at all")
    wrong = sorted({(name, arg) for name, arg in calls
                    if not name.endswith('_CLK') or arg != clock})
    if wrong:
        raise AssertionError(
            f"{where} emits {wrong}; every flop must use the clock-parameterized "
            f"macro naming {clock!r}. A bare macro captures the identifier `clk`, "
            f"which is not a port of a module in another domain")
    families = {name for name, _ in calls}
    undefined = sorted(families - _flops_clk_families())
    if undefined:
        raise AssertionError(
            f"{where} emits {undefined}, which {FLOPS_SV} does not define; the "
            f"emitted macro name has to be one the flop library ships")
    return families


def check_regs_handler_non_default_domain(emitted):
    """The handler of a bus in a non-default domain declares that clock and uses
    it in every flop.

    Port list and flop bodies are asserted together on purpose: emitting
    @(posedge clkSlow) in a module whose port list omits clkSlow does not
    elaborate, and declaring it without using it is a dead port."""
    text = emitted[REGS_HANDLER]
    lines = _sv_wrapper_input_lines(text, 'leafA_regs module')
    if lines != ['input clkSlow,', 'input rstBus_n']:
        raise AssertionError(f"leafA_regs declares {lines}, expected "
                             f"['input clkSlow,', 'input rstBus_n']")
    families = _assert_flops_clocked_by(text, 'clkSlow', 'leafA_regs')
    for family in ('DFFREN_CLK', 'DFF_CLK', 'DFFEN_CLK', 'DFFR_CLK'):
        if family not in families:
            raise AssertionError(
                f"leafA_regs emits no {family}; the fixture's registers, memories "
                f"and ready pipeline should each produce one")
    # The generator has five flop-emitting paths and they are separate code, so
    # each is pinned by a shape only that path produces. Without this the fixture
    # could quietly stop reaching one and the case would still pass.
    for why, pattern in (
            ('the per-segment register flop', r"`DFFREN_CLK\(clkSlow, cfgA_reg\[\d+:\d+\]"),
            ('the generate-guarded parameterizable register word',
             r"`DFFREN_CLK\(clkSlow, cfgWide_reg\[32\*gi"),
            ('the parameterizable memory word', r"`DFFEN_CLK\(clkSlow, tbl_reg\[32\*gi"),
            ('the fixed-width memory word', r"`DFFEN_CLK\(clkSlow, tblFixed_data\["),
            ('the memory access sequence', r"`DFF_CLK\(clkSlow, tbl_addr,")):
        if not re.search(pattern, text):
            raise AssertionError(
                f"leafA_regs emits nothing matching {pattern!r}, so {why} is not "
                f"covered by this fixture")
    return True


def check_regs_handler_reset_term(emitted):
    """The select terms are qualified by the handler's own resolved reset name."""
    text = emitted[REGS_HANDLER]
    for select in ('wr_select', 'rd_select'):
        _expect(text, f"{select} = ", 'the handler qualifies its selects',
                'leafA_regs')
    if text.count('& rstBus_n;') != 2:
        raise AssertionError(
            "leafA_regs does not qualify both select terms with rstBus_n; the "
            "handler's reset is the one declared on its own bus clock, and a "
            "literal rst_n is not a port of a project that renamed its resets")
    _refute(text, 'rst_n;', 'the project declares no reset named rst_n',
            'leafA_regs')
    return True


def check_leaf_binds_its_generated_handler(emitted):
    """The routed leaf binds its GENERATED handler's own clock and reset names.

    leafA spans clk and clkSlow and carries the reset of each, while its handler
    spans only clkSlow and carries only that domain's reset, so both sets
    genuinely differ here: a container that bound its own first clock or first
    reset, or the old literal `clk`, names a port the handler does not declare."""
    binds = _instance_binds(emitted[REGS_LEAF], 'leafA module')
    handler = next(name for name in binds if name.endswith('leafA_regs'))
    return _assert_instance_tail(binds, 'leafA module', {
        handler: [('clkSlow', 'clkSlow'), ('rstBus_n', 'rstBus_n')]})


def _memory_instance_binds(emitted, where):
    """The bind list of every memory primitive instantiated in leafA."""
    binds = _instance_binds(emitted[REGS_LEAF], where)
    memories = {name: bound for name, bound in binds.items()
                if name.startswith('uTbl')}
    if len(memories) != 2:
        raise AssertionError(
            f"{where} instantiates {sorted(memories)}, expected the fixture's two "
            f"memories; the fixture no longer covers the memory bind")
    return memories


def check_memory_instance_binds_the_accessor_domain(emitted):
    """A memory primitive is clocked by the domain of the channels reaching it.

    Both of leafA's memories are regAccess and are reached only by the generated
    handler, which is on the register bus (clkSlow). leafA's own set is
    [clk, clkSlow], so the bus clock is NOT the block's first one - an emitter
    taking the block's primary clock, or the old literal `clk`, would clock a
    memory that clkSlow flops in the handler write, and nothing else in the
    toolchain reports that."""
    for name, bound in _memory_instance_binds(emitted, 'leafA module').items():
        if bound[-1] != ('clk', 'clkSlow'):
            raise AssertionError(
                f"leafA memory {name} ends with {bound[-1]}, expected "
                f"('clk', 'clkSlow'); the memory primitive's own port is `clk` "
                f"and the signal is the memory's domain")
    return True


def check_memory_instance_default_domain(emitted):
    """The same memory bind in the DEFAULT domain names the default clock.

    Which is what makes this change churn-free for every single-domain project:
    the memory's accessor domain and the literal that used to be emitted
    coincide there."""
    for name, bound in _memory_instance_binds(
            emitted, 'default-domain leafA module').items():
        if bound[-1] != ('clk', 'clk'):
            raise AssertionError(
                f"leafA memory {name} ends with {bound[-1]}, expected "
                f"('clk', 'clk')")
    return True


def check_regs_handler_is_not_its_owning_block(emitted):
    """The handler carries the BUS domain, not the served block's set.

    leafA spans two clocks - the bus clock of its generated decode and the
    default clock of the logic reaching its register - while its handler spans
    only the bus clock. An emitter reading the owning block's set instead would
    declare a port the handler never clocks anything with, and could pick the
    wrong one for the flops."""
    leaf = _block_module_input_line(emitted[REGS_LEAF], 'leafA module')
    if leaf != 'input clk, clkSlow, rstMain_n, rstBus_n':
        raise AssertionError(
            f"leafA port list is {leaf!r}, expected 'input clk, clkSlow, "
            f"rstMain_n, rstBus_n'; the fixture no longer separates the two sets")
    handler = _names(_sv_wrapper_input_lines(emitted[REGS_HANDLER],
                                            'leafA_regs module'))
    if handler != ['clkSlow', 'rstBus_n']:
        raise AssertionError(
            f"leafA_regs declares {handler}, expected ['clkSlow', 'rstBus_n']")
    return True


def check_regs_handler_default_domain(emitted):
    """A handler in the DEFAULT domain uses the same parameterized spelling.

    One spelling, unconditionally: an emitter that fell back to the bare macro
    whenever the clock happens to be named `clk` would leave two forms in the
    tree and the domain-correct one exercised by nothing shipped."""
    text = emitted[REGS_HANDLER]
    lines = _sv_wrapper_input_lines(text, 'default-domain leafA_regs module')
    if lines != ['input clk,', 'input rstMain_n']:
        raise AssertionError(f"leafA_regs declares {lines}, expected "
                             f"['input clk,', 'input rstMain_n']")
    _assert_flops_clocked_by(text, 'clk', 'default-domain leafA_regs')
    return True


# --------------------------------------------------- apbDecode router --

def check_router_non_default_domain(emitted):
    """The generated router of a bus in a non-default domain declares that clock
    and uses it in every flop.

    Port list and flop bodies are asserted together because the router's port
    list has come from the derived set since before its flops did: the two are
    separate emission sites reading the same domain, and only comparing them
    catches one moving without the other."""
    text = emitted[REGS_ROUTER]
    line = _block_module_input_line(text, 'apbDecode module')
    if line != 'input clkSlow, rstBus_n':
        raise AssertionError(f"apbDecode port list is {line!r}, expected "
                             f"'input clkSlow, rstBus_n'")
    _assert_flops_clocked_by(text, 'clkSlow', 'apbDecode')
    # The generator has three flop-emitting sites in separate code - the parent
    # request capture template, the per-child select template, and the response
    # path appended by hand - so each is pinned by a shape only that site
    # produces. Without this the fixture could quietly stop reaching one.
    for why, pattern in (
            ('the parent request capture',
             r"`DFF_CLK\(clkSlow, paddr_q, apbReg\.paddr\)"),
            ('the transaction-active flop',
             r"`SCFF_CLK\(clkSlow, trans_active, set_trans_active, pready\)"),
            ('the per-child select flop',
             r"`SCFF_CLK\(clkSlow, apbReg_uLeafA_psel, apbReg_uLeafA_next_psel,"),
            ('the parent response path',
             r"`DFF_CLK\(clkSlow, pready, apbReg_next_pready\)")):
        if not re.search(pattern, text):
            raise AssertionError(
                f"apbDecode emits nothing matching {pattern!r}, so {why} is not "
                f"covered by this fixture")
    return True


def check_router_and_handler_share_the_bus_domain(emitted):
    """The router and the handler of one decode tree are clocked by one domain.

    They are the two ends of one APB segment, so a mismatch would put a clock
    crossing on the handshake itself. Two generators read the domain separately,
    and this is the only case that compares their answers."""
    domains = {where: {arg for _name, arg in _flop_calls(emitted[rel])}
               for where, rel in (('apbDecode', REGS_ROUTER),
                                  ('leafA_regs', REGS_HANDLER))}
    if domains['apbDecode'] != domains['leafA_regs'] or len(domains['apbDecode']) != 1:
        raise AssertionError(
            f"the router is clocked by {sorted(domains['apbDecode'])} and its "
            f"handler by {sorted(domains['leafA_regs'])}; one decode tree is one "
            f"bus domain, and each module must carry exactly that one")
    return True


def check_router_default_domain(emitted):
    """A router in the DEFAULT domain uses the same parameterized spelling.

    One spelling, unconditionally: an emitter that fell back to the bare macro
    whenever the clock happens to be named `clk` would leave two forms in the
    tree and the domain-correct one exercised by nothing shipped."""
    text = emitted[REGS_ROUTER]
    line = _block_module_input_line(text, 'default-domain apbDecode module')
    if line != 'input clk, rstMain_n':
        raise AssertionError(f"apbDecode port list is {line!r}, expected "
                             f"'input clk, rstMain_n'")
    _assert_flops_clocked_by(text, 'clk', 'default-domain apbDecode')
    return True


def _assert_router_rejected(feed_clock, router_clocks, expected_clocks):
    """A router whose derived set is widened past its bus domain is an ERROR.

    Both the exit status and the message are asserted: a router emitter reads the
    FIRST entry of the derived set, so a two-clock router that merely generated
    would put a clock crossing on the APB handshake between the router and its
    own handler, emitted as a real port and therefore elaborating cleanly. The
    message has to name the router, both clocks, and the condition - telling the
    author to merge the two domains is a dead end, because the router does not own
    the bus clock it is given.

    No remedy is asserted. These fixtures widen the set with a clocks: entry, but
    a contained instance whose block declares its own clocks, a non-register
    connection carrying clock:, and a second register-bus connection widen it too,
    with no clocks: entry to remove; pinning one prescription here would re-lock a
    message that is wrong for those authors."""
    fixture, _db, built = _build_regs(feed_clock, router_clocks=router_clocks)
    try:
        if built.returncode == 0:
            raise AssertionError(
                f"a router carrying clocks: {router_clocks} with the feed on "
                f"{feed_clock} built successfully; a multi-domain router is not "
                f"supported and must be rejected")
        report = built.stdout + built.stderr
        for needle in ["'apbDecode'", 'single-domain module',
                       *[f"'{clock}'" for clock in expected_clocks]]:
            if needle not in report:
                raise AssertionError(
                    f"the rejection does not mention {needle!r}, so the author "
                    f"cannot tell which block or which clocks to fix:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


def check_router_extra_clock_rejected():
    """The measured wrong-domain shape: the bus is on clkSlow and the router also
    declares the default clock, which canonical order puts FIRST."""
    return _assert_router_rejected('clkSlow', ['clk'], ('clk', 'clkSlow'))


def check_router_extra_clock_rejected_bus_first():
    """The same rejection when canonical order happens to put the BUS clock first.

    Here the emitter's index would pick the right clock, so this is the case that
    pins the rule as being about the CARDINALITY of the router's set rather than
    about the order within it: the router still declares a second clock port that
    nothing clocks, and the supported shape is one domain."""
    return _assert_router_rejected(None, ['clkSlow'], ('clk', 'clkSlow'))


def check_release_cycles_default():
    """The schema default is the count that leaves an existing 1 ns project's
    release where an absolute 5 ns put it (edges at 3, 4, 5 ns)."""
    with open(os.path.join(base_dir, 'config', 'schema.yaml')) as f:
        schema = yaml.safe_load(f)
    if schema['resets']['releaseCycles'] != 'optional(3)':
        raise AssertionError(
            f"resets.releaseCycles is {schema['resets']['releaseCycles']!r}, "
            f"expected 'optional(3)'")
    return True


def main():
    print("=" * 72)
    print("Clock / reset port emission")
    print("=" * 72)
    ok = [_run_case('every timeUnit the schema admits has an sc_time spelling',
                    check_time_unit_map_covers_schema),
          _run_case('resets.releaseCycles defaults to 3',
                    check_release_cycles_default),
          _run_case('every flop family has a _CLK variant in both reset branches',
                    check_flops_clk_variant_per_family),
          _run_case('every bare flop macro is an alias, not a second body',
                    check_flops_bare_macro_is_an_alias),
          _run_case('a router with an authored extra clock is rejected',
                    check_router_extra_clock_rejected),
          _run_case('a router with an extra clock is rejected on cardinality',
                    check_router_extra_clock_rejected_bus_first)]

    fixture, emitted = _generate()
    try:
        cases = [
            ('a leaf in a non-default domain names neither clk nor rst_n',
             check_non_default_domain_port_list),
            ('three clocks and two resets on one input line, canonical order',
             check_multi_domain_port_list),
            ('a block reached from two domains carries both clocks',
             check_two_clock_port_list),
            ('the container declares the union of its children',
             check_container_port_list),
            ("a container binds each child's own clock and reset port names",
             check_container_binds_child_port_names),
            ("a container's bind list is the child's port list",
             check_container_binds_are_the_child_port_lists),
            ("a container binds a foreign child's spelling to its own signals",
             check_container_binds_foreign_child),
            ('no instantiation binds a literal clk/rst_n the child lacks',
             check_container_binds_no_literal_clk),
            ('the SV wrapper port list is the module port list',
             check_wrapper_port_list_matches_module),
            ('the SV wrapper keeps its own one-per-line port style',
             check_wrapper_keeps_per_line_style),
            ('the SV wrapper binds every clock and reset in order',
             check_wrapper_dut_bindings),
            ('a variant trampoline declares and forwards the same list',
             check_variant_trampoline),
            ('one gated clock signal per clock, at its own period and unit',
             check_sc_clock_per_declared_period),
            ('one clock thread per clock over the shared gated toggler',
             check_one_clock_thread_per_clock),
            ('one sc_signal per reset, born released',
             check_reset_signal_per_reset),
            ('each reset is released after its own count of its own clock',
             check_release_counts_own_clock),
            ('no wrapper releases a reset at an absolute time',
             check_release_is_not_absolute_time),
            ('one driver thread per reset, distinctly named',
             check_one_driver_thread_per_reset),
            ('the SC wrapper binds every domain the DUT declares',
             check_sc_wrapper_binds_every_domain),
            ('a BFM binds names the wrapper declares',
             check_bfm_binds_names_the_wrapper_declares),
            ("a BFM is clocked by its own connection's domain",
             check_bfm_binds_its_own_connection_domain),
            ('a leaf wholly in a non-default domain aliases clk and rst_n',
             check_alias_non_default_domain),
            ('a leaf already carrying clk and rst_n gets no alias',
             check_alias_absent_default_domain),
            ('a multi-domain leaf whose first clock is clk gets no alias',
             check_alias_absent_multi_domain_clk_first),
        ]
        ok += [_run_case(label, lambda fn=fn: fn(emitted)) for label, fn in cases]
    finally:
        shutil.rmtree(fixture)

    fixture, emitted = _generate_regs('clkSlow')
    try:
        cases = [
            ('a register handler on a non-default bus clock declares and uses it',
             check_regs_handler_non_default_domain),
            ("the handler's select terms name its own resolved reset",
             check_regs_handler_reset_term),
            ("the handler carries the bus domain, not its owning block's set",
             check_regs_handler_is_not_its_owning_block),
            ("a leaf binds its generated handler's own clock and reset names",
             check_leaf_binds_its_generated_handler),
            ('a memory primitive is clocked by the domain reaching it',
             check_memory_instance_binds_the_accessor_domain),
            ('a router on a non-default bus clock declares and uses it',
             check_router_non_default_domain),
            ('the router and its handler are clocked by one bus domain',
             check_router_and_handler_share_the_bus_domain),
            ('a renamed default reset aliases rst_n independently of the clock',
             check_alias_reset_independent_of_clock),
        ]
        ok += [_run_case(label, lambda fn=fn: fn(emitted)) for label, fn in cases]
    finally:
        shutil.rmtree(fixture)

    fixture, emitted = _generate_regs(None)
    try:
        ok += [_run_case(label, lambda fn=fn: fn(emitted)) for label, fn in (
            ('a default-domain register handler uses the same parameterized macro',
             check_regs_handler_default_domain),
            ('a default-domain router uses the same parameterized macro',
             check_router_default_domain),
            ('a default-domain memory primitive binds the default clock',
             check_memory_instance_default_domain),
        )]
    finally:
        shutil.rmtree(fixture)

    fixture, emitted = _generate_clk_member()
    try:
        ok += [_run_case('a clock named clk that is not first still skips the alias',
                         lambda: check_alias_clk_member_not_first_skips_alias(emitted)),
              _run_case('the alias RHS is the block\'s own clock/reset, not a shared literal',
                         lambda: check_alias_value_is_not_a_shared_literal(emitted))]
    finally:
        shutil.rmtree(fixture)

    print()
    if all(ok):
        print("RESULT: all clock/reset emission checks passed")
        return 0
    print(f"RESULT: {ok.count(False)} of {len(ok)} clock/reset emission checks failed")
    return 1


if __name__ == '__main__':
    sys.exit(main())
