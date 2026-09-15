"""In-memory clock/reset container model (spec-clock-reset-requirements.md).

Purpose: give the rest of projectCreate one place to check and use a
project's clock and reset declarations and bindings, instead of walking
flatData rows by hand at every call site. Built once, in memory, during
projectCreate; it is not persisted itself. The three schema-adjacent tables
`blockClocksResets`, `instanceClockResetBinds` and `memoryClocks` stay the
persisted form templates read through the existing `getBD*` views
(processYaml.py); `rows()` below produces exactly the tuples those tables
already store, in the same column order, so `_persistClockTree` can insert
them unchanged.

This module does not replace the parser: `_normalizeClockResetShortForm`,
the `_post_resolve*` schema hooks and the `flatData` row shapes it consumes
all stay in processYaml.py. This module must not import processYaml (the
dependency runs the other way: processYaml.build()s a tree and reads it
back).

The graph built during `build()` (BlockDomains, Container, Net, Consumer) is
the single source of every fact `rows()` and `check()` report: neither reads
the raw flatData dicts `build()` was called with, and `ClockTree` does not
keep them. Everything either reads, or is walked from, `self.blocks` and
`self.containers`.

Phase 1 scope only (see plan-clock-container-model.md §7): block
declarations (`BlockDomains`) and the input-only, name-match/`clk`/`rst_n`
fallback instance binding phase 1 already performs (spec §4.4, R10). An
instance `clocks:`/`resets:` map, `direction: output`, local nets and
resolution (the "resolved clock" of spec §2) are later phases and are not
computed here.
"""

from collections import OrderedDict
from dataclasses import dataclass


@dataclass
class ClockDecl:
    """One block clock, as declared or implied (spec §4.2)."""
    desc: str
    direction: str
    default: bool
    period: object
    timeUnit: str


@dataclass
class ResetDecl:
    """One block reset, as declared or implied (spec §4.2).

    Named `isAsync` rather than the spec's own field name `async`: `async`
    has been a reserved word since Python 3.7 and cannot be a dataclass
    field.
    """
    desc: str
    direction: str
    default: bool
    clock: str
    isAsync: bool


@dataclass
class MemoryDomain:
    """One memory a block owns, and the distinct clocks its
    memoryConnections rows use (spec §3.4 single-domain check).
    """
    memoryBlockKey: str
    memory: str
    memoryType: str
    clocks: tuple


@dataclass
class Driver:
    """The single source of a net inside a container (spec §4.6 table).

    `kind` is one of 'input' (the container's own input port, driven by its
    parent), 'childOutput' (a child instance's output), 'ownImplementation'
    (a declared output no child drives) or 'environment' (the testbench, at
    the root). Phase 1 binds inputs only, so only 'input' and 'environment'
    occur; later phases add the source instance/port a 'childOutput' driver
    needs.
    """
    kind: str


@dataclass
class Consumer:
    """A child instance's block clock or reset bound onto a net.

    `binding` records the rule that resolved it: 'map' (an instance
    `clocks:`/`resets:` map entry, phase 2), 'name' (automatic binding by
    name match) or 'fallback' (the `clk`/`rst_n` default fallback, spec
    §4.4, R10).
    """
    instanceKey: str
    blockPort: str
    binding: str


class Net:
    """One clock or reset net inside a container (spec §4.6).

    `kind` is 'declared' (one of the container's own block clocks/resets),
    'local' (driven by a child output under a name the container does not
    declare) or 'testbench' (at the root). `clockNet` is the name of the
    clock net a reset belongs to, or None for a clock net or an
    asynchronous reset input.
    """

    def __init__(self, name, kind, isReset, clockNet, driver):
        self.name = name
        self.kind = kind
        self.isReset = isReset
        self.clockNet = clockNet
        self.driver = driver
        self.consumers = []


class Container:
    """A block that instantiates others, or the testbench acting as root.

    `blockKey` is a real blockKey for a block container, or
    `ClockTree.ROOT_KEY` for the root. `nets` is keyed by net name;
    `instances` maps each direct child's instanceKey to its own blockKey (so
    a reachability walk can descend into that child's own container without
    a second lookup).
    """

    def __init__(self, blockKey):
        self.blockKey = blockKey
        self.nets = OrderedDict()
        self.instances = OrderedDict()


