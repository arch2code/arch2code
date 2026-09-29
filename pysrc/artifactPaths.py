"""Where a fileMap artifact lives on disk, and whether it applies to a block.
Every tool that writes or inspects generated files resolves both here, so
the path rule exists once."""

import os
from pysrc.arch2codeHelper import printError, printWarning, warningAndErrorReport
from pysrc.migrateCommon import userRegionLines, _regions, _find
from pysrc.variantSelection import standaloneVariantDescriptors

def fileNamePrefix(fileDefinition, layout):
    # The owning project's filename prefix for the entry's langDomain. A
    # project-mode name is a literal basename and takes none. Nor does a legacy
    # entry (migrateOrphans.LEGACY_FILEMAP): the file it names predates prefixes.
    if fileDefinition.get('mode', 'block') == 'project' or fileDefinition.get('legacy', False):
        return ''
    return layout['filePrefix'][fileDefinition['langDomain']]

def unprefixedStem(fileDefinition, moduleFileStub):
    # The artifact's name before the filename prefix. A C++ class named after
    # its file follows the fileMap name but not scFilePrefix.
    return f"{moduleFileStub}{fileDefinition.get('name', '')}"

def fileStem(fileDefinition, moduleFileStub, layout):
    # Artifact basename without extension. An SV artifact's design unit is
    # named by this same stem.
    return f"{fileNamePrefix(fileDefinition, layout)}{unprefixedStem(fileDefinition, moduleFileStub)}"

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
        # functional segment root outer, decomposition inner:
        #   $root/<segment>/<decomp>[/module]/file.
        if not os.path.exists(segment) and not missingDirOk:
            printError(f"path of {segment} does not exist")
        moduleDirAbs = os.path.abspath(os.path.join(segment, moduleDir))
    blockDir = fileDefinition.get('blockDir', False)
    if blockDir:
        moduleDirAbs = os.path.join(moduleDirAbs, module)
    fileName = fileStem(fileDefinition, moduleFileStub, layout)
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

def projectFileMaps(prj):
    # Each project's merged fileMap. A block's or context's artifacts follow
    # the fileMap of the project that owns it, the same as when that project
    # builds on its own.
    return {project: layout['fileMap'] for project, layout in prj.projectLayout.items()}

def configModuleFileDef(fileMap):
    # The owner-qualified Config module entry. ownerQualified marks both
    # owner-qualified registrar entries; the variant-bearing one is the SV wrapper top.
    (fileDef,) = [fd for fd in fileMap.values()
                  if fd.get('ownerQualified', False) and not fd.get('variant', False)]
    return fileDef

