"""In-memory clock/reset container model (spec-clock-reset-requirements.md).

Purpose: give the rest of projectCreate one place to check and use a
project's clock and reset declarations and bindings, instead of walking
flatData rows by hand at every call site. Built once, in memory, during
projectCreate; it is not persisted itself. The five non-schema tables
`blockClocksResets`, `instanceClockResetBinds`, `memoryClocks`, `portDomains`
and `containerLocalNets` stay the persisted form templates read through the
existing `getBD*` views (processYaml.py); `rows()` below produces exactly the
tuples those tables already store, in the same column order, so
`_persistClockTree` can insert them unchanged.

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

Block declarations (`BlockDomains`), instance binding by map, name match and
`clk`/`rst_n` fallback (spec §4.4, R10), the top-down leaf register-port
selection (R25, V8, V25, V26), `direction: output` clocks and resets, and the
local nets an output binding creates (spec §4.5) are all in scope. An
instance map value may name a container-declared clock/reset, a new local
net name (an output only), or `~` (an output only, to leave it unconnected).
Resolution (the "resolved clock" of spec §2, following bindings up through a
container's own parent to a testbench net) is a later phase and is not
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
    """One memory a block owns (spec §4.3): its memoryType, for the
    dual/single-port shape, and its resolved `clock`/`reset` - the
    declaration's own `clock:`/`reset:` when authored, else the owning
    block's default clock and that clock's selected reset (BlockDomains.build
    resolves these in place once its own defaultClock/selectedReset are
    known). Per-accessor domain agreement (V8) is checked in `build()`
    directly, against the resolved consumer net, not carried here.

    `regAccess` marks a memory the register bus must be able to reach
    through its owning block's own register handler (R20); `build()`'s V24
    pass reads it to reject one on a clock other than that handler's bus
    clock, the R20 bridge not being implemented yet.
    """
    memoryBlockKey: str
    memory: str
    memoryType: str
    clock: str
    reset: str
    regAccess: bool


@dataclass
class Driver:
    """The single source of a net inside a container (spec §4.6 table).

    `kind` is one of 'input' (the container's own input port, driven by its
    parent), 'childOutput' (a child instance's output - `instanceKey` and
    `blockPort` name it), 'ownImplementation' (a declared output no child
    drives) or 'environment' (the testbench, at the root). `instanceKey`/
    `blockPort` are set only for 'childOutput'.
    """
    kind: str
    instanceKey: object = None
    blockPort: object = None


@dataclass
class Consumer:
    """A child instance's block clock or reset bound onto a net.

    `binding` records the rule that resolved it: 'map' (an instance
    `clocks:`/`resets:` map entry), 'name' (automatic binding by
    name match), 'fallback' (the `clk`/`rst_n` default fallback, spec §4.4,
    R10), or 'register' (a synthesised `<block>_regs` handler's clock/reset,
    bound directly onto its owning leaf's selected register clock/reset -
    R25, or a reusable IP's `registerPorts:` clock/reset - no instance map
    authors this bind, so it is not 'map').
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
    a second lookup). `unconnectedOutputs` is the (instanceKey, blockPort)
    pairs of an `output` explicitly bound to `~` (spec §4.5): no net is
    created for one, so `rows()` reads this set to still emit its bind row,
    with an empty signal, rather than dropping the port from the
    instantiation the way an ordinary unmapped port would be (R11: an
    unconnected output is written explicitly, never silently omitted).
    """

    def __init__(self, blockKey):
        self.blockKey = blockKey
        self.nets = OrderedDict()
        self.instances = OrderedDict()
        self.unconnectedOutputs = set()


class BlockDomains:
    """One block's own declared clock and reset set (spec §4.2, R5).

    Built independently per block: nothing is inferred from the block's
    children, connections or containment. `clocks` and `resets` are ordered
    by declaration (R18); `defaultClock` and `selectedReset` are the block
    default clock and, per clock the block carries, its selected reset
    among the block's own declared resets; a container's local reset net is
    never a candidate for it (a local reset net's own clock membership, spec
    §4.2/§4.5, is a separate fact). `isRouter`
    marks a block carrying `addressBlock:`; `isRegHandler` marks a
    synthesised `<block>_regs` handler block (the block row's own
    `isRegHandler`, schema `optional(false)`), the other block kind whose
    `registerClock`/`registerReset` are container nets rather than a leaf's
    own port names (see below); `memories` is the fact
    check()'s "owning block has no default clock" rule needs;
    per-accessor domain agreement (V8) is a memoryConnections-derived check
    made in `build()` against the resolved consumer net, not a per-block
    declaration fact, so it is not carried here.

    `registerClock`/`registerReset` are the block-level R25/rule-1 result
    (spec §4.3): for a router, the container net its own instance's
    bus clock/reset port resolves to; for a leaf whose registers a
    synthesised `<block>_regs` handler serves, the leaf's own clock/reset
    PORT NAME that carries the register bus (a reusable IP's authored
    `registerPorts:` clock/reset or its block default, else the top-down R25
    selection). Both start unset and are filled in once binding has run
    (`_resolveRouterBusClockReset`, `_resolveRegisterHandlerBinds`): neither
    is knowable at `BlockDomains.build()` time, since a router's is an
    instance fact and a top-down leaf's needs its outer instances' own
    binds. A block that is neither keeps both `None`.
    """

    def __init__(self, blockKey, block, clocks, resets, defaultClock, selectedReset,
                 isRouter, isRegHandler, memories, names):
        self.blockKey = blockKey
        self.block = block
        self.clocks = clocks
        self.resets = resets
        self.defaultClock = defaultClock
        self.selectedReset = selectedReset
        self.isRouter = isRouter
        self.isRegHandler = isRegHandler
        self.memories = memories
        # The block's own name -> kind map (clocks, resets, interface ports,
        # registerPorts, memories, and the reserved clk/rst_n aliases where
        # they fire), the same set V7 already checks pairwise distinct at
        # declaration time. A CONTAINER's own local net names (spec §4.5/
        # §4.6) are driven into existence later, by an output binding in
        # ClockTree.build() rather than here, so V7's collision check
        # against them is made there, against this same set, rather than
        # re-collecting it.
        self.names = names
        self.registerClock = None
        self.registerReset = None
        # The router's or handler's OWN declared clock/reset PORT NAME
        # carrying the register bus (spec §4.3 "Routers"; `_routerBusPorts`
        # for a router, the handler's sole implicit clk/rst_n for a
        # handler), filled in alongside registerClock/registerReset by the
        # same two resolution passes. Unlike registerClock/registerReset,
        # this is always a port name of THIS block, never a container net,
        # for both kinds - the one fact intf_gen_utils.py's
        # bus_clock_reset_port_data needs to rename the right declared
        # clocks/resets row without re-deriving the addressBlock: override
        # rule itself. A block that is neither a router nor a handler keeps
        # both `None`.
        self.busClockPort = None
        self.busResetPort = None
        # A served leaf's own port carrying the register bus: the `registerPorts:` key,
        # or the router's registerDecoderPort a top-down leaf infers. It is also a
        # synthesised connectionMaps boundary port, so the V19 hasVl clause excludes it
        # by name and leaves it to the register-bus V19 pass. None for other blocks.
        self.registerBusPort = None
        # Standalone simulation attributes (spec §4.8, R24, V21): per INPUT
        # clock, the period/timeUnit a standalone (`hasVl`) build of this
        # block generates it at; per INPUT reset, the releaseCycles it is
        # held asserted for. Filled in by `_resolveStandaloneAttrs`, after
        # every instance's bindings are resolved, from the clock/reset's own
        # declared value when present, else the testbench clock/reset it
        # resolves to uniquely across every instance of the block in its own
        # declaring project. A block that is never a standalone target keeps
        # these empty; a clock/reset with neither a declared value nor a
        # resolvable one is filled with the schema default (V21 already
        # reported the error, for a `hasVl` block, by the time that happens).
        self.resolvedPeriod = dict()
        self.resolvedTimeUnit = dict()
        self.resolvedReleaseCycles = dict()

    @classmethod
    def build(cls, blockKey, blockRow, memories, resetsDeclaredEmpty, diag):
        """Materialise one block's clocks:/resets: (spec R5) and check V1's
        async rules, V7, V15 and V18.

        V1/V2's existence part is the schema's blockClock/blockReset combo
        foreign key: a reset's, port's, registerPorts:, addressBlock: or
        memory's stated clock:/reset: names a row of this block's own
        clocks:/resets:. That check is already applied at parse time, so
        every stated name reaching here is one of `clocks`/`resets`. A block
        declaring no clocks: has no such rows, so any stated clock: on it is
        rejected there too; its implicit clk/rst_n exist only in this model.
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

        # V18: default: and period: never appear on an output clock - both
        # are properties of the clock a BLOCK CONSUMES (which clock is its
        # default, and the standalone period it simulates at), meaningless
        # for one it PRODUCES.
        for name in outputClocks:
            if clocks[name]['default']:
                diag.logError(
                    f"Block '{block}' output clock '{name}' declares "
                    f"default: true; default marks the block's default "
                    f"INPUT clock and never applies to an output (V18). "
                    f"{diagLoc(clocks[name])}")
            if clocks[name]['period']:
                diag.logError(
                    f"Block '{block}' output clock '{name}' declares "
                    f"period:; period is the standalone simulation rate for "
                    f"an input clock the design does not determine, and "
                    f"never applies to an output, which the block itself "
                    f"produces (V18). {diagLoc(clocks[name])}")

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

        # V15: a declared port's (ports:, registerPorts:, addressBlock:)
        # unstated clock: means the block default clock, which a block with
        # no default clock (every declared clock direction: output) does not
        # have, so such a block must name every port's clock explicitly.
        def checkPortClock(label, name, row):
            if not row['clock'] and defaultClock is None:
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
        isRegHandler = bool(blockRow['isRegHandler'])

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
                # V1: an asynchronous reset input belongs to no clock, and
                # only an input reset may be asynchronous (spec §4.2).
                if resetRow['direction'] != 'input':
                    diag.logError(
                        f"Block '{block}' reset '{resetName}' declares async: "
                        f"true with direction: '{resetRow['direction']}'; only "
                        f"an input reset may be asynchronous (V1). "
                        f"{diagLoc(resetRow)}")
                if resetRow['clock']:
                    diag.logError(
                        f"Block '{block}' reset '{resetName}' declares both "
                        f"async: true and clock: '{resetRow['clock']}'; an "
                        f"asynchronous reset input belongs to no clock and may "
                        f"not name one (V1). {diagLoc(resetRow)}")
                resetRow['clock'] = ''
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
        # distinct. A container's own local net names collide against this
        # same set too, checked in ClockTree.build() when an output binding
        # creates one, since a local net does not exist until then.
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

        # spec §4.3 "Memories": a memory's clock defaults to the owning
        # block's default clock, and its reset (for the R20 bridge's memory
        # side) to that clock's selected reset.
        for memDomain in memories:
            memDomain.clock = memDomain.clock or defaultClock
            memDomain.reset = memDomain.reset or selected.get(memDomain.clock)

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
                  isRouter, isRegHandler, memories, names)


