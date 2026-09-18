#!/usr/bin/env python3
"""Coverage for per-block clock and reset declaration (spec R5): a block's
clocks and resets are exactly its own clocks:/resets: entries, or the
implicit clk/rst_n, for a container as for a leaf. Nothing is inferred from
a block's children, connections or containment.

Groups: the completeness rule itself (implicit clk/rst_n, an explicitly
empty resets:); the template-facing view (getBlockData, including a port's
selected reset); the V1/V2/V6 validation diagnostics; the single-domain
rules for memories and register buses, driven directly against the check
because authoring a memory decode hierarchy would say nothing extra about
the rule; and project-scope name collisions, unaffected by this rule since
they are a project-file concern.

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
    """R5: a block's clocks and resets are exactly what it declares.

    'spare' declares neither, so it gets the implicit clk/rst_n. 'cons'
    declares an explicitly empty resets: {}, which means a block with no
    reset at all, distinct from omitting resets: entirely (which is what
    gives 'spare' its implicit rst_n). A second, separate build repeats the
    empty-resets case as a list (resets: []), on a leaf again rather than on
    'dut': 'dut' is prod/cons/spare's container, and a container with no
    reset of its own leaves its children's implicit rst_n with nothing to
    fall back to (V11) - a different rule this fixture is not for."""
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
                    f"clocks=['clk'], resets=['rst_n'] (R5)")
            return True

        def empty_mapping_resets_means_none():
            clocks, resets = _clock_reset_rows(db_path, 'cons')
            if resets:
                raise AssertionError(
                    f"'cons' declares resets: {{}} and persisted resets="
                    f"{resets}, expected none: an explicitly empty resets: "
                    f"is distinct from omitting it (spec §4.2)")
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
                    f"the same as the empty mapping form (spec §4.2)")
            return True

        results.append(_run_case(
            "a block declaring resets: [] has no reset at all",
            empty_list_resets_means_none))
        return all(results)
    finally:
        shutil.rmtree(fixture)


def run_view_build():
    """getBlockData() surfaces the block's own declared clocks/resets, in
    declaration order with period (R18), and gives a port the SELECTED
    reset of its own clock (V19) - not the block's first declared reset on
    that clock, which getBDPortDomainReset used to return regardless of
    which one the block itself marked default."""
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
    # every input reset of the top block must bind to something (V3).
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
                    f"['clk', 'clkSlow']: declaration order (R18)")
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
            # merely declared first - the exact distinction
            # getBDPortDomainReset dropped.
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
    """R7: a declared port naming no clock: resolves to the block DEFAULT
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
    # library leaf, R7 in isolation from any binding) and top_tb declares
    # nothing of its own, so the default single implicit clk/rst_n is all
    # the testbench needs to bind (V10) - PROJECT_DOMAINS' extra clkSlow
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
                f"unstated means the block DEFAULT clock (R7), not the "
                f"first declared (clkSlow)")
        return _run_case(
            "a declared port naming no clock resolves to the block default, "
            "not its first declared clock", lambda: True)
    finally:
        shutil.rmtree(fixture)


def run_declared_port_connection_mismatch_v14_rejected():
    """V14 (pysrc/clockTree.py build()): a declared port's clock: (its own,
    or the block default when it names none) and a connection reaching it
    are not read as a precedence; where both are present they must agree.
    Checked in projectCreate now, against the container binding
    clockTree.build() itself computed, so a disagreeing design fails the
    database build, not just a later view render."""
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
        ['V14'], design=design)