def artifactRows(prj, blockCondData, instances, fileMaps):
    """One row per generated artifact, over every project in the database.
    fileMaps holds a fileMap per project (projectFileMaps); an artifact is
    named by the entries of the project whose layout places it, and project-
    mode entries come from the project running the build. Fields:
    fileType/fileDef, mode, stem (the expandNewModulePath result), files
    {extKey: path}, owner, layout, blockKey/anchorKey, variant ('' when none),
    topModule (pairVlTop rows), context/includeEntries (context rows). The
    caller supplies blockCondData and instances so projectCreate (flatData)
    and projectOpen (data) both use it."""
    projectLayout = prj.projectLayout
    contextOwningProject = prj.contextOwningProject

    def layoutForContext(context):
        return projectLayout[contextOwningProject[context]]

    def entries(project, mode):
        return [(fileType, fileDef) for fileType, fileDef in fileMaps[project].items()
                if fileDef.get('mode', 'block') == mode]

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
        for fileType, fileDef in entries(owner, 'block'):
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
    if any(entries(project, 'registrar') for project in fileMaps):
        registrarPairs = prj.config.getConfig('REGISTRARPAIRS')
        for (assemblerKey, childKey), pair in registrarPairs.items():
            assemblerRow = blockCondData[assemblerKey]
            childRow = blockCondData[childKey]
            anchorLayout = layoutForContext(assemblerRow['_context'])
            owner = contextOwningProject[assemblerRow['_context']]
            registrarMap = entries(owner, 'registrar')
            for fileType, fileDef in registrarMap:
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
            for fileType, fileDef in registrarMap:
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
            for fileType, fileDef in entries(contextOwningProject[parentRow['_context']],
                                             'registrar'):
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
            for fileType, fileDef in entries(contextOwningProject[parentRow['_context']],
                                             'registrar'):
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
    for project in fileMaps:
        for fileType, fileDef in entries(project, 'context'):
            entriesByContext = dict()
            for ext in fileDef['ext']:
                expandedType = f"{fileType}_{ext}"
                if expandedType not in includeFiles:
                    continue
                for context, entry in includeFiles[expandedType].items():
                    if contextOwningProject[context] == project:
                        entriesByContext.setdefault(context, dict())[ext] = entry
            for context, extEntries in entriesByContext.items():
                stem = next(iter(extEntries.values()))['stem']
                rows.append(row(fileType, fileDef, 'context', stem, project,
                                layoutForContext(context),
                                context=context, includeEntries=extEntries))

    # Project mode: exactly one artifact per project-mode entry, at the top
    # context's node (hierarchical) or $root (functional). A definitions-only
    # project (no topInstance) has no top context and emits none.
    # A caller passing only block-mode entries may also pass a block subset
    # without the top block, so the anchor is resolved only when needed.
    topContext = prj.config.getConfig('TOPCONTEXT')
    buildProject = prj.config.getConfig('PROJECTNAME')
    projectEntries = entries(buildProject, 'project')
    if topContext is not None and projectEntries:
        anchorLayout = layoutForContext(topContext)
        if anchorLayout['mode'] == 'hierarchical':
            topBlockKey = next(inst['instanceTypeKey']
                               for inst in instances.values()
                               if inst['container'] == '_topInstance')
            nodeDir = blockCondData[topBlockKey]['dir']
        else:
            nodeDir = ''
        for fileType, fileDef in projectEntries:
            stemPath = expandNewModulePath(fileDef, nodeDir, '', '', anchorLayout,
                                           missingDirOk=True)
            rows.append(row(fileType, fileDef, 'project', stemPath,
                            contextOwningProject[topContext], anchorLayout))

    return rows


def currentArtifactRows(prj):
    """Every artifact the build names today, in every project, from a
    projectOpen handle. Migrate never deletes or moves onto one of these
    paths."""
    blockCondData = {k: prj.getBlockCondRow(k) for k in prj.data['blocks']}
    return artifactRows(prj, blockCondData, prj.data['instances'], projectFileMaps(prj))


