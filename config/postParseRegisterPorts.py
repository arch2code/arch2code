"""New-schema post-parse pass for register-bus distribution.

Activated when at least one block declares `addressBlock:`; a no-op
otherwise. This is the sole register-bus distribution pass. The
register-bus interface and per-router attributes come exclusively from
per-block `addressBlock:` / `registerPorts:` declarations.

Responsibilities:
  1. Build the router index from `prj.flatData['blocks']` rows that
     carry `addressBlock:`.
  2. Resolve the router instance per group via container-locality.
  3. Infer the primary router by hierarchy walk.
  4. Synthesise the `<block>_regs` handler block, instance, and
     leaf-to-handler `connectionMap` per routed leaf via the
     `synthesiseRegHandler` helper defined in this module.
  5. Emit the router-to-leaf connection per routed instance, with the
     interface sourced from the leaf's `registerPorts:` entry.
  6. Emit the parent-router-to-child-router connection per nested
     router.
  7. Resolve, by fixed point, every router-less container that passes
     the register bus to exactly one consumer: a leaf, a
     `registerPorts:` IP, or another such container. Dispatch to the
     container as to a leaf and bridge its boundary port inward with
     one `connectionMap` per chain level.
  8. Tag synthesised binds with their owning block's YAML context by
     feeding them through `processSingleFile(ownerContext, ...)` per
     owner, never `_global`.

The script bypasses the dispatcher's `_global` re-feed by calling
`prj.processSingleFile(...)` directly per owner context and returning
None.
"""

from pysrc.arch2codeHelper import printError, warningAndErrorReport
from pysrc.processYaml import camelCase, qualifiedKeyContext


def regHandlerNaming(prj):
    """Resolve the regBlockNaming policy that governs synthesised
    register-handler block and instance names. Returns
    (instance_prefix, block_suffix, camel_case).
    """
    file_gen = prj.a2cProj.get('fileGeneration', {})
    proj_file_gen = prj.proj.get('fileGeneration', {})
    regBlockNaming = proj_file_gen.get('regBlockNaming', file_gen.get('regBlockNaming', {}))
    instance_prefix = regBlockNaming.get('instancePrefix', 'u_')
    block_suffix = regBlockNaming.get('blockSuffix', '_regs')
    camel_case = regBlockNaming.get('camelCase', False)
    return instance_prefix, block_suffix, camel_case


def collectBlocksNeedingRegHandler(prj):
    """Return {blockKey: block} for every leaf block that owns
    registers or regAccess memories and therefore needs a synthesised
    <block>_regs handler.
    """
    blocksWithRegisters = dict()
    for registerData in prj.flatData['registers'].values():
        if registerData['blockKey'] not in blocksWithRegisters:
            blocksWithRegisters[registerData['blockKey']] = registerData['block']
    blocksWithMemories = dict()
    for memoryData in prj.flatData['memories'].values():
        if memoryData['regAccess'] and memoryData['blockKey'] not in blocksWithMemories:
            blocksWithMemories[memoryData['blockKey']] = memoryData['block']
    blocksNeedingConnections = blocksWithRegisters.copy()
    blocksNeedingConnections.update(blocksWithMemories)
    return blocksNeedingConnections


def synthesiseRegHandler(prj, block_key, block, reg_interface, blockInfo,
                         instance_prefix, block_suffix, camel_case,
                         parentParams):
    """Build the synthesised register-handler block, instance, and
    leaf-to-handler connectionMap for a single routed leaf block.

    parentParams is the list of the leaf block's parameter names; the
    handler inherits them so it emits module parameters and selects the
    leaf's module-local parameterizable declarations (its register/memory
    storage is variant-width, sized by these params).

    Returns (reg_block, block_def, instance_name, instance_def, connection_map).
    """
    reg_block = block + block_suffix
    has_mdl = len(prj.hierKey.get(block_key, [])) > 0
    instance_name = camelCase(instance_prefix, reg_block) if camel_case else instance_prefix + reg_block
    block_def = {
        'desc': block + ' Register handler',
        'isRegHandler': True,
        'hasVl': False,
        'hasRtl': True,
        'hasMdl': has_mdl,
        'hasTb': False,
        'hasSkt': False,
        'dir': blockInfo.get(block_key, {}).get('dir', ''),
        'params': parentParams,
    }
    instance_def = {
        'instanceType': reg_block,
        'container': block,
    }
    connection_map = {
        'interface': reg_interface,
        'block': block,
        'direction': 'dst',
        'instance': instance_name,
    }
    return reg_block, block_def, instance_name, instance_def, connection_map


def _exit_with_error(msg):
    printError(msg)
    exit(warningAndErrorReport())


def _collectRouterBlocks(blockInfo):
    """Return {routerBlockKey: routerBlockRow} for every block whose
    `addressBlock:` is populated."""
    return {
        blockKey: row
        for blockKey, row in blockInfo.items()
        if row.get('addressBlock')
    }


def _resolveRouterInstances(prj, routers, reachable):
    """Resolve the single router instance per router block within the active
    build's design hierarchy. Router instances that belong only to a
    referenced project's standalone harness (not reachable from this build's
    topInstance) are not part of this dispatch tree and are skipped. Multi-
    instance routers are diagnosed here."""
    router_instance = dict()
    for instRow in prj.flatData['instances'].values():
        if instRow['instanceKey'] not in reachable:
            continue
        instanceTypeKey = instRow['instanceTypeKey']
        if instanceTypeKey not in routers:
            continue
        if instanceTypeKey in router_instance:
            prior = router_instance[instanceTypeKey]
            router_block_name = routers[instanceTypeKey]['block']
            _exit_with_error(
                f"Router block '{router_block_name}' has multiple "
                f"instances ('{prior['instance']}' in "
                f"'{prior['containerKey']}', "
                f"'{instRow['instance']}' in "
                f"'{instRow['containerKey']}'). Multi-instance "
                f"routers are not supported by the new "
                f"addressBlock: schema."
            )
        router_instance[instanceTypeKey] = instRow
    return router_instance