class BlockDomains:
    """One block's own declared clock and reset set (spec §4.2, R5).

    Built independently per block: nothing is inferred from the block's
    children, connections or containment. `clocks` and `resets` are ordered
    by declaration (R18); `defaultClock` and `selectedReset` are the block
    default clock and, per clock the block carries, its selected reset
    among the block's own declared resets (a container's local reset nets
    are not yet a candidate; that is phase 3, spec §4.2/§4.5). `isRouter`
    marks a block carrying `addressBlock:`; `memories` and
    `registerConnectionClocks` are the facts check()'s single-domain rules
    need (spec §3.4), attached here rather than kept as raw connection rows
    on ClockTree.
    """

    def __init__(self, blockKey, block, clocks, resets, defaultClock, selectedReset,
                 isRouter, memories, registerConnectionClocks):
        self.blockKey = blockKey
        self.block = block
        self.clocks = clocks
        self.resets = resets
        self.defaultClock = defaultClock
        self.selectedReset = selectedReset
        self.isRouter = isRouter
        self.memories = memories
        self.registerConnectionClocks = registerConnectionClocks

    @classmethod
    def build(cls, blockKey, blockRow, memories, registerConnectionClocks,
              resetsDeclaredEmpty, diag):
        """Materialise one block's clocks:/resets: (spec R5) and check V1,
        V2, V7, V15, V18, and the phase-1 output/async rejections.
        """
        block = blockRow['block']

        def diagLoc(row):
            return diag.diagnosticLocation(row['_context'], row.get('lc'))

        declaredClocks = blockRow.get('clocks')
        if declaredClocks:
            clocks = OrderedDict(declaredClocks)
        else:
            clocks = OrderedDict()
            clocks['clk'] = {'clock': 'clk', 'desc': '', 'direction': 'input',
                             'default': False, 'period': '', 'timeUnit': 'ns',
                             '_context': blockRow['_context'], 'lc': blockRow.get('lc')}
        clockNames = list(clocks.keys())
        inputClocks = [name for name in clockNames if clocks[name]['direction'] == 'input']
        outputClocks = [name for name in clockNames if clocks[name]['direction'] == 'output']

        for name in outputClocks:
            diag.logError(
                f"Block '{block}' clock '{name}' declares direction: "
                f"output. An output clock is not yet bindable (an "
                # TODO phase 3: instance clocks:/resets: maps
                f"instance clocks:/resets: map does not exist yet): "
                f"declare it direction: input, or drop the block's own "
                f"clocks: entry until instance maps land. "
                f"{diagLoc(clocks[name])}")

        if not inputClocks:
            defaultClock = None
        elif len(inputClocks) == 1:
            defaultClock = inputClocks[0]
        else:
            marked = [name for name in inputClocks if clocks[name]['default']]
            if len(marked) != 1:
                diag.logError(
                    f"Block '{block}' declares {len(inputClocks)} input clocks "
                    f"({', '.join(inputClocks)}) and marks {len(marked)} of "
                    f"them default: true. A block declaring more than one "
                    f"input clock must mark exactly one default: true (spec "
                    f"§4.2): the block default clock is what an unstated "
                    f"port's, reset's, or fallback binding's clock means "
                    f"(R6, R7), declaration order does not decide it, and "
                    f"marking none or several leaves that meaning undefined "
                    f"(V18). {diagLoc(blockRow)}")
                # No default clock is knowable from an ambiguous marking;
                # leave it unset rather than guess one under
                # continueOnError, the same as the "no candidate" case
                # below leaves a clock's selected reset unset.
                defaultClock = None
            else:
                defaultClock = marked[0]
        # Normalise: the default clock's own row always reads default:
        # true, whether the block marked it (required with several input
        # clocks) or it is simply the block's only one (implied, V18).
        # getBDPortDomain and the alias helper both key off this field.
        if defaultClock is not None:
            clocks[defaultClock]['default'] = True

        # V2/V15: a declared port's (ports:, registerPorts:, addressBlock:)
        # clock: names a block clock of the same block; unstated means the
        # block default clock, which a block with no default clock (every
        # declared clock direction: output) does not have, so such a
        # block must name every port's clock explicitly.
        def checkPortClock(label, name, row):
            clockName = row['clock']
            if clockName:
                if clockName not in clocks:
                    diag.logError(
                        f"Block '{block}' {label} '{name}' names clock: "
                        f"'{clockName}', which is not one of the block's "
                        f"own declared clocks ({', '.join(clockNames)}) "
                        f"(V2). {diagLoc(row)}")
            elif defaultClock is None:
                cause = ("every declared clock is direction: output"
                        if not inputClocks else
                        "no single input clock is marked default: true (V18)")
                diag.logError(
                    f"Block '{block}' has no default clock ({cause}) "
                    f"and {label} '{name}' names no clock:; such a block "
                    f"must name every port's clock explicitly (V15). "
                    f"{diagLoc(row)}")

        for portName, portRow in (blockRow.get('ports') or {}).items():
            checkPortClock('ports', portName, portRow)
        for portName, portRow in (blockRow.get('registerPorts') or {}).items():
            checkPortClock('registerPorts', portName, portRow)
        addressBlockRow = blockRow.get('addressBlock')
        isRouter = bool(addressBlockRow)
        if addressBlockRow:
            checkPortClock('addressBlock', 'addressBlock', addressBlockRow)

        declaredResets = blockRow.get('resets')
        if declaredResets:
            resets = OrderedDict(declaredResets)
        elif resetsDeclaredEmpty or defaultClock is None:
            resets = OrderedDict()
        else:
            resets = OrderedDict()
            resets['rst_n'] = {'reset': 'rst_n', 'desc': '', 'direction': 'input',
                               'default': False, 'clock': defaultClock, 'async': False,
                               '_context': blockRow['_context'], 'lc': blockRow.get('lc')}

        for resetName, resetRow in resets.items():
            if resetRow['async']:
                diag.logError(
                    f"Block '{block}' reset '{resetName}' declares async: "
                    f"true. An asynchronous reset input is not yet "
                    f"released (the supplier contract does not exist "
                    f"yet; TODO phase 4): declare it a plain input reset, "
                    f"or drop it until then. {diagLoc(resetRow)}")
                continue
            statedClock = resetRow['clock']
            clockName = statedClock or defaultClock
            if not clockName:
                diag.logError(
                    f"Block '{block}' reset '{resetName}' names no clock: and "
                    f"the block has no default clock; a block with no "
                    f"default clock must name every reset's clock explicitly "
                    f"(V15). {diagLoc(resetRow)}")
                continue
            if clockName not in clocks:
                diag.logError(
                    f"Block '{block}' reset '{resetName}' names clock: "
                    f"'{clockName}', which is not one of the block's own "
                    f"declared clocks ({', '.join(clockNames)}) (V1). "
                    f"{diagLoc(resetRow)}")
                continue
            resetRow['clock'] = clockName

        # R6/V18/V19, declared-only part: the selected reset of each clock
        # the block carries, among its own declared resets. A container's
        # local reset nets are not yet part of the candidate set.
        byClock = dict()
        for resetName, resetRow in resets.items():
            if resetRow['async']:
                continue
            byClock.setdefault(resetRow['clock'], list()).append(resetName)
        selected = dict()
        for clockName, names in byClock.items():
            marked = [name for name in names if resets[name]['default']]
            if len(marked) > 1:
                diag.logError(
                    f"Block '{block}' clock '{clockName}' has more than one "
                    f"reset marked default: true ({', '.join(marked)}); at "
                    f"most one reset per clock may be the default (V18). "
                    f"{diagLoc(blockRow)}")
                # No selected reset is knowable from an ambiguous marking;
                # leave it unset rather than guess one under
                # continueOnError, the same as the no-candidate case below.
                selected[clockName] = None
            elif marked:
                selected[clockName] = marked[0]
            elif len(names) == 1:
                selected[clockName] = names[0]
            elif clockName == defaultClock:
                diag.logError(
                    f"Block '{block}' default clock '{clockName}' has "
                    f"{len(names)} declared resets ({', '.join(names)}) and "
                    f"none is marked default: true; a block with several "
                    f"resets on its default clock must mark exactly one "
                    f"(V18). {diagLoc(blockRow)}")
                selected[clockName] = None
            else:
                selected[clockName] = None

        # V7: clocks, resets, interface ports, memories and, when the block
        # does not declare them, the reserved names clk/rst_n, are pairwise
        # distinct. Local nets are not yet part of this set.
        names = dict()
        collisions = list()

        def addName(name, kind):
            if name in names:
                collisions.append((name, names[name], kind))
            else:
                names[name] = kind

        for name in clocks:
            addName(name, 'clock')
        for name in resets:
            addName(name, 'reset')
        for name in (blockRow.get('ports') or {}):
            addName(name, 'port')
        for name in (blockRow.get('registerPorts') or {}):
            addName(name, 'registerPort')
        for memDomain in memories:
            addName(memDomain.memory, 'memory')
        # The reserved names are aliases onto the default clock and its
        # selected reset (intf_gen_utils.sv_default_domain_aliases), so
        # each is reserved only where that alias actually fires: a block
        # with no default clock (every declared clock direction: output)
        # gets no clk alias, and a default clock with no selected reset
        # (resets: {} or empty resets: [] make one, or the block has no
        # default clock at all) gets no rst_n alias.
        if 'clk' not in clocks and defaultClock is not None:
            addName('clk', 'implicit clock')
        if 'rst_n' not in resets and defaultClock is not None and selected.get(defaultClock):
            addName('rst_n', 'implicit reset')
        for name, firstKind, secondKind in collisions:
            diag.logError(
                f"Block '{block}' uses the name '{name}' for both a "
                f"{firstKind} and a {secondKind}; clocks, resets, interface "
                f"ports, memories and, when the block does not declare "
                f"them, the reserved names clk/rst_n, must be pairwise "
                f"distinct within a block (V7). {diagLoc(blockRow)}")

        clockDecls = OrderedDict(
            (name, ClockDecl(desc=row['desc'], direction=row['direction'],
                             default=bool(row['default']), period=row['period'],
                             timeUnit=row['timeUnit']))
            for name, row in clocks.items())
        resetDecls = OrderedDict(
            (name, ResetDecl(desc=row['desc'], direction=row['direction'],
                             default=bool(row['default']), clock=row['clock'],
                             isAsync=bool(row['async'])))
            for name, row in resets.items())
        return cls(blockKey, block, clockDecls, resetDecls, defaultClock, selected,
                  isRouter, memories, registerConnectionClocks)


