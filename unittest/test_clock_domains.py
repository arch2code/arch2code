#!/usr/bin/env python3
"""Coverage for per-block clock and reset declaration: a block's
clocks and resets are exactly its own clocks:/resets: entries, or the
implicit clk/rst_n, for a container as for a leaf. Nothing is inferred from
a block's children, connections or containment.

Groups: the completeness rule itself (implicit clk/rst_n, an explicitly
empty resets:); the template-facing view (getBlockData, including a port's
selected reset); the reset-clock, stated-clock and reset-membership
validation diagnostics; the single-domain rules for memories and register
buses; and project-scope name collisions, unaffected by this rule since they
are a project-file concern.

Assertions are on the persisted declaration, never on the build merely
succeeding: a build that emits nothing at all succeeds too.

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
from collections import OrderedDict

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
import pysrc.clockTree as clockTree
from pysrc.processYaml import projectOpen

import test_register_decode_clock as regdecode
from _addrctl_helpers import APB_PREAMBLE

g.disableColors = True

# Two non-commensurate clocks and one reset per domain, so a block can be placed
# in a domain that is not the default and the two stay distinguishable.
PROJECT_DOMAINS = """
clocks:
    clk:     { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    clkSlow: { desc: "a slower, non-commensurate clock", period: 3, timeUnit: ns }

resets:
    rst_n:     { desc: "the default reset", default: true, clock: clk }
    rstSlow_n: { desc: "the slow-domain reset", clock: clkSlow }
"""

PROJECT_TAIL = """
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

# One producer feeding one consumer inside a container, plus a leaf ('spare')
# that no connection touches and declares nothing, so its clock/reset are the
# implicit clk/rst_n. Every block is generation-disabled: this fixture asserts
# on the database, and scaffolding implementation files would say nothing more.
DESIGN = """types:
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
            clk:     {{ default: true }}
            clkSlow: {{ }}
        resets:
            rst_n:     {{ clock: clk }}
            rstSlow_n: {{ clock: clkSlow }}
    dut:
        desc: "container of the producer and consumer"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
{containerDomains}    prod:   {{ desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    spare:  {{ desc: "leaf no connection touches", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    cons:
        desc: "consumer"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
{consumerDomains}{extraBlocks}
instances:
    top_tb: {{ container: top_tb, instanceType: top_tb, instGroup: top }}
    u_dut:  {{ container: top_tb, instanceType: dut,    instGroup: top }}
    uProd:  {{ container: dut,    instanceType: prod,   instGroup: top }}
    uCons:  {{ container: dut,    instanceType: cons,   instGroup: top }}
    uSpare: {{ container: dut,    instanceType: spare,  instGroup: top }}
{extraInstances}
connections:
    - {{ interface: dataIf, src: uProd, srcport: out, dst: uCons, dstport: in{connectionClock} }}
{extraConnections}{extraSections}"""


def _make_fixture(consumerDomains='', connectionClock='',
                  projectDomains=PROJECT_DOMAINS, design=None,
                  extraBlocks='', extraSections='', containerDomains='',
                  extraInstances='', extraConnections=''):
    """Write a design fixture into a fresh temp dir outside the repo tree.

    `consumerDomains` is appended to the cons block and `containerDomains` to the
    dut block that contains it, to author block clocks: /
    resets: lists. `connectionClock` is appended to the one connection, to author
    its clock:. `extraBlocks`, `extraInstances` and `extraConnections` are
    appended to the blocks:, instances: and connections: sections, and
    `extraSections` to the design yaml, for shapes DESIGN's fixed block set and
    section set do not hold.
    `design` replaces the design yaml outright, for the containment shapes
    DESIGN's fixed instance tree cannot express.

    Returns (fixture_dir, project_path, db_path).
    """
    fixture = tempfile.mkdtemp(prefix='clkdomains_')
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))

    projectFiles = ['    - ../../yaml/top.yaml\n']

    if design is None:
        design = DESIGN.format(consumerDomains=consumerDomains,
                               containerDomains=containerDomains,
                               extraInstances=extraInstances,
                               connectionClock=connectionClock,
                               extraConnections=extraConnections,
                               extraBlocks=extraBlocks,
                               extraSections=extraSections)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(design)
    project_path = os.path.join(fixture, 'prj', 'yaml', 'project.yaml')
    with open(project_path, 'w') as f:
        f.write("yamlFormat: 2\n"
                "projectName: clkTest\n"
                "topInstance: top_tb\n"
                "\n"
                "projectFiles:\n"
                f"{''.join(projectFiles)}"
                f"{projectDomains}"
                "\n"
                "dirs:\n"
                "    root: ../..\n"
                f"{PROJECT_TAIL}")
    return fixture, project_path, os.path.join(fixture, 'project.db')


def _run_case(label, fn):
    try:
        ok = fn()
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    print(f"{'PASS' if ok else 'FAIL'}: {label}")
    return ok


def _build(project_path, db_path):
    """Run one database build in a subprocess. Returns (returncode, output)."""
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    completed = subprocess.run(
        [sys.executable, os.path.join(base_dir, 'arch2code.py'),
         '--yaml', project_path, '--db', db_path],
        capture_output=True, text=True, timeout=300, env=env, cwd=test_dir)
    return completed.returncode, completed.stdout + completed.stderr


def _arch2code(*args, cwd):
    """Run one arch2code.py invocation (newmodule scaffolding, or rendering
    a single file) in a subprocess. Returns the completed process."""
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run([sys.executable, os.path.join(base_dir, 'arch2code.py'), *args],
                          capture_output=True, text=True, timeout=120, cwd=cwd, env=env)


def _expect_diagnostic(label, needles, **fixtureKwargs):
    def check():
        fixture, project_path, db_path = _make_fixture(**fixtureKwargs)
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code == 0:
            raise AssertionError(f"build succeeded; it must fail.\n{output}")
        # A crash is not a diagnostic: an unguarded dict index exits non-zero too.
        if 'Traceback' in output:
            raise AssertionError(
                f"the build crashed instead of reporting a diagnostic.\n{output}")
        for needle in needles:
            if needle not in output:
                raise AssertionError(
                    f"diagnostic does not mention '{needle}', so the author is not "
                    f"pointed at what to fix.\n{output}")
        return True
    return _run_case(label, check)


def _expect_builds(label, viewCheck=None, **fixtureKwargs):
    """The fixture must build; `viewCheck(db_path)`, when given, then
    asserts on the persisted result."""
    def check():
        fixture, project_path, db_path = _make_fixture(**fixtureKwargs)
        try:
            code, output = _build(project_path, db_path)
            if code != 0:
                raise AssertionError(f"the build failed.\n{output}")
            if viewCheck is not None:
                viewCheck(db_path)
        finally:
            shutil.rmtree(fixture)
        return True
    return _run_case(label, check)


def _port_domain(db_path, blockName, portName):
    """The domainClock the template-facing view gives a block's connection
    port."""
    prj = projectOpen(db_path)
    blockKey = next(key for key, row in prj.data['blocks'].items()
                    if row['block'] == blockName)
    return prj.getBlockData(blockKey)['ports']['connections'][portName]['domainClock']


# ------------------------------------------------------------- derivation --

def _clock_reset_rows(db_path, blockName):
    """(clock names, reset names) persisted for a block, in declaration order.

    Reads blockClocksResets directly by SQL rather than through projectOpen,
    so a fixture can be checked without opening the module-global database
    state a second time (projectOpen is opened once elsewhere in this file).
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    blockKey = cur.execute(
        "SELECT blockKey FROM blocks WHERE block = ?", (blockName,)).fetchone()['blockKey']
    clocks = [row['itemKey'] for row in cur.execute(
        "SELECT itemKey FROM blockClocksResets WHERE blockKey = ? AND kind = 'clock' "
        "ORDER BY orderIndex", (blockKey,)).fetchall()]
    resets = [row['itemKey'] for row in cur.execute(
        "SELECT itemKey FROM blockClocksResets WHERE blockKey = ? AND kind = 'reset' "
        "ORDER BY orderIndex", (blockKey,)).fetchall()]
    con.close()
    return clocks, resets


def run_declaration_completeness_cases():
    """A block's clocks and resets are exactly what it declares.

    'spare' declares neither, so it gets the implicit clk/rst_n. 'cons'
    declares an explicitly empty resets: {}, which means a block with no
    reset at all, distinct from omitting resets: entirely (which is what
    gives 'spare' its implicit rst_n). A second, separate build repeats the
    empty-resets case as a list (resets: []), on a leaf again rather than on
    'dut': 'dut' is prod/cons/spare's container, and a container with no
    reset of its own leaves its children's implicit rst_n with nothing to
    fall back to - a different rule this fixture is not for."""
    fixture, project_path, db_path = _make_fixture(
        consumerDomains="        resets: {}\n")
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: the declaration-completeness fixture builds\n{output}")
            return False
        print("PASS: the declaration-completeness fixture builds")

        def undeclared_block_gets_implicit_clk_rst_n():
            clocks, resets = _clock_reset_rows(db_path, 'spare')
            if clocks != ['clk'] or resets != ['rst_n']:
                raise AssertionError(
                    f"'spare' declares no clocks:/resets: and persisted "
                    f"clocks={clocks}, resets={resets}, expected "
                    f"clocks=['clk'], resets=['rst_n']")
            return True

        def empty_mapping_resets_means_none():
            clocks, resets = _clock_reset_rows(db_path, 'cons')
            if resets:
                raise AssertionError(
                    f"'cons' declares resets: {{}} and persisted resets="
                    f"{resets}, expected none: an explicitly empty resets: "
                    f"is distinct from omitting it")
            if clocks != ['clk']:
                raise AssertionError(
                    f"'cons' declares no clocks: and persisted clocks="
                    f"{clocks}, expected ['clk']")
            return True

        results = [
            _run_case("an undeclared block gets the implicit clk/rst_n",
                      undeclared_block_gets_implicit_clk_rst_n),
            _run_case("a block declaring resets: {} has no reset at all",
                      empty_mapping_resets_means_none)]
    finally:
        shutil.rmtree(fixture)

    fixture, project_path, db_path = _make_fixture(
        consumerDomains="        resets: []\n")
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: the empty-list-resets fixture builds\n{output}")
            return False
        print("PASS: the empty-list-resets fixture builds")

        def empty_list_resets_means_none():
            clocks, resets = _clock_reset_rows(db_path, 'cons')
            if resets:
                raise AssertionError(
                    f"'cons' declares resets: [] and persisted resets="
                    f"{resets}, expected none: the empty list form means "
                    f"the same as the empty mapping form")
            return True

        results.append(_run_case(
            "a block declaring resets: [] has no reset at all",
            empty_list_resets_means_none))
        return all(results)
    finally:
        shutil.rmtree(fixture)


def run_view_build():
    """getBlockData() surfaces the block's own declared clocks/resets, in
    declaration order with period, and gives a port the SELECTED reset of
    its own clock - not the block's first declared reset on that clock when
    the block marked another one default."""
    # A custom design, not consumerDomains on DESIGN's dut-contained cons:
    # clkSlow is not clk/rst_n, so every container up to the root would have
    # to declare it too for the automatic binding to resolve (no instance
    # map exists yet). One level - top_tb containing prod and cons directly -
    # avoids that cascade.
    design = """types:
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
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:     { default: true }
            clkSlow: { }
        resets:
            rst_n:    { clock: clk, default: true }
            rstAlt_n: { clock: clk }
            rstSlow_n: { clock: clkSlow }
    prod:   { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    cons:
        desc: "consumer"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:     { default: true, period: 1, timeUnit: ns }
            clkSlow: { period: 3, timeUnit: ns }
        resets:
            rst_n:     { clock: clk }
            rstAlt_n:  { clock: clk, default: true }
            rstSlow_n: { clock: clkSlow }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd:  { container: top_tb, instanceType: prod,   instGroup: top }
    uCons:  { container: top_tb, instanceType: cons,   instGroup: top }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uCons, dstport: in }
"""
    # A dedicated projectDomains matching top_tb's own third reset
    # (rstAlt_n, on clk): PROJECT_DOMAINS declares only rst_n/rstSlow_n, and
    # every input reset of the top block must bind to something.
    projectDomains = """
clocks:
    clk:     { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    clkSlow: { desc: "a slower, non-commensurate clock", period: 3, timeUnit: ns }

resets:
    rst_n:     { desc: "the default reset", default: true, clock: clk }
    rstAlt_n:  { desc: "a second clk-domain reset", clock: clk }
    rstSlow_n: { desc: "the slow-domain reset", clock: clkSlow }
"""
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains=projectDomains)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: the view fixture builds\n{output}")
            return False
        print("PASS: the view fixture builds")
        prj = projectOpen(db_path)
        blockKey = next(key for key, row in prj.data['blocks'].items()
                        if row['block'] == 'cons')
        view = prj.getBlockData(blockKey)

        def clocks_in_declaration_order():
            names = [row['clock'] for row in view['clocks']]
            if names != ['clk', 'clkSlow']:
                raise AssertionError(
                    f"the view lists clocks {names}, expected "
                    f"['clk', 'clkSlow']: declaration order")
            if view['clocks'][1]['period'] != 3:
                raise AssertionError(
                    f"the view's clkSlow entry carries period "
                    f"{view['clocks'][1]['period']}, expected 3")
            if view['defaultClock'] != 'clk' or view['defaultReset'] != 'rstAlt_n':
                raise AssertionError(
                    f"the view's defaultClock/defaultReset are "
                    f"{view['defaultClock']!r}/{view['defaultReset']!r}, "
                    f"expected 'clk'/'rstAlt_n': clk's selected reset is the "
                    f"one marked default: true, not the first declared")
            return True

        def resets_carry_their_own_clock():
            names = [row['reset'] for row in view['resets']]
            if names != ['rst_n', 'rstAlt_n', 'rstSlow_n']:
                raise AssertionError(
                    f"the view lists resets {names}, expected "
                    f"['rst_n', 'rstAlt_n', 'rstSlow_n']")
            if view['resets'][2]['clock'] != 'clkSlow':
                raise AssertionError(
                    f"the view's rstSlow_n entry carries clock="
                    f"{view['resets'][2]['clock']!r}, expected 'clkSlow'")
            return True

        def port_takes_the_selected_reset_not_the_first_declared():
            # 'in' is reached by the default (unstated-clock) connection, so
            # its domain is the block default clock, clk. clk's selected
            # reset is rstAlt_n (marked default: true), not rst_n, which is
            # merely declared first.
            port = view['ports']['connections']['in']
            if port['domainClock'] != 'clk' or port['domainReset'] != 'rstAlt_n':
                raise AssertionError(
                    f"'in' reports domainClock/domainReset "
                    f"{port['domainClock']!r}/{port['domainReset']!r}, "
                    f"expected 'clk'/'rstAlt_n'")
            return True

        return all([
            _run_case("getBlockData lists the block's clocks in declaration "
                      "order and reports the default clock/reset",
                      clocks_in_declaration_order),
            _run_case("getBlockData lists the block's resets with their own "
                      "clock", resets_carry_their_own_clock),
            _run_case("a port takes the selected reset of its clock, not the "
                      "first declared", port_takes_the_selected_reset_not_the_first_declared)])
    finally:
        shutil.rmtree(fixture)


def run_default_clock_port_resolution_cases():
    """A declared port naming no clock: resolves to the block DEFAULT
    clock - not the block's first declared clock, which carries no domain
    meaning of its own. 'leaf' declares clkSlow before clk, with clk marked
    default, so an emitter reading the first entry would answer clkSlow."""
    design = """types:
    dataT: { width: 8, desc: "payload word" }

structures:
    dataSt:
        data: { varType: dataT, desc: "payload word" }

interfaces:
    dataIf:
        desc: "leaf register bus"
        interfaceType: push_ack
        structures:
            - { structure: dataSt, structureType: data_t }

blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    leaf:
        desc: "declares clkSlow before the default clock clk, with a declared port naming neither"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkSlow: { }
            clk:     { default: true }
        ports:
            regs: { interface: dataIf, direction: dst }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
"""
    # projectDomains='': 'leaf' is never instantiated (a zero-instance
    # library leaf, so the default-clock rule is checked apart from any
    # binding) and top_tb declares nothing of its own, so the default single
    # implicit clk/rst_n is all the testbench needs to bind - PROJECT_DOMAINS' extra clkSlow
    # would have nothing in this design to consume it.
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains='')
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: the default-clock-port fixture builds\n{output}")
            return False
        print("PASS: the default-clock-port fixture builds")
        prj = projectOpen(db_path)
        blockKey = next(key for key, row in prj.data['blocks'].items()
                        if row['block'] == 'leaf')
        view = prj.getBlockData(blockKey)
        domain = view['ports']['connections']['regs']['domainClock']
        if domain != 'clk':
            raise AssertionError(
                f"'regs' reports domainClock {domain!r}, expected 'clk': "
                f"unstated means the block DEFAULT clock, not the "
                f"first declared (clkSlow)")
        return _run_case(
            "a declared port naming no clock resolves to the block default, "
            "not its first declared clock", lambda: True)
    finally:
        shutil.rmtree(fixture)


def run_declared_port_connection_clock_mismatch_rejected():
    """A declared port's clock: (its own, or the block default when it names
    none) and a connection reaching it are not read as a precedence; where
    both are present they must agree. Checked in projectCreate, against the
    container binding clockTree.build() computed, so a disagreeing design
    fails the database build, not just a later view render."""
    design = """types:
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
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:     { default: true }
            clkSlow: { }
        resets:
            rst_n:     { clock: clk }
            rstSlow_n: { clock: clkSlow }
    prod: { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    cons:
        desc: "consumer; declares 'in' on clkSlow explicitly"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:     { default: true }
            clkSlow: { }
        resets:
            rst_n:     { clock: clk }
            rstSlow_n: { clock: clkSlow }
        ports:
            in: { interface: dataIf, direction: dst, clock: clkSlow }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd:  { container: top_tb, instanceType: prod,   instGroup: top }
    uCons:  { container: top_tb, instanceType: cons,   instGroup: top }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uCons, dstport: in, clock: clk }
