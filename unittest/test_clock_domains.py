#!/usr/bin/env python3
"""Coverage for per-block clock and reset derivation.

Three groups: subprocess builds of a real design fixture, asserting the DERIVED
per-block sets stored in blockClocksResets, including a composed build whose two
projects disagree on a clock of the same name; the single-domain rules for
memories and register buses, driven directly against the check because authoring
a memory decode hierarchy would say nothing extra about the rule; and subprocess
builds of a real `addressBlock:` router fixture, because the router rule is
scoped to the routers a build actually routes and that scoping cannot be
expressed by handing the check a synthetic clock set.

Assertions are on the stored derivation, never on the build merely succeeding: a
build that emits nothing at all succeeds too.

Two invariants are asserted on EVERY fixture that builds here rather than in
cases of their own, because they are properties of the derivation and not of any
one shape: every reset a block carries is released on a clock that block also
carries, and every signal a container binds to a child's clock or reset port is
one the container itself declares.

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

import pysrc.arch2codeGlobals as g
from pysrc.processYaml import projectCreate, projectOpen

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

# One producer feeding one consumer inside a container, plus a leaf that no
# connection touches - the block whose clock can only come from the derivation
# floor. Every block is generation-disabled: this fixture asserts on the
# database, and scaffolding implementation files would say nothing more.
DESIGN = """{include}
types:
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

# The child half of a composed fixture: a reusable leaf owned by another project,
# which declares a clock of the SAME NAME as the assembler at a different period.
CHILD_DESIGN = """
types:
    ipDataT: {{ width: 8, desc: "payload word" }}

structures:
    ipDataSt:
        data: {{ varType: ipDataT, desc: "payload word" }}

interfaces:
    ipDataIf:
        desc: "child IP producer stream"
        interfaceType: push_ack
        structures:
            - {{ structure: ipDataSt, structureType: data_t }}

blocks:
    ipProd:
        desc: "reusable producer owned by the child project"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
{childBlockDomains}        ports:
            out: {{ interface: ipDataIf, direction: src }}
"""


# Two containers each instantiating the other, and no connection anywhere. The
# shape has no leaf, so nothing seeds the container union and every block's clock
# set can only come from the floor. Mutual containment is itself a design error
# that projectCreate accepts silently; what is asserted here is that the floor
# holds regardless, because a zero-clock block reaches the emitters as a module
# with no clock port.
CYCLE_DESIGN = """
blocks:
    top_tb: { desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    blkA:   { desc: "container instantiating blkB", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }
    blkB:   { desc: "container instantiating blkA", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }

instances:
    top_tb: { container: top_tb, instanceType: top_tb, instGroup: top }
    uA:     { container: top_tb, instanceType: blkA,   instGroup: top }
    uB:     { container: blkA,   instanceType: blkB,   instGroup: top }
    uA2:    { container: blkB,   instanceType: blkA,   instGroup: top }
"""

# Two clocks and three resets, two of them in the SAME domain. This is the only
# shape in which the reset a domain gets is a choice: the derivation takes the
# first of the canonical order (default first, then declaration order), so
# rstSlowA_n is the slow domain's and rstSlowB_n is reachable only by authoring it.
TWO_SLOW_RESETS = """
clocks:
    clk:     { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    clkSlow: { desc: "a slower, non-commensurate clock", period: 3, timeUnit: ns }

resets:
    rst_n:      { desc: "the default reset", default: true, clock: clk }
    rstSlowA_n: { desc: "the slow domain's first declared reset", clock: clkSlow }
    rstSlowB_n: { desc: "a second reset in the same domain", clock: clkSlow }
"""

# Three clocks, and two resets in each of two domains. This is what it takes for
# the reset that goes with a PORT to be a choice rather than the only candidate:
# a port's domain can name two of the block's resets, and canonical order - the
# default first, then declaration order - picks, so the second of a domain is
# reachable only by a consumer that selects some other member. The third clock is
# what gives a block a clock set the project default is not the first entry of.
TWO_RESETS_PER_DOMAIN = """
clocks:
    clk:     { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    clkSlow: { desc: "a slower, non-commensurate clock", period: 3, timeUnit: ns }
    clkPico: { desc: "a third clock, in a unit other than ns", period: 500, timeUnit: ps }

resets:
    rst_n:      { desc: "the default reset", default: true, clock: clk }
    rstAlt_n:   { desc: "a second reset in the default clock's domain", clock: clk }
    rstSlow_n:  { desc: "the slow-domain reset", clock: clkSlow }
    rstPicoA_n: { desc: "the pico domain's first declared reset", clock: clkPico }
    rstPicoB_n: { desc: "a second reset in the pico domain", clock: clkPico }
"""

# The assembler's default reset declared on a clock that is NOT its default. Legal
# on its own - a block carrying clk takes rst_n and a block carrying clkSlow takes
# rstSlow_n - and it is what makes the name-else-default respelling of a reset
# reaching this project from outside land in a domain the receiving block need not
# carry.
DEFAULT_RESET_OFF_DEFAULT_CLOCK = """
clocks:
    clk:     { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    clkSlow: { desc: "a slower, non-commensurate clock", period: 3, timeUnit: ns }

resets:
    rstSlow_n: { desc: "the default reset, declared on the non-default clock", default: true, clock: clkSlow }
    rst_n:     { desc: "the default clock's own reset", clock: clk }
"""

# A child project whose clock and reset are named nothing the assembler declares,
# so both cross the boundary by FALL BACK to the assembler's defaults rather than
# by a match on the child's own name.
CHILD_FOREIGN_DOMAINS = """
clocks:
    ipClk: { desc: "child clock, named nothing the assembler declares", default: true, period: 4, timeUnit: ns }

resets:
    ipRst_n: { desc: "child reset, named nothing the assembler declares", default: true, clock: ipClk }
"""

# A child project whose CLOCK is named nothing the assembler declares - so it falls
# back to the assembler's default clock - while its RESET is a name the assembler
# does declare, on the assembler's other clock. The two crossings are independent
# name lookups, so they land in different domains with no fall back to a default
# reset anywhere: the shape in which every clause of a diagnostic blaming the
# default-reset fall back is false.
CHILD_COLLIDING_RESET_NAME = """
clocks:
    ipClk: { desc: "child clock, named nothing the assembler declares", default: true, period: 4, timeUnit: ns }

resets:
    rstSlow_n: { desc: "child reset, a name the ASSEMBLER declares too - on its other clock", default: true, clock: ipClk }
"""

# A child project declaring TWO domains, both spelled as the assembler spells its
# own and both at other periods. A composed leaf carrying both is the only shape in
# which a bind pair says anything: the child's two clocks resolve to two DIFFERENT
# parent clocks, so pairing a reset with the child's first clock rather than with
# the clock it is declared on gives a different answer.
CHILD_SHARED_TWO_DOMAINS = """
clocks:
    clk:     { desc: "child default clock, the assembler's name at another period", default: true, period: 4, timeUnit: ns }
    clkSlow: { desc: "child slow clock, the assembler's name at another period", period: 9, timeUnit: ns }

resets:
    rst_n:     { desc: "child default reset, clk domain", default: true, clock: clk }
    rstSlow_n: { desc: "child slow-domain reset", clock: clkSlow }
"""

