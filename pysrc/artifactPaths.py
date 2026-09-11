"""Where a fileMap artifact lives on disk, and whether it applies to a block.
Every tool that writes or inspects generated files resolves both here, so
the path rule exists once."""

import os
from pysrc.arch2codeHelper import printError, warningAndErrorReport

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

def getRegistrarFiles(prj, blockCondData, filemap):
    """Registrar files left behind by an instance rename or removal are not
    removed by gen or migrateOrphans. This is the set a project currently
    expects under its own registrar directories; a generated file there that
    is not in the set is stale. Returns (files, dirs) as absolute paths."""
    registrarPairs = prj.config.getConfig('REGISTRARPAIRS')
    configModules = prj.config.getConfig('CONFIGMODULES')
    projectName = prj.config.getConfig('PROJECTNAME')
    registrarSegmentMap = {k: v for k, v in filemap.items()
                           if v.get('mode', 'block') == 'registrar'
                           and v['basePath'] == 'registrar'}
    dirs = set()
    files = set()
    blockPairMap = {k: v for k, v in registrarSegmentMap.items()
                    if not v.get('foreignConfig', False)}
    configModuleMap = {k: v for k, v in registrarSegmentMap.items()
                       if v.get('foreignConfig', False)
                       and not v.get('variant', False)}
    layout = prj.projectLayout[projectName]
    # All registrar-segment fileDefs share basePath 'registrar', so one of them
    # expands each owned block's registrar directory; only its dirname is used.
    registrarDef = next(iter(registrarSegmentMap.values()))

    for blockRow in blockCondData.values():
        if prj.contextOwningProject[blockRow['_context']] != projectName:
            continue
        filePath = expandNewModulePath(registrarDef, blockRow['dir'],
                                       blockRow['block'], '', layout,
                                       missingDirOk=True)
        dirs.add(os.path.dirname(filePath))

    for (assemblerKey, childKey), pair in registrarPairs.items():
        assemblerRow = blockCondData[assemblerKey]
        if prj.contextOwningProject[assemblerRow['_context']] != projectName:
            continue
        childRow = blockCondData[childKey]
        for fileDef in blockPairMap.values():
            if not fileMapCondMatch(fileDef, childRow):
                continue
            if fileDef.get('requiresRegistrations', False) \
                    and not pair['aggregateHasModelRegistrations']:
                continue
            filePath = expandNewModulePath(fileDef, assemblerRow['dir'],
                                           childRow['block'], pair['artifactStem'],
                                           layout, missingDirOk=True)
            for ext in fileDef['ext'].values():
                files.add(filePath + '.' + ext)

    for (owner, childKey), entry in configModules.items():
        if owner != projectName:
            continue
        childRow = blockCondData[childKey]
        parentRow = blockCondData[entry['parentKey']]
        for fileDef in configModuleMap.values():
            if not fileMapCondMatch(fileDef, childRow):
                continue
            filePath = expandNewModulePath(fileDef, parentRow['dir'],
                                           childRow['block'], entry['stub'],
                                           layout, missingDirOk=True)
            for ext in fileDef['ext'].values():
                files.add(filePath + '.' + ext)
    return files, dirs