"""
    return _expect_diagnostic(
        "a declared port's clock: disagreeing with the reaching "
        "connection's clock: is rejected",
        ["its connection's clock: must agree"], design=design)


# 'dut' bridges boundary ports apbReg and apbReg2 inward by connectionMaps:
# apbReg to 'uInner.regs', declared on apbClk; apbReg2 to 'uInner2.regs2', a
# top-down port on inner2's own default clock, renamed onto apbClk by uInner2's
# instance map. `{dutPorts}` holds dut's ports: section, `{connClock}` is
# appended to the connection reaching apbReg, and `{prodMap}` to uProd.
BOUNDARY_DESIGN = """types:
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
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
    prod: { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container bridging two boundary ports inward"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
{dutPorts}    inner:
        desc: "inner instance: its own declared port names clock: apbClk explicitly"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
        ports:
            regs: { interface: dataIf, direction: dst, clock: apbClk }
    inner2:
        desc: "inner2 instance: a TOP-DOWN port (regs2), declared nowhere on this block, so it takes the block's own default clkTick - renamed onto dut's apbClk by uInner2's own instance map"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkTick: { default: true }
        resets:
            rstTick_n: { clock: clkTick }

instances:
    top_tb:  { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd:   { container: top_tb, instanceType: prod,   instGroup: top{prodMap} }
    uProd2:  { container: top_tb, instanceType: prod,   instGroup: top }
    uDut:    { container: top_tb, instanceType: dut,    instGroup: top }
    uInner:  { container: dut,    instanceType: inner,  instGroup: top }
    uInner2: { container: dut,    instanceType: inner2, instGroup: top,
              clocks: { clkTick: apbClk }, resets: { rstTick_n: apbRst_n } }

connections:
    - { interface: dataIf, src: uProd,  srcport: out, dst: uDut, dstport: apbReg{connClock} }
    - { interface: dataIf, src: uProd2, srcport: out, dst: uDut, dstport: apbReg2 }

connectionMaps:
    - { interface: dataIf, block: dut, direction: dst, instance: uInner,  port: apbReg,  instancePort: regs }
    - { interface: dataIf, block: dut, direction: dst, instance: uInner2, port: apbReg2, instancePort: regs2 }
"""

# The testbench clocks BOUNDARY_DESIGN's top_tb names.
BOUNDARY_PROJECT_DOMAINS = """
clocks:
    clk:    { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    apbClk: { desc: "the register-bus clock", period: 3, timeUnit: ns }

resets:
    rst_n:    { desc: "the default reset", default: true, clock: clk }
    apbRst_n: { desc: "the register-bus reset", clock: apbClk }
"""


def _boundary_design(dutPorts='', connClock='', prodMap=''):
    return (BOUNDARY_DESIGN.replace('{dutPorts}', dutPorts)
            .replace('{connClock}', connClock).replace('{prodMap}', prodMap))


def run_connectionmaps_boundary_derives_inside_out():
    """A connectionMaps: boundary port
    derives its domain inside-out from the inner port it routes to, not from
    the block default an unstated outer connection would otherwise give it.
    'dut' declares clk (default) and apbClk; its 'apbReg' boundary port is
    not in its ports: and is reached by an outer connection naming no clock:
    (the block default would give it clk), but connectionMaps: bridges it
    inward to 'uInner', whose own declared port 'regs' names clock: apbClk
    explicitly - so the boundary port's derived domain must be apbClk, not
    clk. The fact is computed once in projectCreate and persisted (the
    non-schema portDomains table); getBlockData()'s view reads it back
    rather than re-deriving it, so this is checked through getBDPortDomain,
    after open.

    A second boundary port ('apbReg2', bridged to 'uInner2') covers a
    TOP-DOWN inner port: 'inner2' declares no ports:/registerPorts: at all
    for 'regs2', so it takes its own block's default clock (clkTick, not
    dut's), renamed onto dut's apbClk by uInner2's own instance map (the
    uSlowTick shape, examples/twoClk/yaml/twoClk.yaml: a reusable IP's own
    clock renamed at its assembler). Falling back to dut's OUTER default
    clock (clk) whenever the inner port declares nothing would be silently
    wrong for exactly this renamed case."""
    fixture, project_path, db_path = _make_fixture(
        design=_boundary_design(), projectDomains=BOUNDARY_PROJECT_DOMAINS)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: the connectionMaps boundary fixture builds\n{output}")
            return False
        print("PASS: the connectionMaps boundary fixture builds")
        prj = projectOpen(db_path)
        dutKey = next(key for key, row in prj.data['blocks'].items()
                     if row['block'] == 'dut')
        view = prj.getBlockData(dutKey)
        domain = view['ports']['connections']['apbReg']['domainClock']
        if domain != 'apbClk':
            raise AssertionError(
                f"'apbReg' reports domainClock {domain!r}, expected 'apbClk': "
                f"a connectionMaps: boundary port derives inside-out from the "
                f"inner port it routes to, not from the block default "
                f"an unstated outer connection would otherwise give it")
        domain2 = view['ports']['connections']['apbReg2']['domainClock']
        if domain2 != 'apbClk':
            raise AssertionError(
                f"'apbReg2' reports domainClock {domain2!r}, expected 'apbClk': "
                f"a TOP-DOWN inner port (declared nowhere) takes its own "
                f"block's default clock, mapped outward through its "
                f"instance's own rename, not dut's own default clock")
        # The SAME connectionMaps: row, read from the ROUTED-TO block's own
        # self-render (getBlockData(innerKey), where ret['instances'] is
        # every instance OF 'inner' itself, not dut's children): getBDPorts'
        # connectionMapPorts-sourced view keys this port by instancePortName
        # ('regs'), not the boundary's own port: name ('apbReg' - `port:`
        # and `instancePort:` differ on this very row). getBDPortDomain's
        # own connectionMaps gate must still find the row's boundary domain
        # here, not fall through to the block default, by reading the
        # matching ret['connectionMaps'] entry's own parentPortName rather
        # than comparing the instancePortName argument against it directly.
        innerKey = next(key for key, row in prj.data['blocks'].items()
                       if row['block'] == 'inner')
        innerView = prj.getBlockData(innerKey)
        innerDomain = innerView['ports']['connectionMaps']['regs']['domainClock']
        if innerDomain != 'apbClk':
            raise AssertionError(
                f"'regs' (instancePort:, differing from the row's own port: "
                f"'apbReg'), read from inner's own self-render, reports "
                f"domainClock {innerDomain!r}, expected 'apbClk'")
        return _run_case(
            "a connectionMaps: boundary port derives its domain inside-out "
            "from the inner port it routes to, declared or top-down", lambda: True)
    finally:
        shutil.rmtree(fixture)


def run_boundary_port_clock_agreement_cases():
    """'apbReg' is bridged to 'uInner.regs', which runs on dut's apbClk. When
    dut declares 'apbReg' in ports:, its own clock (its clock:, else the
    block default clk) must be apbClk. When dut does not declare it, a
    connection clock: reaching it must name the parent clock dut's apbClk is
    bound to."""
    def onApbClk(db_path):
        domain = _port_domain(db_path, 'dut', 'apbReg')
        if domain != 'apbClk':
            raise AssertionError(f"'apbReg' reports domainClock {domain!r}, expected 'apbClk'")

    declared = ("        ports:\n"
                "            apbReg: {{ interface: dataIf, direction: dst{clock} }}\n")
    return all([
        _expect_builds(
            "a declared boundary port whose clock: is its inner port's clock builds",
            onApbClk,
            design=_boundary_design(dutPorts=declared.format(clock=', clock: apbClk')),
            projectDomains=BOUNDARY_PROJECT_DOMAINS),
        _expect_diagnostic(
            "a declared boundary port on the block default, bridged to an "
            "inner port on another clock, is rejected",
            ("Port 'apbReg' of block 'dut'", "declared on clock 'clk'",
             "inner port 'uInner.regs'", "runs on 'apbClk'",
             "declare clock: apbClk on port 'apbReg'",
             "bind 'apbClk' of instance 'uInner' to 'clk' in its clocks: map"),
            design=_boundary_design(dutPorts=declared.format(clock='')),
            projectDomains=BOUNDARY_PROJECT_DOMAINS),
        _expect_builds(
            "an undeclared boundary port reached by a connection clock: "
            "matching its derived clock builds",
            onApbClk,
            design=_boundary_design(connClock=', clock: apbClk',
                                    prodMap=', clocks: { clk: apbClk }, resets: { rst_n: apbRst_n }'),
            projectDomains=BOUNDARY_PROJECT_DOMAINS),
        _expect_diagnostic(
            "an undeclared boundary port reached by a connection clock: "
            "other than its derived clock is rejected",
            ("Port 'apbReg' of block 'dut' (instance 'uDut')",
             "is a connectionMaps: boundary port on clock 'apbClk'",
             "inner port 'uInner.regs'", "bound to 'apbClk'",
             "names clock: 'clk' instead",
             "bind 'apbClk' of instance 'uDut' to 'clk' in its clocks: map",
             "change the connection's clock: to 'apbClk'"),
            design=_boundary_design(connClock=', clock: clk'),
            projectDomains=BOUNDARY_PROJECT_DOMAINS),
    ])


# A three-level chain of connectionMaps: wrap's 'r' is bridged to uMid.q, and
# mid's 'q' to uLeaf.p, which leaf declares on clkB, not its default clkA.
# uMid binds clkA to c1 and clkB to c2, so both 'q' and 'r' are on clkB's
# side of each binding: 'q' on clkB, 'r' on c2. `{wrapPorts}` holds wrap's
# ports: section and `{connClock}` is appended to the connection reaching 'r'.
CHAINED_BOUNDARY_DESIGN = """types:
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
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
    prod: { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    wrap:
        desc: "outer container bridging r to its child mid"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            c1: { default: true }
            c2: { }
        resets:
            rc1_n: { clock: c1 }
            rc2_n: { clock: c2 }
{wrapPorts}    mid:
        desc: "middle container bridging q to its child leaf"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkA: { default: true }
            clkB: { }
        resets:
            rA_n: { clock: clkA }
            rB_n: { clock: clkB }
    leaf:
        desc: "leaf declaring p on its second clock"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkA: { default: true }
            clkB: { }
        resets:
            rA_n: { clock: clkA }
            rB_n: { clock: clkB }
        ports:
            p: { interface: dataIf, direction: dst, clock: clkB }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd:  { container: top_tb, instanceType: prod,   instGroup: top{prodMap} }
    uWrap:  { container: top_tb, instanceType: wrap,   instGroup: top,
              clocks: { c1: clk, c2: apbClk }, resets: { rc1_n: rst_n, rc2_n: apbRst_n } }
    uMid:   { container: wrap,   instanceType: mid,    instGroup: top,
              clocks: { clkA: c1, clkB: c2 }, resets: { rA_n: rc1_n, rB_n: rc2_n } }
    uLeaf:  { container: mid,    instanceType: leaf,   instGroup: top }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uWrap, dstport: r{connClock} }

connectionMaps:
    - { interface: dataIf, block: wrap, direction: dst, instance: uMid,  port: r, instancePort: q }
    - { interface: dataIf, block: mid,  direction: dst, instance: uLeaf, port: q, instancePort: p }
"""


def _chained_boundary_design(wrapPorts='', connClock='', prodMap=''):
    return (CHAINED_BOUNDARY_DESIGN.replace('{wrapPorts}', wrapPorts)
            .replace('{connClock}', connClock).replace('{prodMap}', prodMap))


def run_chained_boundary_port_cases():
    """Maps chain upward: 'r' takes the derived clock of 'q', the inner
    boundary port it is bridged to, not mid's default clock. wrap's map is
    listed first, so the chain resolves its inner port regardless of
    declaration order."""
    def onC2(db_path):
        domain = _port_domain(db_path, 'wrap', 'r')
        if domain != 'c2':
            raise AssertionError(f"'r' reports domainClock {domain!r}, expected 'c2'")

    declared = ("        ports:\n"
                "            r: {{ interface: dataIf, direction: dst{clock} }}\n")
    apbProd = ', clocks: { clk: apbClk }, resets: { rst_n: apbRst_n }'
    return all([
        _expect_builds(
            "an undeclared chained boundary port derives through the inner "
            "boundary port's own derived clock",
            onC2, design=_chained_boundary_design(),
            projectDomains=BOUNDARY_PROJECT_DOMAINS),
        _expect_builds(
            "a chained boundary port declared on its derived clock builds",
            onC2, design=_chained_boundary_design(wrapPorts=declared.format(clock=', clock: c2')),
            projectDomains=BOUNDARY_PROJECT_DOMAINS),
        _expect_builds(
            "a chained boundary port reached by a connection clock: naming the "
            "net its derived clock is bound to builds",
            onC2, design=_chained_boundary_design(connClock=', clock: apbClk', prodMap=apbProd),
            projectDomains=BOUNDARY_PROJECT_DOMAINS),
        _expect_diagnostic(
            "a chained boundary port declared on another clock is rejected "
            "with the derived clock",
            ("Port 'r' of block 'wrap'", "declared on clock 'c1'",
             "inner port 'uMid.q'", "runs on 'c2'",
             "set clock: c2 on port 'r'",
             "bind 'clkB' of instance 'uMid' to 'c1' in its clocks: map"),
            design=_chained_boundary_design(wrapPorts=declared.format(clock=', clock: c1')),
            projectDomains=BOUNDARY_PROJECT_DOMAINS),
    ])


# wrap bridges 'txW' to uGen.tx. gen declares tx on `{genTxClock}`; its output
# clock clkO is bound by uGen to `{genBind}`. uWrap exports clkW onto top_tb's
# local net clkT, which uMon consumes; uSink stays on top_tb's clk.
# `{wrapPorts}` holds wrap's ports: section, and the one connection reaches
# `{dst}` with `{connClock}` appended.
OUTPUT_CLOCK_BOUNDARY_DESIGN = """types:
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
    gen:
        desc: "clock generator with a port of its own"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:  { default: true }
            clkO: { direction: output }
        ports:
            tx: { interface: dataIf, direction: src, clock: {genTxClock} }
    wrap:
        desc: "container exporting its child's output clock"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:   { default: true }
            clkW:  { direction: output }
            clkW2: { direction: output }
{wrapPorts}    sink: { desc: "consumer on the default clock", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    mon:
        desc: "consumer on the exported clock"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        resets: { }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uWrap:  { container: top_tb, instanceType: wrap, instGroup: top, clocks: { clkW: clkT, clkW2: ~ } }
    uSink:  { container: top_tb, instanceType: sink, instGroup: top }
    uMon:   { container: top_tb, instanceType: mon,  instGroup: top, clocks: { clk: clkT } }
    uGen:   { container: wrap,   instanceType: gen,  instGroup: top, clocks: { clkO: {genBind} } }

connections:
    - { interface: dataIf, src: uWrap, srcport: txW, dst: {dst}, dstport: in{connClock} }

connectionMaps:
    - { interface: dataIf, block: wrap, direction: src, instance: uGen, port: txW, instancePort: tx }
"""


def _output_clock_boundary_design(genTxClock='clkO', genBind='clkW', wrapPorts='',
                                  dst='uMon', connClock=''):
    return (OUTPUT_CLOCK_BOUNDARY_DESIGN.replace('{genTxClock}', genTxClock)
            .replace('{genBind}', genBind).replace('{wrapPorts}', wrapPorts)
            .replace('{dst}', dst).replace('{connClock}', connClock))


def run_output_clock_boundary_port_cases():
    """A boundary port bridged to an inner port on an inner OUTPUT clock
    derives to the net that output drives, and is checked like any other:
    against a connection clock: reaching it, and against its own declared
    clock."""
    def onClkW(db_path):
        domain = _port_domain(db_path, 'wrap', 'txW')
        if domain != 'clkW':
            raise AssertionError(f"'txW' reports domainClock {domain!r}, expected 'clkW'")

    declared = ("        ports:\n"
                "            txW: {{ interface: dataIf, direction: src{clock} }}\n")
    return all([
        _expect_builds(
            "a boundary port on an inner output clock, reached by a connection "
            "clock: naming the net it drives, builds",
            onClkW, design=_output_clock_boundary_design(connClock=', clock: clkT'),
            projectDomains=''),
        _expect_diagnostic(
            "a boundary port on an inner output clock, reached by another "
            "connection clock:, is rejected",
            ("Port 'txW' of block 'wrap' (instance 'uWrap')",
             "is a connectionMaps: boundary port on clock 'clkW'",
             "inner port 'uGen.tx'", "bound to 'clkT'", "names clock: 'clk' instead",
             "Change the connection's clock: to 'clkT'."),
            design=_output_clock_boundary_design(dst='uSink', connClock=', clock: clk'),
            projectDomains=''),
        _expect_builds(
            "a boundary port declared on the output clock its inner port "
            "drives builds",
            onClkW, design=_output_clock_boundary_design(
                wrapPorts=declared.format(clock=', clock: clkW')),
            projectDomains=''),
        _expect_diagnostic(
            "a boundary port declared on the block default, bridged to an "
            "inner port on an output clock, is rejected without a bind fix onto "
            "an input clock",
            ("Port 'txW' of block 'wrap'", "declared on clock 'clk'",
             "runs on 'clkW'", "Declare clock: clkW on port 'txW'."),
            design=_output_clock_boundary_design(wrapPorts=declared.format(clock='')),
            projectDomains=''),
        _expect_diagnostic(
            "a boundary port declared on another output clock offers to "
            "rebind the inner output clock onto it",
            ("declared on clock 'clkW2'", "runs on 'clkW'",
             "Either set clock: clkW on port 'txW' or bind 'clkO' of instance "
             "'uGen' to 'clkW2' in its clocks: map."),
            design=_output_clock_boundary_design(
                wrapPorts=declared.format(clock=', clock: clkW2')),
            projectDomains=''),
        _expect_builds(
            "rebinding the inner output clock onto the declared clock builds",
            design=_output_clock_boundary_design(
                genBind='clkW2', wrapPorts=declared.format(clock=', clock: clkW2')),
            projectDomains=''),
        _expect_diagnostic(
            "a boundary port declared on an output clock its inner port's "
            "instance drives offers no bind fix onto it",
            ("declared on clock 'clkW'", "runs on 'clk'",
             "Set clock: clk on port 'txW'."),
            design=_output_clock_boundary_design(
                genTxClock='clk', wrapPorts=declared.format(clock=', clock: clkW')),
            projectDomains=''),
        _expect_diagnostic(
            "a boundary port on an inner output clock bound to `~` is rejected",
            ("Boundary port 'txW' of block 'wrap'", "inner port 'uGen.tx'",
             "output clock 'clkO' of block 'gen'", "binds 'clkO' to `~`"),
            design=_output_clock_boundary_design(genBind='~'),
            projectDomains=''),
    ])


def run_boundary_port_on_clockless_inner_port_rejected():
    """gen has no input clock, so its undeclared port tx has no clock and a
    boundary port bridged to it has no domain."""
    design = (_output_clock_boundary_design()
              .replace("            clk:  { default: true }\n            clkO:",
                       "            clkO:")
              .replace("        ports:\n            tx: { interface: dataIf, direction: src, clock: clkO }\n",
                       "        resets: { }\n"))
    return _expect_diagnostic(
        "a boundary port bridged to an inner port with no clock is rejected",
        ("Boundary port 'txW' of block 'wrap'", "inner port 'uGen.tx'",
         "which has no clock", "every clock it declares is direction: output",
         "Declare port 'tx' on block 'gen' with a clock:."),
        design=design, projectDomains='')

# --------------------------------------------------------- derived tables --

def _grouped_table(cur, table, groupKey, orderBy=None):
    """A table's rows grouped by groupKey, in the given ORDER BY - the same
    shape projectOpen._loadDerivedTables() builds, computed independently by
    direct SQL so the loader's output can be checked against it."""
    sql = f"SELECT * FROM {table}"
    if orderBy:
        sql += f" ORDER BY {orderBy}"
    cur.execute(sql)
    grouped = {}
    for row in cur.fetchall():
        grouped.setdefault(row[groupKey], []).append(dict(row))
    return grouped


def run_derived_tables_loader_cases():
    """projectOpen._loadDerivedTables() loads the four non-schema tables
    persisted by projectCreate into self.data, grouped by the column each
    getBD* helper keys on, in place of a per-key SELECT. A fixture with a
    container (blockClocksResets, instanceClockResetBinds across more than
    one block/instance), a memory (memoryClocks) and a parameterizable
    block whose only consumer is a module-local structure (blockParameterizedDecls)
    exercises all four with more than one row, so a grouping-key mistake
    would show up as a mismatch rather than a vacuous empty-dict comparison.
    """
    design = """ipParameters:
    constants:
        SHARED_WIDTH: { value: 8, maxValue: 16, desc: "shared exposed param" }
    types:
        sharedDataT:
            width: SHARED_WIDTH
            maxBitwidth: 16
            desc: "parameterizable type referenced only by hand-written code"

constants:
    TBL_WORDS: { value: 4, desc: "memory word count" }

types:
    dataT: { width: 8, desc: "payload word" }
    memAddrT: { width: 3, desc: "memory address" }

structures:
    dataSt:
        data: { varType: dataT, desc: "payload word" }
    memAddrSt:
        address: { varType: memAddrT, generator: address, desc: "memory address" }
    memSt:
        data: { varType: dataT, generator: memory, desc: "memory payload" }
    sharedDataSt:
        payload: { varType: sharedDataT }

interfaces:
    dataIf:
        desc: "producer to consumer stream"
        interfaceType: push_ack
        structures:
            - { structure: dataSt, structureType: data_t }

blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container of the producer and consumer"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { default: true, period: 1, timeUnit: ns }
        resets:
            rst_n: { clock: clk, default: true }
    prod: { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    cons:
        desc: "consumer, holds a memory and the sole consumer of the parameterizable decl set"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        params: [SHARED_WIDTH]

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:  { container: top_tb, instanceType: dut,    instGroup: top }
    uProd:  { container: dut,    instanceType: prod,   instGroup: top }
    uCons:  { container: dut,    instanceType: cons,   instGroup: top, variant: v0 }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uCons, dstport: in }

memories:
    - { memory: tbl, block: cons, structure: memSt, addressStruct: memAddrSt, wordLines: TBL_WORDS, ports: [p], desc: "consumer table" }

parameters:
    cons:
        v0:
            SHARED_WIDTH: 12
"""
    # projectDomains='': top_tb declares nothing of its own (implicit
    # clk/rst_n only); PROJECT_DOMAINS' extra clkSlow would have nothing in
    # this design to consume it.
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains='')
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: the derived-tables fixture builds\n{output}")
            return False
        print("PASS: the derived-tables fixture builds")

        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        expected = {
            'blockClocksResets': _grouped_table(cur, 'blockClocksResets', 'blockKey', 'kind, orderIndex'),
            'instanceClockResetBinds': _grouped_table(cur, 'instanceClockResetBinds', 'instanceKey', 'orderIndex'),
            'memoryClocks': _grouped_table(cur, 'memoryClocks', 'memoryBlockKey'),
            'blockParameterizedDecls': _grouped_table(cur, 'blockParameterizedDecls', 'blockKey', 'orderIndex'),
        }
        con.close()

        def nonTrivialFixture():
            if len(expected['blockClocksResets']) < 2:
                raise AssertionError(
                    f"fixture has only {len(expected['blockClocksResets'])} "
                    f"block(s) with clocks/resets, expected several, so a "
                    f"grouping mistake could pass unnoticed")
            if not expected['instanceClockResetBinds']:
                raise AssertionError("fixture has no instance clock/reset binds")
            if not expected['memoryClocks']:
                raise AssertionError("fixture has no memory clock rows")
            if not expected['blockParameterizedDecls']:
                raise AssertionError("fixture has no parameterized decl rows")
            return True

        def helpersMatchPerKeySelect():
            """Each of the four getBD* helpers' OWN output, for one concrete
            key the fixture provides, against an independent per-key `SELECT
            ... WHERE key = ? ORDER BY ...` - the query shape each helper ran
            directly before the loader existed - rather than the loader's own
            groupby-everything algorithm repeated (which `expected` above is,
            so a mistake in that shared grouping logic could pass unnoticed
            against it)."""
            con = sqlite3.connect(db_path)
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            consBlockKey = cur.execute(
                "SELECT blockKey FROM blocks WHERE block = 'cons'").fetchone()['blockKey']
            consInstanceKey = cur.execute(
                "SELECT instanceKey FROM instances WHERE instance = 'uCons'").fetchone()['instanceKey']
            memoryBlockKey = cur.execute(
                "SELECT memoryBlockKey FROM memories WHERE memory = 'tbl'").fetchone()['memoryBlockKey']

            clocksResetsRows = [dict(row) for row in cur.execute(
                "SELECT * FROM blockClocksResets WHERE blockKey = ? ORDER BY kind, orderIndex",
                (consBlockKey,)).fetchall()]
            bindRows = [dict(row) for row in cur.execute(
                "SELECT * FROM instanceClockResetBinds WHERE instanceKey = ? ORDER BY orderIndex",
                (consInstanceKey,)).fetchall()]
            memoryRow = cur.execute(
                "SELECT * FROM memoryClocks WHERE memoryBlockKey = ?",
                (memoryBlockKey,)).fetchone()
            declRows = [dict(row) for row in cur.execute(
                "SELECT * FROM blockParameterizedDecls WHERE blockKey = ? ORDER BY orderIndex",
                (consBlockKey,)).fetchall()]
            con.close()

            prj = projectOpen(db_path)

            retClocksResets = {'qualBlock': consBlockKey}
            prj.getBDClocksResets(retClocksResets)
            expectedClockNames = [r['itemKey'] for r in clocksResetsRows if r['kind'] == 'clock']
            expectedResetNames = [r['itemKey'] for r in clocksResetsRows if r['kind'] == 'reset']
            gotClockNames = [c['clock'] for c in retClocksResets['clocks']]
            gotResetNames = [r['reset'] for r in retClocksResets['resets']]
            if (gotClockNames, gotResetNames) != (expectedClockNames, expectedResetNames):
                raise AssertionError(
                    f"getBDClocksResets({consBlockKey!r}) gave clocks "
                    f"{gotClockNames}/resets {gotResetNames}, expected "
                    f"{expectedClockNames}/{expectedResetNames} per a direct "
                    f"per-key SELECT")

            gotBinds = prj.getBDInstanceClockResetBinds(consInstanceKey)
            expectedBinds = [{'port': r['childPort'], 'signal': r['parentSignal']}
                             for r in bindRows]
            if gotBinds != expectedBinds:
                raise AssertionError(
                    f"getBDInstanceClockResetBinds({consInstanceKey!r}) gave "
                    f"{gotBinds}, expected {expectedBinds} per a direct "
                    f"per-key SELECT")

            gotMemoryClock = prj.getBDMemoryClock(memoryBlockKey)
            expectedMemoryClock = {'memoryBlockKey': memoryRow['memoryBlockKey'],
                                   'clock': memoryRow['clock'], 'reset': memoryRow['reset']}
            if gotMemoryClock != expectedMemoryClock:
                raise AssertionError(
                    f"getBDMemoryClock({memoryBlockKey!r}) gave "
                    f"{gotMemoryClock!r}, expected {expectedMemoryClock!r} per "
                    f"a direct per-key SELECT")

            retDecls = {'qualBlock': consBlockKey}
            prj.getBDParameterizedDecls(retDecls)
            gotDeclKeys = [d['declKey'] for d in retDecls['parameterizedDecls']]
            expectedDeclKeys = [r['declKey'] for r in declRows]
            if gotDeclKeys != expectedDeclKeys:
                raise AssertionError(
                    f"getBDParameterizedDecls({consBlockKey!r}) gave "
                    f"{gotDeclKeys}, expected {expectedDeclKeys} per a direct "
                    f"per-key SELECT")
            return True

        return all([
            _run_case("the fixture exercises all four tables with more than "
                      "one row", nonTrivialFixture),
            _run_case("getBDClocksResets, getBDInstanceClockResetBinds, "
                      "getBDMemoryClock and getBDParameterizedDecls each "
                      "match a direct per-key SELECT", helpersMatchPerKeySelect)])
    finally:
        shutil.rmtree(fixture)


# ------------------------------------------------------------- validation --

def run_reference_cases():
    """A connection clock: naming a clock no relevant block resolves to is
    rejected by clockTree.build(). A connection's clock: is a container
    reference validated against the container's own nets, not a
    project-scoped name, so there is no project 'clocks:' section to check it
    against first. A block's own clocks:/resets: entry needs no reference
    check at all: it is a fresh declaration, not a reference, so there is no
    name to misspell."""
    def check():
        fixture, project_path, db_path = _make_fixture(connectionClock=', clock: noSuchClock')
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code == 0 or 'Traceback' in output:
            raise AssertionError(f"the build did not report a diagnostic.\n{output}")
        for needle in ("must name the container clock an input clock of the instance is bound to",
                       "'noSuchClock' is not a clock net of container 'dut'",
                       "Correct the connection's clock: to a clock net of 'dut'"):
            if needle not in output:
                raise AssertionError(f"diagnostic does not mention '{needle}'.\n{output}")
        if 'input clocks to' in output:
            raise AssertionError(
                f"the diagnostic offers to bind an input clock to 'noSuchClock', "
                f"which is no net of the container to bind.\n{output}")
        return True
    return _run_case("a connection clock: naming an undeclared clock is rejected", check)


# uGen drives clkLocal from its output clock clkO and uSink runs on it; the
# connection from uGen's top-down port names clock: clkLocal. `{genPorts}`
# holds gen's ports: section.
SELF_DRIVEN_CONNECTION_CLOCK = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    gen:
        desc: "generator with an output clock"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:  { default: true }
            clkO: { direction: output }
        resets: { }
{genPorts}    sink:
        desc: "sink with no reset"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        resets: { }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uGen:   { container: top_tb, instanceType: gen, instGroup: top, clocks: { clkO: clkLocal } }
    uSink:  { container: top_tb, instanceType: sink, instGroup: top, clocks: { clk: clkLocal } }

connections:
    - { interface: dataIf, src: uGen, srcport: tx, dst: uSink, dstport: in, clock: clkLocal }
"""


def run_connection_clock_driven_by_end_cases():
    """uGen itself drives the connection's clock: clkLocal, so binding one of
    its input clocks to clkLocal would be rejected as self-driven and is not
    offered; declaring its port on the output clock is, and builds."""
    def design(genPorts=''):
        return HASVL_PORT_INTF + SELF_DRIVEN_CONNECTION_CLOCK.replace('{genPorts}', genPorts)

    def check():
        fixture, project_path, db_path = _make_fixture(design=design(), projectDomains='')
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code == 0 or 'Traceback' in output:
            raise AssertionError(f"the build did not report a diagnostic.\n{output}")
        for needle in ("'uGen'", "names clock: 'clkLocal'",
                       "declare port 'tx' on block 'gen' with clock: clkO",
                       "change the connection's clock:"):
            if needle not in output:
                raise AssertionError(f"diagnostic does not mention '{needle}'.\n{output}")
        if 'input clocks to' in output:
            raise AssertionError(
                f"the diagnostic offers to bind an input clock of uGen to the net "
                f"uGen itself drives.\n{output}")
        return True

    genPorts = ("        ports:\n"
                "            tx: { interface: dataIf, direction: src, clock: clkO }\n")
    return all([
        _run_case("a connection clock: the end's own instance drives offers no "
                  "input-clock bind", check),
        _expect_builds("declaring the port on the driving output clock builds",
                       design=design(genPorts), projectDomains=''),
    ])


def run_connection_clock_endpoint_cases():
    """A connection's clock: must name a clock BOTH endpoint blocks declare
    (name match only - this fixture has no instance map). 'clkSlow' is a
    real project clock (PROJECT_DOMAINS), so this is not the reference check
    above: without it an undeclared BLOCK clock would land silently on the
    block default, discarding the author's stated domain."""
    results = [_expect_diagnostic(
        "a connection clock: naming a clock neither endpoint block "
        "declares is rejected",
        ('prod', 'clkSlow', "must name the container clock an input clock of the instance is bound to"),
        connectionClock=', clock: clkSlow')]

    design = """types:
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
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkSlow: { }
        resets:
            rstSlow_n: { clock: clkSlow }
    prod:
        desc: "producer declaring clkSlow"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkSlow: { }
    cons:
        desc: "consumer declaring clkSlow"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkSlow: { }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd:  { container: top_tb, instanceType: prod,   instGroup: top }
    uCons:  { container: top_tb, instanceType: cons,   instGroup: top }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uCons, dstport: in, clock: clkSlow }
"""
    # A dedicated projectDomains: top_tb here declares only clkSlow (no
    # clk), so PROJECT_DOMAINS' clk/rst_n would have nothing to bind.
    projectDomains = """
clocks:
    clkSlow: { desc: "the block's only clock", default: true, period: 3, timeUnit: ns }

resets:
    rstSlow_n: { desc: "the block's only reset", default: true, clock: clkSlow }
"""
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains=projectDomains)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: a connection clock: both endpoints declare builds\n{output}")
            results.append(False)
        else:
            print("PASS: a connection clock: both endpoints declare builds")
            results.append(True)
    finally:
        shutil.rmtree(fixture)
    return all(results)


AMBIGUOUS_CONNECTION_CLOCK = """types:
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
    top_tb: {{ desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    prod:   {{ desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    cons:
        desc: "consumer with two input clocks, both bound to the container's clk"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:  {{ default: true }}
            clkB: {{ }}
{consPorts}
instances:
    top_tb: {{ container: top_tb, instanceType: top_tb, instGroup: top }}
    uProd:  {{ container: top_tb, instanceType: prod, instGroup: top }}
    uCons:  {{ container: top_tb, instanceType: cons, instGroup: top, clocks: {{ clkB: clk }} }}

connections:
    - {{ interface: dataIf, src: uProd, srcport: out, dst: uCons, dstport: in, clock: clk }}
"""


def run_ambiguous_connection_clock_cases():
    """uCons binds both clk and clkB to the container's clk, so a
    connection clock: clk cannot pick the block clock of its top-down port
    'in'. Declaring 'in' with its own clock: clears it."""
    results = [_expect_diagnostic(
        "a connection clock: two input clocks of a top-down end resolve to is rejected",
        ("'uCons'", "port 'in' is ambiguous", 'Bind only one of clk, clkB',
         "declare port 'in' on block 'cons' with its own clock:",
         "drop the connection's clock:"),
        design=AMBIGUOUS_CONNECTION_CLOCK.format(consPorts=''), projectDomains='')]

    def declaredPortBuilds():
        consPorts = ("        ports:\n"
                     "            in: { interface: dataIf, direction: dst, clock: clkB }\n")
        fixture, project_path, db_path = _make_fixture(
            design=AMBIGUOUS_CONNECTION_CLOCK.format(consPorts=consPorts), projectDomains='')
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code != 0:
            raise AssertionError(f"the build failed.\n{output}")
        return True
    results.append(_run_case(
        "a declared port with its own clock: is not ambiguous under a shared connection clock:",
        declaredPortBuilds))

    def onDefaultClock(db_path):
        domain = _port_domain(db_path, 'cons', 'in')
        if domain != 'clk':
            raise AssertionError(f"'in' reports domainClock {domain!r}, expected the "
                                 f"block default 'clk'")
    consPorts = ("        ports:\n"
                 "            in: { interface: dataIf, direction: dst }\n")
    results.append(_expect_builds(
        "a declared port naming no clock: on a block with two input clocks bound "
        "to the connection's clock: is on the block default and builds",
        onDefaultClock,
        design=AMBIGUOUS_CONNECTION_CLOCK.format(consPorts=consPorts), projectDomains=''))
    return all(results)


# 'gen' has two input clocks on the container's clk and declares port 'tx' on
# its output clock clkO. 'sink' has no resets, so it may sit on a local clock.
OUTPUT_CLOCK_PORT = """types:
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
    top_tb: {{ desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    gen:
        desc: "generator whose port tx is on its output clock"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkA: {{ default: true }}
            clkB: {{ }}
            clkO: {{ direction: output }}
        ports:
            tx: {{ interface: dataIf, direction: src, clock: clkO }}
    sink:
        desc: "sink with no reset"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        resets: {{ }}

instances:
    top_tb: {{ container: top_tb, instanceType: top_tb, instGroup: top }}
    uGen:   {{ container: top_tb, instanceType: gen, instGroup: top,
              clocks: {{ clkA: clk, clkB: clk, clkO: {genBind} }} }}
    uSink:  {{ container: top_tb, instanceType: sink, instGroup: top{sinkMap} }}
{extraInstances}
connections:
    - {{ interface: dataIf, src: uGen, srcport: tx, dst: uSink, dstport: in, clock: {connClock} }}
"""


def run_output_clock_port_cases():
    """A declared port on an output clock is on the net that clock drives,
    which a connection's clock: must name."""
    results = [_expect_diagnostic(
        "a port on an output clock driving another net than the connection's clock: is rejected",
        ("Port 'tx'", "'uGen'", "declares clock: 'clkO'", "bound to 'clkLocal'",
         "names clock: 'clk'", "change the clock: of port 'tx' to clkA or clkB",
         "change the connection's clock: to 'clkLocal'"),
        design=OUTPUT_CLOCK_PORT.format(
            genBind='clkLocal', sinkMap='', connClock='clk',
            extraInstances="    uLocal: { container: top_tb, instanceType: sink, instGroup: top,\n"
                           "              clocks: { clk: clkLocal } }\n"),
        projectDomains='')]

    def onOutputClock(db_path):
        for block, port, expected in (('gen', 'tx', 'clkO'), ('sink', 'in', 'clk')):
            domain = _port_domain(db_path, block, port)
            if domain != expected:
                raise AssertionError(f"'{block}.{port}' reports domainClock {domain!r}, "
                                     f"expected {expected!r}")
    results.append(_expect_builds(
        "a port on an output clock driving the connection's clock: builds",
        onOutputClock,
        design=OUTPUT_CLOCK_PORT.format(
            genBind='clkLocal', sinkMap=', clocks: { clk: clkLocal }',
            connClock='clkLocal', extraInstances=''),
        projectDomains=''))

    results.append(_expect_diagnostic(
        "a port on an output clock bound to ~ cannot carry a connection",
        ("Port 'tx'", "'uGen'", "output clock 'clkO'", 'binds to `~`',
         'no connection clock: can agree with it',
         "change the clock: of port 'tx' to clkA or clkB",
         "drop the connection's clock:"),
        design=OUTPUT_CLOCK_PORT.format(
            genBind='~', sinkMap='', connClock='clk', extraInstances=''),
        projectDomains=''))
    return all(results)


def run_unsupported_direction_cases():
    """`async: true` on a reset is bindable: an asynchronous reset input
    takes no default fallback, only a map entry or a name match, so 'cons'
    declaring one with no matching name in its container 'dut' (which
    declares no resets: of its own) is an error naming the reset and the
    block, not an "unsupported" rejection. `direction: output` on a clock is
    bindable too (run_output_clock_bindable_cases)."""
    return _expect_diagnostic(
        "an unbound async reset input is rejected, not the shape itself",
        ('cons', 'rstA_n', 'takes no default fallback'),
        consumerDomains="        resets:\n"
                        "            rstA_n: { async: true }\n")


ASYNC_NAME_DESIGN = """blocks:
    top_tb:
        desc: "testbench container: declares rstA_n directly, one level from cons"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        resets:
            rst_n:  { default: true }
            rstA_n: { }
    cons:
        desc: "consumer with an async reset input, implicit clk"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        resets:
            rstA_n: { async: true }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uCons:  { container: top_tb, instanceType: cons,   instGroup: top }
"""


def run_async_reset_bound_by_name_cases():
    """An asynchronous reset input binds by an ordinary name match when its
    container declares a reset of the same name: 'top_tb'
    declares 'rstA_n' and 'cons' consumes it as an async input, with no
    instance map at all. One level, top_tb directly containing 'cons',
    keeps 'rstA_n' from also needing a SECOND, outer binding of its own
    (the input clock/reset the map or name match resolves is a net of the
    child's OWN container only, not chased further up)."""
    # A dedicated projectDomains: top_tb IS the topInstance here, so its own
    # extra reset rstA_n must also bind to a matching testbench entry.
    projectDomains = """
resets:
    rst_n:  { desc: "the default reset", default: true }
    rstA_n: { desc: "a second reset on the implicit default clock" }
"""
    fixture, project_path, db_path = _make_fixture(design=ASYNC_NAME_DESIGN,
                                                    projectDomains=projectDomains)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: an async reset input bound by name match builds\n{output}")
            return False
        print("PASS: an async reset input bound by name match builds")
        return True
    finally:
        shutil.rmtree(fixture)


ASYNC_MAP_DESIGN = """blocks:
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:     { default: true }
            clkSlow: { }
        resets:
            rst_n:     { clock: clk }
            rstSlow_n: { clock: clkSlow }
    dut:
        desc: "container with two clocks/resets"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:     { default: true }
            clkSlow: { }
        resets:
            rst_n:     { clock: clk }
            rstSlow_n: { clock: clkSlow }
    cons:
        desc: "consumer with an async reset input, implicit clk"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        resets:
            rstA_n: { async: true }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    u_dut:  { container: top_tb, instanceType: dut,    instGroup: top }
    uCons:  { container: dut,    instanceType: cons,   instGroup: top,
              resets: { rstA_n: rstSlow_n } }
"""


def run_async_reset_bound_by_map_cases():
    """An asynchronous reset input binds by an explicit instance map, and is
    exempt from the reset clock-membership check: 'uCons' maps
    its async 'rstA_n' onto 'rstSlow_n', which belongs to 'clkSlow', while
    'cons' itself runs on the implicit 'clk' (bound to 'dut's 'clk' by name
    match) - a mismatch rejected for a SYNCHRONOUS reset, but an
    asynchronous reset input belongs to no clock of its own, so it builds."""
    fixture, project_path, db_path = _make_fixture(design=ASYNC_MAP_DESIGN)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: an async reset input mapped across clocks builds\n{output}")
            return False
        print("PASS: an async reset input mapped across clocks builds, exempt from clock membership")
        return True
    finally:
        shutil.rmtree(fixture)


def run_output_clock_bindable_cases():
    """`direction: output` on a clock is bindable: an output's
    map entry is required and its value is `~` to leave it
    unconnected, a new local net name, or a declared output of the
    container (export)."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    gen:
        desc: "clock generator"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            genClk: { direction: output }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uGen:   { container: top_tb, instanceType: gen, instGroup: top,
              clocks: { genClk: ~ } }
"""
    # projectDomains='': top_tb declares nothing of its own (implicit
    # clk/rst_n only); PROJECT_DOMAINS' extra clkSlow would have nothing in
    # this design to consume it.
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains='')
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: an output clock bound to \\`~\\` builds clean\n{output}")
            return False
        print("PASS: an output clock bound to `~` builds clean")
        return True
    finally:
        shutil.rmtree(fixture)