# Two clocks and one reset, which leaves the slow domain with no reset at all.
NO_SLOW_RESET = """
clocks:
    clk:     { desc: "the default clock", default: true, period: 1, timeUnit: ns }
    clkSlow: { desc: "a slower, non-commensurate clock", period: 3, timeUnit: ns }

resets:
    rst_n: { desc: "the only reset, in the default domain", default: true, clock: clk }
"""


# A container whose only child lives wholly in the slow domain. The container must
# inherit clkSlow and nothing else: a floor that fired on every empty set instead
# of only on what the union left empty would give it an unused default clock. The
# leaf's resets: line is a parameter, because the same shape is what separates a
# derived reset set from an authored one.
SLOW_CONTAINER_DESIGN = """
blocks:
    top_tb: {{ desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    dut:    {{ desc: "container of the slow leaf only", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    slowLeaf:
        desc: "leaf declaring the slow domain and nothing else"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks: [clkSlow]
{leafResets}
instances:
    top_tb: {{ container: top_tb, instanceType: top_tb, instGroup: top }}
    u_dut:  {{ container: top_tb, instanceType: dut,      instGroup: top }}
    uSlow:  {{ container: dut,    instanceType: slowLeaf, instGroup: top }}
"""


def _make_fixture(consumerDomains='', connectionClock='', childPeriod=None,
                  projectDomains=PROJECT_DOMAINS, design=None,
                  childConnectionClock='', extraBlocks='', extraSections='',
                  childDomains=None, containerDomains='', childBlockDomains='',
                  extraInstances='', extraConnections=''):
    """Write a design fixture into a fresh temp dir outside the repo tree.

    `consumerDomains` is appended to the cons block and `containerDomains` to the
    dut block that contains it, to author block clocks: /
    resets: lists. `connectionClock` is appended to the one connection, to author
    its clock:. `childPeriod` adds a composed child project whose leaf is
    instantiated by the assembler, so a connection spans two projects, and
    `childConnectionClock` is appended to THAT connection, so the clock crossing
    the boundary can be one the child project does not declare. `childDomains`
    replaces the child project's clocks: / resets: sections outright, so the child
    can declare names the assembler does not - the only shape in which the
    boundary respelling of a reset is a fall back to the assembler's default
    rather than a match on the child's own name - and `childBlockDomains` is
    appended to the child's ipProd block, so the composed leaf can carry more than
    one domain of its own. `extraBlocks`, `extraInstances` and `extraConnections`
    are appended to the blocks:, instances: and connections: sections, and
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
    include = ''
    if childPeriod is not None:
        os.makedirs(os.path.join(fixture, 'ip', 'prj', 'yaml'))
        os.makedirs(os.path.join(fixture, 'ip', 'yaml'))
        with open(os.path.join(fixture, 'ip', 'yaml', 'childIp.yaml'), 'w') as f:
            f.write(CHILD_DESIGN.format(childBlockDomains=childBlockDomains))
        if childDomains is None:
            childDomains = (
                "\nclocks:\n"
                f"    clk: {{ desc: \"child clock\", default: true, period: {childPeriod}, timeUnit: ns }}\n"
                "\nresets:\n"
                "    rst_n: { desc: \"child reset\", default: true, clock: clk }\n")
        with open(os.path.join(fixture, 'ip', 'prj', 'yaml', 'childProject.yaml'), 'w') as f:
            f.write("yamlFormat: 2\n"
                    "projectName: childIp\n"
                    "\n"
                    "projectFiles:\n"
                    "    - ../../yaml/childIp.yaml\n"
                    f"{childDomains}"
                    "\n"
                    "dirs:\n"
                    "    root: ../..\n"
                    f"{PROJECT_TAIL}")
        projectFiles.insert(0, '    - ../../ip/prj/yaml/childProject.yaml\n')
        # The child's DESIGN yaml also joins the assembler's include chain:
        # projectFiles: creates no include edge, and name resolution walks the
        # referencing context's chain.
        include = 'include:\n    - ../ip/yaml/childIp.yaml\n'
        extraInstances += ('    uIpProd: { container: dut, instanceType: ipProd, '
                          'instGroup: top }\n')
        extraConnections += ('    - { interface: ipDataIf, src: uIpProd, srcport: out, '
                            f'dst: uCons, dstport: ipIn{childConnectionClock} }}\n')

    if design is None:
        design = DESIGN.format(include=include, consumerDomains=consumerDomains,
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


def _derived_sets(db_path):
    """The persisted derivation as {blockName: {'clock': [...], 'reset': [...]}}.

    Keyed by block NAME and listing the qualified declaration keys in the stored
    order, so an assertion reads as the port list a block will carry.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        blocks = {r['blockKey']: r['block']
                  for r in conn.execute('select block, blockKey from blocks')}
        derived = {name: {'clock': [], 'reset': []} for name in blocks.values()}
        for row in conn.execute('select blockKey, kind, itemKey from blockClocksResets '
                                'order by blockKey, kind, orderIndex'):
            derived[blocks[row['blockKey']]][row['kind']].append(row['itemKey'])
        return derived
    finally:
        conn.close()


def _connection_clocks(db_path):
    """{connection interface: (clock, clockKey)} for every stored connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return {r['interface']: (r['clock'], r['clockKey'])
                for r in conn.execute('select interface, clock, clockKey from connections')}
    finally:
        conn.close()


def _block_sets(conn):
    """{blockKey: {'clock': {names}, 'reset': {names}}} for every block.

    Names, not qualified keys: a port list and a bind name are spelled with the
    declaration name, which is what both invariants below compare."""
    names = {'clock': {r['clockKey']: r['clock']
                       for r in conn.execute('select clock, clockKey from clocks')},
             'reset': {r['resetKey']: r['reset']
                       for r in conn.execute('select reset, resetKey from resets')}}
    sets = {r['blockKey']: {'clock': set(), 'reset': set()}
            for r in conn.execute('select blockKey from blocks')}
    for row in conn.execute('select blockKey, kind, itemKey from blockClocksResets'):
        sets[row['blockKey']][row['kind']].add(names[row['kind']][row['itemKey']])
    return sets


def _domain_invariant(db_path):
    """Every reset a block carries is released on a clock that block carries.

    The rule the whole derivation exists for, asserted over whatever blocks the
    fixture happens to hold rather than by naming cases: the generated
    co-simulation wrapper emits a release thread per reset that waits on THAT
    reset's clock, and declares a clock signal per clock of the block's set and
    nothing else, so a reset from a domain the block does not carry is a wait on an
    identifier the wrapper never declares."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        resetClock = {r['reset']: r['clock']
                      for r in conn.execute('select reset, clock from resets')}
        sets = _block_sets(conn)
        blocks = {r['blockKey']: r['block']
                  for r in conn.execute('select block, blockKey from blocks')}
    finally:
        conn.close()
    for blockKey, kinds in sets.items():
        for reset in sorted(kinds['reset']):
            if resetClock[reset] not in kinds['clock']:
                raise AssertionError(
                    f"block '{blocks[blockKey]}' carries reset '{reset}', whose clock "
                    f"is '{resetClock[reset]}', but its clock set is "
                    f"{sorted(kinds['clock'])}")
    return True