def run_connectionmaps_boundary_derives_inside_out_v16():
    """V16 (pysrc/clockTree.py build()): a connectionMaps: boundary port
    derives its domain inside-out from the inner port it routes to, not from
    the block default an unstated outer connection would otherwise give it.
    'dut' declares clk (default) and apbClk; its own 'apbReg' boundary port
    names no clock: and is reached by an outer connection naming none either
    (rule 3 would give it clk), but connectionMaps: bridges it inward to
    'uInner', whose own declared port 'regs' names clock: apbClk explicitly
    (rule 1) - so the boundary port's derived domain must be apbClk, not
    clk. The fact is computed once in projectCreate and persisted (the
    non-schema portDomains table); getBlockData()'s view reads it back
    rather than re-deriving it, so this is checked the same way as before -
    through getBDPortDomain, after open.

    A second boundary port ('apbReg2', bridged to 'uInner2') covers a
    TOP-DOWN inner port: 'inner2' declares no ports:/registerPorts: at all
    for 'regs2', so it takes its own block's default clock (clkTick, not
    dut's), renamed onto dut's apbClk by uInner2's own instance map (the
    uSlowTick shape, examples/twoClk/yaml/twoClk.yaml: a reusable IP's own
    clock renamed at its assembler). Before the fix the view fell to dut's
    OUTER default clock (clk) whenever the inner port declared nothing,
    silently wrong for exactly this renamed case."""
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
            clk:    { default: true }
            apbClk: { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
    prod: { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "container: its own boundary port names no clock:"
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
            apbReg: { interface: dataIf, direction: dst }
            apbReg2: { interface: dataIf, direction: dst }
    inner:
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
    uProd:   { container: top_tb, instanceType: prod,   instGroup: top }
    uProd2:  { container: top_tb, instanceType: prod,   instGroup: top }
    uDut:    { container: top_tb, instanceType: dut,    instGroup: top }
    uInner:  { container: dut,    instanceType: inner,  instGroup: top }
    uInner2: { container: dut,    instanceType: inner2, instGroup: top,
              clocks: { clkTick: apbClk }, resets: { rstTick_n: apbRst_n } }

connections:
    - { interface: dataIf, src: uProd,  srcport: out, dst: uDut, dstport: apbReg }
    - { interface: dataIf, src: uProd2, srcport: out, dst: uDut, dstport: apbReg2 }

connectionMaps:
    - { interface: dataIf, block: dut, direction: dst, instance: uInner,  port: apbReg,  instancePort: regs }
    - { interface: dataIf, block: dut, direction: dst, instance: uInner2, port: apbReg2, instancePort: regs2 }
"""
    # A dedicated projectDomains: this design's own top_tb names its clocks
    # clk/apbClk (not PROJECT_DOMAINS' clk/clkSlow), so the testbench must
    # match those names for V10 to bind them.
    projectDomains = """
clocks:
    clk:    { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    apbClk: { desc: "the register-bus clock", period: 3, timeUnit: ns }

resets:
    rst_n:    { desc: "the default reset", default: true, clock: clk }
    apbRst_n: { desc: "the register-bus reset", clock: apbClk }
"""
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains=projectDomains)
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
                f"inner port it routes to (V16), not from the block default "
                f"an unstated outer connection would otherwise give it")
        domain2 = view['ports']['connections']['apbReg2']['domainClock']
        if domain2 != 'apbClk':
            raise AssertionError(
                f"'apbReg2' reports domainClock {domain2!r}, expected 'apbClk': "
                f"a TOP-DOWN inner port (declared nowhere) takes its own "
                f"block's default clock, mapped outward through its "
                f"instance's own rename (V16), not dut's own default clock")
        # The SAME connectionMaps: row, read from the ROUTED-TO block's own
        # self-render (getBlockData(innerKey), where ret['instances'] is
        # every instance OF 'inner' itself, not dut's children): getBDPorts'
        # connectionMapPorts-sourced view keys this port by instancePortName
        # ('regs'), not the boundary's own port: name ('apbReg' - `port:`
        # and `instancePort:` differ on this very row). getBDPortDomain's
        # own rule-2 gate must still find the row's boundary domain here,
        # not fall through to rule 3 (the block default), by reading the
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
    # this design to consume it (V10).
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
    rejected (V13, clockTree.build()). A connection's clock: is a container
    reference validated against the container's own nets, not a project-scoped
    name (spec §4.3): unlike the baseline, there is no project 'clocks:'
    section to check it against first. A block's own clocks:/resets: entry
    needs no reference check at all: it is a fresh declaration, not a
    reference, so there is no name to misspell (spec R5)."""
    return _expect_diagnostic(
        "a connection clock: naming an undeclared clock is rejected",
        ('noSuchClock', 'V13'),
        connectionClock=', clock: noSuchClock')


def run_connection_clock_endpoint_cases():
    """V13: a connection's clock: must name a clock BOTH endpoint blocks
    declare (name match only - this fixture has no instance map). 'clkSlow'
    is a real project clock (PROJECT_DOMAINS), so this is
    not the reference check above: an undeclared BLOCK clock silently
    landed on the block default before this check existed, discarding the
    author's stated domain with no diagnostic."""
    results = [_expect_diagnostic(
        "a connection clock: naming a clock neither endpoint block "
        "declares is rejected",
        ('prod', 'clkSlow', 'V13'),
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
    # clk), so PROJECT_DOMAINS' clk/rst_n would have nothing to bind (V10).
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


def run_unsupported_direction_cases():
    """`async: true` on a reset is bindable (spec §4.2): an asynchronous
    reset input takes no default fallback (R10), only a map entry or a name
    match, so 'cons' declaring one with no matching name in its container
    'dut' (which declares no resets: of its own) is a V4 error naming the
    reset and the block, not an "unsupported" rejection. `direction: output`
    on a clock is bindable too (run_output_clock_bindable_cases)."""
    return _expect_diagnostic(
        "an unbound async reset input is rejected (V4), not the shape itself",
        ('cons', 'rstA_n', 'V4'),
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
    """An asynchronous reset input binds by an ordinary name match (spec
    §4.4) when its container declares a reset of the same name: 'top_tb'
    declares 'rstA_n' and 'cons' consumes it as an async input, with no
    instance map at all. One level, top_tb directly containing 'cons',
    keeps 'rstA_n' from also needing a SECOND, outer binding of its own
    (spec R9: the input clock/reset the map or name match resolves is a
    net of the child's OWN container only, not chased further up)."""
    # A dedicated projectDomains: top_tb IS the topInstance here, so its own
    # extra reset rstA_n must also bind to a matching testbench entry (V3).
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
    """An asynchronous reset input binds by an explicit instance map (spec
    §4.4), and is exempt from V6 clock membership (spec §4.2): 'uCons' maps
    its async 'rstA_n' onto 'rstSlow_n', which belongs to 'clkSlow', while
    'cons' itself runs on the implicit 'clk' (bound to 'dut's 'clk' by name
    match) - a mismatch V6 would reject for a SYNCHRONOUS reset, but an
    asynchronous reset input belongs to no clock of its own, so it builds."""
    fixture, project_path, db_path = _make_fixture(design=ASYNC_MAP_DESIGN)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: an async reset input mapped across clocks builds\n{output}")
            return False
        print("PASS: an async reset input mapped across clocks builds, exempt from V6")
        return True
    finally:
        shutil.rmtree(fixture)


def run_output_clock_bindable_cases():
    """`direction: output` on a clock is bindable (spec §4.5): an output's
    map entry is required (V3) and its value is `~` to leave it
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
    # this design to consume it (V10).
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


# ----------------------------------------------------------------- V21 --

V21_PROJECT_TWO_CLOCKS = """
clocks:
    clkA: { desc: "default testbench clock", default: true, period: 7, timeUnit: ns }
    clkB: { desc: "second testbench clock", period: 9, timeUnit: ns }

resets:
    rst_n:  { desc: "clkA's reset", default: true, clock: clkA }
    rstB_n: { desc: "clkB's reset", clock: clkB }
"""

V21_TOP_TWO_CLOCKS = """blocks:
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


def run_v21_agrees_through_both_instances():
    """V21 positive: 'leaf' declares no period:, but both of its instances
    bind clk to the same testbench clock clkA - the design determines its
    period (7 ns), read back from the generated standalone wrapper."""
    design = V21_TOP_TWO_CLOCKS + """    leaf:
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
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains=V21_PROJECT_TWO_CLOCKS)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: V21 agreement through two instances builds\n{output}")
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
        print("PASS: V21 resolves through two agreeing instances to clkA's own period")
        return True
    finally:
        shutil.rmtree(fixture)


def run_v21_declared_period_wins_over_disagreement():
    """V21 positive: 'leaf' declares its own period:, so a disagreement
    between its two instances' resolved clocks is immaterial - the
    declaration wins outright."""
    design = V21_TOP_TWO_CLOCKS + """    leaf:
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
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains=V21_PROJECT_TWO_CLOCKS)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: V21 declared period wins builds\n{output}")
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
        print("PASS: V21 a declared period wins even though the two instances disagree")
        return True
    finally:
        shutil.rmtree(fixture)


def run_v21_rejects_disagreement():
    """V21 negative: 'leaf' declares no period: and its two instances
    resolve to different testbench clocks - an error naming both instances
    (spec V21 "an error naming the instances that disagree")."""
    design = V21_TOP_TWO_CLOCKS + """    leaf:
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
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains=V21_PROJECT_TWO_CLOCKS)
    try:
        code, output = _build(project_path, db_path)
        if code == 0:
            print(f"FAIL: V21 disagreeing instances built successfully\n{output}")
            return False
        ok = all(needle in output for needle in ('V21', 'uLeafA', 'uLeafB'))
        print(f"{'PASS' if ok else 'FAIL'}: V21 rejects two instances resolving to "
              f"different testbench clocks, naming both{'' if ok else chr(10) + output}")
        return ok
    finally:
        shutil.rmtree(fixture)


def run_v21_rejects_supplier_output():
    """V21 negative: 'leaf' declares no period: and its instance resolves to
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
            print(f"FAIL: V21 resolving to a supplier's output built successfully\n{output}")
            return False
        ok = all(needle in output for needle in ('V21', 'uLeaf', "supplier"))
        print(f"{'PASS' if ok else 'FAIL'}: V21 rejects a clock resolving to a supplier's "
              f"output with no declared period{'' if ok else chr(10) + output}")
        return ok
    finally:
        shutil.rmtree(fixture)


def run_v21_rejects_zero_instance():
    """V21 negative: 'leaf' declares no period: and is never instantiated at
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
            print(f"FAIL: V21 on a zero-instance hasVl block built successfully\n{output}")
            return False
        ok = all(needle in output for needle in ('V21', 'leaf', 'no instance'))
        print(f"{'PASS' if ok else 'FAIL'}: V21 rejects a zero-instance hasVl block with no "
              f"declared period{'' if ok else chr(10) + output}")
        return ok
    finally:
        shutil.rmtree(fixture)


def run_v21_cases():
    return all([
        run_v21_agrees_through_both_instances(),
        run_v21_declared_period_wins_over_disagreement(),
        run_v21_rejects_disagreement(),
        run_v21_rejects_supplier_output(),
        run_v21_rejects_zero_instance(),
    ])


# ------------------------------------------------------------------ V9 --

def run_v9_top_rejects_reset_on_unbound_clock():
    """V9 negative, at the design top: top_tb's own INPUT reset 'rstOut_n'
    belongs to 'clkOut', an OUTPUT clock of top_tb. 'rstOut_n' itself binds
    fine (the testbench declares a matching name), but its own clock never
    does - clkOut is an output, never bound to a testbench net at all - so
    the testbench would be releasing a reset of a clock it does not
    generate."""
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
        ok = 'V9' in output
        print(f"{'PASS' if ok else 'FAIL'}: V9 rejects a top input reset whose own clock is "
              f"never bound to a testbench net{'' if ok else chr(10) + output}")
        return ok
    finally:
        shutil.rmtree(fixture)


def run_v9_standalone_rejects_reset_on_output_clock():
    """V9 for a standalone hasVl block (spec §4.8): 'leaf' is hasVl and its
    reset 'rst2_n' belongs to 'clk2', an OUTPUT clock of 'leaf' itself - a
    standalone build cannot count release cycles on an observed output
    clock, which may not run before its own release."""
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
    # rst2_n is mapped directly onto top_tb's own rst_n so the ordinary
    # instance binding succeeds cleanly (clk2 has no clockBindNet entry - an
    # output is never bound as an input clock - so V6's membership check is
    # not reached either); the ONLY diagnostic this fixture can raise is the
    # standalone-specific V9 check under test.
    fixture, project_path, db_path = _make_fixture(design=design, projectDomains='')
    try:
        code, output = _build(project_path, db_path)
        if code == 0:
            print(f"FAIL: a standalone reset on an output clock built successfully\n{output}")
            return False
        ok = all(needle in output for needle in ('V9', 'leaf', 'rst2_n'))
        print(f"{'PASS' if ok else 'FAIL'}: V9 rejects a standalone hasVl block's reset "
              f"belonging to its own output clock{'' if ok else chr(10) + output}")
        return ok
    finally:
        shutil.rmtree(fixture)


# ------------------------------------------------------- end-of-run report --

def run_end_of_run_report_cases():
    """R23 end-of-run report (spec §4.8): a hasVl block with an output clock
    and an output reset gets an end_of_simulation() override reporting both
    (plan item 4); a hasVl block with no outputs at all gets no override,
    so the fix that scoped the override does not regress into emitting an
    empty one everywhere."""
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
    """V1: a block reset's clock: names a block clock of the same block.
    V2: a port's, registerPorts:, addressBlock: or memory's clock:/reset:
    does too. The existence part of both is the schema's blockClock/
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
    """V6: a reset bound by name match must belong to the clock its own
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
        ('uCons', 'cons', 'top_tb', "'clkB'", "'rst_n'", "'clk'", 'V6'),
        design=design)


# --------------------------------------------------------- instance maps --

def run_instance_map_bad_key_rejected():
    """V4: a map key must name a block clock of the instantiated block."""
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
        ('uCons', 'clkBogus', 'cons', 'V4'),
        design=design)


def run_instance_map_bad_value_rejected():
    """V4: a map value must name a declared clock/reset of the container (a
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
        ('uCons', 'cons', 'top_tb', 'noSuchNet', 'V4'),
        design=design)


def run_instance_map_kind_mismatch_rejected():
    """V4: a clock map entry must bind a clock net, not a reset net (and a
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
        ('uCons', 'cons', 'top_tb', 'rst_n', 'V4'),
        design=design)


def run_instance_map_renamed_v13_accepted():
    """V13 through a renamed instance map: a connection's clock: derives to
    exactly one input clock of the instance, even though the block's own
    clock name (clkC) differs from the container's (clkSlow) - the exact
    composition-and-renaming shape spec §4.4 exists for."""
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
        print(f"FAIL: a renamed instance map still resolves V13 to the "
              f"one renamed input clock\n{output}")
        return False
    print("PASS: a renamed instance map still resolves V13 to the one "
          "renamed input clock")
    return True


def run_instance_maps_cases():
    return all([
        run_instance_map_bad_key_rejected(),
        run_instance_map_bad_value_rejected(),
        run_instance_map_kind_mismatch_rejected(),
        run_instance_map_renamed_v13_accepted(),
    ])


# --------------------------------------------------------------- local nets --

# A generator with an output clock, and a consumer, both inside 'dut': the
# generator's output binding names 'clkGen', a name 'dut' does not declare,
# creating a local net; the consumer's own 'clk' binds to it by an explicit
# map (spec §4.5).
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
    creates a local net (spec §4.5): kind 'local', driven by the output
    ('childOutput'), consumed by the other child's own map entry."""
    # projectDomains='': top_tb declares nothing of its own (implicit
    # clk/rst_n only); PROJECT_DOMAINS' extra clkSlow would have nothing in
    # this design to consume it (V10).
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
    """V22: a local net with no child input consumer is an error naming the
    driving binding."""
    design = LOCAL_NET_DESIGN.replace(
        "    uCons:  { container: dut,    instanceType: cons,   instGroup: top,\n"
        "              clocks: { clk: clkGen } }\n",
        "    uCons:  { container: dut,    instanceType: cons,   instGroup: top }\n")
    assert design != LOCAL_NET_DESIGN, "the uCons replacement did not match"
    return _expect_diagnostic(
        "a local net with no consumer is rejected",
        ('dut', 'clkGen', 'uGen', 'genClk', 'V22'),
        design=design, projectDomains='')


def run_output_bound_to_container_input_rejected():
    """V5: an output may not bind to a container INPUT, which already has a
    driver (its own parent)."""
    design = LOCAL_NET_DESIGN.replace(
        "clocks: { clk: sysClk, genClk: clkGen }", "clocks: { clk: sysClk, genClk: sysClk }")
    assert design != LOCAL_NET_DESIGN, "the genClk replacement did not match"
    return _expect_diagnostic(
        "an output bound to a container input is rejected",
        ('uGen', 'genClk', 'sysClk', 'V5'),
        design=design)


def run_two_outputs_one_net_rejected():
    """V5: two child outputs bound to the same local net name is a second
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
        ('dut', 'clkGen', 'V5'),
        design=design)


def run_declared_output_undriven_gets_own_implementation():
    """spec §4.6 table: a declared output no child drives is driven by the
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
    # this design to consume it (V10).
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


# --------------------------------------------- single-domain object rules --

class _StubDiag:
    """The diag protocol clockTree needs: `logError` collects rather than
    exits, unlike the real one - `continueOnError` is a module-level False
    with no setter anywhere in the tree, so a production build reports at
    most ONE of these diagnostics. The message counts below are properties
    of this harness, and what they assert is that a given shape produces
    exactly one diagnostic and not a second spurious one.
    `diagnosticLocation` is part of the protocol; no test here builds
    through BlockDomains.build()/clockTree.build(), the only callers, so it
    is never actually invoked.
    """

    def __init__(self):
        self.messages = []

    def logError(self, msg):
        self.messages.append(msg)

    def diagnosticLocation(self, yamlFile, lc):
        return yamlFile


def _validateRouterDomain(routerClocks):
    """Run ClockTree.check() over one synthetic router BlockDomains.

    THIS EXERCISES THE CHECK IN ISOLATION, not a build: BlockDomains built by
    hand, not by BlockDomains.build(), so a multi-clock router needs no
    default-clock marking of its own (V18, irrelevant to this rule) to reach
    the check. Every synthetic block is instantiated at the top so it is
    reachable; the pruning of unreachable routers is what the end-to-end
    cases cover (run_router_domain_cases).
    """
    clocks = OrderedDict(
        (name, clockTree.ClockDecl(desc='', direction='input',
                                   default=(index == 0), period='', timeUnit='ns'))
        for index, name in enumerate(routerClocks))
    domains = {
        'router/top.yaml': clockTree.BlockDomains(
            'router/top.yaml', 'router', clocks, OrderedDict(), routerClocks[0], {},
            True, False, [], {}),
    }
    root = clockTree.Container(clockTree.ClockTree.ROOT_KEY)
    root.instances['u_router/top.yaml'] = 'router/top.yaml'
    diag = _StubDiag()
    tree = clockTree.ClockTree(domains, {}, root, diag, [])
    tree.check()
    return diag.messages


# A memory owner (implicit clk) and one hardware accessor, so V8 (spec §4.3,
# §4.3 "Memories": a hardware accessor via memoryConnections: must be in the
# memory's own domain) can be driven through a real build rather than by hand:
# unlike the OLD project-scoped `clock:` literal this rule reads instead the
# accessor's own resolved container clock, which only a real instance bind
# produces.
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
        ('uAccessor', 'tbl', 'memOwner', 'clkSlow', 'clk', 'V8'),
        design=MEMORY_ACCESS_DESIGN.format(
            accessorClocks="        clocks:\n"
                          "            clkSlow: { }\n"
                          "        resets:\n"
                          "            rstSlow_n: { clock: clkSlow }\n")))

    def router_one_domain_accepted():
        messages = _validateRouterDomain(['clkSlow'])
        if messages:
            raise AssertionError(
                f"a router wholly in one non-default domain was rejected: "
                f"{messages}. A router takes the clock of its register bus, "
                f"whichever domain that is.")
        return True

    def router_two_domains_rejected():
        messages = _validateRouterDomain(['clk', 'clkSlow'])
        if len(messages) != 1:
            raise AssertionError(
                f"expected exactly one diagnostic, got {messages}")
        for needle in ('router', "'clk'", "'clkSlow'", 'single-domain module'):
            if needle not in messages[0]:
                raise AssertionError(
                    f"the message does not mention '{needle}'. It has to name the "
                    f"router, both clocks, and the condition - a router does not own "
                    f"its bus clock, so 'put both in one domain' is a dead end here: "
                    f"{messages[0]}")
        # Deliberately NOT asserting a remedy. Three routes widen a router's set
        # with no clocks: entry to remove (a contained instance whose block
        # declares its own clocks, a non-register connection carrying clock:, a
        # second register-bus connection), so pinning one prescription here would
        # re-lock a message that is wrong for those authors.
        return True

    def router_rule_is_on_cardinality_not_order():
        """The bus clock coming FIRST does not make a two-clock router legal.

        The emitter reads the first entry, so this shape happens to emit the right
        clock - and is still rejected, because the router would declare a second
        clock port that nothing clocks."""
        messages = _validateRouterDomain(['clkSlow', 'clkPico'])
        if len(messages) != 1:
            raise AssertionError(
                f"a two-clock router whose bus clock sorts first was accepted "
                f"({messages}); the rule is on the size of the set")
        return True

    for label, fn in (
            ("a memory accessor in the memory's own domain is accepted",
             memory_accessor_same_domain_accepted),
            ("a router wholly in one non-default domain is accepted",
             router_one_domain_accepted),
            ("a router resolving to two clocks is rejected by name",
             router_two_domains_rejected),
            ("a two-clock router is rejected however the set is ordered",
             router_rule_is_on_cardinality_not_order)):
        results.append(_run_case(label, fn))
    return all(results)


# --------------------------------------- V24 (regAccess memory, R20 bridge) --

# A router-served, TOP-DOWN leaf (no registerPorts:, so R25's top-down
# selection resolves its register bus from the router dispatching to it) on
# two clocks, with a regAccess memory the '%s' slot places on either one -
# 'clk', the router's own bus clock, for the positive shape, or 'clkPix' for
# the negative one. `%`-substituted rather than `.format()`-substituted: the
# design otherwise reads as ordinary YAML, with none of `.format()`'s braces
# to escape.
V24_DESIGN = """constants:
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
            rstPix_n: { clock: clkPix }
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
            clk:    { default: true }
            clkPix: { }
        resets:
            rst_n:    { clock: clk }
            rstPix_n: { clock: clkPix }

instances:
    top_tb:     { container: top_tb, instanceType: top_tb,    instGroup: top }
    uCPU:       { container: top_tb, instanceType: cpu,       instGroup: top }
    uAPBDecode: { container: top_tb, instanceType: apbDecode, instGroup: top }
    uLeafA:     { container: top_tb, instanceType: leafA,     instGroup: top, addressGroup: top }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

memories:
    - { memory: tbl, block: leafA, structure: memSt, addressStruct: memAddrSt, wordLines: TBL_WORDS, ports: [p], regAccess: true, desc: "leafA regAccess table"%s }
"""

V24_PROJECT_DOMAINS = """
clocks:
    clk:    { desc: "the default testbench clock", default: true, period: 1, timeUnit: ns }
    clkPix: { desc: "a second testbench clock", period: 2, timeUnit: ns }

resets:
    rst_n:    { desc: "the default reset", default: true, clock: clk }
    rstPix_n: { desc: "clkPix's reset", clock: clkPix }
"""


def run_v24_regaccess_memory_domain_cases():
    """V24 (spec R20/V24): until the register-handler bridge exists (plan
    §6 phase 6), a regAccess memory on a clock other than its block's own
    register bus clock is rejected at build, rather than silently generating
    a handler whose memory-side flops are actually driven by the bus clock.

    The positive shape - 'tbl' declared on 'clk', the same clock 'apbDecode'
    dispatches leafA's register bus on - already builds in
    test_clock_reset_emission.py (its own leafA fixture, ~438-439/657-665,
    declares two regAccess memories on the feed clock for exactly this
    reason), so it is not repeated here."""
    return _expect_diagnostic(
        "a regAccess memory on a clock other than its block's register bus "
        "clock is rejected",
        ('V24', 'tbl', 'leafA', 'clkPix', "'clk'"),
        design=V24_DESIGN % ', clock: clkPix', projectDomains=V24_PROJECT_DOMAINS)


# ---------------------- register-bus port domain override (getBDPorts) --

# A reusable-IP hasVl leaf whose registerPorts: names its own clock and, to
# pick between two unmarked resets on it, its own reset: too (spec ~388-390,
# V19): neither reset is marked default: true, so apbClk's shared selectedReset
# is None.
V25_REGISTER_BUS_PORT_DESIGN = """constants:
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

V25_PROJECT_DOMAINS = """
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
        design=V25_REGISTER_BUS_PORT_DESIGN, projectDomains=V25_PROJECT_DOMAINS)
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
    connection) with registerClock/registerReset (R25's own selection), not
    the domain a plain V16 connectionMaps boundary derivation would read off
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
                    f"expected 'clkCap'/'rstCap_n': R25's own bus clock/reset "
                    f"selection, not the handler's initial name-match bind")
            return True

        return _run_case(
            "a top-down leaf's register-bus port takes R25's own "
            "registerClock/registerReset selection",
            bus_port_takes_the_leaf_register_clock)
    finally:
        shutil.rmtree(fixture)


# -------------------------------------------- V19, hasVl BFM port clause --

# A hasVl leaf whose one declared interface port is reached by a real
# connection (module_hdl_wrapper.py's BFM binds only a port something
# actually produces), so the fixture can vary the port's own clock's
# resets without touching connectivity.
V19_HASVL_INTF = """types:
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
V19_APB_PROJECT_DOMAINS = """
clocks:
    clk:    { desc: "the default testbench clock", default: true, period: 1, timeUnit: ns }
    apbClk: { desc: "the register-bus testbench clock", period: 3, timeUnit: ns }

resets:
    rst_n:    { desc: "the default reset", default: true, clock: clk }
    apbRst_n: { desc: "the register-bus reset", clock: apbClk }
"""


def run_v19_hasvl_port_ambiguous_reset_rejected():
    """V19 negative A: 'leaf's declared port 'in' is timed by 'clkB', which
    carries two resets and neither is marked default: true - the co-
    simulation wrapper has no reset to bind the port's BFM to. 'leaf' is
    instantiated (bound onto 'top_tb's own clk/rst_n by name match) so V21's
    zero-instance check does not also fire alongside V19."""
    design = V19_HASVL_INTF + """blocks:
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
        ('V19', 'leaf', 'in', 'clkB', 'rstB1_n', 'rstB2_n'),
        design=design, projectDomains='')


