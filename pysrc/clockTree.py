"""In-memory clock/reset container model.

Built once during projectCreate and not persisted itself: `rows()` yields the
tuples of the `blockClocksResets`, `instanceClockResetBinds`, `memoryClocks`,
`portDomains` and `containerLocalNets` tables, in their column order. `rows()`
and `check()` read only the graph (`BlockDomains`, `Container`, `Net`,
`Consumer`), never the flatData `build()` was given. processYaml imports this
module, never the reverse.
"""

from collections import OrderedDict
from dataclasses import dataclass


@dataclass
class ClockDecl:
    """One block clock, as declared or implied."""
    desc: str
    direction: str
    default: bool
    period: object
    timeUnit: str


@dataclass
class ResetDecl:
    """One block reset, as declared or implied. `isAsync` is the YAML field
    `async`, a Python keyword. `clockStated` is whether the declaration
    authors clock:, since `clock` is filled in with the default when unstated.
    """
    desc: str
    direction: str
    default: bool
    clock: str
    isAsync: bool
    clockStated: bool


@dataclass
class MemoryDomain:
    """One memory a block owns. `clock`/`reset` are the declaration's own, else
    the owning block's default clock and that clock's selected reset.
    `regAccess` marks a memory the block's register handler serves; one on a
    clock other than the bus clock is served through the handler's bridge,
    which needs a reset in the memory's own clock domain.
    """
    memoryBlockKey: str
    memory: str
    clock: str
    reset: str
    regAccess: bool


@dataclass
class Driver:
    """The single source of a net inside a container. `kind` is 'input' (the
    container's own input port), 'childOutput' (a child's output, named by
    `instanceKey`/`blockPort`), 'ownImplementation' (a declared output no child
    drives) or 'environment' (the testbench).
    """
    kind: str
    instanceKey: object = None
    blockPort: object = None


@dataclass
class Consumer:
    """A child instance's block clock or reset bound onto a net. `binding` is
    'map', 'name' (a container net of the same name), 'fallback' (clk to the
    container's default clock, rst_n to that clock's selected reset) or
    'register' (a synthesised `<block>_regs` handler's port, bound to its leaf's
    register clock/reset or to a bridged memory's clock/reset).
    """
    instanceKey: str
    blockPort: str
    binding: str


class Net:
    """One clock or reset net inside a container. `kind` is 'declared',
    'local' or 'testbench'. `clockNet` is the clock net a reset belongs to; None
    for a clock or an asynchronous reset.
    """

    def __init__(self, name, kind, isReset, clockNet, driver):
        self.name = name
        self.kind = kind
        self.isReset = isReset
        self.clockNet = clockNet
        self.driver = driver
        self.consumers = []


class Container:
    """A block that instantiates others, or the testbench root
    (`ClockTree.ROOT_KEY`). `instances` maps each child instanceKey to its
    blockKey. `unconnectedOutputs` holds the (instanceKey, blockPort) of each
    output bound to `~`, so its bind row is still written, unconnected, rather
    than the port being omitted.
    """

    def __init__(self, blockKey):
        self.blockKey = blockKey
        self.nets = OrderedDict()
        self.instances = OrderedDict()
        self.unconnectedOutputs = set()