def _instance_binds(db_path, instance):
    """The stored (childPort, parentSignal) binds for one instance, in order."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        instanceKey = next(r['instanceKey'] for r in
                           conn.execute('select instance, instanceKey from instances')
                           if r['instance'] == instance)
        return [(r['childPort'], r['parentSignal'])
                for r in conn.execute('select childPort, parentSignal from '
                                      'instanceClockResetBinds where instanceKey = ? '
                                      'order by orderIndex', (instanceKey,))]
    finally:
        conn.close()


def _bind_invariant(db_path):
    """Every clock and reset a container binds is one the container declares.

    Discovered from the stored binds rather than listed: a container must DECLARE
    every signal it binds, and _persistInstanceClockResetBinds resolves the
    CHILD's clock/reset NAME in the container's project with a fall back to that
    project's default. So a child whose choice in one domain is a name the
    container does not carry silently gets the container's default instead - a
    wrong wire that elaborates. Checked per kind, so a reset bound to a clock
    signal fails too."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        sets = _block_sets(conn)
        blocks = {r['blockKey']: r['block']
                  for r in conn.execute('select block, blockKey from blocks')}
        instances = {r['instanceKey']: (r['instance'], r['containerKey'],
                                        r['instanceTypeKey'])
                     for r in conn.execute('select instance, instanceKey, containerKey, '
                                           'instanceTypeKey from instances')}
        binds = [(r['instanceKey'], r['childPort'], r['parentSignal'])
                 for r in conn.execute('select instanceKey, childPort, parentSignal '
                                       'from instanceClockResetBinds')]
    finally:
        conn.close()
    if not binds:
        raise AssertionError(
            "the build stored no clock/reset binds at all, so this fixture asserts "
            "nothing about them")
    for instanceKey, childPort, parentSignal in binds:
        instance, containerKey, childKey = instances[instanceKey]
        child, container = sets[childKey], sets[containerKey]
        kinds = [kind for kind in ('clock', 'reset') if childPort in child[kind]]
        if len(kinds) != 1:
            raise AssertionError(
                f"instance '{instance}' binds port '{childPort}', which is not one "
                f"of block '{blocks[childKey]}'s own clocks "
                f"{sorted(child['clock'])} or resets {sorted(child['reset'])}")
        kind = kinds[0]
        if parentSignal not in container[kind]:
            raise AssertionError(
                f"instance '{instance}' in container '{blocks[containerKey]}' binds "
                f"{kind} port '{childPort}' to signal '{parentSignal}', which is not "
                f"one of the container's {kind}s {sorted(container[kind])}")
    return True


# Asserted on EVERY fixture this suite builds, rather than in cases of their own:
# both are properties of the derivation itself, so what covers them is whatever
# shapes the suite holds - including any added later.
INVARIANTS = (
    ("every reset a block carries is released on a clock it carries",
     lambda db_path, output: _domain_invariant(db_path)),
    ("every clock and reset a container binds is one it declares",
     lambda db_path, output: _bind_invariant(db_path)),
)


def _built(label, checks, **fixtureKwargs):
    """Build a fixture and run `checks` over it.

    Each check is (name, fn(db_path, output)); fn returns True or raises."""
    fixture, project_path, db_path = _make_fixture(**fixtureKwargs)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        print(f"PASS: {label}")
        # A list, not a generator: all() would short-circuit and leave the
        # remaining checks unreported, which reads as coverage that does not exist.
        return all([_run_case(name, lambda fn=fn: fn(db_path, output))
                    for name, fn in tuple(checks) + INVARIANTS])
    finally:
        shutil.rmtree(fixture)


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


def _assertSets(derived, expected):
    for block, kinds in expected.items():
        for kind, keys in kinds.items():
            if derived[block][kind] != keys:
                raise AssertionError(
                    f"block '{block}' derived {kind}s {derived[block][kind]}, "
                    f"expected {keys}")
    return True


# ------------------------------------------------------------- derivation --

def run_default_domain_build():
    """Nothing authored: every block lands in the project default domain.

    This is the shape of every project in existence, so it is what backward
    compatibility means concretely - and the `spare` leaf, which no connection
    touches, can only get its clock from the derivation floor."""

    def every_block_default(db_path, output):
        derived = _derived_sets(db_path)
        return _assertSets(derived, {
            block: {'clock': ['clk/clkTest'], 'reset': ['rst_n/clkTest']}
            for block in ('top_tb', 'dut', 'prod', 'cons', 'spare')})

    def unstated_connection_clock_resolved(db_path, output):
        stored = _connection_clocks(db_path)['dataIf']
        if stored != ('clk', 'clk/clkTest'):
            raise AssertionError(
                f"the connection stored clock={stored[0]!r} clockKey={stored[1]!r}, "
                f"expected ('clk', 'clk/clkTest'): an unstated clock: is the "
                f"declaring project's default clock, resolved once so no consumer "
                f"sees an empty field")
        return True

    return _built(
        "a design authoring no domains builds",
        (("every block derives the project default clock and reset",
          every_block_default),
         ("an unstated connection clock: is stored as the project default",
          unstated_connection_clock_resolved)))


def run_connection_clock_build():
    """A connection declaring clock: puts BOTH its endpoint blocks in that domain.

    The clock belongs to the wire, so a connection is what carries a domain to a
    leaf that declares nothing itself; `spare`, which the connection does not
    touch, must stay on the default."""

    def endpoints_follow_the_wire(db_path, output):
        derived = _derived_sets(db_path)
        return _assertSets(derived, {
            'prod':  {'clock': ['clkSlow/clkTest']},
            'cons':  {'clock': ['clkSlow/clkTest']},
            # The container unions its children, so it holds both domains.
            'dut':   {'clock': ['clk/clkTest', 'clkSlow/clkTest']},
            'spare': {'clock': ['clk/clkTest']}})

    def resets_follow_the_clocks(db_path, output):
        # The reset set follows the clock set, so a connection that moves a leaf
        # wholly into another domain moves its reset with it. The OLD expectation
        # here was that a connection clock: changed no block's reset set: every
        # block kept the project default reset unconditionally, which left prod and
        # cons holding rst_n - a reset released on a clk edge, in blocks whose only
        # clock is clkSlow and whose emitted wrapper declares no clk at all.
        derived = _derived_sets(db_path)
        return _assertSets(derived, {
            'prod':  {'reset': ['rstSlow_n/clkTest']},
            'cons':  {'reset': ['rstSlow_n/clkTest']},
            # spare is untouched by the connection, so it keeps the default domain.
            'spare': {'reset': ['rst_n/clkTest']},
            # The container spans both domains and carries the reset of each.
            'dut':   {'reset': ['rst_n/clkTest', 'rstSlow_n/clkTest']}})

    return _built(
        "a connection declaring clock: builds",
        (("both endpoint blocks derive the connection's clock",
          endpoints_follow_the_wire),
         ("a connection clock: moves both endpoints' resets with their clocks",
          resets_follow_the_clocks)),
        connectionClock=', clock: clkSlow')