def run_v19_hasvl_port_no_reset_at_all_rejected():
    """V19 negative B: 'leaf' declares resets: {} - a block with no reset at
    all is otherwise legitimate (spec §4.2) - but its declared port 'in'
    still needs one, since it is hasVl and the co-simulation wrapper's BFM
    is generated logic under V19. 'leaf' is instantiated so V21's
    zero-instance check does not also fire alongside V19."""
    design = V19_HASVL_INTF + """blocks:
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
        ('V19', 'leaf', 'in'),
        design=design, projectDomains='')


def run_v19_hasvl_connection_derived_port_rejected():
    """V19 negative, connection-derived port (a genuine defect fixed here):
    'leaf' declares no ports: at all, so its one port 'in' is an ordinary
    top-down port (spec §4.3), entirely defined by the connection reaching
    it. The connection names clock: clkSlow, which 'uProd's own instance map
    (clocks: { clk: clkSlow }) resolves 'uProd's clk onto - the consumer-edge
    match V13 itself performs - so 'in' is timed by 'leaf's 'clkB' (bound
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
        ('V19', 'leaf', 'in', 'clkB'),
        design=V19_HASVL_INTF + design, projectDomains=PROJECT_DOMAINS)


def run_v19_hasvl_connectionmaps_boundary_port_rejected():
    """V19 negative, connectionMaps boundary port (the portDomainsByBlock
    branch): hasVl container 'dut' declares its own boundary port 'apbReg'
    with no clock: of its own, bridged inward via connectionMaps to
    'inner's 'regs' port, which does name clock: apbClk explicitly - the
    inside-out V16 derivation gives 'apbReg' the domain 'apbClk', which
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
        ports:
            apbReg: { interface: dataIf, direction: dst }
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
        ('V19', 'dut', 'apbReg', 'apbClk', 'apbRstA_n', 'apbRstB_n'),
        design=V19_HASVL_INTF + design, projectDomains=V19_APB_PROJECT_DOMAINS)


def run_v19_hasvl_connectionmaps_boundary_port_not_derived_twice():
    """V19 positive (a genuine defect fixed here): as the negative above,
    but 'dut' declares no ports: at all - 'apbReg' is a PURE connectionMaps
    boundary port, reached ALSO by the outer connection (top-down). The
    connection authors clock: clkX, which 'uDut's own instance map resolves
    'dut's clkX onto - a THIRD clock, ambiguous on 'dut' (rstX1_n/rstX2_n,
    neither default), entirely distinct from 'apbClk' (the connectionMaps
    boundary row's own, correct domain, with a clean sole reset). Before the
    fix, the connection-derived branch did not know 'apbReg' was already a
    boundary port and derived it a second time, from clkX - spuriously
    rejecting a build that must succeed, since the boundary row's own
    'apbClk' has one reset."""
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
            clkX:   { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
            rstX1_n:  { clock: clkX }
            rstX2_n:  { clock: clkX }
    prod: { desc: "producer", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    dut:
        desc: "hasVl container: apbReg is a pure connectionMaps boundary port, also reached by the outer connection"
        hasVl: true
        hasMdl: true
        hasTb: false
        hasRtl: true
        clocks:
            clk:    { default: true }
            apbClk: { }
            clkX:   { }
        resets:
            rst_n:    { clock: clk }
            apbRst_n: { clock: apbClk }
            rstX1_n:  { clock: clkX }
            rstX2_n:  { clock: clkX }
    inner:
        desc: "inner instance; its own declared port names clock: apbClk explicitly"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: true
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
    uProd:  { container: top_tb, instanceType: prod,   instGroup: top,
              clocks: { clk: clkX }, resets: { rst_n: rstX1_n } }
    uDut:   { container: top_tb, instanceType: dut,    instGroup: top,
              clocks: { clkX: clkX } }
    uInner: { container: dut,    instanceType: inner,  instGroup: top }

connections:
    - { interface: dataIf, src: uProd, srcport: out, dst: uDut, dstport: apbReg, clock: clkX }

connectionMaps:
    - { interface: dataIf, block: dut, direction: dst, instance: uInner, port: apbReg, instancePort: regs }
"""
    projectDomains = """
clocks:
    clk:    { desc: "the default testbench clock", default: true, period: 1, timeUnit: ns }
    apbClk: { desc: "the register-bus testbench clock", period: 3, timeUnit: ns }
    clkX:   { desc: "a third testbench clock", period: 5, timeUnit: ns }

resets:
    rst_n:    { desc: "the default reset", default: true, clock: clk }
    apbRst_n: { desc: "the register-bus reset", clock: apbClk }
    rstX1_n:  { desc: "clkX's first reset", clock: clkX }
    rstX2_n:  { desc: "clkX's second reset", clock: clkX }
"""

    def check():
        fixture, project_path, db_path = _make_fixture(
            design=V19_HASVL_INTF + design, projectDomains=projectDomains)
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code != 0:
            raise AssertionError(
                f"a hasVl container's connectionMaps boundary port was "
                f"spuriously derived a second time, from the outer "
                f"connection's own clock, and rejected:\n{output}")
        return True

    return _run_case(
        "a hasVl container's connectionMaps boundary port, also reached by "
        "the outer connection, is not derived a second time",
        check)


def run_v19_hasvl_output_clock_port_rejected():
    """V19 negative, direction: output clock: 'leaf' declares its port
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
        ('V19', 'leaf', 'outp', 'clkOut', 'rstOutA_n', 'rstOutB_n'),
        design=V19_HASVL_INTF + design, projectDomains='')


def run_v19_hasvl_output_clock_port_positive():
    """V19 positive, direction: output clock: as above, but 'clkOut's one
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
            design=V19_HASVL_INTF + design, projectDomains='')
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