def getStaleSegmentFiles(prj, rows, blockCondData, basePath):
    """The files the fileMap says should exist under one project's own
    basePath segment, in the shapes newModule scaffolds; a generated file there
    outside this set is stale (left by a block, variant or instance rename).
    Returns (files, dirs) as absolute paths."""
    projectName = prj.config.getConfig('PROJECTNAME')
    layout = prj.projectLayout[projectName]

    dirs = set()
    files = set()
    segmentDef = next((fileDef for fileDef in layout['fileMap'].values()
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


# Retired context-mode fileMap entries, keyed by the still-current entry whose
# artifact they were scaffolded beside. `config` (VariantConfig.h) carried no
# content but the include guard and markers, and sat beside the current entry's
# `<context>Includes.cppm` in both layouts, so that artifact's directory is
# where a surviving copy is found.
RETIRED_CONTEXT_SIBLINGS = {"include": [("VariantConfig", "h")]}


def retiredSiblingPaths(prj):
    """Absolute candidate paths of a retired context-mode artifact named in
    RETIRED_CONTEXT_SIBLINGS, one entry per still-current sibling context file
    this project owns, placed in the directory of that current file, in either
    layout."""
    projectName = prj.config.getConfig("PROJECTNAME")
    includeFiles = prj.config.getConfig("INCLUDEFILES")
    fileMap = prj.config.getConfig("FILEMAP")
    paths = set()
    for currentFileType, siblings in RETIRED_CONTEXT_SIBLINGS.items():
        for ext in fileMap[currentFileType]["ext"].values():
            expandedType = f"{currentFileType}_{ext}"
            if expandedType not in includeFiles:
                continue
            for context, entry in includeFiles[expandedType].items():
                if prj.contextOwningProject[context] != projectName:
                    continue
                placementDir = os.path.dirname(entry["fileName"])
                includeName = prj.includeName[context]
                for name, retiredExt in siblings:
                    paths.add(os.path.join(placementDir,
                                           f"{includeName}{name}.{retiredExt}"))
    return paths


def getRetiredContextFiles(prj):
    """Generated retired context siblings (see RETIRED_CONTEXT_SIBLINGS) in
    this project's owned include directories. Only a file carrying the retired
    `--template=config` region is reported, so a user file of that name is
    never touched. Returns absolute paths, sorted."""
    stale = set()
    for candidate in retiredSiblingPaths(prj):
        if not os.path.isfile(candidate):
            continue
        with open(candidate, 'r', errors='replace') as f:
            text = f.read()
        if 'GENERATED_CODE_BEGIN --template=config' in text:
            stale.add(os.path.abspath(candidate))
    return sorted(stale)


LEGACY_FW_OPEN = 'namespace fw_ns {'
LEGACY_FW_CLOSE = '} // end of namespace fw_ns'


def legacyFwWrapper(text):
    """Old firmware header scaffolds wrapped the constants, types, enums and
    structures regions in one `namespace fw_ns {` block of their own: opened
    between the headerIncludes and constants regions, closed after the last
    region by the scaffold's `} // end of namespace fw_ns` line. The regions now
    open the context's namespace under fw_ns, which that block would nest a
    second time. Returns the (open, close) line indices of that block, or None
    when the header does not have exactly that shape, so a user's own fw_ns
    block anywhere else is never taken for it."""
    regions = _regions(text)
    headerIncludes = _find(regions, 'structures', 'headerIncludes')
    constants = _find(regions, 'includes', 'constants')
    if headerIncludes is None or constants is None:
        return None
    lines = text.splitlines()
    opens = [i for i in range(headerIncludes.end + 1, constants.begin)
             if lines[i].strip() == LEGACY_FW_OPEN]
    closes = [i for i in range(regions[-1].end + 1, len(lines))
              if lines[i].strip() == LEGACY_FW_CLOSE]
    if len(opens) != 1 or len(closes) != 1:
        return None
    return opens[0], closes[0]


def unwrapLegacyFwHeader(text):
    """The legacy header with its scaffold-owned fw_ns block removed. User text
    that sat inside that block keeps its fw_ns scope: each non-blank user span
    between the block's open and close is wrapped in its own fw_ns block."""
    openIdx, closeIdx = legacyFwWrapper(text)
    lines = text.splitlines()
    spans = []
    for i, _ in userRegionLines(text):
        if not openIdx < i < closeIdx:
            continue
        if spans and spans[-1][-1] == i - 1:
            spans[-1].append(i)
        else:
            spans.append([i])
    wrapped = {span[0]: span[-1] for span in spans
               if any(lines[i].strip() for i in span)}
    out = []
    spanEnd = None
    for i, line in enumerate(lines):
        if i in (openIdx, closeIdx):
            continue
        if i in wrapped:
            out.append(LEGACY_FW_OPEN)
            spanEnd = wrapped[i]
        out.append(line)
        if i == spanEnd:
            out.append('} // namespace fw_ns')
            spanEnd = None
    return '\n'.join(out) + ('\n' if text.endswith('\n') else '')


def getLegacyFwHeaders(prj, rows):
    """Owned firmware headers still carrying the legacy scaffold-owned fw_ns
    block (see legacyFwWrapper). Returns absolute paths, sorted."""
    projectName = prj.config.getConfig('PROJECTNAME')
    legacy = set()
    for row in rows:
        if row['mode'] != 'context' or row['owner'] != projectName:
            continue
        if row['fileType'] != 'includeFW' or 'hdr' not in row['files']:
            continue
        path = row['files']['hdr']
        if not os.path.isfile(path):
            continue
        try:
            with open(path, 'r') as f:
                text = f.read()
        except UnicodeDecodeError as exc:
            printWarning(f"Skipping the legacy firmware header check of {path}: "
                         f"{exc.reason} at byte {exc.start}. If it still wraps its "
                         f"regions in the legacy fw_ns block, remove that block by hand.")
            continue
        if legacyFwWrapper(text) is not None:
            legacy.add(os.path.abspath(path))
    return sorted(legacy)
