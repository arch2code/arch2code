#!/usr/bin/env python3
"""Coverage for output clocks and resets, the local nets a child instance's
output binding creates inside its container, an export, and a `~` binding
(spec-clock-reset-requirements.md §4.5/§4.6).

Small fixtures are built (and, where an emitted fact is asserted, generated)
per case, then the emitted text or the build diagnostic is read back, the
same way test_clock_reset_emission.py does: assertions are on emitted text or
a diagnostic message, never on generation or a build merely succeeding.

Fixture A ("wireTest"), shared read-only across its five checks: container
`dut` re-declares `clkDiv` as its own `output` clock; `divider` produces
`clkDiv` (exported straight onto `dut`'s own output) and `rstDiv_n` (bound to
a NEW name, `rstDivInt_n`, so it stays a local net); `consumer` binds both
from the local net / the exported net. `divider` also carries a second,
deliberately unused output (`clkDivBy2`) bound to `~`. This mirrors
examples/clkGen at unit-test scale, so the container module's
generated text can be pinned directly: the `output` port declaration, the
internal `wire` line for the local net, the divider's instantiation binds,
the consumer's instantiation binds, and the explicit `.clkDivBy2 ()` for the
`~` binding (R11: an unconnected output is written explicitly, never
silently omitted).

The remaining fixtures each cover one further V-item local nets and exports
introduce: V13 (a connection clock: naming a local net), V7 (a local net
colliding with a reserved name), V5 (an instance driving its own input from
its own output), V6 (an exported reset's declared clock, and a local reset
net's own membership), V11 (the rst_n fallback resolving a local clock's
sole local reset candidate), V16 (a boundary port deriving to an unexported
local net), and V20 (the supply graph's cycle and root rules).
"""

import os
import shutil
import subprocess
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)
if test_dir not in sys.path:
    sys.path.insert(0, test_dir)

from _addrctl_helpers import APB_PREAMBLE, render_leaf, render_plain_block, render_router

ARCH2CODE = os.path.join(base_dir, 'arch2code.py')


def _arch2code(*args, cwd):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run([sys.executable, ARCH2CODE, *args],
                          capture_output=True, text=True, timeout=120,
                          cwd=cwd, env=env)


# Shared preamble: a trivial one-word push_ack stream, and the four
# clock/reset-bearing blocks common to every fixture in this file. `divider`
# carries a second, deliberately unused output (clkDivBy2) so a `~` binding
# is always in scope, whether or not a given case's assertions read it.
PREAMBLE = """types:
    dataT: {{ width: 8, desc: "payload word" }}

structures:
    dataSt:
        data: {{ varType: dataT, desc: "payload word" }}

interfaces:
    dataIf:
        desc: "producer to consumer stream"
        interfaceType: push_ack
        structures:
            - {{ structure: dataSt, structureType: data_t }}

blocks:
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkRef: {{ default: true }}
        resets:
            rstRef_n: {{ clock: clkRef }}
    dut:
        desc: "container under test"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
{dutClocks}
    divider:
        desc: "produces clkDiv (exported or local) and rstDiv_n; clkDivBy2 is unused"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clkRef: {{ }}
            clkDiv: {{ direction: output }}
            clkDivBy2: {{ direction: output }}
        resets:
            rstRef_n: {{ clock: clkRef }}
            rstDiv_n: {{ clock: clkDiv, direction: output }}
    consumer:
        desc: "consumes the divided clock and its own reset"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clk: {{ default: true }}
        resets:
            rst_n: {{ clock: clk }}
        ports:
            in: {{ interface: dataIf, direction: dst }}
    producer:
        desc: "drives the consumer, on the same divided clock"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clk: {{ }}
        resets:
            rst_n: {{ clock: clk }}
        ports:
            out: {{ interface: dataIf, direction: src }}
    plain:
        desc: "declares nothing: implicit clk (input) and rst_n (on clk)"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
    plainNoReset:
        desc: "declares only clk (implicit input) and explicitly no resets"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        resets: {{}}
    osc1:
        desc: "free-running oscillator: no input clock, a root of the supply graph"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clkOut: {{ direction: output }}
    osc2:
        desc: "cross-coupled oscillator pair member (V20 cycle fixture)"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clkIn: {{ }}
            clkOut: {{ direction: output }}
        resets: {{}}
    osc2dual:
        desc: "two-input supplier: clkA (declared FIRST) reaches a real root, clkCycle (declared second) closes a cycle with its pair - the edge rule feeds clkOut from EITHER, so a short-circuiting any() that stops at clkA never finds the cycle behind clkCycle"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clkA:     {{ default: true }}
            clkCycle: {{ }}
            clkOut:   {{ direction: output }}
        resets: {{}}
"""

