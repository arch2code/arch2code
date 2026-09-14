"""Where a fileMap artifact lives on disk, and whether it applies to a block.
Every tool that writes or inspects generated files resolves both here, so
the path rule exists once."""

import os
from pysrc.arch2codeHelper import printError, warningAndErrorReport
from pysrc.variantSelection import standaloneVariantDescriptors

def expandNewModulePath(fileDefinition, moduleDir, module, moduleFileStub, layout, missingDirOk = False):
    # layout is the owning project's layoutConfig (PROJECTLAYOUT[owner]); the
    # caller selects it by the object's defining-context owner so a child-owned
    # object's path roots under the child project's own segments.
    fileStub = fileDefinition.get('name', '')

    basePathKey = fileDefinition.get('basePath', '')
    segment = layout['segments'][basePathKey]['path']
    if layout['mode'] == 'hierarchical':
        # decomposition node outer, functional segment inner:
        #   <node>/<segment>[/module]/file. moduleDir is the node's own absolute
        #   directory (derived in processSingleFile); the segment is the bare
        #   node-relative functional name joined onto it.
        if not moduleDir and not os.path.isabs(segment):
            # A node-relative segment with no node directory would abspath
            # against the process cwd and deposit the artifact outside the
            # project tree. Fail loudly so a miswired caller cannot leak to cwd
            # (every caller must supply the object's node dir: block/context/
            # registrar the object's own, project-scope the top context's).
            printError(f"hierarchical path resolution for '{fileStub}' has no "
                       f"node directory for node-relative segment '{segment}'")
            exit(warningAndErrorReport())
        if not os.path.exists(moduleDir) and not missingDirOk:
            printError(f"node path of {moduleDir} does not exist")
        moduleDirAbs = os.path.abspath(os.path.join(moduleDir, segment))
    else:
        # functional segment root outer, decomposition inner (unchanged):
        #   $root/<segment>/<decomp>[/module]/file.
        if not os.path.exists(segment) and not missingDirOk:
            printError(f"path of {segment} does not exist")
        moduleDirAbs = os.path.abspath(os.path.join(segment, moduleDir))
    blockDir = fileDefinition.get('blockDir', False)
    if blockDir:
        moduleDirAbs = os.path.join(moduleDirAbs, module)
    fileName = f"{moduleFileStub}{fileStub}"
    filePath = os.path.join(moduleDirAbs, fileName)
    return filePath

def fileMapCondMatch(fileDefinition, condData):
    # Evaluate a fileMap entry's cond/condAnd predicate against a block's
    # file-generation data row. OR semantics for cond (any true makes the
    # file), AND semantics for condAnd (all must hold), no predicate means
    # always make. This is the single decision the file generator (newModule)
    # and the build-manifest artifact hook share, so
    # the manifest's directory set cannot drift from the files actually emitted.
    cond = fileDefinition.get("cond", None)
    condAnd = fileDefinition.get("condAnd", None)
    makeFile = not cond
    if cond:
        for field, value in cond.items():
            if condData[field] == value:
                makeFile = True
                break
    if condAnd:
        for field, value in condAnd.items():
            if condData[field] != value:
                makeFile = False
                break
    return makeFile

def blockCondRow(blockRow, blocksWithParams):
    # fileMap cond fields are block columns plus hasOwnParams, which is the block's
    # own params: relationship rather than a column.
    row = dict(blockRow)
    row['hasOwnParams'] = int(blockRow['blockKey'] in blocksWithParams)
    return row

def configModuleFileDef(fileMap):
    # The owner-qualified Config module entry. ownerQualified marks both
    # owner-qualified registrar entries; the variant-bearing one is the SV wrapper top.
    (fileDef,) = [fd for fd in fileMap.values()
                  if fd.get('ownerQualified', False) and not fd.get('variant', False)]
    return fileDef