def run_block_domains_build():
    """A block declaring clocks: and resets:.

    The two lists are deliberately asymmetric: clocks: ADDS to what the
    connections imply, while resets: is the block's complete own set and replaces
    the per-domain derivation it would otherwise get. It must still cover every
    domain the block carries, so the shape that shows the replacement is a project
    declaring TWO resets on one clock: cons names the one its container derives
    for the other domain and the OTHER one for the slow domain, so its list and
    the derivation differ while both are complete."""

    def clocks_are_additive(db_path, output):
        derived = _derived_sets(db_path)
        return _assertSets(derived, {
            # clk from the connection, clkSlow declared: canonical order is the
            # project's declaration order with the default first.
            'cons': {'clock': ['clk/clkTest', 'clkSlow/clkTest']},
            'dut':  {'clock': ['clk/clkTest', 'clkSlow/clkTest']}})

    def resets_are_complete(db_path, output):
        derived = _derived_sets(db_path)
        return _assertSets(derived, {
            # The derivation would give cons rstSlowA_n for its slow domain, being
            # the first declared there; the authored list is what puts rstSlowB_n
            # in its place.
            'cons': {'reset': ['rst_n/clkTest', 'rstSlowB_n/clkTest']},
            # The container spans both domains, so it derives rst_n and rstSlowA_n,
            # and the union adds the child's choice on top.
            'dut':  {'reset': ['rst_n/clkTest', 'rstSlowA_n/clkTest',
                               'rstSlowB_n/clkTest']},
            'prod': {'reset': ['rst_n/clkTest']}})

    return _built(
        "a block declaring clocks: and resets: builds",
        (("a block clocks: entry adds to the connection-implied set",
          clocks_are_additive),
         ("a block resets: list replaces the derivation for that block only",
          resets_are_complete)),
        projectDomains=TWO_SLOW_RESETS,
        consumerDomains="        clocks: [clkSlow]\n"
                        "        resets: [rst_n, rstSlowB_n]\n")


def run_composed_crossing_build():
    """A connection across a composition boundary, the two projects disagreeing.

    Both projects declare a clock named `clk`; with boundary binding deferred, the
    two ends are wired together by that name match, so the child runs at the
    assembler's rate rather than its own declared period. A crossing is the
    designer's to handle, so the build says nothing about it - what is asserted
    here is that each end still resolves inside its own project."""

    def each_block_stays_in_its_own_project(db_path, output):
        derived = _derived_sets(db_path)
        return _assertSets(derived, {
            # A block's port list must be spelled in clocks its OWN project
            # declares, or the same block would emit different ports standalone
            # and composed.
            'ipProd': {'clock': ['clk/childIp'], 'reset': ['rst_n/childIp']},
            'cons':   {'clock': ['clk/clkTest'], 'reset': ['rst_n/clkTest']}})

    return _built(
        "a composed design whose two projects disagree on clk builds",
        (("every block's domains resolve inside its own project",
          each_block_stays_in_its_own_project),),
        childPeriod=4)


def run_containment_cycle_build():
    """No block ends with an empty clock set, even when nothing seeds the union.

    Two containers instantiating each other hold no leaf, so the leaf floor never
    fires and the union has nothing to propagate. Without the second floor pass
    every block stores zero clocks, and the emitters then produce a module with no
    clock port - silently in SystemVerilog, and as an IndexError on `clocks[0]` in
    the Verilated SystemC wrapper."""

    def every_block_holds_a_clock(db_path, output):
        derived = _derived_sets(db_path)
        for block in ('top_tb', 'blkA', 'blkB'):
            if not derived[block]['clock']:
                raise AssertionError(
                    f"block '{block}' derived no clock at all; a zero-clock block "
                    f"emits a module with no clock port")
        return _assertSets(derived, {
            block: {'clock': ['clk/clkTest'], 'reset': ['rst_n/clkTest']}
            for block in ('top_tb', 'blkA', 'blkB')})

    return _built(
        "a design whose containment is a cycle builds",
        (("every block in the cycle derives the project default clock",
          every_block_holds_a_clock),),
        design=CYCLE_DESIGN)


def run_slow_container_build():
    """A container of slow-domain children does NOT also acquire the default clock.

    This is what the floor must not cost. The container's set comes wholly from
    the union, so a floor applied to every empty set rather than only to what the
    union left empty would add an unused `clk` port to every such module."""

    def container_inherits_only_the_slow_domain(db_path, output):
        derived = _derived_sets(db_path)
        return _assertSets(derived, {
            'slowLeaf': {'clock': ['clkSlow/clkTest']},
            'dut':      {'clock': ['clkSlow/clkTest']},
            'top_tb':   {'clock': ['clkSlow/clkTest']}})

    def no_container_holds_the_default_reset(db_path, output):
        # The reset side of the same rule. The OLD expectation was that every
        # container also carried rst_n, because a block authoring no resets: took
        # the project default unconditionally: dut and top_tb declare only clkSlow,
        # so that reset was released on a clk edge in a module with no clk.
        derived = _derived_sets(db_path)
        return _assertSets(derived, {
            'slowLeaf': {'reset': ['rstSlow_n/clkTest']},
            'dut':      {'reset': ['rstSlow_n/clkTest']},
            'top_tb':   {'reset': ['rstSlow_n/clkTest']}})

    return _built(
        "a container holding only slow-domain children builds",
        (("the container inherits clkSlow and does not gain the default clock",
          container_inherits_only_the_slow_domain),
         ("no block in the chain gains the default-domain reset",
          no_container_holds_the_default_reset)),
        design=SLOW_CONTAINER_DESIGN.format(
            leafResets='        resets: [rstSlow_n]\n'))


def run_derived_slow_reset_build():
    """A leaf in the slow domain that authors NO resets: derives the slow reset.

    The core of the rule: the reset set is a function of the clock set, so the
    block that declares only `clocks: [clkSlow]` gets the reset declared on
    clkSlow without naming it, and the default-domain reset appears nowhere in the
    build at all."""

    def every_block_derives_the_slow_reset(db_path, output):
        derived = _derived_sets(db_path)
        return _assertSets(derived, {
            block: {'clock': ['clkSlow/clkTest'], 'reset': ['rstSlow_n/clkTest']}
            for block in ('slowLeaf', 'dut', 'top_tb')})

    return _built(
        "a slow-domain leaf authoring no resets: builds",
        (("every block derives the reset of the domain it carries",
          every_block_derives_the_slow_reset),),
        design=SLOW_CONTAINER_DESIGN.format(leafResets=''))


def run_domain_reset_selection_build():
    """Where a project declares TWO resets on one clock, canonical order picks.

    Not an error: the ordering contract already in force everywhere else - the
    default first, then declaration order - is deterministic, so the first
    declared reset of the domain is the one a block that authors none takes."""

    def the_first_declared_reset_of_the_domain_wins(db_path, output):
        derived = _derived_sets(db_path)
        return _assertSets(derived, {
            block: {'clock': ['clkSlow/clkTest'], 'reset': ['rstSlowA_n/clkTest']}
            for block in ('slowLeaf', 'dut', 'top_tb')})

    return _built(
        "a project declaring two resets on one clock builds",
        (("a block takes the first declared reset of its domain",
          the_first_declared_reset_of_the_domain_wins),),
        projectDomains=TWO_SLOW_RESETS,
        design=SLOW_CONTAINER_DESIGN.format(leafResets=''))


