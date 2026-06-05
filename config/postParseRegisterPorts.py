"""New-schema post-parse pass for register-bus distribution.

Activated when at least one block declares `addressBlock:`. Mutually
exclusive with the legacy `postParseRegister.py`: blocks may not mix
the two spellings — the schema-side `_post_registerAddressBlock` hook
errors when a project also declares a legacy `addressControl.yaml`,
so this script can assume the new-schema state is canonical when it
runs.

Responsibilities:
  1. Build the router index from `prj.flatData['blocks']` rows that
     carry `addressBlock:`.
  2. Resolve the router instance per group via container-locality.
  3. Infer the primary router by hierarchy walk.
  4. Synthesise the `<block>_regs` handler block, instance, and
     leaf-to-handler `connectionMap` per routed leaf via the shared
     helper exposed from `postParseRegister.py`.
  5. Emit the router-to-leaf connection per routed instance, with the
     interface sourced from the leaf's `registerPorts:` entry.
  6. Emit the parent-router-to-child-router connection per nested
     router.
  7. Tag synthesised binds with their owning block's YAML context by
     feeding them through `processSingleFile(ownerContext, ...)` per
     owner, never `_global`.

The script bypasses the dispatcher's `_global` re-feed by calling
`prj.processSingleFile(...)` directly per owner context and returning
None.
"""

from pysrc.arch2codeHelper import printError, warningAndErrorReport
from config.postParseRegister import (
    collectBlocksNeedingRegHandler,
    regHandlerNaming,
    synthesiseRegHandler,
)


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


def _resolveRouterInstances(prj, routers):
    """Resolve the single router instance per router block. Multi-
    instance routers are diagnosed here."""
    router_instance = dict()
    for instRow in prj.flatData['instances'].values():
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


def _findRouterParent(prj, childRouterInstRow, decoderContainer):
    """Walk up from a router instance's containerKey to locate the
    parent router that serves the router's container block."""
    routerContainerBlockKey = childRouterInstRow['containerKey']
    for instRow in prj.flatData['instances'].values():
        if instRow['instanceTypeKey'] != routerContainerBlockKey:
            continue
        ancestor_container = instRow['containerKey']
        candidate = decoderContainer.get(ancestor_container)
        if candidate is not None and candidate is not childRouterInstRow:
            return candidate
    return None


def _findPrimaryRouter(prj, routers, router_instance):
    """Infer the primary router by hierarchy walk. Errors if zero or
    more than one candidate is found."""
    decoderContainer = {
        routerInstRow['containerKey']: routerInstRow
        for routerInstRow in router_instance.values()
    }

    primary_candidates = []
    for routerInstRow in router_instance.values():
        parent_router = _findRouterParent(prj, routerInstRow, decoderContainer)
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