# consumer's own BFM binding line, generated only for a hasVl block: the one
# emitted fact that reflects its port's resolved domainClock (spec §4.3),
# used to assert V13's resolution result concretely rather than on build
# success alone.
# A second, otherwise-unused clock on consumer, so its port's resolved
# domain (which of ITS OWN clocks the connection's clock: picked) is an
# observable fact - a single-clock consumer's BFM always binds its one
# clock by name regardless of which container net V13 resolved.
TWO_CLOCK_CONSUMER_PREAMBLE = PREAMBLE.replace(
    '''    consumer:
        desc: "consumes the divided clock and its own reset"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clk: {{ default: true }}
        resets:
            rst_n: {{ clock: clk }}
        ports:
            in: {{ interface: dataIf, direction: dst }}''',
    '''    consumer:
        desc: "consumes the divided clock and its own reset; clkAlt is unused elsewhere. Declares no ports: at all, so 'in' is a true top-down port (spec §4.3 rule 2), letting the reaching connection's clock: select which of its two clocks the port lies in"
        hasVl: true
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clk: {{ default: true }}
            clkAlt: {{ period: 40, timeUnit: ns }}
        resets:
            rst_n: {{ clock: clk }}''')

PROJECT = """yamlFormat: 2
projectName: {name}
topInstance: top_tb

projectFiles:
    - ../../yaml/top.yaml

clocks:
    clkRef: {{ desc: "reference clock", default: true, period: 10, timeUnit: ns }}

resets:
    rstRef_n: {{ desc: "reference reset", default: true, clock: clkRef }}

dirs:
    root: ../..

instanceGroups:
    top:
        varType: inst_top
        enumPrefix: INST_TOP_

addressObjects:
    memories:  {{ alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true }}
    registers: {{ alignment: 8, sortDescending: true }}

fileGeneration:
    layout: hierarchical
    template: $a2c/templates/fileGen/fileGen.py
"""


def _build(name, dut_clocks, instances, connections='', connection_maps='',
          expect_success=True, preamble=PREAMBLE):
    """Write and build one fixture. Returns (fixture_dir, db_path, result)."""
    fixture = tempfile.mkdtemp(prefix='clklocalnet_')
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(PROJECT.format(name=name))
    design = preamble.format(dutClocks=dut_clocks) + "\ninstances:\n" + instances
    if connections:
        design += "\nconnections:\n" + connections
    if connection_maps:
        design += "\nconnectionMaps:\n" + connection_maps
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(design)

    db = os.path.join(fixture, f"{name}.db")
    built = _arch2code('--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'),
                       '--db', db, cwd=fixture)
    if expect_success and built.returncode != 0:
        raise AssertionError(f"database build failed:\n{built.stdout}\n{built.stderr}")
    return fixture, db, built


# --------------------------------------------------- Fixture A: wireTest --

DUT_CLOCKS_EXPORTED = """        clocks:
            clkRef: { default: true }
            clkDiv: { direction: output }
        resets:
            rstRef_n: { clock: clkRef }
"""

INSTANCES_A = """    top_tb:    { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:     { container: top_tb, instanceType: dut, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: ~ }, resets: { rstRef_n: rstRef_n } }
    uDivider:  { container: dut, instanceType: divider, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ },
                 resets: { rstRef_n: rstRef_n, rstDiv_n: rstDivInt_n } }
    uProducer: { container: dut, instanceType: producer, instGroup: top,
                 clocks: { clk: clkDiv }, resets: { rst_n: rstDivInt_n } }
    uConsumer: { container: dut, instanceType: consumer, instGroup: top,
                 clocks: { clk: clkDiv }, resets: { rst_n: rstDivInt_n } }
"""

CONNECTIONS_A = (
    "    - { interface: dataIf, src: uProducer, srcport: out, dst: uConsumer, "
    "dstport: in }\n"
)