# ------------------------------------ standalone period resolution --

STANDALONE_PROJECT_TWO_CLOCKS = """
clocks:
    clkA: { desc: "default testbench clock", default: true, period: 7, timeUnit: ns }
    clkB: { desc: "second testbench clock", period: 9, timeUnit: ns }

resets:
    rst_n:  { desc: "clkA's reset", default: true, clock: clkA }
    rstB_n: { desc: "clkB's reset", clock: clkB }
"""

STANDALONE_TOP_TWO_CLOCKS = """blocks:
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkA: { default: true }
            clkB: { }
        resets:
            rst_n:  { clock: clkA }
            rstB_n: { clock: clkB }
"""


def run_standalone_period_agrees_through_both_instances():
    """Standalone period, positive: 'leaf' declares no period:, but both of its instances
    bind clk to the same testbench clock clkA - the design determines its
    period (7 ns), read back from the generated standalone wrapper."""
    design = STANDALONE_TOP_TWO_CLOCKS + """    leaf:
        desc: "hasVl leaf with no declared period, instantiated twice on the same clock"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uLeafA: { container: top_tb, instanceType: leaf, instGroup: top,
              clocks: { clk: clkA }, resets: { rst_n: rst_n } }
    uLeafB: { container: top_tb, instanceType: leaf, instGroup: top,
              clocks: { clk: clkA }, resets: { rst_n: rst_n } }
"""
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains=STANDALONE_PROJECT_TWO_CLOCKS)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: standalone period agreement through two instances builds\n{output}")
            return False
        made = _arch2code('--db', db_path, '-r', '--newmodule', cwd=fixture)
        if made.returncode != 0:
            print(f"FAIL: newmodule failed:\n{made.stdout}\n{made.stderr}")
            return False
        rel = 'verif/leaf_hdl_sc_wrapper.h'
        gen = _arch2code('--db', db_path, '-r', '--systemc',
                         '--file', os.path.join(fixture, rel), cwd=fixture)
        if gen.returncode != 0:
            print(f"FAIL: generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
            return False
        with open(os.path.join(fixture, rel)) as f:
            text = f.read()
        if 'sc_time(7, SC_NS) / 2' not in text:
            print(f"FAIL: leaf's resolved period is not clkA's 7 ns:\n{text}")
            return False
        print("PASS: the standalone period resolves through two agreeing instances to clkA's own period")
        return True
    finally:
        shutil.rmtree(fixture)


def run_standalone_declared_period_wins_over_disagreement():
    """Standalone period, positive: 'leaf' declares its own period:, so a disagreement
    between its two instances' resolved clocks is immaterial - the
    declaration wins outright."""
    design = STANDALONE_TOP_TWO_CLOCKS + """    leaf:
        desc: "hasVl leaf with its own declared period, instantiated on two different clocks"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        clocks:
            clk: { period: 5, timeUnit: ns }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uLeafA: { container: top_tb, instanceType: leaf, instGroup: top,
              clocks: { clk: clkA }, resets: { rst_n: rst_n } }
    uLeafB: { container: top_tb, instanceType: leaf, instGroup: top,
              clocks: { clk: clkB }, resets: { rst_n: rstB_n } }
"""
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains=STANDALONE_PROJECT_TWO_CLOCKS)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: a declared standalone period wins builds\n{output}")
            return False
        made = _arch2code('--db', db_path, '-r', '--newmodule', cwd=fixture)
        if made.returncode != 0:
            print(f"FAIL: newmodule failed:\n{made.stdout}\n{made.stderr}")
            return False
        rel = 'verif/leaf_hdl_sc_wrapper.h'
        gen = _arch2code('--db', db_path, '-r', '--systemc',
                         '--file', os.path.join(fixture, rel), cwd=fixture)
        if gen.returncode != 0:
            print(f"FAIL: generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
            return False
        with open(os.path.join(fixture, rel)) as f:
            text = f.read()
        if 'sc_time(5, SC_NS) / 2' not in text:
            print(f"FAIL: leaf's own declared period (5 ns) did not win:\n{text}")
            return False
        print("PASS: a declared standalone period wins even though the two instances disagree")
        return True
    finally:
        shutil.rmtree(fixture)


def run_standalone_period_rejects_disagreement():
    """Standalone period, negative: 'leaf' declares no period: and its two
    instances resolve to different testbench clocks - an error naming both
    instances."""
    design = STANDALONE_TOP_TWO_CLOCKS + """    leaf:
        desc: "hasVl leaf with no declared period, instantiated on two different clocks"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uLeafA: { container: top_tb, instanceType: leaf, instGroup: top,
              clocks: { clk: clkA }, resets: { rst_n: rst_n } }
    uLeafB: { container: top_tb, instanceType: leaf, instGroup: top,
              clocks: { clk: clkB }, resets: { rst_n: rstB_n } }
"""
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains=STANDALONE_PROJECT_TWO_CLOCKS)
    try:
        code, output = _build(project_path, db_path)
        if code == 0:
            print(f"FAIL: disagreeing instances with no declared period built successfully\n{output}")
            return False
        ok = all(needle in output for needle in ('A standalone build needs a period', 'uLeafA', 'uLeafB'))
        print(f"{'PASS' if ok else 'FAIL'}: the missing-period check rejects two instances resolving to "
              f"different testbench clocks, naming both{'' if ok else chr(10) + output}")
        return ok
    finally:
        shutil.rmtree(fixture)


def run_standalone_period_rejects_supplier_output():
    """Standalone period, negative: 'leaf' declares no period: and its instance resolves to
    a supplier's output (a local net a divider drives), not a testbench
    net - an error naming the cause."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    gen:
        desc: "clock generator: produces a local, non-testbench clock and reset"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            clk:    { default: true }
            genClk: { direction: output }
        resets:
            rst_n:    { clock: clk }
            genRst_n: { clock: genClk, direction: output }
    leaf:
        desc: "hasVl leaf with no declared period, resolving to gen's output"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uGen:   { container: top_tb, instanceType: gen, instGroup: top,
              clocks: { genClk: clkLocal }, resets: { genRst_n: rstLocal_n } }
    uLeaf:  { container: top_tb, instanceType: leaf, instGroup: top,
              clocks: { clk: clkLocal }, resets: { rst_n: rstLocal_n } }
"""
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains='')
    try:
        code, output = _build(project_path, db_path)
        if code == 0:
            print(f"FAIL: a clock with no period resolving to a supplier's output built successfully\n{output}")
            return False
        ok = all(needle in output for needle in ('A standalone build needs a period', 'uLeaf', "supplier"))
        print(f"{'PASS' if ok else 'FAIL'}: the missing-period check rejects a clock resolving to a supplier's "
              f"output with no declared period{'' if ok else chr(10) + output}")
        return ok
    finally:
        shutil.rmtree(fixture)


def run_standalone_period_rejects_zero_instance():
    """Standalone period, negative: 'leaf' declares no period: and is never instantiated at
    all in its own declaring project - an error naming that cause."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    leaf:
        desc: "hasVl leaf, never instantiated"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
"""
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains='')
    try:
        code, output = _build(project_path, db_path)
        if code == 0:
            print(f"FAIL: a zero-instance hasVl block with no period built successfully\n{output}")
            return False
        ok = all(needle in output for needle in ('A standalone build needs a period', 'leaf', 'no instance'))
        print(f"{'PASS' if ok else 'FAIL'}: the missing-period check rejects a zero-instance hasVl block with no "
              f"declared period{'' if ok else chr(10) + output}")
        return ok
    finally:
        shutil.rmtree(fixture)


def run_standalone_period_cases():
    return all([
        run_standalone_period_agrees_through_both_instances(),
        run_standalone_declared_period_wins_over_disagreement(),
        run_standalone_period_rejects_disagreement(),
        run_standalone_period_rejects_supplier_output(),
        run_standalone_period_rejects_zero_instance(),
    ])


# ------------------------------------- input reset on an output clock --

def run_top_rejects_reset_on_unbound_clock():
    """At the design top: top_tb's own INPUT reset 'rstOut_n' belongs to
    'clkOut', an OUTPUT clock of top_tb, so the testbench would be releasing a
    reset of a clock it does not generate. An input reset must belong to an
    input clock, so top_tb's declaration is rejected, even though the
    testbench declares a reset of the same name."""
    design = """blocks:
    top_tb:
        desc: "testbench container with an output clock and a reset on it"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            clkOut: { direction: output }
        resets:
            rst_n:    { clock: clk }
            rstOut_n: { clock: clkOut }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
"""
    projectDomains = """
clocks:
    clk: { desc: "the default clock", default: true, period: 1, timeUnit: ns }

resets:
    rst_n:    { desc: "the default reset", default: true, clock: clk }
    rstOut_n: { desc: "same name as top_tb's own reset on its output clock", clock: clk }
"""
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains=projectDomains)
    try:
        code, output = _build(project_path, db_path)
        if code == 0:
            print(f"FAIL: a top reset on an unbound (output) clock built successfully\n{output}")
            return False
        ok = 'an input reset must belong to an input clock' in output
        print(f"{'PASS' if ok else 'FAIL'}: a top input reset on an output clock is "
              f"rejected{'' if ok else chr(10) + output}")
        return ok
    finally:
        shutil.rmtree(fixture)


def run_top_rst_fallback_several_testbench_resets_rejected():
    """top_tb's rst_n is on clkSlow and falls back to that testbench clock's
    selected reset, but clkSlow has two testbench resets and neither is
    selected. The fix is to map rst_n to one of them, not to declare
    another."""
    design = """blocks:
    top_tb:
        desc: "testbench container whose rst_n is on its second clock"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:     { default: true }
            clkSlow: { }
        resets:
            rstMain_n: { clock: clk }
            rst_n:     { clock: clkSlow }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
"""
    projectDomains = """
clocks:
    clk:     { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    clkSlow: { desc: "a slower clock", period: 3, timeUnit: ns }

resets:
    rstMain_n:  { desc: "the default reset", default: true, clock: clk }
    rstSlowA_n: { desc: "first reset of clkSlow", clock: clkSlow }
    rstSlowB_n: { desc: "second reset of clkSlow", clock: clkSlow }
"""
    return _expect_diagnostic(
        "the top rst_n fallback onto a testbench clock with several unselected resets is rejected",
        ("'top_tb'", "'clkSlow'", '2 testbench resets (rstSlowA_n, rstSlowB_n)',
         'Map rst_n to one of rstSlowA_n, rstSlowB_n'),
        design=design, projectDomains=projectDomains)


def run_standalone_rejects_reset_on_output_clock():
    """A standalone hasVl block: 'leaf''s input reset 'rst2_n' belongs to
    'clk2', an OUTPUT clock of 'leaf' itself. An input reset must belong to an
    input clock, so the declaration is rejected; a standalone build could not
    count release cycles on an observed output clock either."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    leaf:
        desc: "hasVl leaf whose second reset belongs to its own output clock"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        clocks:
            clk:  { default: true, period: 10, timeUnit: ns }
            clk2: { direction: output }
        resets:
            rst_n:  { clock: clk }
            rst2_n: { clock: clk2 }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uLeaf:  { container: top_tb, instanceType: leaf, instGroup: top,
              clocks: { clk2: ~ }, resets: { rst2_n: rst_n } }
"""
    # rst2_n is mapped directly onto top_tb's own rst_n so that the
    # declaration check is the only diagnostic this fixture can raise.
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains='')
    try:
        code, output = _build(project_path, db_path)
        if code == 0:
            print(f"FAIL: a standalone reset on an output clock built successfully\n{output}")
            return False
        ok = all(needle in output for needle in
                 ('an input reset must belong to an input clock', 'leaf', 'rst2_n'))
        print(f"{'PASS' if ok else 'FAIL'}: a standalone hasVl block's input reset "
              f"on its own output clock is rejected{'' if ok else chr(10) + output}")
        return ok
    finally:
        shutil.rmtree(fixture)


# ------------------------------------------------------- end-of-run report --

def run_end_of_run_report_cases():
    """End-of-run report: a hasVl block with an output clock and an output
    reset gets an end_of_simulation() override reporting both; a hasVl block
    with no outputs at all gets no override rather than an empty one."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    gen:
        desc: "produces an output clock and an output reset"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        clocks:
            clk:    { default: true }
            genClk: { direction: output }
        resets:
            rst_n:    { clock: clk }
            genRst_n: { clock: genClk, direction: output }
    plainVl:
        desc: "hasVl leaf with no outputs at all"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uGen:   { container: top_tb, instanceType: gen, instGroup: top,
              clocks: { genClk: ~ }, resets: { genRst_n: ~ } }
    uPlain: { container: top_tb, instanceType: plainVl, instGroup: top }
"""
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains='')
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: end-of-run report fixture builds\n{output}")
            return False
        made = _arch2code('--db', db_path, '-r', '--newmodule', cwd=fixture)
        if made.returncode != 0:
            print(f"FAIL: newmodule failed:\n{made.stdout}\n{made.stderr}")
            return False

        def render(rel):
            gen = _arch2code('--db', db_path, '-r', '--systemc',
                             '--file', os.path.join(fixture, rel), cwd=fixture)
            if gen.returncode != 0:
                raise AssertionError(f"generating {rel} failed:\n{gen.stdout}\n{gen.stderr}")
            with open(os.path.join(fixture, rel)) as f:
                return f.read()

        genText = render('verif/gen_hdl_sc_wrapper.h')
        plainText = render('verif/plainVl_hdl_sc_wrapper.h')
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        return False
    finally:
        shutil.rmtree(fixture)

    ok = True
    for needle in ('void end_of_simulation() override', "produced no edge",
                  'was never observed to release during the run'):
        if needle not in genText:
            print(f"FAIL: end-of-run report: {needle!r} missing from gen's own wrapper")
            ok = False
    if 'end_of_simulation' in plainText:
        print("FAIL: end-of-run report: plainVl (no outputs at all) must get no override")
        ok = False
    print(f"{'PASS' if ok else 'FAIL'}: the end-of-run report is emitted only for a block "
          f"with an output clock or reset, omitted entirely otherwise")
    return ok


# ------------------------------------------------------- domain agreement --

# A memory on a consumer that declares its own clocks and resets, so the
# memory's clock:/reset: have declared rows to be checked against. top_tb
# declares nothing (projectDomains='' pairs with it); the memory domain
# fields are appended to the memory entry.
MEMORY_DESIGN = """constants:
    TBL_WORDS: {{ value: 4, desc: "memory word count" }}

types:
    dataT: {{ width: 8, desc: "payload word" }}
    memAddrT: {{ width: 3, desc: "memory address" }}

structures:
    dataSt:
        data: {{ varType: dataT, desc: "payload word" }}
    memAddrSt:
        address: {{ varType: memAddrT, generator: address, desc: "memory address" }}
    memSt:
        data: {{ varType: dataT, generator: memory, desc: "memory payload" }}

interfaces:
    dataIf:
        desc: "producer to consumer stream"
        interfaceType: push_ack
        structures:
            - {{ structure: dataSt, structureType: data_t }}

blocks:
    top_tb: {{ desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    dut:
        desc: "container of the producer and consumer"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: {{ default: true }}
        resets:
            rst_n: {{ clock: clk }}
    prod: {{ desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    cons:
        desc: "consumer holding a memory"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: {{ default: true }}
        resets:
            rst_n: {{ clock: clk }}

instances:
    top_tb: {{ container: top_tb, instanceType: top_tb, instGroup: top }}
    u_dut:  {{ container: top_tb, instanceType: dut,    instGroup: top }}
    uProd:  {{ container: dut,    instanceType: prod,   instGroup: top }}
    uCons:  {{ container: dut,    instanceType: cons,   instGroup: top }}

connections:
    - {{ interface: dataIf, src: uProd, srcport: out, dst: uCons, dstport: in }}

memories:
    - {{ memory: tbl, block: cons, structure: memSt, addressStruct: memAddrSt, wordLines: TBL_WORDS, ports: [p], desc: "consumer table"{memoryDomain} }}
"""


def run_domain_agreement_cases():
    """A block reset's clock: names a block clock of the same block, and a
    port's, registerPorts:, addressBlock: or memory's clock:/reset: does
    too. The existence part of both is the schema's blockClock/
    blockReset combo foreign key (schema.yaml), so the diagnostic is the
    parser's "not valid in context" form naming the block and the stated
    name; a block declaring no clocks: has no rows for the key to find, so
    a stated clock: on one is rejected the same way (its only clock is the
    implicit clk, so stating it is redundant at best)."""
    results = [_expect_diagnostic(
        "a block reset's clock: naming a clock the block does not declare "
        "is rejected",
        ('cons', 'rst_n', 'noSuchClock', 'not valid in context'),
        consumerDomains="        clocks:\n"
                        "            clk: { default: true }\n"
                        "        resets:\n"
                        "            rst_n: { clock: noSuchClock }\n")]
    results.append(_expect_diagnostic(
        "a declared port's clock: naming a clock the block does not "
        "declare is rejected",
        ('cons', 'regs', 'noSuchClock', 'not valid in context'),
        consumerDomains="        clocks:\n"
                        "            clk: { default: true }\n"
                        "        ports:\n"
                        "            regs: { interface: dataIf, direction: dst, "
                        "clock: noSuchClock }\n"))
    results.append(_expect_diagnostic(
        "a stated clock: on a block declaring no clocks: is rejected, even "
        "as 'clk': the block has no clock rows, its one clock is implicit",
        ('cons', 'rst_n', 'clk', 'not valid in context'),
        consumerDomains="        resets:\n"
                        "            rst_n: { clock: clk }\n"))
    results.append(_expect_diagnostic(
        "a memory's clock: naming a clock its block does not declare is "
        "rejected",
        ('cons', 'noSuchClock', 'not valid in context'),
        design=MEMORY_DESIGN.format(memoryDomain=', clock: noSuchClock'),
        projectDomains=''))
    results.append(_expect_diagnostic(
        "a memory's reset: naming a reset its block does not declare is "
        "rejected",
        ('cons', 'noSuchReset', 'not valid in context'),
        design=MEMORY_DESIGN.format(memoryDomain=', reset: noSuchReset'),
        projectDomains=''))
    return all(results)


# ---------------------------------------------------- instance bind pairs --

def run_bind_pair_cases():
    """A reset bound by name match must belong to the clock its own
    block clock is bound to.

    A custom design, one level (top_tb containing cons directly): clkB is
    not clk/rst_n, so a dut-in-between would also have to declare it for
    the automatic binding to reach cons at all, which the container/
    consumer-domains form of the fixture cannot express without a third
    level.

    top_tb declares clk (default) and clkB, each with a reset. cons also
    declares clk and clkB, but names its OWN reset 'rst_n' on clkB - the
    same name as top_tb's clk-domain reset. Both clocks bind by name match;
    the reset then binds by name match too, landing cons on top_tb's
    'rst_n' - which top_tb releases on clk, not clkB. That is exactly the
    pair a per-block set cannot see: top_tb legitimately carries both
    domains."""
    design = """blocks:
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:  { default: true }
            clkB: { }
        resets:
            rst_n:  { clock: clk }
            rstB_n: { clock: clkB }
    cons:
        desc: "consumer"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:  { default: true }
            clkB: { }
        resets:
            rst_n: { clock: clkB }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uCons:  { container: top_tb, instanceType: cons,   instGroup: top }
"""
    return _expect_diagnostic(
        "a reset bound by name match to the wrong container clock's reset "
        "is rejected",
        ('uCons', 'cons', 'top_tb', "'clkB'", "'rst_n'", "'clk'",
         'A synchronous reset must be released on the container clock'),
        design=design)


# --------------------------------------------------------- instance maps --

def run_instance_map_bad_key_rejected():
    """A map key must name a block clock of the instantiated block."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    cons:
        desc: "consumer"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { default: true }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uCons:  { container: top_tb, instanceType: cons,   instGroup: top,
              clocks: { clkBogus: clk } }
"""
    return _expect_diagnostic(
        "a map key naming a clock the instantiated block does not declare "
        "is rejected",
        ('uCons', 'clkBogus', 'cons', "from the instance's clocks: map"),
        design=design)


def run_instance_map_bad_value_rejected():
    """A map value must name a declared clock/reset of the container (a
    local net or `~` is covered by the local-net tests)."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    cons:
        desc: "consumer"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { default: true }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uCons:  { container: top_tb, instanceType: cons,   instGroup: top,
              clocks: { clk: noSuchNet } }
"""
    return _expect_diagnostic(
        "a map value naming a net the container does not declare is "
        "rejected",
        ('uCons', 'cons', 'top_tb', 'noSuchNet', 'Map it to one of those clocks'),
        design=design)


def run_instance_map_kind_mismatch_rejected():
    """A clock map entry must bind a clock net, not a reset net (and a
    reset entry a reset net), even when the name exists in the container."""
    design = """blocks:
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { default: true }
        resets:
            rst_n: { clock: clk }
    cons:
        desc: "consumer"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { default: true }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uCons:  { container: top_tb, instanceType: cons,   instGroup: top,
              clocks: { clk: rst_n } }
"""
    return _expect_diagnostic(
        "a clock map entry naming a container RESET is rejected: a clock "
        "entry binds a clock net, not a reset net",
        ('uCons', 'cons', 'top_tb', 'rst_n', 'Map it to one of those clocks'),
        design=design)


def run_instance_map_renamed_connection_clock_accepted():
    """A connection's clock: through a renamed instance map derives to
    exactly one input clock of the instance, even though the block's own
    clock name (clkC) differs from the container's (clkSlow) - the
    composition-and-renaming shape instance maps exist for."""
    design = """types:
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
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:     { default: true }
            clkSlow: { }
        resets:
            rst_n:     { clock: clk }
            rstSlow_n: { clock: clkSlow }
    prod: { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    cons:
        desc: "consumer; declares its clock as clkC, not clkSlow"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkC: { default: true }
        resets:
            rstC_n: { clock: clkC }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd:  { container: top_tb, instanceType: prod,   instGroup: top,
              clocks: { clk: clkSlow }, resets: { rst_n: rstSlow_n } }
    uCons:  { container: top_tb, instanceType: cons,   instGroup: top,
              clocks: { clkC: clkSlow }, resets: { rstC_n: rstSlow_n } }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uCons, dstport: in, clock: clkSlow }
"""
    fixture, project_path, db_path = _make_fixture(design=design)
    try:
        code, output = _build(project_path, db_path)
    finally:
        shutil.rmtree(fixture)
    if code != 0:
        print(f"FAIL: a renamed instance map still resolves the connection "
              f"clock: to the one renamed input clock\n{output}")
        return False
    print("PASS: a renamed instance map still resolves the connection clock: "
          "to the one renamed input clock")
    return True