class ClockTree:
    """The project's clock/reset containers (plan-clock-container-model.md §3.7).

    `blocks` is every block's `BlockDomains`, keyed by blockKey. `containers`
    is every block that instantiates at least one child, keyed by blockKey;
    the root (the testbench) is `root`, a `Container` in its own right, not
    a member of `containers`. `check()` and `rows()` read only `self.blocks`
    and `self.containers`/`self.root`; the flatData dicts `build()` took are
    not kept.
    """

    ROOT_KEY = '_topInstance'

    def __init__(self, blocks, containers, root, diag):
        self.blocks = blocks
        self.containers = containers
        self.root = root
        self._diag = diag

    def check(self):
        """Invariants that need every block's domains already built: a
        memory or a generated register decoder is one module in one
        domain, so its connections must agree on a clock (spec §3.4).

        Checked here rather than in BlockDomains.build(), even though
        domain.defaultClock/domain.memories are known by the time a single
        block finishes building: build() runs block by block, so a
        diagnostic raised there would fire before later blocks' own
        declarations, V13 and the instance binds are even checked, ahead of
        where it fell under fail-fast at HEAD. check() runs only after
        build() has finished all of that.
        """
        for domain in self.blocks.values():
            if domain.defaultClock is not None:
                continue
            hasInputClock = any(clockDecl.direction == 'input' for clockDecl in domain.clocks.values())
            cause = ("no single input clock is marked default: true (V18)"
                     if hasInputClock else
                     "every declared clock is direction: output")
            for memDomain in domain.memories:
                self._diag.logError(
                    f"Memory '{memDomain.memory}' of block '{domain.block}' "
                    f"has no clock: its owning block has no default clock "
                    f"({cause}). A memory defaults to the owning block's "
                    f"default clock (spec §4.3); give the owning block one.")

        for domain in self.blocks.values():
            for memDomain in domain.memories:
                if len(memDomain.clocks) < 2:
                    continue
                names = ', '.join(f"'{clock}'" for clock in memDomain.clocks)
                if memDomain.memoryType == 'dualPort':
                    # The shipped dual-port primitive writes one array from two
                    # always @(posedge clk) blocks, so two independent clocks turn a
                    # same-address race into a race at every coincident edge, and the
                    # reference model has no clock domains to verify it against.
                    self._diag.logError(f"Memory '{memDomain.memory}' of block '{domain.block}' is "
                                  f"dualPort and its ports resolve to different clocks ({names}). "
                                  f"Dual-clock memory is not supported: put both ports in one "
                                  f"clock domain.")
                else:
                    self._diag.logError(f"Memory '{memDomain.memory}' of block '{domain.block}' has "
                                  f"connections in more than one clock domain ({names}). A memory "
                                  f"is a single-domain primitive.")
            if len(domain.registerConnectionClocks) >= 2:
                names = ', '.join(f"'{clock}'" for clock in domain.registerConnectionClocks)
                self._diag.logError(f"Block '{domain.block}' has register "
                              f"connections in more than one clock domain ({names}). The generated "
                              f"register decoder is a single-domain module.")
        # A generated apbDecode router is one module clocked by the register bus
        # it routes, and its emitter reads the FIRST entry of the block's own
        # declared clock set (moduleRegs.py, apbDecodeModule.py). A router
        # declaring more than one clock puts a clock other than the bus in
        # front of that set - a crossing on the APB handshake between the
        # router and its own handler, emitted as a real port so it still
        # elaborates. Multi-domain routers are rejected rather than ordered.
        # Scoped to the routers this build routes. The register-decode pass drops a
        # router whose every instance lies outside this build's topInstance - a
        # referenced child project's standalone-harness router - so this build
        # neither routes nor emits it, and failing on it would fail a root build on
        # a block only the child's own build is responsible for.
        # The candidates are selected FIRST and reachability computed only if one
        # exists. Reachability does not cache, and projectCreate already performs
        # one full walk of its own after generateHierarchy(), so computing it here
        # unconditionally would walk the whole design twice on every build to serve
        # a rule that almost no design triggers.
        multiClockRouters = {blockKey: domain for blockKey, domain in self.blocks.items()
                             if domain.isRouter and len(domain.clocks) > 1}
        if multiClockRouters:
            reachableBlockKeys = self._reachableBlockKeys()
            for blockKey, domain in multiClockRouters.items():
                if blockKey not in reachableBlockKeys:
                    continue
                names = ', '.join(f"'{clockName}'" for clockName in domain.clocks)
                self._diag.logError(f"Register-decode router block '{domain.block}' resolves to more "
                              f"than one clock ({names}). A router is a single-domain module "
                              f"clocked by the register bus it routes, so its set must hold one "
                              f"clock. Commonly a 'clocks:' entry on the block widened it, but a "
                              f"contained instance, a non-register connection carrying clock:, or "
                              f"a second register-bus connection into the router widens it too.")

    def _reachableBlockKeys(self):
        """Block keys of every instance transitively contained by the
        build's topInstance, walked over `containers` from `root` (spec
        §4.8): the same instance tree `container.instances` was built from,
        so it cannot drift from it.
        """
        reachable = set()
        queue = [self.root]
        seen = set()
        while queue:
            container = queue.pop()
            for blockKey in container.instances.values():
                reachable.add(blockKey)
                if blockKey in seen:
                    continue
                seen.add(blockKey)
                child = self.containers.get(blockKey)
                if child is not None:
                    queue.append(child)
        return reachable

    def rows(self):
        """The three persisted tables' rows, in their existing column order:
        blockClocksResets, instanceClockResetBinds, memoryClocks.
        """
        blockClocksResetsRows = list()
        memoryClocksRows = list()
        for blockKey, domain in self.blocks.items():
            for orderIndex, (name, clockDecl) in enumerate(domain.clocks.items()):
                blockClocksResetsRows.append(
                    (blockKey, 'clock', name, orderIndex, clockDecl.desc,
                     clockDecl.direction, int(clockDecl.default), clockDecl.period,
                     clockDecl.timeUnit, '', 0, domain.selectedReset.get(name)))
            for orderIndex, (name, resetDecl) in enumerate(domain.resets.items()):
                blockClocksResetsRows.append(
                    (blockKey, 'reset', name, orderIndex, resetDecl.desc,
                     resetDecl.direction, int(resetDecl.default), None, None,
                     resetDecl.clock, int(resetDecl.isAsync), ''))
            if domain.defaultClock is not None:
                for memDomain in domain.memories:
                    memoryClocksRows.append((memDomain.memoryBlockKey, domain.defaultClock))

        instanceClockResetBindsRows = list()
        for container in self._containersWithRoot():
            consumerNet = dict()
            for netName, net in container.nets.items():
                for consumer in net.consumers:
                    consumerNet[(consumer.instanceKey, consumer.blockPort)] = netName
            for instanceKey, childKey in container.instances.items():
                child = self.blocks[childKey]
                binds = list()
                # No direction filter here: build() gives only an input
                # clock/reset a Consumer (an output is not yet bindable,
                # V3-phase1), so consumerNet has no entry for one anyway.
                for name in child.clocks:
                    net = consumerNet.get((instanceKey, name))
                    if net is not None:
                        binds.append((name, net))
                for name in child.resets:
                    net = consumerNet.get((instanceKey, name))
                    if net is not None:
                        binds.append((name, net))
                for orderIndex, (childPort, parentSignal) in enumerate(binds):
                    instanceClockResetBindsRows.append((instanceKey, childPort, parentSignal, orderIndex))

        return blockClocksResetsRows, instanceClockResetBindsRows, memoryClocksRows

    def _containersWithRoot(self):
        """Every container `rows()` walks for instance binds: the blocks
        that instantiate children, and the root."""
        yield self.root
        yield from self.containers.values()


