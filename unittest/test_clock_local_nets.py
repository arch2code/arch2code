#!/usr/bin/env python3
"""Coverage for output clocks and resets, the local nets a child instance's
output binding creates inside its container, an export, and a `~` binding.

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
`~` binding (an unconnected output is written explicitly, never silently
omitted).

The remaining fixtures each cover one further rule local nets and exports
introduce: a connection clock: naming a local net, a local net colliding
with a reserved name, an instance driving its own input from its own
output, an exported reset's declared clock and a local reset net's own
membership, the rst_n fallback resolving a local clock's sole local reset
candidate, a boundary port deriving to an unexported local net, and the
supply graph's cycle and root rules.
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
        desc: "cross-coupled oscillator pair member (supply-cycle fixture)"
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
# emitted fact that reflects its port's resolved domainClock, used to assert
# the connection clock: resolution concretely rather than on build success
# alone.
# A second, otherwise-unused clock on consumer, so its port's resolved
# domain (which of ITS OWN clocks the connection's clock: picked) is an
# observable fact - a single-clock consumer's BFM always binds its one
# clock by name regardless of which container net the connection resolved.
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
        desc: "consumes the divided clock and its own reset; declares no ports: at all, so 'in' is a true top-down port, letting the reaching connection's clock: select which of its two clocks the port lies in"
        hasVl: true
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clk: {{ default: true }}
            clkAlt: {{ period: 40, timeUnit: ns }}
        resets:
            rst_n: {{ clock: clk }}
            rstAlt_n: {{ clock: clkAlt }}''')

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
    """An `output` clock the container itself declares (clkDiv, exported
    from uDivider) is a port of the container's own module."""
    if 'output clkDiv' not in text:
        raise AssertionError(
            f"dut.sv's port list does not declare 'output clkDiv':\n{text}")
    return True


def check_container_declares_local_net_wire(text):
    """One internal net per local net: rstDiv_n is bound to a NAME
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
    """clkDivBy2 is bound to `~` and left unconnected, but the
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


# ------------------------------ Fixture B: a connection clock: on a local net --

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
INSTANCES_CONN_CLOCK_ON_LOCAL_NET = """    top_tb:    { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:     { container: top_tb, instanceType: dut, instGroup: top,
                 clocks: { clkRef: clkRef }, resets: { rstRef_n: rstRef_n } }
    uDivider:  { container: dut, instanceType: divider, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ },
                 resets: { rstRef_n: rstRef_n, rstDiv_n: rstDivInt_n } }
    uProducer: { container: dut, instanceType: producer, instGroup: top,
                 clocks: { clk: clkDiv }, resets: { rst_n: rstDivInt_n } }
    uConsumer: { container: dut, instanceType: consumer, instGroup: top,
                 clocks: { clk: clkRef, clkAlt: clkDiv },
                 resets: { rst_n: rstRef_n, rstAlt_n: rstDivInt_n } }
"""