def run_instance_maps_cases():
    return all([
        run_instance_map_bad_key_rejected(),
        run_instance_map_bad_value_rejected(),
        run_instance_map_kind_mismatch_rejected(),
        run_instance_map_renamed_connection_clock_accepted(),
    ])


# --------------------------------------------------------------- local nets --

# A generator with an output clock, and a consumer, both inside 'dut': the
# generator's output binding names 'clkGen', a name 'dut' does not declare,
# creating a local net; the consumer's own 'clk' binds to it by an explicit
# map.
LOCAL_NET_DESIGN = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container: the generated clock is a local net of this block"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            sysClk: { default: true }
    gen:
        desc: "clock generator"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            genClk: { direction: output }
        resets: {}
    cons:
        desc: "consumer of the generated clock"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        resets: {}

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uDut:   { container: top_tb, instanceType: dut,    instGroup: top,
              clocks: { sysClk: clk } }
    uGen:   { container: dut,    instanceType: gen,    instGroup: top,
              clocks: { clk: sysClk, genClk: clkGen } }
    uCons:  { container: dut,    instanceType: cons,   instGroup: top,
              clocks: { clk: clkGen } }
"""


def run_local_net_positive_case():
    """A child output bound to a name the container does not declare
    creates a local net: kind 'local', driven by the output
    ('childOutput'), consumed by the other child's own map entry."""
    # projectDomains='': top_tb declares nothing of its own (implicit
    # clk/rst_n only); PROJECT_DOMAINS' extra clkSlow would have nothing in
    # this design to consume it.
    fixture, project_path, db_path = _make_fixture(design=LOCAL_NET_DESIGN, projectDomains='')
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: the local-net fixture builds\n{output}")
            return False
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        dutKey = cur.execute("SELECT blockKey FROM blocks WHERE block = 'dut'").fetchone()['blockKey']
        genInstanceKey = cur.execute(
            "SELECT instanceKey FROM instances WHERE instance = 'uGen'").fetchone()['instanceKey']
        consInstanceKey = cur.execute(
            "SELECT instanceKey FROM instances WHERE instance = 'uCons'").fetchone()['instanceKey']
        localNets = cur.execute(
            "SELECT * FROM containerLocalNets WHERE blockKey = ?", (dutKey,)).fetchall()
        genBinds = cur.execute(
            "SELECT * FROM instanceClockResetBinds WHERE instanceKey = ?", (genInstanceKey,)).fetchall()
        consBinds = cur.execute(
            "SELECT * FROM instanceClockResetBinds WHERE instanceKey = ?", (consInstanceKey,)).fetchall()
        con.close()

        failed = False
        if len(localNets) != 1 or localNets[0]['netName'] != 'clkGen':
            print(f"FAIL: containerLocalNets for 'dut' is {[dict(r) for r in localNets]}, "
                  f"expected one 'clkGen' net")
            failed = True
        genOutputBinds = [(r['childPort'], r['parentSignal']) for r in genBinds]
        if ('genClk', 'clkGen') not in genOutputBinds:
            print(f"FAIL: uGen's own binds are {genOutputBinds}, expected "
                  f"('genClk', 'clkGen') among them")
            failed = True
        consInputBinds = [(r['childPort'], r['parentSignal']) for r in consBinds]
        if ('clk', 'clkGen') not in consInputBinds:
            print(f"FAIL: uCons's own binds are {consInputBinds}, expected "
                  f"('clk', 'clkGen') among them")
            failed = True
        print(f"{'FAIL' if failed else 'PASS'}: a child output bound to a new name "
              f"creates a local net, consumed by a sibling's own map entry")
        return not failed
    finally:
        shutil.rmtree(fixture)


def run_local_net_no_consumer_rejected():
    """A local net with no child input consumer is an error naming the
    driving binding."""
    design = LOCAL_NET_DESIGN.replace(
        "    uCons:  { container: dut,    instanceType: cons,   instGroup: top,\n"
        "              clocks: { clk: clkGen } }\n",
        "    uCons:  { container: dut,    instanceType: cons,   instGroup: top }\n")
    assert design != LOCAL_NET_DESIGN, "the uCons replacement did not match"
    return _expect_diagnostic(
        "a local net with no consumer is rejected",
        ('dut', 'clkGen', 'uGen', 'genClk',
         'A local net must be consumed by at least one child input binding'),
        design=design, projectDomains='')


def run_output_bound_to_container_input_rejected():
    """An output may not bind to a container INPUT, which already has a
    driver (its own parent)."""
    design = LOCAL_NET_DESIGN.replace(
        "clocks: { clk: sysClk, genClk: clkGen }", "clocks: { clk: sysClk, genClk: sysClk }")
    assert design != LOCAL_NET_DESIGN, "the genClk replacement did not match"
    return _expect_diagnostic(
        "an output bound to a container input is rejected",
        ('uGen', 'genClk', 'sysClk', 'already driven by its own parent'),
        design=design)


def run_two_outputs_one_net_rejected():
    """Two child outputs bound to the same local net name is a second
    driver on one net."""
    design = LOCAL_NET_DESIGN.replace(
        "    cons:\n",
        "    gen2:\n"
        "        desc: \"a second clock generator\"\n"
        "        hasVl: false\n"
        "        hasMdl: false\n"
        "        hasTb: false\n"
        "        hasRtl: false\n"
        "        clocks:\n"
        "            clk:    { default: true }\n"
        "            genClk: { direction: output }\n"
        "    cons:\n"
    ).replace(
        "    uCons:  { container: dut,    instanceType: cons,   instGroup: top,\n"
        "              clocks: { clk: clkGen } }\n",
        "    uCons:  { container: dut,    instanceType: cons,   instGroup: top,\n"
        "              clocks: { clk: clkGen } }\n"
        "    uGen2:  { container: dut,    instanceType: gen2,   instGroup: top,\n"
        "              clocks: { clk: sysClk, genClk: clkGen } }\n")
    assert design != LOCAL_NET_DESIGN, "the uCons/uGen2 replacement did not match"
    return _expect_diagnostic(
        "two child outputs bound to the same local net is a second driver",
        ('dut', 'clkGen', 'has more than one driver'),
        design=design)


def run_declared_output_undriven_gets_own_implementation():
    """A declared output no child drives is driven by the
    container's own implementation."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container: exports a clock its own body produces"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            outClk: { direction: output }
    cons: { desc: "plain child", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uDut:   { container: top_tb, instanceType: dut,    instGroup: top,
              clocks: { outClk: ~ } }
    uCons:  { container: dut,    instanceType: cons,   instGroup: top }
"""
    # projectDomains='': top_tb declares nothing of its own (implicit
    # clk/rst_n only); PROJECT_DOMAINS' extra clkSlow would have nothing in
    # this design to consume it.
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains='')
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: a declared output with no driving child builds\n{output}")
            return False
        print("PASS: a declared output with no driving child builds clean "
              "(its own implementation is the driver)")
        return True
    finally:
        shutil.rmtree(fixture)


def run_local_net_cases():
    return all([
        run_local_net_positive_case(),
        run_local_net_no_consumer_rejected(),
        run_output_bound_to_container_input_rejected(),
        run_two_outputs_one_net_rejected(),
        run_declared_output_undriven_gets_own_implementation(),
    ])


# ------------------------------------------------- binding conformance --

def _binds_of(db_path, instanceName):
    """(childPort, parentSignal) pairs persisted for one instance."""
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    instanceKey = cur.execute(
        "SELECT instanceKey FROM instances WHERE instance = ?", (instanceName,)).fetchone()['instanceKey']
    binds = [(row['childPort'], row['parentSignal']) for row in cur.execute(
        "SELECT * FROM instanceClockResetBinds WHERE instanceKey = ?", (instanceKey,)).fetchall()]
    con.close()
    return binds


def _expect_bind(label, design, instanceName, expectedBind):
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains='')
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}: the build failed\n{output}")
            return False
        binds = _binds_of(db_path, instanceName)
        ok = expectedBind in binds
        print(f"{'PASS' if ok else 'FAIL'}: {label}"
              f"{'' if ok else f': {instanceName} binds {binds}, expected {expectedBind}'}")
        return ok
    finally:
        shutil.rmtree(fixture)


def run_rst_fallback_excludes_async_only_local_net():
    """A PLL wrapper supplies clkSys and a raw reset 'rstSysRaw_n' consumed
    only by a synchroniser's asynchronous input, so the raw reset releases
    nothing synchronously and is not a candidate for clkSys's selected reset.
    uCore's unmapped rst_n falls back to 'rstSys_n', the sole candidate."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    soc:
        desc: "container whose system clock and resets are local nets"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkRef: { }
        resets:
            rstRef_n: { clock: clkRef }
    clkGen:
        desc: "PLL wrapper"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            refClk:  { }
            clkCore: { direction: output }
        resets:
            rst_n:        { clock: refClk }
            rstCoreRaw_n: { clock: clkCore, direction: output }
    rstSync:
        desc: "reset synchroniser"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { }
        resets:
            rstIn_n:  { async: true }
            rstOut_n: { clock: clk, direction: output }
    core: { desc: "plain block", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }

instances:
    top_tb:   { container: top_tb, instanceType: top_tb, instGroup: top }
    uSoc:     { container: top_tb, instanceType: soc, instGroup: top,
                clocks: { clkRef: clk }, resets: { rstRef_n: rst_n } }
    uClkGen:  { container: soc, instanceType: clkGen, instGroup: top,
                clocks: { refClk: clkRef, clkCore: clkSys },
                resets: { rst_n: rstRef_n, rstCoreRaw_n: rstSysRaw_n } }
    uRstSys:  { container: soc, instanceType: rstSync, instGroup: top,
                clocks: { clk: clkSys },
                resets: { rstIn_n: rstSysRaw_n, rstOut_n: rstSys_n } }
    uCore:    { container: soc, instanceType: core, instGroup: top,
                clocks: { clk: clkSys } }
"""
    return _expect_bind(
        "the rst_n fallback skips a local reset consumed only by asynchronous inputs",
        design, 'uCore', ('rst_n', 'rstSys_n'))


def run_name_match_binds_local_net():
    """An unmapped input clock binds the container net of the same name,
    local nets included: 'cons' declares input clock 'clkDiv' and has no map,
    and 'uGen' drives the local net 'clkDiv'."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container: clkDiv is a local net of this block"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            sysClk: { default: true }
    gen:
        desc: "clock divider"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            clkDiv: { direction: output }
        resets: {}
    cons:
        desc: "consumer of the divided clock, bound by name"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkDiv: { }
        resets: {}

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uDut:   { container: top_tb, instanceType: dut,    instGroup: top,
              clocks: { sysClk: clk } }
    uGen:   { container: dut,    instanceType: gen,    instGroup: top,
              clocks: { clk: sysClk, clkDiv: clkDiv } }
    uCons:  { container: dut,    instanceType: cons,   instGroup: top }
"""
    return _expect_bind("an input clock binds a local net of the same name",
                        design, 'uCons', ('clkDiv', 'clkDiv'))


def run_input_reset_on_output_clock_rejected():
    """An input reset must belong to an input clock. 'leaf''s rst_n names its
    output clock 'clkGen', so the declaration is rejected."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    leaf:
        desc: "input reset on its own output clock"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { }
            clkGen: { direction: output }
        resets:
            rst_n: { clock: clkGen }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uLeaf:  { container: top_tb, instanceType: leaf, instGroup: top,
              clocks: { clkGen: ~ } }
"""
    return _expect_diagnostic(
        "an input reset on an output clock is rejected at declaration",
        ("'leaf'", "'rst_n'", "'clkGen'", 'an input reset must belong to an input clock'),
        design=design, projectDomains='')


def run_local_net_named_rst_n_rejected():
    """'dut' has no reset on its default clock, so the local net 'rst_n' its
    synchroniser drives becomes the default clock's selected reset. An
    undeclared rst_n is the alias of that reset, so the local net's name
    collides with it: the container would emit both `wire rst_n = rst_n;` and
    `wire rst_n;`."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container with no reset on its default clock"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        resets:
            rstAsync_n: { async: true }
    rsync:
        desc: "reset synchroniser"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { }
        resets:
            rstIn_n:  { async: true }
            rstOut_n: { clock: clk, direction: output }
    cons: { desc: "plain block", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uDut:   { container: top_tb, instanceType: dut, instGroup: top,
              resets: { rstAsync_n: rst_n } }
    uSync:  { container: dut, instanceType: rsync, instGroup: top,
              resets: { rstIn_n: rstAsync_n, rstOut_n: rst_n } }
    uCons:  { container: dut, instanceType: cons, instGroup: top,
              resets: { rst_n: rst_n } }
"""
    return _expect_diagnostic(
        "a local net named rst_n that becomes the default clock's selected reset is rejected",
        ("'dut'", 'rst_n is the alias of its default clock', 'for a local net'),
        design=design, projectDomains='')


def run_rst_fallback_onto_own_output_rejected():
    """'uGen''s own output reset drives 'rstSys_n', the sole reset on
    'sysClk', so the rst_n fallback would bind uGen's rst_n input to the
    reset uGen itself drives. That is rejected as the same binding by an
    explicit map is."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container whose only synchronous reset is a local net"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            sysClk: { default: true }
        resets:
            rstAsync_n: { async: true }
    gen:
        desc: "reset generator with a synchronous reset input of its own"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { }
        resets:
            rstAsync_n: { async: true }
            rst_n:      { clock: clk, default: true }
            rstOut_n:   { clock: clk, direction: output }
    cons: { desc: "plain block", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uDut:   { container: top_tb, instanceType: dut, instGroup: top,
              clocks: { sysClk: clk }, resets: { rstAsync_n: rst_n } }
    uGen:   { container: dut, instanceType: gen, instGroup: top,
              clocks: { clk: sysClk }, resets: { rstOut_n: rstSys_n } }
    uCons:  { container: dut, instanceType: cons, instGroup: top,
              resets: { rst_n: rstSys_n } }
"""
    return _expect_diagnostic(
        "the rst_n fallback onto the instance's own output reset is rejected",
        ("'uGen'", "'rst_n'", "'rstSys_n'", "'rstOut_n'", 'already drives'),
        design=design, projectDomains='')


RST_FALLBACK_CONTAINER = """blocks:
    top_tb: {{ desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    dut:
        desc: "container with only an asynchronous reset of its own"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            sysClk: {{ default: true }}
        resets:
            rstAsync_n: {{ async: true }}
    rsync:
        desc: "reset synchroniser"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: {{ }}
        resets:
            rstIn_n:  {{ async: true }}
            rstOut_n: {{ clock: clk, direction: output }}
    cons: {{ desc: "plain block", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}

instances:
    top_tb: {{ container: top_tb, instanceType: top_tb, instGroup: top }}
    uDut:   {{ container: top_tb, instanceType: dut, instGroup: top,
              clocks: {{ sysClk: clk }}, resets: {{ rstAsync_n: rst_n }} }}
    uPlain: {{ container: dut, instanceType: cons, instGroup: top }}
{extraInstances}"""


def run_rst_fallback_no_candidate_rejected():
    """'dut''s default clock sysClk has no synchronous reset, declared or
    local, so uPlain's rst_n fallback has nothing to bind. A map would have
    nothing on sysClk to name, so the diagnostic offers the other fixes; the
    ones it offers are then shown to build."""
    label = "the rst_n fallback onto a container clock with no reset candidate is rejected"
    needles = ("'uPlain'", "'sysClk'", "no synchronous reset of 'dut', declared or local, is on it",
               "declare a synchronous reset on 'sysClk' in block 'dut''s resets:",
               "have a child drive a local reset net on 'sysClk'",
               "declare `resets: {}` on block 'cons'",
               "declare 'rst_n' async: true on block 'cons' and map it in the instance's resets:")

    def check():
        fixture, project_path, db_path = _make_fixture(
            design=RST_FALLBACK_CONTAINER.format(extraInstances=''), projectDomains='')
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code == 0 or 'Traceback' in output:
            raise AssertionError(f"the build did not report a diagnostic.\n{output}")
        for needle in needles:
            if needle not in output:
                raise AssertionError(f"diagnostic does not mention '{needle}'.\n{output}")
        if 'map rst_n' in output.lower():
            raise AssertionError(
                f"the diagnostic offers a map of rst_n, but no reset is on "
                f"sysClk for it to name.\n{output}")
        return True
    results = [_run_case(label, check)]

    design = RST_FALLBACK_CONTAINER.format(extraInstances='')
    results.append(_expect_builds(
        "declaring a synchronous reset on the container clock clears the empty rst_n fallback",
        design=design.replace(
            "            rstAsync_n: { async: true }\n    rsync:",
            "            rstAsync_n: { async: true }\n"
            "            rstSys_n:   { clock: sysClk }\n    rsync:").replace(
            "resets: { rstAsync_n: rst_n } }", "resets: { rstAsync_n: rst_n, rstSys_n: rst_n } }"),
        projectDomains=''))
    results.append(_expect_builds(
        "resets: {} on the child clears the empty rst_n fallback",
        design=design.replace(
            'cons: { desc: "plain block", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }',
            'cons: { desc: "plain block", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false, resets: {} }'),
        projectDomains=''))
    results.append(_expect_builds(
        "an asynchronous rst_n mapped to a container reset clears the empty rst_n fallback",
        design=design.replace(
            'cons: { desc: "plain block", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }',
            'cons: { desc: "plain block", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false,\n'
            '            resets: { rst_n: { async: true } } }').replace(
            "instanceType: cons, instGroup: top }",
            "instanceType: cons, instGroup: top, resets: { rst_n: rstAsync_n } }"),
        projectDomains=''))
    return all(results)


# uSync drives the local reset rstL_n on sysClk, consumed only by uAsync's
# asynchronous input, so rstL_n is on sysClk but no fallback candidate.
ASYNC_ONLY_LOCAL_RESET = """    uSync:  { container: dut, instanceType: rsync, instGroup: top,
              clocks: { clk: sysClk }, resets: { rstIn_n: rstAsync_n, rstOut_n: rstL_n } }
    uAsync: { container: dut, instanceType: acons, instGroup: top, resets: { rstIn_n: rstL_n } }
"""


def _with_async_consumer(design):
    return design.replace(
        '    cons: { desc: "plain block"',
        '    acons:\n'
        '        desc: "block with only an asynchronous reset"\n'
        '        hasVl: false\n'
        '        hasMdl: false\n'
        '        hasTb: false\n'
        '        hasRtl: false\n'
        '        resets:\n'
        '            rstIn_n: { async: true }\n'
        '    cons: { desc: "plain block"')


def run_rst_fallback_async_only_local_net_rejected():
    """The only reset on sysClk is a local net consumed only by an
    asynchronous input, which the rst_n fallback does not select. The
    diagnostic says so and offers a map to it, which then builds."""
    design = _with_async_consumer(
        RST_FALLBACK_CONTAINER.format(extraInstances=ASYNC_ONLY_LOCAL_RESET))
    results = [_expect_diagnostic(
        "the rst_n fallback onto a clock whose only reset is consumed asynchronously is rejected",
        ("'uPlain'", "'sysClk'",
         "the only resets on it are local nets (rstL_n) consumed only by "
         "asynchronous reset inputs",
         "map rst_n to rstL_n in the instance's resets:"),
        design=design, projectDomains='')]
    results.append(_expect_builds(
        "mapping rst_n to the asynchronously consumed local reset builds",
        design=design.replace(
            "    uPlain: { container: dut, instanceType: cons, instGroup: top }",
            "    uPlain: { container: dut, instanceType: cons, instGroup: top,\n"
            "              resets: { rst_n: rstL_n } }"),
        projectDomains=''))
    return all(results)


TOP_RST_ON_RESETLESS_CLOCK = """blocks:
    top_tb:
        desc: "testbench container whose rst_n is on a clock with no testbench reset"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkA: { default: true }
            clk:  { }
        resets:
            rstA_n: { clock: clkA }
            rst_n:  { {rstBody} }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top{topMap} }
"""

TOP_RST_ON_RESETLESS_CLOCK_PROJECT = """
clocks:
    clkA: { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    clk:  { desc: "a second clock", period: 3, timeUnit: ns }

resets:
    rstA_n: { desc: "the default reset", default: true, clock: clkA }
{extraReset}"""


# uGsync's own output drives the local reset rstL_n on sysClk, consumed only
# by uAsync's asynchronous input; uGsync's synchronous rst_n, which authors
# clock:, falls back onto sysClk and finds no candidate.
RST_FALLBACK_SELF_DRIVEN = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container with only an asynchronous reset of its own"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            sysClk: { default: true }
        resets:
            rstAsync_n: { async: true }
    gsync:
        desc: "reset synchroniser with a synchronous reset input of its own"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { }
        resets:
            rstIn_n:  { async: true }
            rst_n:    { {rstBody} }
            rstOut_n: { clock: clk, direction: output, default: true }
    acons:
        desc: "block with only an asynchronous reset"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        resets:
            rstIn_n: { async: true }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uDut:   { container: top_tb, instanceType: dut, instGroup: top,
              clocks: { sysClk: clk }, resets: { rstAsync_n: rst_n } }
    uGsync: { container: dut, instanceType: gsync, instGroup: top,
              clocks: { clk: sysClk }, resets: { rstIn_n: rstAsync_n, rstOut_n: rstL_n{gsyncMap} } }
    uAsync: { container: dut, instanceType: acons, instGroup: top, resets: { rstIn_n: rstL_n } }
"""

# uCons's clock is bound to dut's declared output clock clkO, which uGen
# drives and which has no reset.
RST_FALLBACK_OUTPUT_CLOCK = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container exporting an output clock with no reset"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            sysClk: { default: true }
            clkO:   { direction: output }
        resets:
            rstAsync_n: { async: true }
{outputReset}    gen:
        desc: "clock generator"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            clkOut: { direction: output }
        resets: { }
    cons: { desc: "plain block", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uDut:   { container: top_tb, instanceType: dut, instGroup: top,
              clocks: { sysClk: clk, clkO: ~ }, resets: { rstAsync_n: rst_n{outputResetMap} } }
    uGen:   { container: dut, instanceType: gen, instGroup: top,
              clocks: { clk: sysClk, clkOut: clkO } }
    uCons:  { container: dut, instanceType: cons, instGroup: top, clocks: { clk: clkO } }
"""


def run_rst_fallback_offered_fix_cases():
    """The fixes an empty rst_n fallback offers: no map onto a net the
    instance itself drives, an output reset on a container output clock, and
    removing clock: when making an rst_n that authors one asynchronous. Each
    offered fix is then shown to build."""
    def selfDriven(rstBody='clock: clk', gsyncMap=''):
        return (RST_FALLBACK_SELF_DRIVEN.replace('{rstBody}', rstBody)
                .replace('{gsyncMap}', gsyncMap))

    def selfDrivenCheck():
        fixture, project_path, db_path = _make_fixture(design=selfDriven(), projectDomains='')
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code == 0 or 'Traceback' in output:
            raise AssertionError(f"the build did not report a diagnostic.\n{output}")
        for needle in ("'uGsync'", "the only resets on it are local nets (rstL_n)",
                       "declare 'rst_n' async: true on block 'gsync' and remove its "
                       "clock:, then map it in the instance's resets:"):
            if needle not in output:
                raise AssertionError(f"diagnostic does not mention '{needle}'.\n{output}")
        if 'map rst_n to rstL_n' in output:
            raise AssertionError(
                f"the diagnostic offers to map rst_n onto rstL_n, which uGsync "
                f"itself drives.\n{output}")
        return True

    def outputClock(outputReset='', outputResetMap=''):
        return (RST_FALLBACK_OUTPUT_CLOCK.replace('{outputReset}', outputReset)
                .replace('{outputResetMap}', outputResetMap))

    return all([
        _run_case("the rst_n fallback does not offer a map onto a net the "
                  "instance drives", selfDrivenCheck),
        _expect_builds(
            "an asynchronous rst_n with its clock: removed and mapped clears the "
            "empty rst_n fallback",
            design=selfDriven(rstBody='async: true', gsyncMap=', rst_n: rstAsync_n'),
            projectDomains=''),
        _expect_diagnostic(
            "the rst_n fallback onto a container output clock offers an output reset",
            ("'uCons'", "'clkO'",
             "declare a synchronous `direction: output` reset on 'clkO' in "
             "block 'dut''s resets:"),
            design=outputClock(), projectDomains=''),
        _expect_builds(
            "a synchronous output reset on the container output clock clears the "
            "empty rst_n fallback",
            design=outputClock(
                outputReset="            rstO_n: { clock: clkO, direction: output }\n",
                outputResetMap=', rstO_n: ~'),
            projectDomains=''),
    ])


def run_top_rst_fallback_no_testbench_reset_rejected():
    """top_tb's rst_n is on clk, which has no testbench reset. Mapping rst_n
    synchronously cannot help, since every testbench reset is on clkA, so the
    diagnostic offers a testbench reset on clk or an asynchronous rst_n; both
    then build. The asynchronous fix is applied as the diagnostic states it,
    to the rejected rst_n's own fields."""
    rstFields = ['clock: clk']

    def design(fields=rstFields, topMap=''):
        return (TOP_RST_ON_RESETLESS_CLOCK.replace('{rstBody}', ', '.join(fields))
                .replace('{topMap}', topMap))

    def project(extraReset=''):
        return TOP_RST_ON_RESETLESS_CLOCK_PROJECT.replace('{extraReset}', extraReset)

    label = "the top rst_n fallback onto a testbench clock with no reset is rejected"
    needles = ("'top_tb'", "testbench clock 'clk'", 'that clock has no testbench reset',
               "Declare a reset on 'clk' in the project file's resets:",
               "declare 'rst_n' async: true on block 'top_tb' and remove its "
               "clock:, then map it in the topInstance's resets:")

    def check():
        fixture, project_path, db_path = _make_fixture(design=design(), projectDomains=project())
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code == 0 or 'Traceback' in output:
            raise AssertionError(f"the build did not report a diagnostic.\n{output}")
        for needle in needles:
            if needle not in output:
                raise AssertionError(f"diagnostic does not mention '{needle}'.\n{output}")
        if 'map rst_n' in output.lower():
            raise AssertionError(
                f"the diagnostic offers a map of rst_n, which fails the testbench "
                f"reset clock check.\n{output}")
        return True
    results = [_run_case(label, check)]
    results.append(_expect_builds(
        "a testbench reset on the clock clears the top rst_n fallback",
        design=design(),
        projectDomains=project('    rstB_n: { desc: "reset of clk", clock: clk }\n')))
    results.append(_expect_builds(
        "an asynchronous top rst_n mapped to a testbench reset clears the top rst_n fallback",
        design=design(fields=[field for field in rstFields if field != 'clock: clk']
                      + ['async: true'],
                      topMap=', resets: { rst_n: rstA_n }'),
        projectDomains=project()))
    results.append(_expect_diagnostic(
        "an asynchronous top rst_n that keeps its clock: is rejected",
        ("'rst_n'", "declares both async: true and clock: 'clk'"),
        design=design(fields=rstFields + ['async: true'], topMap=', resets: { rst_n: rstA_n }'),
        projectDomains=project()))
    return all(results)


