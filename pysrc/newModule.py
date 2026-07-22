# file generation
# this file contains the templates neceesary to generate blank files for a new module
import pysrc.processYaml as processYaml
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
            row = dict(prj.data['blocks'][qualBlock])
            row['hasOwnParams'] = int(bool(prj.getBlockConfigView(qualBlock)['hasOwnParams']))
            blockCondData[qualBlock] = row
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
            data['variants'] = prj.getQualBlockVariants(qualBlock)
            data['block'] = block
            data['qualBlock'] = qualBlock
            for fileKey, fileDefinition in blockFileGenerationConfig.items():
                if self._condMatch(fileDefinition, blockCondData[qualBlock]):
                    hasVariant = fileDefinition.get('variant', False)
                    if hasVariant and data['variants']:
                        for variant in data['variants']:
                            self.create_from_template(fileGenerationConfig, fileKey, fileDefinition, variant, True, prj, data, args)
                    else:
                        # Single-emission testbench artifacts are created exactly
                        # once per block. When that block has own variants, seed
                        # the skeleton with the first declared variant for this
                        # block.
                        # This keeps `make newmodule` project-wide: multiple TBs can
                        # be created in one pass without a global variant argument,
                        # and users can edit the file-level GENERATED_CODE_PARAM if
                        # they want a different DUT variant for a specific TB.
                        selectedVariant = self._selectSingleVariant(
                            fileKey, data, blockCondData[qualBlock])
                        self.create_from_template(
                            fileGenerationConfig, fileKey, fileDefinition,
                            selectedVariant, False, prj, data, args)

        registrarFileGenerationConfig = {k: v for k, v in fileGenerationConfig['fileMap'].items() if v.get('mode', 'block') == 'registrar'}
        if registrarFileGenerationConfig:
            self.registrar_create_from_templates(fileGenerationConfig, registrarFileGenerationConfig, blockCondData, prj, args)

        includeFiles = prj.config.getConfig('INCLUDEFILES')
        self.context_create_from_template(includeFiles, fileGenerationConfig, prj, args)

    _TB_FILE_KEYS = ('testBench', 'tbConfig', 'tbExternal')

    def _condMatch(self, fileDefinition, condData):
        # The fileMap cond/condAnd predicate is shared with the build-manifest
        # derivation; see processYaml.fileMapCondMatch.
        return processYaml.fileMapCondMatch(fileDefinition, condData)

    def _selectSingleVariant(self, fileKey, data, blockCond):
        # Return the variant string (or None) to bind into the generated-code
        # parameter of a single-emission artifact. Only the testbench family
        # binds a DUT variant; other single-emission file types stay variant-
        # agnostic. Non-parameterizable blocks pass through as None. For
        # parameterizable TBs, use the first variant in the block's declaration
        # order as a useful skeleton default rather than making `newmodule`
        # depend on one global variant selection.
        if fileKey not in self._TB_FILE_KEYS:
            return None
        if not blockCond['isParameterizable']:
            return None
        if not data['variants']:
            return None
        return next(iter(data['variants']))

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
        # A registrar trampoline TU is owned by the assembling block, not the
        # leaf: for every distinct parameterizable child an assembler
        # instantiates, one `<child>Registrar.cpp` is emitted under the
        # assembler's directory in the `registrar` root (mirroring how `base`
        # mirrors the yaml directory tree). The trampoline is keyed on the child
        # block (`--block=<child>`), so the same child reused under two
        # assemblers yields two independent compilations of the same
        # registration — the accepted-duplication case (factory emplace is
        # first-wins).
        parentChildren = dict()
        for inst in prj.data['instances'].values():
            containerKey = inst['containerKey']
            # The synthetic project-root container is not a block and owns no
            # registrar; skip any container that is not a defined block.
            if containerKey not in prj.data['blocks']:
                continue
            parentChildren.setdefault(containerKey, set()).add(inst['instanceTypeKey'])
        # Owner-qualified foreign-Config headers, keyed (owningProject, child) ->
        # module file stub. Computed once in projectCreate under the same emit gate
        # the config emitter uses, so the scaffold never creates a header the
        # emitter would not produce. Dedup below because a project with two
        # assembler blocks of one child hits the same pair twice.
        foreignConfigHeaders = prj.config.getConfig('FOREIGNCONFIGHEADERS')
        emittedForeign = set()
        projectName = prj.config.getConfig('PROJECTNAME')
        for parentKey in sorted(parentChildren):
            parentDir = prj.data['blocks'][parentKey]['dir']
            for childKey in sorted(parentChildren[parentKey]):
                childBlock = prj.data['blocks'][childKey]['block']
                for fileKey, fileDefinition in registrarFileConfig.items():
                    if not self._condMatch(fileDefinition, blockCondData[childKey]):
                        continue
                    if fileDefinition.get('foreignConfig', False):
                        # Only the declaring assembler project scaffolds it.
                        owner = prj.contextOwningProject[prj.data['blocks'][parentKey]['_context']]
                        # Ownership gate: the foreign-config header is parent-owned;
                        # skip it when the assembler is owned by a different project
                        # so a build never scaffolds across the ownership boundary.
                        if owner != projectName:
                            print(f"{childBlock} foreign-config header owned by project '{owner}', skipping (scaffold it from that project's rundir)")
                            continue
                        if (owner, childKey) not in foreignConfigHeaders:
                            continue
                        if (owner, childKey) in emittedForeign:
                            continue
                        emittedForeign.add((owner, childKey))
                    self.create_registrar_file(
                        fileGenerationConfig, fileKey, fileDefinition,
                        parentDir, childBlock, childKey, parentKey, prj, args)

    def create_registrar_file(self, fileGenerationConfig, fileKey, fileDefinition, parentDir, childBlock, childQualBlock, parentKey, prj, args):
        # Build the registrar path: the child-named trampoline lands under the
        # parent's directory within the registrar root.
        data = dict()
        data['block'] = childBlock
        data['qualBlock'] = childQualBlock
        data['variant'] = None
        data['parent'] = prj.data['blocks'][parentKey]['block']
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
        # The owner-qualified foreign-Config header stub is the persisted identity
        # from calcForeignConfigHeaders (declaring project prefixed onto the child
        # so its basename cannot collide with the child-owned context config header
        # on the shared registrar include path); the gate above guarantees the pair
        # is present when foreignConfig is set.
        if fileDefinition.get('foreignConfig', False):
            fileStub = prj.config.getConfig('FOREIGNCONFIGHEADERS')[(owner, childQualBlock)]['stub']
        else:
            fileStub = childBlock
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

    def context_create_from_template(self, files, fileGeneration, prj, args):
        # for each file target we need to build a path and filename to perform file template creation
        # the filename itself is based on the module name with prefix and suffixes applied

        for fileKey, fileKeyData in files.items():
            for context, fileDefinition in fileKeyData.items():
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