def run_authored_second_reset_build():
    """A child authoring the OTHER reset of its domain is carried by its container.

    The shape that makes the reset containment union load-bearing rather than a
    restatement of the derivation. slowLeaf names rstSlowB_n, its container derives
    rstSlowA_n for the same domain, and the container has to declare BOTH: the
    emitted bind resolves the child's reset by NAME in the container's project, so
    a container that only declared what it derived would drive that child's reset
    port from a signal it does not have."""

    def the_container_declares_both(db_path, output):
        derived = _derived_sets(db_path)
        return _assertSets(derived, {
            'slowLeaf': {'reset': ['rstSlowB_n/clkTest']},
            'dut':      {'reset': ['rstSlowA_n/clkTest', 'rstSlowB_n/clkTest']},
            'top_tb':   {'reset': ['rstSlowA_n/clkTest', 'rstSlowB_n/clkTest']}})

    return _built(
        "a child authoring the second reset of its domain builds",
        (("the container carries its own derived reset and the child's",
          the_container_declares_both),),
        projectDomains=TWO_SLOW_RESETS,
        design=SLOW_CONTAINER_DESIGN.format(
            leafResets='        resets: [rstSlowB_n]\n'))


def run_view_build():
    """getBlockData() surfaces the derived sets and each port's domain.

    Run last and only once: projectOpen holds the open database on module state,
    so a second open in the same process would be reading a different build. One
    fixture therefore has to carry every view shape, which is why it is the
    COMPOSED one: `cons` is reached from two domains AND from another project, so
    the same build holds a port whose domain is not its block's first clock and a
    port whose connection names a clock the owning block's project never
    declared. The authored connectionMap adds a port of a second KIND in the
    non-first domain: a connection port carries its connection's fields merged
    in, while a connectionMap / register / memory port keeps its source row
    whole, so the two are annotated from different places and one can be right
    while the other is wrong.

    The project declares two resets per domain and `cons` authors both of its
    default-domain ones, so the reset a port takes is a choice within one domain
    as well as a choice between domains. `libLeaf` is the block no connection and
    no instance reaches, so its port's domain can only come from its clock set.
    """
    fixture, project_path, db_path = _make_fixture(
        projectDomains=TWO_RESETS_PER_DOMAIN,
        consumerDomains="        clocks: [clkSlow]\n"
                        "        resets: [rst_n, rstAlt_n, rstSlow_n]\n",
        childPeriod=4, childConnectionClock=', clock: clkSlow',
        extraBlocks="    libLeaf:\n"
                    "        desc: \"exported leaf this project never instantiates\"\n"
                    "        hasVl: false\n"
                    "        hasMdl: false\n"
                    "        hasTb: false\n"
                    "        hasRtl: false\n"
                    "        clocks: [clkSlow, clkPico]\n"
                    "        resets: [rstPicoB_n, rstSlow_n]\n"
                    "        ports:\n"
                    "            libIn: { interface: dataIf, direction: dst }\n"
                    # A connectionMap's parent port must be defined by a boundary
                    # connection on the block, so the map into uCons is fed from
                    # a testbench-level source.
                    "    tbSrc:\n"
                    "        desc: \"testbench-level source\"\n"
                    "        hasVl: false\n"
                    "        hasMdl: false\n"
                    "        hasTb: false\n"
                    "        hasRtl: false\n",
        extraInstances="    uTbSrc: { container: top_tb, instanceType: tbSrc, instGroup: top }\n",
        extraConnections="    - { interface: dataIf, src: uTbSrc, srcport: out,"
                         " dst: u_dut, dstport: mapIn, clock: clkSlow }\n",
        extraSections="\nconnectionMaps:\n"
                      "    - { interface: dataIf, block: dut, port: mapIn,"
                      " direction: dst, instance: uCons, instancePort: mapIn,"
                      " clock: clkSlow }\n")
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

        def clocks_in_canonical_order():
            names = [row['clock'] for row in view['clocks']]
            if names != ['clk', 'clkSlow']:
                raise AssertionError(
                    f"the view lists clocks {names}, expected ['clk', 'clkSlow']: "
                    f"the persisted canonical order, default first")
            if view['clocks'][1]['period'] != 3:
                raise AssertionError(
                    f"the view's clkSlow entry carries period "
                    f"{view['clocks'][1]['period']}, expected 3: the entries are "
                    f"the declaration rows, so period/timeUnit need no second lookup")
            return True

        def resets_carry_their_domain():
            names = [row['reset'] for row in view['resets']]
            if names != ['rst_n', 'rstAlt_n', 'rstSlow_n']:
                raise AssertionError(
                    f"the view lists resets {names}, expected "
                    f"['rst_n', 'rstAlt_n', 'rstSlow_n']: the persisted canonical "
                    f"order, which is the project's and not the authored list's")
            if view['resets'][2]['clock'] != 'clkSlow':
                raise AssertionError(
                    f"the view's rstSlow_n entry carries clock="
                    f"{view['resets'][2]['clock']!r}, expected 'clkSlow': "
                    f"the entries are the declaration rows, so a consumer reads a "
                    f"reset's own domain without a second lookup")
            return True

        def ports_carry_their_own_connection_domain():
            # cons is reached from both domains, so its set is [clk, clkSlow] and
            # its two ports lie in different ones. Any consumer that took the
            # block's FIRST clock would clock ipIn's BFM from clk, which is a
            # real member here, so the mistake is silent.
            domains = {name: row['domainClock']
                       for portType in view['ports']
                       for name, row in view['ports'][portType].items()}
            expected = {'in': 'clk', 'ipIn': 'clkSlow', 'mapIn': 'clkSlow'}
            if domains != expected:
                raise AssertionError(
                    f"the view reports port domains {domains}, expected "
                    f"{expected}: each port lies in the domain of the connection "
                    f"it carries, not the block's first")
            names = {row['clock'] for row in view['clocks']}
            outside = {port: clock for port, clock in domains.items()
                       if clock not in names}
            if outside:
                raise AssertionError(
                    f"port domains {outside} name no clock of the block's own "
                    f"set {sorted(names)}; every emission site declares that set "
                    f"and nothing else, so such a name does not even compile")
            return True

        def ports_carry_the_reset_of_their_domain():
            # The reset that goes with a port is the block's reset released on
            # THAT port's clock. cons holds three, two of them in the clk domain,
            # so this separates three wrong answers at once: the block's first
            # reset, which would give every port rst_n; the reset of another port's
            # domain; and the second member of the right domain.
            resets = {name: row['domainReset']
                      for portType in view['ports']
                      for name, row in view['ports'][portType].items()}
            expected = {'in': 'rst_n', 'ipIn': 'rstSlow_n', 'mapIn': 'rstSlow_n'}
            if resets != expected:
                raise AssertionError(
                    f"the view reports port resets {resets}, expected {expected}: "
                    f"each port takes the reset declared on its own clock, and "
                    f"where a domain holds two the canonical order picks")
            names = {row['reset'] for row in view['resets']}
            outside = {port: reset for port, reset in resets.items()
                       if reset not in names}
            if outside:
                raise AssertionError(
                    f"port resets {outside} name no reset of the block's own set "
                    f"{sorted(names)}; every emission site declares that set and "
                    f"nothing else, so such a name does not even compile")
            return True

        def foreign_clock_name_resolves_in_the_owning_project():
            # The connection into ipProd is authored on clkSlow, which only the
            # ASSEMBLER declares. ipProd is owned by childIp, whose set is
            # therefore its own default clock, and the port's domain has to be
            # that - a block cannot be given a port naming a domain its project
            # does not declare.
            ipBlockKey = next(key for key, row in prj.data['blocks'].items()
                              if row['block'] == 'ipProd')
            ipView = prj.getBlockData(ipBlockKey)
            names = [row['clock'] for row in ipView['clocks']]
            if names != ['clk']:
                raise AssertionError(
                    f"ipProd's derived set is {names}, expected ['clk']: the "
                    f"fixture no longer crosses the boundary with a clock the "
                    f"child project does not declare")
            domain = ipView['ports']['connections']['out']['domainClock']
            if domain != 'clk':
                raise AssertionError(
                    f"ipProd's out port reports domain {domain!r}, expected "
                    f"'clk': a clock name the owning project does not declare "
                    f"resolves to that project's default, the same rule "
                    f"deriveBlockClocksResets applied to build the set")
            return True

        def a_port_with_no_connection_takes_the_first_clock():
            # libLeaf is instantiated nowhere, so getBDDefinitionPorts synthesises
            # its boundary from `ports:` and there is no connection to take a
            # domain from. The block's first clock is the only answer available;
            # what this pins is that it is the FIRST and not some other member,
            # since the block deliberately declares two.
            libBlockKey = next(key for key, row in prj.data['blocks'].items()
                               if row['block'] == 'libLeaf')
            libView = prj.getBlockData(libBlockKey)
            names = [row['clock'] for row in libView['clocks']]
            if names != ['clkSlow', 'clkPico']:
                raise AssertionError(
                    f"libLeaf's derived set is {names}, expected "
                    f"['clkSlow', 'clkPico']: the fixture no longer gives the "
                    f"connectionless block more than one clock to choose from")
            domain = libView['ports']['connections']['libIn']['domainClock']
            if domain != 'clkSlow':
                raise AssertionError(
                    f"libLeaf's libIn port reports domain {domain!r}, expected "
                    f"'clkSlow': a declared port of an uninstantiated block has no "
                    f"connection, so it takes the block's first clock - and this "
                    f"block deliberately does not carry the project default")
            return True

        return all([
            _run_case("the view fixture keeps every reset in a clock it carries",
                      lambda: _domain_invariant(db_path)),
            _run_case("the view fixture binds only what each container declares",
                      lambda: _bind_invariant(db_path)),
            _run_case("getBlockData lists the block's clocks in canonical order",
                      clocks_in_canonical_order),
            _run_case("getBlockData lists the block's resets with their clock",
                      resets_carry_their_domain),
            _run_case("getBlockData gives each port its own connection's domain",
                      ports_carry_their_own_connection_domain),
            _run_case("getBlockData gives each port the reset of its own domain",
                      ports_carry_the_reset_of_their_domain),
            _run_case("a boundary clock the owning project lacks takes its default",
                      foreign_clock_name_resolves_in_the_owning_project),
            _run_case("a declared port with no connection takes the first clock",
                      a_port_with_no_connection_takes_the_first_clock)])
    finally:
        shutil.rmtree(fixture)