def run_rst_fallback_several_local_candidates_rejected():
    """Two synchronisers drive local resets rstA_n and rstB_n on dut's default
    clock sysClk, so uPlain's rst_n fallback is ambiguous, and so is dut's own
    rst_n. A map would clear only uPlain's, so the diagnostic lists both nets
    with their drivers and offers only a declared reset marked default: true.
    On a clock other than the default the map is offered, and builds."""
    extraInstances = """    uSyncA: { container: dut, instanceType: rsync, instGroup: top,
              clocks: { clk: sysClk }, resets: { rstIn_n: rstAsync_n, rstOut_n: rstA_n } }
    uSyncB: { container: dut, instanceType: rsync, instGroup: top,
              clocks: { clk: sysClk }, resets: { rstIn_n: rstAsync_n, rstOut_n: rstB_n } }
    uConsA: { container: dut, instanceType: cons, instGroup: top, resets: { rst_n: rstA_n } }
    uConsB: { container: dut, instanceType: cons, instGroup: top, resets: { rst_n: rstB_n } }
"""
    label = "the rst_n fallback onto several local reset candidates is rejected"
    needles = ("'uPlain'", "default clock 'sysClk'",
               "local reset net 'rstA_n' (driven by instance 'uSyncA') and local "
               "reset net 'rstB_n' (driven by instance 'uSyncB')",
               "The block's rst_n, used by its default-clock flops",
               "Declare a synchronous reset on 'sysClk' marked default: true in "
               "block 'dut''s resets:.")

    def check():
        fixture, project_path, db_path = _make_fixture(
            design=RST_FALLBACK_CONTAINER.format(extraInstances=extraInstances),
            projectDomains='')
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code == 0 or 'Traceback' in output:
            raise AssertionError(f"the build did not report a diagnostic.\n{output}")
        for needle in needles:
            if needle not in output:
                raise AssertionError(f"diagnostic does not mention '{needle}'.\n{output}")
        if 'map rst_n' in output.lower():
            raise AssertionError(
                f"the diagnostic offers a map of rst_n, which leaves dut's own "
                f"rst_n unselected.\n{output}")
        return True

    # The same candidates on a second, non-default clock slowClk.
    slow = (RST_FALLBACK_CONTAINER.format(extraInstances=extraInstances.replace(
                'clocks: { clk: sysClk }', 'clocks: { clk: slowClk }')
                .replace("instanceType: cons, instGroup: top, resets:",
                         "instanceType: cons, instGroup: top, clocks: { clk: slowClk }, resets:"))
            .replace("            sysClk: { default: true }\n",
                     "            sysClk: { default: true }\n            slowClk: { }\n")
            .replace("clocks: { sysClk: clk }", "clocks: { sysClk: clk, slowClk: clk }"))
    slowPlain = ("uPlain: { container: dut, instanceType: cons, instGroup: top }",
                 "uPlain: { container: dut, instanceType: cons, instGroup: top, "
                 "clocks: { clk: slowClk }{resets} }")
    return all([
        _run_case(label, check),
        _expect_diagnostic(
            "the rst_n fallback onto several local candidates on a non-default clock offers a map",
            ("'uPlain'", "'slowClk'", '2 reset candidates (rstA_n, rstB_n)',
             "Map rst_n to one of them in the instance's resets:."),
            design=slow.replace(slowPlain[0], slowPlain[1].replace('{resets}', '')),
            projectDomains=''),
        _expect_builds(
            "mapping rst_n on the non-default clock builds",
            design=slow.replace(slowPlain[0], slowPlain[1].replace(
                '{resets}', ', resets: { rst_n: rstA_n }')),
            projectDomains=''),
    ])


def run_sync_consumer_of_unclocked_local_reset_rejected():
    """uGen's output clock is bound to `~`, so the local reset rstGen_n it
    drives on that clock is released on no clock of 'dut'. uCons binds its
    synchronous rstGen_n to it by name match, which is rejected."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            sysClk: { default: true }
        resets:
            rstSys_n: { clock: sysClk }
    gen:
        desc: "clock generator with a reset on its own output clock"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            clkOut: { direction: output }
        resets:
            rst_n:    { clock: clk }
            rstGen_n: { clock: clkOut, direction: output }
    cons:
        desc: "synchronous consumer bound by name"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { default: true }
        resets:
            rstGen_n: { clock: clk }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uDut:   { container: top_tb, instanceType: dut, instGroup: top,
              clocks: { sysClk: clk }, resets: { rstSys_n: rst_n } }
    uGen:   { container: dut, instanceType: gen, instGroup: top,
              clocks: { clkOut: ~ }, resets: { rstGen_n: rstGen_n } }
    uCons:  { container: dut, instanceType: cons, instGroup: top }
"""
    return _expect_diagnostic(
        "a synchronous consumer of a local reset whose clock is bound to ~ is rejected",
        ("'uCons'", "'rstGen_n'", "'uGen'", "'clkOut' is bound to `~`",
         'only an asynchronous reset input may consume it'),
        design=design, projectDomains='')