def artifactRows(prj, blockCondData, instances, fileMap):
    """One row per generated artifact the fileMap names, over every project in
    the database. Fields: fileType/fileDef, mode, stem (the expandNewModulePath
    result), files {extKey: path}, owner, layout, blockKey/anchorKey, variant
    ('' when none), topModule (pairVlTop rows), context/includeEntries (context
    rows). The caller supplies blockCondData and instances so projectCreate
    (flatData) and projectOpen (data) both use it."""
    projectLayout = prj.projectLayout
    contextOwningProject = prj.contextOwningProject

    def layoutForContext(context):
        return projectLayout[contextOwningProject[context]]

    def row(fileType, fileDef, mode, stem, owner, layout, blockKey=None,
            anchorKey=None, variant='', topModule=None, context=None,
            includeEntries=None):
        return {
            'fileType': fileType, 'fileDef': fileDef, 'mode': mode,
            'stem': stem,
            'files': rowFiles(stem, fileDef),
            'owner': owner, 'layout': layout,
            'blockKey': blockKey, 'anchorKey': anchorKey,
            'variant': variant, 'topModule': topModule,
            'context': context, 'includeEntries': includeEntries,
        }

    def rowFiles(stem, fileDef):
        return {ext: stem + '.' + val for ext, val in fileDef['ext'].items()}

    rows = list()

    # Block mode: one row per block per matching block-mode entry, one row
    # per variant stem when the entry varies per variant.
    for blockRow in blockCondData.values():
        anchorLayout = layoutForContext(blockRow['_context'])
        owner = contextOwningProject[blockRow['_context']]
        for fileType, fileDef in fileMap.items():
            if fileDef.get('mode', 'block') != 'block':
                continue
            if not fileMapCondMatch(fileDef, blockRow):
                continue
            hasVariant = fileDef.get('variant', False)
            variants = sorted(standaloneVariantDescriptors(prj.config, blockRow['blockKey'])) \
                if hasVariant else []
            if hasVariant and variants:
                stemVariants = [(f"{blockRow['block']}_{v}", v) for v in variants]
            elif hasVariant and blockRow['hasOwnParams']:
                # Every variant is container-sourced; the pair rows cover this block's tops.
                continue
            else:
                stemVariants = [(blockRow['block'], '')]
            for stem, variant in stemVariants:
                stemPath = expandNewModulePath(fileDef, blockRow['dir'],
                                               blockRow['block'], stem,
                                               anchorLayout, missingDirOk=True)
                rows.append(row(fileType, fileDef, 'block', stemPath, owner, anchorLayout,
                                blockKey=blockRow['blockKey'], anchorKey=blockRow['blockKey'],
                                variant=variant))

    # Registrar mode: four shapes told apart by ownerQualified, variant and pairVlTop.
    registrarMap = {k: v for k, v in fileMap.items()
                    if v.get('mode', 'block') == 'registrar'}
    if registrarMap:
        registrarPairs = prj.config.getConfig('REGISTRARPAIRS')
        for (assemblerKey, childKey), pair in registrarPairs.items():
            assemblerRow = blockCondData[assemblerKey]
            childRow = blockCondData[childKey]
            anchorLayout = layoutForContext(assemblerRow['_context'])
            owner = contextOwningProject[assemblerRow['_context']]
            for fileType, fileDef in registrarMap.items():
                if fileDef.get('ownerQualified', False) or fileDef.get('pairVlTop', False):
                    continue
                if not fileMapCondMatch(fileDef, childRow):
                    continue
                if fileDef.get('requiresRegistrations', False) \
                        and not pair['aggregateHasModelRegistrations']:
                    continue
                stemPath = expandNewModulePath(fileDef, assemblerRow['dir'],
                                               childRow['block'], pair['artifactStem'],
                                               anchorLayout, missingDirOk=True)
                rows.append(row(fileType, fileDef, 'registrar', stemPath, owner, anchorLayout,
                                blockKey=childKey, anchorKey=assemblerKey))
            for fileType, fileDef in registrarMap.items():
                if not fileDef.get('pairVlTop', False):
                    continue
                if not fileMapCondMatch(fileDef, childRow):
                    continue
                for registration in pair['verifRegistrations']:
                    if not registration['pairSpecific']:
                        continue
                    stemPath = expandNewModulePath(fileDef, assemblerRow['dir'],
                                                   childRow['block'],
                                                   registration['physicalFileStub'],
                                                   anchorLayout, missingDirOk=True)
                    rows.append(row(fileType, fileDef, 'registrar', stemPath, owner, anchorLayout,
                                    blockKey=childKey, anchorKey=assemblerKey,
                                    variant=registration['variant'],
                                    topModule=registration['topModule']))

        for (owner, childKey), entry in prj.config.getConfig('CONFIGMODULES').items():
            childRow = blockCondData[childKey]
            parentRow = blockCondData[entry['parentKey']]
            anchorLayout = layoutForContext(parentRow['_context'])
            for fileType, fileDef in registrarMap.items():
                if not fileDef.get('ownerQualified', False) or fileDef.get('variant', False):
                    continue
                if not fileMapCondMatch(fileDef, childRow):
                    continue
                stemPath = expandNewModulePath(fileDef, parentRow['dir'],
                                               childRow['block'], entry['stub'],
                                               anchorLayout, missingDirOk=True)
                rows.append(row(fileType, fileDef, 'registrar', stemPath, owner, anchorLayout,
                                blockKey=childKey, anchorKey=entry['parentKey']))

        for (owner, childKey), entry in prj.config.getConfig('FOREIGNCONFIGHEADERS').items():
            childRow = blockCondData[childKey]
            parentRow = blockCondData[entry['parentKey']]
            anchorLayout = layoutForContext(parentRow['_context'])
            for fileType, fileDef in registrarMap.items():
                if not (fileDef.get('ownerQualified', False) and fileDef.get('variant', False)):
                    continue
                if not fileMapCondMatch(fileDef, childRow):
                    continue
                for variant in entry['vlVariants']:
                    stemPath = expandNewModulePath(fileDef, parentRow['dir'],
                                                   childRow['block'],
                                                   f"{entry['stub']}_{variant}",
                                                   anchorLayout, missingDirOk=True)
                    rows.append(row(fileType, fileDef, 'registrar', stemPath, owner, anchorLayout,
                                    blockKey=childKey, anchorKey=entry['parentKey'],
                                    variant=variant))

    # Context mode: one row per (fileType, context), all its exts in `files`.
    includeFiles = prj.config.getConfig('INCLUDEFILES')
    for fileType, fileDef in fileMap.items():
        if fileDef.get('mode', 'block') != 'context':
            continue
        entriesByContext = dict()
        for ext in fileDef['ext']:
            expandedType = f"{fileType}_{ext}"
            if expandedType not in includeFiles:
                continue
            for context, entry in includeFiles[expandedType].items():
                entriesByContext.setdefault(context, dict())[ext] = entry
        for context, extEntries in entriesByContext.items():
            stem = next(iter(extEntries.values()))['stem']
            rows.append(row(fileType, fileDef, 'context', stem,
                            contextOwningProject[context], layoutForContext(context),
                            context=context, includeEntries=extEntries))

    # Project mode: exactly one artifact per project-mode entry, at the top
    # context's node (hierarchical) or $root (functional). A definitions-only
    # project (no topInstance) has no top context and emits none.
    topContext = prj.config.getConfig('TOPCONTEXT')
    if topContext is not None:
        anchorLayout = layoutForContext(topContext)
        if anchorLayout['mode'] == 'hierarchical':
            topBlockKey = next(inst['instanceTypeKey']
                               for inst in instances.values()
                               if inst['container'] == '_topInstance')
            nodeDir = blockCondData[topBlockKey]['dir']
        else:
            nodeDir = ''
        for fileType, fileDef in fileMap.items():
            if fileDef.get('mode', 'block') != 'project':
                continue
            stemPath = expandNewModulePath(fileDef, nodeDir, '', '', anchorLayout,
                                           missingDirOk=True)
            rows.append(row(fileType, fileDef, 'project', stemPath,
                            contextOwningProject[topContext], anchorLayout))

    return rows