def run_v19_hasvl_port_positive():
    """V19 positive: 'leaf's one declared port takes the block default
    clock, whose sole (implicit) reset is its selected one - the ordinary
    shape, which must not be rejected."""
    design = V19_HASVL_INTF + """blocks:
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


def run_v19_hasvl_two_instances_same_port_not_duplicated():
    """V19 dedupe (a genuine defect fixed here): 'leaf' is instantiated
    TWICE, each instance's port 'in' connected from its own producer, one
    shared clock with no reset at all. Before the fix, portsByClock
    appended one entry per connection end rather than per port name, so the
    diagnostic listed 'in, in' - once for each instance - though a hasVl
    BLOCK's ports are named once, regardless of instance count."""
    design = V19_HASVL_INTF + """blocks:
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


# APB register-bus preamble (constants/types/structures/interfaces), the
# same shape as V25_REGISTER_BUS_PORT_DESIGN's, reused here for a top-down
# (registerPorts:-less) hasVl leaf instead of a reusable IP.
V19_TOPDOWN_APB_PREAMBLE = """constants:
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
"""

# 'leafD' is a top-down hasVl leaf (no registerPorts:): its register bus
# ('apbReg') is inferred from 'apbDecode's dispatch (R25), on 'apbClk', with
# a clean single reset 'apbRst_n'. Its DEFAULT clock is 'clkD' (V18 forbids
# an ambiguous reset there); a second, non-default clock literally named
# 'clk' carries two unmarked resets instead - unrelated to the bus, but the
# literal name a synthesised register handler's own implicit clock always
# takes. The handler (leafD_regs) binds inside leafD's own body by plain
# name match (comment at clockTree.py's BlockDomains.registerBusPort), so
# the handler-bridged connectionMaps boundary guess for 'apbReg' lands on
# 'clk', not on the leaf's real bus clock 'apbClk' - the guess this clause
# must not blame the register-bus port for.
V19_TOPDOWN_BUS_PORT_DESIGN = V19_TOPDOWN_APB_PREAMBLE + """blocks:
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