def _selectLeafRegisterPort(leafBlockKey, leafBlock):
    """Return (portName, registerPortRow) for a leaf block. Multiple
    registerPorts: rows are rejected by the block parse hook."""
    registerPorts = leafBlock.get('registerPorts') or {}
    blockName = leafBlock['block']
    if len(registerPorts) == 0:
        _exit_with_error(
            f"Routed leaf block '{blockName}' declares registers or "
            f"memories but has no registerPorts: entry. Declare "
            f"exactly one registerPorts: row whose interface resolves "
            f"to an addressBus: true interfaceType."
        )
    portName = next(iter(registerPorts.keys()))
    return portName, registerPorts[portName]


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
        # No new-schema declarations. Legacy postParseRegister.py
        # handles this project (or there is no register bus at all).
        return None

    instance_prefix, block_suffix, camel_case = regHandlerNaming(prj)

    router_instance = _resolveRouterInstances(prj, routers)

    missing = [
        routers[blockKey]['block']
        for blockKey in routers
        if blockKey not in router_instance
    ]
    if missing:
        _exit_with_error(
            f"Router blocks declare addressBlock: but have no "
            f"instances in the design: {', '.join(missing)}."
        )

    primary_router = _findPrimaryRouter(prj, routers, router_instance)

    decoderContainer = {
        routerInstRow['containerKey']: routerInstRow
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
    blocksNeedingHandler = collectBlocksNeedingRegHandler(prj)

    def _routerServingLeaf(leafBlockKey):
        # Return any router serving an instance of this leaf block.
        # All routers reaching this leaf must agree on
        # registerDecoderPort (the handler block has one port name);
        # picking any one is fine.
        for _instRow in prj.flatData['instances'].values():
            if _instRow['instanceTypeKey'] != leafBlockKey:
                continue
            routerInst = decoderContainer.get(_instRow['containerKey'])
            if routerInst is not None:
                return routers[routerInst['instanceTypeKey']]
        return None

    for leafBlockKey, leafBlockSimple in blocksNeedingHandler.items():
        leafBlock = blockInfo[leafBlockKey]
        portName, regPortRow = _selectLeafRegisterPort(leafBlockKey, leafBlock)
        leafInterfaceName = regPortRow['interface']
        leafContext = leafBlock['_context']

        # The handler block's register-bus port is named after the
        # router's registerDecoderPort, not the leaf's authored port.
        # This matches the legacy convention: every <leaf>Regs block
        # exposes the same canonical port name (typically `apbReg`).
        # The leaf-side authored port name (`portName`, e.g. `regs`)
        # still appears on the connectionMap's parent-boundary `port:`
        # field so the leaf's authored `registerPorts:` row binds to
        # the handler's canonical port through this map.
        servingRouter = _routerServingLeaf(leafBlockKey)
        if servingRouter is None:
            _exit_with_error(
                f"Leaf block '{leafBlockSimple}' needs a register "
                f"handler but no router was found serving any of its "
                f"instances. Place the leaf in a router's container."
            )
        handlerPort = servingRouter['addressBlock']['registerDecoderPort']

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
        context = instRow['_context']
        instanceTypeKey = instRow['instanceTypeKey']

        # Router-to-leaf: every instance whose block declares
        # registerPorts: gets a dispatch connection from its parent
        # router, even when the leaf owns no registers/memories and
        # therefore needs no <block>_regs handler. The leaf's
        # register-bus surface (the registerPorts: entry) is the
        # contract for dispatch; handler synthesis is a separate
        # concern handled above.
        leafBlock = blockInfo[instanceTypeKey]
        if leafBlock.get('registerPorts'):
            containerKey = instRow['containerKey']
            parentRouter = decoderContainer.get(containerKey)
            if parentRouter is None:
                _exit_with_error(
                    f"Leaf instance '{instRow['instance']}' "
                    f"(block '{instanceTypeKey}') is in container "
                    f"'{containerKey}' which is not served by any "
                    f"router. Place the instance in a router's "
                    f"container or add a router for this scope."
                )
            routerBlock = routers[parentRouter['instanceTypeKey']]
            addressBlock = routerBlock['addressBlock']
            regDecoderPort = addressBlock['registerDecoderPort']

            portName, regPortRow = _selectLeafRegisterPort(
                instanceTypeKey, leafBlock
            )
            routerInterface, routerIfaceRow, routerIfaceContext = \
                _resolveRouterRegisterBusInterface(
                    prj, routerBlock, addressBusTypes,
                    routerInterfaceCache,
            )
            leafIfaceKey = regPortRow['interfaceKey']
            leafIfaceContext = leafIfaceKey.split('/', 1)[1]
            leafIfaceRow = prj.flatData['interfaces'][leafIfaceKey]
            prj.checkInterfacePair(
                routerIfaceRow, leafIfaceRow, instanceTypeKey,
                instRow['variant'] or '',
                f"Register-bus dispatch from router "
                f"'{parentRouter['instance']}' to leaf instance "
                f"'{instRow['instance']}' (registerPorts: row "
                f"'{portName}')",
                routerIfaceContext, leafIfaceContext,
                parentRouter['instanceTypeKey'],
                parentRouter['variant'] or '',
            )

            listOfInstances.append(instRow['instanceKey'])
            connection = {
                'src': parentRouter['instance'],
                'dst': instRow['instance'],
                'dstport': portName,
                'interface': routerInterface,
                'srcport': f"{regDecoderPort}_{instRow['instance']}",
                'interfaceName': f"{regDecoderPort}_{instRow['instance']}",
            }
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

            parentRouter = _findRouterParent(prj, instRow, decoderContainer)
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

            # The container block boundary maps its inherited
            # upstream interface to the nested router instance.
            # Emit into the yaml file that authored the nested
            # router instance row (`context`): that file already
            # includes both the parent router's yaml (so the
            # register-bus interface resolves) and the container
            # block's yaml (so `block:` resolves), and it owns the
            # nested router instance row itself (so `instance:`
            # resolves).
            containerBlockName = blockInfo[containerBlockKey]['block']
            connection_map = {
                'interface': childInterface,
                'block': containerBlockName,
                'port': childUpstreamPort,
                'direction': 'dst',
                'instance': instRow['instance'],
                'instancePort': childUpstreamPort,
            }
            _section(context, 'connectionMaps').append(connection_map)

    # ---- Emit per owner context ----
    for ownerContext, sections in perContext.items():
        ordered = dict()
        for sectionName in ('blocks', 'instances', 'connections', 'connectionMaps'):
            if sectionName in sections:
                ordered[sectionName] = sections[sectionName]
        if ordered:
            prj.processSingleFile(ownerContext, sections=ordered)

    prj.config.setConfig("INSTANCES_WITH_REGAPB", listOfInstances, bin=True)
    # Returning None bypasses the dispatcher's _global re-feed.
    return None
