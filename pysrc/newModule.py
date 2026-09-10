# file generation
# this file contains the templates neceesary to generate blank files for a new module
import pysrc.processYaml as processYaml
import pysrc.migrateCommon as migrateCommon
from pysrc.arch2codeHelper import printError, warningAndErrorReport
import os
import importlib
from pysrc.renderer import renderer

class newModule:
    renderer = None
    instances = None
    code = None
    #
    def __init__(self, prj, args):
        # iterate through the fileDefinitions and create the file names and file contents using the
        # same scheme as the renderer

        data = dict()
        fileGenerationConfig = prj.config.getConfig('FILEGENERATION', failOk=True)
        if not fileGenerationConfig:
            printError(f"fileGeneration section of project file must exist for this functionality to work, see example project file")
            exit(warningAndErrorReport())

        for key in ['fileMap', 'template', 'fileCopyrightStatement']:
            if key not in fileGenerationConfig:
                printError(f"fileGeneration section of project file must contain {key}")
                exit(warningAndErrorReport())
        # File-map conditions read scalar fields from the block row, plus the
        # derived `hasOwnParams` flag from the block config view.
        # `isParameterizable` and `defaultConfig` are persisted on the block
        # row by projectCreate.calcBlockConfigInfo() because they require a
        # transitive surface walk. `hasOwnParams` is the block's own `params:`
        # relationship — a cheap derivation that needs no persisted column, so
        # getBlockConfigView() surfaces it and it is overlaid here as a cond
        # scalar (routing own-params leaf blocks, emitted as class templates
        # whose member bodies must be module-visible, to a module interface
        # unit and all other blocks to .h/.cpp).
        # A definitions-only project (shared types/interfaces, no blocks or
        # instances) has no block rows; the block/registrar passes below then
        # iterate nothing, but the context artifacts (include/package/firmware)
        # are still created, so do not return early.
        blockCondData = dict()
        for qualBlock in prj.data.get('blocks', {}):
            blockCondData[qualBlock] = prj.getBlockCondRow(qualBlock)
        someBlock = next(iter(blockCondData), None) # any block row, or None when definitions-only
        for fileKey, fileDefinition in fileGenerationConfig['fileMap'].items():
            mode = fileDefinition.get('mode', 'block') 
            for key in ['basePath', 'name', 'ext']:
                if key not in fileDefinition:
                    printError(f"fileGeneration section of project file for file definition:{fileKey} in fileMap: must contain entry for {key}: ")
                    exit(warningAndErrorReport())
            cond = fileDefinition.get("cond", {})
            condAnd = fileDefinition.get("condAnd", {})
            if len(cond) > 0 or len(condAnd) > 0:
                # perform project file error checking vs schema
                both = dict(cond, **condAnd)
                for field, value in both.items():
                    if isinstance(value, bool):
                        both[field] = int(value)
                    # registrar mode applies cond/condAnd to the instantiated
                    # child block, so its fields come from the same block row
                    # data as block mode.
                    if mode in ('block', 'registrar') and someBlock is not None and field not in blockCondData[someBlock]:
                        printError(f"field {field} in cond does not exist in block file-generation data")
            basePathKey = fileDefinition.get('basePath', '')
            if not basePathKey in processYaml.dirMacros:
                printError(f"A basePath of {basePathKey} is not defined in the dirs section of the project file")
                exit(warningAndErrorReport())

        # parameters all checked
        # load the template file
        templateProg = processYaml.expandDirMacros(fileGenerationConfig['template'])
        templateDefinition = { 'templates': { 'fileGen': templateProg } }
        self.renderer = renderer(prj, docType='', directTemplate=templateDefinition)
        blockFileGenerationConfig = {k: v for k, v in fileGenerationConfig['fileMap'].items() if v.get('mode', 'block') == 'block'}
        for block, blockData in prj.blocks.items():
            data = dict()
            qualBlock = prj.getQualBlock(block)
            data['variants'] = list(prj.getStandaloneVariants(qualBlock))
            data['block'] = block
            data['qualBlock'] = qualBlock
            # Project-qualified module name for the scaffold's user-owned
            # `endmodule: <label>` so a freshly created block matches its
            # generator-emitted (qualified) module begin-label.
            data['blockModuleName'] = prj.blockModuleName[qualBlock]
            for fileKey, fileDefinition in blockFileGenerationConfig.items():
                if self._condMatch(fileDefinition, blockCondData[qualBlock]):
                    hasVariant = fileDefinition.get('variant', False)
                    if hasVariant and data['variants']:
                        for variant in data['variants']:
                            self.create_from_template(fileGenerationConfig, fileKey, fileDefinition, variant, True, prj, data, args)
                    elif hasVariant and blockCondData[qualBlock]['hasOwnParams']:
                        # Every variant is container-sourced: the registrar pass
                        # scaffolds the pair-qualified tops into this file instead.
                        continue
                    else:
                        # Single-emission artifacts are created once per block. A
                        # dutVariant artifact's variant is seeded from the block's
                        # own declarations, which keeps `make newmodule`
                        # project-wide: many testbenches in one pass with no
                        # global variant argument.
                        selectedVariant = self._selectSingleVariant(
                            fileDefinition, prj, qualBlock, blockCondData[qualBlock])
                        self.create_from_template(
                            fileGenerationConfig, fileKey, fileDefinition,
                            selectedVariant, False, prj, data, args)

        registrarFileGenerationConfig = {k: v for k, v in fileGenerationConfig['fileMap'].items() if v.get('mode', 'block') == 'registrar'}
        if registrarFileGenerationConfig:
            self.registrar_create_from_templates(fileGenerationConfig, registrarFileGenerationConfig, blockCondData, prj, args)
            self.cleanup_stale_registrar_files(blockCondData, prj)

        projectFileGenerationConfig = {k: v for k, v in fileGenerationConfig['fileMap'].items() if v.get('mode', 'block') == 'project'}
        if projectFileGenerationConfig:
            self.project_create_from_templates(fileGenerationConfig, projectFileGenerationConfig, prj, args)

        includeFiles = prj.config.getConfig('INCLUDEFILES')
        self.context_create_from_template(includeFiles, fileGenerationConfig, prj, args)

        # Create-once user-owned build makefiles. Distinct from the fileMap
        # passes above: these carry no generated regions, are written only when
        # absent, and are never rewritten or deleted afterwards.
        self.scaffold_create(fileGenerationConfig, prj, args)

    # Layout keys that name a project-scope convention directory rather than a
    # fileMap segment (see processYaml._buildLayoutFor).
    _LAYOUT_CONVENTION_KEYS = ('root', 'include', 'rundir', 'prj', 'yaml')

    def _condMatch(self, fileDefinition, condData):
        # The fileMap cond/condAnd predicate is shared with the build-manifest
        # derivation; see processYaml.fileMapCondMatch.
        return processYaml.fileMapCondMatch(fileDefinition, condData)

    def _selectSingleVariant(self, fileDefinition, prj, qualBlock, blockCond):
        # The variant bound into a single-emission artifact's generated-code
        # parameter, or None when the artifact names no DUT. A dutVariant artifact
        # names a variant the DUT block itself declares: the first in declaration
        # order is the skeleton default, which a user retargets by editing the
        # file's GENERATED_CODE_PARAM. A block that is parameterizable only
        # through a contained child at a frozen variant declares no params:, hence
        # no variant, and its testbench names none.
        if not fileDefinition.get('dutVariant', False):
            return None
        if not blockCond['isParameterizable']:
            return None
        ownVariants = prj.getQualBlockVariants(qualBlock)
        if not ownVariants:
            return None
        return ownVariants[0]

    def create_from_template(self, fileGenerationConfig, fileKey, fileDefinition, variant, variantFile, prj, data, args):
        # for each file target we need to build a path and filename to perform file template creation
        # the filename itself is based on the module name with prefix and suffixes applied
        module = data['block']
        moduleFileStub = module
        qualModule = data['qualBlock']
        moduleDir = prj.data['blocks'][qualModule]['dir']
        if variant:
            data['variant'] = variant
        else:
            data['variant'] = None
        if variantFile:
            moduleFileStub += '_' + data['variant']
        # Resolve under the layout of the project that owns this block (the
        # project that owns the block's defining context).
        owner = prj.contextOwningProject[prj.data['blocks'][qualModule]['_context']]
        # Ownership gate (mirrors the systemcGen/systemVerilog generation gates):
        # skip a block owned by a different project so a build never scaffolds
        # across the ownership boundary. The owner comes from the block context ->
        # contextOwningProject, keyed absolutely, so it is stable regardless of
        # the current build root.
        projectName = prj.config.getConfig('PROJECTNAME')
        if owner != projectName:
            print(f"{module} owned by project '{owner}', skipping (scaffold it from that project's rundir)")
            return
        layout = prj.projectLayout[owner]
        filePath = processYaml.expandNewModulePath(fileDefinition, moduleDir, module, moduleFileStub, layout, missingDirOk=True)
        moduleDirAbs = os.path.dirname(filePath)
        for ext in fileDefinition['ext']:
            filePathExt = filePath + "." + fileDefinition['ext'][ext]
            fileName = os.path.basename(filePathExt)
            if not os.path.exists(moduleDirAbs):
                os.makedirs(moduleDirAbs)
            if os.path.exists(filePathExt) and not args.overwrite:
                print(f"{filePathExt} exists so skipping, use --overwrite to overwrite")
            else:
                print(f"Making {fileName} at {moduleDirAbs} ")
                # make the file contents
                data['target'] = fileKey + "_" + ext
                data['targetDetails'] = fileDefinition
                data['fileGeneration'] = fileGenerationConfig
                vars = {'prj': prj.data, 'block': data, 'args': args}
                newFileContents = self.renderer.render('fileGen', vars)
                with open(filePathExt, "w") as f:
                    f.write(newFileContents)

    def registrar_create_from_templates(self, fileGenerationConfig, registrarFileConfig, blockCondData, prj, args):
        # Registrar artifacts belong to a qualified parent-child pair. Their
        # persisted stems remain distinct when one directory hosts several
        # parents using the same child.
        blockFileConfig = {k: v for k, v in registrarFileConfig.items()
                           if not v.get('foreignConfig', False)
                           and not v.get('pairVlTop', False)}
        for parentKey, childKey in sorted(prj.registrarPairs):
            parentDir = prj.data['blocks'][parentKey]['dir']
            childBlock = prj.data['blocks'][childKey]['block']
            pair = prj.registrarPairs[(parentKey, childKey)]
            for fileKey, fileDefinition in blockFileConfig.items():
                if not self._condMatch(fileDefinition, blockCondData[childKey]):
                    continue
                if fileDefinition.get('requiresRegistrations', False) \
                        and not pair['aggregateHasModelRegistrations']:
                    continue
                self.create_registrar_file(
                    fileGenerationConfig, fileKey, fileDefinition,
                    parentDir, childBlock, childKey, parentKey, prj, args)
        pairVlConfig = {k: v for k, v in registrarFileConfig.items()
                        if v.get('pairVlTop', False)}
        for parentKey, childKey in sorted(prj.registrarPairs):
            pair = prj.registrarPairs[(parentKey, childKey)]
            childBlock = prj.data['blocks'][childKey]['block']
            parentDir = prj.data['blocks'][parentKey]['dir']
            for fileKey, fileDefinition in pairVlConfig.items():
                if not self._condMatch(fileDefinition, blockCondData[childKey]):
                    continue
                for registration in pair['verifRegistrations']:
                    if not registration['pairSpecific']:
                        continue
                    self.create_registrar_file(
                        fileGenerationConfig, fileKey, fileDefinition,
                        parentDir, childBlock, childKey, parentKey, prj, args,
                        variant=registration['variant'])
        self.config_create_from_templates(
            fileGenerationConfig, registrarFileConfig, blockCondData, prj, args)

    def cleanup_stale_registrar_files(self, blockCondData, prj):
        # newmodule owns registrar scaffolding, so it also deletes generated files
        # in owned registrar directories that the current contract no longer names.
        registrarFiles, registrarDirs = processYaml.getRegistrarFiles(
            prj, blockCondData, prj.filemap)
        generatedInDirs, _ = migrateCommon.classifyGeneratedDir(registrarDirs)
        for staleFile in sorted(set(generatedInDirs) - registrarFiles):
            print(f"Removing stale registrar file {staleFile}")
            os.remove(staleFile)

    def config_create_from_templates(self, fileGenerationConfig, registrarFileConfig,
                                     blockCondData, prj, args):
        # foreignConfig: true marks two artifact families; the variant: flag tells them apart.
        foreignFileConfig = {k: v for k, v in registrarFileConfig.items()
                             if v.get('foreignConfig', False)}
        configModuleFileConfig = {k: v for k, v in foreignFileConfig.items()
                                  if not v.get('variant', False)}
        vlWrapFileConfig = {k: v for k, v in foreignFileConfig.items()
                           if v.get('variant', False)}
        projectName = prj.config.getConfig('PROJECTNAME')

        def scaffoldPairs(fileConfig, headers, artifactLabel):
            for (owner, childKey), entry in sorted(headers.items()):
                childBlock = prj.data['blocks'][childKey]['block']
                if owner != projectName:
                    print(f"{childBlock} {artifactLabel} owned by project '{owner}', skipping (scaffold it from that project's rundir)")
                    continue
                parentKey = entry['parentKey']
                parentDir = prj.data['blocks'][parentKey]['dir']
                for fileKey, fileDefinition in fileConfig.items():
                    if not self._condMatch(fileDefinition, blockCondData[childKey]):
                        continue
                    variants = entry['vlVariants'] \
                        if fileDefinition.get('variant', False) else [None]
                    for variant in variants:
                        self.create_registrar_file(
                            fileGenerationConfig, fileKey, fileDefinition,
                            parentDir, childBlock, childKey, parentKey, prj, args,
                            variant=variant, configEntry=entry)

        scaffoldPairs(configModuleFileConfig, prj.config.getConfig('CONFIGMODULES'),
                     'Config module')
        scaffoldPairs(vlWrapFileConfig, prj.config.getConfig('FOREIGNCONFIGHEADERS'),
                     'foreign registrar artifact')

    def create_registrar_file(self, fileGenerationConfig, fileKey, fileDefinition, parentDir, childBlock, childQualBlock, parentKey, prj, args, variant=None, configEntry=None):
        # Build the registrar path: the child-named trampoline lands under the
        # parent's directory within the registrar root.
        data = dict()
        data['block'] = childBlock
        data['qualBlock'] = childQualBlock
        data['variant'] = variant
        data['parent'] = parentKey
        # The trampoline is parent-owned: it lands under the assembler's
        # directory, so it resolves under the parent (assembler) project layout.
        owner = prj.contextOwningProject[prj.data['blocks'][parentKey]['_context']]
        # Ownership gate: skip a parent-owned registrar file when the assembler
        # is owned by a different project so a build never scaffolds across the
        # ownership boundary (mirrors the generation gates).
        projectName = prj.config.getConfig('PROJECTNAME')
        if owner != projectName:
            print(f"{childBlock} registrar owned by project '{owner}', skipping (scaffold it from that project's rundir)")
            return
        layout = prj.projectLayout[owner]
        if fileDefinition.get('foreignConfig', False):
            fileStub = configEntry['stub']
        elif fileDefinition.get('pairVlTop', False):
            registrations = prj.registrarPairs[
                (parentKey, childQualBlock)]['verifRegistrations']
            registration = next(
                entry for entry in registrations if entry['variant'] == variant)
            fileStub = registration['physicalFileStub']
        else:
            fileStub = prj.registrarPairs[
                (parentKey, childQualBlock)]['artifactStem']
        # A variant:true foreign artifact (per-variant SV verilated wrapper top)
        # appends the variant to its owner-qualified stub, mirroring the block
        # mode variant-file stub, so each foreign variant is a distinct file/top.
        if variant and not fileDefinition.get('pairVlTop', False):
            fileStub += '_' + variant
        filePath = processYaml.expandNewModulePath(fileDefinition, parentDir, childBlock, fileStub, layout, missingDirOk=True)
        moduleDirAbs = os.path.dirname(filePath)
        for ext in fileDefinition['ext']:
            filePathExt = filePath + "." + fileDefinition['ext'][ext]
            fileName = os.path.basename(filePathExt)
            if not os.path.exists(moduleDirAbs):
                os.makedirs(moduleDirAbs)
            if os.path.exists(filePathExt) and not args.overwrite:
                print(f"{filePathExt} exists so skipping, use --overwrite to overwrite")
            else:
                print(f"Making {fileName} at {moduleDirAbs} ")
                data['headerName'] = fileName
                data['target'] = fileKey + "_" + ext
                data['targetDetails'] = fileDefinition
                data['fileGeneration'] = fileGenerationConfig
                vars = {'prj': prj.data, 'block': data, 'args': args}
                newFileContents = self.renderer.render('fileGen', vars)
                with open(filePathExt, "w") as f:
                    f.write(newFileContents)

    def project_create_from_templates(self, fileGenerationConfig, projectFileConfig, prj, args):
        # Project mode: exactly one artifact per project, placed at its basePath
        # segment root and keyed to the project's top context (the design's root
        # context whose include chain spans the whole build). A definitions-only
        # project (no topInstance) has no top context and emits nothing.
        topContext = prj.config.getConfig('TOPCONTEXT')
        if topContext is None:
            return
        # Ownership gate (mirrors the block/registrar scaffolds): only the project
        # that owns the top context scaffolds its per-project artifact, so a
        # composed build never creates a referenced child project's copy.
        owner = prj.contextOwningProject[topContext]
        projectName = prj.config.getConfig('PROJECTNAME')
        if owner != projectName:
            return
        layout = prj.projectLayout[owner]
        # In hierarchical layout the single per-project artifact anchors to the
        # top context's node directory: the persisted node dir of the top block
        # (the block topInstance instantiates), whose defining context is the
        # top context, so this is the same node dir block mode derives for a
        # block in that context. Anchoring here keeps the artifact's node-
        # relative functional segment inside the project tree rather than
        # resolving against the process cwd. Functional layout uses $root-
        # absolute segments, so it needs no node anchor (empty moduleDir).
        if layout['mode'] == 'hierarchical':
            topBlockKey = next(row['instanceTypeKey']
                               for row in prj.data['instances'].values()
                               if row['container'] == '_topInstance')
            nodeDir = prj.data['blocks'][topBlockKey]['dir']
        else:
            nodeDir = ''
        # The per-project artifact stamps its owning projectName directly on the
        # GENERATED_CODE_PARAM line (--project). Owner resolution then reads that
        # name without a context/basename round-trip. projectName is the owner
        # resolved above (the project that owns the top context).
        for fileKey, fileDefinition in projectFileConfig.items():
            self.create_project_file(fileGenerationConfig, fileKey, fileDefinition, projectName, nodeDir, layout, prj, args)

    def create_project_file(self, fileGenerationConfig, fileKey, fileDefinition, projectName, nodeDir, layout, prj, args):
        # The single per-project artifact lands at its segment root with no
        # module file stub, so the filename is composed purely from the fileMap
        # name + ext (e.g. rtl + f -> rtl.f). nodeDir is the top context's node
        # directory in hierarchical layout (so the segment resolves inside the
        # project tree) and empty in functional layout (segments are $root-
        # absolute).
        data = dict()
        data['project'] = projectName
        filePath = processYaml.expandNewModulePath(fileDefinition, nodeDir, '', '', layout, missingDirOk=True)
        moduleDirAbs = os.path.dirname(filePath)
        for ext in fileDefinition['ext']:
            filePathExt = filePath + "." + fileDefinition['ext'][ext]
            fileName = os.path.basename(filePathExt)
            if not os.path.exists(moduleDirAbs):
                os.makedirs(moduleDirAbs)
            if os.path.exists(filePathExt) and not args.overwrite:
                print(f"{filePathExt} exists so skipping, use --overwrite to overwrite")
            else:
                print(f"Making {fileName} at {moduleDirAbs} ")
                data['headerName'] = fileName
                data['target'] = fileKey + "_" + ext
                data['targetDetails'] = fileDefinition
                data['fileGeneration'] = fileGenerationConfig
                vars = {'prj': prj.data, 'block': data, 'args': args}
                newFileContents = self.renderer.render('fileGen', vars)
                with open(filePathExt, "w") as f:
                    f.write(newFileContents)

    def _deriveTopModules(self, prj):
        # Best-effort scaffold defaults for the shared.mk identity variables.
        # TB_TOP_MODULE is the design's top block (the block instanced at
        # _topInstance). HDL_TOP_MODULE is that top block's single RTL/verilated
        # child when unambiguous, else it falls back to the top block. Both are
        # create-once, user-editable defaults, so a definitions-only project (no
        # topInstance) simply uses the project name.
        projectName = prj.config.getConfig('PROJECTNAME')
        topBlockKey = next((row['instanceTypeKey']
                            for row in prj.data['instances'].values()
                            if row['container'] == '_topInstance'), None)
        if topBlockKey is None:
            return projectName, projectName
        tbTop = prj.data['blocks'][topBlockKey]['block']
        dutBlocks = {row['instanceTypeKey']
                     for row in prj.data['instances'].values()
                     if row['containerKey'] == topBlockKey
                     and (prj.data['blocks'][row['instanceTypeKey']]['hasRtl']
                          or prj.data['blocks'][row['instanceTypeKey']]['hasVl'])}
        if len(dutBlocks) == 1:
            hdlTop = prj.data['blocks'][next(iter(dutBlocks))]['block']
        else:
            hdlTop = tbTop
        return tbTop, hdlTop

    def scaffold_create(self, fileGenerationConfig, prj, args):
        # Write the project's user-owned build makefiles once. Each file is
        # emitted only if absent and is NEVER rewritten or deleted afterwards
        # (--overwrite is deliberately ignored): the user owns their make
        # structure and must not be pestered. A repeated migrate/newmodule on a
        # project that already has its makefiles is therefore a silent no-op.
        scaffoldConfig = fileGenerationConfig['scaffold']
        projectName = prj.config.getConfig('PROJECTNAME')
        layout = prj.projectLayout[projectName]
        tbTop, hdlTop = self._deriveTopModules(prj)

        templateProg = processYaml.expandDirMacros(scaffoldConfig['template'])
        scaffoldRenderer = renderer(
            prj, docType='', directTemplate={'templates': {'scaffold': templateProg}})

        for fileKey, fileDef in scaffoldConfig['files'].items():
            place = fileDef['place']
            if place in layout['segments']:
                baseDir = layout['segments'][place]['path']
            elif place in self._LAYOUT_CONVENTION_KEYS:
                baseDir = layout[place]
            else:
                printError(f"scaffold file {fileKey} references place '{place}' "
                           f"that is not a layout segment or convention")
                exit(warningAndErrorReport())
            # A node-relative segment (hierarchical layout) anchors at the project
            # root so the project-scope makefile never resolves against the cwd.
            if not os.path.isabs(baseDir):
                baseDir = os.path.join(layout['root'], baseDir)
            filePath = os.path.join(baseDir, fileDef['sub'])
            if os.path.exists(filePath):
                continue
            moduleDirAbs = os.path.dirname(filePath)
            if not os.path.exists(moduleDirAbs):
                os.makedirs(moduleDirAbs)
            print(f"Scaffolding {filePath}")
            data = {
                'target': fileKey,
                'projectName': projectName,
                'tbTop': tbTop,
                'hdlTop': hdlTop,
            }
            vars = {'prj': prj.data, 'block': data, 'args': args}
            newFileContents = scaffoldRenderer.render('scaffold', vars)
            with open(filePath, "w") as f:
                f.write(newFileContents)

    def context_create_from_template(self, files, fileGeneration, prj, args):
        # for each file target we need to build a path and filename to perform file template creation
        # the filename itself is based on the module name with prefix and suffixes applied

        projectName = prj.config.getConfig('PROJECTNAME')
        for fileKey, fileKeyData in files.items():
            for context, fileDefinition in fileKeyData.items():
                # Ownership gate (mirrors restampContextParam/_contextModeFiles and
                # the render gate): only scaffold contexts this project owns, so a
                # composed build never lays down a child's context file stamped with
                # a parent-relative --context the child's own build cannot resolve.
                # INCLUDEFILES is keyed identically to contextOwningProject.
                if prj.contextOwningProject[context] != projectName:
                    continue
                baseName = fileDefinition['baseName']
                fileName = fileDefinition['fileName']
                moduleDirAbs = os.path.dirname(fileName)
                if not os.path.exists(moduleDirAbs):
                    os.makedirs(moduleDirAbs)
                if os.path.exists(fileName) and not args.overwrite:
                    print(f"{fileName} exists so skipping, use --overwrite to overwrite")
                else:
                    print(f"Making {baseName} at {moduleDirAbs} ")
                    # make the file contents
                    data = dict()
                    data['target'] = fileKey
                    data['context'] = context
                    # Context files carry BOTH --context (canonical yamlContext
                    # key, used for rendering) and --project (the context's
                    # owning project, used directly by resolveFileOwner). context
                    # is the INCLUDEFILES key, keyed identically to
                    # contextOwningProject.
                    data['project'] = prj.contextOwningProject[context]
                    data['headerName'] = baseName
                    # Paired header basename for source artifacts, derived from
                    # the file type's ext map in saveIncludeFiles (filespec).
                    if 'siblingHeaderName' in fileDefinition:
                        data['siblingHeaderName'] = fileDefinition['siblingHeaderName']
                    data['fileGeneration'] = fileGeneration
                    vars = {'prj': prj.data, 'block': data, 'args': args}
                    newFileContents = self.renderer.render('fileGen', vars)
                    with open(fileName, "w") as f:
                        f.write(newFileContents)