def check_connection_clock_resolves_against_a_local_net():
    """A connection's clock: may name a LOCAL net (clkDiv, never
    exported by dut here), the same way it resolves against a declared
    container clock. uConsumer's clkAlt, not its default clk, is the one
    bound to clkDiv, so its port's resolved domain (clkAlt) is a generated
    fact - its BFM's own clk bind - checked directly, not inferred from
    build success alone."""
    fixture, db, built = _build('connClockLocalNet', DUT_CLOCKS_UNEXPORTED,
                                INSTANCES_CONN_CLOCK_ON_LOCAL_NET, CONNECTION_ON_LOCAL_NET,
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


def check_declared_port_clock_disagreeing_with_connection_clock_rejected():
    """A declared port's own clock and the connection's clock: reaching it
    must agree. Both uProducer's and uConsumer's ports are declared on their
    block default clock, which each instance binds to the divider's clkDiv
    local net, but the connection names clkRef, dut's own declared clock."""
    connection = CONNECTION_ON_LOCAL_NET.replace('clock: clkDiv', 'clock: clkRef')
    fixture, _db, built = _build('connClockLocalNetMiss', DUT_CLOCKS_UNEXPORTED,
                                 INSTANCES_B, connection,
                                 expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "a connection clock: disagreeing with the declared ports it "
                "reaches built successfully; expected an agreement diagnostic")
        report = built.stdout + built.stderr
        if "bound to 'clkDiv', but connection" not in report or "must agree" not in report:
            raise AssertionError(f"the rejection does not report the expected diagnostic:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


# ------------------------------------ Fixture C: reserved-name collision --

def check_local_net_collides_with_reserved_name():
    """dut declares no clk/rst_n of its own, so both names are reserved
    aliases onto its default clock (clkRef) and selected reset (rstRef_n).
    Binding the divider's rstDiv_n output onto the literal name 'rst_n'
    collides with that reservation - a local net's name may not collide
    with the container's own clocks, resets, ports, memories, or the
    reserved clk/rst_n names."""
    instances = INSTANCES_A.replace('rstDiv_n: rstDivInt_n', 'rstDiv_n: rst_n')
    fixture, _db, built = _build('localNetCollision', DUT_CLOCKS_EXPORTED,
                                 instances, CONNECTIONS_A, expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "a local net named 'rst_n' built successfully; expected a "
                "collision with dut's reserved rst_n alias")
        report = built.stdout + built.stderr
        for needle in ("binds output reset 'rstDiv_n' to 'rst_n'",
                       "already uses that name for its implicit reset",
                       "a local net's name may not collide"):
            if needle not in report:
                raise AssertionError(f"the rejection does not mention {needle!r}:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


# ---------------------- Fixture D: self-driven input, reset membership --

def check_rejects_self_driven_input():
    """uDivider binds its own INPUT clkRef onto 'clkDiv', the net its
    own OUTPUT clkDiv already drives - a combinational loop through the
    child, rejected regardless of the net's name matching by coincidence."""
    instances = INSTANCES_A.replace(
        'clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ }',
        'clocks: { clkRef: clkDiv, clkDiv: clkDiv, clkDivBy2: ~ }')
    fixture, _db, built = _build('selfDriven', DUT_CLOCKS_EXPORTED,
                                 instances, CONNECTIONS_A, expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "uDivider binding its own input to a net its own output "
                "drives built successfully; expected a self-driven input diagnostic")
        report = built.stdout + built.stderr
        if 'An instance may not bind one of its own inputs to a net' not in report:
            raise AssertionError(f"the rejection does not report the expected diagnostic:\n{report}")
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

INSTANCES_EXPORT_RESET_MISMATCH = """    top_tb:    { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:     { container: top_tb, instanceType: dut, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: ~ }, resets: { rstRef_n: rstRef_n, rstDiv_n: ~ } }
    uDivider:  { container: dut, instanceType: divider, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ },
                 resets: { rstRef_n: rstRef_n, rstDiv_n: rstDiv_n } }
"""


def check_rejects_export_clock_mismatch():
    """The export case: dut declares rstDiv_n's own clock as clkRef, but
    uDivider's rstDiv_n actually belongs to clkDiv (mapped through its own
    instance) - the supplier's own reset domain must agree with what the
    container's declaration claims for the net it exports onto."""
    fixture, _db, built = _build('exportMismatch', DUT_CLOCKS_EXPORT_RESET,
                                 INSTANCES_EXPORT_RESET_MISMATCH, expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "exporting a reset to a declared output whose stated clock "
                "disagrees with the supplier's own built successfully; "
                "expected a reset clock-membership diagnostic")
        report = built.stdout + built.stderr
        if 'An exported reset must be released on the clock' not in report:
            raise AssertionError(f"the rejection does not report the expected diagnostic:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


INSTANCES_LOCAL_RESET_MISMATCH = """    top_tb:    { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:     { container: top_tb, instanceType: dut, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: ~ }, resets: { rstRef_n: rstRef_n } }
    uDivider:  { container: dut, instanceType: divider, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ },
                 resets: { rstRef_n: rstRef_n, rstDiv_n: rstDivInt_n } }
    uConsumer: { container: dut, instanceType: consumer, instGroup: top,
                 clocks: { clk: clkRef }, resets: { rst_n: rstDivInt_n } }
"""


def check_rejects_local_net_membership_mismatch():
    """The local-net case: uConsumer's own clock (clk) is bound to
    clkRef, but its reset (rst_n) is bound to rstDivInt_n, a local net
    released on clkDiv instead - the two must agree."""
    fixture, _db, built = _build('localMismatch', DUT_CLOCKS_EXPORTED,
                                 INSTANCES_LOCAL_RESET_MISMATCH, expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "a reset bound to a local net released on a different clock "
                "than the consumer's own clock built successfully; expected "
                "a reset clock-membership diagnostic")
        report = built.stdout + built.stderr
        if 'A synchronous reset must be released on the container clock' not in report:
            raise AssertionError(f"the rejection does not report the expected diagnostic:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


INSTANCES_LOCAL_RST_FALLBACK = """    top_tb:    { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:     { container: top_tb, instanceType: dut, instGroup: top,
                 clocks: { clkRef: clkRef }, resets: { rstRef_n: rstRef_n } }
    uDivider:  { container: dut, instanceType: divider, instGroup: top,
                 clocks: { clkRef: clkRef, clkDiv: clkDiv, clkDivBy2: ~ },
                 resets: { rstRef_n: rstRef_n, rstDiv_n: rstDivInt_n } }
    uPlain:    { container: dut, instanceType: plain, instGroup: top,
                 clocks: { clk: clkDiv } }
"""


def check_rst_fallback_resolves_local_reset():
    """Positive: uPlain declares nothing (implicit clk/rst_n);
    its clk maps to the local clock net clkDiv, and rst_n is left unmapped.
    The sole local reset net on clkDiv (rstDivInt_n) is its selected reset
    so the automatic rst_n fallback must resolve to it rather
    than reject for lack of a declared candidate."""
    fixture, db, built = _build('localFallback', DUT_CLOCKS_UNEXPORTED,
                                INSTANCES_LOCAL_RST_FALLBACK)
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


RSYNC_PREAMBLE = PREAMBLE + """    rsync:
        desc: "reset synchroniser: an asynchronous reset in, a reset on clk out"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clk: {{ }}
        resets:
            rstIn_n:  {{ async: true }}
            rstOut_n: {{ clock: clk, direction: output }}
"""

DUT_CLOCKS_ASYNC_ONLY = """        clocks:
            clkRef: { default: true }
        resets:
            rstAsync_n: { async: true }
"""

INSTANCES_LOCAL_DEFAULT_RESET = """    top_tb:  { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:   { container: top_tb, instanceType: dut, instGroup: top,
               clocks: { clkRef: clkRef }, resets: { rstAsync_n: rstRef_n } }
    uSync:   { container: dut, instanceType: rsync, instGroup: top,
               clocks: { clk: clkRef }, resets: { rstIn_n: rstAsync_n, rstOut_n: rstSyncd_n } }
    uPlain:  { container: dut, instanceType: plain, instGroup: top,
               clocks: { clk: clkRef }, resets: { rst_n: rstSyncd_n } }
"""


def check_local_net_wire_precedes_alias_reading_it():
    """dut's only reset on its default clock is the local net rstSyncd_n,
    so its rst_n alias reads that net; the net's wire must be declared
    before the alias line that reads it."""
    fixture, db, _built = _build('localDefaultReset', DUT_CLOCKS_ASYNC_ONLY,
                                 INSTANCES_LOCAL_DEFAULT_RESET, preamble=RSYNC_PREAMBLE)
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
        wire = text.find('wire rstSyncd_n;')
        alias = text.find('wire rst_n = rstSyncd_n;')
        if wire < 0 or alias < 0 or wire > alias:
            raise AssertionError(
                f"dut.sv does not declare 'wire rstSyncd_n;' before the alias "
                f"'wire rst_n = rstSyncd_n;' that reads it:\n{text}")
    finally:
        shutil.rmtree(fixture)
    return True


# ------------------------------- Fixture E: boundary port, supply graph --

INSTANCES_UNEXPORTED_BOUNDARY = """    top_tb:       { container: top_tb, instanceType: top_tb, instGroup: top }
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

CONNECTION_UNEXPORTED_BOUNDARY = (
    "    - { interface: dataIf, src: uOuterProducer, srcport: out, dst: u_dut, "
    "name: toConsumer }\n"
)

CONNECTION_MAPS_UNEXPORTED_BOUNDARY = (
    "    - { interface: dataIf, block: dut, direction: dst, instance: uConsumer, "
    "name: toConsumer }\n"
)


def check_rejects_boundary_port_on_unexported_local_net():
    """dut never exports clkDiv, so uConsumer's own domain (the local
    net clkDiv) cannot back a boundary port a connectionMaps: row routes to
    it - the parent could neither drive nor name that domain."""
    fixture, _db, built = _build('localBoundary', DUT_CLOCKS_UNEXPORTED,
                                 INSTANCES_UNEXPORTED_BOUNDARY,
                                 CONNECTION_UNEXPORTED_BOUNDARY,
                                 CONNECTION_MAPS_UNEXPORTED_BOUNDARY,
                                 expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "a connectionMaps: boundary port deriving to an unexported "
                "local net built successfully; expected an unexported-local-net diagnostic")
        report = built.stdout + built.stderr
        if 'A boundary port timed by a local net the container does not export' not in report:
            raise AssertionError(f"the rejection does not report the expected diagnostic:\n{report}")
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


def check_rejects_supply_cycle():
    """Two cross-coupled dividers, each clocked by the other's output,
    with no external supply at all - the supply graph must be acyclic."""
    fixture, _db, built = _build('supplyCycle', DUT_CLOCKS_UNEXPORTED,
                                 INSTANCES_CYCLE, expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "two instances clocking each other built successfully; "
                "expected a supply-cycle diagnostic")
        report = built.stdout + built.stderr
        if 'these nets supply each other' not in report:
            raise AssertionError(f"the rejection does not report the expected diagnostic:\n{report}")
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


def check_supply_rejects_cycle_behind_a_second_input():
    """Supply-cycle determinism: uDualA/uDualB each have TWO inputs, clkA (declared
    first, bound to the real clkRef) and clkCycle (declared second, closing
    a cycle with the other instance). The edge rule feeds clkOut from EITHER
    input, so the cycle behind clkCycle must still be reported even though
    clkA alone would answer "reaches a root" - a check that evaluated inputs
    with a short-circuiting any() over a hash-ordered set could miss this
    whenever clkA happened to be visited first."""
    fixture, _db, built = _build('twoInputCycle', DUT_CLOCKS_UNEXPORTED,
                                 INSTANCES_TWO_INPUT_CYCLE, expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "a two-input supplier whose SECOND input closes a cycle built "
                "successfully; expected a supply-cycle diagnostic")
        report = built.stdout + built.stderr
        if 'these nets supply each other' not in report:
            raise AssertionError(f"the rejection does not report the expected diagnostic:\n{report}")
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


def check_supply_accepts_oscillator_as_root():
    """Positive: uOsc has no input clock or reset at all, so it is a
    root of the supply graph; a consumer running on its
    output must build clean, with no cycle or missing-root diagnostic - and
    the generated container must actually wire the oscillator's output onto
    the local net uPlain consumes, not merely build without error."""
    fixture, db, _built = _build('supplyRoot', DUT_CLOCKS_UNEXPORTED, INSTANCES_ROOT)
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


# expC exports clkOut from an inner child and has an input clock of its own;
# a sibling divider clocked by the export feeds expC's input back.
EXPORTER_PREAMBLE = PREAMBLE + """    expC:
        desc: "exports an inner child's clock as clkOut; clkIn feeds another inner child"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clkIn:  {{ default: true }}
            clkOut: {{ direction: output }}
        resets: {{}}
"""

INSTANCES_EXPORT_FEEDBACK = """    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:  { container: top_tb, instanceType: dut, instGroup: top,
              clocks: { clkRef: clkRef }, resets: { rstRef_n: rstRef_n } }
    uExp:   { container: dut, instanceType: expC, instGroup: top,
              clocks: { clkIn: clkSlow, clkOut: clkFast } }
    uDiv:   { container: dut, instanceType: osc2, instGroup: top,
              clocks: { clkIn: clkFast, clkOut: clkSlow } }
    uSink:  { container: expC, instanceType: plainNoReset, instGroup: top,
              clocks: { clk: clkIn } }
"""


def check_supply_export_fed_by_inner_oscillator_accepted():
    """Positive: expC's clkOut comes from an inner oscillator, so it does
    not depend on expC's clkIn, and the divider feeding clkIn from clkOut
    closes no cycle."""
    instances = INSTANCES_EXPORT_FEEDBACK + (
        "    uOsc:   { container: expC, instanceType: osc1, instGroup: top,\n"
        "              clocks: { clkOut: clkOut } }\n")
    fixture, _db, built = _build('exportFromOsc', DUT_CLOCKS_UNEXPORTED, instances,
                                 expect_success=False, preamble=EXPORTER_PREAMBLE)
    try:
        report = built.stdout + built.stderr
        if built.returncode != 0 or 'these nets supply each other' in report:
            raise AssertionError(
                f"an export driven by an inner oscillator was reported as "
                f"part of a supply cycle:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


def check_supply_export_fed_by_container_input_rejected():
    """Negative: expC's clkOut comes from an inner divider on expC's
    clkIn, so the divider feeding clkIn from clkOut is a cycle through the
    export."""
    instances = INSTANCES_EXPORT_FEEDBACK + (
        "    uInner: { container: expC, instanceType: osc2, instGroup: top,\n"
        "              clocks: { clkIn: clkIn, clkOut: clkOut } }\n")
    fixture, _db, built = _build('exportFromInput', DUT_CLOCKS_UNEXPORTED, instances,
                                 expect_success=False, preamble=EXPORTER_PREAMBLE)
    try:
        report = built.stdout + built.stderr
        if built.returncode == 0 or 'these nets supply each other' not in report:
            raise AssertionError(
                f"a cycle through an export driven from the container's own "
                f"input was not reported:\n{report}")
    finally:
        shutil.rmtree(fixture)
    return True


# ------------------- Fixture F: a local reset candidate for the bus clock --

# A router, a routed leaf (leafA) and a reset synchroniser, built independently
# of the PREAMBLE topology above: leafA's second clock, clkBus, hosts its
# register bus (registerPorts:'s own clock:); uSync, a
# child INSIDE leafA's own container, is the only other source of a reset on
# clkBus, driving the local net rstBusInt_n. Extending BlockDomains.
# selectedReset with local candidates (its second pass) must pick it up as a
# candidate for the register bus's own reset. uRegConsumer keeps
# rstBusInt_n consumed independently of how the synthesised handler's own
# reset resolves, so an ambiguous candidate set is reported as a missing
# bus reset, not masked by an unrelated no-consumer finding.

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
    onto 'top's own rst_n - membership still agrees, since clkBus
    itself is mapped onto 'top's own default clock below."""
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


def check_selected_reset_is_sole_local_reset_candidate():
    """Positive: leafA's register bus clock (clkBus) declares no reset
    of its own at all; the sole candidate is uSync's local output
    rstBusInt_n. The extended BlockDomains.selectedReset must pick it up,
    with no missing-reset diagnostic, and the synthesised handler's own
    reset must reach generation bound to it - its own port renamed to the
    net name, so both sides of the bind read rstBusInt_n."""
    fixture, db, built = _build_registered_leaf('soleLocalReset', LEAF_EXTRA_SOLE_LOCAL)
    try:
        report = built.stdout + built.stderr
        if 'no selected reset' in report:
            raise AssertionError(
                f"a register bus clock whose sole reset candidate is a "
                f"local net raised a missing-reset diagnostic; expected the local net to be "
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


def check_selected_reset_rejects_two_unmarked_candidates():
    """Negative: clkBus has TWO reset candidates - the declared
    rstBusDecl_n and uSync's local rstBusInt_n - and neither marks
    default: true, so the register bus's reset is ambiguous."""
    fixture, _db, built = _build_registered_leaf(
        'twoResetCandidates', LEAF_EXTRA_AMBIGUOUS,
        leaf_reset_map=', resets: { rstBusDecl_n: rst_n }', expect_success=False)
    try:
        if built.returncode == 0:
            raise AssertionError(
                "a register bus clock with two unmarked reset candidates "
                "(one declared, one local) built successfully; expected a "
                "missing bus reset diagnostic")
        report = built.stdout + built.stderr
        if 'register bus clock must have one' not in report:
            raise AssertionError(f"the rejection does not report the expected diagnostic:\n{report}")
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
        ("a connection's clock: resolves against a local net",
         check_connection_clock_resolves_against_a_local_net),
        ("a declared port's clock disagreeing with the connection's clock: is rejected",
         check_declared_port_clock_disagreeing_with_connection_clock_rejected),
        ("a local net colliding with a container's reserved rst_n is rejected",
         check_local_net_collides_with_reserved_name),
        ("an instance binding its own input to a net its own output drives is rejected",
         check_rejects_self_driven_input),
        ('an exported reset whose declared clock disagrees with the supplier is rejected',
         check_rejects_export_clock_mismatch),
        ("a reset bound to a local net whose membership disagrees with the consumer's own clock is rejected",
         check_rejects_local_net_membership_mismatch),
        ('the rst_n fallback resolves to the sole local reset net on a local clock',
         check_rst_fallback_resolves_local_reset),
        ("a local net's wire is declared before the default-domain alias that reads it",
         check_local_net_wire_precedes_alias_reading_it),
        ('a boundary port deriving to an unexported local net is rejected',
         check_rejects_boundary_port_on_unexported_local_net),
        ('a supply cycle between two cross-coupled dividers is rejected',
         check_rejects_supply_cycle),
        ('a cycle behind a two-input supplier\'s second input is rejected',
         check_supply_rejects_cycle_behind_a_second_input),
        ('a no-input-clock oscillator is accepted as a supply-graph root',
         check_supply_accepts_oscillator_as_root),
        ('an export fed by an inner oscillator closes no cycle through the container input',
         check_supply_export_fed_by_inner_oscillator_accepted),
        ("a cycle through an export fed by the container's own input is rejected",
         check_supply_export_fed_by_container_input_rejected),
        ('a register bus clock\'s sole local reset candidate is selected',
         check_selected_reset_is_sole_local_reset_candidate),
        ('a register bus clock with two unmarked reset candidates is rejected',
         check_selected_reset_rejects_two_unmarked_candidates),
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
