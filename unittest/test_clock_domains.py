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
    top_tb: {{ desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
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
    fixture, project_path, db_path = _make_fixture(design=design)
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
    fixture, project_path, db_path = _make_fixture(design=design)
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


# ------------------------------------------------------------- validation --

def run_reference_cases():
    """A connection clock: naming a clock the project does not declare is
    rejected. A block's own clocks:/resets: entry needs no such check: it is
    a fresh declaration, not a reference, so there is no name to misspell
    (spec R5)."""
    return _expect_diagnostic(
        "a connection clock: naming an undeclared clock is rejected",
        ('noSuchClock', 'clocks:'),
        connectionClock=', clock: noSuchClock')


def run_connection_clock_endpoint_cases():
    """V13, phase 1 form: a connection's clock: must name a clock BOTH
    endpoint blocks declare (name match only - there is no instance map
    yet). 'clkSlow' is a real project clock (PROJECT_DOMAINS), so this is
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
    fixture, project_path, db_path = _make_fixture(design=design)
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
    """`direction: output` on a clock and `async: true` on a reset are
    declared shapes the schema accepts (spec §4.2) but neither is bindable
    yet, so each is rejected with a diagnostic naming the field and the
    block."""
    results = [_expect_diagnostic(
        "a clock declaring direction: output is rejected",
        ('cons', 'clkOut', 'direction', 'output'),
        consumerDomains="        clocks:\n"
                        "            clkOut: { direction: output }\n")]
    results.append(_expect_diagnostic(
        "a reset declaring async: true is rejected",
        ('cons', 'rstA_n', 'async'),
        consumerDomains="        resets:\n"
                        "            rstA_n: { async: true }\n"))
    return all(results)


# ------------------------------------------------------- domain agreement --

def run_domain_agreement_cases():
    """V1: a block reset's clock: names a block clock of the same block.
    V2: a declared port's clock: does too."""
    results = [_expect_diagnostic(
        "a block reset's clock: naming a clock the block does not declare "
        "is rejected",
        ('cons', 'rst_n', 'noSuchClock', 'V1'),
        consumerDomains="        resets:\n"
                        "            rst_n: { clock: noSuchClock }\n")]
    results.append(_expect_diagnostic(
        "a declared port's clock: naming a clock the block does not "
        "declare is rejected",
        ('cons', 'regs', 'noSuchClock', 'clk', 'V2'),
        consumerDomains="        ports:\n"
                        "            regs: { interface: dataIf, direction: dst, "
                        "clock: noSuchClock }\n"))
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


def _orderedUniqueClocks(rows):
    """The distinct clocks of a set of connection rows, first-seen order -
    matches clockTree.build()'s own grouping so a message's clock order
    here matches what production would emit."""
    seen = OrderedDict()
    for row in rows:
        seen[row['clock']] = None
    return tuple(seen.keys())


def _validateSingleDomain(memories, memoryConnections, registerConnections,
                          routerClocks=None):
    """Run ClockTree.check() over synthetic BlockDomains.

    THIS EXERCISES THE CHECK IN ISOLATION, not a build: BlockDomains built by
    hand, not by BlockDomains.build(), so a multi-clock router needs no
    default-clock marking of its own (V18, irrelevant to this rule) to reach
    the check.

    Driven directly rather than through a built fixture: the memory and register
    rules read only the RESOLVED clock of each connection row, and authoring a
    memory decode hierarchy around them would exercise the decode machinery rather
    than these rules. The router rule is covered end to end as well, by
    run_router_domain_cases, because its reachability scoping has no synthetic
    equivalent.

    routerClocks, when given, adds a ROUTER block (one carrying `addressBlock:`)
    whose derived clock set holds those clocks. The router rule reads the derived
    set the caller hands in, not a connection row, so this is where that set
    enters. Every synthetic block is instantiated at the top so it is reachable;
    the pruning of unreachable routers is what the end-to-end cases cover.
    """
    memoryDomains = [
        clockTree.MemoryDomain(
            memoryBlockKey, memRow['memory'], memRow['memoryType'],
            _orderedUniqueClocks(row for row in memoryConnections.values()
                                if row['memoryBlockKey'] == memoryBlockKey))
        for memoryBlockKey, memRow in memories.items()]
    registerConnectionClocks = _orderedUniqueClocks(
        row for row in registerConnections.values() if row['blockKey'] == 'blockA/top.yaml')
    domains = {
        'blockA/top.yaml': clockTree.BlockDomains(
            'blockA/top.yaml', 'blockA',
            OrderedDict([('clk', clockTree.ClockDecl(desc='', direction='input',
                                                     default=True, period='', timeUnit='ns'))]),
            OrderedDict(), 'clk', {}, False, memoryDomains, registerConnectionClocks),
    }
    if routerClocks is not None:
        clocks = OrderedDict(
            (name, clockTree.ClockDecl(desc='', direction='input',
                                       default=(index == 0), period='', timeUnit='ns'))
            for index, name in enumerate(routerClocks))
        domains['router/top.yaml'] = clockTree.BlockDomains(
            'router/top.yaml', 'router', clocks, OrderedDict(), routerClocks[0], {},
            True, [], ())
    # Every synthetic block is instantiated directly at the top (spec §4.8),
    # recorded on the root container exactly as clockTree.build() records a
    # topInstance.
    root = clockTree.Container(clockTree.ClockTree.ROOT_KEY)
    for blockKey, domain in domains.items():
        root.instances[f'u_{domain.block}/top.yaml'] = blockKey
    diag = _StubDiag()
    tree = clockTree.ClockTree(domains, {}, root, diag)
    tree.check()
    return diag.messages


def _memoryConnection(clock, port):
    return {'memoryBlockKey': 'tbl/blockA/top.yaml', 'clock': clock, 'port': port,
            'memory': 'tbl', 'block': 'blockA'}


def _memory(memoryType):
    return {'tbl/blockA/top.yaml': {'memory': 'tbl', 'block': 'blockA',
                                    'memoryType': memoryType}}


def run_single_domain_cases():
    results = []

    def one_domain_accepted():
        messages = _validateSingleDomain(
            _memory('dualPort'),
            {'a': _memoryConnection('clk', 'port1'),
             'b': _memoryConnection('clk', 'port2')},
            {})
        if messages:
            raise AssertionError(
                f"a memory whose ports agree on a clock was rejected: {messages}. "
                f"A single-domain memory is the supported case.")
        return True

    def dual_clock_memory_named_as_unsupported():
        messages = _validateSingleDomain(
            _memory('dualPort'),
            {'a': _memoryConnection('clk', 'port1'),
             'b': _memoryConnection('clkSlow', 'port2')},
            {})
        if len(messages) != 1:
            raise AssertionError(
                f"expected exactly one diagnostic, got {messages}")
        for needle in ('dualPort', 'Dual-clock memory is not supported',
                       "'clk'", "'clkSlow'"):
            if needle not in messages[0]:
                raise AssertionError(
                    f"the message does not mention '{needle}', so it does not "
                    f"explain why this is rejected rather than supported: "
                    f"{messages[0]}")
        return True

    def single_port_memory_gets_the_generic_message():
        messages = _validateSingleDomain(
            _memory('singlePort'),
            {'a': _memoryConnection('clk', 'port1'),
             'b': _memoryConnection('clkSlow', 'port1')},
            {})
        if len(messages) != 1 or 'single-domain primitive' not in messages[0]:
            raise AssertionError(
                f"expected the generic single-domain message, got {messages}")
        if 'dualPort' in messages[0]:
            raise AssertionError(
                f"a singlePort memory was told dual-clock memory is unsupported, "
                f"which is not its problem: {messages[0]}")
        return True

    def register_bus_must_be_one_domain():
        messages = _validateSingleDomain(
            {}, {},
            {'a': {'blockKey': 'blockA/top.yaml', 'clock': 'clk'},
             'b': {'blockKey': 'blockA/top.yaml', 'clock': 'clkSlow'}})
        if len(messages) != 1:
            raise AssertionError(
                f"expected exactly one diagnostic, got {messages}")
        for needle in ('blockA', 'register decoder', "'clk'", "'clkSlow'"):
            if needle not in messages[0]:
                raise AssertionError(
                    f"the message does not mention '{needle}': {messages[0]}")
        return True

    def register_bus_one_domain_accepted():
        messages = _validateSingleDomain(
            {}, {},
            {'a': {'blockKey': 'blockA/top.yaml', 'clock': 'clkSlow'},
             'b': {'blockKey': 'blockA/top.yaml', 'clock': 'clkSlow'}})
        if messages:
            raise AssertionError(
                f"a register bus wholly in one non-default domain was rejected: "
                f"{messages}. Only a DISAGREEMENT is an error.")
        return True

    def router_one_domain_accepted():
        messages = _validateSingleDomain({}, {}, {}, routerClocks=['clkSlow'])
        if messages:
            raise AssertionError(
                f"a router wholly in one non-default domain was rejected: "
                f"{messages}. A router takes the clock of its register bus, "
                f"whichever domain that is.")
        return True

    def router_two_domains_rejected():
        messages = _validateSingleDomain({}, {}, {},
                                         routerClocks=['clk', 'clkSlow'])
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
        messages = _validateSingleDomain({}, {}, {},
                                         routerClocks=['clkSlow', 'clkPico'])
        if len(messages) != 1:
            raise AssertionError(
                f"a two-clock router whose bus clock sorts first was accepted "
                f"({messages}); the rule is on the size of the set")
        return True

    for label, fn in (
            ("a memory whose ports agree on one clock is accepted",
             one_domain_accepted),
            ("a dualPort memory in two clock domains is named as unsupported",
             dual_clock_memory_named_as_unsupported),
            ("a non-dualPort memory in two clock domains gets the generic message",
             single_port_memory_gets_the_generic_message),
            ("a block whose register connections disagree on a clock is rejected",
             register_bus_must_be_one_domain),
            ("a register bus wholly in one non-default domain is accepted",
             register_bus_one_domain_accepted),
            ("a router wholly in one non-default domain is accepted",
             router_one_domain_accepted),
            ("a router resolving to two clocks is rejected by name",
             router_two_domains_rejected),
            ("a two-clock router is rejected however the set is ordered",
             router_rule_is_on_cardinality_not_order)):
        results.append(_run_case(label, fn))
    return all(results)


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
    clockTree.build(): an asynchronous reset input's own declaration is
    itself rejected in phase 1 (run_unsupported_direction_cases), so a
    design authoring one can never reach a real build without a diagnostic.
    The bound shape a later phase gives such a reset - a Consumer like any
    other, 'name' or 'map', never 'fallback' - is dead code today, reachable
    only under continueOnError; asserting its shape here is what keeps that
    dead code honest until phase 4 makes it reachable for real.
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
        False, [], ())
    uartA = clockTree.BlockDomains(
        'uartA/top.yaml', 'uartA', OrderedDict([('clkPeripheral', clockDecl(default=True))]),
        OrderedDict(), 'clkPeripheral', {}, False, [], ())
    plainDut = clockTree.BlockDomains(
        'plainDut/top.yaml', 'plainDut', OrderedDict([('clk', clockDecl(default=True))]),
        OrderedDict([('rst_n', resetDecl(clock='clk', default=True))]),
        'clk', {'clk': 'rst_n'}, False, [], ())
    asyncBlock = clockTree.BlockDomains(
        'asyncBlock/top.yaml', 'asyncBlock', OrderedDict([('clk', clockDecl(default=True))]),
        OrderedDict([('rstPeripheral_n', resetDecl(isAsync=True))]),
        'clk', {}, False, [], ())

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
    tree = clockTree.ClockTree(domains, {'soc/top.yaml': container}, root, diag)

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
                                  run_default_clock_port_resolution_cases)),
        ("Domain references", (run_reference_cases,
                               run_connection_clock_endpoint_cases,
                               run_unsupported_direction_cases)),
        ("Domain agreement", (run_domain_agreement_cases,)),
        ("Instance bind pairs", (run_bind_pair_cases,)),
        ("Single-domain objects", (run_single_domain_cases,)),
        ("Name collisions", (run_collision_cases,)),
        ("Graph shape", (run_clock_tree_shape_cases,)),
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