# ------------------------------------------------------------- validation --

def run_reference_cases():
    results = []
    results.append(_expect_diagnostic(
        "a block clocks: entry naming an undeclared clock is rejected",
        ('noSuchClock', 'clocks:'),
        consumerDomains="        clocks: [noSuchClock]\n"))
    results.append(_expect_diagnostic(
        "a block resets: entry naming an undeclared reset is rejected",
        ('noSuchReset', 'resets:'),
        consumerDomains="        resets: [noSuchReset]\n"))
    results.append(_expect_diagnostic(
        "a connection clock: naming an undeclared clock is rejected",
        ('noSuchClock', 'clocks:'),
        connectionClock=', clock: noSuchClock'))
    return all(results)


# ------------------------------------------------------- domain agreement --

def run_domain_agreement_cases():
    """The four ways a reset set and a clock set can fail to line up.

    The first three are AUTHORED, which is what makes them errors rather than a
    silent choice: the author names a reset of the right domain (or adds the
    clock), covers the domain the authored list left out (or stops carrying it),
    or declares the missing reset.

    The first two are converses, and both are needed: a block must hold no reset
    outside the domains it carries AND a reset in every domain it carries. Neither
    implies the other, and dropping the second is what let the tool hand a domain a
    reset released on some other clock.

    The fourth is not authored at all - it is the reset containment union importing
    a child's reset across a composition boundary by NAME, a rule blind to which
    clock the answer sits on. The post-union invariant is what covers it, and it
    generalises the first: no block may end up holding a reset from a domain it
    does not carry, however that reset got there."""
    results = []
    results.append(_expect_diagnostic(
        "a block resets: entry outside the block's own domains is rejected",
        ('cons', 'rst_n', 'clkSlow', "clocks:"),
        connectionClock=', clock: clkSlow',
        consumerDomains="        resets: [rst_n]\n"))
    # The converse. cons takes clk from the connection and declares clkSlow, so it
    # carries two domains while authoring a reset in one - the shape that used to
    # build clean and hand the clkSlow BFM rst_n, released on clk edges. The
    # uncovered domain is deliberately the SECOND of the block's set, so a check
    # that looked at the block's primary clock alone would let it through.
    results.append(_expect_diagnostic(
        "a domain the block carries and its authored resets: omits is rejected",
        ('cons', "'clkSlow'", "'rst_n'", 'hold none declared on that clock',
         'resets:'),
        consumerDomains="        clocks: [clkSlow]\n"
                        "        resets: [rst_n]\n"))
    results.append(_expect_diagnostic(
        "a domain in which the project declares no reset is rejected",
        ('clkSlow', 'declares no reset', 'clock: clkSlow'),
        projectDomains=NO_SLOW_RESET,
        connectionClock=', clock: clkSlow'))
    # The residual boundary hole, which needs all three conditions together: two
    # projects; a child reset name (ipRst_n) the assembler does not declare, so the
    # union falls back to the assembler's DEFAULT reset; and that default declared
    # on clkSlow while the child's ipClk respells onto clk. The container of the
    # composed leaf then carries rstSlow_n while its only clock is clk.
    results.append(_expect_diagnostic(
        "a reset a composition boundary lands outside the block's domains is rejected",
        ('rstSlow_n', 'clkSlow', "('clk')", 'clkTest', 'declare a reset'),
        projectDomains=DEFAULT_RESET_OFF_DEFAULT_CLOCK,
        childPeriod=4, childDomains=CHILD_FOREIGN_DOMAINS))
    # The same invariant reached with NO fall back anywhere: the assembler declares
    # the child's reset name, on its other clock, so that crossing KEEPS the name
    # while the child's clock crossing falls back to the assembler's default clock.
    # A message blaming the default-reset fall back is false for this shape, and a
    # remedy that adjusts which reset is the project default is a no-op in it.
    results.append(_expect_diagnostic(
        "a child reset name the container's project declares on another clock is "
        "rejected",
        ('rstSlow_n', 'clkSlow', "('clk')", 'the two lookups are independent',
         'declares no reset of that name'),
        childPeriod=4, childDomains=CHILD_COLLIDING_RESET_NAME))
    return all(results)


# ---------------------------------------------------- instance bind pairs --