def _findRouterParent(prj, childRouterInstRow, decoderContainer, reachable):
    """Walk up from a router instance's containerKey to locate the
    parent router that serves the router's container block. Only instances
    within the active build's design hierarchy are considered."""
    routerContainerBlockKey = childRouterInstRow['containerKey']
    for instRow in prj.flatData['instances'].values():
        if instRow['instanceKey'] not in reachable:
            continue
        if instRow['instanceTypeKey'] != routerContainerBlockKey:
            continue
        ancestor_container = instRow['containerKey']
        candidate = decoderContainer.get(ancestor_container)
        if candidate is not None and candidate is not childRouterInstRow:
            return candidate
    return None


def _findRouterlessAncestorContainer(prj, childRouterInstRow, decoderContainer,
                                     topBlockKeys, reachable):
    """Find a reachable instance of the router's container block that
    itself sits in a router-less, non-root container. `_findRouterParent`
    does not walk this far, and passthrough synthesis does not support
    this shape either.

    Returns that instance row, or None when the router's container is
    at the design root or in a container a router serves.
    """
    routerContainerBlockKey = childRouterInstRow['containerKey']
    for instRow in prj.flatData['instances'].values():
        if instRow['instanceKey'] not in reachable:
            continue
        if instRow['instanceTypeKey'] != routerContainerBlockKey:
            continue
        if instRow['container'] == '_topInstance':
            continue
        ancestor_container = instRow['containerKey']
        if ancestor_container in decoderContainer or ancestor_container in topBlockKeys:
            continue
        return instRow
    return None


def _findPrimaryRouter(prj, routers, router_instance, reachable, topBlockKeys):
    """Infer the primary router by hierarchy walk. Errors if zero or
    more than one candidate is found."""
    decoderContainer = {
        routerInstRow['containerKey']: routerInstRow
        for routerInstRow in router_instance.values()
    }

    primary_candidates = []
    for routerInstRow in router_instance.values():
        parent_router = _findRouterParent(prj, routerInstRow, decoderContainer, reachable)
        if parent_router is None:
            primary_candidates.append(routerInstRow)

    if len(primary_candidates) == 0:
        names = ', '.join(
            f"{r['instance']} (block {r['instanceType']})"
            for r in router_instance.values()
        )
        _exit_with_error(
            f"No primary router could be inferred. Every router-block "
            f"instance is contained by another router's served scope: "
            f"{names}. Exactly one router must be the dispatch-tree "
            f"root."
        )

    if len(primary_candidates) > 1:
        blockInfo = prj.flatData['blocks']
        offenders = []
        for routerInstRow in primary_candidates:
            ancestorInstRow = _findRouterlessAncestorContainer(
                prj, routerInstRow, decoderContainer, topBlockKeys, reachable)
            if ancestorInstRow is not None:
                offenders.append((routerInstRow, ancestorInstRow))
        if offenders:
            childInstRow, ancestorInstRow = offenders[0]
            ancestorBlockRow = blockInfo[ancestorInstRow['containerKey']]
            hostBlockRow = blockInfo[childInstRow['containerKey']]
            offenderKeys = {r['instanceKey'] for r, _ in offenders}
            dispatchers = [
                r for r in primary_candidates if r['instanceKey'] not in offenderKeys
            ]
            if len(dispatchers) == 1:
                dispatchContainerBlock = blockInfo[dispatchers[0]['containerKey']]['block']
                fix = (
                    f"Move '{ancestorInstRow['instance']}' into "
                    f"'{dispatchContainerBlock}', or add an addressBlock: "
                    f"router to '{ancestorBlockRow['block']}'."
                )
            else:
                fix = f"Add an addressBlock: router to '{ancestorBlockRow['block']}'."
            _exit_with_error(
                f"Nested router '{childInstRow['instance']}' (block "
                f"'{childInstRow['instanceType']}') is hosted by block "
                f"'{hostBlockRow['block']}', whose instance "
                f"'{ancestorInstRow['instance']}' sits in router-less "
                f"container '{ancestorBlockRow['block']}'. A nested "
                f"router's container must be instantiated directly in "
                f"the container of the router that dispatches to it; "
                f"passing the register bus through a router-less "
                f"container to a nested router is not supported. {fix}"
            )

        names = ', '.join(
            f"{r['instance']} (block {r['instanceType']})"
            for r in primary_candidates
        )
        _exit_with_error(
            f"Multiple candidate primary routers: {names}. Exactly "
            f"one router must be the dispatch-tree root; other "
            f"routers must be nested under it."
        )

    return primary_candidates[0]


def _leafRegisterBinding(prj, leafBlock, servingRouter, addressBusTypes,
                         routerInterfaceCache):
    """Resolve a routed leaf's register-bus binding as
    (portName, interfaceName, ifaceRow, ifaceContext, authored).

    A reusable IP block authors its own register-bus surface in
    `registerPorts:` and is the only kind that must declare it; the
    authored row carries the leaf-local interface so `<block>Base.h`
    stays self-contained across the projects that instantiate the IP.

    A top-down leaf authors no register port and infers its
    register-bus interface and canonical port from the serving router's
    addressBlock declaration. `authored` distinguishes the two so
    callers run the cross-interface compatibility check only when the
    leaf names its own interface.

    Multiple registerPorts: rows are rejected by the block parse hook."""
    registerPorts = leafBlock.get('registerPorts')
    if registerPorts:
        portName = next(iter(registerPorts.keys()))
        regPortRow = registerPorts[portName]
        leafIfaceKey = regPortRow['interfaceKey']
        leafIfaceContext = qualifiedKeyContext(
            regPortRow['interface'], leafIfaceKey, 'registerPorts interface')
        leafIfaceRow = prj.flatData['interfaces'][leafIfaceKey]
        return portName, regPortRow['interface'], leafIfaceRow, leafIfaceContext, True

    routerInterface, routerIfaceRow, routerIfaceContext = \
        _resolveRouterRegisterBusInterface(
            prj, servingRouter, addressBusTypes, routerInterfaceCache,
        )
    portName = servingRouter['addressBlock']['registerDecoderPort']
    return portName, routerInterface, routerIfaceRow, routerIfaceContext, False