def _generate_wire_test():
    """Built once and shared by every Fixture A check (they only read the
    emitted text, never mutate the fixture)."""
    fixture, db, built = _build('wireTest', DUT_CLOCKS_EXPORTED, INSTANCES_A,
                                CONNECTIONS_A)
    made = _arch2code('--db', db, '-r', '--newmodule', cwd=fixture)
    if made.returncode != 0:
        raise AssertionError(f"newmodule failed:\n{made.stdout}\n{made.stderr}")
    rel = 'rtl/dut.sv'
    gen = _arch2code('--db', db, '-r', '--systemVerilog',
                     '--file', os.path.join(fixture, rel), cwd=fixture)
    if gen.returncode != 0:
        raise AssertionError(f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
    with open(os.path.join(fixture, rel)) as f:
        text = f.read()
    return fixture, text


def check_container_declares_output_port(text):
    """R18: an `output` clock the container itself declares (clkDiv, exported
    from uDivider) is a port of the container's own module."""
    if 'output clkDiv' not in text:
        raise AssertionError(
            f"dut.sv's port list does not declare 'output clkDiv':\n{text}")
    return True


def check_container_declares_local_net_wire(text):
    """R18 "one internal net per local net": rstDiv_n is bound to a NAME
    dut does not declare (rstDivInt_n), so it is a local net and needs its
    own internal wire, distinct from dut's port list."""
    if 'wire rstDivInt_n;' not in text:
        raise AssertionError(
            f"dut.sv does not declare 'wire rstDivInt_n;' for its local "
            f"reset net:\n{text}")
    return True


def check_divider_instantiation_binds_export_and_local_net(text):
    """uDivider's own clkDiv binds onto dut's declared output (the export);
    its rstDiv_n binds onto the local net."""
    for needle in ('.clkDiv (clkDiv)', '.rstDiv_n (rstDivInt_n)'):
        if needle not in text:
            raise AssertionError(
                f"uDivider's instantiation does not contain {needle!r}:\n{text}")
    return True


def check_consumer_instantiation_binds_local_net_and_export(text):
    """uConsumer's clk binds onto dut's exported clkDiv; its rst_n binds
    onto the same local reset net the divider drives."""
    for needle in ('.clk (clkDiv)', '.rst_n (rstDivInt_n)'):
        if needle not in text:
            raise AssertionError(
                f"uConsumer's instantiation does not contain {needle!r}:\n{text}")
    return True


def check_unconnected_output_written_explicitly(text):
    """R11: clkDivBy2 is bound to `~` and left unconnected, but the
    instantiation writes the port explicitly (`.clkDivBy2 ()`), rather than
    dropping it from the instance's port connection list silently."""
    if '.clkDivBy2 ()' not in text:
        raise AssertionError(
            f"uDivider's instantiation does not write clkDivBy2 explicitly "
            f"unconnected ('.clkDivBy2 ()'):\n{text}")
    return True


FIXTURE_A_CHECKS = [
    ("dut declares clkDiv as an output port",
     check_container_declares_output_port),
    ('a local net gets its own internal wire declaration',
     check_container_declares_local_net_wire),
    ("the driving instance's own bind names the export and the local net",
     check_divider_instantiation_binds_export_and_local_net),
    ("a consuming instance's own bind names the export and the local net",
     check_consumer_instantiation_binds_local_net_and_export),
    ('a `~`-bound output is written explicitly unconnected',
     check_unconnected_output_written_explicitly),
]


# ---------------------------------------------- Fixture B: v13LocalNet --

DUT_CLOCKS_UNEXPORTED = """        clocks:
            clkRef: { default: true }
        resets:
            rstRef_n: { clock: clkRef }
"""

INSTANCES_B = """    top_tb:    { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:     { container: top_tb, instanceType: dut, instGroup: top,
                 clocks: { clkRef: clkRef }, resets: { rstRef_n: rstRef_n } }
    uDivider:  { container: dut, instanceType: divider, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ },
                 resets: { rstRef_n: rstRef_n, rstDiv_n: rstDivInt_n } }
    uProducer: { container: dut, instanceType: producer, instGroup: top,
                 clocks: { clk: clkDiv }, resets: { rst_n: rstDivInt_n } }
    uConsumer: { container: dut, instanceType: consumer, instGroup: top,
                 clocks: { clk: clkDiv }, resets: { rst_n: rstDivInt_n } }
"""

CONNECTION_ON_LOCAL_NET = (
    "    - { interface: dataIf, src: uProducer, srcport: out, dst: uConsumer, "
    "dstport: in, clock: clkDiv }\n"
)

# consumer carries a second clock (clkAlt) here, bound to the local net
# clkDiv while its default clk is bound elsewhere (clkRef): the connection's
# clock: must pick clkAlt, not clk, so the resolution is a real fact the
# generated BFM bind can be checked against.
INSTANCES_V13POS = """    top_tb:    { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:     { container: top_tb, instanceType: dut, instGroup: top,
                 clocks: { clkRef: clkRef }, resets: { rstRef_n: rstRef_n } }
    uDivider:  { container: dut, instanceType: divider, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ },
                 resets: { rstRef_n: rstRef_n, rstDiv_n: rstDivInt_n } }
    uProducer: { container: dut, instanceType: producer, instGroup: top,
                 clocks: { clk: clkDiv }, resets: { rst_n: rstDivInt_n } }
    uConsumer: { container: dut, instanceType: consumer, instGroup: top,
                 clocks: { clk: clkRef, clkAlt: clkDiv }, resets: { rst_n: rstRef_n } }
"""


def check_v13_resolves_against_a_local_net():
    """V13: a connection's clock: may name a LOCAL net (clkDiv, never
    exported by dut here), the same way it resolves against a declared
    container clock. uConsumer's clkAlt, not its default clk, is the one
    bound to clkDiv, so its port's resolved domain (clkAlt) is a generated
    fact - its BFM's own clk bind - checked directly, not inferred from
    build success alone."""
    fixture, db, built = _build('v13LocalNet', DUT_CLOCKS_UNEXPORTED,
                                INSTANCES_V13POS, CONNECTION_ON_LOCAL_NET,
                                preamble=TWO_CLOCK_CONSUMER_PREAMBLE)
    try:
        made = _arch2code('--db', db, '-r', '--newmodule', cwd=fixture)
        if made.returncode != 0:
            raise AssertionError(f"newmodule failed:\n{made.stdout}\n{made.stderr}")
        rel = 'verif/consumer_hdl_sc_wrapper.h'
        gen = _arch2code('--db', db, '-r', '--systemc',
                         '--file', os.path.join(fixture, rel), cwd=fixture)
        if gen.returncode != 0:
            raise AssertionError(f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
        with open(os.path.join(fixture, rel)) as f:
            text = f.read()
        if 'in_bfm.clk(clkAlt);' not in text:
            raise AssertionError(
                f"consumer's own BFM does not bind clk to clkAlt, the block's "
                f"own clock the connection's clock: (clkDiv) resolved to:\n{text}")
    finally:
        shutil.rmtree(fixture)
    return True


def check_v13_rejects_local_net_neither_end_resolves_to():
    """V13: a connection's clock: naming a net that NEITHER end's input
    clock resolves to is an error - here `clkRef`, dut's own declared
    clock, while both uProducer and uConsumer run on the divider's clkDiv
    local net instead."""
    connection = CONNECTION_ON_LOCAL_NET.replace('clock: clkDiv', 'clock: clkRef')
    fixture, _db, built = _build('v13LocalNetMiss', DUT_CLOCKS_UNEXPORTED,
                                 INSTANCES_B, connection,
                                 expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "a connection clock: naming a local net neither end resolves "
                "to built successfully; expected a V13 diagnostic")
        report = built.stdout + built.stderr
        if 'V13' not in report:
            raise AssertionError(f"the rejection does not cite V13:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


# ---------------------------------------------------- Fixture C: V7 --

def check_v7_local_net_collides_with_reserved_name():
    """V7: dut declares no clk/rst_n of its own, so both names are reserved
    aliases onto its default clock (clkRef) and selected reset (rstRef_n).
    Binding the divider's rstDiv_n output onto the literal name 'rst_n'
    collides with that reservation - a local net's name may not collide
    with the container's own clocks, resets, ports, memories, or the
    reserved clk/rst_n names."""
    instances = INSTANCES_A.replace('rstDiv_n: rstDivInt_n', 'rstDiv_n: rst_n')
    fixture, _db, built = _build('v7LocalNetCollision', DUT_CLOCKS_EXPORTED,
                                 instances, CONNECTIONS_A, expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "a local net named 'rst_n' built successfully; expected a "
                "V7 collision with dut's reserved rst_n alias")
        report = built.stdout + built.stderr
        for needle in ("'rst_n'", 'V7'):
            if needle not in report:
                raise AssertionError(f"the rejection does not mention {needle!r}:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


# ------------------------------------------------- Fixture D: V5, V6, V11 --

def check_v5_rejects_self_driven_input():
    """V5: uDivider binds its own INPUT clkRef onto 'clkDiv', the net its
    own OUTPUT clkDiv already drives - a combinational loop through the
    child, rejected regardless of the net's name matching by coincidence."""
    instances = INSTANCES_A.replace(
        'clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ }',
        'clocks: { clkRef: clkDiv, clkDiv: clkDiv, clkDivBy2: ~ }')
    fixture, _db, built = _build('v5SelfDriven', DUT_CLOCKS_EXPORTED,
                                 instances, CONNECTIONS_A, expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "uDivider binding its own input to a net its own output "
                "drives built successfully; expected a V5 diagnostic")
        report = built.stdout + built.stderr
        if 'V5' not in report:
            raise AssertionError(f"the rejection does not cite V5:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


DUT_CLOCKS_EXPORT_RESET = """        clocks:
            clkRef: { default: true }
            clkDiv: { direction: output }
        resets:
            rstRef_n: { clock: clkRef, default: true }
            rstDiv_n: { clock: clkRef, direction: output }
"""

INSTANCES_V6EXPORT = """    top_tb:    { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:     { container: top_tb, instanceType: dut, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: ~ }, resets: { rstRef_n: rstRef_n, rstDiv_n: ~ } }
    uDivider:  { container: dut, instanceType: divider, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ },
                 resets: { rstRef_n: rstRef_n, rstDiv_n: rstDiv_n } }
"""


def check_v6_rejects_export_clock_mismatch():
    """V6, the export case: dut declares rstDiv_n's own clock as clkRef, but
    uDivider's rstDiv_n actually belongs to clkDiv (mapped through its own
    instance) - the supplier's own reset domain must agree with what the
    container's declaration claims for the net it exports onto."""
    fixture, _db, built = _build('v6ExportMismatch', DUT_CLOCKS_EXPORT_RESET,
                                 INSTANCES_V6EXPORT, expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "exporting a reset to a declared output whose stated clock "
                "disagrees with the supplier's own built successfully; "
                "expected a V6 diagnostic")
        report = built.stdout + built.stderr
        if 'V6' not in report:
            raise AssertionError(f"the rejection does not cite V6:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


INSTANCES_V6LOCAL = """    top_tb:    { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:     { container: top_tb, instanceType: dut, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: ~ }, resets: { rstRef_n: rstRef_n } }
    uDivider:  { container: dut, instanceType: divider, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ },
                 resets: { rstRef_n: rstRef_n, rstDiv_n: rstDivInt_n } }
    uConsumer: { container: dut, instanceType: consumer, instGroup: top,
                 clocks: { clk: clkRef }, resets: { rst_n: rstDivInt_n } }
"""


def check_v6_rejects_local_net_membership_mismatch():
    """V6, the local-net case: uConsumer's own clock (clk) is bound to
    clkRef, but its reset (rst_n) is bound to rstDivInt_n, a local net
    released on clkDiv instead - the two must agree."""
    fixture, _db, built = _build('v6LocalMismatch', DUT_CLOCKS_EXPORTED,
                                 INSTANCES_V6LOCAL, expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "a reset bound to a local net released on a different clock "
                "than the consumer's own clock built successfully; expected "
                "a V6 diagnostic")
        report = built.stdout + built.stderr
        if 'V6' not in report:
            raise AssertionError(f"the rejection does not cite V6:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


INSTANCES_V11POS = """    top_tb:    { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:     { container: top_tb, instanceType: dut, instGroup: top,
                 clocks: { clkRef: clkRef }, resets: { rstRef_n: rstRef_n } }
    uDivider:  { container: dut, instanceType: divider, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ },
                 resets: { rstRef_n: rstRef_n, rstDiv_n: rstDivInt_n } }
    uPlain:    { container: dut, instanceType: plain, instGroup: top,
                 clocks: { clk: clkDiv } }
"""


def check_v11_fallback_resolves_local_reset():
    """V11 positive: uPlain declares nothing (implicit clk/rst_n, spec R5);
    its clk maps to the local clock net clkDiv, and rst_n is left unmapped.
    The sole local reset net on clkDiv (rstDivInt_n) is its selected reset
    (spec §4.2), so the automatic rst_n fallback must resolve to it rather
    than reject for lack of a declared candidate."""
    fixture, db, built = _build('v11LocalFallback', DUT_CLOCKS_UNEXPORTED,
                                INSTANCES_V11POS)
    try:
        made = _arch2code('--db', db, '-r', '--newmodule', cwd=fixture)
        if made.returncode != 0:
            raise AssertionError(f"newmodule failed:\n{made.stdout}\n{made.stderr}")
        rel = 'rtl/dut.sv'
        gen = _arch2code('--db', db, '-r', '--systemVerilog',
                         '--file', os.path.join(fixture, rel), cwd=fixture)
        if gen.returncode != 0:
            raise AssertionError(f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
        with open(os.path.join(fixture, rel)) as f:
            text = f.read()
        if '.rst_n (rstDivInt_n)' not in text:
            raise AssertionError(
                f"uPlain's own rst_n fallback did not resolve to the local "
                f"reset net rstDivInt_n:\n{text}")
    finally:
        shutil.rmtree(fixture)
    return True


# ------------------------------------------------- Fixture E: V16, V20 --

INSTANCES_V16 = """    top_tb:       { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:        { container: top_tb, instanceType: dut, instGroup: top,
                    clocks: { clkRef: clkRef }, resets: { rstRef_n: rstRef_n } }
    uOuterProducer: { container: top_tb, instanceType: producer, instGroup: top,
                    clocks: { clk: clkRef }, resets: { rst_n: rstRef_n } }
    uDivider:     { container: dut, instanceType: divider, instGroup: top,
                    clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ },
                    resets: { rstRef_n: rstRef_n, rstDiv_n: rstDivInt_n } }
    uConsumer:    { container: dut, instanceType: consumer, instGroup: top,
                    clocks: { clk: clkDiv }, resets: { rst_n: rstDivInt_n } }
"""

CONNECTION_V16 = (
    "    - { interface: dataIf, src: uOuterProducer, srcport: out, dst: u_dut, "
    "name: toConsumer }\n"
)

CONNECTION_MAPS_V16 = (
    "    - { interface: dataIf, block: dut, direction: dst, instance: uConsumer, "
    "name: toConsumer }\n"
)


def check_v16_rejects_boundary_port_on_unexported_local_net():
    """V16: dut never exports clkDiv, so uConsumer's own domain (the local
    net clkDiv) cannot back a boundary port a connectionMaps: row routes to
    it - the parent could neither drive nor name that domain."""
    fixture, _db, built = _build('v16LocalBoundary', DUT_CLOCKS_UNEXPORTED,
                                 INSTANCES_V16, CONNECTION_V16, CONNECTION_MAPS_V16,
                                 expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "a connectionMaps: boundary port deriving to an unexported "
                "local net built successfully; expected a V16 diagnostic")
        report = built.stdout + built.stderr
        if 'V16' not in report:
            raise AssertionError(f"the rejection does not cite V16:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


INSTANCES_CYCLE = """    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:  { container: top_tb, instanceType: dut, instGroup: top,
              clocks: { clkRef: clkRef }, resets: { rstRef_n: rstRef_n } }
    uOscA:  { container: dut, instanceType: osc2, instGroup: top,
              clocks: { clkIn: clkB, clkOut: clkA } }
    uOscB:  { container: dut, instanceType: osc2, instGroup: top,
              clocks: { clkIn: clkA, clkOut: clkB } }
"""


def check_v20_rejects_supply_cycle():
    """V20: two cross-coupled dividers, each clocked by the other's output,
    with no external supply at all - the supply graph must be acyclic."""
    fixture, _db, built = _build('v20Cycle', DUT_CLOCKS_UNEXPORTED,
                                 INSTANCES_CYCLE, expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "two instances clocking each other built successfully; "
                "expected a V20 supply-cycle diagnostic")
        report = built.stdout + built.stderr
        if 'V20' not in report:
            raise AssertionError(f"the rejection does not cite V20:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


INSTANCES_TWO_INPUT_CYCLE = """    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:  { container: top_tb, instanceType: dut, instGroup: top,
              clocks: { clkRef: clkRef }, resets: { rstRef_n: rstRef_n } }
    uDualA: { container: dut, instanceType: osc2dual, instGroup: top,
              clocks: { clkA: clkRef, clkCycle: clkDualB, clkOut: clkDualA } }
    uDualB: { container: dut, instanceType: osc2dual, instGroup: top,
              clocks: { clkA: clkRef, clkCycle: clkDualA, clkOut: clkDualB } }
"""


def check_v20_rejects_cycle_behind_a_second_input():
    """V20 determinism: uDualA/uDualB each have TWO inputs, clkA (declared
    first, bound to the real clkRef) and clkCycle (declared second, closing
    a cycle with the other instance). The edge rule feeds clkOut from EITHER
    input, so the cycle behind clkCycle must still be reported even though
    clkA alone would answer "reaches a root" - a check that evaluated inputs
    with a short-circuiting any() over a hash-ordered set could miss this
    whenever clkA happened to be visited first."""
    fixture, _db, built = _build('v20TwoInputCycle', DUT_CLOCKS_UNEXPORTED,
                                 INSTANCES_TWO_INPUT_CYCLE, expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "a two-input supplier whose SECOND input closes a cycle built "
                "successfully; expected a V20 supply-cycle diagnostic")
        report = built.stdout + built.stderr
        if 'V20' not in report:
            raise AssertionError(f"the rejection does not cite V20:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


INSTANCES_ROOT = """    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:  { container: top_tb, instanceType: dut, instGroup: top,
              clocks: { clkRef: clkRef }, resets: { rstRef_n: rstRef_n } }
    uOsc:   { container: dut, instanceType: osc1, instGroup: top,
              clocks: { clkOut: clkOsc } }
    uPlain: { container: dut, instanceType: plainNoReset, instGroup: top,
              clocks: { clk: clkOsc } }
"""


def check_v20_accepts_oscillator_as_root():
    """V20 positive: uOsc has no input clock or reset at all, so it is a
    root of the supply graph (spec §4.5/V20); a consumer running on its
    output must build clean, with no cycle or missing-root diagnostic - and
    the generated container must actually wire the oscillator's output onto
    the local net uPlain consumes, not merely build without error."""
    fixture, db, _built = _build('v20Root', DUT_CLOCKS_UNEXPORTED, INSTANCES_ROOT)
    try:
        made = _arch2code('--db', db, '-r', '--newmodule', cwd=fixture)
        if made.returncode != 0:
            raise AssertionError(f"newmodule failed:\n{made.stdout}\n{made.stderr}")
        rel = 'rtl/dut.sv'
        gen = _arch2code('--db', db, '-r', '--systemVerilog',
                         '--file', os.path.join(fixture, rel), cwd=fixture)
        if gen.returncode != 0:
            raise AssertionError(f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
        with open(os.path.join(fixture, rel)) as f:
            text = f.read()
        if '.clkOut (clkOsc)' not in text:
            raise AssertionError(
                f"uOsc's own output clkOut is not bound to the local net "
                f"clkOsc:\n{text}")
    finally:
        shutil.rmtree(fixture)
    return True


# --------------------------------- Fixture F: V19, a local reset candidate --

# A router, a routed leaf (leafA) and a reset synchroniser, built independently
# of the PREAMBLE topology above: leafA's second clock, clkBus, hosts its
# register bus (registerPorts:'s own clock:, spec §4.3 rule 1); uSync, a
# child INSIDE leafA's own container, is the only other source of a reset on
# clkBus, driving the local net rstBusInt_n. Extending BlockDomains.
# selectedReset with local candidates (spec §4.2 "selected reset", second
# pass) must pick it up as a candidate for the register bus's own reset
# (V19). uRegConsumer keeps rstBusInt_n consumed (V22) independently of how
# the synthesised handler's own reset resolves, so an ambiguous candidate
# set is reported as V19, not masked by an unrelated V22 finding.

SYNC_BLOCK = """    sync:
        desc: "reset synchroniser: produces a synchronised reset from its own input clock; declares no reset of its own to release it"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clkIn: { }
        resets:
            rstSync_n: { clock: clkIn, direction: output }
"""

REG_CONSUMER_BLOCK = """    regConsumer:
        desc: "consumes the register bus's local reset net directly, so it always has a consumer regardless of how the handler's own binding resolves"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clk: { }
        resets:
            rst_n: { clock: clk }
"""

REGISTER_LOCAL_RESET = ("registers:\n"
                        "    - { register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, "
                        "desc: \"leafA configuration\" }\n")

INSTANCES_LOCAL_RESET = (
    "    uSync:        { container: leafA, instanceType: sync,\n"
    "                    clocks: { clkIn: clkBus }, resets: { rstSync_n: rstBusInt_n } }\n"
    "    uRegConsumer: { container: leafA, instanceType: regConsumer,\n"
    "                    clocks: { clk: clkBus }, resets: { rst_n: rstBusInt_n } }\n")


def _registered_leaf_design(leaf_extra_lines, leaf_reset_map=''):
    """Assemble the router/leaf/synchroniser design; `leaf_extra_lines`
    supplies leafA's own clocks:/resets: (its register-bus clock, clkBus,
    declares zero or one reset of its own on it, per the calling check).
    `leaf_reset_map` binds any further declared INPUT reset of leafA's own
    (e.g. rstBusDecl_n) that 'top' cannot bind by name match or fallback,
    onto 'top's own rst_n (V3) - membership still agrees, since clkBus
    itself is mapped onto 'top's own default clock below (V6)."""
    leaf = render_leaf('leafA', extra_block_lines=leaf_extra_lines,
                       port_extra=', clock: clkBus')
    return f"""include:
    - shared.yaml

blocks:
{render_plain_block('top')}{render_plain_block('cpu')}{render_router('apbDecode', 'top')}{leaf}{SYNC_BLOCK}{REG_CONSUMER_BLOCK}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top,
                  clocks: {{ clkBus: clk }}{leaf_reset_map} }}
{INSTANCES_LOCAL_RESET}
connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

{REGISTER_LOCAL_RESET}"""


PROJECT_REG = """yamlFormat: 2
projectName: {name}
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
    memories:  {{ alignment: memsize, sizeRoundUpPowerOf2: true, sortDescending: true }}
    registers: {{ alignment: 8, sortDescending: true }}

fileGeneration:
    layout: hierarchical
    template: $a2c/templates/fileGen/fileGen.py
"""


def _build_registered_leaf(name, leaf_extra_lines, leaf_reset_map='', expect_success=True):
    """Write and build the router/leaf/synchroniser fixture. Returns
    (fixture_dir, db_path, result)."""
    fixture = tempfile.mkdtemp(prefix='clkregleaf_')
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(PROJECT_REG.format(name=name))
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(_registered_leaf_design(leaf_extra_lines, leaf_reset_map))

    db = os.path.join(fixture, f"{name}.db")
    built = _arch2code('--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'),
                       '--db', db, cwd=fixture)
    if expect_success and built.returncode != 0:
        raise AssertionError(f"database build failed:\n{built.stdout}\n{built.stderr}")
    return fixture, db, built


LEAF_EXTRA_SOLE_LOCAL = ("        clocks:\n"
                        "            clk:    { default: true }\n"
                        "            clkBus: { }\n"
                        "        resets:\n"
                        "            rst_n:  { clock: clk }\n")


def check_v19_selects_sole_local_reset_candidate():
    """V19 positive: leafA's register bus clock (clkBus) declares no reset
    of its own at all; the sole candidate is uSync's local output
    rstBusInt_n. The extended BlockDomains.selectedReset must pick it up,
    with no V19 diagnostic, and the synthesised handler's own reset must
    reach generation bound to it - its own port renamed to the net name
    (spec §4.3 "Routers"), so both sides of the bind read rstBusInt_n."""
    fixture, db, built = _build_registered_leaf('v19SoleLocal', LEAF_EXTRA_SOLE_LOCAL)
    try:
        report = built.stdout + built.stderr
        if 'V19' in report:
            raise AssertionError(
                f"a register bus clock whose sole reset candidate is a "
                f"local net raised V19; expected the local net to be "
                f"selected instead:\n{report}")
        made = _arch2code('--db', db, '-r', '--newmodule', cwd=fixture)
        if made.returncode != 0:
            raise AssertionError(f"newmodule failed:\n{made.stdout}\n{made.stderr}")
        rel = 'rtl/leafA.sv'
        gen = _arch2code('--db', db, '-r', '--systemVerilog',
                         '--file', os.path.join(fixture, rel), cwd=fixture)
        if gen.returncode != 0:
            raise AssertionError(f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
        with open(os.path.join(fixture, rel)) as f:
            text = f.read()
        if '.rstBusInt_n (rstBusInt_n)' not in text:
            raise AssertionError(
                f"leafA.sv's synthesised register handler is not bound to "
                f"the local reset net rstBusInt_n:\n{text}")
    finally:
        shutil.rmtree(fixture)
    return True


LEAF_EXTRA_AMBIGUOUS = ("        clocks:\n"
                       "            clk:    { default: true }\n"
                       "            clkBus: { }\n"
                       "        resets:\n"
                       "            rst_n:        { clock: clk }\n"
                       "            rstBusDecl_n: { clock: clkBus }\n")


def check_v19_rejects_two_unmarked_candidates():
    """V19 negative: clkBus now has TWO reset candidates - the declared
    rstBusDecl_n and uSync's local rstBusInt_n - and neither marks
    default: true, so the register bus's reset is ambiguous."""
    fixture, _db, built = _build_registered_leaf(
        'v19TwoCandidates', LEAF_EXTRA_AMBIGUOUS,
        leaf_reset_map=', resets: { rstBusDecl_n: rst_n }', expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "a register bus clock with two unmarked reset candidates "
                "(one declared, one local) built successfully; expected a "
                "V19 diagnostic")
        report = built.stdout + built.stderr
        if 'V19' not in report:
            raise AssertionError(f"the rejection does not cite V19:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


# ------------------------------------------------------------- harness --

def _run_case(label, fn):
    try:
        ok = fn()
    except AssertionError as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    if not ok:
        print(f"FAIL: {label}: returned falsy")
        return False
    print(f"PASS: {label}")
    return True


def main():
    print("=" * 72)
    print("Clock/reset local nets, exports, and `~` bindings")
    print("=" * 72)
    ok = []
    fixture, text = _generate_wire_test()
    try:
        ok += [_run_case(label, lambda fn=fn: fn(text)) for label, fn in FIXTURE_A_CHECKS]
    finally:
        shutil.rmtree(fixture)

    cases = [
        ("V13 resolves a connection's clock: against a local net",
         check_v13_resolves_against_a_local_net),
        ('V13 rejects a connection clock: naming a local net neither end resolves to',
         check_v13_rejects_local_net_neither_end_resolves_to),
        ("V7 rejects a local net colliding with a container's reserved rst_n",
         check_v7_local_net_collides_with_reserved_name),
        ("V5 rejects an instance binding its own input to a net its own output drives",
         check_v5_rejects_self_driven_input),
        ('V6 rejects an exported reset whose declared clock disagrees with the supplier',
         check_v6_rejects_export_clock_mismatch),
        ("V6 rejects a reset bound to a local net whose membership disagrees with the consumer's own clock",
         check_v6_rejects_local_net_membership_mismatch),
        ('V11 fallback resolves rst_n to the sole local reset net on a local clock',
         check_v11_fallback_resolves_local_reset),
        ('V16 rejects a boundary port deriving to an unexported local net',
         check_v16_rejects_boundary_port_on_unexported_local_net),
        ('V20 rejects a supply cycle between two cross-coupled dividers',
         check_v20_rejects_supply_cycle),
        ('V20 rejects a cycle behind a two-input supplier\'s second input',
         check_v20_rejects_cycle_behind_a_second_input),
        ('V20 accepts a no-input-clock oscillator as a supply-graph root',
         check_v20_accepts_oscillator_as_root),
        ('V19 selects a register bus clock\'s sole local reset candidate',
         check_v19_selects_sole_local_reset_candidate),
        ('V19 rejects a register bus clock with two unmarked reset candidates',
         check_v19_rejects_two_unmarked_candidates),
    ]
    ok += [_run_case(label, fn) for label, fn in cases]

    print()
    print("=" * 72)
    if all(ok):
        print(f"RESULT: all {len(ok)} local-net checks passed")
    else:
        print(f"RESULT: {ok.count(False)} of {len(ok)} local-net checks FAILED")
    print("=" * 72)
    return 0 if all(ok) else 1


if __name__ == '__main__':
    sys.exit(main())