V19_TOPDOWN_PROJECT_DOMAINS = """
clocks:
    clk:    { desc: "the default testbench clock", default: true, period: 1, timeUnit: ns }
    apbClk: { desc: "the register-bus testbench clock", period: 3, timeUnit: ns }

resets:
    rst_n:    { desc: "the default reset", default: true, clock: clk }
    apbRst_n: { desc: "the register-bus reset", clock: apbClk }
"""


def run_v19_hasvl_topdown_register_bus_port_excluded():
    """V19 positive (clockTree.py's BlockDomains.registerBusPort
    exclusion, spec §4.8): 'leafD's clock 'clk' has no selected reset, yet
    the build must succeed, because the only port the hasVl clause would
    otherwise blame 'clk' for is the register-bus port 'apbReg' - excluded
    so the separate register-bus V19 pass (domain.registerClock/
    registerReset) is the one that judges it, correctly, against
    'apbClk'/'apbRst_n'."""
    fixture, project_path, db_path = _make_fixture(
        design=V19_TOPDOWN_BUS_PORT_DESIGN, projectDomains=V19_TOPDOWN_PROJECT_DOMAINS)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: the top-down hasVl register-bus port fixture builds\n{output}")
            return False
        print("PASS: the top-down hasVl register-bus port fixture builds")
        if 'V19' in output:
            print(f"FAIL: build succeeded but still reported a V19 diagnostic\n{output}")
            return False
        print("PASS: no V19 diagnostic")
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
            "a top-down hasVl leaf's register-bus port takes R25's own "
            "registerClock/registerReset, not the handler's own guess",
            bus_port_matches_register_clock_reset)
    finally:
        shutil.rmtree(fixture)