# uGsync's rst_n falls back onto sysClk, whose candidates include local
# resets uGsync itself drives, each consumed synchronously by a uCons
# instance. `{dutResets}` extends dut's resets, `{topResets}` uDut's reset
# map, `{gsyncOutputs}` gsync's output resets, `{gsyncMap}` uGsync's reset
# map, and `{consumers}` holds the uCons instances.
RST_FALLBACK_SELF_DRIVEN_CANDIDATES = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            sysClk: { default: true }
        resets:
            rstAsync_n: { async: true }
{dutResets}    gsync:
        desc: "reset synchroniser with a synchronous reset input of its own"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { }
        resets:
            rstIn_n: { async: true }
            rst_n:   { clock: clk }
{gsyncOutputs}    cons: { desc: "plain block", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uDut:   { container: top_tb, instanceType: dut, instGroup: top,
              clocks: { sysClk: clk }, resets: { rstAsync_n: rst_n{topResets} } }
    uGsync: { container: dut, instanceType: gsync, instGroup: top,
              clocks: { clk: sysClk }, resets: { rstIn_n: rstAsync_n{gsyncMap} } }
{consumers}"""


def _self_driven_candidates(dutResets='', topResets='', gsyncOutputs='', gsyncMap='',
                            consumers=''):
    return (RST_FALLBACK_SELF_DRIVEN_CANDIDATES.replace('{dutResets}', dutResets)
            .replace('{topResets}', topResets).replace('{gsyncOutputs}', gsyncOutputs)
            .replace('{gsyncMap}', gsyncMap).replace('{consumers}', consumers))


def _expect_diagnostic_without(label, needles, absent, **fixtureKwargs):
    """As _expect_diagnostic, and the output must not mention `absent`."""
    def check():
        fixture, project_path, db_path = _make_fixture(**fixtureKwargs)
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code == 0 or 'Traceback' in output:
            raise AssertionError(f"the build did not report a diagnostic.\n{output}")
        for needle in needles:
            if needle not in output:
                raise AssertionError(f"diagnostic does not mention '{needle}'.\n{output}")
        if absent in output:
            raise AssertionError(f"diagnostic offers '{absent}', which cannot clear it.\n{output}")
        return True
    return _run_case(label, check)


def run_rst_fallback_self_driven_candidates_cases():
    """The several-candidates rst_n fallback on the container's default clock
    offers no map, since dut's own rst_n would stay unselected. It offers
    marking the declared reset default: true, or, where the only candidates
    are resets the instance drives, declaring one. Each offered fix is then
    shown to build."""
    oneOutput = "            rstOut_n: { clock: clk, direction: output, default: true }\n"
    twoOutputs = ("            rstOutA_n: { clock: clk, direction: output, default: true }\n"
                  "            rstOutB_n: { clock: clk, direction: output }\n")
    declaredReset = "            rstD_n:     { clock: sysClk{marking} }\n"
    partial = dict(dutResets=declaredReset.replace('{marking}', ''),
                   topResets=', rstD_n: rst_n', gsyncOutputs=oneOutput,
                   gsyncMap=', rstOut_n: rstL_n',
                   consumers="    uCons:  { container: dut, instanceType: cons, instGroup: top, "
                             "resets: { rst_n: rstL_n } }\n")
    every = dict(gsyncOutputs=twoOutputs,
                 gsyncMap=', rstOutA_n: rstLA_n, rstOutB_n: rstLB_n',
                 consumers="    uConsA: { container: dut, instanceType: cons, instGroup: top, "
                           "resets: { rst_n: rstLA_n } }\n"
                           "    uConsB: { container: dut, instanceType: cons, instGroup: top, "
                           "resets: { rst_n: rstLB_n } }\n")
    return all([
        _expect_diagnostic_without(
            "the several-candidates rst_n fallback on the default clock offers "
            "marking the declared reset, not a map",
            ("'uGsync'", "default clock 'sysClk'",
             "declared reset 'rstD_n' and local reset net 'rstL_n' (driven by "
             "instance 'uGsync')",
             "none is selected because neither is marked default: true",
             "Mark 'rstD_n' default: true in block 'dut''s resets:."),
            "map rst_n",
            design=_self_driven_candidates(**partial), projectDomains=''),
        _expect_builds(
            "marking the declared candidate default: true builds",
            design=_self_driven_candidates(**dict(partial, dutResets=declaredReset.replace(
                '{marking}', ', default: true'))),
            projectDomains=''),
        _expect_diagnostic_without(
            "the several-candidates rst_n fallback onto resets the instance "
            "alone drives offers no map",
            ("'uGsync'", "default clock 'sysClk'",
             "local reset net 'rstLA_n' (driven by instance 'uGsync') and local "
             "reset net 'rstLB_n' (driven by instance 'uGsync')",
             "only a declared reset can be marked default: true",
             "Declare a synchronous reset on 'sysClk' marked default: true in "
             "block 'dut''s resets:."),
            "map rst_n",
            design=_self_driven_candidates(**every), projectDomains=''),
        _expect_builds(
            "a declared reset marked default: true on the clock clears it",
            design=_self_driven_candidates(**dict(
                every, dutResets=declaredReset.replace('{marking}', ', default: true'),
                topResets=', rstD_n: rst_n')),
            projectDomains=''),
    ])


def run_rst_fallback_self_driven_candidates_non_default_clock_cases():
    """The self-driven candidates moved onto dut's second, non-default clock
    slowClk. With a declared candidate beside the one uGsync drives, the
    diagnostic names the self-driven one and offers the declared reset as a
    map target and for marking default: true. When uGsync drives every
    candidate, none can be its rst_n."""
    def onSlowClk(**parts):
        return (_self_driven_candidates(**parts)
                .replace("            sysClk: { default: true }\n",
                         "            sysClk: { default: true }\n            slowClk: { }\n")
                .replace("clocks: { sysClk: clk }", "clocks: { sysClk: clk, slowClk: clk }")
                .replace("clocks: { clk: sysClk }", "clocks: { clk: slowClk }")
                .replace("instanceType: cons, instGroup: top, resets:",
                         "instanceType: cons, instGroup: top, clocks: { clk: slowClk }, resets:"))
    oneOutput = "            rstOut_n: { clock: clk, direction: output, default: true }\n"
    twoOutputs = ("            rstOutA_n: { clock: clk, direction: output, default: true }\n"
                  "            rstOutB_n: { clock: clk, direction: output }\n")
    partial = dict(dutResets="            rstD_n:     { clock: slowClk }\n",
                   topResets=', rstD_n: rst_n', gsyncOutputs=oneOutput,
                   gsyncMap=', rstOut_n: rstL_n',
                   consumers="    uCons:  { container: dut, instanceType: cons, instGroup: top, "
                             "resets: { rst_n: rstL_n } }\n")
    every = dict(gsyncOutputs=twoOutputs,
                 gsyncMap=', rstOutA_n: rstLA_n, rstOutB_n: rstLB_n',
                 consumers="    uConsA: { container: dut, instanceType: cons, instGroup: top, "
                           "resets: { rst_n: rstLA_n } }\n"
                           "    uConsB: { container: dut, instanceType: cons, instGroup: top, "
                           "resets: { rst_n: rstLB_n } }\n")
    return all([
        _expect_diagnostic(
            "a self-driven rst_n candidate on a non-default clock is named, and "
            "the declared one is offered",
            ("'uGsync'", "container clock 'slowClk'",
             "and the instance itself drives rstL_n",
             "map rst_n to rstD_n in the instance's resets:",
             "mark one of the declared resets (rstD_n) default: true"),
            design=onSlowClk(**partial), projectDomains=''),
        _expect_diagnostic(
            "rst_n candidates on a non-default clock that the instance alone "
            "drives cannot be its rst_n",
            ("'uGsync'", "container clock 'slowClk'",
             "and the instance itself drives every one of them, so none can be "
             "its rst_n"),
            design=onSlowClk(**every), projectDomains=''),
    ])


def run_rst_fallback_async_map_suppressed_when_only_self_driven():
    """dut declares no reset, and the only reset net in it is the local
    rstL_n that uGsync itself drives. The fallback diagnostic cannot offer
    an asynchronous rst_n mapped in the instance's resets:, since the only
    net it could name is self-driven."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container declaring no reset"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            sysClk: { default: true }
        resets: { }
    gsync:
        desc: "block with a synchronous reset input and an output reset"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { }
        resets:
            rst_n:    { clock: clk }
            rstOut_n: { clock: clk, direction: output, default: true }
    acons:
        desc: "block with only an asynchronous reset"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        resets:
            rstIn_n: { async: true }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uDut:   { container: top_tb, instanceType: dut, instGroup: top, clocks: { sysClk: clk } }
    uGsync: { container: dut, instanceType: gsync, instGroup: top,
              clocks: { clk: sysClk }, resets: { rstOut_n: rstL_n } }
    uAsync: { container: dut, instanceType: acons, instGroup: top, resets: { rstIn_n: rstL_n } }
"""
    return _expect_diagnostic_without(
        "the rst_n fallback does not offer an asynchronous map when every "
        "reset net is self-driven",
        ("'uGsync'", "the only resets on it are local nets (rstL_n)",
         "declare a synchronous reset on 'sysClk' in block 'dut''s resets:",
         "remove 'rst_n' from block 'gsync''s resets:"),
        "async: true on block",
        design=design, projectDomains='')

def run_binding_conformance_cases():
    return all([
        run_rst_fallback_excludes_async_only_local_net(),
        run_name_match_binds_local_net(),
        run_input_reset_on_output_clock_rejected(),
        run_local_net_named_rst_n_rejected(),
        run_rst_fallback_onto_own_output_rejected(),
        run_top_rst_fallback_several_testbench_resets_rejected(),
        run_top_rst_fallback_no_testbench_reset_rejected(),
        run_rst_fallback_no_candidate_rejected(),
        run_rst_fallback_async_only_local_net_rejected(),
        run_rst_fallback_offered_fix_cases(),
        run_rst_fallback_several_local_candidates_rejected(),
        run_rst_fallback_self_driven_candidates_cases(),
        run_rst_fallback_self_driven_candidates_non_default_clock_cases(),
        run_rst_fallback_async_map_suppressed_when_only_self_driven(),
        run_sync_consumer_of_unclocked_local_reset_rejected(),
    ])


# ------------------------------------------------------------ clockless rows --

# A container boundary port bridged inward to a child by one connectionMaps
# row; `{mapClock}` is appended to that row.
CONNECTION_MAP_DESIGN = """types:
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
    top_tb: {{ desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    prod:   {{ desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    dut:
        desc: "container bridging its boundary port to a child"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        ports:
            inP: {{ interface: dataIf, direction: dst }}
    cons:   {{ desc: "consumer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}

instances:
    top_tb: {{ container: top_tb, instanceType: top_tb, instGroup: top }}
    uProd:  {{ container: top_tb, instanceType: prod, instGroup: top }}
    uDut:   {{ container: top_tb, instanceType: dut,  instGroup: top }}
    uCons:  {{ container: dut,    instanceType: cons, instGroup: top }}

connections:
    - {{ interface: dataIf, src: uProd, srcport: out, dst: uDut, dstport: inP }}

connectionMaps:
    - {{ interface: dataIf, block: dut, direction: dst, instance: uCons, port: inP, instancePort: in{mapClock} }}
"""


def run_clockless_row_cases():
    """A connectionMaps, memoryConnections or registerConnections row may not
    author clock:. Each fixture first builds clean without it, so the failure
    is the clock: field's alone."""
    def expectRejected(section, build, cleanDesign, clockDesign):
        def check():
            for design, mustFail in ((cleanDesign, False), (clockDesign, True)):
                fixture, project_path, db_path = build(design)
                try:
                    code, output = _build(project_path, db_path)
                finally:
                    shutil.rmtree(fixture)
                if not mustFail:
                    if code != 0:
                        raise AssertionError(f"the fixture without clock: fails to build\n{output}")
                    continue
                if code == 0:
                    raise AssertionError(f"build succeeded; it must fail.\n{output}")
                if 'Traceback' in output:
                    raise AssertionError(
                        f"the build crashed instead of reporting a diagnostic.\n{output}")
                for needle in (f"section {section}", 'Remove the clock: field'):
                    if needle not in output:
                        raise AssertionError(
                            f"diagnostic does not mention '{needle}', so the author is "
                            f"not pointed at what to fix.\n{output}")
            return True
        return _run_case(f"a {section} row authoring clock: is rejected", check)

    def buildDomains(design):
        return _make_fixture(design=design, projectDomains='')

    def buildRegDecode(design):
        return regdecode._make_fixture(design)

    objectAccess = regdecode.OBJECT_ACCESS
    memClock = objectAccess.replace("instance: uMemAccessor, port: p }",
                                    "instance: uMemAccessor, port: p, clock: objClk }")
    assert memClock != objectAccess, "the memoryConnections replacement did not match"
    regClock = objectAccess.replace("instance: uRegAccessor }",
                                    "instance: uRegAccessor, clock: objClk }")
    assert regClock != objectAccess, "the registerConnections replacement did not match"
    return all([
        expectRejected('connectionMaps', buildDomains,
                       CONNECTION_MAP_DESIGN.format(mapClock=''),
                       CONNECTION_MAP_DESIGN.format(mapClock=', clock: clk')),
        expectRejected('memoryConnections', buildRegDecode, objectAccess, memClock),
        expectRejected('registerConnections', buildRegDecode, objectAccess, regClock),
    ])


# --------------------------------------------- single-domain object rules --

# A memory owner (implicit clk) and one hardware accessor, so the rule that a
# memoryConnections: accessor must be in the memory's own domain can be driven
# through a real build rather than by hand: the rule reads the accessor's own
# resolved container clock, which only a real instance bind produces.
MEMORY_ACCESS_DESIGN = """types:
    dataT: {{ width: 8, desc: "payload word" }}
    memAddrT: {{ width: 3, desc: "memory address" }}

structures:
    memSt:
        data: {{ varType: dataT, desc: "memory payload" }}
    memAddrSt:
        address: {{ varType: memAddrT, desc: "memory address" }}

blocks:
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:     {{ default: true }}
            clkSlow: {{ }}
        resets:
            rst_n:     {{ clock: clk }}
            rstSlow_n: {{ clock: clkSlow }}
    memOwner: {{ desc: "memory owner", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    accessor:
        desc: "hardware accessor"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
{accessorClocks}
instances:
    top_tb:    {{ container: top_tb, instanceType: top_tb,   instGroup: top }}
    uMemOwner: {{ container: top_tb, instanceType: memOwner, instGroup: top }}
    uAccessor: {{ container: top_tb, instanceType: accessor, instGroup: top }}

memories:
    - {{ memory: tbl, block: memOwner, structure: memSt, addressStruct: memAddrSt, wordLines: 4, ports: [p], desc: "table" }}

memoryConnections:
    - {{ memory: tbl, block: memOwner, instance: uAccessor, port: p }}
"""


def run_single_domain_cases():
    results = []

    def memory_accessor_same_domain_accepted():
        design = MEMORY_ACCESS_DESIGN.format(accessorClocks='')
        fixture, project_path, db_path = _make_fixture(design=design)
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code != 0:
            raise AssertionError(
                f"a memory accessor in the memory's own domain (both implicit "
                f"clk) was rejected:\n{output}")
        return True

    results.append(_expect_diagnostic(
        "a memory accessor in a different domain than the memory is rejected",
        ('uAccessor', 'tbl', 'memOwner', 'clkSlow', 'clk',
         "must be in the memory's own domain"),
        design=MEMORY_ACCESS_DESIGN.format(
            accessorClocks="        clocks:\n"
                          "            clkSlow: { }\n"
                          "        resets:\n"
                          "            rstSlow_n: { clock: clkSlow }\n")))

    results.append(_run_case("a memory accessor in the memory's own domain is accepted",
                             memory_accessor_same_domain_accepted))

    # A router is single-clock: one clock of any name builds, and a second
    # declared clock is rejected by name whichever clock is the bus clock.
    # Only the rule is asserted, not the wording of its fix.
    def routerDesign(routerClocks, routerMap):
        design = (BRIDGE_DESIGN % ('', '\n            rstPix_n: { clock: clkPix }',
                                   ', rstPix_n: rstPix_n', BRIDGE_ONE_MEMORY_ROW % ''))
        return design.replace(
            ROUTER_HEADER, ROUTER_HEADER + "        clocks:\n" + routerClocks).replace(
            "uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top }",
            "uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top, "
            f"clocks: {{ {routerMap} }} }}")

    results.append(_expect_builds(
        "a router with one clock of its own name is accepted",
        design=routerDesign("            clkBus: { }\n", "clkBus: clk"),
        projectDomains=BRIDGE_PROJECT_DOMAINS))
    results.append(_expect_diagnostic(
        "a router resolving to two clocks is rejected by name",
        ("Register-decode router block 'apbDecode' declares more than one clock "
         "('clk', 'clkSlow'). A router is a single-domain module",
         "Found 1 Error."),
        design=routerDesign("            clk:     { default: true }\n"
                            "            clkSlow: { }\n", "clk: clk, clkSlow: clkPix"),
        projectDomains=BRIDGE_PROJECT_DOMAINS))
    results.append(_expect_diagnostic(
        "a two-clock router is rejected however the set is ordered",
        ("Register-decode router block 'apbDecode' declares more than one clock "
         "('clkSlow', 'clkPico').",
         "Found 1 Error."),
        design=routerDesign("            clkSlow: { default: true }\n"
                            "            clkPico: { }\n", "clkSlow: clk, clkPico: clkPix"),
        projectDomains=BRIDGE_PROJECT_DOMAINS))
    results.append(_expect_diagnostic(
        "a two-clock router is rejected when its bus clock is declared second",
        ("Register-decode router block 'apbDecode' declares more than one clock "
         "('clkSlow', 'clkBus').",
         "Found 1 Error."),
        design=routerDesign("            clkSlow: { default: true }\n"
                            "            clkBus:  { }\n"
                            "        resets:\n"
                            "            rst_n: { clock: clkBus }\n",
                            "clkSlow: clkPix, clkBus: clk").replace(
            "            registerDecoderPort: apbReg\n",
            "            registerDecoderPort: apbReg\n            clock: clkBus\n"),
        projectDomains=BRIDGE_PROJECT_DOMAINS))
    return all(results)


# ------------------------------------------ regAccess memory bridge reset --

# A router-served, TOP-DOWN leaf (no registerPorts:, so its register bus is
# resolved from the router dispatching to it),
# declaring its bus clock/reset under names OTHER than the handler's own
# implicit clk/rst_n (clkBus/rstBus_n, bound onto the project's clk/rst_n by
# an explicit instance map - a name match would fire on 'clk'/'rst_n', which
# is exactly what this fixture must not rely on), plus a second clock
# (clkPix) the memories: '%s' slot places one or more regAccess memories on,
# so a memory is served through the register handler's bridge. Four `%s`
# slots, substituted in order: top_tb's own extra
# resets (a case naming a second clkPix reset in its instance map needs a
# matching testbench reset for top_tb to bind it to), leafA's own extra
# resets, uLeafA's own instance resets: map extra entries, and the whole
# memories: row list. `%`-substituted rather than `.format()`-substituted:
# the design otherwise reads as ordinary YAML, with none of `.format()`'s
# braces to escape.
BRIDGE_DESIGN = """constants:
    ADDR_WIDTH: { value: 32, desc: "Register bus address width" }
    DATA_WIDTH: { value: 32, desc: "Register bus data width" }
    TBL_WORDS:  { value: 4, desc: "memory word count" }

types:
    apbAddrT: { width: ADDR_WIDTH, desc: "APB address" }
    apbDataT: { width: DATA_WIDTH, desc: "APB data" }
    dataT:    { width: 8, desc: "payload word" }
    memAddrT: { width: 3, desc: "memory address" }

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    memAddrSt:
        address: { varType: memAddrT, generator: address, desc: "memory address" }
    memSt:
        data: { varType: dataT, generator: memory, desc: "memory payload" }

interfaces:
    apbReg:
        desc: "APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }

blocks:
    top_tb:
        desc: "design top"
        hasMdl: true
        clocks:
            clk:    { default: true }
            clkPix: { }
        resets:
            rst_n:    { clock: clk }
            rstPix_n: { clock: clkPix }%s
    cpu:
        desc: "register-bus master"
        hasMdl: true
    apbDecode:
        desc: "Router block 'apbDecode'"
        hasMdl: true
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
    leafA:
        desc: "Top-down routed leaf owning a regAccess memory"
        hasMdl: true
        clocks:
            clkBus: { default: true }
            clkPix: { }
        resets:
            rstBus_n: { clock: clkBus }%s

instances:
    top_tb:     { container: top_tb, instanceType: top_tb,    instGroup: top }
    uCPU:       { container: top_tb, instanceType: cpu,       instGroup: top }
    uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top }
    uLeafA:     { container: top_tb, instanceType: leafA,     instGroup: top, addressGroup: top,
                  clocks: { clkBus: clk, clkPix: clkPix },
                  resets: { rstBus_n: rst_n%s } }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

memories:
%s"""

# One 'tbl' memory row on clkPix, for the single-memory bridge cases.
BRIDGE_ONE_MEMORY_ROW = (
    '    - { memory: tbl, block: leafA, structure: memSt, addressStruct: memAddrSt, '
    'wordLines: TBL_WORDS, ports: [p], regAccess: true, desc: "leafA regAccess table", '
    'clock: clkPix%s }\n')

BRIDGE_PROJECT_DOMAINS = """
clocks:
    clk:    { desc: "the default testbench clock", default: true, period: 1, timeUnit: ns }
    clkPix: { desc: "a second testbench clock", period: 2, timeUnit: ns }

resets:
    rst_n:    { desc: "the default reset", default: true, clock: clk }
    rstPix_n: { desc: "clkPix's reset", clock: clkPix }
"""


def run_regaccess_memory_bridge_clock_no_reset_rejected():
    """A regAccess memory served through the register handler's bridge needs
    a reset in its own domain for the bridge's memory side. leafA's own clkPix carries no reset at all,
    so the bridge the memory's 'clock: clkPix' would otherwise need has
    nothing to reset the memory-side logic with, and the build is rejected
    rather than silently generating an unreset bridge."""
    return _expect_diagnostic(
        "a regAccess memory bridged to a clock with no selected reset is "
        "rejected",
        ("The register handler's bridge to that memory", 'tbl', 'leafA', 'clkPix'),
        design=BRIDGE_DESIGN % ('', '', '', BRIDGE_ONE_MEMORY_ROW % ''),
        projectDomains=BRIDGE_PROJECT_DOMAINS)


def run_router_bus_on_output_clock_rejected():
    """A router consumes its register bus clock, so addressBlock: clock:
    naming one of the router's own output clocks is rejected."""
    design = (BRIDGE_DESIGN % ('', '\n            rstPix_n: { clock: clkPix }',
                               ', rstPix_n: rstPix_n', BRIDGE_ONE_MEMORY_ROW % ''))
    design = design.replace(
        """        desc: "Router block 'apbDecode'"
        hasMdl: true
""",
        """        desc: "Router block 'apbDecode'"
        hasMdl: true
        clocks:
            clkOut: { direction: output }
""").replace(
        "            registerDecoderPort: apbReg\n",
        "            registerDecoderPort: apbReg\n            clock: clkOut\n")
    return _expect_diagnostic(
        "a router bus clock that is an output clock of the router is rejected",
        ("Block 'apbDecode' addressBlock: names clock: 'clkOut', an output "
         "clock of 'apbDecode'. A router is clocked by the register bus it "
         "routes, so its clock must be direction: input.",
         "Make 'clkOut' an input clock of 'apbDecode', and its only clock."),
        design=design, projectDomains=BRIDGE_PROJECT_DOMAINS)


ROUTER_HEADER = """        desc: "Router block 'apbDecode'"
        hasMdl: true
"""


def run_router_bus_on_output_reset_rejected():
    """A router consumes its register bus reset, so addressBlock: reset:
    naming one of the router's own output resets is rejected, and is the
    only error reported."""
    design = (BRIDGE_DESIGN % ('', '\n            rstPix_n: { clock: clkPix }',
                               ', rstPix_n: rstPix_n', BRIDGE_ONE_MEMORY_ROW % ''))
    design = design.replace(
        ROUTER_HEADER,
        ROUTER_HEADER + """        resets:
            rst_n: { default: true }
            rstOut_n: { direction: output }
""").replace(
        "            registerDecoderPort: apbReg\n",
        "            registerDecoderPort: apbReg\n            reset: rstOut_n\n")
    return _expect_diagnostic(
        "a router bus reset that is an output reset of the router is rejected",
        ("Block 'apbDecode' addressBlock: names reset: 'rstOut_n', an output "
         "reset of 'apbDecode'. A router is reset by the register bus it "
         "routes, so its reset must be direction: input.",
         "Make 'rstOut_n' an input reset of 'apbDecode', or name an input "
         "reset in addressBlock: reset:.",
         "Found 1 Error."),
        design=design, projectDomains=BRIDGE_PROJECT_DOMAINS)


def run_router_bus_without_reset_rejected():
    """A router whose bus clock has no selected input reset is reported at
    the router, not as a leaf-side reset binding error: one with resets: {},
    and one whose selected reset is its own output reset."""
    direct = (BRIDGE_DESIGN % ('', '\n            rstPix_n: { clock: clkPix }',
                               ', rstPix_n: rstPix_n', BRIDGE_ONE_MEMORY_ROW % ''))
    outputSelected = direct.replace(
        ROUTER_HEADER, ROUTER_HEADER + """        resets:
            rstOut_n: { direction: output }
""").replace(
        "uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top }",
        "uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top, "
        "resets: { rstOut_n: ~ } }")
    return all([
        _expect_diagnostic_without(
            "a router with resets: {} serving a top-down leaf is reported at the router",
            ("Block 'apbDecode' addressBlock: runs its register bus on clock "
             "'clk', but 'clk' has no selected reset and addressBlock: names "
             "no reset:.",
             "so the router needs an input reset on 'clk'. Declare a "
             "synchronous input reset on 'clk' in 'apbDecode''s resets:.",
             "Found 1 Error."),
            "bound to the register bus's selected reset",
            design=direct.replace(ROUTER_HEADER, ROUTER_HEADER + "        resets: {}\n"),
            projectDomains=BRIDGE_PROJECT_DOMAINS),
        _expect_diagnostic_without(
            "a router whose bus clock's selected reset is an output reset is "
            "reported at the router",
            ("but the selected reset of 'clk' is 'rstOut_n', an output reset "
             "of 'apbDecode', and addressBlock: names no reset:.",
             "so the router needs an input reset on 'clk'. Declare an input "
             "reset on 'clk' in 'apbDecode''s resets: and mark it default: "
             "true, or name an input reset in addressBlock: reset:.",
             "Found 1 Error."),
            "bound to the register bus's selected reset",
            design=outputSelected, projectDomains=BRIDGE_PROJECT_DOMAINS),
    ])


def run_multi_clock_router_bus_reset_rejected_as_multi_clock():
    """A router with a second clock is reported as multi-clock even when its
    bus clock also has no selected reset, since the reset advice assumes a
    single-clock router."""
    design = (BRIDGE_DESIGN % ('', '\n            rstPix_n: { clock: clkPix }',
                               ', rstPix_n: rstPix_n', BRIDGE_ONE_MEMORY_ROW % ''))
    design = design.replace(
        ROUTER_HEADER, ROUTER_HEADER + """        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rstA_n: { clock: apbClk }
            rstB_n: { clock: apbClk }
""").replace(
        "            registerDecoderPort: apbReg\n",
        "            registerDecoderPort: apbReg\n            clock: apbClk\n").replace(
        "uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top }",
        "uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top, "
        "clocks: { clk: clkPix, apbClk: clk }, resets: { rstA_n: rst_n, rstB_n: rst_n } }")
    return _expect_diagnostic_without(
        "a two-clock router whose bus clock has no selected reset is reported "
        "as multi-clock",
        ("Register-decode router block 'apbDecode' declares more than one clock "
         "('clk', 'apbClk'). A router is a single-domain module clocked by the "
         "register bus it routes. Declare at most one clock in the router's "
         "'clocks:'.",
         "Found 1 Error."),
        "Declare a synchronous input reset",
        design=design, projectDomains=BRIDGE_PROJECT_DOMAINS)


def run_router_with_children_rejected():
    """A router's module is generated whole from its addressBlock:, so a
    router block containing instances is rejected: one plain child, and a
    child driving a local reset net another child consumes."""
    direct = (BRIDGE_DESIGN % ('', '\n            rstPix_n: { clock: clkPix }',
                               ', rstPix_n: rstPix_n', BRIDGE_ONE_MEMORY_ROW % ''))
    oneChild = direct.replace("    leafA:\n", """    sink:
        desc: "a child of the router"
        hasMdl: true
    leafA:
""").replace(
        "\nconnections:",
        "    uSink:      { container: apbDecode, instanceType: sink }\n\nconnections:")
    localNet = direct.replace(
        ROUTER_HEADER, ROUTER_HEADER + "        resets: {}\n").replace(
        "    leafA:\n", """    rstGen:
        desc: "drives a reset inside the router"
        hasMdl: true
        resets:
            rstO_n: { direction: output }
    sink:
        desc: "consumes the router's local reset net"
        hasMdl: true
    leafA:
""").replace(
        "\nconnections:",
        "    uRstGen:    { container: apbDecode, instanceType: rstGen, resets: { rstO_n: rstL_n } }\n"
        "    uSink:      { container: apbDecode, instanceType: sink, resets: { rst_n: rstL_n } }\n"
        "\nconnections:")
    tail = ("A router's module is generated entirely from its addressBlock:, "
            "so it cannot contain instances.")
    return all([
        _expect_diagnostic(
            "a router block containing one instance is rejected",
            ("Register-decode router block 'apbDecode' contains instance(s) 'uSink'.",
             tail, "Move 'uSink' into the container that instantiates 'apbDecode'.",
             "Found 1 Error."),
            design=oneChild, projectDomains=BRIDGE_PROJECT_DOMAINS),
        _expect_diagnostic(
            "a router block containing a local reset net's driver and consumer is rejected",
            ("Register-decode router block 'apbDecode' contains instance(s) "
             "'uRstGen', 'uSink'.",
             tail,
             "Move 'uRstGen', 'uSink' into the container that instantiates 'apbDecode'.",
             "Found 1 Error."),
            design=localNet, projectDomains=BRIDGE_PROJECT_DOMAINS),
    ])


def run_router_bus_async_reset_rejected():
    """addressBlock: reset: must be released on the router's bus clock, so
    an asynchronous reset, which belongs to no clock, is rejected."""
    design = (BRIDGE_DESIGN % ('', '\n            rstPix_n: { clock: clkPix }',
                               ', rstPix_n: rstPix_n', BRIDGE_ONE_MEMORY_ROW % ''))
    design = design.replace(
        ROUTER_HEADER, ROUTER_HEADER + """        resets:
            rst_n:  { }
            rstA_n: { async: true }
""").replace(
        "            registerDecoderPort: apbReg\n",
        "            registerDecoderPort: apbReg\n            reset: rstA_n\n").replace(
        "uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top }",
        "uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top, "
        "resets: { rstA_n: rst_n } }")
    return _expect_diagnostic(
        "a router bus reset that is an asynchronous reset is rejected",
        ("Block 'apbDecode' addressBlock: names reset: 'rstA_n', an "
         "asynchronous reset input belonging to no clock. A router's bus "
         "reset must belong to its bus clock 'clk'",
         "Name a reset of 'clk' in addressBlock: reset:, or remove reset: "
         "to use that clock's selected reset.",
         "Found 1 Error."),
        design=design, projectDomains=BRIDGE_PROJECT_DOMAINS)


def run_passthrough_register_ports_without_bus_reset_rejected():
    """A passthrough container that declares registerPorts: on a clock with
    two unmarked resets has no register-bus reset. That is reported at the
    container, not as the leaf behind it failing to bind the container's
    reset."""
    design = HASVL_PASSTHROUGH_BUS_PORT_DESIGN
    for old, new in (
            ("""            apbRst_n: { clock: apbClk }
    leafV:""", """            apbRst_n: { clock: apbClk }
        registerPorts:
            apbReg: { interface: apbReg, clock: clk }
    leafV:"""),
            ("""        desc: "top-down leaf behind the passthrough container"
        hasMdl: true
""", """        desc: "top-down leaf behind the passthrough container"
        hasMdl: true
        resets:
            rst_n: { }
        registerPorts:
            regs: { interface: apbReg, reset: rst_n }
"""),
            ("""                  clocks: { clkD: clk },
                  resets: { rstD_n: rst_n, rstAlt_n: rst_n } }""",
             """                  clocks: { clkD: clk, clk: apbClk },
                  resets: { rstD_n: rst_n, rst_n: apbRst_n, rstAlt_n: apbRst_n } }"""),
            ("clocks: { clk: apbClk }, resets: { rst_n: apbRst_n } }\n\nconnections",
             "clocks: { clk: clk }, resets: { rst_n: rst_n } }\n\nconnections")):
        design = design.replace(old, new)
    return _expect_diagnostic_without(
        "a passthrough container with registerPorts: and no bus reset is "
        "reported at the container",
        ("Block 'wrapV' hosts its register bus on clock 'clk', but that clock "
         "has no selected reset.",
         "Found 1 Error."),
        "not bound to the same container reset",
        design=design, projectDomains=HASVL_APB_PROJECT_DOMAINS)


def run_regaccess_memory_bridge_reset_declared_builds():
    """The positive shape: leafA declares a reset on clkPix, so the
    bridge has a memory-side reset and the build succeeds. The handler's
    ports carry the leaf's own clock/reset names, not the handler's own
    implicit clk/rst_n, so the persisted handler block ('leafA_regs')
    carries the bus pair (clkBus/rstBus_n) first, then the bridged
    clkPix/rstPix_n pair, in leafA's own declaration order; the handler
    instance's own binds mirror the same order onto the leaf's own nets, and
    busClockPort/busResetPort and clkPix's own selectedReset confirm which
    pair is the bus."""
    label = "a regAccess memory bridged to a clock with a declared reset builds"
    fixture, project_path, db_path = _make_fixture(
        design=BRIDGE_DESIGN % ('', '\n            rstPix_n: { clock: clkPix }',
                             ', rstPix_n: rstPix_n', BRIDGE_ONE_MEMORY_ROW % ''),
        projectDomains=BRIDGE_PROJECT_DOMAINS)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        clocks, resets = _clock_reset_rows(db_path, 'leafA_regs')
        failed = False
        if clocks != ['clkBus', 'clkPix'] or resets != ['rstBus_n', 'rstPix_n']:
            print(f"FAIL: {label}: leafA_regs persisted clocks={clocks}, "
                  f"resets={resets}, expected clocks=['clkBus', 'clkPix'], "
                  f"resets=['rstBus_n', 'rstPix_n'] (bus pair first, then "
                  f"the bridged pair)")
            failed = True
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        handlerBlockKey = cur.execute(
            "SELECT blockKey FROM blocks WHERE block = 'leafA_regs'").fetchone()['blockKey']
        clockRows = [dict(row) for row in cur.execute(
            "SELECT * FROM blockClocksResets WHERE blockKey = ? AND kind = 'clock' "
            "ORDER BY orderIndex", (handlerBlockKey,)).fetchall()]
        handlerInstanceKey = cur.execute(
            "SELECT instanceKey FROM instances WHERE instance = 'u_leafA_regs'").fetchone()['instanceKey']
        binds = [(row['childPort'], row['parentSignal']) for row in cur.execute(
            "SELECT * FROM instanceClockResetBinds WHERE instanceKey = ? "
            "ORDER BY orderIndex", (handlerInstanceKey,)).fetchall()]
        con.close()
        # rows() lists every clock bind before any reset bind, so the bus pair and the bridged pair each land in
        # their own clocks-then-resets group, bus port first in each.
        expectedOrder = [('clkBus', 'clkBus'), ('clkPix', 'clkPix'),
                         ('rstBus_n', 'rstBus_n'), ('rstPix_n', 'rstPix_n')]
        if binds != expectedOrder:
            print(f"FAIL: {label}: u_leafA_regs's own binds are {binds}, "
                  f"expected {expectedOrder} (bus port first within the "
                  f"clocks group and within the resets group)")
            failed = True
        busClockPorts = {row['busClockPort'] for row in clockRows}
        busResetPorts = {row['busResetPort'] for row in clockRows}
        if busClockPorts != {'clkBus'} or busResetPorts != {'rstBus_n'}:
            print(f"FAIL: {label}: leafA_regs's busClockPort/busResetPort "
                  f"are {busClockPorts}/{busResetPorts}, expected "
                  f"{{'clkBus'}}/{{'rstBus_n'}} on every clock row (the "
                  f"bus pair, not the bridged one)")
            failed = True
        clkPixRow = next(row for row in clockRows if row['itemKey'] == 'clkPix')
        if clkPixRow['selectedReset'] != 'rstPix_n':
            print(f"FAIL: {label}: leafA_regs's clkPix row carries "
                  f"selectedReset={clkPixRow['selectedReset']!r}, expected "
                  f"'rstPix_n' (the bridged reset for that clock, not the "
                  f"bus reset)")
            failed = True
        print(f"{'FAIL' if failed else 'PASS'}: {label}")
        return not failed
    finally:
        shutil.rmtree(fixture)


def run_regaccess_memory_bridge_conflicting_resets_rejected():
    """The register handler's bridge to one non-bus clock is one piece of
    generated logic with one reset, not one per memory. leafA declares two resets on
    clkPix (rstPix_n, default, and rstPix2_n); 'tblA' takes clkPix's default
    reset (rstPix_n) by leaving reset: unset, while 'tblB' names rstPix2_n
    explicitly, so the two memories bridged to the same clock disagree on
    which reset serves it, and the build is rejected rather than silently
    picking one."""
    twoMemoryRows = (
        '    - { memory: tblA, block: leafA, structure: memSt, addressStruct: memAddrSt, '
        'wordLines: TBL_WORDS, ports: [p], regAccess: true, desc: "leafA regAccess table A", '
        'clock: clkPix }\n'
        '    - { memory: tblB, block: leafA, structure: memSt, addressStruct: memAddrSt, '
        'wordLines: TBL_WORDS, ports: [p], regAccess: true, desc: "leafA regAccess table B", '
        'clock: clkPix, reset: rstPix2_n }\n')
    design = BRIDGE_DESIGN % (
        '\n            rstPix2_n: { clock: clkPix }',
        '\n            rstPix_n: { clock: clkPix, default: true }'
        '\n            rstPix2_n: { clock: clkPix }',
        ', rstPix_n: rstPix_n, rstPix2_n: rstPix2_n', twoMemoryRows)
    return _expect_diagnostic(
        "two regAccess memories bridged to the same clock resolving to "
        "different resets are rejected",
        ("The register handler's bridge to one clock has one reset",
         'leafA', 'clkPix', 'tblA', 'tblB', 'rstPix_n', 'rstPix2_n'),
        design=design,
        projectDomains=BRIDGE_PROJECT_DOMAINS + """    rstPix2_n: { desc: "clkPix's second reset", clock: clkPix }
""")


def run_memory_reset_names_wrong_clock_rejected():
    """A memory's reset: must name a reset belonging to the memory's own
    clock. 'tbl' is on clkPix but names 'rstBus_n', which belongs to clkBus,
    so the bridge would consume the bus reset for a clkPix memory instead of
    a clkPix reset, and the build is rejected."""
    return _expect_diagnostic(
        "a memory's reset: naming a reset of a different clock is rejected",
        ("A memory's reset: must belong to the memory's own clock",
         'tbl', 'leafA', 'rstBus_n', 'clkBus', 'clkPix'),
        design=BRIDGE_DESIGN % ('', '', '', BRIDGE_ONE_MEMORY_ROW % ', reset: rstBus_n'),
        projectDomains=BRIDGE_PROJECT_DOMAINS)


def run_memory_reset_names_async_reset_rejected():
    """An asynchronous reset input belongs to no clock, so it
    cannot be a memory's own-clock reset either. 'tbl' on clkPix names the
    async 'rstAsync_n' (mapped onto the container's existing rst_n net -
    binding is unaffected by clock membership, only the memory reset check
    cares), and the build is rejected the same way as a synchronous reset
    naming the wrong clock."""
    return _expect_diagnostic(
        "a memory's reset: naming an asynchronous reset is rejected",
        ("must name a reset belonging to the memory's own clock",
         'tbl', 'leafA', 'rstAsync_n', 'asynchronous'),
        design=BRIDGE_DESIGN % ('', '\n            rstAsync_n: { async: true }',
                             ', rstAsync_n: rst_n',
                             BRIDGE_ONE_MEMORY_ROW % ', reset: rstAsync_n'),
        projectDomains=BRIDGE_PROJECT_DOMAINS)


# ---------------------- register-bus port domain override (getBDPorts) --

# A reusable-IP hasVl leaf whose registerPorts: names its own clock and, to
# pick between two unmarked resets on it, its own reset: too: neither reset
# is marked default: true, so apbClk's shared selectedReset is None.
REGISTER_PORTS_RESET_DESIGN = """constants:
    ADDR_WIDTH: { value: 32, desc: "Register bus address width" }
    DATA_WIDTH: { value: 32, desc: "Register bus data width" }
    REG_WIDTH:  { value: 16, desc: "Register payload width" }

types:
    apbAddrT: { width: ADDR_WIDTH, desc: "APB address" }
    apbDataT: { width: DATA_WIDTH, desc: "APB data" }
    cfgT:     { width: REG_WIDTH,  desc: "Register payload" }

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "Register payload" }

interfaces:
    apbReg:
        desc: "APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }

blocks:
    top_tb:
        desc: "design top"
        hasMdl: true
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:     { clock: clk }
            apbRstA_n: { clock: apbClk }
            apbRstB_n: { clock: apbClk }
    cpu:
        desc: "register-bus master"
        hasMdl: true
    apbDecode:
        desc: "Router block 'apbDecode'"
        hasMdl: true
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
    leafC:
        desc: "reusable IP leaf whose registerPorts: reset: disambiguates two unmarked resets"
        hasVl: true
        hasMdl: true
        hasRtl: true
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:     { clock: clk }
            apbRstA_n: { clock: apbClk }
            apbRstB_n: { clock: apbClk }
        registerPorts:
            apbReg: { interface: apbReg, clock: apbClk, reset: apbRstA_n }

instances:
    top_tb:     { container: top_tb, instanceType: top_tb,    instGroup: top }
    uCPU:       { container: top_tb, instanceType: cpu,       instGroup: top }
    uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top,
                  clocks: { clk: apbClk }, resets: { rst_n: apbRstA_n } }
    uLeafC:     { container: top_tb, instanceType: leafC,     instGroup: top, addressGroup: top }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cfgC, regType: rw, block: leafC, structure: cfgRegSt, desc: "leafC configuration" }
"""

REGISTER_PORTS_RESET_PROJECT_DOMAINS = """
clocks:
    clk:    { desc: "the default testbench clock", default: true, period: 1, timeUnit: ns }
    apbClk: { desc: "the register-bus testbench clock", period: 3, timeUnit: ns }

resets:
    rst_n:     { desc: "the default reset", default: true, clock: clk }
    apbRstA_n: { desc: "the register-bus reset A", clock: apbClk }
    apbRstB_n: { desc: "the register-bus reset B", clock: apbClk }
"""


def run_registerports_reset_disambiguates_bus_port_domain():
    """getBDPorts stamps a reusable IP's own register-bus port with
    registerClock/registerReset (clockTree.py's BlockDomains.registerBusPort),
    not the port clock's shared selectedReset, which registerPorts: reset:
    cannot resolve for any other port sharing that clock."""
    fixture, project_path, db_path = _make_fixture(
        design=REGISTER_PORTS_RESET_DESIGN, projectDomains=REGISTER_PORTS_RESET_PROJECT_DOMAINS)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: the registerPorts reset: fixture builds\n{output}")
            return False
        print("PASS: the registerPorts reset: fixture builds")
        prj = projectOpen(db_path)
        blockKey = next(key for key, row in prj.data['blocks'].items()
                        if row['block'] == 'leafC')
        view = prj.getBlockData(blockKey)

        def bus_port_takes_the_authored_reset():
            busPortName = view['registerBusPort']
            # The router-to-leaf dispatch is a synthesised ordinary
            # connection (config/postParseRegisterPorts.py), so the port
            # lands in the connections loop's row, not connectionMaps.
            port = view['ports']['connections'][busPortName]
            if port['domainClock'] != 'apbClk' or port['domainReset'] != 'apbRstA_n':
                raise AssertionError(
                    f"'{busPortName}' reports domainClock/domainReset "
                    f"{port['domainClock']!r}/{port['domainReset']!r}, "
                    f"expected 'apbClk'/'apbRstA_n'")
            return True

        def apbclk_selected_reset_stays_ambiguous():
            apbClkEntry = next(row for row in view['clocks'] if row['clock'] == 'apbClk')
            if apbClkEntry['selectedReset'] is not None:
                raise AssertionError(
                    f"apbClk's selectedReset is {apbClkEntry['selectedReset']!r}, "
                    f"expected None: the register-bus port override must not "
                    f"leak into the clock's own shared selection")
            return True

        return all([
            _run_case("a reusable IP's register-bus port takes the authored "
                      "registerPorts: reset:, not the clock's ambiguous shared "
                      "selection", bus_port_takes_the_authored_reset),
            _run_case("apbClk's own selectedReset stays None",
                      apbclk_selected_reset_stays_ambiguous)])
    finally:
        shutil.rmtree(fixture)


def run_topdown_leaf_bus_port_domain_matches_register_clock():
    """getBDPorts stamps a top-down leaf's register-bus port (the router's
    registerDecoderPort, reached by the synthesised router-to-leaf dispatch
    connection) with registerClock/registerReset (the leaf's own bus
    selection), not the domain a plain connectionMaps boundary derivation would read off
    the handler's initial name-match bind inside the leaf's own container.
    """
    fixture, project_path, db_path = regdecode._make_fixture(
        regdecode._sampler_design("clocks: { clkCap: apbClk },\n"
                                  "                  resets: { rstCap_n: apbRst_n }"))
    try:
        code, output = regdecode._build(project_path, db_path)
        if code != 0:
            print(f"FAIL: the top-down sampler fixture builds\n{output}")
            return False
        print("PASS: the top-down sampler fixture builds")
        prj = projectOpen(db_path)
        blockKey = next(key for key, row in prj.data['blocks'].items()
                        if row['block'] == 'sampler')
        view = prj.getBlockData(blockKey)

        def bus_port_takes_the_leaf_register_clock():
            busPortName = view['registerBusPort']
            # The router-to-leaf dispatch is a synthesised ordinary
            # connection, so the port lands in the connections loop's row.
            port = view['ports']['connections'][busPortName]
            if port['domainClock'] != 'clkCap' or port['domainReset'] != 'rstCap_n':
                raise AssertionError(
                    f"'{busPortName}' reports domainClock/domainReset "
                    f"{port['domainClock']!r}/{port['domainReset']!r}, "
                    f"expected 'clkCap'/'rstCap_n': the leaf's own bus "
                    f"clock/reset selection, not the handler's initial "
                    f"name-match bind")
            return True

        return _run_case(
            "a top-down leaf's register-bus port takes the leaf's own "
            "registerClock/registerReset selection",
            bus_port_takes_the_leaf_register_clock)
    finally:
        shutil.rmtree(fixture)


# ------------------------------------------- hasVl BFM port reset check --

# A hasVl leaf whose one declared interface port is reached by a real
# connection (module_hdl_wrapper.py's BFM binds only a port something
# actually produces), so the fixture can vary the port's own clock's
# resets without touching connectivity.
HASVL_PORT_INTF = """types:
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

"""

# clk/apbClk testbench domains, for a fixture whose top_tb itself declares an
# apbClk (a register-bus-style second clock) rather than PROJECT_DOMAINS'
# clkSlow.
HASVL_APB_PROJECT_DOMAINS = """
clocks:
    clk:    { desc: "the default testbench clock", default: true, period: 1, timeUnit: ns }
    apbClk: { desc: "the register-bus testbench clock", period: 3, timeUnit: ns }

resets:
    rst_n:    { desc: "the default reset", default: true, clock: clk }
    apbRst_n: { desc: "the register-bus reset", clock: apbClk }
"""


def run_hasvl_port_ambiguous_reset_rejected():
    """Negative A: 'leaf's declared port 'in' is timed by 'clkB', which
    carries two resets and neither is marked default: true - the co-
    simulation wrapper has no reset to bind the port's BFM to. 'leaf' is
    instantiated (bound onto 'top_tb's own clk/rst_n by name match) so the
    zero-instance missing-period check does not also fire."""
    design = HASVL_PORT_INTF + """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    leaf:
        desc: "hasVl leaf whose declared port sits on a clock with two unmarked resets"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        clocks:
            clk:  { default: true }
            clkB: { }
        resets:
            rst_n:   { clock: clk }
            rstB1_n: { clock: clkB }
            rstB2_n: { clock: clkB }
        ports:
            in: { interface: dataIf, direction: dst, clock: clkB }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uLeaf:  { container: top_tb, instanceType: leaf, instGroup: top,
              clocks: { clkB: clk }, resets: { rstB1_n: rst_n, rstB2_n: rst_n } }
"""
    return _expect_diagnostic(
        "a hasVl port's clock with two unmarked resets is rejected",
        ("The co-simulation wrapper's BFM needs one", 'leaf', 'in', 'clkB', 'rstB1_n', 'rstB2_n'),
        design=design, projectDomains='')


def run_hasvl_port_no_reset_at_all_rejected():
    """Negative B: 'leaf' declares resets: {} - a block with no reset at
    all is otherwise legitimate - but its declared port 'in' still needs
    one, since it is hasVl and the co-simulation wrapper's BFM is generated
    logic. 'leaf' is instantiated so the zero-instance missing-period check
    does not also fire."""
    design = HASVL_PORT_INTF + """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    leaf:
        desc: "hasVl leaf declaring resets: {} with one declared port"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        resets: {}
        ports:
            in: { interface: dataIf, direction: dst }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uLeaf:  { container: top_tb, instanceType: leaf, instGroup: top }
"""
    return _expect_diagnostic(
        "a hasVl leaf declaring resets: {} still needs one for its declared port",
        ("The co-simulation wrapper's BFM needs one", 'leaf', 'in'),
        design=design, projectDomains='')


def run_hasvl_connection_derived_port_rejected():
    """Negative, connection-derived port: 'leaf' declares no ports: at all,
    so its one port 'in' is an ordinary top-down port, entirely defined by
    the connection reaching
    it. The connection names clock: clkSlow, which 'uProd's own instance map
    (clocks: { clk: clkSlow }) resolves 'uProd's clk onto - the consumer-edge
    match the connection clock: check performs - so 'in' is timed by
    'leaf's 'clkB' (bound
    onto the same clkSlow net), which carries no selected reset."""
    design = """blocks:
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:     { default: true }
            clkSlow: { }
        resets:
            rst_n:     { clock: clk }
            rstSlow_n: { clock: clkSlow }
    prod:   { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    leaf:
        desc: "hasVl leaf with no declared ports: its one port is connection-derived"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        clocks:
            clk:  { default: true }
            clkB: { }
        resets:
            rst_n: { clock: clk }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd:  { container: top_tb, instanceType: prod,   instGroup: top,
              clocks: { clk: clkSlow }, resets: { rst_n: rstSlow_n } }
    uLeaf:  { container: top_tb, instanceType: leaf,   instGroup: top,
              clocks: { clkB: clkSlow } }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uLeaf, dstport: in, clock: clkSlow }
"""
    return _expect_diagnostic(
        "a connection-derived (top-down) port of a hasVl block needs a "
        "selected reset on the clock the connection resolves it to",
        ("The co-simulation wrapper's BFM needs one", 'leaf', 'in', 'clkB'),
        design=HASVL_PORT_INTF + design, projectDomains=PROJECT_DOMAINS)


def run_hasvl_connectionmaps_boundary_port_rejected():
    """Negative, connectionMaps boundary port (the portDomainsByBlock
    branch): hasVl container 'dut' does not declare its boundary port
    'apbReg' in ports:; connectionMaps bridges it inward to 'inner's 'regs'
    port, which does name clock: apbClk explicitly - the
    inside-out derivation gives 'apbReg' the domain 'apbClk', which
    carries two unmarked resets on 'dut' itself."""
    design = """blocks:
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
    prod: { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "hasVl container whose connectionMaps boundary port derives to a clock with two unmarked resets"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:     { clock: clk }
            apbRstA_n: { clock: apbClk }
            apbRstB_n: { clock: apbClk }
    inner:
        desc: "inner instance; its own declared port names clock: apbClk explicitly"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
        ports:
            regs: { interface: dataIf, direction: dst, clock: apbClk }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd:  { container: top_tb, instanceType: prod,   instGroup: top }
    uDut:   { container: top_tb, instanceType: dut,    instGroup: top,
              resets: { apbRstA_n: apbRst_n, apbRstB_n: apbRst_n } }
    uInner: { container: dut,    instanceType: inner,  instGroup: top,
              resets: { apbRst_n: apbRstA_n } }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uDut, dstport: apbReg }

connectionMaps:
    - { interface: dataIf, block: dut, direction: dst, instance: uInner, port: apbReg, instancePort: regs }
"""
    return _expect_diagnostic(
        "a hasVl container's connectionMaps boundary port deriving to a "
        "clock with two unmarked resets is rejected",
        ("The co-simulation wrapper's BFM needs one", 'dut', 'apbReg', 'apbClk',
         'apbRstA_n', 'apbRstB_n'),
        design=HASVL_PORT_INTF + design, projectDomains=HASVL_APB_PROJECT_DOMAINS)


def run_hasvl_connectionmaps_boundary_port_not_derived_twice():
    """Positive: hasVl container 'dut' does not declare 'apbReg', a
    connectionMaps boundary port bridged to 'uInner.regs' on apbClk, which
    has a sole reset. The outer connection reaching it names no clock:, so
    were it treated as a top-down port it would take dut's default clock clk,
    which has no reset at all. The connection-derived branch must know
    'apbReg' is already a boundary port and not derive it a second time,
    which would reject a build that must succeed."""
    design = """blocks:
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
    prod: { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "hasVl container: apbReg is a pure connectionMaps boundary port; its default clock has no reset"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            apbRst_n: { clock: apbClk }
    inner:
        desc: "inner instance on apbClk only"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
        clocks:
            apbClk: { }
        resets:
            apbRst_n: { clock: apbClk }
        ports:
            regs: { interface: dataIf, direction: dst }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd:  { container: top_tb, instanceType: prod,   instGroup: top }
    uDut:   { container: top_tb, instanceType: dut,    instGroup: top }
    uInner: { container: dut,    instanceType: inner,  instGroup: top }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uDut, dstport: apbReg }

connectionMaps:
    - { interface: dataIf, block: dut, direction: dst, instance: uInner, port: apbReg, instancePort: regs }
"""

    def check():
        fixture, project_path, db_path = _make_fixture(
            design=HASVL_PORT_INTF + design, projectDomains=BOUNDARY_PROJECT_DOMAINS)
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code != 0:
            raise AssertionError(
                f"a hasVl container's connectionMaps boundary port was "
                f"spuriously derived a second time, from the outer "
                f"connection, and rejected:\n{output}")
        return True

    return _run_case(
        "a hasVl container's connectionMaps boundary port, also reached by "
        "the outer connection, is not derived a second time",
        check)


def run_hasvl_output_clock_port_rejected():
    """Negative, direction: output clock: 'leaf' declares its port
    'outp' on 'clkOut', a clock the block itself outputs rather than
    receives - two unmarked resets on 'clkOut' still leave the BFM with
    nothing to bind."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    leaf:
        desc: "hasVl leaf whose declared port sits on a direction: output clock"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        clocks:
            clk:    { default: true }
            clkOut: { direction: output }
        resets:
            rst_n:     { clock: clk }
            rstOutA_n: { clock: clkOut, direction: output }
            rstOutB_n: { clock: clkOut, direction: output }
        ports:
            outp: { interface: dataIf, direction: dst, clock: clkOut }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uLeaf:  { container: top_tb, instanceType: leaf, instGroup: top,
              clocks: { clkOut: ~ }, resets: { rstOutA_n: ~, rstOutB_n: ~ } }
"""
    return _expect_diagnostic(
        "a hasVl port on a direction: output clock with two unmarked "
        "resets is rejected",
        ("The co-simulation wrapper's BFM needs one", 'leaf', 'outp', 'clkOut',
         'rstOutA_n', 'rstOutB_n'),
        design=HASVL_PORT_INTF + design, projectDomains='')


def run_hasvl_output_clock_port_positive():
    """Positive, direction: output clock: as above, but 'clkOut's one
    reset is its sole (auto-selected) candidate, and the port is actually
    connected, so the build must succeed end to end."""
    design = """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    prod:   { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    leaf:
        desc: "hasVl leaf whose declared port sits on a direction: output clock"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        clocks:
            clk:    { default: true }
            clkOut: { direction: output }
        resets:
            rst_n:    { clock: clk }
            rstOut_n: { clock: clkOut, direction: output }
        ports:
            outp: { interface: dataIf, direction: dst, clock: clkOut }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd:  { container: top_tb, instanceType: prod, instGroup: top }
    uLeaf:  { container: top_tb, instanceType: leaf, instGroup: top,
              clocks: { clkOut: ~ }, resets: { rstOut_n: ~ } }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uLeaf, dstport: outp }
"""

    def check():
        fixture, project_path, db_path = _make_fixture(
            design=HASVL_PORT_INTF + design, projectDomains='')
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code != 0:
            raise AssertionError(
                f"a hasVl port on a direction: output clock whose sole "
                f"reset is auto-selected was rejected:\n{output}")
        return True

    return _run_case(
        "a hasVl port on a direction: output clock with exactly one "
        "selected reset is accepted",
        check)


def run_hasvl_port_positive():
    """Positive: 'leaf's one declared port takes the block default
    clock, whose sole (implicit) reset is its selected one - the ordinary
    shape, which must not be rejected."""
    design = HASVL_PORT_INTF + """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    prod:   { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    leaf:
        desc: "hasVl leaf whose declared port's clock has exactly one selected reset"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        ports:
            in: { interface: dataIf, direction: dst }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd:  { container: top_tb, instanceType: prod,    instGroup: top }
    uLeaf:  { container: top_tb, instanceType: leaf,    instGroup: top }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uLeaf, dstport: in }
"""

    def check():
        fixture, project_path, db_path = _make_fixture(design=design, projectDomains='')
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code != 0:
            raise AssertionError(
                f"a hasVl leaf whose declared port's clock has exactly one "
                f"selected reset was rejected:\n{output}")
        return True

    return _run_case(
        "a hasVl port whose clock has exactly one selected reset is accepted",
        check)


def run_hasvl_two_instances_same_port_not_duplicated():
    """Dedupe: 'leaf' is instantiated TWICE, each instance's port 'in'
    connected from its own producer, one shared clock with no reset at all.
    portsByClock must add one entry per port name, not per connection end,
    so the diagnostic does not list 'in, in': a hasVl BLOCK's ports are
    named once, regardless of instance count."""
    design = HASVL_PORT_INTF + """blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    prod:   { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    leaf:
        desc: "hasVl leaf with no declared ports:, instantiated twice, each connected on its one port 'in'"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        resets: {}

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd1: { container: top_tb, instanceType: prod, instGroup: top }
    uProd2: { container: top_tb, instanceType: prod, instGroup: top }
    uLeaf1: { container: top_tb, instanceType: leaf, instGroup: top }
    uLeaf2: { container: top_tb, instanceType: leaf, instGroup: top }

connections:
    - { interface: dataIf, src: uProd1, srcport: out, dst: uLeaf1, dstport: in }
    - { interface: dataIf, src: uProd2, srcport: out, dst: uLeaf2, dstport: in }
"""

    def check():
        fixture, project_path, db_path = _make_fixture(design=design, projectDomains='')
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code == 0:
            raise AssertionError(f"build succeeded; it must fail.\n{output}")
        needle = "port(s) in are timed by clock 'clk'"
        if needle not in output:
            raise AssertionError(
                f"diagnostic does not mention '{needle}' - port 'in' should "
                f"be listed exactly once, not once per instance.\n{output}")
        if "in, in" in output:
            raise AssertionError(
                f"diagnostic lists port 'in' twice, once per instance, "
                f"rather than once per port name.\n{output}")
        return True

    return _run_case(
        "a hasVl port shared by two instances of the same block is listed "
        "once, not once per instance",
        check)


# APB_PREAMBLE plus a producer/consumer dataIf: one preamble serves both
# the register-bus-only positive fixture below (dataIf declared but unused)
# and the negative twin, which needs it for its extra connection-derived
# port. APB_PREAMBLE itself is shared with another module and stays as-is.
HASVL_TOPDOWN_PREAMBLE = APB_PREAMBLE.replace(
    '\ntypes:\n', '\ntypes:\n    dataT:    { width: 8, desc: "payload word" }\n'
).replace(
    '\nstructures:\n',
    '\nstructures:\n'
    '    dataSt:\n'
    '        data: { varType: dataT, desc: "payload word" }\n'
).replace(
    '\ninterfaces:\n',
    '\ninterfaces:\n'
    '    dataIf:\n'
    '        desc: "producer to consumer stream"\n'
    '        interfaceType: push_ack\n'
    '        structures:\n'
    '            - { structure: dataSt, structureType: data_t }\n'
)

# leafD's non-default clock is literally named 'clk': the synthesised
# register handler's own implicit clock always binds by that name, so the
# handler-bridged connectionMaps boundary guess for 'apbReg' lands on
# 'clk' rather than the leaf's real bus clock 'apbClk'.
HASVL_TOPDOWN_BUS_PORT_DESIGN = HASVL_TOPDOWN_PREAMBLE + """blocks:
    top_tb:
        desc: "design top"
        hasMdl: true
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
    cpu:
        desc: "register-bus master"
        hasMdl: true
    apbDecode:
        desc: "Router block 'apbDecode'"
        hasMdl: true
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
    leafD:
        desc: "top-down hasVl leaf; owns a register, authors no registerPorts:"
        hasVl: true
        hasMdl: true
        hasRtl: true
        clocks:
            clkD:   { default: true }
            clk:    { }
            apbClk: { }
        resets:
            rstD_n:   { clock: clkD }
            rst_n:    { clock: clk }
            rstAlt_n: { clock: clk }
            apbRst_n: { clock: apbClk }

instances:
    top_tb:     { container: top_tb, instanceType: top_tb,    instGroup: top }
    uCPU:       { container: top_tb, instanceType: cpu,       instGroup: top }
    uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top,
                  clocks: { clk: apbClk }, resets: { rst_n: apbRst_n } }
    uLeafD:     { container: top_tb, instanceType: leafD,     instGroup: top, addressGroup: top,
                  clocks: { clkD: clk },
                  resets: { rstD_n: rst_n, rstAlt_n: rst_n } }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cfgD, regType: rw, block: leafD, structure: cfgRegSt, desc: "leafD configuration" }
"""


def run_hasvl_topdown_register_bus_port_excluded():
    """Positive: 'clk' has no selected reset, but the registerBusPort
    exclusion means only the register-bus reset check judges 'apbReg', against
    'apbClk'/'apbRst_n', so the build succeeds."""
    fixture, project_path, db_path = _make_fixture(
        design=HASVL_TOPDOWN_BUS_PORT_DESIGN, projectDomains=HASVL_APB_PROJECT_DOMAINS)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: the top-down hasVl register-bus port fixture builds\n{output}")
            return False
        print("PASS: the top-down hasVl register-bus port fixture builds")
        if 'no selected reset' in output:
            print(f"FAIL: build succeeded but still reported a missing-reset diagnostic\n{output}")
            return False
        print("PASS: no missing-reset diagnostic")
        prj = projectOpen(db_path)
        blockKey = next(key for key, row in prj.data['blocks'].items()
                        if row['block'] == 'leafD')
        view = prj.getBlockData(blockKey)

        def bus_port_matches_register_clock_reset():
            busPortName = view['registerBusPort']
            port = view['ports']['connections'][busPortName]
            if port['domainClock'] != 'apbClk' or port['domainReset'] != 'apbRst_n':
                raise AssertionError(
                    f"'{busPortName}' reports domainClock/domainReset "
                    f"{port['domainClock']!r}/{port['domainReset']!r}, "
                    f"expected 'apbClk'/'apbRst_n'")
            return True

        return _run_case(
            "a top-down hasVl leaf's register-bus port takes the leaf's own "
            "registerClock/registerReset, not the handler's own guess",
            bus_port_matches_register_clock_reset)
    finally:
        shutil.rmtree(fixture)


def run_hasvl_topdown_extra_port_still_rejected():
    """Negative twin: same 'leafD' as the positive above, plus one
    extra, ordinary connection-derived port 'in' on a second, non-bus,
    non-default clock 'clkX' with two unmarked resets. The registerBusPort
    exclusion names only 'apbReg'; 'in' must still be rejected, proving the
    exclusion does not blanket the whole block."""
    design = HASVL_TOPDOWN_PREAMBLE + """blocks:
    top_tb:
        desc: "design top"
        hasMdl: true
        clocks:
            clk:    { default: true }
            apbClk: { }
            clkY:   { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
            rstY_n:   { clock: clkY }
    cpu:
        desc: "register-bus master"
        hasMdl: true
    prod:
        desc: "producer"
        hasMdl: true
    apbDecode:
        desc: "Router block 'apbDecode'"
        hasMdl: true
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
    leafD:
        desc: "top-down hasVl leaf; a register plus a second, non-bus connection-derived port"
        hasVl: true
        hasMdl: true
        hasRtl: true
        clocks:
            clkD:   { default: true }
            clk:    { }
            apbClk: { }
            clkX:   { }
        resets:
            rstD_n:   { clock: clkD }
            rst_n:    { clock: clk }
            rstAlt_n: { clock: clk }
            apbRst_n: { clock: apbClk }
            rstX1_n:  { clock: clkX }
            rstX2_n:  { clock: clkX }

instances:
    top_tb:     { container: top_tb, instanceType: top_tb,    instGroup: top }
    uCPU:       { container: top_tb, instanceType: cpu,       instGroup: top }
    uProd:      { container: top_tb, instanceType: prod,      instGroup: top,
                  clocks: { clk: clkY }, resets: { rst_n: rstY_n } }
    uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top,
                  clocks: { clk: apbClk }, resets: { rst_n: apbRst_n } }
    uLeafD:     { container: top_tb, instanceType: leafD,     instGroup: top, addressGroup: top,
                  clocks: { clkD: clk, clkX: clkY },
                  resets: { rstD_n: rst_n, rstAlt_n: rst_n, rstX1_n: rstY_n, rstX2_n: rstY_n } }

connections:
    - { interface: apbReg, src: uCPU,  dst: uAPBDecode }
    - { interface: dataIf, src: uProd, srcport: out, dst: uLeafD, dstport: in, clock: clkY }

registers:
    - { register: cfgD, regType: rw, block: leafD, structure: cfgRegSt, desc: "leafD configuration" }
"""
    # Binding clkX onto the shared apbClk net instead of a distinct clkY
    # collapses to an ambiguous-block-clock diagnostic before the BFM reset
    # check gets a look, so this keeps its own clkY/rstY_n and custom projectDomains
    # rather than reusing HASVL_APB_PROJECT_DOMAINS.
    projectDomains = """
clocks:
    clk:    { desc: "the default testbench clock", default: true, period: 1, timeUnit: ns }
    apbClk: { desc: "the register-bus testbench clock", period: 3, timeUnit: ns }
    clkY:   { desc: "a third testbench clock", period: 5, timeUnit: ns }

resets:
    rst_n:    { desc: "the default reset", default: true, clock: clk }
    apbRst_n: { desc: "the register-bus reset", clock: apbClk }
    rstY_n:   { desc: "clkY's reset", clock: clkY }
"""
    return _expect_diagnostic(
        "a top-down hasVl leaf's non-bus connection-derived port on an "
        "ambiguous clock is still rejected, unaffected by the register-bus "
        "port's own exclusion",
        ("The co-simulation wrapper's BFM needs one", 'leafD', 'in', 'clkX',
         'rstX1_n', 'rstX2_n'),
        design=design, projectDomains=projectDomains)


# wrapV declares no addressBlock: or registerPorts:, so it is a
# passthrough container. Its registerClock/registerReset come from the
# top-down bus selection via `resolveBlock`; leafV infers its bus from wrapV's pair, not from
# the router.
HASVL_PASSTHROUGH_BUS_PORT_DESIGN = HASVL_TOPDOWN_PREAMBLE + """blocks:
    top_tb:
        desc: "design top"
        hasMdl: true
        clocks:
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
    cpu:
        desc: "register-bus master"
        hasMdl: true
    apbDecode:
        desc: "Router block 'apbDecode'"
        hasMdl: true
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
    wrapV:
        desc: "router-less passthrough container, hasVl at the design boundary"
        hasVl: true
        hasMdl: true
        hasRtl: true
        clocks:
            clkD:   { default: true }
            clk:    { }
            apbClk: { }
        resets:
            rstD_n:   { clock: clkD }
            rst_n:    { clock: clk }
            rstAlt_n: { clock: clk }
            apbRst_n: { clock: apbClk }
    leafV:
        desc: "top-down leaf behind the passthrough container"
        hasMdl: true

instances:
    top_tb:     { container: top_tb, instanceType: top_tb,    instGroup: top }
    uCPU:       { container: top_tb, instanceType: cpu,       instGroup: top }
    uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top,
                  clocks: { clk: apbClk }, resets: { rst_n: apbRst_n } }
    uWrapV:     { container: top_tb, instanceType: wrapV,     instGroup: top, addressGroup: top,
                  clocks: { clkD: clk },
                  resets: { rstD_n: rst_n, rstAlt_n: rst_n } }
    uLeafV:     { container: wrapV, instanceType: leafV,
                  clocks: { clk: apbClk }, resets: { rst_n: apbRst_n } }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cfgV, regType: rw, block: leafV, structure: cfgRegSt, desc: "leafV configuration" }
"""


def run_hasvl_passthrough_register_bus_port_excluded():
    """Positive for a passthrough container's own register-bus port: 'clk'
    has no selected reset, but the registerBusPort exclusion leaves 'apbClk'
    to the register-bus reset check, so the build succeeds."""
    fixture, project_path, db_path = _make_fixture(
        design=HASVL_PASSTHROUGH_BUS_PORT_DESIGN, projectDomains=HASVL_APB_PROJECT_DOMAINS)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: the passthrough container hasVl register-bus port fixture builds\n{output}")
            return False
        print("PASS: the passthrough container hasVl register-bus port fixture builds")
        if 'no selected reset' in output:
            print(f"FAIL: build succeeded but still reported a missing-reset diagnostic\n{output}")
            return False
        print("PASS: no missing-reset diagnostic")
        prj = projectOpen(db_path)
        blockKey = next(key for key, row in prj.data['blocks'].items()
                        if row['block'] == 'wrapV')
        view = prj.getBlockData(blockKey)

        def bus_port_matches_register_clock_reset():
            busPortName = view['registerBusPort']
            port = view['ports']['connections'][busPortName]
            if port['domainClock'] != 'apbClk' or port['domainReset'] != 'apbRst_n':
                raise AssertionError(
                    f"'{busPortName}' reports domainClock/domainReset "
                    f"{port['domainClock']!r}/{port['domainReset']!r}, "
                    f"expected 'apbClk'/'apbRst_n'")
            return True

        return _run_case(
            "a router-less passthrough container's register-bus port takes "
            "its own resolved registerClock/registerReset",
            bus_port_matches_register_clock_reset)
    finally:
        shutil.rmtree(fixture)


def run_hasvl_passthrough_extra_port_still_rejected():
    """Negative twin: same 'wrapV' as the positive above, plus one
    extra, ordinary connection-derived port 'in' on a second, non-bus,
    non-default clock 'clkX' with two unmarked resets. The registerBusPort
    exclusion names only 'apbClk'; 'in' must still be rejected, proving the
    exclusion does not blanket the whole container block."""
    design = HASVL_TOPDOWN_PREAMBLE + """blocks:
    top_tb:
        desc: "design top"
        hasMdl: true
        clocks:
            clk:    { default: true }
            apbClk: { }
            clkY:   { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
            rstY_n:   { clock: clkY }
    cpu:
        desc: "register-bus master"
        hasMdl: true
    prod:
        desc: "producer"
        hasMdl: true
    apbDecode:
        desc: "Router block 'apbDecode'"
        hasMdl: true
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: apbReg
            registerDecoderPort: apbReg
    wrapV:
        desc: "router-less passthrough container, a second non-bus connection-derived port"
        hasVl: true
        hasMdl: true
        hasRtl: true
        clocks:
            clkD:   { default: true }
            clk:    { }
            apbClk: { }
            clkX:   { }
        resets:
            rstD_n:   { clock: clkD }
            rst_n:    { clock: clk }
            rstAlt_n: { clock: clk }
            apbRst_n: { clock: apbClk }
            rstX1_n:  { clock: clkX }
            rstX2_n:  { clock: clkX }
    leafV:
        desc: "top-down leaf behind the passthrough container"
        hasMdl: true

instances:
    top_tb:     { container: top_tb, instanceType: top_tb,    instGroup: top }
    uCPU:       { container: top_tb, instanceType: cpu,       instGroup: top }
    uProd:      { container: top_tb, instanceType: prod,      instGroup: top,
                  clocks: { clk: clkY }, resets: { rst_n: rstY_n } }
    uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top,
                  clocks: { clk: apbClk }, resets: { rst_n: apbRst_n } }
    uWrapV:     { container: top_tb, instanceType: wrapV,     instGroup: top, addressGroup: top,
                  clocks: { clkD: clk, clkX: clkY },
                  resets: { rstD_n: rst_n, rstAlt_n: rst_n, rstX1_n: rstY_n, rstX2_n: rstY_n } }
    uLeafV:     { container: wrapV, instanceType: leafV,
                  clocks: { clk: apbClk }, resets: { rst_n: apbRst_n } }

connections:
    - { interface: apbReg, src: uCPU,  dst: uAPBDecode }
    - { interface: dataIf, src: uProd, srcport: out, dst: uWrapV, dstport: in, clock: clkY }

registers:
    - { register: cfgV, regType: rw, block: leafV, structure: cfgRegSt, desc: "leafV configuration" }
"""
    # Binding clkX onto the shared apbClk net instead of a distinct clkY
    # collapses to an ambiguous-block-clock diagnostic before the BFM reset
    # check gets a look, so this keeps its own clkY/rstY_n and custom projectDomains
    # rather than reusing HASVL_APB_PROJECT_DOMAINS.
    projectDomains = """
clocks:
    clk:    { desc: "the default testbench clock", default: true, period: 1, timeUnit: ns }
    apbClk: { desc: "the register-bus testbench clock", period: 3, timeUnit: ns }
    clkY:   { desc: "a third testbench clock", period: 5, timeUnit: ns }

resets:
    rst_n:    { desc: "the default reset", default: true, clock: clk }
    apbRst_n: { desc: "the register-bus reset", clock: apbClk }
    rstY_n:   { desc: "clkY's reset", clock: clkY }
"""
    return _expect_diagnostic(
        "a passthrough container's non-bus connection-derived port on an "
        "ambiguous clock is still rejected, unaffected by the register-bus "
        "port's own exclusion",
        ("The co-simulation wrapper's BFM needs one", 'wrapV', 'in', 'clkX',
         'rstX1_n', 'rstX2_n'),
        design=design, projectDomains=projectDomains)


def run_hasvl_port_reset_cases():
    return all((run_hasvl_port_ambiguous_reset_rejected(),
                run_hasvl_port_no_reset_at_all_rejected(),
                run_hasvl_connection_derived_port_rejected(),
                run_hasvl_connectionmaps_boundary_port_rejected(),
                run_hasvl_connectionmaps_boundary_port_not_derived_twice(),
                run_hasvl_output_clock_port_rejected(),
                run_hasvl_output_clock_port_positive(),
                run_hasvl_port_positive(),
                run_hasvl_two_instances_same_port_not_duplicated(),
                run_hasvl_topdown_register_bus_port_excluded(),
                run_hasvl_topdown_extra_port_still_rejected(),
                run_hasvl_passthrough_register_bus_port_excluded(),
                run_hasvl_passthrough_extra_port_still_rejected()))


# ------------------------------------------------------- name collisions --

# A clock and a reset of the same name would be two module ports of one name.
COLLIDING_NAMES = """
clocks:
    clk:     { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    clkSlow: { desc: "a slower clock", period: 3, timeUnit: ns }

resets:
    clkSlow:   { desc: "a reset named after a clock" }
    rstSlow_n: { desc: "the slow-domain reset", default: true }
"""


def run_collision_cases():
    return _expect_diagnostic(
        "a reset sharing a clock's name is rejected",
        ('clkSlow', 'clocks:', 'resets:'),
        projectDomains=COLLIDING_NAMES)


# --------------------------------------------------------- graph shape --

class _StubDiag:
    """The diag protocol clockTree needs: `logError(msg)` and
    `diagnosticLocation(yamlFile, lc)`.
    """

    def __init__(self):
        self.messages = []

    def logError(self, msg):
        self.messages.append(msg)

    def diagnosticLocation(self, yamlFile, lc):
        return yamlFile


def run_clock_tree_shape_cases():
    """The clockTree.py graph (Net.kind/.isReset/.clockNet/.driver,
    Driver.kind, Consumer.binding, BlockDomains.blockKey/Container.blockKey)
    is read here, not just written: a two-level design, container 'soc'
    with two declared clocks and resets, and three children - one bound by
    name match, one by the clk/rst_n fallback, and one asynchronous reset
    input bound by an explicit name.

    Built directly through the constructors rather than through
    BlockDomains.build()/clockTree.build(): a graph-shape check on the
    model's own classes, not a real project build
    (run_async_reset_bound_by_name_cases and
    run_async_reset_bound_by_map_cases exercise a real build for that). An
    asynchronous reset input binds as a Consumer like any other, 'name' or
    'map', never 'fallback' (it takes no clk/rst_n-style default fallback).
    """
    def clockDecl(default=False):
        return clockTree.ClockDecl(desc='', direction='input', default=default,
                                   period='', timeUnit='ns')

    def resetDecl(clock='', default=False, isAsync=False):
        return clockTree.ResetDecl(desc='', direction='input', default=default,
                                   clock=clock, isAsync=isAsync, clockStated=bool(clock))

    soc = clockTree.BlockDomains(
        'soc/top.yaml', 'soc',
        OrderedDict([('clkSys', clockDecl(default=True)), ('clkPeripheral', clockDecl())]),
        OrderedDict([('rstSys_n', resetDecl(clock='clkSys', default=True)),
                    ('rstPeripheral_n', resetDecl(clock='clkPeripheral', default=True))]),
        'clkSys', {'clkSys': 'rstSys_n', 'clkPeripheral': 'rstPeripheral_n'},
        False, False, [], {})
    uartA = clockTree.BlockDomains(
        'uartA/top.yaml', 'uartA', OrderedDict([('clkPeripheral', clockDecl(default=True))]),
        OrderedDict(), 'clkPeripheral', {}, False, False, [], {})
    plainDut = clockTree.BlockDomains(
        'plainDut/top.yaml', 'plainDut', OrderedDict([('clk', clockDecl(default=True))]),
        OrderedDict([('rst_n', resetDecl(clock='clk', default=True))]),
        'clk', {'clk': 'rst_n'}, False, False, [], {})
    asyncBlock = clockTree.BlockDomains(
        'asyncBlock/top.yaml', 'asyncBlock', OrderedDict([('clk', clockDecl(default=True))]),
        OrderedDict([('rstPeripheral_n', resetDecl(isAsync=True))]),
        'clk', {}, False, False, [], {})

    container = clockTree.Container('soc/top.yaml')
    for name, isReset, clockNet in (('clkSys', False, None), ('clkPeripheral', False, None),
                                    ('rstSys_n', True, 'clkSys'),
                                    ('rstPeripheral_n', True, 'clkPeripheral')):
        container.nets[name] = clockTree.Net(name, 'declared', isReset, clockNet,
                                             clockTree.Driver('input'))
    container.nets['clkPeripheral'].consumers.append(
        clockTree.Consumer('uUartA', 'clkPeripheral', 'name'))
    container.nets['clkSys'].consumers.append(clockTree.Consumer('uDut', 'clk', 'fallback'))
    container.nets['rstSys_n'].consumers.append(clockTree.Consumer('uDut', 'rst_n', 'fallback'))
    container.nets['clkSys'].consumers.append(clockTree.Consumer('uAsync', 'clk', 'fallback'))
    container.nets['rstPeripheral_n'].consumers.append(
        clockTree.Consumer('uAsync', 'rstPeripheral_n', 'name'))
    container.instances['uUartA'] = 'uartA/top.yaml'
    container.instances['uDut'] = 'plainDut/top.yaml'
    container.instances['uAsync'] = 'asyncBlock/top.yaml'

    root = clockTree.Container(clockTree.ClockTree.ROOT_KEY)
    root.nets['clkTb'] = clockTree.Net('clkTb', 'testbench', False, None,
                                       clockTree.Driver('environment'))
    root.nets['rstTb_n'] = clockTree.Net('rstTb_n', 'testbench', True, 'clkTb',
                                        clockTree.Driver('environment'))
    root.instances['uSoc'] = 'soc/top.yaml'

    domains = {domain.blockKey: domain for domain in (soc, uartA, plainDut, asyncBlock)}
    diag = _StubDiag()
    tree = clockTree.ClockTree(domains, {'soc/top.yaml': container}, root, diag, [])

    def net_shape():
        if set(container.nets) != {'clkSys', 'clkPeripheral', 'rstSys_n', 'rstPeripheral_n'}:
            raise AssertionError(f"container nets by name: {list(container.nets)}")
        if any(net.kind != 'declared' for net in container.nets.values()):
            raise AssertionError("a container's own nets must be kind 'declared'")
        if any(net.driver.kind != 'input' for net in container.nets.values()):
            raise AssertionError("a container's own nets are driven by its own input port")
        if container.nets['rstSys_n'].clockNet != 'clkSys':
            raise AssertionError(f"rstSys_n.clockNet: {container.nets['rstSys_n'].clockNet!r}")
        return True

    def root_net_shape():
        if set(root.nets) != {'clkTb', 'rstTb_n'}:
            raise AssertionError(f"root nets by name: {list(root.nets)}")
        for net in root.nets.values():
            if net.kind != 'testbench' or net.driver.kind != 'environment':
                raise AssertionError(
                    f"a root net must be kind 'testbench' with an 'environment' "
                    f"driver, got {net.kind}/{net.driver.kind}")
        return True

    def consumerOf(netName, instanceKey):
        for consumer in container.nets[netName].consumers:
            if consumer.instanceKey == instanceKey:
                return consumer
        return None

    def name_match_consumer():
        consumer = consumerOf('clkPeripheral', 'uUartA')
        if consumer is None or consumer.blockPort != 'clkPeripheral' or consumer.binding != 'name':
            raise AssertionError(f"uUartA's clock should be a name-match consumer: {consumer}")
        return True

    def fallback_consumers():
        clockConsumer = consumerOf('clkSys', 'uDut')
        resetConsumer = consumerOf('rstSys_n', 'uDut')
        if clockConsumer is None or clockConsumer.binding != 'fallback':
            raise AssertionError(f"uDut's clock should fall back to clkSys: {clockConsumer}")
        if resetConsumer is None or resetConsumer.binding != 'fallback':
            raise AssertionError(f"uDut's reset should fall back to rstSys_n: {resetConsumer}")
        return True

    def async_reset_bound_by_name():
        consumer = consumerOf('rstPeripheral_n', 'uAsync')
        if consumer is None or consumer.binding != 'name':
            raise AssertionError(
                f"an asynchronous reset input bound by explicit name is still a "
                f"'name' consumer, never 'fallback': {consumer}")
        return True

    def block_domains_fields():
        if soc.defaultClock != 'clkSys':
            raise AssertionError(f"soc's default clock: {soc.defaultClock!r}")
        if soc.selectedReset != {'clkSys': 'rstSys_n', 'clkPeripheral': 'rstPeripheral_n'}:
            raise AssertionError(f"soc's selected resets: {soc.selectedReset!r}")
        if tree.blocks['asyncBlock/top.yaml'].resets['rstPeripheral_n'].isAsync is not True:
            raise AssertionError("asyncBlock's own reset declaration should read back as async")
        return True

    def no_diagnostics():
        if diag.messages:
            raise AssertionError(f"building the fixture itself raised diagnostics: {diag.messages}")
        return True

    results = [_run_case(label, fn) for label, fn in (
        ("building the fixture raises no diagnostics", no_diagnostics),
        ("a container's own declared clocks/resets are 'declared' nets driven by its own input port",
         net_shape),
        ("the root's testbench clocks/resets are 'testbench' nets driven by the environment",
         root_net_shape),
        ("a child clock bound by name match is a 'name' consumer",
         name_match_consumer),
        ("a child clock/reset named clk/rst_n falls back to the container default",
         fallback_consumers),
        ("an asynchronous reset input bound by an explicit name is a 'name' consumer",
         async_reset_bound_by_name),
        ("BlockDomains.defaultClock/selectedReset read back what was built",
         block_domains_fields))]
    return all(results)


# ------------------------------------ selected reset, top-down ports, memories --

LOCAL_NET_DEFAULT_RESET_DESIGN = """types:
    dataT: { width: 8, desc: "payload word" }

blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container: one default clock and one unmarked declared reset rstA"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { default: true }
        resets:
            rstA: { clock: clk{rstAMark} }
    driver:
        desc: "drives a local reset net on clk"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { default: true }
        resets:
            outRst: { clock: clk, direction: output }
    consumer:
        desc: "consumes the local reset net synchronously as its rst_n"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false

instances:
    top_tb:    { container: top_tb, instanceType: top_tb,   instGroup: top }
    uDut:      { container: top_tb, instanceType: dut,      instGroup: top, resets: { rstA: rst_n } }
    uDriver:   { container: dut,    instanceType: driver,   instGroup: top, resets: { outRst: lr } }
    uConsumer: { container: dut,    instanceType: consumer, instGroup: top, resets: { rst_n: lr } }
"""


def run_default_clock_local_reset_candidates_cases():
    """A local reset net on a container's default clock joins its declared
    reset as a candidate, so an unmarked declared reset does not select
    itself when a local reset net shares its clock. The default clock's
    selected reset is the block's rst_n, so the ambiguity is rejected, listing
    the local net too; marking the declared reset default: true selects it
    over the local net. With no resets: at all, the candidate is the implicit
    rst_n, and the fix is to declare it with default: true."""
    def implicitRstN(dutResets):
        return (LOCAL_NET_DEFAULT_RESET_DESIGN.replace(
                    "        resets:\n            rstA: { clock: clk{rstAMark} }\n", dutResets)
                .replace(", resets: { rstA: rst_n } }", " }"))

    def rstASelected(db_path):
        prj = projectOpen(db_path)
        dutKey = next(key for key, row in prj.data['blocks'].items() if row['block'] == 'dut')
        defaultReset = prj.getBlockData(dutKey)['defaultReset']
        if defaultReset != 'rstA':
            raise AssertionError(f"dut's default reset is {defaultReset!r}, expected 'rstA'")

    return all([
        _expect_diagnostic(
            "a default clock with a declared and a local reset candidate, none marked, is rejected",
            ("Block 'dut' has 2 resets on its default clock 'clk'",
             "declared reset 'rstA' and local reset net 'lr' (driven by instance 'uDriver')",
             "The block's rst_n, used by its default-clock flops and default-domain "
             "aliases, comes from the single selected reset of the default clock",
             "none is selected because neither is marked default: true",
             "Mark 'rstA' default: true in block 'dut''s resets:."),
            design=LOCAL_NET_DEFAULT_RESET_DESIGN.replace('{rstAMark}', ''), projectDomains=''),
        _expect_builds(
            "marking the declared reset default: true selects it over a local net",
            rstASelected,
            design=LOCAL_NET_DEFAULT_RESET_DESIGN.replace('{rstAMark}', ', default: true'),
            projectDomains=''),
        _expect_diagnostic(
            "an implicit rst_n and a local reset candidate, none marked, is rejected",
            ("Block 'dut' has 2 resets on its default clock 'clk'",
             "implicit reset 'rst_n' and local reset net 'lr' (driven by instance 'uDriver')",
             "Declare 'rst_n' in block 'dut''s resets: with default: true."),
            design=implicitRstN(''), projectDomains=''),
        _expect_builds(
            "declaring rst_n with default: true selects it over a local net",
            design=implicitRstN("        resets:\n            rst_n: { default: true }\n"),
            projectDomains=''),
    ])


TOPDOWN_OUTPUT_ONLY_DESIGN = """types:
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
    prod:   { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    gen2:
        desc: "every declared clock is direction: output"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkOut: { direction: output }
{gen2Ports}
instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uProd:  { container: top_tb, instanceType: prod,   instGroup: top }
    uGen2:  { container: top_tb, instanceType: gen2,   instGroup: top, clocks: { clkOut: ~ } }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uGen2, dstport: in }
"""


def run_topdown_port_on_no_default_clock_block_cases():
    """A top-down port reached by a connection with no clock: takes its
    block's default clock, so a block whose every clock is an output cannot
    have one. Declaring the port in ports: with its clock: builds."""
    return all([
        _expect_diagnostic(
            "a top-down port of a block with no default clock is rejected",
            ("top-down port 'in'", "'uGen2'", "'gen2' has no default clock",
             "declare port 'in' in block 'gen2''s ports: with its clock:"),
            design=TOPDOWN_OUTPUT_ONLY_DESIGN.replace('{gen2Ports}', ''), projectDomains=''),
        _expect_builds(
            "the same port declared in ports: with its clock: builds",
            lambda db_path: _port_domain(db_path, 'gen2', 'in'),
            design=TOPDOWN_OUTPUT_ONLY_DESIGN.replace(
                '{gen2Ports}',
                "        ports:\n"
                "            in: { interface: dataIf, direction: dst, clock: clkOut }\n"),
            projectDomains=''),
    ])


MEMORY_STATED_CLOCK_DESIGN = """types:
    dataT: { width: 8, desc: "payload word" }
    memAddrT: { width: 3, desc: "memory address" }

structures:
    memSt:
        data: { varType: dataT, desc: "memory payload" }
    memAddrSt:
        address: { varType: memAddrT, desc: "memory address" }

blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    memOwner:
        desc: "no default clock; the memory states its own clock:"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkA: { direction: output }
            clkB: { direction: output }

instances:
    top_tb:    { container: top_tb, instanceType: top_tb,   instGroup: top }
    uMemOwner: { container: top_tb, instanceType: memOwner, instGroup: top,
                 clocks: { clkA: ~, clkB: ~ } }

memories:
    - { memory: tbl, block: memOwner, structure: memSt, addressStruct: memAddrSt,
        wordLines: 4, ports: [p], desc: "table", clock: clkB }
"""


def run_memory_stated_clock_on_no_default_clock_block_accepted():
    """A memory that names its own clock: needs no default clock from its
    owning block, and the view carries that clock."""
    def onClkB(db_path):
        prj = projectOpen(db_path)
        ownerKey = next(key for key, row in prj.data['blocks'].items()
                        if row['block'] == 'memOwner')
        clocks = {row['memory']: row['domainClock']
                  for row in prj.getBlockData(ownerKey)['memories'].values()}
        if clocks != {'tbl': 'clkB'}:
            raise AssertionError(f"memOwner's memory clocks are {clocks}, expected tbl on clkB")

    return _expect_builds(
        "a memory stating its own clock: on a block with no default clock builds",
        onClkB, design=MEMORY_STATED_CLOCK_DESIGN, projectDomains='')


EXPORT_RESET_UNCONNECTED_CLOCK_DESIGN = """types:
    dataT: { width: 8, desc: "payload word" }

blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    supplier:
        desc: "drives an output clock and an output reset on it"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clkS: { direction: output }
        resets:
            rstS_n: { clock: clkS, direction: output }
    dut:
        desc: "exports the supplier's reset onto its own declared output reset"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            c1: { default: true }
            cOut: { direction: output }
        resets:
            rstOut_n: { clock: {rstOutClock}, direction: output }

instances:
    top_tb:    { container: top_tb, instanceType: top_tb,   instGroup: top }
    uDut:      { container: top_tb, instanceType: dut,      instGroup: top,
                 clocks: { c1: clk, cOut: ~ }, resets: { rstOut_n: ~ } }
    uSupplier: { container: dut,    instanceType: supplier, instGroup: top,
                 clocks: { clkS: {clkSBind} }, resets: { rstS_n: rstOut_n } }
"""


def run_export_reset_from_unconnected_clock_cases():
    """A reset exported onto a container's declared output reset is released
    on its supplier's clock. When that clock is bound to `~` it is released on
    no container clock, so it cannot belong to the declared reset's clock."""
    def design(rstOutClock, clkSBind):
        return EXPORT_RESET_UNCONNECTED_CLOCK_DESIGN.replace(
            '{rstOutClock}', rstOutClock).replace('{clkSBind}', clkSBind)

    return all([
        _expect_diagnostic(
            "an export whose supplier clock is bound to `~` onto a reset of an input clock is rejected",
            ("'uSupplier' exports reset 'rstS_n'", "declared output reset 'rstOut_n'",
             "'clkS', which is bound to `~`",
             "output clock of 'dut' that no other child drives"),
            design=design('c1', '~'), projectDomains=''),
        _expect_diagnostic(
            "the same export onto a reset of an undriven output clock names that clock",
            ("'clkS', which is bound to `~`",
             "bind 'clkS' of instance 'uSupplier' to 'cOut' in its clocks: map"),
            design=design('cOut', '~'), projectDomains=''),
        _expect_builds(
            "binding the supplier clock to the declared reset's output clock builds",
            design=design('cOut', 'cOut'), projectDomains=''),
    ])


MEMORY_OUTPUT_CLOCK_DESIGN = """types:
    dataT: { width: 8, desc: "payload word" }
    memAddrT: { width: 3, desc: "memory address" }

structures:
    memSt:
        data: { varType: dataT, desc: "memory payload" }
    memAddrSt:
        address: { varType: memAddrT, desc: "memory address" }

blocks:
    top_tb:
        desc: "testbench container"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { default: true }
            clkWrong: { }
        resets:
            rst_n:      { clock: clk }
            rstWrong_n: { clock: clkWrong }
    memOwner:
        desc: "owns a memory on its own output clock clkGen"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:    { default: true }
            clkGen: { direction: output }
    accessor:
        desc: "hardware accessor of the memory"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk: { default: true }
        resets: { }

instances:
    top_tb:    { container: top_tb, instanceType: top_tb,   instGroup: top }
    uMemOwner: { container: top_tb, instanceType: memOwner, instGroup: top,
                 clocks: { clkGen: {clkGenBind} } }
    uAccessor: { container: top_tb, instanceType: accessor, instGroup: top,
                 clocks: { clk: {accessorBind} } }

memories:
    - { memory: tbl, block: memOwner, structure: memSt, addressStruct: memAddrSt,
        wordLines: 4, ports: [p], desc: "table", clock: clkGen }

memoryConnections:
    - { memory: tbl, block: memOwner, instance: uAccessor, port: p }
"""

MEMORY_OUTPUT_CLOCK_PROJECT_DOMAINS = """
clocks:
    clk:      { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    clkWrong: { desc: "a second testbench clock", period: 3, timeUnit: ns }

resets:
    rst_n:      { desc: "the default reset", default: true, clock: clk }
    rstWrong_n: { desc: "the second clock's reset", clock: clkWrong }
"""


MEMORY_ACCESSOR_NO_DEFAULT_CLOCK_DESIGN = """types:
    dataT: { width: 8, desc: "payload word" }
    memAddrT: { width: 3, desc: "memory address" }

structures:
    memSt:
        data: { varType: dataT, desc: "memory payload" }
    memAddrSt:
        address: { varType: memAddrT, desc: "memory address" }

blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    memOwner: { desc: "owns a memory on its default clock", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    accessor:
        desc: "hardware accessor of the memory"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
{accessorClocks}            clkO: { direction: output }

instances:
    top_tb:    { container: top_tb, instanceType: top_tb,   instGroup: top }
    uMemOwner: { container: top_tb, instanceType: memOwner, instGroup: top }
    uAccessor: { container: top_tb, instanceType: accessor, instGroup: top,
                 clocks: { {accessorMap}clkO: ~ } }

memories:
    - { memory: tbl, block: memOwner, structure: memSt, addressStruct: memAddrSt,
        wordLines: 4, ports: [p], desc: "table" }

memoryConnections:
    - { memory: tbl, block: memOwner, instance: uAccessor, port: p }
"""


def run_memory_accessor_without_default_clock_cases():
    """A memory accessor takes its block's default clock, so an accessor
    whose every clock is an output is rejected. Given an input clock, it
    builds and its view opens."""
    def design(accessorClocks, accessorMap):
        return MEMORY_ACCESSOR_NO_DEFAULT_CLOCK_DESIGN.replace(
            '{accessorClocks}', accessorClocks).replace('{accessorMap}', accessorMap)

    def accessorViewOpens(db_path):
        prj = projectOpen(db_path)
        accessorKey = next(key for key, row in prj.data['blocks'].items()
                           if row['block'] == 'accessor')
        prj.getBlockData(accessorKey)

    return all([
        _expect_diagnostic(
            "a memory accessor with no default clock is rejected",
            ("'uAccessor' of block 'accessor' accesses memory 'tbl'",
             "'accessor' has no default clock (every declared clock is direction: output)",
             "A memory accessor takes its block's default clock",
             "Give 'accessor' an input clock."),
            design=design('', ''), projectDomains=''),
        _expect_builds(
            "the accessor given an input clock builds",
            accessorViewOpens,
            design=design('            clk: { }\n', 'clk: clk, '), projectDomains=''),
        _expect_builds(
            "a memoryConnections row with no instance, beside an accessor, builds",
            design=design('            clk: { }\n', 'clk: clk, ')
            + "    - { memory: tbl, block: memOwner, port: p }\n", projectDomains=''),
    ])


def run_memory_accessor_without_default_clock_unreachable_rejected():
    """An accessor with no default clock is rejected inside a root-project
    container that nothing instantiates. A child project's uninstantiated
    harness is covered in test_register_decode_clock.py."""
    design = MEMORY_ACCESSOR_NO_DEFAULT_CLOCK_DESIGN.replace(
        '{accessorClocks}', '').replace('{accessorMap}', '').replace(
        "    memOwner: {",
        "    orphan: { desc: \"container no instance names\", hasVl: false, hasMdl: false, "
        "hasTb: false, hasRtl: false }\n    memOwner: {").replace(
        "uMemOwner: { container: top_tb,", "uMemOwner: { container: orphan,").replace(
        "uAccessor: { container: top_tb,", "uAccessor: { container: orphan,")
    return _expect_diagnostic(
        "a memory accessor with no default clock in an uninstantiated container is rejected",
        ("Instance 'uAccessor' of block 'accessor' accesses memory 'tbl' of block "
         "'memOwner', but 'accessor' has no default clock (every declared clock is "
         "direction: output). A memory accessor takes its block's default clock. "
         "Give 'accessor' an input clock.",
         "Found 1 Error."),
        design=design, projectDomains='')


MEMORY_ACCESSOR_UNINSTANTIATED_CONTAINER_DESIGN = """types:
    dataT: { width: 8, desc: "payload word" }
    memAddrT: { width: 3, desc: "memory address" }

structures:
    memSt:
        data: { varType: dataT, desc: "memory payload" }
    memAddrSt:
        address: { varType: memAddrT, desc: "memory address" }

blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    orphan:
        desc: "container no instance names"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks:
            clk:  { default: true }
            clkB: { }
        resets:
            rst_n:  { clock: clk }
            rstB_n: { clock: clkB }
    memOwner: { desc: "owns a memory on its default clock", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    accessor: { desc: "hardware accessor of the memory", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }

instances:
    top_tb:    { container: top_tb, instanceType: top_tb,   instGroup: top }
    oMemOwner: { container: orphan, instanceType: memOwner, instGroup: top }
    oAccessor: { container: orphan, instanceType: accessor, instGroup: top,
                 clocks: { clk: {accessorClock} }, resets: { rst_n: {accessorReset} } }

memories:
    - { memory: tbl, block: memOwner, structure: memSt, addressStruct: memAddrSt,
        wordLines: 4, ports: [p], desc: "table" }

memoryConnections:
    - { memory: tbl, block: memOwner, instance: oAccessor, port: p }
"""


def run_memory_accessor_uninstantiated_container_domain_cases():
    """The root project generates every container it declares, so an
    accessor's domain is checked inside one that nothing instantiates: on
    another clock than the memory it is rejected, on the memory's own clock
    it builds."""
    def design(accessorClock, accessorReset):
        return MEMORY_ACCESSOR_UNINSTANTIATED_CONTAINER_DESIGN.replace(
            '{accessorClock}', accessorClock).replace('{accessorReset}', accessorReset)

    return all([
        _expect_diagnostic(
            "an accessor in an uninstantiated root container on another clock "
            "than its memory is rejected",
            ("Instance 'oAccessor' accesses memory 'tbl' of block 'memOwner' over "
             "clock 'clkB', but the memory is on 'clk'. A hardware accessor of a "
             "memory must be in the memory's own domain. Bind the accessor's "
             "default clock to 'clk'.",
             "Found 1 Error."),
            design=design('clkB', 'rstB_n'), projectDomains=''),
        _expect_builds(
            "an accessor in an uninstantiated root container on its memory's clock builds",
            design=design('clk', 'rst_n'), projectDomains=''),
    ])


def run_memory_on_owner_output_clock_cases():
    """A memory on an output clock of its owning instance is on the net that
    output drives. Bound to `~`, that clock reaches no net, so a sibling
    accessor cannot be in the memory's domain; bound to a net, an accessor on
    that net is."""
    def design(clkGenBind, accessorBind):
        return MEMORY_OUTPUT_CLOCK_DESIGN.replace(
            '{clkGenBind}', clkGenBind).replace('{accessorBind}', accessorBind)

    return all([
        _expect_diagnostic(
            "an accessor of a memory on an owner output clock bound to `~` is rejected",
            ("'uAccessor' accesses memory 'tbl'", "output clock 'clkGen'",
             "'uMemOwner' binds 'clkGen' to `~`",
             "Bind 'clkGen' of instance 'uMemOwner' to a net"),
            design=design('~', 'clkWrong'), projectDomains=MEMORY_OUTPUT_CLOCK_PROJECT_DOMAINS),
        _expect_builds(
            "an accessor on the net the owner's output clock drives builds",
            design=design('genClk', 'genClk'), projectDomains=MEMORY_OUTPUT_CLOCK_PROJECT_DOMAINS),
    ])


def _run():
    print("=" * 72)
    print("TESTING PER-BLOCK CLOCK AND RESET DERIVATION")
    print("=" * 72)

    groups = (
        ("Declaration completeness", (run_declaration_completeness_cases,)),
        ("Template-facing view", (run_view_build,
                                  run_default_clock_port_resolution_cases,
                                  run_declared_port_connection_clock_mismatch_rejected,
                                  run_connectionmaps_boundary_derives_inside_out,
                                  run_boundary_port_clock_agreement_cases,
                                  run_chained_boundary_port_cases,
                                  run_output_clock_boundary_port_cases,
                                  run_boundary_port_on_clockless_inner_port_rejected)),
        ("Derived tables load at open", (run_derived_tables_loader_cases,)),
        ("Domain references", (run_reference_cases,
                               run_connection_clock_endpoint_cases,
                               run_connection_clock_driven_by_end_cases,
                               run_ambiguous_connection_clock_cases,
                               run_output_clock_port_cases,
                               run_unsupported_direction_cases,
                               run_async_reset_bound_by_name_cases,
                               run_async_reset_bound_by_map_cases,
                               run_output_clock_bindable_cases,
                               run_topdown_port_on_no_default_clock_block_cases)),
        ("Domain agreement", (run_domain_agreement_cases,)),
        ("Instance bind pairs", (run_bind_pair_cases,)),
        ("Instance maps", (run_instance_maps_cases,)),
        ("Local nets", (run_local_net_cases,
                        run_default_clock_local_reset_candidates_cases,
                        run_export_reset_from_unconnected_clock_cases)),
        ("Binding conformance", (run_binding_conformance_cases,)),
        ("Clockless rows", (run_clockless_row_cases,)),
        ("Single-domain objects", (run_single_domain_cases,
                                   run_memory_stated_clock_on_no_default_clock_block_accepted,
                                   run_memory_on_owner_output_clock_cases,
                                   run_memory_accessor_without_default_clock_cases,
                                   run_memory_accessor_without_default_clock_unreachable_rejected,
                                   run_memory_accessor_uninstantiated_container_domain_cases)),
        ("regAccess memory bridge reset", (run_regaccess_memory_bridge_clock_no_reset_rejected,
                                               run_regaccess_memory_bridge_reset_declared_builds,
                                               run_regaccess_memory_bridge_conflicting_resets_rejected,
                                               run_memory_reset_names_wrong_clock_rejected,
                                               run_memory_reset_names_async_reset_rejected)),
        ("Register-bus port domain override (registerBusPort)",
         (run_registerports_reset_disambiguates_bus_port_domain,
          run_topdown_leaf_bus_port_domain_matches_register_clock,
          run_router_bus_on_output_clock_rejected,
          run_router_bus_on_output_reset_rejected,
          run_router_bus_without_reset_rejected,
          run_router_bus_async_reset_rejected,
          run_router_with_children_rejected,
          run_multi_clock_router_bus_reset_rejected_as_multi_clock,
          run_passthrough_register_ports_without_bus_reset_rejected)),
        ("hasVl BFM port reset", (run_hasvl_port_reset_cases,)),
        ("Name collisions", (run_collision_cases,)),
        ("Graph shape", (run_clock_tree_shape_cases,)),
        ("Standalone attribute resolution", (run_standalone_period_cases,)),
        ("Reset-clock membership", (run_top_rejects_reset_on_unbound_clock,
                                       run_standalone_rejects_reset_on_output_clock)),
        ("End-of-run report", (run_end_of_run_report_cases,)),
    )
    results = []
    for title, runners in groups:
        print(f"\n{title}")
        print("-" * 72)
        for runner in runners:
            results.append(runner())

    print()
    print("=" * 72)
    if all(results):
        print("RESULT: all clock and reset derivation checks passed")
        return 0
    print("RESULT: clock and reset derivation checks FAILED")
    return 1


def run_all_tests():
    return _run()


if __name__ == '__main__':
    sys.exit(_run())
