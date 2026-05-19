"""New-schema post-parse pass for register-bus distribution.

Activated when at least one block declares `addressBlock:` (the new
per-router authoring path defined in
`builder/base/plan-address-control-refactor.md`). Mutually exclusive
with the legacy `postParseRegister.py`: blocks may not mix the two
spellings — the schema-side `_post_registerAddressBlock` hook errors
when a project also declares a legacy `addressControl.yaml`, so this
script can assume the new-schema state is canonical when it runs.

Stage 4 responsibilities (per the plan):
  1. Build the router index from `prj.data['blocks']` rows that carry
     `addressBlock:`.
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


def _flattenBlocks(prj):
    """Return {blockKey: blockRow} across all contexts."""
    flat = dict()
    for context, blocks in prj.data['blocks'].items():
        for _, blockRow in blocks.items():
            flat[blockRow['blockKey']] = blockRow
    return flat


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
    for context, instances in prj.data['instances'].items():
        for _, instRow in instances.items():
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
    for context, instances in prj.data['instances'].items():
        for _, instRow in instances.items():
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
            if row.get('addressBus'):
                types.add(typeName)
    return types


def _resolveRouterRegisterBusInterface(prj, routerBlock, addressBusTypes,
                                       cache):
    """Find the single addressBus: true interface authored in the router
    block's load-time scope. Routers do not declare `registerPorts:`
    (Stage 1.2 forbids the combination with `addressBlock:`), so the
    upstream / downstream interface is identified by walking the
    router's visible YAML contexts and selecting the one interface whose
    interfaceType resolves to an `addressBus: true` interface_defs row.

    Errors if zero or more than one such interface is in scope."""
    routerContext = routerBlock['_context']
    if routerContext in cache:
        return cache[routerContext]

    visibleContexts = set(prj.yamlContext.get(routerContext, {}).keys())
    visibleContexts.add(routerContext)

    candidates = []
    for ctx in visibleContexts:
        ifaces = prj.data.get('interfaces', {}).get(ctx, {})
        for ifaceName, ifaceRow in ifaces.items():
            if ifaceRow.get('interfaceType') in addressBusTypes:
                candidates.append((ifaceName, ctx))

    blockName = routerBlock['block']
    if not candidates:
        _exit_with_error(
            f"Router block '{blockName}' (file {routerContext}) has no "
            f"addressBus: true interface authored in its load-time "
            f"scope. Declare the router's register-bus interface in its "
            f"YAML file or an included file, and ensure its "
            f"interfaceType resolves to an interface_defs row with "
            f"addressBus: true."
        )
    if len(candidates) > 1:
        names = ', '.join(f"'{name}' (file {ctx})" for name, ctx in candidates)
        _exit_with_error(
            f"Router block '{blockName}' (file {routerContext}) has "
            f"multiple addressBus: true interfaces in its load-time "
            f"scope: {names}. Exactly one register-bus interface is "
            f"supported per router."
        )
    cache[routerContext] = candidates[0][0]
    return cache[routerContext]


def postProcess(prj):
    blockInfo = _flattenBlocks(prj)
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

    for leafBlockKey, leafBlockSimple in blocksNeedingHandler.items():
        leafBlock = blockInfo[leafBlockKey]
        portName, regPortRow = _selectLeafRegisterPort(leafBlockKey, leafBlock)
        leafInterfaceName = regPortRow['interface']
        leafContext = leafBlock['_context']

        reg_block, block_def, instance_name, instance_def, connection_map = \
            synthesiseRegHandler(
                prj, leafBlockKey, leafBlockSimple, leafInterfaceName,
                blockInfo, instance_prefix, block_suffix, camel_case,
            )
        # The leaf-to-handler bind names the leaf's registerPorts:
        # entry as the leaf-side port; the handler block (synthesised)
        # exposes the matching interface at its dst end.
        connection_map['port'] = portName

        _section(leafContext, 'blocks')[reg_block] = block_def
        _section(leafContext, 'instances')[instance_name] = instance_def
        _section(leafContext, 'connectionMaps').append(connection_map)

    # ---- Steps 5 & 6: emit router-to-leaf and router-to-router binds ----
    for context, instances in prj.data['instances'].items():
        for _, instRow in instances.items():
            instanceTypeKey = instRow['instanceTypeKey']

            # Router-to-leaf: every instance whose block declares
            # registerPorts: gets a dispatch connection from its parent
            # router, even when the leaf owns no registers/memories and
            # therefore needs no <block>_regs handler. The leaf's
            # register-bus surface (the registerPorts: entry) is the
            # contract for dispatch; handler synthesis is a separate
            # concern handled above.
            leafBlock = blockInfo.get(instanceTypeKey)
            if leafBlock is not None and leafBlock.get('registerPorts'):
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
                routerContext = routerBlock['_context']

                portName, regPortRow = _selectLeafRegisterPort(
                    instanceTypeKey, leafBlock
                )
                leafInterface = regPortRow['interface']

                listOfInstances.append(instRow['instanceKey'])
                connection = {
                    'src': parentRouter['instance'],
                    'dst': instRow['instance'],
                    'interface': leafInterface,
                    'srcport': f"{regDecoderPort}_{instRow['instance']}",
                    'interfaceName': f"{regDecoderPort}_{instRow['instance']}",
                }
                _section(routerContext, 'connections').append(connection)

            # Router-to-router: instance whose block is itself a router
            # AND this is the canonical router instance for that block
            # AND this router is not the primary.
            if instanceTypeKey in router_instance \
                    and router_instance[instanceTypeKey] is instRow \
                    and instRow is not primary_router:
                childBlock = routers[instanceTypeKey]
                # upstreamPort / registerDecoderPort are port-name
                # conventions only (Stage 4.1). The emitted interface
                # must come from the child router's authored
                # register-bus interface declaration, not from the port
                # name string.
                childInterface = _resolveRouterRegisterBusInterface(
                    prj, childBlock, addressBusTypes, routerInterfaceCache,
                )

                parentRouter = _findRouterParent(prj, instRow, decoderContainer)
                parentBlock = routers[parentRouter['instanceTypeKey']]
                parentAddressBlock = parentBlock['addressBlock']
                parentRegDecoderPort = parentAddressBlock['registerDecoderPort']
                parentContext = parentBlock['_context']

                listOfInstances.append(instRow['instanceKey'])
                connection = {
                    'src': parentRouter['instance'],
                    'dst': instRow['instance'],
                    'interface': childInterface,
                    'srcport': f"{parentRegDecoderPort}_{instRow['instance']}",
                    'interfaceName': f"{parentRegDecoderPort}_{instRow['instance']}",
                }
                _section(parentContext, 'connections').append(connection)

                # Per Stage 4 step 6, also emit a connectionMap so the
                # nested router exposes its upstream port to the
                # parent router's dispatch — mirrors the legacy
                # hierarchical decoder connection map. The bound
                # interface is the child router's authored register-bus
                # interface, not the upstreamPort port-name string.
                connection_map = {
                    'interface': childInterface,
                    'block': childBlock['block'],
                    'direction': 'dst',
                    'instance': instRow['instance'],
                }
                _section(parentContext, 'connectionMaps').append(connection_map)

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