# Same constants/types/structures/interfaces as V19_TOPDOWN_APB_PREAMBLE,
# plus dataIf's, merged into single sections: two "types:"/"structures:"/
# "interfaces:" top-level keys in one concatenated yaml file is a duplicate-
# key parse error, not a merge.
V19_TOPDOWN_APB_PLUS_DATA_PREAMBLE = """constants:
    ADDR_WIDTH: { value: 32, desc: "Register bus address width" }
    DATA_WIDTH: { value: 32, desc: "Register bus data width" }
    REG_WIDTH:  { value: 16, desc: "Register payload width" }

types:
    apbAddrT: { width: ADDR_WIDTH, desc: "APB address" }
    apbDataT: { width: DATA_WIDTH, desc: "APB data" }
    cfgT:     { width: REG_WIDTH,  desc: "Register payload" }
    dataT:    { width: 8, desc: "payload word" }

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "Register payload" }
    dataSt:
        data: { varType: dataT, desc: "payload word" }

interfaces:
    apbReg:
        desc: "APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
    dataIf:
        desc: "producer to consumer stream"
        interfaceType: push_ack
        structures:
            - { structure: dataSt, structureType: data_t }
"""


def run_v19_hasvl_topdown_extra_port_still_rejected():
    """V19 negative twin: same 'leafD' as the positive above, plus one
    extra, ordinary connection-derived port 'in' (no ports: - a top-down
    register-owning leaf may declare none at all, or postParseRegisterPorts
    exits with an error) on a second, non-bus, non-default clock 'clkX'
    with two unmarked resets. The registerBusPort exclusion names only
    'apbReg'; 'in' must still be rejected, proving the exclusion does not
    blanket the whole block."""
    design = V19_TOPDOWN_APB_PLUS_DATA_PREAMBLE + """blocks:
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
    # top_tb declares clkY itself (uProd's own domain), so the testbench
    # binding needs a same-named project clock too (spec §4.8, R3).
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
        ('V19', 'leafD', 'in', 'clkX', 'rstX1_n', 'rstX2_n'),
        design=design, projectDomains=projectDomains)


def run_v19_hasvl_port_cases():
    return all((run_v19_hasvl_port_ambiguous_reset_rejected(),
                run_v19_hasvl_port_no_reset_at_all_rejected(),
                run_v19_hasvl_connection_derived_port_rejected(),
                run_v19_hasvl_connectionmaps_boundary_port_rejected(),
                run_v19_hasvl_connectionmaps_boundary_port_not_derived_twice(),
                run_v19_hasvl_output_clock_port_rejected(),
                run_v19_hasvl_output_clock_port_positive(),
                run_v19_hasvl_port_positive(),
                run_v19_hasvl_two_instances_same_port_not_duplicated(),
                run_v19_hasvl_topdown_register_bus_port_excluded(),
                run_v19_hasvl_topdown_extra_port_still_rejected()))


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

def run_clock_tree_shape_cases():
    """The clockTree.py graph (Net.kind/.isReset/.clockNet/.driver,
    Driver.kind, Consumer.binding, BlockDomains.blockKey/Container.blockKey)
    is read here, not just written: a two-level design, container 'soc'
    with two declared clocks and resets, and three children - one bound by
    name match, one by the clk/rst_n fallback, and one asynchronous reset
    input bound by an explicit name.

    Built directly through the constructors, the way _validateSingleDomain
    builds its fixtures, rather than through BlockDomains.build()/
    clockTree.build(): a graph-shape check on the model's own classes, not a
    real project build (run_async_reset_bound_by_name_cases and
    run_async_reset_bound_by_map_cases exercise a real build for that). An
    asynchronous reset input binds as a Consumer like any other, 'name' or
    'map', never 'fallback' (spec §4.4: it takes no clk/rst_n-style default
    fallback).
    """
    def clockDecl(default=False):
        return clockTree.ClockDecl(desc='', direction='input', default=default,
                                   period='', timeUnit='ns')

    def resetDecl(clock='', default=False, isAsync=False):
        return clockTree.ResetDecl(desc='', direction='input', default=default,
                                   clock=clock, isAsync=isAsync)

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


def _run():
    print("=" * 72)
    print("TESTING PER-BLOCK CLOCK AND RESET DERIVATION")
    print("=" * 72)

    groups = (
        ("Declaration completeness", (run_declaration_completeness_cases,)),
        ("Template-facing view", (run_view_build,
                                  run_default_clock_port_resolution_cases,
                                  run_declared_port_connection_mismatch_v14_rejected,
                                  run_connectionmaps_boundary_derives_inside_out_v16)),
        ("Derived tables load at open", (run_derived_tables_loader_cases,)),
        ("Domain references", (run_reference_cases,
                               run_connection_clock_endpoint_cases,
                               run_unsupported_direction_cases,
                               run_async_reset_bound_by_name_cases,
                               run_async_reset_bound_by_map_cases,
                               run_output_clock_bindable_cases)),
        ("Domain agreement", (run_domain_agreement_cases,)),
        ("Instance bind pairs", (run_bind_pair_cases,)),
        ("Instance maps", (run_instance_maps_cases,)),
        ("Local nets", (run_local_net_cases,)),
        ("Single-domain objects", (run_single_domain_cases,)),
        ("V24 regAccess memory on the register bus", (run_v24_regaccess_memory_domain_cases,)),
        ("Register-bus port domain override (registerBusPort)",
         (run_registerports_reset_disambiguates_bus_port_domain,
          run_topdown_leaf_bus_port_domain_matches_register_clock)),
        ("V19 hasVl BFM port clause", (run_v19_hasvl_port_cases,)),
        ("Name collisions", (run_collision_cases,)),
        ("Graph shape", (run_clock_tree_shape_cases,)),
        ("V21 standalone attribute resolution", (run_v21_cases,)),
        ("V9 reset-clock membership", (run_v9_top_rejects_reset_on_unbound_clock,
                                       run_v9_standalone_rejects_reset_on_output_clock)),
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