def run_bind_pair_cases():
    """A container binding ONE child a clock and a reset from two domains.

    The post-union invariant is on per-block SETS, so it says nothing here: the
    container carries both domains, which any container of a second, genuinely slow
    child does anyway. What is wrong is the PAIR. The child declares its reset on
    its own clock, so the two are one domain in the child and stay one domain
    wherever the child is emitted standalone; the container respells each side by an
    independent name lookup, and here they land apart - a 1 ns clock and a release
    counted in 3 ns edges. Nothing in the per-block sets can see it."""
    results = []
    results.append(_expect_diagnostic(
        "a container binding a child a clock and a reset from two domains is "
        "rejected",
        ('uIpProd', 'ipProd', 'dut', 'ipClk', 'rstSlow_n', "'clk'", 'clkSlow'),
        childPeriod=4, childDomains=CHILD_COLLIDING_RESET_NAME,
        containerDomains='        clocks: [clkSlow]\n'))

    def each_reset_pairs_with_its_own_clock(db_path, output):
        # A composed leaf in TWO domains, whose clocks resolve to two different
        # parent clocks. Every pair here is coherent, so what this pins is WHICH
        # clock each reset is checked against: pairing a reset with the child's
        # first clock, or with the clock at its own position in the list, are
        # separable answers only when the child holds more than one of each.
        binds = _instance_binds(db_path, 'uIpProd')
        expected = [('clk', 'clk'), ('clkSlow', 'clkSlow'),
                    ('rst_n', 'rst_n'), ('rstSlow_n', 'rstSlow_n')]
        if binds != expected:
            raise AssertionError(
                f"uIpProd's stored binds are {binds}, expected {expected}: the "
                f"child's canonical order, clocks then resets, each side spelled "
                f"in its own project")
        return True

    results.append(_built(
        "a composed leaf carrying two domains builds",
        (("each of the child's resets pairs with the clock it is declared on",
          each_reset_pairs_with_its_own_clock),),
        childPeriod=4, childDomains=CHILD_SHARED_TWO_DOMAINS,
        childBlockDomains='        clocks: [clkSlow]\n'))
    return all(results)


# --------------------------------------------- single-domain object rules --

def _validateSingleDomain(memories, memoryConnections, registerConnections,
                          routerClocks=None):
    """Run projectCreate._validateSingleDomainObjects over synthetic rows.

    THIS EXERCISES THE VALIDATOR IN ISOLATION, not a build. `logError` is replaced
    by a collector that does not exit, while the real one exits on the first
    diagnostic (`continueOnError` is a module-level False with no setter anywhere
    in the tree). So a production build reports at most ONE of these; the message
    counts below are properties of this harness, and what they assert is that a
    given shape produces exactly one diagnostic and not a second spurious one.

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
    pc = object.__new__(projectCreate)
    pc.errorState = False
    blocks = {'blockA/top.yaml': {'block': 'blockA', 'blockKey': 'blockA/top.yaml'}}
    blockClocks = {'blockA/top.yaml': ['clk/top.yaml']}
    if routerClocks is not None:
        blocks['router/top.yaml'] = {'block': 'router', 'blockKey': 'router/top.yaml',
                                     'addressBlock': {'addressGroup': 'top'}}
        blockClocks['router/top.yaml'] = [f'{clock}/top.yaml' for clock in routerClocks]
    pc.flatData = {
        'memories': memories,
        'memoryConnections': memoryConnections,
        'registerConnections': registerConnections,
        'blocks': blocks,
        'clocks': {f'{clock}/top.yaml': {'clock': clock}
                   for clock in ('clk', 'clkSlow', 'clkPico')},
        'instances': {f'u_{row["block"]}/top.yaml':
                      {'container': '_topInstance', 'instanceTypeKey': blockKey}
                      for blockKey, row in blocks.items()},
    }
    pc.hierKey = dict()
    messages = []
    pc.logError = lambda msg: (messages.append(msg), setattr(pc, 'errorState', True))
    try:
        pc._validateSingleDomainObjects(blockClocks)
    except SystemExit:
        pass
    return messages


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


# ------------------------------------------------- register-decode routers --

# The router rule needs a real `addressBlock:` router: it reads the block's
# derived set (so the bus feed and any authored clocks: have to actually meet
# there) and it is scoped to the routers this build routes (so the instance tree
# has to actually be walked). Neither is expressible by handing the check a
# synthetic set.
#
# The rejection itself is also reached by test_clock_reset_emission's richer
# emission fixture. It is kept here as the in-fixture control for the pruning
# case below: without a shape this fixture DOES reject, a passing pruning case
# would be indistinguishable from a fixture that rejects nothing.
#
# One register-bus surface per project, prefixed so the root's and the child's
# declarations do not collide in a composed load scope.
ROUTER_TYPES = """
constants:
    {p}DWORD: {{ value: 32, desc: "register bus word" }}

types:
    {p}ApbAddrT: {{ width: {p}DWORD, desc: "register bus address" }}
    {p}ApbDataT: {{ width: {p}DWORD, desc: "register bus data" }}
    {p}RegT:     {{ width: 8, desc: "a register field" }}

structures:
    {p}ApbAddrSt:
        address: {{ varType: {p}ApbAddrT, generator: address }}
    {p}ApbDataSt:
        data: {{ varType: {p}ApbDataT, generator: data }}
    {p}RegSt:
        f: {{ varType: {p}RegT, generator: register }}

interfaces:
    {p}ApbReg:
        desc: "register bus"
        interfaceType: apb
        structures:
            - {{ structure: {p}ApbAddrSt, structureType: addr_t }}
            - {{ structure: {p}ApbDataSt, structureType: data_t }}