class BlockDomains:
    """One block's declared clocks and resets, in declaration order,
    independent of its children, connections and containment.

    `selectedReset` is per clock; for a container it is recomputed once its
    local reset nets are known. `registerClock`/`registerReset` are where the
    register bus lands: for a router or handler, the container net its bus port
    binds to; for a served leaf or passthrough container, its own port names.
    They are filled in by the register-bus resolution passes and stay None on
    other blocks.
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
        # they fire), whose names must be pairwise distinct. A container's
        # local net names only exist once an output binding in
        # ClockTree.build() creates them, so build() checks them against
        # this same map.
        self.names = names
        self.registerClock = None
        self.registerReset = None
        # The router's or handler's OWN declared clock/reset PORT NAME
        # carrying the register bus: `_routerBusPorts` for a router, the
        # leaf's registerClock/registerReset names for a handler once
        # `_resolveRegisterHandlerBinds` renames its pair onto them. Unlike
        # registerClock/registerReset this is always a port of THIS block,
        # never a container net, so it is what the router's own flops name.
        # None on a block that is neither a router nor a handler.
        self.busClockPort = None
        self.busResetPort = None
        # A served leaf's or passthrough container's own port carrying the
        # register bus: the `registerPorts:` key, or the port
        # postParseRegisterPorts synthesises for a top-down leaf or
        # passthrough container. It is also a synthesised connectionMaps
        # boundary port, so the co-simulation wrapper reset check skips it
        # by name and leaves it to the register-bus reset check. None for
        # other blocks.
        self.registerBusPort = None
        # Standalone simulation attributes: per INPUT
        # clock, the period/timeUnit a standalone (`hasVl`) build of this
        # block generates it at; per INPUT reset, the releaseCycles it is
        # held asserted for. Filled in by `_resolveStandaloneAttrs`, after
        # every instance's bindings are resolved, from the clock/reset's own
        # declared value when present, else the testbench clock/reset it
        # resolves to uniquely across every instance of the block in its own
        # declaring project. A block that is never a standalone target keeps
        # these empty; a clock/reset with neither a declared value nor a
        # resolvable one is filled with the schema default; for a `hasVl`
        # block the missing-period error has already been reported.
        self.resolvedPeriod = dict()
        self.resolvedTimeUnit = dict()
        self.resolvedReleaseCycles = dict()

    @classmethod
    def build(cls, blockKey, blockRow, memories, resetsDeclaredEmpty, diag):
        """Materialise one block's clocks:/resets: and check the block-level
        declaration rules: default-clock marking, one default reset per clock,
        async resets, name uniqueness, explicit clocks on a block with no default
        clock, that an input reset belongs to an input clock, and that a router's
        addressBlock: clock: and reset: are inputs, the reset synchronous. That a
        stated clock:/reset: names one of the block's own is checked at parse time
        by the schema's blockClock/blockReset foreign keys.
        """
        block = blockRow['block']

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

        # default: and period: describe a clock the block consumes, so
        # neither may appear on an output clock.
        for name in outputClocks:
            if clocks[name]['default']:
                diag.logError(
                    f"Block '{block}' output clock '{name}' declares "
                    f"default: true; default: marks the block's default "
                    f"input clock and does not apply to an output. Remove "
                    f"default: from '{name}'. {_diagLoc(diag, clocks[name])}")
            if clocks[name]['period']:
                diag.logError(
                    f"Block '{block}' output clock '{name}' declares "
                    f"period:; period: is the standalone simulation rate of "
                    f"an input clock and does not apply to an output, which "
                    f"the block itself produces. Remove period: from "
                    f"'{name}'. {_diagLoc(diag, clocks[name])}")

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
                    f"them default: true. A block with more than one input "
                    f"clock must mark exactly one default: true, because an "
                    f"unstated port, reset or fallback binding takes the "
                    f"default clock and declaration order does not choose "
                    f"it. Mark exactly one input clock default: true. "
                    f"{_diagLoc(diag, blockRow)}")
            defaultClock = marked[0]
        # Normalise: the default clock's own row always reads default:
        # true, whether the block marked it (required with several input
        # clocks) or it is simply the block's only one.
        # getBDPortDomain and the alias helper both key off this field.
        if defaultClock is not None:
            clocks[defaultClock]['default'] = True

        # A declared port's (ports:, registerPorts:, addressBlock:)
        # unstated clock: means the block default clock, which a block with
        # no default clock (every declared clock direction: output) does not
        # have, so such a block must name every port's clock explicitly.
        def checkPortClock(label, name, row):
            if not row['clock'] and defaultClock is None:
                diag.logError(
                    f"Block '{block}' has no default clock (every declared "
                    f"clock is direction: output) "
                    f"and {label} '{name}' names no clock:; a block with no "
                    f"default clock must name every port's clock. Add "
                    f"clock: to '{name}', or give the block one default "
                    f"input clock. {_diagLoc(diag, row)}")

        for portName, portRow in (blockRow.get('ports') or {}).items():
            checkPortClock('ports', portName, portRow)
        for portName, portRow in (blockRow.get('registerPorts') or {}).items():
            checkPortClock('registerPorts', portName, portRow)
        addressBlockRow = blockRow.get('addressBlock')
        isRouter = bool(addressBlockRow)
        if addressBlockRow:
            checkPortClock('addressBlock', 'addressBlock', addressBlockRow)
            busClock = addressBlockRow['clock']
            if busClock and clocks[busClock]['direction'] == 'output':
                diag.logError(
                    f"Block '{block}' addressBlock: names clock: "
                    f"'{busClock}', an output clock of '{block}'. A router "
                    f"is clocked by the register bus it routes, so its clock "
                    f"must be direction: input. Make '{busClock}' an input "
                    f"clock of '{block}', and its only clock. "
                    f"{_diagLoc(diag, addressBlockRow)}")
            busReset = addressBlockRow['reset']
            if busReset and blockRow['resets'][busReset]['direction'] == 'output':
                diag.logError(
                    f"Block '{block}' addressBlock: names reset: "
                    f"'{busReset}', an output reset of '{block}'. A router "
                    f"is reset by the register bus it routes, so its reset "
                    f"must be direction: input. Make '{busReset}' an input "
                    f"reset of '{block}', or name an input reset in "
                    f"addressBlock: reset:. {_diagLoc(diag, addressBlockRow)}")
            elif busReset and blockRow['resets'][busReset]['async']:
                # The router and the leaves it serves release the bus reset
                # synchronously on the bus clock; an asynchronous reset
                # belongs to no clock.
                busClockName = busClock or defaultClock
                diag.logError(
                    f"Block '{block}' addressBlock: names reset: "
                    f"'{busReset}', an asynchronous reset input belonging "
                    f"to no clock. A router's bus reset must belong to its "
                    f"bus clock '{busClockName}', on which the router and "
                    f"the leaves it serves release it. Name a reset of "
                    f"'{busClockName}' in addressBlock: reset:, or remove "
                    f"reset: to use that clock's selected reset. "
                    f"{_diagLoc(diag, addressBlockRow)}")
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

        # Read before the loop below fills in each unstated clock:.
        clockStated = {name for name, row in (declaredResets or {}).items() if row['clock']}
        for resetName, resetRow in resets.items():
            if resetRow['async']:
                if resetRow['direction'] != 'input':
                    diag.logError(
                        f"Block '{block}' reset '{resetName}' declares async: "
                        f"true with direction: '{resetRow['direction']}'; only "
                        f"an input reset may be asynchronous. Make "
                        f"'{resetName}' an input or remove async: true. "
                        f"{_diagLoc(diag, resetRow)}")
                if resetRow['clock']:
                    diag.logError(
                        f"Block '{block}' reset '{resetName}' declares both "
                        f"async: true and clock: '{resetRow['clock']}'; an "
                        f"asynchronous reset input belongs to no clock and may "
                        f"not name one. Remove the clock: field or async: "
                        f"true. {_diagLoc(diag, resetRow)}")
                resetRow['clock'] = ''
                continue
            statedClock = resetRow['clock']
            clockName = statedClock or defaultClock
            if not clockName:
                diag.logError(
                    f"Block '{block}' reset '{resetName}' names no clock: and "
                    f"the block has no default clock; a block with no "
                    f"default clock must name every reset's clock. Add "
                    f"clock: to '{resetName}'. {_diagLoc(diag, resetRow)}")
                continue
            if resetRow['direction'] == 'input' and clocks[clockName]['direction'] != 'input':
                diag.logError(
                    f"Block '{block}' input reset '{resetName}' names clock "
                    f"'{clockName}', an output clock of '{block}'; an input "
                    f"reset must belong to an input clock. Name an input "
                    f"clock in its clock:, or mark it async: true if no clock "
                    f"of '{block}' samples it. {_diagLoc(diag, resetRow)}")
            resetRow['clock'] = clockName

        # The selected reset of each clock, chosen among the block's own
        # declared resets. A container's local reset nets are not yet part
        # of the candidate set.
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
                    f"most one reset per clock may be the default. Keep "
                    f"default: true on only one of them. {_diagLoc(diag, blockRow)}")
            if marked:
                selected[clockName] = marked[0]
            elif len(names) == 1:
                selected[clockName] = names[0]
            elif clockName == defaultClock:
                diag.logError(
                    f"Block '{block}' default clock '{clockName}' has "
                    f"{len(names)} declared resets ({', '.join(names)}) and "
                    f"none is marked default: true; a block with several "
                    f"resets on its default clock must mark exactly one. "
                    f"Mark one of them default: true. {_diagLoc(diag, blockRow)}")
            else:
                selected[clockName] = None

        # Clocks, resets, interface ports, memories and, when the block
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
        # default clock at all) gets no rst_n alias. A container whose local
        # reset net later becomes that selected reset reserves rst_n then,
        # in build().
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
                f"distinct within a block. Rename one of them. "
                f"{_diagLoc(diag, blockRow)}")

        # A memory's clock defaults to the owning block's default clock, and
        # its reset to that clock's selected reset. The reset clears the
        # memory side of the register handler's bridge, so an authored
        # reset: must belong to the memory's own clock, as a
        # registerPorts:/addressBlock: reset: override must.
        for memDomain in memories:
            memDomain.clock = memDomain.clock or defaultClock
            if memDomain.reset:
                resetClock = resets[memDomain.reset]['clock']
                if not resetClock:
                    diag.logError(
                        f"Memory '{memDomain.memory}' of block '{block}' "
                        f"names reset: '{memDomain.reset}', an asynchronous "
                        f"reset input belonging to no clock. A memory's "
                        f"reset: must name a reset belonging to the memory's "
                        f"own clock '{memDomain.clock}'. Name a reset of "
                        f"'{memDomain.clock}', or remove reset:.")
                elif resetClock != memDomain.clock:
                    diag.logError(
                        f"Memory '{memDomain.memory}' of block '{block}' "
                        f"names reset: '{memDomain.reset}', which belongs "
                        f"to clock '{resetClock}', not the memory's own "
                        f"clock '{memDomain.clock}'. A memory's reset: must "
                        f"belong to the memory's own clock. Name a reset of "
                        f"'{memDomain.clock}', or remove reset: to use that "
                        f"clock's selected reset.")
            memDomain.reset = memDomain.reset or selected.get(memDomain.clock)

        clockDecls = OrderedDict(
            (name, ClockDecl(desc=row['desc'], direction=row['direction'],
                             default=bool(row['default']), period=row['period'],
                             timeUnit=row['timeUnit']))
            for name, row in clocks.items())
        resetDecls = OrderedDict(
            (name, ResetDecl(desc=row['desc'], direction=row['direction'],
                             default=bool(row['default']), clock=row['clock'],
                             isAsync=bool(row['async']), clockStated=name in clockStated))
            for name, row in resets.items())
        return cls(blockKey, block, clockDecls, resetDecls, defaultClock, selected,
                  isRouter, isRegHandler, memories, names)


class ClockTree:
    """The project's clock/reset containers: `blocks` (every BlockDomains, by
    blockKey), `containers` (every block with a child) and `root` (the
    testbench, not in `containers`).
    """

    ROOT_KEY = '_topInstance'

    def __init__(self, blocks, containers, root, diag, portDomainRows):
        self.blocks = blocks
        self.containers = containers
        self.root = root
        self._diag = diag
        # Each connectionMaps: row's boundary port's derived domain,
        # computed once from the inside-out net lookup rather than
        # re-derived by the projectOpen view. (outerBlockKey,
        # boundaryPortName, domainClock) tuples, ready for
        # projectCreate._persistClockTree() to insert unchanged.
        self.portDomainRows = portDomainRows

    def check(self):
        """Invariants that need every block's domains built, checked once
        build() has run so that they do not pre-empt its diagnostics.
        """
        for domain in self.blocks.values():
            if domain.defaultClock is not None:
                continue
            for memDomain in domain.memories:
                if memDomain.clock:
                    continue
                self._diag.logError(
                    f"Memory '{memDomain.memory}' of block '{domain.block}' "
                    f"has no clock: its owning block has no default clock "
                    f"(every declared clock is direction: output). A memory "
                    f"defaults to the owning block's "
                    f"default clock. Give the owning block one default input "
                    f"clock, or name the memory's clock:.")

    def rows(self):
        """The five persisted tables' rows, in their existing column order:
        blockClocksResets, instanceClockResetBinds, memoryClocks, portDomains,
        containerLocalNets.
        """
        blockClocksResetsRows = list()
        memoryClocksRows = list()
        for blockKey, domain in self.blocks.items():
            # registerClock/registerReset/registerBusPort and
            # busClockPort/busResetPort are block-level facts, repeated onto
            # every row of the block so getBDClocksResets reads them off any
            # one row with no second table. period/timeUnit hold the RESOLVED
            # standalone-simulation value for an input clock: the declared
            # value when present, else the one resolved from the testbench
            # clock every instance of the block resolves to. An output clock
            # keeps its declared value, which is always empty. releaseCycles
            # is the same resolution for a reset; None on a clock row.
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
        for container in (self.root, *self.containers.values()):
            consumerNet = _consumerNetIndex(container)
            # A `~`-bound output has no entry in driverNet (build() never
            # creates a net for one); its bind row instead comes from
            # `container.unconnectedOutputs` below, with an empty signal, so
            # the instantiation writes it explicitly unconnected rather than
            # omitting it.
            driverNet = _driverNetIndex(container)
            for instanceKey, childKey in container.instances.items():
                child = self.blocks[childKey]
                binds = list()
                # Every child, a router or handler included, is bound by its
                # own declared clock/reset port names.
                for name, clockDecl in child.clocks.items():
                    net = (consumerNet if clockDecl.direction == 'input' else driverNet).get((instanceKey, name))
                    if net is not None:
                        binds.append((name, net))
                    elif (instanceKey, name) in container.unconnectedOutputs:
                        binds.append((name, ''))
                for name, resetDecl in child.resets.items():
                    net = (consumerNet if resetDecl.direction == 'input' else driverNet).get((instanceKey, name))
                    if net is not None:
                        binds.append((name, net))
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


def build(blocks, instances, connections, memories, memoryConnections,
          registerConnections, connectionMaps, registerBusPassthroughs,
          blocksDeclaringNoResets,
          testbenchClocks, testbenchResets, contextOwningProject, rootProjectName, diag):
    """Build the project's ClockTree from parsed flatData tables.

    `registerBusPassthroughs` is the `REGAPB_PASSTHROUGH` blob from
    config/postParseRegisterPorts.py, keyed by passthrough container blockKey.
    `blocksDeclaringNoResets` is a parser-recorded fact from projectCreate.
    `testbenchClocks`/`testbenchResets` are the root project's own entries and
    become the root container's nets.
    `contextOwningProject` and `rootProjectName` limit standalone-attribute
    resolution to each block's declaring project. `diag` provides
    `logError(msg)` and `diagnosticLocation(yamlFile, lc)`. No argument is kept
    on the result.
    """
    memoriesByBlock = dict()
    for memoryBlockKey, memRow in memories.items():
        memoriesByBlock.setdefault(memRow['blockKey'], list()).append(
            MemoryDomain(memoryBlockKey, memRow['memory'], memRow['clock'],
                        memRow['reset'], memRow['regAccess']))

    # A router's module is generated whole from its addressBlock:, so it
    # cannot contain instances; reported before any router clock/reset check.
    routerChildren = dict()
    for instRow in instances.values():
        containerKey = instRow['containerKey']
        if instRow['container'] != ClockTree.ROOT_KEY and blocks[containerKey].get('addressBlock'):
            routerChildren.setdefault(containerKey, list()).append(instRow['instance'])
    for routerKey, childNames in routerChildren.items():
        routerRow = blocks[routerKey]
        names = ', '.join(f"'{name}'" for name in childNames)
        diag.logError(
            f"Register-decode router block '{routerRow['block']}' contains "
            f"instance(s) {names}. A router's module is generated entirely "
            f"from its addressBlock:, so it cannot contain instances. Move "
            f"{names} into the container that instantiates "
            f"'{routerRow['block']}'. {_diagLoc(diag, routerRow)}")

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

    def rejectSelfDrivenInput(container, instanceKey, net, ownName, netKind):
        # An input, by map, name match or fallback, may not land on a net one
        # of the same instance's outputs drives.
        netObj = container.nets[net]
        if netObj.driver.kind == 'childOutput' and netObj.driver.instanceKey == instanceKey:
            instRow = instances[instanceKey]
            diag.logError(
                f"Instance '{instRow['instance']}' of block "
                f"'{blocks[instRow['instanceTypeKey']]['block']}' "
                f"binds its own {netKind} '{ownName}' to '{net}', which its "
                f"own {netKind} '{netObj.driver.blockPort}' already drives. "
                f"An instance may not bind one of its own inputs to a net one "
                f"of its own outputs supplies. Bind '{ownName}' to a net "
                f"another source drives.")
            return True
        return False

    # Output binding: every output block clock/reset needs a map entry,
    # bound to a container's declared output (the export), a new local net
    # name, or `~` to leave it unconnected. This runs for every instance of
    # every container before the input pass below, because a local net is
    # created by being driven and an input consumer (map, name match or
    # fallback) must find it already in `container.nets`.
    for instanceKey, instRow in instances.items():
        if instRow['container'] == ClockTree.ROOT_KEY:
            # The top block's own outputs are observed by the testbench,
            # not bound to a container net.
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
        # at all is the ordinary case (automatic binding), not a
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
                    f"to a container net, a new local net name, or `~`. Add "
                    f"'{name}' to the instance's {netKind}s: map.")
                return
            net = mapRow['bind']
            if not net:
                # `~`: no net is created, but the instantiation still writes
                # the port explicitly unconnected (rows() reads this set)
                # rather than omitting it the way an ordinary unmapped port
                # would be.
                container.unconnectedOutputs.add((instanceKey, name))
                return
            existing = container.nets.get(net)
            if existing is None:
                # A genuinely new local net name: it cannot collide with one
                # of the container's own declared clocks/resets (those are
                # already in container.nets, so `existing` would not be
                # None), but it can still collide with one of the
                # container's own interface ports, registerPorts, memories,
                # or the reserved clk/rst_n aliases, all in the `names` map
                # BlockDomains.build() collected for this block.
                collidingKind = domains[containerKey].names.get(net)
                if collidingKind is not None:
                    diag.logError(
                        f"Instance '{instRow['instance']}' of block "
                        f"'{childBlock}' binds output {netKind} '{name}' to "
                        f"'{net}', but '{containerBlock}' already uses that "
                        f"name for its {collidingKind}; a local net's name may "
                        f"not collide with the container's own clocks, "
                        f"resets, interface ports, memories, or the "
                        f"reserved names clk/rst_n. Choose another local net "
                        f"name.")
                    return
                # A local reset net's own clock membership is
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
                    f"net of '{containerBlock}', not a {netKind} net. An "
                    f"output {netKind} must drive a {netKind} net. Map "
                    f"'{name}' to a {netKind} net, a new local net name, or "
                    f"`~`.")
                return
            if existing.driver is not None and existing.driver.kind == 'input':
                diag.logError(
                    f"Instance '{instRow['instance']}' of block "
                    f"'{childBlock}' binds output {netKind} '{name}' to "
                    f"'{net}', an INPUT of '{containerBlock}' already "
                    f"driven by its own parent. A net may have only one "
                    f"driver. Map '{name}' to a declared output, a new local "
                    f"net name, or `~`.")
                return
            if existing.driver is not None:
                diag.logError(
                    f"Container '{containerBlock}' net '{net}' has more "
                    f"than one driver: instance '{instRow['instance']}''s "
                    f"output {netKind} '{name}' and an earlier one. A net may "
                    f"have only one driver. Map one of the outputs to a "
                    f"different net or to `~`.")
                return
            existing.driver = Driver('childOutput', instanceKey, name)

        for name, clockDecl in childDomain.clocks.items():
            if clockDecl.direction == 'output':
                bindOutput(name, clockMap, 'clock')
        for name, resetDecl in childDomain.resets.items():
            if resetDecl.direction == 'output':
                bindOutput(name, resetMap, 'reset')

    # A declared output no child
    # instance's own binding drove above is produced by the container's own
    # implementation instead - the only other source such a net can have.
    for container in containers.values():
        for net in container.nets.values():
            if net.kind == 'declared' and net.driver is None:
                net.driver = Driver('ownImplementation')

    # Input binding, in precedence order: an instance's own
    # clocks:/resets: map entry, else name match for an input, else the
    # default-clock/selected-reset fallback for a block clock or reset named
    # literally clk/rst_n. A map value is a container-declared net or a
    # local net the output pass above already created; `~` is never valid
    # for an input (only an output may be left unconnected).
    # (instanceKey, resetName, containerKey, boundClockNet) for an rst_n
    # fallback onto a LOCAL clock net: its own selected reset may be a local
    # reset net, not resolvable until every local net's own
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
                    f"clocks ({', '.join(childDomain.clocks)}). Remove "
                    f"'{mapKey}' from the instance's clocks: map. {_diagLoc(diag, mapRow)}")
        for mapKey, mapRow in resetMap.items():
            if mapKey not in childDomain.resets:
                diag.logError(
                    f"Instance '{instRow['instance']}' maps reset '{mapKey}', "
                    f"which is not one of block '{childBlock}''s own declared "
                    f"resets ({', '.join(childDomain.resets)}). Remove "
                    f"'{mapKey}' from the instance's resets: map. {_diagLoc(diag, mapRow)}")

        def localNetNames(netKind):
            return ', '.join(f"'{name}'" for name, localNet in container.nets.items()
                             if localNet.kind == 'local' and localNet.isReset == (netKind == 'reset'))

        def isContainerNet(name, netKind):
            # A container clock or reset: declared, or a local net.
            netObj = container.nets.get(name)
            return netObj is not None and netObj.isReset == (netKind == 'reset')

        def resolveMappedNet(mapRow, netKind):
            net = mapRow['bind']
            if not net:
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' "
                    f"maps '{mapRow[netKind]}' to `~`; an input {netKind} "
                    f"needs an actual net to consume, declared or local; "
                    f"`~` only leaves an OUTPUT unconnected. Map "
                    f"'{mapRow[netKind]}' to a {netKind} of the container. "
                    f"{_diagLoc(diag, mapRow)}")
                return None
            if not isContainerNet(net, netKind):
                declared = ', '.join(f"'{name}'" for name in
                                     (containerDomain.resets if netKind == 'reset'
                                      else containerDomain.clocks))
                local = localNetNames(netKind)
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' "
                    f"in container '{containerBlock}' maps {netKind} "
                    f"'{mapRow[netKind]}' to '{net}', which is not one of "
                    f"'{containerBlock}''s declared {netKind}s ({declared}) "
                    f"or its local {netKind} nets ({local or 'none'}). Map "
                    f"it to one of those {netKind}s. {_diagLoc(diag, mapRow)}")
                return None
            return net

        clockBindNet = dict()
        for clockName, clockDecl in childDomain.clocks.items():
            if clockDecl.direction != 'input':
                continue
            mapRow = clockMap.get(clockName)
            if mapRow is not None:
                net = resolveMappedNet(mapRow, 'clock')
                if net is None:
                    continue
                if rejectSelfDrivenInput(container, instanceKey, net, clockName, 'clock'):
                    continue
                binding = 'map'
            elif isContainerNet(clockName, 'clock'):
                net = clockName
                if rejectSelfDrivenInput(container, instanceKey, net, clockName, 'clock'):
                    continue
                binding = 'name'
            elif clockName == 'clk' and containerDomain.defaultClock:
                net = containerDomain.defaultClock
                binding = 'fallback'
            else:
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' "
                    f"in container '{containerBlock}' has no binding for its "
                    f"clock '{clockName}': '{containerBlock}' has no clock of "
                    f"that name, declared or local, and only 'clk' falls back "
                    f"to the container's default clock. Map it in the "
                    f"instance's clocks:. Declared clocks of "
                    f"'{containerBlock}': ({', '.join(containerDomain.clocks)}); "
                    f"local clock nets: ({localNetNames('clock') or 'none'}).")
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
                if rejectSelfDrivenInput(container, instanceKey, net, resetName, 'reset'):
                    continue
                binding = 'map'
            elif isContainerNet(resetName, 'reset'):
                net = resetName
                if rejectSelfDrivenInput(container, instanceKey, net, resetName, 'reset'):
                    continue
                binding = 'name'
            elif isAsync:
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' "
                    f"in container '{containerBlock}' has no binding for its "
                    f"asynchronous reset '{resetName}': '{containerBlock}' "
                    f"has no reset of that name, declared or local, and an "
                    f"asynchronous reset input takes no default fallback. Map "
                    f"it in the instance's resets:.")
                continue
            elif resetName == 'rst_n':
                # A synthesised register handler's rst_n takes no fallback:
                # _resolveRegisterHandlerBinds binds it to its leaf's register
                # bus reset, or the leaf is rejected.
                if childDomain.isRegHandler:
                    continue
                boundClockNet = clockBindNet[resetDecl.clock]
                # Deferred: local reset nets are candidates for the selected
                # reset, and their clock membership is known only once every
                # binding is resolved.
                pendingRstFallback.append((instanceKey, resetName, containerKey, boundClockNet))
                continue
            else:
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' "
                    f"in container '{containerBlock}' has no binding for its "
                    f"reset '{resetName}': '{containerBlock}' has no reset of "
                    f"that name, declared or local, and only 'rst_n' falls back "
                    f"to a selected reset. Map it in the instance's resets:. "
                    f"Declared resets of "
                    f"'{containerBlock}': ({', '.join(containerDomain.resets)}); "
                    f"local reset nets: ({localNetNames('reset') or 'none'}).")
                continue
            if not isAsync and container.nets[net].kind == 'declared':
                # The reset's own clock, mapped through this instance, must
                # be the clock the bound container reset belongs to. An
                # async container reset belongs to no clock (''), so a
                # synchronous child reset bound onto it fails here. A LOCAL
                # net's membership is known only once every binding is
                # resolved, so that case is checked in a later pass.
                childClockOfReset = resetDecl.clock
                boundClockNet = clockBindNet[childClockOfReset]
                netMembership = container.nets[net].clockNet
                if netMembership != boundClockNet:
                    diag.logError(
                        f"Instance '{instRow['instance']}' of block "
                        f"'{childBlock}' in container '{containerBlock}' "
                        f"would bind clock '{childClockOfReset}' to "
                        f"'{boundClockNet}' and reset '{resetName}' to "
                        f"'{net}', but '{containerBlock}' releases '{net}' "
                        f"on clock '{netMembership}', not on "
                        f"'{boundClockNet}'. A synchronous reset must be "
                        f"released on the container clock that the reset's "
                        f"own block clock is bound to. "
                        f"Map '{resetName}' to a reset released on "
                        f"'{boundClockNet}'.")
                    continue
            container.nets[net].consumers.append(Consumer(instanceKey, resetName, binding))

    # The top instance's own binding to the project file's testbench nets:
    # map, name match, or the clk/rst_n default fallback. The top's own
    # OUTPUTS are observed by the testbench rather than bound onto a net, so
    # root never has a local net to defer against.
    _bindTopInstance(root, instances, domains, blocks, testbenchClocks, testbenchResets, diag)

    # Reset-net membership on the SUPPLIER side: the clock the supplying
    # output's reset belongs to, mapped through the supplier's instance.
    # Deferred to here because the supplier's clock port may be an input
    # bound later in the pass above. For a LOCAL net this sets its
    # membership and checks each consumer against it. For a DECLARED output
    # only the supplier is checked, since the loop above already checked
    # that net's consumers.
    for container in containers.values():
        consumerNet = _consumerNetIndex(container)
        driverNet = _driverNetIndex(container)
        for net in container.nets.values():
            if not net.isReset or net.driver.kind != 'childOutput':
                continue
            supplierInstanceKey = net.driver.instanceKey
            supplierBlockKey = instances[supplierInstanceKey]['instanceTypeKey']
            supplierDomain = domains[supplierBlockKey]
            supplierResetDecl = supplierDomain.resets[net.driver.blockPort]
            if supplierResetDecl.isAsync:
                continue  # belongs to no clock
            supplierClockDecl = supplierDomain.clocks[supplierResetDecl.clock]
            index = consumerNet if supplierClockDecl.direction == 'input' else driverNet
            supplierClockNet = index.get((supplierInstanceKey, supplierResetDecl.clock))
            if supplierClockNet is None:
                # A failed binding has already stopped the build, so the
                # supplier's clock is an output bound to `~` and the reset
                # belongs to no clock of the container.
                if net.kind == 'local':
                    for consumer in net.consumers:
                        consumerDomain = domains[instances[consumer.instanceKey]['instanceTypeKey']]
                        if consumerDomain.resets[consumer.blockPort].isAsync:
                            continue
                        diag.logError(
                            f"Instance '{instances[consumer.instanceKey]['instance']}' "
                            f"binds synchronous reset '{consumer.blockPort}' to "
                            f"'{net.name}', a local net driven by instance "
                            f"'{instances[supplierInstanceKey]['instance']}' output "
                            f"'{net.driver.blockPort}', whose clock "
                            f"'{supplierResetDecl.clock}' is bound to `~`. That "
                            f"reset is released on no clock of "
                            f"'{blocks[container.blockKey]['block']}', so only an "
                            f"asynchronous reset input may consume it. Bind "
                            f"'{supplierResetDecl.clock}' to a net, or map "
                            f"'{consumer.blockPort}' to another reset.")
                else:
                    containerBlock = blocks[container.blockKey]['block']
                    supplierInstance = instances[supplierInstanceKey]['instance']
                    supplierClock = supplierResetDecl.clock
                    # Only a declared output no child drives can take the
                    # supplier's clock.
                    if container.nets[net.clockNet].driver.kind == 'ownImplementation':
                        fixes = [f"bind '{supplierClock}' of instance "
                                 f"'{supplierInstance}' to '{net.clockNet}' in its "
                                 f"clocks: map"]
                    else:
                        fixes = [f"bind '{supplierClock}' of instance "
                                 f"'{supplierInstance}' to an output clock of "
                                 f"'{containerBlock}' that no other child drives "
                                 f"(declaring one if needed) and set the clock: "
                                 f"of '{net.name}' to it"]
                    fixes.append(f"export another reset onto '{net.name}'")
                    diag.logError(
                        f"Instance '{supplierInstance}' exports reset "
                        f"'{net.driver.blockPort}' onto '{containerBlock}''s "
                        f"declared output reset '{net.name}', released on "
                        f"clock '{net.clockNet}', but the supplier's own reset "
                        f"belongs to its clock '{supplierClock}', which is "
                        f"bound to `~`, so it is released on no clock of "
                        f"'{containerBlock}'. An exported reset must be "
                        f"released on the clock of the declared output it "
                        f"drives. {_fixSentence(fixes)}")
                continue
            if net.kind == 'local':
                net.clockNet = supplierClockNet
                for consumer in net.consumers:
                    consumerDomain = domains[instances[consumer.instanceKey]['instanceTypeKey']]
                    consumerResetDecl = consumerDomain.resets[consumer.blockPort]
                    if consumerResetDecl.isAsync:
                        continue
                    boundClockNet = consumerNet[(consumer.instanceKey, consumerResetDecl.clock)]
                    if net.clockNet != boundClockNet:
                        diag.logError(
                            f"Instance '{instances[consumer.instanceKey]['instance']}' "
                            f"binds reset '{consumer.blockPort}' to '{net.name}', a "
                            f"local net released on clock '{net.clockNet}', but that "
                            f"instance's own clock '{consumerResetDecl.clock}' is "
                            f"bound to '{boundClockNet}' instead. A synchronous "
                            f"reset must be released on the container clock that "
                            f"the reset's own block clock is bound to. Map "
                            f"'{consumer.blockPort}' to a reset "
                            f"released on '{boundClockNet}'.")
            elif supplierClockNet != net.clockNet:
                diag.logError(
                    f"Instance '{instances[supplierInstanceKey]['instance']}' exports "
                    f"reset '{net.driver.blockPort}' onto "
                    f"'{blocks[container.blockKey]['block']}''s declared output "
                    f"reset '{net.name}', released on clock '{net.clockNet}', but "
                    f"the supplier's own reset belongs to clock '{supplierClockNet}' "
                    f"instead. An exported reset must be released on the clock "
                    f"of the declared output it drives. Export it onto a reset "
                    f"of clock '{supplierClockNet}', or change the clock: of "
                    f"'{net.name}'.")

    # Deferred rst_n fallback: bind to the selected reset of the container
    # clock that the reset's own block clock is bound to. Every candidate
    # belongs to that clock, so the reset and its clock are in one domain by
    # construction.
    for instanceKey, resetName, containerKey, boundClockNet in pendingRstFallback:
        chosen, candidates = _selectedReset(domains[containerKey], containers[containerKey],
                                            boundClockNet, domains, instances)
        if chosen is None:
            instRow = instances[instanceKey]
            childBlock = blocks[instRow['instanceTypeKey']]['block']
            containerBlock = blocks[containerKey]['block']
            containerDomain = domains[containerKey]
            container = containers[containerKey]
            childResets = domains[instRow['instanceTypeKey']].resets
            fixes = []
            if candidates and boundClockNet == containerDomain.defaultClock:
                # Several candidates on the container's default clock leave the
                # container's own rst_n unselected too, so a map would clear
                # only this instance; marking a declared reset default: true
                # clears both. One this instance drives cannot be marked, since
                # the fallback would then bind rst_n to its own output.
                markable = [name for name in candidates if name in containerDomain.resets
                            and not _drivenBy(container.nets[name], instanceKey)]
                diag.logError(
                    f"Instance '{instRow['instance']}' of block '{childBlock}' in "
                    f"container '{containerBlock}' falls back to the selected "
                    f"reset of container clock '{boundClockNet}' for its reset "
                    f"'rst_n'. "
                    + _defaultClockResetAmbiguity(containerDomain, blocks[containerKey], container,
                                                  candidates, markable, instances))
                continue
            if candidates:
                declared = [name for name in candidates if name in containerDomain.resets]
                # Binding rst_n to a reset this instance drives is rejected
                # as self-driven, whether by map or by default: true.
                selfDriven = [name for name in candidates
                              if _drivenBy(container.nets[name], instanceKey)]
                cause = (f"it has {len(candidates)} reset candidates "
                         f"({', '.join(candidates)}) and none is selected")
                mapTargets = [name for name in candidates if name not in selfDriven]
                declaredTargets = [name for name in declared if name not in selfDriven]
                if not mapTargets:
                    cause += (f", and the instance itself drives every one of "
                              f"them, so none can be its rst_n")
                elif selfDriven:
                    cause += f", and the instance itself drives {', '.join(selfDriven)}"
                if len(mapTargets) == len(candidates):
                    fixes.append("map rst_n to one of them in the instance's resets:")
                elif mapTargets:
                    targets = (mapTargets[0] if len(mapTargets) == 1
                               else f"one of {', '.join(mapTargets)}")
                    fixes.append(f"map rst_n to {targets} in the instance's resets:")
                if declaredTargets:
                    fixes.append(f"mark one of the declared resets "
                                 f"({', '.join(declaredTargets)}) default: true")
            else:
                # A local net on this clock consumed only by asynchronous
                # inputs is no candidate, but a map may still name it.
                asyncOnly = [netName for netName, net in container.nets.items()
                             if net.kind == 'local' and net.isReset
                             and net.clockNet == boundClockNet]
                if asyncOnly:
                    cause = (f"the only resets on it are local nets "
                             f"({', '.join(asyncOnly)}) consumed only by "
                             f"asynchronous reset inputs, which the fallback "
                             f"does not select")
                    asyncOnlyTargets = [name for name in asyncOnly
                                        if not _drivenBy(container.nets[name], instanceKey)]
                    if asyncOnlyTargets:
                        fixes.append(f"map rst_n to {' or '.join(asyncOnlyTargets)} "
                                     f"in the instance's resets:")
                else:
                    cause = (f"no synchronous reset of '{containerBlock}', "
                             f"declared or local, is on it")
            if not candidates or not fixes:
                # A further candidate would leave several, so a new
                # declared reset must also be the only marked one.
                marking = " marked default: true" if candidates else ""
                if container.nets[boundClockNet].kind == 'declared':
                    # An input reset may not belong to an output clock.
                    if containerDomain.clocks[boundClockNet].direction == 'output':
                        fixes.append(f"declare a synchronous `direction: output` "
                                     f"reset on '{boundClockNet}'{marking} in block "
                                     f"'{containerBlock}''s resets:")
                    else:
                        fixes.append(f"declare a synchronous reset on "
                                     f"'{boundClockNet}'{marking} in block "
                                     f"'{containerBlock}''s resets:")
                if not candidates:
                    fixes.append(f"have a child drive a local reset net on "
                                 f"'{boundClockNet}'")
                if len(childResets) == 1:
                    fixes.append(f"declare `resets: {{}}` on block '{childBlock}'")
                else:
                    fixes.append(f"remove 'rst_n' from block '{childBlock}''s resets:")
                # A map onto a net this instance drives is rejected as
                # self-driven, so such a net is never offered as a target.
                if any(net.isReset and not _drivenBy(net, instanceKey)
                       for net in container.nets.values()):
                    # async: true together with clock: is rejected.
                    removeClock = (" and remove its clock:, then"
                                   if childResets['rst_n'].clockStated else " and")
                    fixes.append(f"declare 'rst_n' async: true on block "
                                 f"'{childBlock}'{removeClock} map it in the "
                                 f"instance's resets:")
            diag.logError(
                f"Instance '{instRow['instance']}' of block '{childBlock}' in "
                f"container '{containerBlock}' falls back to the selected "
                f"reset of container clock '{boundClockNet}' for its reset "
                f"'rst_n', but {cause}. The rst_n fallback binds the one "
                f"selected reset of its clock. {_fixSentence(fixes)}")
            continue
        if rejectSelfDrivenInput(containers[containerKey], instanceKey, chosen, resetName, 'reset'):
            continue
        containers[containerKey].nets[chosen].consumers.append(
            Consumer(instanceKey, resetName, 'fallback'))

    # Second pass: the selected reset of each container clock, now with local
    # reset nets among the candidates. Zero or several unmarked candidates
    # leaves it None. On the default clock several are an error, as in the
    # first pass: its selected reset is the block's rst_n. Elsewhere None is
    # reported only where generated logic needs a reset.
    for containerKey, container in containers.items():
        domain = domains[containerKey]
        for clockName in domain.clocks:
            selected, candidates = _selectedReset(
                domain, container, clockName, domains, instances)
            if selected is None and len(candidates) > 1 and clockName == domain.defaultClock:
                diag.logError(_defaultClockResetAmbiguity(
                    domain, blocks[containerKey], container, candidates,
                    [name for name in candidates if name in domain.resets], instances))
            domain.selectedReset[clockName] = selected
        # An undeclared rst_n is reserved wherever it is emitted as the
        # alias of the default clock's selected reset. BlockDomains.build()
        # reserved it only for a declared selected reset; a local net
        # promoted here makes the alias fire too.
        defaultReset = domain.selectedReset.get(domain.defaultClock)
        if ('rst_n' in domain.resets or defaultReset is None
                or domain.names.get('rst_n') == 'implicit reset'):
            continue
        collidingKind = domain.names.get('rst_n')
        if collidingKind is None and 'rst_n' in container.nets:
            collidingKind = 'local net'
        if collidingKind is not None:
            diag.logError(
                f"Block '{domain.block}' does not declare rst_n, so rst_n is "
                f"the alias of its default clock '{domain.defaultClock}''s "
                f"selected reset '{defaultReset}', but '{domain.block}' "
                f"already uses the name 'rst_n' for a {collidingKind}; the "
                f"reserved names clk/rst_n must be distinct from every other "
                f"name within a block. Rename the {collidingKind}.")

    # Built once per container, from the ordinary binding pass above: the
    # router/handler/memory-accessor resolution below each read another
    # container's consumer edges by (instanceKey, blockPort) many times over,
    # so the reverse index is worth sharing rather than rebuilding per lookup
    # (a router's own container, a leaf's own container, a memory's owning
    # container may each be read from several call sites below).
    consumerNetByContainer = {blockKey: _consumerNetIndex(container)
                              for blockKey, container in containers.items()}

    # A connectionMaps: row's boundary port derives its domain inside-out
    # from the inner port it routes to, not from the outer connection. The
    # result is persisted (portDomainRows) for the projectOpen view to read
    # back. The inner port's clock is its own derived clock when it is
    # itself a boundary port of the inner block, so maps chain upward; else
    # its declared clock, else the INNER block's default clock, not the
    # outer block's, which a renamed inner instance map need not agree
    # with. That clock is then followed through the inner instance's
    # binding: an input clock to the net it consumes, an output clock to
    # the net it drives. A boundary port whose inner net is a LOCAL net the
    # container never exports is an error, since the parent cannot drive or
    # name that domain. A boundary port the block also declares in ports:
    # has its own clock (its clock:, or the block default), which must be
    # the derived one. Every boundary port left without a derived clock has
    # an error reported, here or at the failed binding it depends on.
    # `boundaryDomains` keeps each derived clock, with the inner port it
    # came from, for the connection checks below.
    connMapByBoundary = {(connMap['blockKey'], connMap['portName']): connMap
                         for connMap in connectionMaps.values()}
    driverNetByContainer = {blockKey: _driverNetIndex(container)
                            for blockKey, container in containers.items()}
    boundaryResults = dict()
    derivingBoundary = set()

    def deriveBoundary(boundaryKey):
        # Memoised so a chained map resolves its inner boundary port first,
        # whatever the declaration order.
        if boundaryKey in boundaryResults:
            return boundaryResults[boundaryKey]
        if boundaryKey in derivingBoundary:
            raise AssertionError(
                f"clockTree.build: connectionMaps boundary port "
                f"{boundaryKey!r} chains back to itself, which the instance "
                f"hierarchy cannot produce")
        derivingBoundary.add(boundaryKey)
        result = deriveOneBoundary(connMapByBoundary[boundaryKey])
        derivingBoundary.remove(boundaryKey)
        boundaryResults[boundaryKey] = result
        return result

    def deriveOneBoundary(connMap):
        outerBlockKey = connMap['blockKey']
        outerBlock = blocks[outerBlockKey]['block']
        boundaryPortName = connMap['portName']
        innerInstanceKey = connMap['instanceKey']
        innerInstance = instances[innerInstanceKey]['instance']
        innerBlockKey = instances[innerInstanceKey]['instanceTypeKey']
        innerDomain = domains[innerBlockKey]
        innerPortName = connMap['instancePortName']
        innerPort = f"{innerInstance}.{innerPortName}"
        if (innerBlockKey, innerPortName) in connMapByBoundary:
            innerClockName = deriveBoundary((innerBlockKey, innerPortName))[0]
        else:
            innerClockName = (_declaredPortClock(blocks, domains, innerBlockKey, innerPortName)
                              or innerDomain.defaultClock)
        if innerClockName is None:
            diag.logError(
                f"Boundary port '{boundaryPortName}' of block '{outerBlock}' "
                f"is bridged by connectionMaps: to inner port '{innerPort}', "
                f"which has no clock: block '{innerDomain.block}' does not "
                f"declare '{innerPortName}' with a clock:, and has no "
                f"default clock because every clock it declares is "
                f"direction: output. A boundary port's domain is the clock "
                f"of the inner port it is bridged to. Declare port "
                f"'{innerPortName}' on block '{innerDomain.block}' with a "
                f"clock:.")
            return None
        outerContainer = containers[outerBlockKey]
        isInputClock = innerDomain.clocks[innerClockName].direction == 'input'
        netIndex = (consumerNetByContainer if isInputClock else driverNetByContainer)[outerBlockKey]
        domainClock = netIndex.get((innerInstanceKey, innerClockName))
        if domainClock is None:
            # A failed binding has already stopped the build, so the clock
            # is an output bound to `~`.
            diag.logError(
                f"Boundary port '{boundaryPortName}' of block "
                f"'{outerBlock}' is bridged by connectionMaps: to inner "
                f"port '{innerPort}', which runs on output clock "
                f"'{innerClockName}' of block '{innerDomain.block}', but "
                f"instance '{innerInstance}' binds '{innerClockName}' to "
                f"`~`. A boundary port's domain is the clock of the "
                f"inner port it is bridged to, so that clock must reach "
                f"a clock of '{outerBlock}'. Bind '{innerClockName}' of "
                f"instance '{innerInstance}' to an output clock of "
                f"'{outerBlock}' in its clocks: map, declaring one if "
                f"needed.")
            return None
        if outerContainer.nets[domainClock].kind == 'local':
            diag.logError(
                f"Boundary port '{boundaryPortName}' of block "
                f"'{outerBlock}' derives to '{domainClock}', "
                f"a local net of '{outerBlock}' the block "
                f"does not export. A boundary port timed by a local net the "
                f"container does not export would carry data in a domain the "
                f"parent cannot drive or name. Declare '{domainClock}' as an "
                f"output clock or reset instead.")
            return None
        declaredRow = (blocks[outerBlockKey].get('ports') or {}).get(boundaryPortName)
        if declaredRow is not None:
            declaredClock = declaredRow['clock'] or domains[outerBlockKey].defaultClock
            if declaredClock != domainClock:
                verb = 'set' if declaredRow['clock'] else 'declare'
                fixes = [f"{verb} clock: {domainClock} on port '{boundaryPortName}'"]
                declaredNet = outerContainer.nets[declaredClock]
                # An input may bind any clock net it does not drive itself;
                # an output only a declared output no other child drives.
                canBind = (not _drivenBy(declaredNet, innerInstanceKey) if isInputClock
                           else declaredNet.driver.kind == 'ownImplementation')
                if canBind:
                    fixes.append(f"bind '{innerClockName}' of instance "
                                 f"'{innerInstance}' to '{declaredClock}' in its "
                                 f"clocks: map")
                diag.logError(
                    f"Port '{boundaryPortName}' of block '{outerBlock}' is "
                    f"declared on clock '{declaredClock}' (its own clock:, or "
                    f"the block default when unstated), but connectionMaps: "
                    f"bridges it to inner port '{innerPort}', which runs on "
                    f"'{domainClock}' of '{outerBlock}'. A declared boundary "
                    f"port's clock must be the clock of the inner port it is "
                    f"bridged to. {_fixSentence(fixes)}")
                return None
        return (domainClock, innerPort)

    for boundaryKey in connMapByBoundary:
        deriveBoundary(boundaryKey)
    # Declaration order, not derivation order, which chaining reorders.
    boundaryDomains = {boundaryKey: boundaryResults[boundaryKey]
                       for boundaryKey in connMapByBoundary}
    portDomainRows = [(blockKey, portName, domainClock, index)
                      for index, ((blockKey, portName), (domainClock, _))
                      in enumerate(boundaryDomains.items())]

    # An AUTHORED connection clock: sets the domain of each top-down end, so
    # exactly one INPUT block clock of that end's instance, in the same
    # container, must be bound to it. Read from the bindings just computed, so
    # a renamed instance map is respected. A declared port or a derived
    # connectionMaps boundary port has a domain of its own, checked for
    # agreement below. Under an unstated clock: each top-down end takes its
    # own block default, so that block must have one; the two ends' names
    # need not agree. Every connection reaching the same top-down port of a
    # block, through any of its instances, must put it on the same block
    # clock, since the block's module has one port.
    topDownPortClock = dict()

    def recordTopDownPortClock(connRow, end, instRow, block, localClock):
        portKey = (end['instanceTypeKey'], end['portName'])
        firstClock, firstInstance, firstLoc = topDownPortClock.setdefault(
            portKey, (localClock, instRow['instance'], _diagLoc(diag, connRow)))
        if firstClock == localClock:
            return
        diag.logError(
            f"Top-down port '{end['portName']}' of block '{block}' is on block "
            f"clock '{firstClock}' through instance '{firstInstance}' (its "
            f"connection at {firstLoc}), but on block clock '{localClock}' "
            f"through instance '{instRow['instance']}' (its connection at "
            f"{_diagLoc(diag, connRow)}). A block's port has one clock across "
            f"every instance of the block. Either declare port "
            f"'{end['portName']}' in block '{block}''s ports: with its clock: "
            f"(a connection clock: reaching it must then agree), or map each "
            f"instance's clocks: so every connection puts '{end['portName']}' "
            f"on the same block clock.")

    for connRow in connections.values():
        clockName = connRow['clock']
        for end in connRow['ends'].values():
            instanceKey = end['instanceKey']
            instRow = instances[instanceKey]
            containerKey = instRow['containerKey']
            block = blocks[end['instanceTypeKey']]['block']
            if (declaredPortRow(blocks[end['instanceTypeKey']], end['portName']) is not None
                    or (end['instanceTypeKey'], end['portName']) in boundaryDomains):
                continue
            if not clockName:
                if domains[end['instanceTypeKey']].defaultClock is None:
                    diag.logError(
                        f"Connection '{connRow['connection']}' names no clock:, "
                        f"so its top-down port '{end['portName']}' of instance "
                        f"'{instRow['instance']}' takes the default clock of "
                        f"block '{block}', but '{block}' has no default clock "
                        f"(every declared clock is direction: output). Either "
                        f"declare port '{end['portName']}' in block '{block}''s "
                        f"ports: with its clock:, or give '{block}' an input "
                        f"clock.")
                recordTopDownPortClock(connRow, end, instRow, block,
                                       domains[end['instanceTypeKey']].defaultClock)
                continue
            if containerKey == ClockTree.ROOT_KEY:
                # The topInstance's own binding to the testbench is
                # resolved separately by `_bindTopInstance`; nothing to
                # resolve against here.
                continue
            container = containers[containerKey]
            matches = _inputClocksResolvingTo(container, instanceKey, clockName)
            if len(matches) == 1:
                recordTopDownPortClock(connRow, end, instRow, block, matches[0])
                continue
            if not matches:
                net = container.nets.get(clockName)
                containerBlock = blocks[containerKey]['block']
                fixes = []
                if net is None or net.isReset:
                    notice = (f" '{clockName}' is not a clock net of container "
                              f"'{containerBlock}'.")
                    fixes.append(f"correct the connection's clock: to a clock "
                                 f"net of '{containerBlock}'")
                else:
                    notice = ""
                    hasInputClock = any(
                        clockDecl.direction == 'input'
                        for clockDecl in domains[end['instanceTypeKey']].clocks.values())
                    if hasInputClock and not _drivenBy(net, instanceKey):
                        fixes.append(f"bind one of the instance's input clocks "
                                     f"to '{clockName}' in its clocks: map")
                    drivingOutputs = [blockPort for (driverKey, blockPort), netName
                                      in driverNetByContainer[containerKey].items()
                                      if driverKey == instanceKey and netName == clockName]
                    if drivingOutputs:
                        fixes.append(f"declare port '{end['portName']}' on block "
                                     f"'{block}' with clock: "
                                     f"{' or '.join(drivingOutputs)}")
                    fixes.append("change the connection's clock:")
                diag.logError(
                    f"Connection '{connRow['connection']}' names clock: "
                    f"'{clockName}', but no input clock of instance "
                    f"'{instRow['instance']}' (block '{block}') resolves to "
                    f"that container clock.{notice} The connection's clock: "
                    f"sets the domain of its top-down port "
                    f"'{end['portName']}', so it must name the container "
                    f"clock an input clock of the instance is bound to. "
                    f"{_fixSentence(fixes)}")
            else:
                diag.logError(
                    f"Connection '{connRow['connection']}' names clock: "
                    f"'{clockName}', but more than one input clock of "
                    f"instance '{instRow['instance']}' (block '{block}') "
                    f"resolves to it ({', '.join(matches)}), so the domain "
                    f"of its top-down port '{end['portName']}' is ambiguous. "
                    f"The connection's clock: sets the domain of a top-down "
                    f"port, so exactly one input clock of the instance may "
                    f"resolve to that clock. Bind only one of "
                    f"{', '.join(matches)} to '{clockName}', declare port "
                    f"'{end['portName']}' on block '{block}' with its own "
                    f"clock:, or drop the connection's clock: so each end "
                    f"takes its block default clock.")

    # A connection's clock: and the domain of a port it reaches must agree;
    # neither takes precedence. That domain is a declared port's own clock
    # (its clock:, or the block default when unstated), else a
    # connectionMaps boundary port's derived clock. An ordinary top-down
    # end has no domain of its own to disagree with.
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
            portName = end['portName']
            declaredClock = _declaredPortClock(blocks, domains, endBlockKey, portName)
            boundary = boundaryDomains.get((endBlockKey, portName))
            if declaredClock is not None:
                portClock = declaredClock
                portDomain = (f"declares clock: '{declaredClock}' (its own, or "
                              f"the block default when unstated)")
            elif boundary is not None:
                portClock, innerPort = boundary
                portDomain = (f"is a connectionMaps: boundary port on clock "
                              f"'{portClock}', the clock of inner port "
                              f"'{innerPort}' it is bridged to")
            else:
                continue
            container = containers[containerKey]
            endDomain = domains[endBlockKey]
            consumerNet = consumerNetByContainer[containerKey]
            driverNet = driverNetByContainer[containerKey]
            portLabel = (f"Port '{portName}' of block "
                         f"'{blocks[endBlockKey]['block']}' (instance "
                         f"'{instRow['instance']}')")
            # A boundary port's clock must stay its inner port's, so only a
            # plain declared port may move to another block clock.
            clocksOnConnection = [
                name for name, clockDecl in endDomain.clocks.items()
                if (consumerNet if clockDecl.direction == 'input' else driverNet).get(
                    (instanceKey, name)) == clockName]
            retarget = (f"change the clock: of port '{portName}' to "
                        f"{' or '.join(clocksOnConnection)}"
                        if clocksOnConnection and boundary is None else None)
            isInputClock = endDomain.clocks[portClock].direction == 'input'
            if isInputClock:
                boundNet = consumerNet[(instanceKey, portClock)]
            elif (instanceKey, portClock) in container.unconnectedOutputs:
                fixes = [retarget] if retarget else []
                fixes.append("drop the connection's clock:")
                diag.logError(
                    f"{portLabel} is on output clock '{portClock}', which the "
                    f"instance binds to `~`, but connection "
                    f"'{connRow['connection']}' reaching it names clock: "
                    f"'{clockName}'. A port on an "
                    f"unconnected clock is on no clock of the container, so "
                    f"no connection clock: can agree with it. "
                    f"{_fixSentence(fixes)}")
                continue
            else:
                boundNet = driverNet[(instanceKey, portClock)]
            if boundNet == clockName:
                continue
            net = container.nets.get(clockName)
            isClockNet = net is not None and not net.isReset
            fixes = []
            if isInputClock and isClockNet and not _drivenBy(net, instanceKey):
                fixes.append(f"bind '{portClock}' of instance "
                             f"'{instRow['instance']}' to '{clockName}' in its "
                             f"clocks: map")
            if retarget:
                fixes.append(retarget)
            fixes.append(f"change the connection's clock: to '{boundNet}'")
            notice = ("" if isClockNet else
                      f" '{clockName}' is not a clock net of container "
                      f"'{blocks[containerKey]['block']}'.")
            diag.logError(
                f"{portLabel} {portDomain}, bound to '{boundNet}', but "
                f"connection '{connRow['connection']}' reaching it names "
                f"clock: '{clockName}' instead.{notice} A port's own domain "
                f"and its connection's clock: must agree. "
                f"{_fixSentence(fixes)}")

    # Instances transitively contained by this build's topInstance. A block
    # shared with another project (a reusable IP) may have an instance in
    # that project's own standalone harness. postParseRegisterPorts routes
    # only reachable instances' register buses, so the register-port
    # resolution below skips the same out-of-scope instances: they have no
    # binds of this build's making to check.
    reachableInstances = _reachableInstanceKeys(containers, root)

    _resolveRouterBusClockReset(domains, instances, blocks, consumerNetByContainer,
                               reachableInstances, diag)
    _resolveRegisterHandlerBinds(domains, containers, instances, connections, blocks,
                                 consumerNetByContainer, reachableInstances,
                                 registerBusPassthroughs, diag)
    # A local net must be consumed by at least one child input binding of
    # its container; `~` is how an output is left unused. Checked once every
    # input is bound, a register handler's included, so a consumer bound
    # later in declaration order is not missed.
    for containerKey, container in containers.items():
        containerBlock = blocks[containerKey]['block']
        for net in container.nets.values():
            if net.kind != 'local' or net.consumers:
                continue
            driverInstance = instances[net.driver.instanceKey]['instance']
            diag.logError(
                f"Container '{containerBlock}' net '{net.name}', driven by "
                f"instance '{driverInstance}' output '{net.driver.blockPort}', "
                f"has no consumer. A local net must be consumed by at least "
                f"one child input binding. Bind a child input to "
                f"'{net.name}', or bind the driving output to `~`.")

    # Memory accessors are checked in every container the root project
    # declares, instantiated or not, since the root project generates each
    # of them; a referenced child project's unreachable instances stay that
    # project's own build's to check.
    accessorScope = reachableInstances | {
        instanceKey for instanceKey, instRow in instances.items()
        if instRow['container'] != ClockTree.ROOT_KEY
        and contextOwningProject[blocks[instRow['containerKey']]['_context']] == rootProjectName}
    _checkMemoryAccessorDomains(domains, containers, instances, memoryConnections,
                                consumerNetByContainer, driverNetByContainer,
                                accessorScope, diag)
    # A registerConnections accessor's port is on its block's default clock,
    # so, like a memory accessor, its block must have one.
    for regConnRow in registerConnections.values():
        accessorInstRow = instances[regConnRow['instanceKey']]
        accessorDomain = domains[accessorInstRow['instanceTypeKey']]
        if accessorDomain.defaultClock is None:
            diag.logError(
                f"Instance '{accessorInstRow['instance']}' of block "
                f"'{accessorDomain.block}' accesses register "
                f"'{regConnRow['register']}' of block '{regConnRow['block']}', "
                f"but '{accessorDomain.block}' has no default clock (every "
                f"declared clock is direction: output). A register accessor "
                f"takes its block's default clock. Give "
                f"'{accessorDomain.block}' an input clock.")

    # The co-simulation wrapper resets each port's BFM with the port clock's
    # selected reset, so every clock timing a port of a hasVl block needs one:
    # declared, connection-derived, boundary, memory and register ports. Only
    # blocks declared in the root project are checked.
    portDomainsByBlock = dict()
    for outerBlockKey, boundaryPortName, domainClock, _ in portDomainRows:
        portDomainsByBlock.setdefault(outerBlockKey, []).append((boundaryPortName, domainClock))
    connectionEndsByBlock = dict()
    for connRow in connections.values():
        for end in connRow['ends'].values():
            connectionEndsByBlock.setdefault(end['instanceTypeKey'], []).append((connRow, end))
    # A memoryConnections or registerConnections row gives the accessing
    # instance's block a port named after the memory or register, on the
    # block default clock. A local-mode memory row names no instance.
    objectPortsByBlock = dict()
    for memConnRow in memoryConnections.values():
        if memConnRow['instanceKey']:
            objectPortsByBlock.setdefault(
                instances[memConnRow['instanceKey']]['instanceTypeKey'], []).append(memConnRow['memory'])
    for regConnRow in registerConnections.values():
        objectPortsByBlock.setdefault(
            instances[regConnRow['instanceKey']]['instanceTypeKey'], []).append(regConnRow['register'])
    for blockKey, blockRow in blocks.items():
        if not blockRow['hasVl'] or contextOwningProject[blockRow['_context']] != rootProjectName:
            continue
        domain = domains[blockKey]
        portsByClock = OrderedDict()
        # A declared port's own clock (its clock:, else the block default),
        # which for a boundary port equals its derived clock; then each
        # remaining connectionMaps boundary row.
        boundaryClocks = dict(portDomainsByBlock.get(blockKey, []))
        # Every boundary port name, before registerBusPort is popped out of
        # boundaryClocks below: reused by the connection branch so a port
        # already resolved here - the register-bus port included - is never
        # derived a second time, once wrong.
        boundaryPorts = set(boundaryClocks)
        boundaryClocks.pop(domain.registerBusPort, None)
        for portName, declaredRow in blockRow.get('ports', {}).items():
            boundaryClocks.pop(portName, None)
            clockName = declaredRow['clock'] or domain.defaultClock
            portsByClock.setdefault(clockName, []).append(portName)
        for boundaryPortName, domainClock in boundaryClocks.items():
            portsByClock.setdefault(domainClock, []).append(boundaryPortName)
        # Top-down port: the connection clock: match from build(), re-applied
        # per end because that check stores nothing.
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
                (portClock,) = _inputClocksResolvingTo(containers[containerKey], instanceKey,
                                                       authoredClock)
            else:
                portClock = domain.defaultClock
            bucket = portsByClock.setdefault(portClock, [])
            if portName not in bucket:
                bucket.append(portName)
        for portName in objectPortsByBlock.get(blockKey, []):
            bucket = portsByClock.setdefault(domain.defaultClock, [])
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
                f"which has no selected reset: {cause}. The "
                f"co-simulation wrapper's BFM needs one; mark a reset on "
                f"'{clockName}' default: true or declare one.")

    # A block clock hosting a register bus (a router's, a served
    # leaf's, or a passthrough container's registerClock) must
    # have a selected reset. A reusable IP with resets: {} and no
    # registerPorts: reset: would otherwise reach generation with
    # registerReset None. A router with none is rejected earlier, in
    # _resolveRouterBusClockReset. Only those three block kinds set
    # registerClock; every other block keeps both None.
    for domain in domains.values():
        if domain.registerClock is not None and domain.registerReset is None:
            diag.logError(
                f"Block '{domain.block}' hosts its register bus on clock "
                f"'{domain.registerClock}', but that clock has no selected "
                f"reset. A router's, a served leaf's or a passthrough "
                f"container's register bus clock must have one. Declare a "
                f"reset on '{domain.registerClock}', or mark one of its "
                f"resets default: true.")

    # A regAccess memory whose clock differs from its block's
    # register bus clock is served through the handler's bridge
    # (_resolveRegisterHandlerBinds), whose memory side needs a reset in the
    # memory's own domain. postParseRegisterPorts rejects a router that owns
    # a regAccess memory before this point, and handlers own no memories, so
    # only served leaves reach this check, in their own clock-port names.
    for domain in domains.values():
        if domain.registerClock is None:
            continue
        bridgedMemoriesByClock = dict()
        for memDomain in domain.memories:
            if not memDomain.regAccess or memDomain.clock == domain.registerClock:
                continue
            bridgedMemoriesByClock.setdefault(memDomain.clock, list()).append(memDomain)
            if memDomain.reset is not None:
                continue
            diag.logError(
                f"Memory '{memDomain.memory}' of block '{domain.block}' is "
                f"regAccess on clock '{memDomain.clock}', which has no "
                f"selected reset, but the block's register bus is on "
                f"'{domain.registerClock}'. The register handler's "
                f"bridge to that memory is generated logic in the memory's "
                f"domain and needs a reset there; declare a reset on "
                f"'{memDomain.clock}' (or mark one default: true) or name it "
                f"with the memory's reset:.")
        # The bridge for one clock is one piece of generated logic with one
        # reset, not one per memory. The handler carries one clock/reset pair
        # per clock (rows() persists one blockClocksResets entry per name), so
        # two memories bridged to the same clock with different resets would
        # leave one of them naming a handler port that was never declared.
        for clockName, memDomainsOnClock in bridgedMemoriesByClock.items():
            resetsUsed = sorted({memDomain.reset for memDomain in memDomainsOnClock
                                 if memDomain.reset is not None})
            if len(resetsUsed) > 1:
                names = ', '.join(f"'{memDomain.memory}' (reset '{memDomain.reset}')"
                                  for memDomain in memDomainsOnClock if memDomain.reset is not None)
                diag.logError(
                    f"Block '{domain.block}' clock '{clockName}' hosts more "
                    f"than one regAccess memory bridged to the register bus "
                    f"({names}), resolving to different resets "
                    f"({', '.join(repr(r) for r in resetsUsed)}). The "
                    f"register handler's bridge to one clock has one reset. "
                    f"Give the memories the same reset: or leave both to the "
                    f"clock's selected reset.")

    _checkSupplyGraph(domains, containers, instances, blocks, diag)

    # Standalone simulation attributes, resolved once
    # every instance's own bindings, across the whole design, are known.
    resolvedByInstance = _resolveAllInstances(root, containers, domains, instances)
    _resolveStandaloneAttrs(domains, blocks, instances, resolvedByInstance,
                           testbenchClocks, testbenchResets,
                           contextOwningProject, rootProjectName, diag)

    return ClockTree(domains, containers, root, diag, portDomainRows)


def _bindTopInstance(root, instances, domains, blocks, testbenchClocks, testbenchResets, diag):
    """Bind the top instance's input clocks and resets to the testbench nets
    by map, name match or the clk/rst_n fallback, and report any testbench net
    that binds nothing. The top's outputs are observed by the testbench, so
    root has no local nets.
    """
    if not root.instances:
        return
    ((topInstanceKey, topBlockKey),) = root.instances.items()
    topDomain = domains[topBlockKey]
    topBlock = blocks[topBlockKey]['block']
    instRow = instances[topInstanceKey]

    rootDefaultClock = next(name for name, row in testbenchClocks.items() if row['default'])
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

    for mapKey, mapRow in clockMap.items():
        if mapKey not in topDomain.clocks:
            diag.logError(
                f"topInstance '{instRow['instance']}' maps clock '{mapKey}', "
                f"which is not one of block '{topBlock}''s own declared "
                f"clocks ({', '.join(topDomain.clocks)}). Remove "
                f"'{mapKey}' from the topInstance's clocks: map. {_diagLoc(diag, mapRow)}")
    for mapKey, mapRow in resetMap.items():
        if mapKey not in topDomain.resets:
            diag.logError(
                f"topInstance '{instRow['instance']}' maps reset '{mapKey}', "
                f"which is not one of block '{topBlock}''s own declared "
                f"resets ({', '.join(topDomain.resets)}). Remove "
                f"'{mapKey}' from the topInstance's resets: map. {_diagLoc(diag, mapRow)}")

    def resolveMappedNet(mapRow, netKind):
        net = mapRow['bind']
        if not net:
            diag.logError(
                f"topInstance '{instRow['instance']}' of block '{topBlock}' "
                f"maps '{mapRow[netKind]}' to `~`; an input {netKind} needs an "
                f"actual testbench net to consume. Map '{mapRow[netKind]}' "
                f"to a testbench {netKind}. {_diagLoc(diag, mapRow)}")
            return None
        netObj = root.nets.get(net)
        if netObj is None or netObj.isReset != (netKind == 'reset'):
            declared = ', '.join(f"'{name}'" for name in
                                 (testbenchResets if netKind == 'reset' else testbenchClocks))
            diag.logError(
                f"topInstance '{instRow['instance']}' of block '{topBlock}' "
                f"maps {netKind} '{mapRow[netKind]}' to '{net}', which is not "
                f"one of the project file's declared {netKind}s ({declared}). "
                f"Map it to one of those {netKind}s. {_diagLoc(diag, mapRow)}")
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
        elif clockName == 'clk':
            net = rootDefaultClock
            binding = 'fallback'
        else:
            diag.logError(
                f"topInstance '{instRow['instance']}' of block '{topBlock}' has "
                f"no binding for its clock '{clockName}': the project file "
                f"declares no clock of that name, and only 'clk' falls back to "
                f"the testbench default clock. Map it in the topInstance's "
                f"clocks:, or declare a testbench clock '{clockName}'. "
                f"Declared testbench clocks: "
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
                f"asynchronous reset input takes no default fallback. Map it "
                f"in the topInstance's resets:, or declare a testbench reset "
                f"'{resetName}'.")
            continue
        elif resetName == 'rst_n':
            boundClockNet = clockBindNet[resetDecl.clock]
            net = rootSelectedReset.get(boundClockNet)
            if not net:
                candidates = byClock.get(boundClockNet, [])
                if candidates:
                    cause = (f"that clock has {len(candidates)} testbench "
                             f"resets ({', '.join(candidates)}) and none is "
                             f"selected")
                    fix = (f"Map rst_n to one of "
                           f"{', '.join(candidates)} in the topInstance's "
                           f"resets:.")
                else:
                    # A synchronous map fails, since every testbench reset is
                    # on another clock, and resets: {} leaves a testbench
                    # reset unconsumed. An asynchronous reset may be mapped.
                    cause = "that clock has no testbench reset"
                    # async: true together with clock: is rejected.
                    removeClock = (" and remove its clock:, then"
                                   if resetDecl.clockStated else " and")
                    fix = (f"Declare a reset on '{boundClockNet}' in the "
                           f"project file's resets:, or declare 'rst_n' "
                           f"async: true on block '{topBlock}'{removeClock} "
                           f"map it in the topInstance's resets:.")
                diag.logError(
                    f"topInstance '{instRow['instance']}' of block '{topBlock}' "
                    f"falls back to the selected reset of testbench clock "
                    f"'{boundClockNet}' for its reset 'rst_n', but {cause}. "
                    f"The rst_n fallback binds the one selected reset of its "
                    f"clock. {fix}")
                continue
            binding = 'fallback'
        else:
            diag.logError(
                f"topInstance '{instRow['instance']}' of block '{topBlock}' has "
                f"no binding for its reset '{resetName}': the project file "
                f"declares no reset of that name, and only 'rst_n' falls back "
                f"to a selected reset. Map it in the topInstance's resets:, "
                f"or declare a testbench reset '{resetName}'. Declared "
                f"testbench resets: "
                f"({', '.join(testbenchResets)}).")
            continue
        if not isAsync:
            # The testbench reset must release on the testbench clock the
            # reset's own clock is bound to.
            boundClockNet = clockBindNet[resetDecl.clock]
            netMembership = root.nets[net].clockNet
            if netMembership != boundClockNet:
                diag.logError(
                    f"topInstance '{instRow['instance']}' of block '{topBlock}' "
                    f"would bind clock '{resetDecl.clock}' to '{boundClockNet}' "
                    f"and reset '{resetName}' to '{net}', but the testbench "
                    f"releases '{net}' on clock '{netMembership}', not on "
                    f"'{boundClockNet}'. A synchronous reset must be released "
                    f"on the testbench clock that the reset's own block clock "
                    f"is bound to. Map "
                    f"'{resetName}' to a testbench reset of "
                    f"'{boundClockNet}'.")
                continue
        root.nets[net].consumers.append(Consumer(topInstanceKey, resetName, binding))

    # Every testbench entry binds something: an entry the top block
    # never consumes would have the testbench generate a clock or reset the
    # design does not have.
    for netName, net in root.nets.items():
        if net.consumers:
            continue
        diag.logError(
            f"Testbench {'reset' if net.isReset else 'clock'} '{netName}' binds "
            f"no input of the top block '{topBlock}'. Every testbench clock "
            f"and reset must bind an input of the top block. Remove "
            f"'{netName}' from the project file, or map a top-block input "
            f"to it.")


def _diagLoc(diag, row):
    return diag.diagnosticLocation(row['_context'], row.get('lc'))


def _selectedReset(domain, container, clockNet, domains, instances):
    """(selected reset or None, candidates) for container clock `clockNet`.
    The candidates are the declared resets on it and the local reset nets
    belonging to it, less a local net consumed only by asynchronous reset
    inputs, which releases nothing synchronously. A local net with no consumer
    yet stays a candidate: the rst_n fallback being resolved may be what
    consumes it. The declared candidate marked default: true wins, else the
    sole candidate.
    """
    declared = [name for name, resetDecl in domain.resets.items()
                if not resetDecl.isAsync and resetDecl.clock == clockNet]
    local = [netName for netName, net in container.nets.items()
             if net.kind == 'local' and net.isReset and net.clockNet == clockNet
             and not (net.consumers and all(
                 domains[instances[c.instanceKey]['instanceTypeKey']].resets[c.blockPort].isAsync
                 for c in net.consumers))]
    candidates = declared + local
    marked = [name for name in declared if domain.resets[name].default]
    if marked:
        return (marked[0] if len(marked) == 1 else None), candidates
    return (candidates[0] if len(candidates) == 1 else None), candidates


def _defaultClockResetAmbiguity(domain, blockRow, container, candidates, markable, instances):
    """The diagnostic for several reset candidates, none selected, on the
    block's default clock. `markable` are the declared candidates whose
    default: true would clear it; one the block does not list in resets: is
    its implicit rst_n.
    """
    declaredResets = blockRow.get('resets') or {}
    labels = []
    for name in candidates:
        if name in declaredResets:
            labels.append(f"declared reset '{name}'")
        elif name in domain.resets:
            labels.append(f"implicit reset '{name}'")
        else:
            driver = instances[container.nets[name].driver.instanceKey]['instance']
            labels.append(f"local reset net '{name}' (driven by instance '{driver}')")
    listed = ', '.join(labels[:-1]) + ' and ' + labels[-1]
    if any(name in domain.resets for name in candidates):
        reason = f"{'neither' if len(candidates) == 2 else 'none'} is marked default: true"
    else:
        reason = "only a declared reset can be marked default: true and none of them is declared"
    if markable and markable[0] in declaredResets:
        fix = f"Mark '{markable[0]}' default: true in block '{domain.block}''s resets:."
    elif markable:
        fix = (f"Declare '{markable[0]}' in block '{domain.block}''s resets: "
               f"with default: true.")
    else:
        fix = (f"Declare a synchronous reset on '{domain.defaultClock}' marked "
               f"default: true in block '{domain.block}''s resets:.")
    return (f"Block '{domain.block}' has {len(candidates)} resets on its default "
            f"clock '{domain.defaultClock}': {listed}. The block's rst_n, used by "
            f"its default-clock flops and default-domain aliases, comes from the "
            f"single selected reset of the default clock, and none is selected "
            f"because {reason}. {fix}")


def _inputClocksResolvingTo(container, instanceKey, netName):
    """The instance's input block clocks whose consumer edge in `container`
    resolves to clock net `netName`."""
    net = container.nets.get(netName)
    if net is None or net.isReset:
        return []
    return [consumer.blockPort for consumer in net.consumers
           if consumer.instanceKey == instanceKey]


def declaredPortRow(blockRow, portName):
    """The block's own `ports:`/`registerPorts:`/`addressBlock:` row declaring
    `portName`, or None for a top-down port. Shared with processYaml's
    getBDPortDomain.
    """
    if portName == 'addressBlock':
        return blockRow.get('addressBlock')
    declaredRow = (blockRow.get('ports') or {}).get(portName)
    if declaredRow is None:
        declaredRow = (blockRow.get('registerPorts') or {}).get(portName)
    return declaredRow


def _declaredPortClock(blocks, domains, blockKey, portName):
    """The clock of the block's own declared port `portName`: its clock:, else
    the block default. None when the port is not declared.
    """
    declaredRow = declaredPortRow(blocks[blockKey], portName)
    if declaredRow is None:
        return None
    return declaredRow['clock'] or domains[blockKey].defaultClock


def _fixSentence(fixes):
    """The offered fixes as one sentence: the one fix capitalised, two as
    "Either a or b.", or more as "Either a, b, or c."
    """
    if len(fixes) == 1:
        return fixes[0][0].upper() + fixes[0][1:] + "."
    if len(fixes) == 2:
        return f"Either {fixes[0]} or {fixes[1]}."
    return "Either " + ', '.join(fixes[:-1]) + f", or {fixes[-1]}."


def _reachableInstanceKeys(containers, root):
    """Instance keys under the build's topInstance."""
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