def build(blocks, instances, connections, memories, memoryConnections,
          registerConnections, blocksDeclaringNoResets,
          connectionsWithAuthoredClock, testbenchClocks, testbenchResets, diag):
    """Build the project's ClockTree from parsed flatData sub-dicts.

    `blocks`, `instances`, `connections`, `memories`, `memoryConnections`
    and `registerConnections` are the matching `flatData` tables.
    `blocksDeclaringNoResets` and `connectionsWithAuthoredClock` are the
    parser-recorded facts projectCreate keeps on itself
    (`_blocksDeclaringNoResets`, `_connectionsWithAuthoredClock`).
    `testbenchClocks`/`testbenchResets` are the root project's own
    `clocks:`/`resets:` entries; phase 1 does not yet bind the topInstance
    to them (that is phase 4), so they only seed the root container's own
    net set - `root.instances` records which instances are top-level, for
    reachability (spec §4.8), without yet computing their consumer edges.
    `diag` is any object with `logError(msg)` and
    `diagnosticLocation(yamlFile, lc)`; production passes the projectCreate
    instance itself, tests a stub. None of these arguments are kept on the
    returned ClockTree: everything a caller needs from them is folded into
    the graph before this function returns.
    """
    # spec §3.4: the distinct clocks each memory's own memoryConnections
    # rows use, and each block's registerConnections rows use - the facts
    # check()'s single-domain rules need, grouped per owning block so
    # BlockDomains.build() can attach them.
    memoryConnectionClocks = dict()
    for row in memoryConnections.values():
        memoryConnectionClocks.setdefault(row['memoryBlockKey'], OrderedDict())[row['clock']] = None
    memoriesByBlock = dict()
    for memoryBlockKey, memRow in memories.items():
        clocks = tuple(memoryConnectionClocks.get(memoryBlockKey, {}).keys())
        memoriesByBlock.setdefault(memRow['blockKey'], list()).append(
            MemoryDomain(memoryBlockKey, memRow['memory'], memRow['memoryType'], clocks))
    registerClocksByBlock = dict()
    for row in registerConnections.values():
        registerClocksByBlock.setdefault(row['blockKey'], OrderedDict())[row['clock']] = None

    domains = dict()
    for blockKey, blockRow in blocks.items():
        resetsDeclaredEmpty = (blockRow['_context'], blockRow['block']) in blocksDeclaringNoResets
        registerConnectionClocks = tuple(registerClocksByBlock.get(blockKey, {}).keys())
        domains[blockKey] = BlockDomains.build(
            blockKey, blockRow, memoriesByBlock.get(blockKey, []),
            registerConnectionClocks, resetsDeclaredEmpty, diag)

    # V13, phase 1 form: an AUTHORED connection clock: names a container
    # clock, which - absent an instance map (phase 2) - can only be a
    # name both endpoint blocks declare themselves (a block declaring
    # nothing has only clk). An unstated clock: is exempt: spec §4.3
    # rule 3 gives it to each endpoint's own block default independently,
    # with no requirement that the two names agree. Without this check
    # an authored name the connection's own project resolves but an
    # endpoint block does not declare is silently discarded
    # (getBDPortDomain falls back to the block default), so the
    # author's stated domain would not be the one emitted.
    for connRow in connections.values():
        if (connRow['_context'], connRow['connection']) not in connectionsWithAuthoredClock:
            continue
        clockName = connRow['clock']
        for end in connRow['ends'].values():
            blockKey = end['instanceTypeKey']
            if clockName not in domains[blockKey].clocks:
                block = blocks[blockKey]['block']
                declared = ', '.join(f"'{name}'" for name in domains[blockKey].clocks)
                diag.logError(
                    f"Connection '{connRow['connection']}' names clock: "
                    f"'{clockName}', but its endpoint block '{block}' "
                    f"declares no clock of that name ({declared}) (V13). "
                    f"A connection's clock: must name a clock every "
                    f"endpoint block declares.")

    # A container exists only for a block that instantiates at least one
    # child; a leaf's own declared nets are never bound against (nothing
    # inside it has a container binding to make), so it needs no Container.
    containerBlockKeys = {instRow['containerKey'] for instRow in instances.values()
                          if instRow['containerKey'] in domains}
    containers = {blockKey: Container(blockKey) for blockKey in containerBlockKeys}
    for blockKey in containerBlockKeys:
        domain = domains[blockKey]
        container = containers[blockKey]
        for name, clockDecl in domain.clocks.items():
            if clockDecl.direction != 'input':
                continue
            container.nets[name] = Net(name, 'declared', False, None, Driver('input'))
        for name, resetDecl in domain.resets.items():
            if resetDecl.direction != 'input':
                continue
            container.nets[name] = Net(name, 'declared', True, resetDecl.clock, Driver('input'))

    root = Container(ClockTree.ROOT_KEY)
    for name in testbenchClocks:
        root.nets[name] = Net(name, 'testbench', False, None, Driver('environment'))
    for name in testbenchResets:
        root.nets[name] = Net(name, 'testbench', True, testbenchResets[name]['clock'],
                              Driver('environment'))

    # Phase 1 binding (spec §4.4, R10): name match for an input, and the
    # default-clock/selected-reset fallback for a block clock or reset named
    # literally clk/rst_n. Instance clocks:/resets: maps and output binding
    # need the container's local-net tracking, which does not exist yet, so
    # an output entry is skipped here rather than bound; BlockDomains.build
    # already rejects a declared output clock/reset before this runs, so the
    # skip is reachable only under continueOnError.
    for instanceKey, instRow in instances.items():
        childKey = instRow['instanceTypeKey']
        containerKey = instRow['containerKey']
        if instRow['container'] == ClockTree.ROOT_KEY:
            # The topInstance's binding to the testbench (spec §4.8) is
            # phase 4 (resolution, V9/V10/V21): recorded here only for
            # reachability, not yet bound against root's testbench nets.
            root.instances[instanceKey] = childKey
            continue
        # Every non-root instance's containerKey names a real block
        # (processYaml.py's generateHierarchy sets containerKey to the
        # container instance's own instanceTypeKey whenever container is
        # not the topInstance sentinel), so it is always a domains key here.
        containerBlock = blocks[containerKey]['block']
        childBlock = blocks[childKey]['block']
        containerDomain = domains[containerKey]
        childDomain = domains[childKey]
        container = containers[containerKey]
        container.instances[instanceKey] = childKey

        clockBindNet = dict()
        for clockName, clockDecl in childDomain.clocks.items():
            if clockDecl.direction != 'input':
                continue
            if clockName in containerDomain.clocks:
                net = clockName
                binding = 'name'
            elif clockName == 'clk' and containerDomain.defaultClock:
                net = containerDomain.defaultClock
                binding = 'fallback'
            else:
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' "
                    f"in container '{containerBlock}' has no binding for its "
                    f"clock '{clockName}': '{containerBlock}' declares no "
                    f"clock of that name, and only 'clk' falls back to the "
                    f"container's default clock (V3). Declared clocks of "
                    f"'{containerBlock}': ({', '.join(containerDomain.clocks)}).")
                continue
            clockBindNet[clockName] = net
            container.nets[net].consumers.append(Consumer(instanceKey, clockName, binding))

        for resetName, resetDecl in childDomain.resets.items():
            if resetDecl.direction != 'input':
                continue
            isAsync = resetDecl.isAsync
            if resetName in containerDomain.resets:
                net = resetName
                binding = 'name'
            elif isAsync:
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' "
                    f"in container '{containerBlock}' has no binding for its "
                    f"asynchronous reset '{resetName}': '{containerBlock}' "
                    f"declares no reset of that name, and an asynchronous "
                    f"reset input takes no default fallback (V4).")
                continue
            elif resetName == 'rst_n':
                childClockOfReset = resetDecl.clock
                boundClockNet = clockBindNet.get(childClockOfReset)
                if boundClockNet is None:
                    # The reset's own clock already failed to bind (V3
                    # reported it); do not also report a fallback failure
                    # against a clock that was never resolved.
                    continue
                net = containerDomain.selectedReset.get(boundClockNet)
                if not net:
                    diag.logError(
                        f"Instance '{instRow['instance']}' of block "
                        f"'{childBlock}' in container '{containerBlock}' "
                        f"falls back to the selected reset of container "
                        f"clock '{boundClockNet}' for its reset 'rst_n', but "
                        f"that clock has none (V11).")
                    continue
                binding = 'fallback'
            else:
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' "
                    f"in container '{containerBlock}' has no binding for its "
                    f"reset '{resetName}': '{containerBlock}' declares no "
                    f"reset of that name, and only 'rst_n' falls back to a "
                    f"selected reset (V3). Declared resets of "
                    f"'{containerBlock}': ({', '.join(containerDomain.resets)}).")
                continue
            if not isAsync:
                # V6: the reset's own clock, mapped through this instance,
                # must be the clock the bound container reset belongs to.
                # A container reset that is itself async belongs to no
                # clock (''), which never equals a real bound clock name,
                # so a synchronous child reset name-matched onto it fails
                # here rather than passing unchecked.
                childClockOfReset = resetDecl.clock
                boundClockNet = clockBindNet.get(childClockOfReset)
                netMembership = containerDomain.resets[net].clock
                if boundClockNet and netMembership != boundClockNet:
                    diag.logError(
                        f"Instance '{instRow['instance']}' of block "
                        f"'{childBlock}' in container '{containerBlock}' "
                        f"would bind clock '{childClockOfReset}' to "
                        f"'{boundClockNet}' and reset '{resetName}' to "
                        f"'{net}', but '{containerBlock}' releases '{net}' "
                        f"on clock '{netMembership}', not on "
                        f"'{boundClockNet}' (V6).")
                    continue
            container.nets[net].consumers.append(Consumer(instanceKey, resetName, binding))

    return ClockTree(domains, containers, root, diag)