def getStaleSegmentFiles(prj, rows, blockCondData, fileMap, basePath):
    """The files fileMap says should exist under one project's own basePath
    segment, in the shapes newModule scaffolds; a generated file there
    outside this set is stale (left by a block, variant or instance rename).
    Returns (files, dirs) as absolute paths."""
    projectName = prj.config.getConfig('PROJECTNAME')
    layout = prj.projectLayout[projectName]

    dirs = set()
    files = set()
    segmentDef = next((fileDef for fileDef in fileMap.values()
                       if fileDef['basePath'] == basePath), None)
    if segmentDef is None:
        return files, dirs

    # Every owned block reserves its directory in the segment whether or not it
    # has an artifact, so a stale file in an emptied directory is still found.
    for condRow in blockCondData.values():
        if prj.contextOwningProject[condRow['_context']] != projectName:
            continue
        anyPath = expandNewModulePath(segmentDef, condRow['dir'],
                                      condRow['block'], '', layout,
                                      missingDirOk=True)
        dirs.add(os.path.dirname(anyPath))

    for row in rows:
        if row['fileDef']['basePath'] != basePath:
            continue
        if row['mode'] not in ('block', 'registrar'):
            continue
        if row['owner'] != projectName:
            continue
        files.update(row['files'].values())

    return files, dirs