def _drivenBy(net, instanceKey):
    """Whether one of the instance's own outputs drives `net`."""
    return net.driver.kind == 'childOutput' and net.driver.instanceKey == instanceKey


def _consumerNetIndex(container):
    """(instanceKey, blockPort) -> net name, over one container's consumers."""
    index = dict()
    for netName, net in container.nets.items():
        for consumer in net.consumers:
            index[(consumer.instanceKey, consumer.blockPort)] = netName
    return index


def _driverNetIndex(container):
    """(instanceKey, blockPort) of a driving child -> the net it drives, in
    one container.
    """
    return {(net.driver.instanceKey, net.driver.blockPort): netName
           for netName, net in container.nets.items()
           if net.driver.kind == 'childOutput'}


def _routerBusPorts(routerBlockKey, blocks, domains):
    """The router's own bus clock and reset port names: the `addressBlock:`
    clock:/reset:, else the block default clock and its selected reset.
    """
    addressBlockRow = blocks[routerBlockKey]['addressBlock']
    routerDomain = domains[routerBlockKey]
    clockPort = addressBlockRow['clock'] or routerDomain.defaultClock
    resetPort = addressBlockRow['reset'] or routerDomain.selectedReset.get(clockPort)
    return clockPort, resetPort


def _resolveRouterBusClockReset(domains, instances, blocks, consumerNetByContainer,
                                reachableInstances, diag):
    """Set each router's bus port names and its registerClock/registerReset,
    the container nets its bus ports bind to at its one reachable instance. An
    unreachable instance belongs to a child project's standalone harness and is
    ignored. A reachable router declaring more than one clock, or whose bus
    clock has no selected input reset, is rejected here, before the leaves it
    serves look for that reset.
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
            # standalone harness, out of this build's own scope. Either
            # way registerClock/registerReset stay unset.
            continue
        # A generated apbDecode router is single-clock by decision: every
        # flop and port is clocked by the register-bus clock, so a second
        # declared clock would be emitted as a port nothing clocks. Checked
        # ahead of the bus reset, whose advice assumes that one clock.
        if len(domain.clocks) > 1:
            names = ', '.join(f"'{clockName}'" for clockName in domain.clocks)
            diag.logError(f"Register-decode router block '{domain.block}' declares more "
                          f"than one clock ({names}). A router is a single-domain module "
                          f"clocked by the register bus it routes. Declare at most one "
                          f"clock in the router's 'clocks:'. "
                          f"{_diagLoc(diag, blocks[blockKey])}")
        containerKey = instances[instanceKey]['containerKey']
        consumerNet = consumerNetByContainer[containerKey]
        clockPort, resetPort = _routerBusPorts(blockKey, blocks, domains)
        # A stated addressBlock: reset: is a synchronous input, checked in
        # BlockDomains.build(); the clock's selected reset may instead be one
        # of the router's output resets, which the bus does not drive.
        if resetPort is None or domain.resets[resetPort].direction == 'output':
            if resetPort is None:
                cause = f"'{clockPort}' has no selected reset"
                fix = (f"Declare a synchronous input reset on '{clockPort}' "
                       f"in '{domain.block}''s resets:.")
            else:
                cause = (f"the selected reset of '{clockPort}' is "
                         f"'{resetPort}', an output reset of '{domain.block}',")
                fix = (f"Declare an input reset on '{clockPort}' in "
                       f"'{domain.block}''s resets: and mark it default: "
                       f"true, or name an input reset in addressBlock: reset:.")
            diag.logError(
                f"Block '{domain.block}' addressBlock: runs its register bus "
                f"on clock '{clockPort}', but {cause} and addressBlock: names "
                f"no reset:. A router is reset by the register bus it routes, "
                f"and the leaves it serves take that same reset, so the router "
                f"needs an input reset on '{clockPort}'. {fix} "
                f"{_diagLoc(diag, blocks[blockKey]['addressBlock'])}")
        domain.busClockPort = clockPort
        domain.busResetPort = resetPort
        domain.registerClock = consumerNet.get((instanceKey, clockPort))
        domain.registerReset = consumerNet.get((instanceKey, resetPort))


def _resolveRegisterHandlerBinds(domains, containers, instances, connections, blocks,
                                 consumerNetByContainer, reachableInstances,
                                 registerBusPassthroughs, diag):
    """Resolve each routed leaf's register clock/reset (from `registerPorts:`,
    else the ports bound to the serving router's bus), then rename its
    synthesised `<block>_regs` handler's clock/reset onto them and rebind them
    as 'register'. The handler gains one clock/reset pair per clock of a
    regAccess memory it bridges. A passthrough container resolves the same way,
    outermost first. Only reachable instances are resolved.
    """
    instancesByBlock = dict()
    for instanceKey, instRow in instances.items():
        if instanceKey in reachableInstances:
            instancesByBlock.setdefault(instRow['instanceTypeKey'], list()).append(instanceKey)

    resolvedBlocks = set()

    def resolveBlock(blockKey):
        if blockKey in resolvedBlocks:
            return
        resolvedBlocks.add(blockKey)
        block = blocks[blockKey]['block']
        domain = domains[blockKey]
        registerPorts = blocks[blockKey].get('registerPorts')
        if registerPorts:
            portName = next(iter(registerPorts))
            regRow = registerPorts[portName]
            authoredReset = regRow['reset']
            domain.registerClock = regRow['clock'] or domain.defaultClock
            domain.registerReset = authoredReset or domain.selectedReset.get(domain.registerClock)
            domain.registerBusPort = portName
            _checkRegisterPortsOnBus(
                blockKey, block, domain.registerClock,
                authoredReset, domain.registerReset,
                instancesByBlock.get(blockKey, []), instances,
                domains, connections, blocks, consumerNetByContainer,
                registerBusPassthroughs, resolveBlock, diag)
        else:
            _resolveTopDownRegisterPorts(
                blockKey, block, domain,
                instancesByBlock.get(blockKey, []), instances,
                domains, connections, blocks, consumerNetByContainer,
                registerBusPassthroughs, resolveBlock, diag)

    for instanceKey, instRow in instances.items():
        handlerBlockKey = instRow['instanceTypeKey']
        if not domains[handlerBlockKey].isRegHandler:
            continue
        leafBlockKey = instRow['containerKey']
        leafDomain = domains[leafBlockKey]
        leafContainer = containers[leafBlockKey]
        handlerDomain = domains[handlerBlockKey]
        # A synthesised handler block declares neither clocks: nor resets:,
        # so BlockDomains.build() always gives it exactly the implicit
        # clk/rst_n pair.
        handlerClockName = next(iter(handlerDomain.clocks))
        handlerResetName = next(iter(handlerDomain.resets))

        resolveBlock(leafBlockKey)

        # The handler's OWN registerClock/registerReset (read by
        # getBDBusClockReset for the handler's own view) is the same net as
        # the leaf's: inside the leaf's own container, the leaf's selected
        # register port NAME already IS that net name.
        handlerDomain.registerClock = leafDomain.registerClock
        handlerDomain.registerReset = leafDomain.registerReset

        # Rename the handler's implicit clock/reset pair to the leaf's own
        # register clock/reset names: the handler's ports take the leaf's
        # own clock/reset names so that a bridged memory (below) declared on
        # a block clock actually named 'clk' cannot collide with the
        # handler's bus pair. The rename makes
        # busClockPort/busResetPort (below) equal registerClock/
        # registerReset: every handler port is named after the leaf net it
        # binds to.
        clockDecl = handlerDomain.clocks.pop(handlerClockName)
        handlerDomain.clocks[leafDomain.registerClock] = clockDecl
        handlerDomain.defaultClock = leafDomain.registerClock
        _rebindConsumer(leafContainer, instanceKey, handlerClockName,
                        leafDomain.registerClock, 'register')

        resetName = handlerResetName
        if leafDomain.registerReset is not None:
            # The reset renames alongside the clock. If it is None,
            # the check later in the module-level build() that a register
            # bus clock has a selected reset rejects the design, so the reset
            # entry is left under its implicit name rather than renamed to
            # nothing; it is still retargeted to the bus clock after this
            # block.
            resetDecl = handlerDomain.resets.pop(handlerResetName)
            handlerDomain.resets[leafDomain.registerReset] = resetDecl
            resetName = leafDomain.registerReset
            _rebindConsumer(leafContainer, instanceKey, handlerResetName,
                            leafDomain.registerReset, 'register')
        handlerDomain.resets[resetName].clock = leafDomain.registerClock
        handlerDomain.selectedReset = {leafDomain.registerClock: resetName}
        handlerDomain.busClockPort = leafDomain.registerClock
        handlerDomain.busResetPort = resetName

        # The bridge: every regAccess memory of
        # the leaf whose own clock differs from the register bus clock gets
        # its own clock/reset port pair on the handler, bound onto the
        # leaf's own net of that same name (the leaf's own clock/reset
        # declarations are already nets of leafContainer, as the bus pair
        # above already relies on). A memory with no reset on its clock is
        # rejected by build()'s reset check instead of bridged here, and two
        # memories on the same clock resolving to different resets is
        # likewise rejected there rather than silently picking one. Order
        # follows the leaf's own clock declaration order, never memory
        # iteration order, so regenerating after an unrelated memory edit
        # does not reshuffle the handler's port list.
        bridgedResetByClock = dict()
        for memDomain in leafDomain.memories:
            if (memDomain.regAccess and memDomain.clock != leafDomain.registerClock
                    and memDomain.reset is not None
                    and memDomain.clock not in bridgedResetByClock):
                bridgedResetByClock[memDomain.clock] = memDomain.reset
        for clockName in leafDomain.clocks:
            if clockName not in bridgedResetByClock:
                continue
            bridgedResetName = bridgedResetByClock[clockName]
            leafClockDecl = leafDomain.clocks[clockName]
            handlerDomain.clocks[clockName] = ClockDecl(
                desc=leafClockDecl.desc, direction='input', default=False,
                period=leafClockDecl.period, timeUnit=leafClockDecl.timeUnit)
            leafResetDecl = leafDomain.resets[bridgedResetName]
            handlerDomain.resets[bridgedResetName] = ResetDecl(
                desc=leafResetDecl.desc, direction='input', default=False,
                clock=clockName, isAsync=False, clockStated=False)
            handlerDomain.selectedReset[clockName] = bridgedResetName
            _rebindConsumer(leafContainer, instanceKey, clockName, clockName,
                            'register')
            _rebindConsumer(leafContainer, instanceKey, bridgedResetName,
                            bridgedResetName, 'register')


def _rebindConsumer(container, instanceKey, oldBlockPort, newBlockPort, kind):
    """Move (instanceKey, oldBlockPort)'s consumer onto the net `newBlockPort`,
    under that name: a handler's port is named after the leaf net it binds.
    """
    for net in container.nets.values():
        net.consumers = [consumer for consumer in net.consumers
                         if not (consumer.instanceKey == instanceKey
                                 and consumer.blockPort == oldBlockPort)]
    container.nets[newBlockPort].consumers.append(Consumer(instanceKey, newBlockPort, kind))


def _servingRouterBusNets(leafInstanceKey, instances, domains, connections, blocks,
                          consumerNetByContainer, registerBusPassthroughs, resolveBlock):
    """(consumerNet, busClockNet, busResetNet, registerBusPort) for the
    register-bus feed reaching this instance: from a router in its own
    container, else from the passthrough container whose inner instance it is.
    """
    instRow = instances[leafInstanceKey]
    containerKey = instRow['containerKey']
    consumerNet = consumerNetByContainer[containerKey]
    routerInstanceKey = None
    for connRow in connections.values():
        if connRow['dstKey'] != leafInstanceKey:
            continue
        srcInstRow = instances[connRow['srcKey']]
        if domains[srcInstRow['instanceTypeKey']].isRouter:
            routerInstanceKey = connRow['srcKey']
            break
    if routerInstanceKey is not None:
        routerBlockKey = instances[routerInstanceKey]['instanceTypeKey']
        routerClockPort, routerResetPort = _routerBusPorts(routerBlockKey, blocks, domains)
        busClockNet = consumerNet.get((routerInstanceKey, routerClockPort))
        busResetNet = consumerNet.get((routerInstanceKey, routerResetPort))
        registerBusPort = next(end['portName'] for end in connRow['ends'].values()
                               if end['instanceKey'] == leafInstanceKey)
        return consumerNet, busClockNet, busResetNet, registerBusPort

    passthrough = registerBusPassthroughs[containerKey]
    resolveBlock(containerKey)
    containerDomain = domains[containerKey]
    return (consumerNet, containerDomain.registerClock,
            containerDomain.registerReset, passthrough['innerPortName'])


def _checkRegisterPortsOnBus(leafBlockKey, leafBlock, clockPortName, authoredReset, resetPortName,
                             leafInstanceKeys, instances, domains,
                             connections, blocks, consumerNetByContainer,
                             registerBusPassthroughs, resolveBlock, diag):
    """For a leaf with `registerPorts:`, each instance's register clock must
    bind to the serving router's bus clock. The reset is checked only when
    `registerPorts:` authors `reset:`; otherwise the leaf's own selected reset
    stands.
    """
    for leafInstanceKey in leafInstanceKeys:
        instRow = instances[leafInstanceKey]
        consumerNet, busClockNet, busResetNet, _ = _servingRouterBusNets(
            leafInstanceKey, instances, domains, connections, blocks,
            consumerNetByContainer, registerBusPassthroughs, resolveBlock)
        if consumerNet.get((leafInstanceKey, clockPortName)) != busClockNet:
            diag.logError(
                f"Instance '{instRow['instance']}' of block '{leafBlock}' "
                f"declares its register port on clock '{clockPortName}', but "
                f"that is not bound to the same container clock as the "
                f"serving router's own bus clock. A register port must run "
                f"on the register bus clock. Bind '{clockPortName}' to the "
                f"router's bus clock in the instance's clocks: map, or change "
                f"the registerPorts: clock:.")
        if authoredReset and busResetNet is not None \
                and consumerNet.get((leafInstanceKey, resetPortName)) != busResetNet:
            diag.logError(
                f"Instance '{instRow['instance']}' of block '{leafBlock}' "
                f"declares its register port's reset as '{resetPortName}' "
                f"(registerPorts: reset:), but that is not bound to the "
                f"same container reset as the serving router's own bus "
                f"reset. A register port's reset must be the register bus "
                f"reset. Bind '{resetPortName}' to the router's bus reset in "
                f"the instance's resets: map, or change the registerPorts: "
                f"reset:.")


def _resolveTopDownRegisterPorts(leafBlockKey, leafBlock, leafDomain, leafInstanceKeys,
                                 instances, domains, connections, blocks,
                                 consumerNetByContainer, registerBusPassthroughs,
                                 resolveBlock, diag):
    """For a block with no `registerPorts:`, a top-down leaf or a passthrough
    container: find the clock and reset ports bound to the serving router's bus
    clock and selected reset. Every instance must agree, since the block is
    generated once; the result is stored on `leafDomain`.
    """
    results = list()
    # The block's own register-bus port: config/postParseRegisterPorts.py
    # names it once per block, so every instance's feed lands on the same
    # port and the first instance's name is the block's.
    registerBusPort = None
    for leafInstanceKey in leafInstanceKeys:
        instRow = instances[leafInstanceKey]
        consumerNet, busClockNet, busResetNet, servedRegisterBusPort = _servingRouterBusNets(
            leafInstanceKey, instances, domains, connections, blocks,
            consumerNetByContainer, registerBusPassthroughs, resolveBlock)
        if registerBusPort is None:
            registerBusPort = servedRegisterBusPort

        clockPortName = None
        for name, clockDecl in leafDomain.clocks.items():
            if clockDecl.direction == 'input' and consumerNet.get((leafInstanceKey, name)) == busClockNet:
                clockPortName = name
                break
        if clockPortName is None:
            diag.logError(
                f"Instance '{instRow['instance']}' of block '{leafBlock}' "
                f"needs a register-bus port, but none of its declared clock "
                f"ports is bound to the register bus's clock, and the "
                f"register port runs on that clock. Bind one "
                f"of '{leafBlock}''s clock ports, in its clocks: map, to the "
                f"same container clock the serving router's own bus clock "
                f"is bound to.")
            continue

        resetPortName = None
        for name, resetDecl in leafDomain.resets.items():
            if (resetDecl.direction == 'input' and not resetDecl.isAsync
                    and consumerNet.get((leafInstanceKey, name)) == busResetNet):
                resetPortName = name
                break
        if resetPortName is None:
            diag.logError(
                f"Instance '{instRow['instance']}' of block '{leafBlock}' "
                f"needs a register-bus port, but none of its declared reset "
                f"ports is bound to the register bus's selected reset, and "
                f"the register port uses that reset. "
                f"Bind one of '{leafBlock}''s reset ports, in its resets: "
                f"map, to that same container reset.")
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
            f"({pairNames}): {names}. Every instance must use the same "
            f"clock/reset pair for its register port. Bind the same clock "
            f"and reset ports to the register bus in every instance's "
            f"clocks:/resets: map.")
        return
    leafDomain.registerClock, leafDomain.registerReset = next(iter(pairs))
    leafDomain.registerBusPort = registerBusPort


def _checkMemoryAccessorDomains(domains, containers, instances, memoryConnections,
                                consumerNetByContainer, driverNetByContainer,
                                scopeInstances, diag):
    """A memoryConnections accessor must run on the memory's clock: its default
    clock, mapped through its instance, is the memory's clock mapped through the
    owning instance. The accessor is a child inside the owning block or a
    sibling of an owning instance, checked against every such instance; any
    other accessor is reported. That the accessor's block has a default clock
    depends only on the block, so it is checked for every accessor instance of
    a memory with a clock; the domain match and placement are checked only for
    accessor and owning instances in `scopeInstances`.
    """
    instancesByBlock = dict()
    for instanceKey, instRow in instances.items():
        if instanceKey in scopeInstances:
            instancesByBlock.setdefault(instRow['instanceTypeKey'], list()).append(instanceKey)
    # A row with no instance is a local-mode connection of the owning block
    # itself, with no accessor instance to check.
    memConnectionsByMemory = dict()
    for row in memoryConnections.values():
        if row['instanceKey']:
            memConnectionsByMemory.setdefault(row['memoryBlockKey'], list()).append(row)

    def checkAccessor(accessorInstanceKey, accessorInstRow, consumerNet, memoryNet, memDomain, domain):
        accessorClockName = domains[accessorInstRow['instanceTypeKey']].defaultClock
        accessorNet = consumerNet[(accessorInstanceKey, accessorClockName)]
        if accessorNet != memoryNet:
            diag.logError(
                f"Instance '{accessorInstRow['instance']}' accesses memory "
                f"'{memDomain.memory}' of block '{domain.block}' over clock "
                f"'{accessorNet}', but the memory is on '{memoryNet}'. "
                f"A hardware accessor of a memory must be in the memory's "
                f"own domain. Bind the accessor's default clock to "
                f"'{memoryNet}'.")

    for blockKey, domain in domains.items():
        for memDomain in domain.memories:
            if not memDomain.clock:
                continue  # no clock at all: reported by ClockTree.check()
            accessorRows = memConnectionsByMemory.get(memDomain.memoryBlockKey, [])
            for row in accessorRows:
                accessorInstRow = instances[row['instanceKey']]
                accessorDomain = domains[accessorInstRow['instanceTypeKey']]
                if accessorDomain.defaultClock is None:
                    diag.logError(
                        f"Instance '{accessorInstRow['instance']}' of block "
                        f"'{accessorDomain.block}' accesses memory "
                        f"'{memDomain.memory}' of block '{domain.block}', but "
                        f"'{accessorDomain.block}' has no default clock (every "
                        f"declared clock is direction: output). A memory "
                        f"accessor takes its block's default clock. Give "
                        f"'{accessorDomain.block}' an input clock.")
            accessorRows = [row for row in accessorRows
                            if row['instanceKey'] in scopeInstances]
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
                    # its own container clock. A memory on an output clock of
                    # its owner is on the net that output drives.
                    consumerNet = consumerNetByContainer[accessorContainerKey]
                    isOutputClock = domain.clocks[memDomain.clock].direction == 'output'
                    ownerNet = (driverNetByContainer if isOutputClock
                                else consumerNetByContainer)[accessorContainerKey]
                    for ownerInstanceKey in ownerInstanceKeys:
                        if (ownerInstanceKey, memDomain.clock) in containers[accessorContainerKey].unconnectedOutputs:
                            ownerInstance = instances[ownerInstanceKey]['instance']
                            diag.logError(
                                f"Instance '{accessorInstRow['instance']}' accesses "
                                f"memory '{memDomain.memory}' of block "
                                f"'{domain.block}', which is on output clock "
                                f"'{memDomain.clock}' of the owning instance "
                                f"'{ownerInstance}', but '{ownerInstance}' binds "
                                f"'{memDomain.clock}' to `~`, so no accessor "
                                f"outside it can be in the memory's domain. A "
                                f"hardware accessor of a memory must be in the "
                                f"memory's own domain. Bind '{memDomain.clock}' "
                                f"of instance '{ownerInstance}' to a net in its "
                                f"clocks: map, and bind the accessor's default "
                                f"clock to that net.")
                        checkAccessor(accessorInstanceKey, accessorInstRow, consumerNet,
                                     ownerNet[(ownerInstanceKey, memDomain.clock)],
                                     memDomain, domain)
                    continue
                diag.logError(
                    f"Instance '{accessorInstRow['instance']}' accesses memory "
                    f"'{memDomain.memory}' of block '{domain.block}', but it shares "
                    f"neither the owning block's own body nor a container of one of "
                    f"the owning block's own instances, so their container clocks "
                    f"cannot be compared. A hardware accessor of a memory must "
                    f"be a sibling of the memory's owning instance, or a child "
                    f"instance directly inside the memory's own owning block. "
                    f"Move the accessor next to an owning instance, or inside "
                    f"the owning block.")


def _checkSupplyGraph(domains, containers, instances, blocks, diag):
    """For each output a block itself produces, an edge runs from each of its
    input clocks and resets, asynchronous ones included. An exported output
    adds no edge of its own: the inner child driving it does, so only the
    container inputs that inner chain reaches feed it. Every supplied net must
    trace back to a testbench net or a root (a block with no inputs); a net
    that does not is on a cycle, which is reported. A container's declared
    input is a stopping point: the top's inputs are bound to the testbench or
    already rejected.
    """
    consumerNetByContainer = {key: _consumerNetIndex(c) for key, c in containers.items()}

    def ownInputNames(blockKey):
        domain = domains[blockKey]
        return ([name for name, clockDecl in domain.clocks.items() if clockDecl.direction == 'input']
               + [name for name, resetDecl in domain.resets.items() if resetDecl.direction == 'input'])

    # The container's own declared inputs each net reaches.
    resolved = dict()
    visiting = list()

    def reachesAll(containerKey, netNames):
        # Every candidate is visited, never short-circuited: reaches() reports
        # a cycle as a side effect, and stopping at the first candidate that
        # answers would make that report depend on iteration order.
        inputs = set()
        for name in netNames:
            inputs |= reaches(containerKey, name)
        return inputs

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
            diag.logError("Supply cycle: every supplied clock or reset must "
                          "trace back to a testbench net or a block with no "
                          "inputs, but these nets supply each other. Drive one "
                          "of them from outside the cycle: " + ' -> '.join(hops))
            return set()
        visiting.append(key)
        net = containers[containerKey].nets[netName]
        if net.driver.kind == 'environment':
            result = set()
        elif net.driver.kind == 'input':
            result = {netName}
        elif net.driver.kind == 'ownImplementation':
            result = reachesAll(containerKey, ownInputNames(containerKey))
        else:  # 'childOutput'
            supplierInstanceKey = net.driver.instanceKey
            supplierBlockKey = instances[supplierInstanceKey]['instanceTypeKey']
            inputs = ownInputNames(supplierBlockKey)
            supplier = containers.get(supplierBlockKey)
            if supplier is not None and supplier.nets[net.driver.blockPort].driver.kind == 'childOutput':
                innerInputs = reaches(supplierBlockKey, net.driver.blockPort)
                inputs = [name for name in inputs if name in innerInputs]
            if not inputs:
                result = set()  # an oscillator, or an export fed by one
            else:
                consumerNet = consumerNetByContainer[containerKey]
                # Declaration order, deduplicated (dict.fromkeys keeps first
                # occurrence order; a plain set would iterate in a hash order
                # randomised per process).
                supplyNets = list(dict.fromkeys(
                    consumerNet[(supplierInstanceKey, name)] for name in inputs))
                result = reachesAll(containerKey, supplyNets)
        visiting.pop()
        resolved[key] = result
        return result

    for containerKey, container in containers.items():
        for netName, net in container.nets.items():
            if net.driver.kind in ('ownImplementation', 'childOutput'):
                reaches(containerKey, netName)


def _resolveAllInstances(root, containers, domains, instances):
    """The resolved net of every reachable instance's block clocks and resets:
    bindings followed upward through input ports to a testbench net, stopping at
    a local net or a supplier's output. Walked top-down because one block may be
    reached by several paths, and one declared instance inside a reused
    container is reached once per occurrence of that container. Returns
    `{instanceKey: [(path, {blockPort: resolved}), ...]}`, one entry per
    occurrence, where `path` is the dotted hierarchical instance path and
    `resolved` is `('testbench', name)` or `('supplied', instanceKey,
    blockPort)`.
    """
    resolvedByInstance = dict()

    def walk(container, ownNetResolved, pathPrefix):
        consumerNet = _consumerNetIndex(container)
        for instanceKey, childKey in container.instances.items():
            childDomain = domains[childKey]
            path = pathPrefix + instances[instanceKey]['instance']
            resolvedPorts = dict()
            for name, clockDecl in childDomain.clocks.items():
                if clockDecl.direction == 'input':
                    resolvedPorts[name] = ownNetResolved[consumerNet[(instanceKey, name)]]
                else:
                    resolvedPorts[name] = ('supplied', instanceKey, name)
            for name, resetDecl in childDomain.resets.items():
                if resetDecl.direction == 'input':
                    resolvedPorts[name] = ownNetResolved[consumerNet[(instanceKey, name)]]
                else:
                    resolvedPorts[name] = ('supplied', instanceKey, name)
            resolvedByInstance.setdefault(instanceKey, list()).append((path, resolvedPorts))

            childContainer = containers.get(childKey)
            if childContainer is None:
                continue
            # The resolved value of every net INSIDE childContainer, handed
            # down one level further: a declared INPUT net's own resolution
            # is exactly the resolution just computed for the block clock of
            # the same name (a container's declared clocks/resets ARE its
            # own block's clocks/resets); a LOCAL net or a declared OUTPUT a
            # child drives is itself a 'supplied' stop, at the driving
            # grandchild's own instance and port, never chased further; a
            # declared OUTPUT the
            # container's OWN implementation drives (no child does) is a
            # 'supplied' stop at this instance itself, the same as an
            # oscillator's own output.
            childNetResolved = dict()
            for netName, net in childContainer.nets.items():
                if net.kind == 'declared' and net.driver.kind == 'input':
                    childNetResolved[netName] = resolvedPorts[netName]
                elif net.driver.kind == 'childOutput':
                    childNetResolved[netName] = ('supplied', net.driver.instanceKey, net.driver.blockPort)
                elif net.driver.kind == 'ownImplementation':
                    childNetResolved[netName] = ('supplied', instanceKey, netName)
                # 'environment' never occurs below root.
            walk(childContainer, childNetResolved, path + '.')

    rootResolved = {name: ('testbench', name) for name in root.nets}
    walk(root, rootResolved, '')
    return resolvedByInstance


def _resolveStandaloneAttrs(domains, blocks, instances, resolvedByInstance,
                            testbenchClocks, testbenchResets,
                            contextOwningProject, rootProjectName, diag):
    """Standalone simulation attributes: each input clock's period/timeUnit
    from its declaration, else from the one testbench clock every instance in
    the declaring project resolves to; each input reset's releaseCycles
    likewise. An unresolvable value takes the project's default testbench
    clock/reset. Filled for every block; an unresolvable value is reported only
    for a `hasVl` block in its declaring project.
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
    # every project must have exactly one default clock and reset.
    _defaultTestbenchClock = next(row for row in testbenchClocks.values() if row['default'])
    _defaultTestbenchReset = next(row for row in testbenchResets.values() if row['default'])

    def instanceResolutions(blockKey, portName):
        """(path, resolved) for each occurrence of each instance of the
        block in this build.
        """
        return [(path, resolvedPorts[portName])
                for instanceKey in instanceKeysByBlock.get(blockKey, [])
                for path, resolvedPorts in resolvedByInstance[instanceKey]]

    def testbenchNetOf(resolutions):
        """The one testbench net every entry of `resolutions` resolves to,
        or None (no instance, a resolution that is not a testbench net, or a
        disagreement)."""
        if not resolutions:
            return None
        nets = set()
        for _, resolved in resolutions:
            if resolved[0] != 'testbench':
                return None
            nets.add(resolved[1])
        return next(iter(nets)) if len(nets) == 1 else None

    def unresolvedPeriodCause(resolutions):
        """Why a clock or reset did not resolve, naming the instances: no
        instance, a supplier's output, or disagreement.
        """
        if not resolutions:
            return "it has no instance in its own declaring project."
        supplierNames = [path for path, r in resolutions if r[0] == 'supplied']
        if supplierNames:
            return (f"instance(s) {', '.join(supplierNames)} resolve it to a "
                    f"supplier's output, not a testbench net.")
        pairs = ', '.join(f"{path}={r[1]}" for path, r in resolutions)
        return f"its instances disagree: {pairs}."

    for blockKey, domain in domains.items():
        blockRow = blocks[blockKey]
        evaluate = contextOwningProject[blockRow['_context']] == rootProjectName
        # The missing-period check is scoped to the block's own declaring
        # project: an assembler never re-evaluates it, so a hasVl block this
        # build only INSTANTIATES
        # (evaluate is False) reports nothing here, even when its own
        # declaring project's build would find a genuine violation.
        reportMissingPeriod = bool(blockRow['hasVl']) and evaluate

        for name, clockDecl in domain.clocks.items():
            if clockDecl.direction != 'input':
                continue
            if clockDecl.period:
                domain.resolvedPeriod[name] = clockDecl.period
                domain.resolvedTimeUnit[name] = clockDecl.timeUnit
                continue
            resolutions = instanceResolutions(blockKey, name) if evaluate else []
            testbenchNet = testbenchNetOf(resolutions)
            if testbenchNet is not None:
                domain.resolvedPeriod[name] = testbenchClocks[testbenchNet]['period']
                domain.resolvedTimeUnit[name] = testbenchClocks[testbenchNet]['timeUnit']
                continue
            if reportMissingPeriod:
                diag.logError(
                    f"Block '{domain.block}' clock '{name}' declares no period: "
                    f"and does not resolve to one testbench clock through every "
                    f"instance of the block in its own declaring project: "
                    f"{unresolvedPeriodCause(resolutions)} A standalone build needs a "
                    f"period for every input clock. Declare period: on '{name}', or "
                    f"make every instance's binding resolve to the same "
                    f"testbench clock.")
            domain.resolvedPeriod[name] = _defaultTestbenchClock['period']
            domain.resolvedTimeUnit[name] = _defaultTestbenchClock['timeUnit']

        for name, resetDecl in domain.resets.items():
            if resetDecl.direction != 'input':
                continue
            if resetDecl.isAsync:
                # An asynchronous reset input counts its release cycles on
                # the block DEFAULT clock's edges (it belongs to no clock of
                # its own), so the block must have one. The release
                # COUNT still follows the reset's own
                # binding, the same rule as any other reset: it is bound to
                # some net (by map or name match) independently of clock
                # membership, and that binding is what resolvedByInstance
                # already computed for it above.
                if domain.defaultClock is None and reportMissingPeriod:
                    diag.logError(
                        f"Block '{domain.block}' asynchronous reset input "
                        f"'{name}' counts its release cycles on the block "
                        f"default clock, but '{domain.block}' has no default "
                        f"clock that is an input. Give '{domain.block}' a "
                        f"default input clock.")
            resolutions = instanceResolutions(blockKey, name) if evaluate else []
            testbenchNet = testbenchNetOf(resolutions)
            if testbenchNet is not None:
                domain.resolvedReleaseCycles[name] = testbenchResets[testbenchNet]['releaseCycles']
                continue
            # An async reset's own clock is '' (it belongs to no clock);
            # the "declares period" fallback it shares with an ordinary
            # reset applies to the clock it is actually counted on instead -
            # the block default clock (already checked above).
            ownClock = domain.defaultClock if resetDecl.isAsync else resetDecl.clock
            ownClockDeclaresPeriod = (ownClock is not None
                                     and bool(domain.clocks[ownClock].period))
            if not ownClockDeclaresPeriod and reportMissingPeriod:
                diag.logError(
                    f"Block '{domain.block}' reset '{name}' does not resolve to "
                    f"one testbench reset through every instance of the block "
                    f"in its own declaring project, and its own clock declares "
                    f"no period: value. {unresolvedPeriodCause(resolutions)} Declare period: "
                    f"on that clock, or make every instance's binding resolve "
                    f"to the same testbench reset.")
            domain.resolvedReleaseCycles[name] = _defaultTestbenchReset['releaseCycles']
