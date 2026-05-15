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
        # File-map conditions read schema fields from the block row.
        # `isParameterizable` and `defaultConfig` are persisted on the
        # block row by projectCreate.calcBlockConfigInfo(); no derived
        # view is required.
        blockCondData = {
            qualBlock: dict(prj.data['blocks'][qualBlock])
            for qualBlock in prj.data['blocks']
        }
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
                    if mode == 'block' and field not in blockCondData[someBlock]:
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
                cond = fileDefinition.get("cond", None)
                condAnd = fileDefinition.get("condAnd", None)
                makeFile = not cond # of there is no or cond, then we will make the file by default
                # no and or or cond - make file
                # or cond - make file if any of the cond is true
                # and cond - make file if all of the cond are true
                # if there is both or and and cond, then we will make the file if any of the or cond is true and all of the and cond are true
                if cond:
                    for field, value in cond.items():
                        if blockCondData[qualBlock][field] == value:
                            makeFile = True 
                            break
                if condAnd:
                    for field, value in condAnd.items():
                        if blockCondData[qualBlock][field] != value:
                            makeFile = False
                            break
                if makeFile:
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

        includeFiles = prj.config.getConfig('INCLUDEFILES')
        self.context_create_from_template(includeFiles, fileGenerationConfig, prj, args)

    _TB_FILE_KEYS = ('testBench', 'tbConfig', 'tbExternal')

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
                    data['fileGeneration'] = fileGeneration
                    vars = {'prj': prj.data, 'block': data, 'args': args}
                    newFileContents = self.renderer.render('fileGen', vars)
                    with open(fileName, "w") as f:
                        f.write(newFileContents)