def _addressBusInterfaceTypes(prj):
    """Return the set of interfaceType names whose interface_defs row
    carries addressBus: true."""
    types = set()
    for _ctx, group in prj.data.get('interface_defs', {}).items():
        for typeName, row in group.items():
            if row['addressBus']:
                types.add(typeName)
    return types


def _resolveRouterRegisterBusInterface(prj, routerBlock, addressBusTypes,
                                       cache):
    """Find the addressBus: true interface named by addressBlock.upstreamPort.

    Routers do not declare `registerPorts:` (declaring both
    `registerPorts:` and `addressBlock:` on the same block is rejected
    by the schema), so the upstream / downstream interface is
    identified by the router's addressBlock port name. Multiple
    APB-shaped interfaces may be visible in the same load-time scope;
    only the one matching the router's port convention belongs to
    this router."""
    routerContext = routerBlock['_context']
    addressBlock = routerBlock['addressBlock']
    upstreamPort = addressBlock['upstreamPort']
    cacheKey = (routerContext, upstreamPort)
    if cacheKey in cache:
        return cache[cacheKey]

    blockName = routerBlock['block']
    ifaceRow, ifaceContext = prj.lookupInScope('interfaces', routerContext, upstreamPort)
    if not ifaceRow:
        _exit_with_error(
            f"Router block '{blockName}' (file {routerContext}) names "
            f"upstreamPort '{upstreamPort}', but no visible interface has "
            f"that name."
        )

    if ifaceRow['interfaceType'] not in addressBusTypes:
        _exit_with_error(
            f"Router block '{blockName}' (file {routerContext}) names "
            f"upstreamPort '{upstreamPort}' (file {ifaceContext}), but that "
            f"interface does not resolve to an addressBus: true "
            f"interfaceType."
        )

    cache[cacheKey] = (upstreamPort, ifaceRow, ifaceContext)
    return cache[cacheKey]