"""

# The root build: a master feeding the dut's boundary, a router inside it, and one
# routed leaf owning a register. Generation is disabled everywhere - these cases
# assert on the database, and scaffolding implementation files would say nothing
# more. `routerDomains` is appended to the router block, to author its clocks:.
ROUTER_DESIGN = """
blocks:
    top_tb: {{ desc: "testbench container", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    cpu:    {{ desc: "register bus master", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    dut:    {{ desc: "container of the router and the leaf", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    decode:
        desc: "the register-decode router"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        addressBlock:
            addressGroup: top
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_top
            enumPrefix: ADDR_ID_TOP_
            upstreamPort: topApbReg
            registerDecoderPort: topApbReg
{routerDomains}
    leaf:   {{ desc: "routed leaf owning a register", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}

instances:
    top_tb:  {{ container: top_tb, instanceType: top_tb, instGroup: top }}
    uCpu:    {{ container: top_tb, instanceType: cpu,    instGroup: top }}
    u_dut:   {{ container: top_tb, instanceType: dut,    instGroup: top }}
    uDecode: {{ container: dut,    instanceType: decode, instGroup: top }}
    uLeaf:   {{ container: dut,    instanceType: leaf,   instGroup: top, addressGroup: top }}

connections:
    - {{ interface: topApbReg, src: uCpu, dst: u_dut }}

connectionMaps:
    - {{ interface: topApbReg, block: dut, direction: dst, instance: uDecode, instancePort: topApbReg }}

registers:
    - {{ register: leafReg, regType: rw, block: leaf, structure: topRegSt, desc: "a routed register" }}
"""

# A referenced child project whose OWN standalone harness holds a router, and
# which the root does not instantiate: exactly the shape of a reusable IP's
# verification top parsed into a root build's database. The harness router
# declares clocks: [clkSlow] on top of the clk its harness bus resolves to, so it
# derives two clocks - and the root neither routes nor emits it. The child's own
# build is the one that must reject it.
HARNESS_CHILD_DESIGN = """
blocks:
    ipStdTop:  {{ desc: "the child project's standalone harness top", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    ipCpu:     {{ desc: "harness register bus master", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    ipStdWrap: {{ desc: "harness container of the harness router", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}
    ipStdDecode:
        desc: "harness-only register-decode router"
        hasVl: false
        hasMdl: false
        hasTb: false
        hasRtl: false
        clocks: [clkSlow]
        addressBlock:
            addressGroup: ipStd
            addressIncrement: 0x01000000
            maxAddressSpaces: 16
            varType: addr_id_ipStd
            enumPrefix: ADDR_ID_IPSTD_
            upstreamPort: ipApbReg
            registerDecoderPort: ipApbReg
    ipLeaf:    {{ desc: "harness routed leaf", hasVl: false, hasMdl: false, hasTb: false, hasRtl: false }}

instances:
    ipStdTop:   {{ container: ipStdTop,  instanceType: ipStdTop,    instGroup: top }}
    uIpCpu:     {{ container: ipStdTop,  instanceType: ipCpu,       instGroup: top }}
    uIpStdWrap: {{ container: ipStdTop,  instanceType: ipStdWrap,   instGroup: top }}
    uIpDecode:  {{ container: ipStdWrap, instanceType: ipStdDecode, instGroup: top }}
    uIpLeaf:    {{ container: ipStdWrap, instanceType: ipLeaf,      instGroup: top, addressGroup: ipStd }}

connections:
    - {{ interface: ipApbReg, src: uIpCpu, dst: uIpStdWrap }}

connectionMaps:
    - {{ interface: ipApbReg, block: ipStdWrap, direction: dst, instance: uIpDecode, instancePort: ipApbReg }}

registers:
    - {{ register: ipLeafReg, regType: rw, block: ipLeaf, structure: ipRegSt, desc: "a harness register" }}
"""


def _make_router_fixture(routerDomains='', harnessChild=False):
    """Write a register-decode router fixture outside the repo tree.

    `routerDomains` is appended to the root's router block, to author its clocks:.
    `harnessChild` adds the referenced child project whose standalone harness holds
    its own multi-clock router, which the root's top does not reach.

    Returns (fixture_dir, project_path, db_path).
    """
    fixture = tempfile.mkdtemp(prefix='routerclk_')
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))

    projectFiles = ['    - ../../yaml/top.yaml\n']
    if harnessChild:
        os.makedirs(os.path.join(fixture, 'ip', 'prj', 'yaml'))
        os.makedirs(os.path.join(fixture, 'ip', 'yaml'))
        with open(os.path.join(fixture, 'ip', 'yaml', 'childIp.yaml'), 'w') as f:
            f.write(ROUTER_TYPES.format(p='ip') + HARNESS_CHILD_DESIGN.format())
        with open(os.path.join(fixture, 'ip', 'prj', 'yaml', 'childProject.yaml'), 'w') as f:
            f.write("yamlFormat: 2\n"
                    "projectName: childIp\n"
                    "topInstance: ipStdTop\n"
                    "\n"
                    "projectFiles:\n"
                    "    - ../../yaml/childIp.yaml\n"
                    f"{PROJECT_DOMAINS}"
                    "\n"
                    "dirs:\n"
                    "    root: ../..\n"
                    f"{PROJECT_TAIL}")
        projectFiles.insert(0, '    - ../../ip/prj/yaml/childProject.yaml\n')

    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(ROUTER_TYPES.format(p='top')
                + ROUTER_DESIGN.format(routerDomains=routerDomains))
    project_path = os.path.join(fixture, 'prj', 'yaml', 'project.yaml')
    with open(project_path, 'w') as f:
        f.write("yamlFormat: 2\n"
                "projectName: clkTest\n"
                "topInstance: top_tb\n"
                "\n"
                "projectFiles:\n"
                f"{''.join(projectFiles)}"
                f"{PROJECT_DOMAINS}"
                "\n"
                "dirs:\n"
                "    root: ../..\n"
                f"{PROJECT_TAIL}")
    return fixture, project_path, os.path.join(fixture, 'project.db')


def run_router_domain_cases():
    results = []

    def reachable_two_clock_router_rejected():
        fixture, project_path, db_path = _make_router_fixture(
            routerDomains='        clocks: [clkSlow]\n')
        try:
            code, output = _build(project_path, db_path)
        finally:
            shutil.rmtree(fixture)
        if code == 0:
            raise AssertionError(
                f"a router carrying its bus clock AND an authored clkSlow built; "
                f"the emitter reads the first entry of the set, so the second clock "
                f"becomes a port nothing clocks.\n{output}")
        if 'Traceback' in output:
            raise AssertionError(
                f"the build crashed instead of reporting a diagnostic.\n{output}")
        for needle in ('decode', "'clk'", "'clkSlow'", 'single-domain module'):
            if needle not in output:
                raise AssertionError(
                    f"the diagnostic does not mention '{needle}', so it does not name "
                    f"the router and the clocks it resolved to.\n{output}")
        return True

    def unreachable_harness_router_does_not_fail_the_root():
        fixture, project_path, db_path = _make_router_fixture(harnessChild=True)
        try:
            code, output = _build(project_path, db_path)
            if code != 0:
                raise AssertionError(
                    f"a root build failed on a two-clock router that lives only in a "
                    f"referenced child's standalone harness. The root neither routes "
                    f"nor emits it - the register-decode pass prunes it as "
                    f"unreachable - so the root cannot be the build that rejects "
                    f"it.\n{output}")
            derived = _derived_sets(db_path)
            # Assert the fixture really is the shape under test: had the harness
            # router derived one clock, this case would pass without exercising the
            # reachability scoping at all.
            if derived['ipStdDecode']['clock'] != ['clk/childIp', 'clkSlow/childIp']:
                raise AssertionError(
                    f"the harness router derived "
                    f"{derived['ipStdDecode']['clock']}, expected two clocks: the "
                    f"case only tests reachability scoping if the pruned router "
                    f"would otherwise be rejected")
            if derived['decode']['clock'] != ['clk/clkTest']:
                raise AssertionError(
                    f"the root's own router derived "
                    f"{derived['decode']['clock']}, expected ['clk/clkTest']")
            # The generated decode tree is the shape no author can fix by hand: a
            # synthesised handler carries no resets: list, so its reset can only
            # come from the derivation.
            _domain_invariant(db_path)
            _bind_invariant(db_path)
        finally:
            shutil.rmtree(fixture)
        return True

    for label, fn in (
            ("a router this build routes, resolving to two clocks, is rejected",
             reachable_two_clock_router_rejected),
            ("a two-clock router in a referenced child's harness does not fail "
             "the root build",
             unreachable_harness_router_does_not_fail_the_root)):
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


def _run():
    print("=" * 72)
    print("TESTING PER-BLOCK CLOCK AND RESET DERIVATION")
    print("=" * 72)

    groups = (
        ("Derived per-block domains", (run_default_domain_build,
                                       run_connection_clock_build,
                                       run_block_domains_build,
                                       run_composed_crossing_build,
                                       run_containment_cycle_build,
                                       run_slow_container_build,
                                       run_derived_slow_reset_build,
                                       run_domain_reset_selection_build,
                                       run_authored_second_reset_build)),
        ("Domain references", (run_reference_cases,)),
        ("Clock/reset domain agreement", (run_domain_agreement_cases,)),
        ("Instance bind pairs", (run_bind_pair_cases,)),
        ("Single-domain objects", (run_single_domain_cases,)),
        ("Register-decode routers", (run_router_domain_cases,)),
        ("Name collisions", (run_collision_cases,)),
        ("Template-facing view", (run_view_build,)),
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
