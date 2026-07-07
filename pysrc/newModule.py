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
        if not prj.data.get("blocks"):
            return
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
        blockCondData = dict()
        for qualBlock in prj.data['blocks']:
            row = dict(prj.data['blocks'][qualBlock])
            row['hasOwnParams'] = int(bool(prj.getBlockConfigView(qualBlock)['hasOwnParams']))
            blockCondData[qualBlock] = row
        someBlock = next(iter(prj.data["blocks"])) # any random entry
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
                    if mode in ('block', 'registrar') and field not in blockCondData[someBlock]:
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
        filePath = processYaml.expandNewModulePath(fileDefinition, moduleDir, module, moduleFileStub, missingDirOk=True)
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
        for parentKey in sorted(parentChildren):
            parentDir = prj.data['blocks'][parentKey]['dir']
            for childKey in sorted(parentChildren[parentKey]):
                childBlock = prj.data['blocks'][childKey]['block']
                for fileKey, fileDefinition in registrarFileConfig.items():
                    if self._condMatch(fileDefinition, blockCondData[childKey]):
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
        filePath = processYaml.expandNewModulePath(fileDefinition, parentDir, childBlock, childBlock, missingDirOk=True)
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