class ClockTree:
    """The project's clock/reset containers.

    `blocks` is every block's `BlockDomains`, keyed by blockKey. `containers`
    is every block that instantiates at least one child, keyed by blockKey;
    the root (the testbench) is `root`, a `Container` in its own right, not
    a member of `containers`. `check()` and `rows()` read only `self.blocks`
    and `self.containers`/`self.root`; the flatData dicts `build()` took are
    not kept.
    """

    ROOT_KEY = '_topInstance'

    def __init__(self, blocks, containers, root, diag, portDomainRows):
        self.blocks = blocks
        self.containers = containers
        self.root = root
        self._diag = diag
        # V16 (spec §4.3): a connectionMaps: row's boundary port's derived
        # domain, computed once here from the inside-out net lookup rather
        # than re-derived by the projectOpen view. (outerBlockKey,
        # boundaryPortName, domainClock) tuples, ready for
        # projectCreate._persistClockTree() to insert unchanged.
        self.portDomainRows = portDomainRows

    def check(self):
        """Invariants that need every block's domains already built.

        Checked here rather than in BlockDomains.build(), even though
        domain.defaultClock/domain.memories are known by the time a single
        block finishes building: build() runs block by block, so a
        diagnostic raised there would fire before later blocks' own
        declarations, V13 and the instance binds are even checked, ahead of
        where it fell under fail-fast at HEAD. check() runs only after
        build() has finished all of that. The memory-accessor agreement of
        V8 is checked in `build()` instead, against the resolved consumer
        net a memoryConnections row's own accessor instance and the
        memory's owning instance bind to, since that check needs the
        per-instance binding build() computes rather than a per-block fact.
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
        """The five persisted tables' rows, in their existing column order:
        blockClocksResets, instanceClockResetBinds, memoryClocks, portDomains,
        containerLocalNets.
        """
        blockClocksResetsRows = list()
        memoryClocksRows = list()
        for blockKey, domain in self.blocks.items():
            # registerClock/registerReset/registerBusPort and
            # busClockPort/busResetPort are each a block-level fact (spec
            # §4.3), repeated onto every row of the block so getBDClocksResets
            # reads them off any one of them with no second table or per-key
            # SELECT. period/timeUnit hold the RESOLVED standalone-simulation
            # value (spec §4.8, R24, V21) for an input clock - the clock's own
            # declared value when present, else the value resolved from the
            # testbench clock every instance of the block resolves to - not the
            # bare declared value; an output clock (which resolves to nothing)
            # keeps its declared value (always empty, V18). releaseCycles is
            # the same resolution for a reset; unused (None) on a clock row.
            for orderIndex, (name, clockDecl) in enumerate(domain.clocks.items()):
                blockClocksResetsRows.append(
                    (blockKey, 'clock', name, orderIndex, clockDecl.desc,
                     clockDecl.direction, int(clockDecl.default),
                     domain.resolvedPeriod.get(name, clockDecl.period),
                     domain.resolvedTimeUnit.get(name, clockDecl.timeUnit),
                     '', 0, domain.selectedReset.get(name),
                     domain.registerClock, domain.registerReset,
                     domain.busClockPort, domain.busResetPort, None,
                     domain.registerBusPort))
            for orderIndex, (name, resetDecl) in enumerate(domain.resets.items()):
                blockClocksResetsRows.append(
                    (blockKey, 'reset', name, orderIndex, resetDecl.desc,
                     resetDecl.direction, int(resetDecl.default), None, None,
                     resetDecl.clock, int(resetDecl.isAsync), '',
                     domain.registerClock, domain.registerReset,
                     domain.busClockPort, domain.busResetPort,
                     domain.resolvedReleaseCycles.get(name),
                     domain.registerBusPort))
            for memDomain in domain.memories:
                if memDomain.clock:
                    memoryClocksRows.append(
                        (memDomain.memoryBlockKey, memDomain.clock, memDomain.reset))

        instanceClockResetBindsRows = list()
        containerLocalNetsRows = list()
        for container in self._containersWithRoot():
            consumerNet = _consumerNetIndex(container)
            # A `~`-bound output has no entry in driverNet (build() never
            # creates a net for one); its bind row instead comes from
            # `container.unconnectedOutputs` below, with an empty signal, so
            # the instantiation writes it explicitly unconnected rather than
            # omitting it (R11).
            driverNet = _driverNetIndex(container)
            for instanceKey, childKey in container.instances.items():
                child = self.blocks[childKey]
                binds = list()
                # A router's or a handler's own registerClock/registerReset
                # is the container net its bus clock/reset port resolved to;
                # the child's emitted port is renamed to that same string
                # (intf_gen_utils.bus_clock_reset_port_data), so the parent's
                # own instantiation must bind childPort = registerClock/
                # registerReset there too. Not for a served LEAF, whose
                # registerClock/registerReset is its own port name instead
                # of a container net (a coincidental string match, not a
                # real one).
                childIsRouterOrHandler = child.isRouter or child.isRegHandler
                for name, clockDecl in child.clocks.items():
                    net = (consumerNet if clockDecl.direction == 'input' else driverNet).get((instanceKey, name))
                    if net is not None:
                        childPort = (child.registerClock
                                    if childIsRouterOrHandler and net == child.registerClock
                                    else name)
                        binds.append((childPort, net))
                    elif (instanceKey, name) in container.unconnectedOutputs:
                        binds.append((name, ''))
                for name, resetDecl in child.resets.items():
                    net = (consumerNet if resetDecl.direction == 'input' else driverNet).get((instanceKey, name))
                    if net is not None:
                        childPort = (child.registerReset
                                    if childIsRouterOrHandler and net == child.registerReset
                                    else name)
                        binds.append((childPort, net))
                    elif (instanceKey, name) in container.unconnectedOutputs:
                        binds.append((name, ''))
                for orderIndex, (childPort, parentSignal) in enumerate(binds):
                    instanceClockResetBindsRows.append(
                        (instanceKey, childPort, parentSignal, orderIndex))

            for orderIndex, netName in enumerate(
                    name for name, net in container.nets.items() if net.kind == 'local'):
                containerLocalNetsRows.append((container.blockKey, netName, orderIndex))

        return (blockClocksResetsRows, instanceClockResetBindsRows,
               memoryClocksRows, self.portDomainRows, containerLocalNetsRows)

    def _containersWithRoot(self):
        """Every container `rows()` walks for instance binds: the blocks
        that instantiate children, and the root."""
        yield self.root
        yield from self.containers.values()


def build(blocks, instances, connections, memories, memoryConnections,
          connectionMaps, blocksDeclaringNoResets, connectionsWithAuthoredClock,
          testbenchClocks, testbenchResets, contextOwningProject, rootProjectName,
          diag):
    """Build the project's ClockTree from parsed flatData sub-dicts.

    `blocks`, `instances`, `connections`, `memories`, `memoryConnections` and
    `connectionMaps` are the matching `flatData` tables. `registerConnections`
    carries no domain field of its own (spec V17): a register value crossing
    into an accessor in another domain is an unchecked crossing like any
    other (R17), so this build() takes no argument for it.
    `blocksDeclaringNoResets` and `connectionsWithAuthoredClock` are the
    parser-recorded facts projectCreate keeps on itself
    (`_blocksDeclaringNoResets`, `_connectionsWithAuthoredClock`).
    `testbenchClocks`/`testbenchResets` are the root project's own
    `clocks:`/`resets:` entries: they seed the root container's own net set
    and are what the top instance is bound onto (`_bindTopInstance`, spec
    §4.8). `contextOwningProject` (`processYaml.py`'s own
    `self.contextOwningProject`) and `rootProjectName` (this build's own
    project) scope V21's standalone-attribute resolution to the project that
    declares each block, never re-evaluated by an assembler (spec §4.8, R3).
    `diag` is any object with `logError(msg)` and
    `diagnosticLocation(yamlFile, lc)`; production passes the projectCreate
    instance itself, tests a stub. None of these arguments are kept on the
    returned ClockTree: everything a caller needs from them is folded into
    the graph before this function returns.
    """
    memoriesByBlock = dict()
    for memoryBlockKey, memRow in memories.items():
        memoriesByBlock.setdefault(memRow['blockKey'], list()).append(
            MemoryDomain(memoryBlockKey, memRow['memory'], memRow['memoryType'],
                        memRow['clock'], memRow['reset'], memRow['regAccess']))

    domains = dict()
    for blockKey, blockRow in blocks.items():
        resetsDeclaredEmpty = (blockRow['_context'], blockRow['block']) in blocksDeclaringNoResets
        domains[blockKey] = BlockDomains.build(
            blockKey, blockRow, memoriesByBlock.get(blockKey, []),
            resetsDeclaredEmpty, diag)

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
            # An input's driver is the container's own parent, known now;
            # an output's driver is either a child's export (the output
            # binding pass below) or, when no child drives it, the
            # container's own implementation - not knowable until every
            # child's output binding has run, so it starts unset.
            driver = Driver('input') if clockDecl.direction == 'input' else None
            container.nets[name] = Net(name, 'declared', False, None, driver)
        for name, resetDecl in domain.resets.items():
            driver = Driver('input') if resetDecl.direction == 'input' else None
            container.nets[name] = Net(name, 'declared', True, resetDecl.clock, driver)

    root = Container(ClockTree.ROOT_KEY)
    for name in testbenchClocks:
        root.nets[name] = Net(name, 'testbench', False, None, Driver('environment'))
    for name in testbenchResets:
        root.nets[name] = Net(name, 'testbench', True, testbenchResets[name]['clock'],
                              Driver('environment'))

    def diagLoc(row):
        return diag.diagnosticLocation(row['_context'], row.get('lc'))

    # Output binding (spec §4.4 "Outputs are always explicit", §4.5): a map
    # entry is required for every output block clock/reset, bound to a
    # container's declared output (the export), a new local net name, or
    # `~` to leave it unconnected (R11). This runs to completion, for every
    # instance of every container, before the input pass below: a local net
    # is created here, by being driven, and an input consumer (map, name
    # match or fallback) must see it already in `container.nets` (spec
    # "A local net exists by being driven"). Global instance order does not
    # matter across containers, since a container's own nets are its own;
    # it matters only within one container, which this satisfies by running
    # every container's outputs before any container's inputs.
    for instanceKey, instRow in instances.items():
        if instRow['container'] == ClockTree.ROOT_KEY:
            # The top block's own outputs are observed by the testbench,
            # not bound to a container net (spec §4.8).
            continue
        childKey = instRow['instanceTypeKey']
        containerKey = instRow['containerKey']
        containerBlock = blocks[containerKey]['block']
        childBlock = blocks[childKey]['block']
        childDomain = domains[childKey]
        container = containers[containerKey]

        # processSimple only sets 'clocks'/'resets' on an instance row when
        # the user actually wrote a non-empty map (an omitted or explicitly
        # empty map leaves the key absent, config/schema.yaml's instances:
        # clocks:/resets:, both optional, multiple); an instance with no map
        # at all is the ordinary case (§4.4 automatic binding), not a
        # violated contract.
        clockMap = instRow['clocks'] if 'clocks' in instRow else {}
        resetMap = instRow['resets'] if 'resets' in instRow else {}

        def bindOutput(name, mapDict, netKind):
            mapRow = mapDict.get(name)
            if mapRow is None:
                diag.logError(
                    f"Instance '{instRow['instance']}' of block "
                    f"'{childBlock}' does not map its output {netKind} "
                    f"'{name}': every output must appear in the map, bound "
                    f"to a container net, a new local net name, or `~` "
                    f"(V3).")
                return
            net = mapRow['bind']
            if not net:
                # `~`: left unconnected, as an unused output port is
                # (spec §4.5) - never a silently dropped net (R11), since
                # the map entry is still required above. No net is created,
                # but the instantiation still writes the port explicitly
                # unconnected (rows() reads this set), rather than omitting
                # it the way an ordinary unmapped port would be.
                container.unconnectedOutputs.add((instanceKey, name))
                return
            existing = container.nets.get(net)
            if existing is None:
                # A genuinely new local net name: it cannot collide with one
                # of the container's own declared clocks/resets (those are
                # already in container.nets, so `existing` would not be
                # None), but it can still collide with one of the
                # container's own interface ports, registerPorts, memories,
                # or the reserved clk/rst_n aliases - the rest of the V7
                # name set BlockDomains.build() already collected for this
                # same block (spec §4.6 "The container's module carries one
                # net per local net"; V7 applies to that net's name too).
                collidingKind = domains[containerKey].names.get(net)
                if collidingKind is not None:
                    diag.logError(
                        f"Instance '{instRow['instance']}' of block "
                        f"'{childBlock}' binds output {netKind} '{name}' to "
                        f"'{net}', but '{containerBlock}' already uses that "
                        f"name for a {collidingKind}; a local net's name may "
                        f"not collide with the container's own clocks, "
                        f"resets, interface ports, memories, or the "
                        f"reserved names clk/rst_n (V7).")
                    return
                # A local reset net's own clock membership (spec §4.4) is
                # not knowable yet here - the driving output's own clock
                # port may itself be an input this pass has not bound yet -
                # so it is left unset and filled in once every instance's
                # bindings, output and input alike, are resolved.
                container.nets[net] = Net(net, 'local', netKind == 'reset', None,
                                          Driver('childOutput', instanceKey, name))
                return
            if existing.isReset != (netKind == 'reset'):
                diag.logError(
                    f"Instance '{instRow['instance']}' of block "
                    f"'{childBlock}' maps output {netKind} '{name}' to "
                    f"'{net}', a {'reset' if existing.isReset else 'clock'} "
                    f"net of '{containerBlock}', not a {netKind} net (V4).")
                return
            if existing.driver is not None and existing.driver.kind == 'input':
                diag.logError(
                    f"Instance '{instRow['instance']}' of block "
                    f"'{childBlock}' binds output {netKind} '{name}' to "
                    f"'{net}', an INPUT of '{containerBlock}' already "
                    f"driven by its own parent (V5).")
                return
            if existing.driver is not None:
                diag.logError(
                    f"Container '{containerBlock}' net '{net}' has more "
                    f"than one driver: instance '{instRow['instance']}''s "
                    f"output {netKind} '{name}' and an earlier one (V5).")
                return
            existing.driver = Driver('childOutput', instanceKey, name)

        for name, clockDecl in childDomain.clocks.items():
            if clockDecl.direction == 'output':
                bindOutput(name, clockMap, 'clock')
        for name, resetDecl in childDomain.resets.items():
            if resetDecl.direction == 'output':
                bindOutput(name, resetMap, 'reset')

    # V20 driver assignment (spec §4.6 table): a declared output no child
    # instance's own binding drove above is produced by the container's own
    # implementation instead - the only other source such a net can have.
    for container in containers.values():
        for net in container.nets.values():
            if net.kind == 'declared' and net.driver is None:
                net.driver = Driver('ownImplementation')

    # Input binding, in precedence order (spec §4.4, R10): an instance's own
    # clocks:/resets: map entry, else name match for an input, else the
    # default-clock/selected-reset fallback for a block clock or reset named
    # literally clk/rst_n. A map value is a container-declared net or a
    # local net the output pass above already created; `~` is never valid
    # for an input (only an output may be left unconnected).
    # (instanceKey, resetName, containerKey, boundClockNet) for an rst_n
    # fallback onto a LOCAL clock net: its own selected reset may be a local
    # reset net (spec §4.2), not resolvable until every local net's own
    # membership is known, so such an entry is resolved in a deferred pass
    # below instead of here.
    pendingRstFallback = list()
    for instanceKey, instRow in instances.items():
        childKey = instRow['instanceTypeKey']
        containerKey = instRow['containerKey']
        if instRow['container'] == ClockTree.ROOT_KEY:
            # Recorded for reachability; bound against root's own testbench
            # nets separately, by _bindTopInstance() below, once every
            # instance's own containerKey is known here.
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

        clockMap = instRow['clocks'] if 'clocks' in instRow else {}
        resetMap = instRow['resets'] if 'resets' in instRow else {}
        for mapKey, mapRow in clockMap.items():
            if mapKey not in childDomain.clocks:
                diag.logError(
                    f"Instance '{instRow['instance']}' maps clock '{mapKey}', "
                    f"which is not one of block '{childBlock}''s own declared "
                    f"clocks ({', '.join(childDomain.clocks)}) (V4). {diagLoc(mapRow)}")
        for mapKey, mapRow in resetMap.items():
            if mapKey not in childDomain.resets:
                diag.logError(
                    f"Instance '{instRow['instance']}' maps reset '{mapKey}', "
                    f"which is not one of block '{childBlock}''s own declared "
                    f"resets ({', '.join(childDomain.resets)}) (V4). {diagLoc(mapRow)}")

        def resolveMappedNet(mapRow, netKind):
            net = mapRow['bind']
            if not net:
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' "
                    f"maps '{mapRow[netKind]}' to `~`; an input {netKind} "
                    f"needs an actual net to consume, declared or local - "
                    f"`~` is only for leaving an OUTPUT unconnected (V4). "
                    f"{diagLoc(mapRow)}")
                return None
            netObj = container.nets.get(net)
            if netObj is None or netObj.isReset != (netKind == 'reset'):
                declared = ', '.join(f"'{name}'" for name in
                                     (containerDomain.resets if netKind == 'reset'
                                      else containerDomain.clocks))
                local = ', '.join(f"'{name}'" for name, localNet in container.nets.items()
                                  if localNet.kind == 'local' and localNet.isReset == (netKind == 'reset'))
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' "
                    f"in container '{containerBlock}' maps {netKind} "
                    f"'{mapRow[netKind]}' to '{net}', which is not one of "
                    f"'{containerBlock}''s declared {netKind}s ({declared}) "
                    f"or its local {netKind} nets ({local or 'none'}) (V4). "
                    f"{diagLoc(mapRow)}")
                return None
            return net

        def rejectSelfDrivenInput(net, ownName, netKind):
            # V5: "an instance never binds two entries to a net one of them
            # drives" - here a MAP entry binding one of the instance's own
            # INPUTS onto a net one of that SAME instance's own OUTPUTS
            # already supplies (a combinational loop through the child).
            netObj = container.nets[net]
            if (netObj.driver is not None and netObj.driver.kind == 'childOutput'
                    and netObj.driver.instanceKey == instanceKey):
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' "
                    f"binds its own {netKind} '{ownName}' to '{net}', which its "
                    f"own {netKind} '{netObj.driver.blockPort}' already drives "
                    f"(V5): an instance may not bind one of its own inputs to a "
                    f"net one of its own outputs supplies.")
                return True
            return False

        clockBindNet = dict()
        for clockName, clockDecl in childDomain.clocks.items():
            if clockDecl.direction != 'input':
                continue
            mapRow = clockMap.get(clockName)
            if mapRow is not None:
                net = resolveMappedNet(mapRow, 'clock')
                if net is None:
                    continue
                if rejectSelfDrivenInput(net, clockName, 'clock'):
                    continue
                binding = 'map'
            elif clockName in containerDomain.clocks:
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
            mapRow = resetMap.get(resetName)
            if mapRow is not None:
                net = resolveMappedNet(mapRow, 'reset')
                if net is None:
                    continue
                if rejectSelfDrivenInput(net, resetName, 'reset'):
                    continue
                binding = 'map'
            elif resetName in containerDomain.resets:
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
                # The candidates for boundClockNet's selected reset are the
                # container's own declared resets on it AND any local reset
                # nets belonging to it (spec §4.2 "selected reset"): a
                # DECLARED clock, including an exported output the container
                # itself does not release, may still be released by a local
                # reset net a child's output drives onto it. Local net
                # membership is not fully known until every instance's
                # bindings, output and input alike, are resolved, so this is
                # always deferred, whether boundClockNet is a declared or a
                # local net.
                pendingRstFallback.append((instanceKey, resetName, containerKey, boundClockNet))
                continue
            else:
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' "
                    f"in container '{containerBlock}' has no binding for its "
                    f"reset '{resetName}': '{containerBlock}' declares no "
                    f"reset of that name, and only 'rst_n' falls back to a "
                    f"selected reset (V3). Declared resets of "
                    f"'{containerBlock}': ({', '.join(containerDomain.resets)}).")
                continue
            if not isAsync and container.nets[net].kind == 'declared':
                # V6: the reset's own clock, mapped through this instance,
                # must be the clock the bound container reset belongs to.
                # A container reset that is itself async belongs to no
                # clock (''), which never equals a real bound clock name,
                # so a synchronous child reset bound onto it (by map or by
                # name match) fails here rather than passing unchecked. A
                # LOCAL net's own membership is not yet known here - the
                # supplying instance's own clock port may not be bound
                # until a later instance in this same pass, or may itself
                # be an input awaiting the ordinary binding above to reach
                # it - so that case is checked once in a follow-up pass
                # below, after every instance's clock and reset bindings,
                # output and input alike, have been resolved.
                childClockOfReset = resetDecl.clock
                boundClockNet = clockBindNet.get(childClockOfReset)
                netMembership = container.nets[net].clockNet
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

    # The top instance's own binding to the project file's testbench nets
    # (spec §4.8, R3): map, name match, or the clk/rst_n default fallback
    # (R10); V9, V10, V11. Independent of every ordinary container's own
    # local-net machinery above, since the top's own OUTPUTS are observed by
    # the testbench rather than bound onto a net (R11 exception), so root
    # never has a local net to defer against.
    _bindTopInstance(root, instances, domains, blocks, testbenchClocks, testbenchResets, diag)

    # Reset-net membership on the SUPPLIER side (spec §4.4 "Local net": "the
    # clock the supplying output's block reset belongs to, mapped through
    # the supplier's instance"), deferred from the loops above: not
    # resolvable there, since the supplier's own clock port - the one its
    # reset belongs to - may itself be an input this same design-wide pass
    # had not yet bound. By now every instance's clock and reset bindings,
    # output and input alike, across the whole design, are resolved, so
    # both directions are available to look up. Covers every reset net a
    # child output drives: a LOCAL net (whose own membership this computes
    # for the first time, then checks every one of its own consumers, spec
    # V6) and a DECLARED net exported onto it (whose membership the
    # container already states; only the supplier side needs checking here,
    # spec V6 - a declared net's own consumers are already checked inline,
    # above, against its always-known membership).
    for container in containers.values():
        consumerNet = _consumerNetIndex(container)
        driverNet = _driverNetIndex(container)
        for net in container.nets.values():
            if not net.isReset or net.driver is None or net.driver.kind != 'childOutput':
                continue
            supplierInstanceKey = net.driver.instanceKey
            supplierBlockKey = instances[supplierInstanceKey]['instanceTypeKey']
            supplierDomain = domains[supplierBlockKey]
            supplierResetDecl = supplierDomain.resets[net.driver.blockPort]
            if supplierResetDecl.isAsync:
                continue  # belongs to no clock (spec §4.2)
            supplierClockDecl = supplierDomain.clocks[supplierResetDecl.clock]
            index = consumerNet if supplierClockDecl.direction == 'input' else driverNet
            supplierClockNet = index.get((supplierInstanceKey, supplierResetDecl.clock))
            if supplierClockNet is None:
                # The supplier's own clock port already failed to bind (an
                # earlier diagnostic reported it); do not cascade a "released
                # on clock 'None'" finding on every one of this net's
                # consumers on top of that.
                continue
            if net.kind == 'local':
                net.clockNet = supplierClockNet
                for consumer in net.consumers:
                    consumerDomain = domains[instances[consumer.instanceKey]['instanceTypeKey']]
                    consumerResetDecl = consumerDomain.resets[consumer.blockPort]
                    if consumerResetDecl.isAsync:
                        continue
                    boundClockNet = consumerNet.get((consumer.instanceKey, consumerResetDecl.clock))
                    if boundClockNet and net.clockNet != boundClockNet:
                        diag.logError(
                            f"Instance '{instances[consumer.instanceKey]['instance']}' "
                            f"binds reset '{consumer.blockPort}' to '{net.name}', a "
                            f"local net released on clock '{net.clockNet}', but that "
                            f"instance's own clock '{consumerResetDecl.clock}' is "
                            f"bound to '{boundClockNet}' instead (V6).")
            elif supplierClockNet is not None and supplierClockNet != net.clockNet:
                diag.logError(
                    f"Instance '{instances[supplierInstanceKey]['instance']}' exports "
                    f"reset '{net.driver.blockPort}' onto "
                    f"'{blocks[container.blockKey]['block']}''s declared output "
                    f"reset '{net.name}', released on clock '{net.clockNet}', but "
                    f"the supplier's own reset belongs to clock '{supplierClockNet}' "
                    f"instead (V6).")

    # Deferred rst_n fallback (spec §4.2 "selected reset", R10): the
    # candidates for boundClockNet are the container's own declared resets
    # belonging to it (any direction - an exported output clock the
    # container does not itself release may still be released by a local
    # net) plus its local reset nets, not resolvable until the membership
    # pass just above has run. The declared candidate marked default: true
    # wins outright; otherwise the sole candidate, declared or local, is the
    # fallback's answer. Membership (V6) is satisfied by construction: every
    # candidate here already belongs to boundClockNet.
    for instanceKey, resetName, containerKey, boundClockNet in pendingRstFallback:
        container = containers[containerKey]
        containerDomain = domains[containerKey]
        declaredCandidates = [name for name, resetDecl in containerDomain.resets.items()
                              if not resetDecl.isAsync and resetDecl.clock == boundClockNet]
        localCandidates = [netName for netName, net in container.nets.items()
                          if net.kind == 'local' and net.isReset and net.clockNet == boundClockNet]
        markedDefault = [name for name in declaredCandidates
                        if containerDomain.resets[name].default]
        instRow = instances[instanceKey]
        childBlock = blocks[instRow['instanceTypeKey']]['block']
        containerBlock = blocks[containerKey]['block']
        if len(markedDefault) == 1:
            chosen = markedDefault[0]
        elif len(declaredCandidates) + len(localCandidates) == 1:
            chosen = (declaredCandidates + localCandidates)[0]
        else:
            diag.logError(
                f"Instance '{instRow['instance']}' of block '{childBlock}' in "
                f"container '{containerBlock}' falls back to the selected reset "
                f"of container clock '{boundClockNet}' for its reset 'rst_n', but "
                f"it has {len(declaredCandidates) + len(localCandidates)} "
                f"candidates and none is marked default: true (V11).")
            continue
        container.nets[chosen].consumers.append(Consumer(instanceKey, resetName, 'fallback'))

    # V22: a local net is consumed by at least one child input binding of
    # the container that holds it - `~` is the way to leave an output
    # unused, so a driven-and-never-consumed net is an error naming the
    # driving binding (spec §4.6, §4.4). Checked once every container's
    # inputs have all been bound, so a consumer bound later in declaration
    # order is not missed.
    for containerKey, container in containers.items():
        containerBlock = blocks[containerKey]['block']
        for net in container.nets.values():
            if net.kind != 'local' or net.consumers:
                continue
            driverInstance = instances[net.driver.instanceKey]['instance']
            diag.logError(
                f"Container '{containerBlock}' net '{net.name}', driven by "
                f"instance '{driverInstance}' output '{net.driver.blockPort}', "
                f"has no consumer (V22): a local net must be consumed by at "
                f"least one child input binding, or bound to `~` at the "
                f"driving output instead.")

    # R6/V19, second pass (spec §4.2 "selected reset"): extend each
    # container clock's selected reset with the container's own local reset
    # nets as candidates, now that local net membership (clockNet) and every
    # consumer - including the rst_n fallback binds just resolved above -
    # are known. A declared reset marked default: true wins outright, as at
    # BlockDomains.build() (declared-only, first pass); several declared
    # defaults on one clock were already reported there (V18) and are left
    # as-is. Absent a marked default, the candidate set is the block's own
    # declared resets on the clock plus its local reset nets on it, a local
    # net consumed only by asynchronous reset inputs excluded (it releases
    # nothing synchronously, spec §4.9): the sole candidate is selected;
    # zero or several is left unresolved, reported later where generated
    # logic actually needs one (V19).
    for containerKey, container in containers.items():
        domain = domains[containerKey]
        for clockName in domain.clocks:
            declaredForClock = [name for name, resetDecl in domain.resets.items()
                                if not resetDecl.isAsync and resetDecl.clock == clockName]
            marked = [name for name in declaredForClock if domain.resets[name].default]
            if len(marked) == 1:
                domain.selectedReset[clockName] = marked[0]
                continue
            if len(marked) > 1:
                continue
            localCandidates = []
            for netName, net in container.nets.items():
                if net.kind != 'local' or not net.isReset or net.clockNet != clockName:
                    continue
                if all(domains[instances[c.instanceKey]['instanceTypeKey']]
                       .resets[c.blockPort].isAsync for c in net.consumers):
                    continue
                localCandidates.append(netName)
            candidates = declaredForClock + localCandidates
            domain.selectedReset[clockName] = candidates[0] if len(candidates) == 1 else None

    # V13: an AUTHORED connection clock: names a container clock that
    # exactly one INPUT block clock of the instance's own consumer edges, in
    # this same container, resolves to (spec §4.3 rule 2). Read back
    # from the binding just computed rather than re-derived, so a renamed
    # instance map is respected: the block's own clock name need no longer
    # equal the container's. An unstated clock: is exempt: rule 3 gives it to
    # each endpoint's own block default independently, with no requirement
    # that the two names agree.
    for connRow in connections.values():
        if (connRow['_context'], connRow['connection']) not in connectionsWithAuthoredClock:
            continue
        clockName = connRow['clock']
        for end in connRow['ends'].values():
            instanceKey = end['instanceKey']
            instRow = instances[instanceKey]
            containerKey = instRow['containerKey']
            block = blocks[end['instanceTypeKey']]['block']
            if containerKey == ClockTree.ROOT_KEY:
                # The topInstance's own binding to the testbench is
                # resolved separately by `_bindTopInstance`; nothing to
                # resolve against here.
                continue
            matches = _inputClocksResolvingTo(containers[containerKey], instanceKey, clockName)
            if len(matches) == 1:
                continue
            if not matches:
                diag.logError(
                    f"Connection '{connRow['connection']}' names clock: "
                    f"'{clockName}', but no input clock of instance "
                    f"'{instRow['instance']}' (block '{block}') resolves to "
                    f"that container clock (V13).")
            else:
                diag.logError(
                    f"Connection '{connRow['connection']}' names clock: "
                    f"'{clockName}', but more than one input clock of "
                    f"instance '{instRow['instance']}' (block '{block}') "
                    f"resolves to it ({', '.join(matches)}), leaving the "
                    f"block clock ambiguous (V13).")

    # Built once per container, from the ordinary binding pass above: the
    # router/handler/memory-accessor resolution below each read another
    # container's consumer edges by (instanceKey, blockPort) many times over,
    # so the reverse index is worth sharing rather than rebuilding per lookup
    # (a router's own container, a leaf's own container, a memory's owning
    # container may each be read from several call sites below).
    consumerNetByContainer = {blockKey: _consumerNetIndex(container)
                              for blockKey, container in containers.items()}

    # V14 (spec §4.3 "On a declared port"): a declared port's own clock:
    # (its own authored clock: or the block default when it names none) and
    # a connection reaching it are not read as a precedence; where both are
    # present they must agree. Checked per end: an end's own portName may be
    # one of the end's own block's declared ports:/registerPorts: entries (a
    # reusable IP typically declares these); an ordinary top-down end
    # declares neither and is exempt, having no port-level clock: of its own
    # to disagree with.
    for connRow in connections.values():
        clockName = connRow['clock']
        if not clockName:
            continue
        for end in connRow['ends'].values():
            instanceKey = end['instanceKey']
            instRow = instances[instanceKey]
            containerKey = instRow['containerKey']
            if containerKey == ClockTree.ROOT_KEY:
                # The topInstance's own binding to the testbench is
                # resolved separately by `_bindTopInstance`; nothing to
                # resolve against here.
                continue
            endBlockKey = end['instanceTypeKey']
            declaredClock = _declaredPortClock(blocks, domains, endBlockKey, end['portName'])
            if declaredClock is None:
                continue
            if declaredClock is _NO_DEFAULT_CLOCK:
                # The port IS declared (rule 1) but names no clock: of its
                # own, and the block has no default clock for rule 3 to
                # supply either (V15 already reported that block-level
                # defect) - so the port's own domain is undefined and can
                # never agree with a connection that states one.
                diag.logError(
                    f"Port '{end['portName']}' of block "
                    f"'{blocks[endBlockKey]['block']}' (instance "
                    f"'{instRow['instance']}') is declared but names no "
                    f"clock: and the block has no default clock, so its "
                    f"own domain is undefined; connection "
                    f"'{connRow['connection']}' reaching it derives to "
                    f"'{clockName}' instead; a declared port's clock: and "
                    f"its connection's clock: must agree (V14).")
                continue
            consumerNet = consumerNetByContainer[containerKey]
            boundNet = consumerNet.get((instanceKey, declaredClock))
            if boundNet is None:
                # The declared clock itself failed to bind (an earlier
                # diagnostic already reported it); do not also report a V14
                # mismatch against a clock that was never resolved.
                continue
            if boundNet != clockName:
                diag.logError(
                    f"Port '{end['portName']}' of block "
                    f"'{blocks[endBlockKey]['block']}' (instance "
                    f"'{instRow['instance']}') declares clock: "
                    f"'{declaredClock}' (its own, or the block default when "
                    f"unstated), but connection '{connRow['connection']}' "
                    f"reaching it derives to '{clockName}' instead; a "
                    f"declared port's clock: and its connection's clock: "
                    f"must agree (V14).")

    # V16 (spec §4.3): a connectionMaps: row's boundary port derives its
    # domain inside-out from the inner port it routes to, not from the
    # outer connection that reaches the boundary - the override the
    # projectOpen view used to compute per render, now a fact computed once
    # here and persisted (ClockTree.rows()/portDomainRows) for the view to
    # read back, one row per connectionMaps port: the inner port's own
    # declared clock, else the INNER block's default clock (a top-down inner
    # port names no declared clock at all, so it takes its own block's
    # default the same way an ordinary unstated port would, spec §4.3 rule
    # 3 - not the OUTER block's default, which a renamed inner instance map
    # need not agree with). A row is contributed for every connectionMaps
    # port except where the inner block has no default clock either, or the
    # inner instance's own bind did not resolve - both already reported
    # elsewhere (V15/V18, V3) - which leave nothing here to derive from.
    # A connectionMaps: boundary port whose inner net is a LOCAL net the
    # container never exports is an error (V16): the boundary would carry
    # data in a domain the parent cannot drive or name. The fix is to
    # declare the net as an output clock/reset instead.
    portDomainRows = []
    for connMap in connectionMaps.values():
        outerBlockKey = connMap['blockKey']
        boundaryPortName = connMap['portName']
        innerInstanceKey = connMap['instanceKey']
        innerBlockKey = instances[innerInstanceKey]['instanceTypeKey']
        innerPortName = connMap['instancePortName']
        innerClockName = _declaredPortClock(blocks, domains, innerBlockKey, innerPortName)
        if innerClockName is _NO_DEFAULT_CLOCK:
            # Declared, but the inner block has no default clock either
            # (V15 already reported); nothing to derive a boundary domain
            # from here, the same as the "not declared at all" case below.
            innerClockName = None
        innerClockName = innerClockName or domains[innerBlockKey].defaultClock
        if innerClockName is None:
            continue
        consumerNet = consumerNetByContainer[outerBlockKey]
        domainClock = consumerNet.get((innerInstanceKey, innerClockName))
        if domainClock is None:
            continue
        if containers[outerBlockKey].nets[domainClock].kind == 'local':
            diag.logError(
                f"Boundary port '{boundaryPortName}' of block "
                f"'{blocks[outerBlockKey]['block']}' derives to '{domainClock}', "
                f"a local net of '{blocks[outerBlockKey]['block']}' the block "
                f"does not export (V16): a boundary port timed by a local "
                f"net the container does not export would carry data in a "
                f"domain the parent cannot drive or name; declare "
                f"'{domainClock}' as an output clock or reset instead.")
            continue
        portDomainRows.append((outerBlockKey, boundaryPortName, domainClock, len(portDomainRows)))

    # Instances transitively contained by this build's topInstance (spec
    # §4.8), walked the same way ClockTree._reachableBlockKeys() walks
    # blocks: a block shared with another project (a reusable IP) may have
    # an instance in that project's own standalone harness, which
    # config/postParseRegisterPorts.py's own dispatch synthesis already
    # scopes out (it routes only a reachable instance's register bus) - the
    # register-port and memory-accessor resolution below scope out the same
    # instances, for the same reason: an out-of-scope instance has no
    # router or accessor binds of this build's making to check at all.
    reachableInstances = _reachableInstanceKeys(containers, root)

    _resolveRouterBusClockReset(domains, instances, blocks, consumerNetByContainer,
                               reachableInstances)
    _resolveRegisterHandlerBinds(domains, containers, instances, connections, blocks,
                                 consumerNetByContainer, reachableInstances, diag)
    _checkMemoryAccessorDomains(domains, instances, memoryConnections, consumerNetByContainer,
                                reachableInstances, diag)

    # V19, hasVl clause (spec §4.8): the co-simulation wrapper resets each port's
    # BFM with the port clock's selected reset, so every clock timing a port of a
    # hasVl block needs one. Declared, connection-derived and boundary ports here.
    # Declaring-project scope, as V21.
    portDomainsByBlock = dict()
    for outerBlockKey, boundaryPortName, domainClock, _ in portDomainRows:
        portDomainsByBlock.setdefault(outerBlockKey, []).append((boundaryPortName, domainClock))
    connectionEndsByBlock = dict()
    for connRow in connections.values():
        for end in connRow['ends'].values():
            connectionEndsByBlock.setdefault(end['instanceTypeKey'], []).append((connRow, end))
    for blockKey, blockRow in blocks.items():
        if not blockRow['hasVl'] or contextOwningProject[blockRow['_context']] != rootProjectName:
            continue
        domain = domains[blockKey]
        portsByClock = OrderedDict()
        # Rule order mirrors getBDPortDomain: explicit port clock:, then the
        # connectionMaps boundary row, then the block default.
        boundaryClocks = dict(portDomainsByBlock.get(blockKey, []))
        # Every boundary port name, before registerBusPort is popped out of
        # boundaryClocks below: reused by the connection branch so a port
        # already resolved here - the register-bus port included - is never
        # derived a second time, once wrong.
        boundaryPorts = set(boundaryClocks)
        boundaryClocks.pop(domain.registerBusPort, None)
        for portName, declaredRow in blockRow.get('ports', {}).items():
            if declaredRow['clock']:
                clockName = declaredRow['clock']
            elif portName in boundaryClocks:
                clockName = boundaryClocks.pop(portName)
            else:
                clockName = domain.defaultClock
                if clockName is None:
                    # Undefined domain; V15 already reported it.
                    continue
            portsByClock.setdefault(clockName, []).append(portName)
        for boundaryPortName, domainClock in boundaryClocks.items():
            portsByClock.setdefault(domainClock, []).append(boundaryPortName)
        # Top-down port: the V13 consumer-edge match, re-applied per end because
        # V13 stores nothing and walks only authored connections.
        for connRow, end in connectionEndsByBlock.get(blockKey, []):
            portName = end['portName']
            if (portName in boundaryPorts
                    or _declaredPortClock(blocks, domains, blockKey, portName) is not None):
                continue
            instanceKey = end['instanceKey']
            authoredClock = connRow['clock']
            if authoredClock:
                containerKey = instances[instanceKey]['containerKey']
                if containerKey == ClockTree.ROOT_KEY:
                    continue
                matches = _inputClocksResolvingTo(containers[containerKey], instanceKey, authoredClock)
                portClock = matches[0] if len(matches) == 1 else None
            else:
                portClock = domain.defaultClock
            if portClock is None:
                # Already reported by V13 (no or ambiguous match) or V15 (no default).
                continue
            bucket = portsByClock.setdefault(portClock, [])
            if portName not in bucket:
                bucket.append(portName)
        for clockName, portNames in portsByClock.items():
            if domain.selectedReset.get(clockName) is not None:
                continue
            candidates = [name for name, resetDecl in domain.resets.items()
                         if not resetDecl.isAsync and resetDecl.clock == clockName]
            cause = (f"resets {', '.join(candidates)} are declared on it "
                     f"and none is marked default: true" if candidates else
                     "no reset is selected for it")
            diag.logError(
                f"Block '{domain.block}' (hasVl): port(s) "
                f"{', '.join(portNames)} are timed by clock '{clockName}', "
                f"which has no selected reset (V19): {cause}. The "
                f"co-simulation wrapper's BFM needs one; mark a reset on "
                f"'{clockName}' default: true or declare one.")

    # V19: a block clock hosting a register bus (a router's or a served
    # leaf's own registerClock, spec §4.3) must have a selected reset - a
    # router's own bus reset port left unbound, or a reusable IP declaring
    # resets: {} with no registerPorts: reset: override, otherwise reaches
    # generation with no reset to emit at all (registerReset stays None).
    # registerClock/registerReset are set together only for a router or a
    # served leaf (BlockDomains' own contract); a block that is neither
    # keeps both None and is not this rule's concern.
    for domain in domains.values():
        if domain.registerClock is not None and domain.registerReset is None:
            diag.logError(
                f"Block '{domain.block}' hosts its register bus on clock "
                f"'{domain.registerClock}', but that clock has no selected "
                f"reset (V19): a router's or a served leaf's register bus "
                f"clock must have one.")

    # V24 (spec R20): a regAccess memory must sit on its block's register bus
    # clock until the R20 bridge exists. Routers and handlers own no memories, so
    # only served leaves reach the compare, in their own clock-port names.
    for domain in domains.values():
        if domain.registerClock is None:
            continue
        for memDomain in domain.memories:
            if not memDomain.regAccess or memDomain.clock == domain.registerClock:
                continue
            diag.logError(
                f"Memory '{memDomain.memory}' of block '{domain.block}' is "
                f"regAccess on clock '{memDomain.clock}', but the block's "
                f"register bus is on '{domain.registerClock}' (V24): the R20 "
                f"bridge is not implemented; declare the memory on the "
                f"register bus clock.")

    _checkSupplyGraph(domains, containers, instances, blocks, diag)

    # Standalone simulation attributes (spec §4.8, R24, V21): resolved once
    # every instance's own bindings, across the whole design, are known.
    resolvedByInstance = _resolveAllInstances(root, containers, domains, instances)
    _resolveStandaloneAttrs(domains, blocks, instances, resolvedByInstance,
                           testbenchClocks, testbenchResets,
                           contextOwningProject, rootProjectName, diag)

    return ClockTree(domains, containers, root, diag, portDomainRows)


def _bindTopInstance(root, instances, domains, blocks, testbenchClocks, testbenchResets, diag):
    """Bind the top instance's own input clocks and resets to the project
    file's testbench nets (spec §4.8, R3): map, name match, or the clk/rst_n
    default fallback (R10); V9 (a top input reset belongs to a top input
    clock the testbench also binds), V10 (every testbench entry binds
    something), V11 (the rst_n fallback's clock has a selected reset). A
    project declaring no topInstance: leaves root.instances empty, exempt
    from V10 (spec §4.1). The top's own OUTPUTS are observed by the
    testbench, not bound onto a net (R11 exception), so this never creates a
    local net and needs none of the deferred local-net machinery the
    ordinary per-container pass above uses; root's own nets are always
    'testbench' kind, whose membership (`clockNet`) is already known from
    their own declaration, so no second pass is needed for it either.
    """
    if not root.instances:
        return
    ((topInstanceKey, topBlockKey),) = root.instances.items()
    topDomain = domains[topBlockKey]
    topBlock = blocks[topBlockKey]['block']
    instRow = instances[topInstanceKey]

    rootDefaultClock = next((name for name, row in testbenchClocks.items() if row['default']), None)
    byClock = dict()
    for name, row in testbenchResets.items():
        byClock.setdefault(row['clock'], list()).append(name)
    rootSelectedReset = dict()
    for clockName, names in byClock.items():
        marked = [name for name in names if testbenchResets[name]['default']]
        rootSelectedReset[clockName] = (marked[0] if len(marked) == 1
                                        else (names[0] if len(names) == 1 else None))

    clockMap = instRow['clocks'] if 'clocks' in instRow else {}
    resetMap = instRow['resets'] if 'resets' in instRow else {}

    def diagLoc(row):
        return diag.diagnosticLocation(row['_context'], row.get('lc'))

    for mapKey, mapRow in clockMap.items():
        if mapKey not in topDomain.clocks:
            diag.logError(
                f"topInstance '{instRow['instance']}' maps clock '{mapKey}', "
                f"which is not one of block '{topBlock}''s own declared "
                f"clocks ({', '.join(topDomain.clocks)}) (V4). {diagLoc(mapRow)}")
    for mapKey, mapRow in resetMap.items():
        if mapKey not in topDomain.resets:
            diag.logError(
                f"topInstance '{instRow['instance']}' maps reset '{mapKey}', "
                f"which is not one of block '{topBlock}''s own declared "
                f"resets ({', '.join(topDomain.resets)}) (V4). {diagLoc(mapRow)}")

    def resolveMappedNet(mapRow, netKind):
        net = mapRow['bind']
        if not net:
            diag.logError(
                f"topInstance '{instRow['instance']}' of block '{topBlock}' "
                f"maps '{mapRow[netKind]}' to `~`; an input {netKind} needs an "
                f"actual testbench net to consume (V4). {diagLoc(mapRow)}")
            return None
        netObj = root.nets.get(net)
        if netObj is None or netObj.isReset != (netKind == 'reset'):
            declared = ', '.join(f"'{name}'" for name in
                                 (testbenchResets if netKind == 'reset' else testbenchClocks))
            diag.logError(
                f"topInstance '{instRow['instance']}' of block '{topBlock}' "
                f"maps {netKind} '{mapRow[netKind]}' to '{net}', which is not "
                f"one of the project file's declared {netKind}s ({declared}) "
                f"(V4). {diagLoc(mapRow)}")
            return None
        return net

    clockBindNet = dict()
    for clockName, clockDecl in topDomain.clocks.items():
        if clockDecl.direction != 'input':
            continue
        mapRow = clockMap.get(clockName)
        if mapRow is not None:
            net = resolveMappedNet(mapRow, 'clock')
            if net is None:
                continue
            binding = 'map'
        elif clockName in testbenchClocks:
            net = clockName
            binding = 'name'
        elif clockName == 'clk' and rootDefaultClock:
            net = rootDefaultClock
            binding = 'fallback'
        else:
            diag.logError(
                f"topInstance '{instRow['instance']}' of block '{topBlock}' has "
                f"no binding for its clock '{clockName}': the project file "
                f"declares no clock of that name, and only 'clk' falls back to "
                f"the testbench default clock (V3). Declared testbench clocks: "
                f"({', '.join(testbenchClocks)}).")
            continue
        clockBindNet[clockName] = net
        root.nets[net].consumers.append(Consumer(topInstanceKey, clockName, binding))

    for resetName, resetDecl in topDomain.resets.items():
        if resetDecl.direction != 'input':
            continue
        isAsync = resetDecl.isAsync
        mapRow = resetMap.get(resetName)
        if mapRow is not None:
            net = resolveMappedNet(mapRow, 'reset')
            if net is None:
                continue
            binding = 'map'
        elif resetName in testbenchResets:
            net = resetName
            binding = 'name'
        elif isAsync:
            diag.logError(
                f"topInstance '{instRow['instance']}' of block '{topBlock}' has "
                f"no binding for its asynchronous reset '{resetName}': the "
                f"project file declares no reset of that name, and an "
                f"asynchronous reset input takes no default fallback (V4).")
            continue
        elif resetName == 'rst_n':
            boundClockNet = clockBindNet.get(resetDecl.clock)
            if boundClockNet is None:
                continue
            net = rootSelectedReset.get(boundClockNet)
            if not net:
                diag.logError(
                    f"topInstance '{instRow['instance']}' of block '{topBlock}' "
                    f"falls back to the selected reset of testbench clock "
                    f"'{boundClockNet}' for its reset 'rst_n', but that clock "
                    f"has none (V11).")
                continue
            binding = 'fallback'
        else:
            diag.logError(
                f"topInstance '{instRow['instance']}' of block '{topBlock}' has "
                f"no binding for its reset '{resetName}': the project file "
                f"declares no reset of that name, and only 'rst_n' falls back "
                f"to a selected reset (V3). Declared testbench resets: "
                f"({', '.join(testbenchResets)}).")
            continue
        if not isAsync:
            # V9: a top input reset belongs to an input clock of the top
            # block that the testbench also binds. V6: the testbench reset it
            # lands on must release on the SAME testbench clock.
            boundClockNet = clockBindNet.get(resetDecl.clock)
            if boundClockNet is None:
                clockDeclOfReset = topDomain.clocks.get(resetDecl.clock)
                if clockDeclOfReset is not None and clockDeclOfReset.direction == 'input':
                    # Its own clock already failed to bind (V3 reported it);
                    # do not also report a V9 finding against a clock that
                    # never resolved.
                    continue
                diag.logError(
                    f"topInstance '{instRow['instance']}' of block '{topBlock}' "
                    f"reset '{resetName}' belongs to clock '{resetDecl.clock}', "
                    f"which is not an input clock of '{topBlock}' (V9): the "
                    f"testbench can only release a reset of a clock it "
                    f"generates.")
                continue
            netMembership = root.nets[net].clockNet
            if netMembership != boundClockNet:
                diag.logError(
                    f"topInstance '{instRow['instance']}' of block '{topBlock}' "
                    f"would bind clock '{resetDecl.clock}' to '{boundClockNet}' "
                    f"and reset '{resetName}' to '{net}', but the testbench "
                    f"releases '{net}' on clock '{netMembership}', not on "
                    f"'{boundClockNet}' (V6).")
                continue
        root.nets[net].consumers.append(Consumer(topInstanceKey, resetName, binding))

    # V10: every testbench entry binds something - an entry the top block
    # never consumes would have the testbench generate a clock or reset the
    # design does not have.
    for netName, net in root.nets.items():
        if net.consumers:
            continue
        diag.logError(
            f"Testbench {'reset' if net.isReset else 'clock'} '{netName}' binds "
            f"no input of the top block '{topBlock}' (V10): every testbench "
            f"clock and reset must bind an input of the top block.")


def _inputClocksResolvingTo(container, instanceKey, netName):
    """The instance's input block clocks whose consumer edge in `container`
    resolves to clock net `netName` (spec §4.3 rule 2)."""
    net = container.nets.get(netName)
    if net is None or net.isReset:
        return []
    return [consumer.blockPort for consumer in net.consumers
           if consumer.instanceKey == instanceKey]


# Sentinel `_declaredPortClock` returns instead of None when the port IS
# declared but names no clock: and the block has no default clock either:
# distinct from None ("not declared at all", an ordinary top-down port),
# so a caller comparing against a connection's own clock: (V14) does not
# silently exempt a genuinely declared port whose domain happens to be
# undefined (a defect V15 already reports at the block level).
_NO_DEFAULT_CLOCK = object()


def declaredPortRow(blockRow, portName):
    """The block's own `ports:`/`registerPorts:`/`addressBlock:` row
    declaring `portName`, or None when the block declares no such entry -
    an ordinary top-down port (spec §4.3). `ports:` and `registerPorts:`
    share one module namespace (V7), so at most one of them declares a
    given name. Shared with processYaml.py's own getBDPortDomain (rule 1),
    so the declared-row lookup exists in exactly one place.
    """
    if portName == 'addressBlock':
        return blockRow.get('addressBlock')
    declaredRow = (blockRow.get('ports') or {}).get(portName)
    if declaredRow is None:
        declaredRow = (blockRow.get('registerPorts') or {}).get(portName)
    return declaredRow


def _declaredPortClock(blocks, domains, blockKey, portName):
    """The clock a block's OWN ports:/registerPorts:/addressBlock: entry
    named `portName` is timed by (spec §4.3 "On a declared port"): its own
    authored clock:, else the block default. None means `portName` names no
    such declaration at all - an ordinary top-down port. `_NO_DEFAULT_CLOCK`
    means `portName` IS declared but names no clock: and the block has no
    default clock for rule 3 to supply either (V15 already reported this).
    """
    declaredRow = declaredPortRow(blocks[blockKey], portName)
    if declaredRow is None:
        return None
    if declaredRow['clock']:
        return declaredRow['clock']
    return domains[blockKey].defaultClock or _NO_DEFAULT_CLOCK


def _reachableInstanceKeys(containers, root):
    """Instance keys transitively contained by the build's topInstance,
    walked over `containers` from `root` (spec §4.8) - the same tree
    ClockTree._reachableBlockKeys() walks, collecting instance keys rather
    than the block keys they instantiate.
    """
    reachable = set()
    queue = [root]
    seen = set()
    while queue:
        container = queue.pop()
        for instanceKey, blockKey in container.instances.items():
            reachable.add(instanceKey)
            if blockKey in seen:
                continue
            seen.add(blockKey)
            child = containers.get(blockKey)
            if child is not None:
                queue.append(child)
    return reachable


def _consumerNetIndex(container):
    """Reverse index of one container's consumer edges: (instanceKey,
    blockPort) -> the net name it resolved to.
    """
    index = dict()
    for netName, net in container.nets.items():
        for consumer in net.consumers:
            index[(consumer.instanceKey, consumer.blockPort)] = netName
    return index


def _driverNetIndex(container):
    """Reverse index of one container's own driven nets: (instanceKey,
    blockPort) of the DRIVING child -> the net it drives. The output
    counterpart of `_consumerNetIndex`.
    """
    return {(net.driver.instanceKey, net.driver.blockPort): netName
           for netName, net in container.nets.items()
           if net.driver is not None and net.driver.kind == 'childOutput'}


def _routerBusPorts(routerBlockKey, blocks, domains):
    """The router's own bus clock and reset PORT NAMES (spec §4.3 "Routers"):
    the `addressBlock:` entry's own `clock:`/`reset:`, else the block default
    clock and its selected reset. A nested router's synthesised feed is a
    `connectionMaps:`/`connections:` row with no `clock:` field, so rule 2
    (the feed connection) never applies here; only rule 1 and rule 3 do.
    """
    addressBlockRow = blocks[routerBlockKey]['addressBlock']
    routerDomain = domains[routerBlockKey]
    clockPort = addressBlockRow['clock'] or routerDomain.defaultClock
    resetPort = addressBlockRow['reset'] or routerDomain.selectedReset.get(clockPort)
    return clockPort, resetPort


def _resolveRouterBusClockReset(domains, instances, blocks, consumerNetByContainer,
                                reachableInstances):
    """A router's own busClock/busReset (spec §4.3 "Routers"), stored
    directly on the router's own BlockDomains as a block-level fact: the
    container net its bus clock/reset port (`_routerBusPorts`) is bound to,
    in its own instance's container. A router has exactly one REACHABLE
    instance (config/postParseRegisterPorts.py rejects a multi-instance
    router before this runs, scoped to this build's reachable instances the
    same way its own dispatch synthesis is); an unreachable instance is a
    referenced child project's own standalone-harness router, which this
    build neither routes nor emits (spec §4.8), so it must not be the one
    picked here. One lookup done once here rather than at every view read
    (processYaml.py's getBDBusClockReset).
    """
    instanceByBlock = dict()
    for instanceKey, instRow in instances.items():
        if instanceKey in reachableInstances:
            instanceByBlock.setdefault(instRow['instanceTypeKey'], instanceKey)

    for blockKey, domain in domains.items():
        if not domain.isRouter:
            continue
        instanceKey = instanceByBlock.get(blockKey)
        if instanceKey is None:
            # No REACHABLE instance: either never instantiated at all
            # (config/postParseRegisterPorts.py already rejects an
            # addressBlock: block with no instance in the design, so a
            # build that reached this point does not hit that case), or
            # instantiated only in a referenced child project's own
            # standalone harness, out of this build's own scope (spec
            # §4.8). Either way registerClock/registerReset stay unset.
            continue
        containerKey = instances[instanceKey]['containerKey']
        consumerNet = consumerNetByContainer[containerKey]
        clockPort, resetPort = _routerBusPorts(blockKey, blocks, domains)
        domain.busClockPort = clockPort
        domain.busResetPort = resetPort
        domain.registerClock = consumerNet.get((instanceKey, clockPort))
        if resetPort:
            domain.registerReset = consumerNet.get((instanceKey, resetPort))


def _resolveRegisterHandlerBinds(domains, containers, instances, connections, blocks,
                                 consumerNetByContainer, reachableInstances, diag):
    """Resolve every routed leaf block's own register-port clock/reset
    (spec R25; rule 1 for a reusable IP's `registerPorts:`), storing the
    result on the leaf's own BlockDomains (spec §4.3: "a block-level
    result"), then bind every synthesised `<block>_regs` handler instance's
    own (sole, implicit) clock and reset onto it, with binding kind
    'register' - no instance map authors this bind, so it is not 'map'. The
    handler instance's own binding pass above already gave it a plain
    name-match/fallback bind within its container (the owning leaf block,
    config/postParseRegisterPorts.py's `synthesiseRegHandler`); this
    replaces that guess. A top-down leaf's selection needs the OUTER leaf
    instances' own binds, done above in every container before this runs.

    Only reachable instances of the leaf block are resolved against: a
    reusable IP shared with another project may have an instance in that
    project's own standalone harness, which config/postParseRegisterPorts.py
    itself never routes (its dispatch is scoped to this build's reachable
    instances too), so such an instance has no router serving it in THIS
    build and is not a V8/V25/V26 finding here.
    """
    instancesByBlock = dict()
    for instanceKey, instRow in instances.items():
        if instanceKey in reachableInstances:
            instancesByBlock.setdefault(instRow['instanceTypeKey'], list()).append(instanceKey)

    resolvedLeaves = set()
    for instanceKey, instRow in instances.items():
        handlerBlockKey = instRow['instanceTypeKey']
        if not domains[handlerBlockKey].isRegHandler:
            continue
        leafBlockKey = instRow['containerKey']
        leafBlock = blocks[leafBlockKey]['block']
        leafDomain = domains[leafBlockKey]
        leafContainer = containers[leafBlockKey]
        handlerDomain = domains[handlerBlockKey]
        # A synthesised handler block declares neither clocks: nor resets:,
        # so BlockDomains.build() always gives it exactly the implicit
        # clk/rst_n pair.
        handlerClockName = next(iter(handlerDomain.clocks))
        handlerResetName = next(iter(handlerDomain.resets))
        handlerDomain.busClockPort = handlerClockName
        handlerDomain.busResetPort = handlerResetName

        if leafBlockKey not in resolvedLeaves:
            registerPorts = blocks[leafBlockKey].get('registerPorts')
            if registerPorts:
                portName = next(iter(registerPorts))
                regRow = registerPorts[portName]
                authoredReset = regRow['reset']
                leafDomain.registerClock = regRow['clock'] or leafDomain.defaultClock
                leafDomain.registerReset = authoredReset or leafDomain.selectedReset.get(leafDomain.registerClock)
                leafDomain.registerBusPort = portName
                if leafDomain.registerClock is not None:
                    # None here means the leaf has no default clock and its
                    # registerPorts: entry names none either - already
                    # logged (V15, BlockDomains.build()'s checkPortClock);
                    # checking further against a clock of 'None' would only
                    # add a nonsensical second diagnostic on top of it.
                    _checkRegisterPortsOnBus(
                        leafBlockKey, leafBlock, leafDomain.registerClock,
                        authoredReset, leafDomain.registerReset,
                        instancesByBlock.get(leafBlockKey, []), instances,
                        domains, connections, blocks, consumerNetByContainer, diag)
            else:
                _resolveTopDownRegisterPorts(
                    leafBlockKey, leafBlock, leafDomain,
                    instancesByBlock.get(leafBlockKey, []), instances,
                    domains, connections, blocks, consumerNetByContainer, diag)
            resolvedLeaves.add(leafBlockKey)

        if leafDomain.registerClock is None:
            # Unresolved (V8/V25/V26 already reported): leave the plain
            # name-match/fallback bind the main pass already gave the
            # handler instance.
            continue
        # The handler's OWN registerClock/registerReset (read by
        # getBDBusClockReset for the handler's own view) is the same net as
        # the leaf's: inside the leaf's own container, the leaf's selected
        # register port NAME already IS that net name.
        handlerDomain.registerClock = leafDomain.registerClock
        handlerDomain.registerReset = leafDomain.registerReset
        _rebindConsumer(leafContainer, instanceKey, handlerClockName,
                        leafDomain.registerClock, 'register')
        if leafDomain.registerReset is not None:
            _rebindConsumer(leafContainer, instanceKey, handlerResetName,
                            leafDomain.registerReset, 'register')


def _rebindConsumer(container, instanceKey, blockPort, newNet, kind):
    for net in container.nets.values():
        net.consumers = [consumer for consumer in net.consumers
                         if not (consumer.instanceKey == instanceKey
                                 and consumer.blockPort == blockPort)]
    container.nets[newNet].consumers.append(Consumer(instanceKey, blockPort, kind))


def _servingRouterBusNets(leafInstanceKey, instances, domains, connections, blocks,
                          consumerNetByContainer):
    """The (consumerNet index, busClockNet, busResetNet, routerBlockKey) for
    the router-to-leaf feed reaching this leaf instance in its own
    container, or None if no router there feeds it.
    """
    instRow = instances[leafInstanceKey]
    consumerNet = consumerNetByContainer[instRow['containerKey']]
    routerInstanceKey = None
    for connRow in connections.values():
        if connRow['dstKey'] != leafInstanceKey:
            continue
        srcInstRow = instances[connRow['srcKey']]
        if domains[srcInstRow['instanceTypeKey']].isRouter:
            routerInstanceKey = connRow['srcKey']
            break
    if routerInstanceKey is None:
        return None

    routerBlockKey = instances[routerInstanceKey]['instanceTypeKey']
    routerClockPort, routerResetPort = _routerBusPorts(routerBlockKey, blocks, domains)
    busClockNet = consumerNet.get((routerInstanceKey, routerClockPort))
    busResetNet = (consumerNet.get((routerInstanceKey, routerResetPort))
                   if routerResetPort else None)
    return consumerNet, busClockNet, busResetNet, routerBlockKey


def _checkRegisterPortsOnBus(leafBlockKey, leafBlock, clockPortName, authoredReset, resetPortName,
                             leafInstanceKeys, instances, domains,
                             connections, blocks, consumerNetByContainer, diag):
    """V8/V25 for a reusable-IP leaf: its own `registerPorts:`-declared (or
    block-default) clock stays authoritative (spec §4.3), but every instance
    of the block must still sit on the router's actual bus clock (a misbound
    instance map is exactly the "register bus is one domain throughout"
    violation V8 exists to catch). The reset is checked the same way only
    when `registerPorts:` authors `reset:` explicitly: spec §4.3 otherwise
    gives a reusable IP's register reset as the selected reset of ITS OWN
    clock (V19) - a candidate among the leaf's own declared resets, not a
    requirement that it be the specific reset the bus's own fallback happens
    to prefer, so a reset the leaf reaches by its own ordinary name match is
    legitimate even where it is not the router's selected one.

    A leaf instance with no router serving its own container is reported
    (V8): config/postParseRegisterPorts.py requires an authored router
    instance in every routed leaf's own direct container, synthesising only
    the dispatch connection between them, so this names a leaf outside this
    build's routed scope.
    """
    for leafInstanceKey in leafInstanceKeys:
        instRow = instances[leafInstanceKey]
        found = _servingRouterBusNets(leafInstanceKey, instances, domains,
                                      connections, blocks, consumerNetByContainer)
        if found is None:
            diag.logError(
                f"Instance '{instRow['instance']}' of block '{leafBlock}' "
                f"needs a register-bus port, but no router serves its own "
                f"container (V8).")
            continue
        consumerNet, busClockNet, busResetNet, _ = found
        if busClockNet is not None and consumerNet.get((leafInstanceKey, clockPortName)) != busClockNet:
            diag.logError(
                f"Instance '{instRow['instance']}' of block '{leafBlock}' "
                f"declares its register port on clock '{clockPortName}', but "
                f"that is not bound to the same container clock as the "
                f"serving router's own bus clock (V8).")
        if authoredReset and busResetNet is not None \
                and consumerNet.get((leafInstanceKey, resetPortName)) != busResetNet:
            diag.logError(
                f"Instance '{instRow['instance']}' of block '{leafBlock}' "
                f"declares its register port's reset as '{resetPortName}' "
                f"(registerPorts: reset:), but that is not bound to the "
                f"same container reset as the serving router's own bus "
                f"reset (V25).")


def _resolveTopDownRegisterPorts(leafBlockKey, leafBlock, leafDomain, leafInstanceKeys,
                                 instances, domains, connections, blocks,
                                 consumerNetByContainer, diag):
    """R25 for a top-down leaf (one that authors no `registerPorts:`): the
    leaf's own declared clock port bound, in its own container, to the same
    net the serving router's own bus clock is bound to; the reset port
    likewise against the bus's selected reset. Every instance of the leaf
    block must agree (V26), and the result is stored on `leafDomain`
    directly (the caller reads it back from there).

    Only the case where the serving router sits in the leaf's own immediate
    container is resolved (the shape of every routed leaf in this tree's
    shipped examples, and the only shape config/postParseRegisterPorts.py
    requires: an authored router instance in the leaf's own direct
    container, with only the dispatch connection between them synthesised).
    A leaf instance with no router serving its own container is reported
    (V8) rather than silently skipped: an outward walk through a NESTED
    router's own container (spec §4.3, "the parent's own synthesised
    register-bus port") is not implemented, so this also covers that shape
    today, as a reported gap rather than a silent one.
    """
    results = list()
    # The port name config/postParseRegisterPorts.py synthesises for THIS
    # BLOCK's own connectionMaps: bridge (its `_routerServingLeaf` resolves
    # once per block, against the first reachable instance it finds) -
    # captured the same way here, from the first instance that resolves.
    registerBusPort = None
    for leafInstanceKey in leafInstanceKeys:
        instRow = instances[leafInstanceKey]
        found = _servingRouterBusNets(leafInstanceKey, instances, domains,
                                      connections, blocks, consumerNetByContainer)
        if found is None:
            diag.logError(
                f"Instance '{instRow['instance']}' of block '{leafBlock}' owns "
                f"firmware-accessible registers or memories, but no router "
                f"serves its own container (V8): a top-down leaf's "
                f"register-bus port is inferred from the router dispatching "
                f"to it directly, and none was found there.")
            continue
        consumerNet, busClockNet, busResetNet, routerBlockKey = found
        if registerBusPort is None:
            registerBusPort = blocks[routerBlockKey]['addressBlock']['registerDecoderPort']

        clockPortName = None
        if busClockNet is not None:
            for name, clockDecl in leafDomain.clocks.items():
                if clockDecl.direction == 'input' and consumerNet.get((leafInstanceKey, name)) == busClockNet:
                    clockPortName = name
                    break
        if clockPortName is None:
            diag.logError(
                f"Instance '{instRow['instance']}' of block '{leafBlock}' owns "
                f"firmware-accessible registers or memories, but none of its "
                f"declared clock ports is bound to the register bus's clock "
                f"(V8). Bind one of '{leafBlock}''s clock ports, in its "
                f"clocks: map, to the same container clock the serving "
                f"router's own bus clock is bound to.")
            continue

        resetPortName = None
        if busResetNet is not None:
            for name, resetDecl in leafDomain.resets.items():
                if (resetDecl.direction == 'input' and not resetDecl.isAsync
                        and consumerNet.get((leafInstanceKey, name)) == busResetNet):
                    resetPortName = name
                    break
        if resetPortName is None:
            diag.logError(
                f"Instance '{instRow['instance']}' of block '{leafBlock}' owns "
                f"firmware-accessible registers or memories, but none of its "
                f"declared reset ports is bound to the register bus's "
                f"selected reset (V25). Bind one of '{leafBlock}''s reset "
                f"ports, in its resets: map, to that same container reset.")
            continue

        results.append((leafInstanceKey, clockPortName, resetPortName))

    if not results:
        return
    pairs = {(clockPortName, resetPortName) for _, clockPortName, resetPortName in results}
    if len(pairs) > 1:
        names = ', '.join(instances[key]['instance'] for key, _, _ in results)
        pairNames = ', '.join(f"{clk}/{rst}" for clk, rst in pairs)
        diag.logError(
            f"Block '{leafBlock}' is generated once, but its instances "
            f"resolve the register port to different clock/reset pairs "
            f"({pairNames}): {names} (V26).")
        return
    leafDomain.registerClock, leafDomain.registerReset = next(iter(pairs))
    leafDomain.registerBusPort = registerBusPort


def _checkMemoryAccessorDomains(domains, instances, memoryConnections, consumerNetByContainer,
                                reachableInstances, diag):
    """V8: every memoryConnections row's accessing side must derive to the
    same container clock as the memory, mapped through the memory's owning
    instance. A plain top-down accessor declares no port for the access (no
    `clock:` to read), so its own domain is its block default clock, mapped
    through its own instance, the same rule an unstated port takes (rule 3).

    An accessor's own container is either of two containers a memory's
    domain is visible in: the owning BLOCK's own body directly (a child
    instance inside the same block that declares the memory, the memDomain
    resolved to a net of the owning block's OWN clock namespace directly),
    or a sibling of one of the owning block's own instances, one level out
    (checked for EVERY reachable instance of the owning block, since a
    memory's domain is a fact of the block, spec §4.3, and a design may
    instantiate the owning block more than once, each on its own container
    clock). Neither is silently skipped: a reachable accessor sharing
    neither container is reported (V8). A memory owner or accessor instance
    outside this build's reachable scope (a block shared with another
    project's own standalone harness) is not checked, the same reachability
    scoping config/postParseRegisterPorts.py's own dispatch uses.
    """
    instancesByBlock = dict()
    for instanceKey, instRow in instances.items():
        if instanceKey in reachableInstances:
            instancesByBlock.setdefault(instRow['instanceTypeKey'], list()).append(instanceKey)
    memConnectionsByMemory = dict()
    for row in memoryConnections.values():
        if row['instanceKey'] in reachableInstances:
            memConnectionsByMemory.setdefault(row['memoryBlockKey'], list()).append(row)

    def checkAccessor(accessorInstanceKey, accessorInstRow, consumerNet, memoryNet, memDomain, domain):
        if memoryNet is None:
            # The owning instance's own clock port bind already failed (V3
            # logged it); comparing an accessor against a net that was
            # never resolved would only add a nonsensical "memory is on
            # 'None'" finding on top of the real one.
            return
        accessorClockName = domains[accessorInstRow['instanceTypeKey']].defaultClock
        if not accessorClockName:
            return
        accessorNet = consumerNet.get((accessorInstanceKey, accessorClockName))
        if accessorNet is not None and accessorNet != memoryNet:
            diag.logError(
                f"Instance '{accessorInstRow['instance']}' accesses memory "
                f"'{memDomain.memory}' of block '{domain.block}' over clock "
                f"'{accessorNet}', but the memory is on '{memoryNet}' (V8). "
                f"A hardware accessor of a memory must be in the memory's "
                f"own domain.")

    for blockKey, domain in domains.items():
        for memDomain in domain.memories:
            if not memDomain.clock:
                continue  # already reported: the owning block has no default clock
            accessorRows = memConnectionsByMemory.get(memDomain.memoryBlockKey, [])
            if not accessorRows:
                continue
            ownerContainerNet = consumerNetByContainer.get(blockKey)
            ownerInstancesByContainer = dict()
            for key in instancesByBlock.get(blockKey, []):
                ownerInstancesByContainer.setdefault(instances[key]['containerKey'], list()).append(key)
            for row in accessorRows:
                accessorInstanceKey = row['instanceKey']
                accessorInstRow = instances[accessorInstanceKey]
                accessorContainerKey = accessorInstRow['containerKey']
                if ownerContainerNet is not None and accessorContainerKey == blockKey:
                    # The accessor is a child instance directly inside the
                    # memory-owning block's own body: memDomain.clock is
                    # already a net name in that body's own namespace.
                    checkAccessor(accessorInstanceKey, accessorInstRow, ownerContainerNet,
                                 memDomain.clock, memDomain, domain)
                    continue
                ownerInstanceKeys = ownerInstancesByContainer.get(accessorContainerKey)
                if ownerInstanceKeys is not None:
                    # The accessor is a sibling of one of the owning block's
                    # own instances, in that instance's own container - every
                    # one of them sharing this container, since the owning
                    # block may be instantiated more than once there, each on
                    # its own container clock.
                    consumerNet = consumerNetByContainer[accessorContainerKey]
                    for ownerInstanceKey in ownerInstanceKeys:
                        memoryNet = consumerNet.get((ownerInstanceKey, memDomain.clock))
                        checkAccessor(accessorInstanceKey, accessorInstRow, consumerNet,
                                     memoryNet, memDomain, domain)
                    continue
                diag.logError(
                    f"Instance '{accessorInstRow['instance']}' accesses memory "
                    f"'{memDomain.memory}' of block '{domain.block}', but it shares "
                    f"neither the owning block's own body nor a container of one of "
                    f"the owning block's own instances, so their container clocks "
                    f"cannot be compared (V8): a hardware accessor of a memory must "
                    f"be a sibling of the memory's owning instance, or a child "
                    f"instance directly inside the memory's own owning block.")


def _checkSupplyGraph(domains, containers, instances, blocks, diag):
    """V20: at every instance of a block, for each output the block itself
    produces (not exported from a child), an edge runs from each of the
    block's own input clocks and resets, asynchronous reset inputs
    included, to that output. The graph is acyclic and rooted: a block
    with no input clock or reset is a root, and every supplied net (one
    whose driver is 'ownImplementation' or 'childOutput') reaches a
    testbench net or a root.

    A container's own declared `input` net is a stopping point here, not
    chased into its own parent: a disconnected chain of declared inputs
    bottoms out at the top block, whose own inputs are bound to the
    testbench (spec §4.8) or rejected there (V3/V10), so this check needs
    only look as far as one container's own edges to catch a cycle or a
    missing root - two siblings clocking each other, or a supplier chain
    bottoming out with no root and no testbench in the same container.
    """
    consumerNetByContainer = {key: _consumerNetIndex(c) for key, c in containers.items()}

    def ownInputNames(blockKey):
        domain = domains[blockKey]
        return ([name for name, clockDecl in domain.clocks.items() if clockDecl.direction == 'input']
               + [name for name, resetDecl in domain.resets.items() if resetDecl.direction == 'input'])

    resolved = dict()
    visiting = list()

    def reaches(containerKey, netName):
        key = (containerKey, netName)
        if key in resolved:
            return resolved[key]
        if key in visiting:
            cycle = visiting[visiting.index(key):] + [key]
            hops = []
            for k, n in cycle:
                driver = containers[k].nets[n].driver
                if driver.kind == 'childOutput':
                    hops.append(f"'{blocks[k]['block']}'.{n} (instance "
                               f"'{instances[driver.instanceKey]['instance']}' "
                               f"output '{driver.blockPort}')")
                else:
                    hops.append(f"'{blocks[k]['block']}'.{n}")
            diag.logError("Supply cycle (V20): " + ' -> '.join(hops))
            return False
        visiting.append(key)
        net = containers[containerKey].nets[netName]
        if net.driver.kind in ('environment', 'input'):
            result = True
        elif net.driver.kind == 'ownImplementation':
            # Declaration order (ownInputNames is a list), and every
            # candidate is visited - never short-circuited by any() - so a
            # cycle behind a LATER candidate is found even when an EARLIER
            # one already reaches a root: reaches() reports a cycle as a
            # side effect the moment it is visited, and skipping a
            # candidate because an earlier one already answered True would
            # make that report depend on iteration order.
            candidates = [name for name in ownInputNames(containerKey)
                         if name in containers[containerKey].nets]
            if not candidates:
                result = True
            else:
                outcomes = [reaches(containerKey, name) for name in candidates]
                result = any(outcomes)
        else:  # 'childOutput'
            supplierInstanceKey = net.driver.instanceKey
            supplierBlockKey = instances[supplierInstanceKey]['instanceTypeKey']
            inputs = ownInputNames(supplierBlockKey)
            if not inputs:
                result = True  # the supplying block is a root (an oscillator)
            else:
                consumerNet = consumerNetByContainer[containerKey]
                # Declaration order, deduplicated (dict.fromkeys keeps first
                # occurrence order; a plain set would iterate in a hash order
                # randomised per process). A candidate that failed to bind
                # (None) is a prior V3 error already reported elsewhere; an
                # ALL-None supply (every one of the supplier's own inputs
                # unbound) skips this check rather than cascading a second,
                # redundant "no path to root" finding on top of that.
                supplyNets = list(dict.fromkeys(
                    consumerNet.get((supplierInstanceKey, name)) for name in inputs))
                supplyNets = [n for n in supplyNets if n is not None]
                if not supplyNets:
                    result = True
                else:
                    outcomes = [reaches(containerKey, n) for n in supplyNets]
                    result = any(outcomes)
        visiting.pop()
        resolved[key] = result
        return result

    for containerKey, container in containers.items():
        for netName, net in container.nets.items():
            if net.driver.kind not in ('ownImplementation', 'childOutput'):
                continue
            if not reaches(containerKey, netName):
                diag.logError(
                    f"Net '{netName}' of '{blocks[containerKey]['block']}' has no "
                    f"path to a root or a testbench net (V20): every supplied net "
                    f"must reach one.")


def _resolveAllInstances(root, containers, domains, instances):
    """The resolved net of every reachable instance's own block clock and
    reset (spec §2 "Resolved clock"): follow bindings upward through INPUT
    ports to a testbench net, stopping at a LOCAL net or a supplier's own
    output without chasing into what drives it (both are themselves the
    resolution, spec §2). A top-down walk from the root, rather than
    chasing each block clock upward one instance at a time: the same block
    may be instantiated more than once, each through a different path, so
    the resolved value is inherently per INSTANCE, not per block, and a
    top-down walk naturally gives every occurrence its own answer without
    tracking which specific parent instance a block was reached through.

    Returns `{instanceKey: {blockPortName: resolvedTuple}}` for every
    instance reachable from `root`, where `resolvedTuple` is one of
    `('testbench', name)`, `('supplied', instanceKey, blockPortName)` (a
    LOCAL net or a supplier's own output, stopping there rather than chasing
    what drives it), or `None` (unbound - an earlier diagnostic, V3, already
    reported this).
    """
    resolvedByInstance = dict()

    def walk(container, ownNetResolved):
        consumerNet = _consumerNetIndex(container)
        for instanceKey, childKey in container.instances.items():
            childDomain = domains[childKey]
            resolvedPorts = dict()
            for name, clockDecl in childDomain.clocks.items():
                if clockDecl.direction == 'input':
                    netName = consumerNet.get((instanceKey, name))
                    resolvedPorts[name] = ownNetResolved.get(netName) if netName else None
                else:
                    resolvedPorts[name] = ('supplied', instanceKey, name)
            for name, resetDecl in childDomain.resets.items():
                if resetDecl.direction == 'input':
                    netName = consumerNet.get((instanceKey, name))
                    resolvedPorts[name] = ownNetResolved.get(netName) if netName else None
                else:
                    resolvedPorts[name] = ('supplied', instanceKey, name)
            resolvedByInstance[instanceKey] = resolvedPorts

            childContainer = containers.get(childKey)
            if childContainer is None:
                continue
            # The resolved value of every net INSIDE childContainer, handed
            # down one level further: a declared INPUT net's own resolution
            # is exactly the resolution just computed for the block clock of
            # the same name (a container's declared clocks/resets ARE its
            # own block's clocks/resets); a LOCAL net or a declared OUTPUT a
            # child drives is itself a 'supplied' stop, at the driving
            # grandchild's own instance and port, never chased further (spec
            # §2 "stopping at ... a local net"); a declared OUTPUT the
            # container's OWN implementation drives (no child does) is a
            # 'supplied' stop at this instance itself, the same as an
            # oscillator's own output.
            childNetResolved = dict()
            for netName, net in childContainer.nets.items():
                if net.kind == 'declared' and net.driver.kind == 'input':
                    childNetResolved[netName] = resolvedPorts.get(netName)
                elif net.driver.kind == 'childOutput':
                    childNetResolved[netName] = ('supplied', net.driver.instanceKey, net.driver.blockPort)
                elif net.driver.kind == 'ownImplementation':
                    childNetResolved[netName] = ('supplied', instanceKey, netName)
                # 'environment' never occurs below root.
            walk(childContainer, childNetResolved)

    rootResolved = {name: ('testbench', name) for name in root.nets}
    walk(root, rootResolved)
    return resolvedByInstance


def _resolveStandaloneAttrs(domains, blocks, instances, resolvedByInstance,
                            testbenchClocks, testbenchResets,
                            contextOwningProject, rootProjectName, diag):
    """Standalone simulation attributes for a `hasVl` block (spec §4.8, R24):
    each INPUT clock's period/timeUnit from its own declaration, else from
    the testbench clock every instance of the block, in the project that
    declares it, resolves to uniquely (V21); each INPUT reset's
    releaseCycles the same way. A clock or reset with neither a declared
    value nor a uniquely resolvable testbench one falls back to the
    project's own default testbench clock/reset row (`_defaultTestbenchClock`/
    `_defaultTestbenchReset` below) - the project's schema-applied defaults,
    not a literal here.
    An asynchronous reset input counts its releaseCycles on the block
    default clock, which must itself be an input clock (V21). Evaluated only
    in the block's own declaring project (`contextOwningProject`), never
    re-evaluated by an assembler: a block instantiated by another project
    keeps whatever its own declaring project's build already resolved.

    A block that never declares `hasVl` has these fields filled in too (the
    generic `getBDClocksResets` view returns them for every block), but
    unresolvable attributes are never reported for it: nothing downstream
    reads them for such a block, so V21's diagnostic is scoped to `hasVl`.
    """
    instanceKeysByBlock = dict()
    for instanceKey, instRow in instances.items():
        if instanceKey in resolvedByInstance:
            instanceKeysByBlock.setdefault(instRow['instanceTypeKey'], list()).append(instanceKey)

    # The project's own default clock/reset: a schema-applied row (its
    # period/timeUnit/releaseCycles already carry the schema's own default,
    # config/schema.yaml's clocks:/resets: `optional(...)` fields), reused as
    # the fallback for a clock/reset that fails to resolve at all, rather
    # than a bare literal duplicating that default. Guaranteed to exist:
    # V23 requires exactly one default clock and reset in every project.
    _defaultTestbenchClock = next(row for row in testbenchClocks.values() if row['default'])
    _defaultTestbenchReset = next(row for row in testbenchResets.values() if row['default'])

    def instanceResolutions(blockKey, portName, evaluate):
        """Per-instance resolved value for blockKey's own portName: a list
        of (instanceKey, resolved) pairs, empty when evaluate is False or
        the block has no instance in this build. `resolved` is whatever
        _resolveAllInstances recorded for that instance's own port: None
        (unbound - a V3 error already reported elsewhere), or a
        ('testbench'|'local'|'supplied', ...) tuple.
        """
        if not evaluate:
            return []
        return [(instanceKey, resolvedByInstance[instanceKey].get(portName))
                for instanceKey in instanceKeysByBlock.get(blockKey, [])]

    def testbenchNetOf(resolutions):
        """The one testbench net every entry of `resolutions` resolves to,
        or None (no instance, a resolution that is not a testbench net, or a
        disagreement)."""
        if not resolutions:
            return None
        nets = set()
        for _, resolved in resolutions:
            if resolved is None or resolved[0] != 'testbench':
                return None
            nets.add(resolved[1])
        return next(iter(nets)) if len(nets) == 1 else None

    def v21Cause(resolutions):
        """The spec V21 cause clause for a clock/reset that fails to
        resolve, one of the three the spec names: no instance in the
        declaring project, a resolution to a supplier's output, or
        disagreeing instances - each its own sentence, naming the
        instances (spec V21: "an error naming the instances that
        disagree")."""
        if not resolutions:
            return "it has no instance in its own declaring project."
        supplierNames = [instances[k]['instance'] for k, r in resolutions
                         if r is not None and r[0] == 'supplied']
        if supplierNames:
            return (f"instance(s) {', '.join(supplierNames)} resolve it to a "
                    f"supplier's output, not a testbench net.")
        pairs = ', '.join(
            f"{instances[k]['instance']}={r[1] if r is not None else '<unresolved>'}"
            for k, r in resolutions)
        return f"its instances disagree: {pairs}."

    for blockKey, domain in domains.items():
        blockRow = blocks[blockKey]
        evaluate = contextOwningProject[blockRow['_context']] == rootProjectName
        # V21 is scoped to the block's own declaring project: an assembler
        # never re-evaluates it, so a hasVl block this build only INSTANTIATES
        # (evaluate is False) reports nothing here, even when its own
        # declaring project's build would find a genuine violation.
        reportV21 = bool(blockRow['hasVl']) and evaluate

        for name, clockDecl in domain.clocks.items():
            if clockDecl.direction != 'input':
                continue
            if clockDecl.period:
                domain.resolvedPeriod[name] = clockDecl.period
                domain.resolvedTimeUnit[name] = clockDecl.timeUnit
                continue
            resolutions = instanceResolutions(blockKey, name, evaluate)
            testbenchNet = testbenchNetOf(resolutions)
            if testbenchNet is not None:
                domain.resolvedPeriod[name] = testbenchClocks[testbenchNet]['period']
                domain.resolvedTimeUnit[name] = testbenchClocks[testbenchNet]['timeUnit']
                continue
            if reportV21:
                diag.logError(
                    f"Block '{domain.block}' clock '{name}' declares no period: "
                    f"and does not resolve to one testbench clock through every "
                    f"instance of the block in its own declaring project (V21): "
                    f"{v21Cause(resolutions)} Declare period: on '{name}', or "
                    f"make every instance's binding resolve to the same "
                    f"testbench clock.")
            domain.resolvedPeriod[name] = _defaultTestbenchClock['period']
            domain.resolvedTimeUnit[name] = _defaultTestbenchClock['timeUnit']

        for name, resetDecl in domain.resets.items():
            if resetDecl.direction != 'input':
                continue
            if resetDecl.isAsync:
                # Spec §4.8: an asynchronous reset input counts its release
                # cycles on the block DEFAULT clock's edges (it belongs to no
                # clock of its own), which must itself be an input clock
                # (V21). The release COUNT still follows the reset's own
                # binding, the same rule as any other reset: it is bound to
                # some net (by map or name match) independently of clock
                # membership, and that binding is what resolvedByInstance
                # already computed for it above.
                defaultClock = domain.defaultClock
                defaultIsInput = (defaultClock is not None
                                 and domain.clocks[defaultClock].direction == 'input')
                if not defaultIsInput and reportV21:
                    diag.logError(
                        f"Block '{domain.block}' asynchronous reset input "
                        f"'{name}' counts its release cycles on the block "
                        f"default clock, but '{domain.block}' has no default "
                        f"clock that is an input (V21).")
            elif domain.clocks[resetDecl.clock].direction != 'input' and reportV21:
                # V9, generalised to a standalone block (spec §4.8): a
                # non-async input reset belongs to an input clock. A reset on
                # an OUTPUT clock is observed, not driven, by the standalone
                # wrapper, so it may not run until its own release - the
                # wrapper's reset_driver would wait on an edge that need not
                # come.
                diag.logError(
                    f"Block '{domain.block}' reset '{name}' belongs to clock "
                    f"'{resetDecl.clock}', which is an output of '{domain.block}', "
                    f"not an input (V9): a standalone build cannot count "
                    f"release cycles on an observed output clock, which may "
                    f"not run before its own release.")
            resolutions = instanceResolutions(blockKey, name, evaluate)
            testbenchNet = testbenchNetOf(resolutions)
            if testbenchNet is not None:
                domain.resolvedReleaseCycles[name] = testbenchResets[testbenchNet]['releaseCycles']
                continue
            # An async reset's own clock is '' (V1: it belongs to no clock);
            # the "declares period" fallback it shares with an ordinary
            # reset applies to the clock it is actually counted on instead -
            # the block default clock (already checked above).
            ownClock = domain.defaultClock if resetDecl.isAsync else resetDecl.clock
            ownClockDeclaresPeriod = (ownClock is not None
                                     and bool(domain.clocks[ownClock].period))
            if not ownClockDeclaresPeriod and reportV21:
                diag.logError(
                    f"Block '{domain.block}' reset '{name}' does not resolve to "
                    f"one testbench reset through every instance of the block "
                    f"in its own declaring project, and its own clock declares "
                    f"no period: (V21): {v21Cause(resolutions)} Declare period: "
                    f"on that clock, or make every instance's binding resolve "
                    f"to the same testbench reset.")
            domain.resolvedReleaseCycles[name] = _defaultTestbenchReset['releaseCycles']