def postProcess(prj):
    blockInfo = prj.flatData['blocks']
    routers = _collectRouterBlocks(blockInfo)
    if not routers:
        # No addressBlock: routers are declared, so no register-bus
        # decode pass runs for this project (the project either has no
        # register bus at all or has not adopted the addressBlock: schema).
        return None

    instance_prefix, block_suffix, camel_case = regHandlerNaming(prj)

    # Router-bus decode is scoped to the active build's design hierarchy.
    # A referenced child project's standalone harness may be parsed into the
    # same database; its instances exist in the flat table but are not part
    # of this build's dispatch tree and must not compete for router/address
    # selection. For a single-project build every instance is reachable, so
    # this scoping changes nothing.
    reachable = prj.reachableInstanceKeys()

    # A router block declared with addressBlock: but never instantiated
    # anywhere is an authoring error. A router instantiated only outside this
    # build's hierarchy (a referenced child's harness) is not an error here;
    # it is simply out of scope and is dropped from the working set below.
    instantiatedRouterBlocks = {
        instRow['instanceTypeKey']
        for instRow in prj.flatData['instances'].values()
        if instRow['instanceTypeKey'] in routers
    }
    missing = [
        routers[blockKey]['block']
        for blockKey in routers
        if blockKey not in instantiatedRouterBlocks
    ]
    if missing:
        _exit_with_error(
            f"Router blocks declare addressBlock: but have no "
            f"instances in the design: {', '.join(missing)}."
        )

    # A router this project OWNS but whose every instance lies outside this
    # build's reachable top cannot have its decode routing synthesised: the
    # Steps 5&6 dispatch loop below skips all its (unreachable) instances, so
    # the router would render as an empty decoder (an empty always_comb plus a
    # stray end). This only fires when the current project both declares/
    # instantiates the router and disowns it from its own top; a referenced
    # child's router that the root legitimately prunes is owned by that child,
    # not the root, so it is excluded by the ownership condition.
    currentProject = prj.config.getConfig('PROJECTNAME')
    reachableRouterBlocks = {
        instRow['instanceTypeKey']
        for instRow in prj.flatData['instances'].values()
        if instRow['instanceKey'] in reachable
        and instRow['instanceTypeKey'] in routers
    }
    orphanedOwnedRouters = [
        routers[blockKey]['block']
        for blockKey in routers
        if blockKey in instantiatedRouterBlocks
        and blockKey not in reachableRouterBlocks
        and prj.contextOwningProject[routers[blockKey]['_context']] == currentProject
    ]
    if orphanedOwnedRouters:
        _exit_with_error(
            f"Register-decode router(s) owned by project "
            f"'{currentProject}' are instantiated only outside its reachable "
            f"top, so their decode routing cannot be synthesised: "
            f"{', '.join(orphanedOwnedRouters)}. Instantiate the router under "
            f"this project's topInstance, or ensure it is owned by the project "
            f"whose top instantiates it."
        )

    router_instance = _resolveRouterInstances(prj, routers, reachable)

    # Restrict the working router set to routers that participate in this
    # build's hierarchy; routers present only in a referenced child's harness
    # are handled by that child's own build.
    routers = {blockKey: routers[blockKey] for blockKey in router_instance}

    # Block keys instantiated at the design root (container: '_topInstance').
    # Used both to infer the primary router and, further down, to keep the
    # passthrough fixed point from treating the root as a passthrough.
    topBlockKeys = {
        instRow['instanceTypeKey']
        for instRow in prj.flatData['instances'].values()
        if instRow['container'] == '_topInstance'
    }

    primary_router = _findPrimaryRouter(prj, routers, router_instance, reachable, topBlockKeys)

    decoderContainer = {
        routerInstRow['containerKey']: routerInstRow
        for routerInstRow in router_instance.values()
    }

    # A nested-router container is dispatched to by the router-to-router
    # branch below, which sends the parent router's register bus to the
    # container instance (the container-sibling of its non-primary nested
    # router) and bridges it inward via a connectionMap. That branch is the
    # complete, correct handling for such a container, so its own
    # registerPorts: surface must not also fire a router-to-leaf dispatch;
    # otherwise the identical parent->container connection is emitted twice.
    # A non-primary nested router's containerKey is exactly the block type of
    # its container instance, so those block keys identify the containers the
    # router-to-leaf branch must skip.
    nestedRouterContainerBlockKeys = {
        routerInstRow['containerKey']
        for routerInstRow in router_instance.values()
        if routerInstRow is not primary_router
    }

    # Every block that hosts a register-decode router (a router instantiated
    # directly inside it) is fed at its own boundary and bridges that boundary
    # inward to the nested router; it is therefore never a router-to-leaf
    # dispatch target for its own registerPorts: surface. The upstream feed is
    # a parent router's dispatch when the block is composed under one (the
    # router-to-router branch below), or an authored master connection when the
    # nested router is itself the dispatch-tree root (a standalone reusable-IP
    # testbench). This set is independent of primary/non-primary status, unlike
    # nestedRouterContainerBlockKeys, so the router-to-leaf skip is applied to a
    # primary nested router's container too — the standalone reusable-IP build
    # where that container would otherwise be dispatched to with no parent
    # router present.
    routerContainerBlockKeys = {
        routerInstRow['containerKey']
        for routerInstRow in router_instance.values()
    }

    # ---- Per-owner-context emission buckets. Each owner block's
    # YAML file becomes the `_context` of the rows we feed back into
    # processSingleFile().
    perContext = dict()

    def _section(ctx, name):
        bucket = perContext.setdefault(ctx, dict())
        if name in ('connections', 'connectionMaps'):
            return bucket.setdefault(name, list())
        return bucket.setdefault(name, dict())

    listOfInstances = list()

    addressBusTypes = _addressBusInterfaceTypes(prj)
    routerInterfaceCache = dict()

    # ---- Step 4: synthesise register handlers per routed leaf ----
    # Handlers are synthesised only for leaf blocks that appear in this
    # build's hierarchy. A register-owning block that is instantiated only in
    # a referenced child's harness is served by that child's own build.
    reachableBlockKeys = {
        prj.flatData['instances'][instanceKey]['instanceTypeKey']
        for instanceKey in reachable
    }
    blocksNeedingHandler = {
        blockKey: block
        for blockKey, block in collectBlocksNeedingRegHandler(prj).items()
        if blockKey in reachableBlockKeys
    }

    # ---- Register-bus passthrough: single-consumer router-less containers ----
    # A router-less container hosting exactly one register consumer is
    # itself a consumer of its parent. A container's status depends on its
    # children's, so the set grows by fixed point. The design root has no
    # parent to feed it and is never a passthrough; an unresolved chain
    # ending there is reported as unserved further down. topBlockKeys was
    # already computed above, ahead of the primary-router resolution.
    consumerBlockKeys = set(blocksNeedingHandler)
    # A nested-router container is fed by an authored master connection or
    # by router-to-router dispatch, never by passthrough synthesis, even
    # when it also declares registerPorts:.
    consumerBlockKeys.update(
        blockKey for blockKey, row in blockInfo.items()
        if row.get('registerPorts') and blockKey not in routerContainerBlockKeys
    )
    while True:
        byContainer = dict()
        for instRow in prj.flatData['instances'].values():
            if instRow['instanceKey'] not in reachable:
                continue
            if instRow['container'] == '_topInstance':
                continue
            if instRow['instanceTypeKey'] not in consumerBlockKeys:
                continue
            byContainer.setdefault(instRow['containerKey'], list()).append(instRow)
        grown = {
            containerBlockKey
            for containerBlockKey, consumerRows in byContainer.items()
            if len(consumerRows) == 1
            and containerBlockKey not in routers
            and containerBlockKey not in routerContainerBlockKeys
            and containerBlockKey not in topBlockKeys
            and containerBlockKey not in consumerBlockKeys
        }
        if not grown:
            break
        consumerBlockKeys.update(grown)

    passthroughConsumer = dict()
    for containerBlockKey, consumerRows in byContainer.items():
        if (containerBlockKey in routers or containerBlockKey in routerContainerBlockKeys
                or containerBlockKey in topBlockKeys):
            continue
        # A container owning registers/memories already claims its
        # boundary port for its own <block>_regs handler; a hosted
        # consumer is a second claim on the same port.
        if len(consumerRows) == 1 and containerBlockKey not in blocksNeedingHandler:
            passthroughConsumer[containerBlockKey] = consumerRows[0]
            continue
        containerBlock = blockInfo[containerBlockKey]['block']
        named = ', '.join(
            f"{row['instance']} (block {blockInfo[row['instanceTypeKey']]['block']})"
            for row in consumerRows
        )
        if containerBlockKey in blocksNeedingHandler:
            _exit_with_error(
                f"Container block '{containerBlock}' owns firmware-"
                f"accessible registers/memories itself and also hosts "
                f"register-bus consumer(s) ({named}) but no register-decode "
                f"router (addressBlock:). Add an addressBlock: router "
                f"block to '{containerBlock}', or move its registers/"
                f"memories onto a leaf the router serves."
            )
        # Several consumers in one router-less container is ambiguous; a
        # passthrough forwards the bus to exactly one.
        _exit_with_error(
            f"Container block '{containerBlock}' hosts {len(consumerRows)} "
            f"instances that need a register bus ({named}) but no "
            f"register-decode router (addressBlock:). A router-less "
            f"container can pass the bus through to exactly one such "
            f"instance; add an addressBlock: router block to "
            f"'{containerBlock}', or move all but one of them under a "
            f"routed container."
        )

    def _routedSlotInstances(containerBlockKey):
        """Every reachable declared instance of containerBlockKey that a
        router ultimately dispatches to directly, walking outward through
        any further router-less passthrough containers in between."""
        slots = []
        for instRow in prj.flatData['instances'].values():
            if instRow['instanceKey'] not in reachable:
                continue
            if instRow['instanceTypeKey'] != containerBlockKey:
                continue
            outerContainerKey = instRow['containerKey']
            if outerContainerKey in decoderContainer:
                slots.append(instRow)
            elif outerContainerKey in passthroughConsumer:
                slots.extend(_routedSlotInstances(outerContainerKey))
        return slots

    # The routed slot is the container instance, so an inner consumer fed
    # through it must not carry addressGroup:.
    for containerBlockKey, consumerInstRow in passthroughConsumer.items():
        if consumerInstRow['addressGroup'] is None:
            continue
        slots = _routedSlotInstances(containerBlockKey)
        if not slots:
            # No router reaches this container; the unserved diagnostics
            # below name it instead.
            continue
        containerBlock = blockInfo[containerBlockKey]['block']
        slotDesc = "the routed slot is instance " + ', '.join(
            f"'{slot['instance']}'" for slot in slots
        )
        _exit_with_error(
            f"Instance '{consumerInstRow['instance']}' (block "
            f"'{blockInfo[consumerInstRow['instanceTypeKey']]['block']}') is "
            f"fed through router-less container '{containerBlock}' and must "
            f"not carry addressGroup: ({slotDesc}); remove it."
        )

    # ---- Structural diagnostics for register-bus boundary declarations ----
    # Run once the register-requiring set (blocksNeedingHandler), the nested-
    # router container set, and the router set are all resolved. A reusable IP
    # that needs a register bus must expose it under registerPorts:, not a plain
    # ports: entry; catch that misconfiguration here rather than letting it
    # surface as a cryptic C++ undeclared-identifier at compile time.

    # {blockKey: first regAccess memory name}, so Check 3 can name the memory.
    regAccessMemoryByBlock = dict()
    for memoryData in prj.flatData['memories'].values():
        if memoryData['regAccess'] and memoryData['blockKey'] not in regAccessMemoryByBlock:
            regAccessMemoryByBlock[memoryData['blockKey']] = memoryData['memory']

    for blockKey, blockRow in blockInfo.items():
        isRouter = blockKey in routers
        hostsNestedRouter = blockKey in nestedRouterContainerBlockKeys
        ownsRegisters = blockKey in blocksNeedingHandler
        isPassthrough = blockKey in passthroughConsumer

        # Check 2 (defensive fail-loud): a nested-router container that also
        # owns its own registers/memories. The router-to-leaf dispatch branch
        # below skips every nested-router container (so the identical parent->
        # container bind is not emitted twice), which would silently drop this
        # block's own <block>_regs handler dispatch. Convert that silent mis-
        # generation into a loud error. No in-tree example exercises this; it is
        # a defensive assert, not supported flexibility. Ordered before Check 1
        # so this more specific case reports itself rather than the generic
        # missing-registerPorts message.
        if hostsNestedRouter and ownsRegisters:
            _exit_with_error(
                f"block '{blockRow['block']}' hosts a nested register-decode "
                f"router but also owns firmware-accessible registers/memories. "
                f"The nested-router dispatch cannot also deliver this block's "
                f"own register handler. Move those registers/memories onto a "
                f"child leaf that the inner decoder serves (see the "
                f"design-register-decode skill §1 nested-router case)."
            )

        # Check 3 (defensive fail-loud): a router that also owns a regAccess
        # memory. Must precede Check 1's `if isRouter: continue`, which would
        # otherwise let this slip through unreported. Without it, calcAddresses
        # raises a KeyError (a router instance carries no addressGroup, so the
        # space check's AddressGroups lookup on it fails), pre-empting the
        # misleading V24 clock-port compare that would otherwise follow.
        if isRouter and blockKey in regAccessMemoryByBlock:
            _exit_with_error(
                f"block '{blockRow['block']}' is a register-decode router "
                f"(addressBlock:) but also owns regAccess memory "
                f"'{regAccessMemoryByBlock[blockKey]}'. A router owns no "
                f"firmware-accessible memories; declare it on a leaf the "
                f"router serves."
            )

        # Check 1 (primary): a bounded register-requiring block that authors an
        # explicit block-level ports: section but no registerPorts:. Presence of
        # the 'ports' key on the block row means the author wrote a block-level
        # ports: section; a top-down monolithic register-owning leaf (e.g.
        # mixed's blockA/blockB) authors no such section — its ports are inferred
        # from connections — and correctly omits registerPorts:. Requiring an
        # explicit ports: section therefore excludes that legitimate case and
        # targets the reusable-IP author who declared a plain ports: boundary
        # where a registerPorts: boundary was required.
        if isRouter:
            continue
        if not (ownsRegisters or hostsNestedRouter or isPassthrough):
            continue
        if 'ports' not in blockRow:
            continue
        if blockRow.get('registerPorts'):
            continue
        _exit_with_error(
            f"block '{blockRow['block']}' requires a register-bus interface "
            f"(it owns firmware-accessible registers/memories, hosts a "
            f"nested register-decode router, or passes the register bus "
            f"through to a single register consumer) but declares no "
            f"registerPorts:. A reusable IP must declare its register-bus "
            f"boundary under registerPorts: (see the design-register-decode "
            f"skill §5)."
        )

    def _routerServingLeaf(leafBlockKey):
        # Return any router serving an instance of this leaf block, walking
        # outward through router-less single-consumer containers when the
        # leaf's own immediate container hosts no router itself. All
        # routers reaching this leaf must agree on registerDecoderPort (the
        # handler block has one port name); picking any one is fine. Only
        # instances in this build's hierarchy are considered.
        for _instRow in prj.flatData['instances'].values():
            if _instRow['instanceKey'] not in reachable:
                continue
            if _instRow['instanceTypeKey'] != leafBlockKey:
                continue
            containerKey = _instRow['containerKey']
            routerInst = decoderContainer.get(containerKey)
            if routerInst is not None:
                return routers[routerInst['instanceTypeKey']]
            if containerKey in passthroughConsumer:
                servingRouter = _routerServingLeaf(containerKey)
                if servingRouter is not None:
                    return servingRouter
        return None

    for leafBlockKey, leafBlockSimple in blocksNeedingHandler.items():
        leafBlock = blockInfo[leafBlockKey]
        leafContext = leafBlock['_context']

        # The handler block's register-bus port is named after the
        # router's registerDecoderPort, not the leaf's authored port.
        # This matches the legacy convention: every <leaf>Regs block
        # exposes the same canonical port name (typically `apbReg`).
        # The leaf-side port name (`portName`) appears on the
        # connectionMap's parent-boundary `port:` field. For a reusable
        # IP it is the authored `registerPorts:` key (e.g. `regs`); for
        # a top-down leaf it is the router's `registerDecoderPort`, the
        # synthesised canonical register-bus port.
        servingRouter = _routerServingLeaf(leafBlockKey)
        if servingRouter is None:
            _exit_with_error(
                f"Leaf block '{leafBlockSimple}' needs a register "
                f"handler but no router was found serving any of its "
                f"instances, directly or through single-consumer "
                f"containers. Place the leaf in a router's container, or "
                f"in a container that a router serves and that holds no "
                f"other register consumer."
            )
        handlerPort = servingRouter['addressBlock']['registerDecoderPort']

        # A reusable IP authors its register-bus interface in
        # registerPorts:; a top-down leaf infers it from the serving
        # router (legacy inference behaviour). The handler block emits
        # this interface for its register storage either way.
        portName, leafInterfaceName, _leafIfaceRow, _leafIfaceContext, _authored = \
            _leafRegisterBinding(
                prj, leafBlock, servingRouter, addressBusTypes,
                routerInterfaceCache,
            )

        # The handler inherits the leaf block's parameters so it emits
        # module parameters and selects the leaf's module-local
        # parameterizable declarations. The leaf's params are already parsed
        # and validated (processYamls runs before this post-parse step).
        parentParams = [row['param'] for row in prj.flatData['blocksparams'].values()
                        if row['blockKey'] == leafBlockKey]
        reg_block, block_def, instance_name, instance_def, connection_map = \
            synthesiseRegHandler(
                prj, leafBlockKey, leafBlockSimple, leafInterfaceName,
                blockInfo, instance_prefix, block_suffix, camel_case,
                parentParams,
            )
        connection_map['port'] = portName
        connection_map['instancePort'] = handlerPort

        _section(leafContext, 'blocks')[reg_block] = block_def
        _section(leafContext, 'instances')[instance_name] = instance_def
        _section(leafContext, 'connectionMaps').append(connection_map)

    # ---- Steps 5 & 6: emit router-to-leaf and router-to-router binds ----
    for instRow in prj.flatData['instances'].values():
        if instRow['instanceKey'] not in reachable:
            continue
        context = instRow['_context']
        instanceTypeKey = instRow['instanceTypeKey']

        # Router-to-leaf: an instance gets a dispatch connection from
        # its parent router when its block owns a register-bus surface.
        # That is either an authored registerPorts: row (a reusable IP,
        # which may carry registers/memories or expose only a register
        # bus), registers/memories that need a synthesised <block>_regs
        # handler (a top-down leaf inferring its register bus from the
        # router), or a router-less container passing the bus through to
        # a single such consumer. Handler synthesis is a separate concern
        # handled above; dispatch fires for every surface.
        leafBlock = blockInfo[instanceTypeKey]
        if (leafBlock.get('registerPorts') or instanceTypeKey in blocksNeedingHandler
                or instanceTypeKey in passthroughConsumer) \
                and instanceTypeKey not in routerContainerBlockKeys:
            containerKey = instRow['containerKey']
            parentRouter = decoderContainer.get(containerKey)
            if parentRouter is None:
                if containerKey not in passthroughConsumer:
                    _exit_with_error(
                        f"Leaf instance '{instRow['instance']}' "
                        f"(block '{instanceTypeKey}') is in container "
                        f"'{containerKey}' which is not served by any "
                        f"router, directly or through single-consumer "
                        f"containers. Place the instance in a router's "
                        f"container, or in a container that a router "
                        f"serves and that holds no other register "
                        f"consumer."
                    )
                # Fed by the router-less container's own boundary map,
                # synthesised below, rather than a direct dispatch here.
                continue
            routerBlock = routers[parentRouter['instanceTypeKey']]
            addressBlock = routerBlock['addressBlock']
            regDecoderPort = addressBlock['registerDecoderPort']

            if instanceTypeKey in passthroughConsumer:
                # The container instance is the dispatched slot and must
                # carry the router's addressGroup, or the router allocates
                # it no slot.
                routerAddressGroup = addressBlock['addressGroup']
                if instRow['addressGroup'] != routerAddressGroup:
                    innerRow = passthroughConsumer[instanceTypeKey]
                    _exit_with_error(
                        f"Instance '{instRow['instance']}' (block "
                        f"'{instanceTypeKey}') passes the register bus "
                        f"from router '{parentRouter['instance']}' "
                        f"(addressGroup '{routerAddressGroup}') to "
                        f"'{innerRow['instance']}' and must carry "
                        f"addressGroup: {routerAddressGroup}; without it "
                        f"the router allocates it no decode slot."
                    )

            routerInterface, _routerIfaceRow, _routerIfaceContext = \
                _resolveRouterRegisterBusInterface(
                    prj, routerBlock, addressBusTypes,
                    routerInterfaceCache,
            )
            # The router-to-leaf port name is the leaf's authored
            # registerPorts: key (reusable IP) or the router's
            # registerDecoderPort (top-down leaf or passthrough
            # container). Cross-interface compatibility of an authored
            # leaf is checked at the end of projectCreate by validatePorts,
            # which reads registerPorts: as part of the leaf's declared-
            # port surface; synthesis only emits the bind here.
            portName = _leafRegisterBinding(
                prj, leafBlock, routerBlock, addressBusTypes,
                routerInterfaceCache,
            )[0]

            listOfInstances.append(instRow['instanceKey'])
            connection = {
                'src': parentRouter['instance'],
                'dst': instRow['instance'],
                'dstport': portName,
                'interface': routerInterface,
                'srcport': f"{regDecoderPort}_{instRow['instance']}",
                'interfaceName': f"{regDecoderPort}_{instRow['instance']}",
            }
            # This connection's own clock: is left unstated: a connection's
            # clock: names a CONTAINER net (spec §4.3 rule 2), while a
            # reusable IP's registerPorts: clock: is block-local (rule 1) -
            # stamping the block-local name here as if it were a container
            # net falsely fails V13 whenever an instance map renames it
            # (e.g. registerPorts: clock: regClk mapped regClk: apbClk).
            # Rule 1 stays authoritative through getBDPortDomain reading the
            # leaf's own registerPorts: row directly, not through this
            # connection.
            # Owner context is the container that holds both
            # endpoints. The router's own YAML file does not see
            # leaf-scoped interfaces; the container's file does, via
            # its include: chain. `context` is the yaml file the
            # instance row was authored in, i.e. the container's
            # file.
            _section(context, 'connections').append(connection)

        # Router-to-router: instance whose block is itself a router
        # AND this is the canonical router instance for that block
        # AND this router is not the primary.
        if instanceTypeKey in router_instance \
                and router_instance[instanceTypeKey] is instRow \
                and instRow is not primary_router:
            childBlock = routers[instanceTypeKey]
            # upstreamPort / registerDecoderPort are port-name
            # conventions only. The emitted interface must come from
            # the child router's authored register-bus interface
            # declaration, not from the port name string.
            childInterface, childIfaceRow, childIfaceContext = \
                _resolveRouterRegisterBusInterface(
                    prj, childBlock, addressBusTypes,
                    routerInterfaceCache,
                )

            childAddressBlock = childBlock['addressBlock']
            childUpstreamPort = childAddressBlock['upstreamPort']

            parentRouter = _findRouterParent(prj, instRow, decoderContainer, reachable)
            parentBlock = routers[parentRouter['instanceTypeKey']]
            parentAddressBlock = parentBlock['addressBlock']
            parentRegDecoderPort = parentAddressBlock['registerDecoderPort']
            _parentInterface, parentIfaceRow, parentIfaceContext = \
                _resolveRouterRegisterBusInterface(
                    prj, parentBlock, addressBusTypes,
                    routerInterfaceCache,
                )
            prj.checkInterfacePair(
                parentIfaceRow, childIfaceRow, instanceTypeKey,
                instRow['variant'] or '',
                f"Register-bus dispatch from parent router "
                f"'{parentRouter['instance']}' to nested router "
                f"'{instRow['instance']}' (upstreamPort "
                f"'{childAddressBlock['upstreamPort']}')",
                parentIfaceContext, childIfaceContext,
                parentRouter['instanceTypeKey'],
                parentRouter['variant'] or '',
            )

            # Find the container-block sibling instance — the
            # instance whose block type is the nested router's
            # container block, and that sits in the parent
            # router's container. The parent router dispatches to
            # that sibling, and a connectionMap on the container
            # block bridges its inherited upstream port into the
            # nested router instance.
            containerBlockKey = instRow['containerKey']
            containerSiblingInst = None
            containerSiblingContext = None
            for _candRow in prj.flatData['instances'].values():
                if _candRow['instanceKey'] not in reachable:
                    continue
                if _candRow['instanceTypeKey'] == containerBlockKey \
                        and _candRow['containerKey'] \
                        == parentRouter['containerKey']:
                    containerSiblingInst = _candRow
                    containerSiblingContext = _candRow['_context']
                    break
            if containerSiblingInst is None:
                _exit_with_error(
                    f"Could not find the sibling container instance "
                    f"for nested router '{instRow['instance']}'. "
                    f"Expected an instance of block "
                    f"'{containerBlockKey}' contained by "
                    f"'{parentRouter['containerKey']}'."
                )

            siblingInstance = containerSiblingInst['instance']
            # INSTANCES_WITH_REGAPB drives the top router's dispatch
            # list: each entry is an instance that the parent router
            # sends register-bus traffic to. For a nested router,
            # the parent dispatches to the *container* instance
            # (e.g. uBridge), not the nested decoder inside the
            # container (uBridgeAPBDecode). Match the legacy
            # convention so the constructor template emits a real
            # downstream port instead of nullptr.
            listOfInstances.append(containerSiblingInst['instanceKey'])
            connection = {
                'src': parentRouter['instance'],
                'dst': siblingInstance,
                'interface': childInterface,
                'srcport': f"{parentRegDecoderPort}_{siblingInstance}",
                'dstport': childUpstreamPort,
                'interfaceName': f"{parentRegDecoderPort}_{siblingInstance}",
            }
            # The parent container owns the sibling instance and
            # the parent router instance, so it is the context that
            # can resolve both endpoints of this dispatch bind.
            _section(containerSiblingContext, 'connections').append(connection)

    # ---- Intrinsic boundary map (container-fed nested router) ----
    # A router instantiated inside a container block is fed at that container's
    # boundary; a connectionMap bridges the container's inherited upstream
    # interface to the nested router instance's upstream port. Emit it when
    # either feed exists:
    #   * the nested router is non-primary — a parent router dispatches to the
    #     container (the composed top-down and composed reusable-IP cases); or
    #   * the container block declares registerPorts: — its boundary is fed by
    #     an authored master connection, including the standalone reusable-IP
    #     testbench whose nested router is the dispatch-tree root (primary).
    # A primary nested router in a plain (no registerPorts:) container has no
    # boundary feed and gets no map. Gating on this union preserves the composed
    # and top-down behaviour (non-primary containers always get the map) and
    # gives a standalone reusable-IP build the same map its composed form has,
    # so the IP's generated files (its <block>Base decoder) stay byte-identical
    # across composed and standalone builds. Emitted into the yaml file that
    # authored the nested router instance row (`_context`): that file includes
    # the container block's yaml (so `block:` resolves), it owns the nested
    # router instance row (so `instance:` resolves), and the register-bus
    # interface is declared by that same container block.
    for routerInstRow in router_instance.values():
        containerBlockKey = routerInstRow['containerKey']
        containerBlockRow = blockInfo[containerBlockKey]
        if routerInstRow is primary_router \
                and not containerBlockRow.get('registerPorts'):
            continue
        routerBlock = routers[routerInstRow['instanceTypeKey']]
        childInterface, _childIfaceRow, _childIfaceContext = \
            _resolveRouterRegisterBusInterface(
                prj, routerBlock, addressBusTypes, routerInterfaceCache,
            )
        childUpstreamPort = routerBlock['addressBlock']['upstreamPort']
        connection_map = {
            'interface': childInterface,
            'block': containerBlockRow['block'],
            'port': childUpstreamPort,
            'direction': 'dst',
            'instance': routerInstRow['instance'],
            'instancePort': childUpstreamPort,
        }
        _section(routerInstRow['_context'], 'connectionMaps').append(connection_map)

    # ---- Passthrough boundary maps (router-less containers) ----
    # Each passthrough container bridges its boundary port, as
    # _leafRegisterBinding names it, to its single inner consumer: one
    # connectionMap per chain level.
    registerBusPassthrough = dict()
    for containerBlockKey, consumerInstRow in passthroughConsumer.items():
        containerBlockRow = blockInfo[containerBlockKey]
        consumerBlock = blockInfo[consumerInstRow['instanceTypeKey']]
        servingRouter = _routerServingLeaf(containerBlockKey)
        boundaryPort = _leafRegisterBinding(
            prj, containerBlockRow, servingRouter, addressBusTypes,
            routerInterfaceCache,
        )[0]
        innerPort, innerInterface, _innerIfaceRow, _innerIfaceContext, _authored = \
            _leafRegisterBinding(
                prj, consumerBlock, servingRouter, addressBusTypes,
                routerInterfaceCache,
            )
        connection_map = {
            'interface': innerInterface,
            'block': containerBlockRow['block'],
            'port': boundaryPort,
            'direction': 'dst',
            'instance': consumerInstRow['instance'],
            'instancePort': innerPort,
        }
        _section(consumerInstRow['_context'], 'connectionMaps').append(connection_map)

        registerBusPassthrough[containerBlockKey] = {
            'boundaryPort': boundaryPort,
            'innerInstanceKey': consumerInstRow['instanceKey'],
            'innerPortName': innerPort,
            'slotInstanceKeys': [
                slot['instanceKey']
                for slot in _routedSlotInstances(containerBlockKey)
            ],
        }

    # ---- Emit per owner context ----
    # Every synthesised connection/connectionMap here is a register-bus feed
    # (§4.3 "Registers"/"Routers"): a top-down leaf's is a synthesised
    # register-bus port, which R25 governs directly rather than a stamped
    # clock:, and a nested router's is a synthesised feed, which spec §4.3
    # says carries no clock: at all (a nested router on a non-default clock
    # names it on its own addressBlock: instead). Neither row states clock:.
    for ownerContext, sections in perContext.items():
        ordered = dict()
        for sectionName in ('blocks', 'instances', 'connections', 'connectionMaps'):
            if sectionName in sections:
                ordered[sectionName] = sections[sectionName]
        if ordered:
            prj.processSingleFile(ownerContext, sections=ordered)

    prj.config.setConfig("INSTANCES_WITH_REGAPB", listOfInstances, bin=True)
    prj.config.setConfig("REGAPB_PASSTHROUGH", registerBusPassthrough, bin=True)
    # Returning None bypasses the dispatcher's _global re-feed.
    return None
