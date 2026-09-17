# file generation
# this file contains the templates neceesary to generate blank files for a new module
import pysrc.processYaml as processYaml
import pysrc.artifactPaths as artifactPaths
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

        fileMap = fileGenerationConfig['fileMap']
        rows = artifactPaths.artifactRows(prj, blockCondData, prj.data['instances'], fileMap)

        self.block_create_from_rows(fileGenerationConfig, rows, blockCondData, prj, args)
        self.registrar_create_from_rows(fileGenerationConfig, rows, prj, args)

        self.cleanup_stale_segment_files(prj, rows, blockCondData, fileMap, 'registrar')
        self.cleanup_stale_segment_files(prj, rows, blockCondData, fileMap, 'vl_wrap')
        self.cleanup_retired_context_files(prj, rows)

        self.project_create_from_rows(fileGenerationConfig, rows, prj, args)
        self.context_create_from_rows(fileGenerationConfig, rows, prj, args)

        # Create-once user-owned build makefiles. Distinct from the fileMap
        # passes above: these carry no generated regions, are written only when
        # absent, and are never rewritten or deleted afterwards.
        self.scaffold_create(fileGenerationConfig, prj, args)

    # Layout keys that name a project-scope convention directory rather than a
    # fileMap segment (see processYaml._buildLayoutFor).
    _LAYOUT_CONVENTION_KEYS = ('root', 'include', 'rundir', 'prj', 'yaml')

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

    def block_create_from_rows(self, fileGenerationConfig, rows, blockCondData, prj, args):
        projectName = prj.config.getConfig('PROJECTNAME')
        for row in rows:
            if row['mode'] != 'block':
                continue
            qualBlock = row['blockKey']
            block = prj.data['blocks'][qualBlock]['block']
            if row['owner'] != projectName:
                print(f"{block} owned by project '{row['owner']}', skipping (scaffold it from that project's rundir)")
                continue
            blockCond = blockCondData[qualBlock]
            data = dict()
            data['block'] = block
            data['qualBlock'] = qualBlock
            data['variants'] = list(prj.getStandaloneVariants(qualBlock))
            # Project-qualified module name for the scaffold's user-owned
            # `endmodule: <label>` so a freshly created block matches its
            # generator-emitted (qualified) module begin-label.
            data['blockModuleName'] = prj.blockModuleName[qualBlock]
            # A dutVariant artifact has no per-variant row; seed it with the
            # block's first declared variant so one pass scaffolds every
            # testbench.
            variant = row['variant'] or self._selectSingleVariant(row['fileDef'], prj, qualBlock, blockCond)
            data['variant'] = variant if variant else None
            self._writeRowFiles(fileGenerationConfig, row, data, prj, args)

    def _writeRowFiles(self, fileGenerationConfig, row, data, prj, args):
        for ext, filePathExt in row['files'].items():
            moduleDirAbs, fileName = os.path.split(filePathExt)
            if not os.path.exists(moduleDirAbs):
                os.makedirs(moduleDirAbs)
            if os.path.exists(filePathExt) and not args.overwrite:
                print(f"{filePathExt} exists so skipping, use --overwrite to overwrite")
            else:
                print(f"Making {fileName} at {moduleDirAbs} ")
                data['headerName'] = fileName
                data['target'] = row['fileType'] + "_" + ext
                data['targetDetails'] = row['fileDef']
                data['fileGeneration'] = fileGenerationConfig
                vars = {'prj': prj.data, 'block': data, 'args': args}
                newFileContents = self.renderer.render('fileGen', vars)
                with open(filePathExt, "w") as f:
                    f.write(newFileContents)

    def registrar_create_from_rows(self, fileGenerationConfig, rows, prj, args):
        for row in rows:
            if row['mode'] != 'registrar':
                continue
            data = dict()
            childBlock = prj.data['blocks'][row['blockKey']]['block']
            data['block'] = childBlock
            data['qualBlock'] = row['blockKey']
            data['variant'] = row['variant'] if row['variant'] else None
            data['parent'] = row['anchorKey']
            projectName = prj.config.getConfig('PROJECTNAME')
            if row['owner'] != projectName:
                fileDef = row['fileDef']
                # Skip-print label for a registrar row another project owns.
                if fileDef.get('ownerQualified', False):
                    label = 'Config module' if not fileDef.get('variant', False) else 'foreign registrar artifact'
                else:
                    label = 'registrar'
                print(f"{childBlock} {label} owned by project '{row['owner']}', skipping (scaffold it from that project's rundir)")
                continue
            self._writeRowFiles(fileGenerationConfig, row, data, prj, args)

    def cleanup_stale_segment_files(self, prj, rows, blockCondData, fileMap, basePath):
        # newmodule owns segment scaffolding, so it also deletes the generated
        # files in owned segment directories the current contract no longer
        # names.
        expectedFiles, segmentDirs = artifactPaths.getStaleSegmentFiles(
            prj, rows, blockCondData, fileMap, basePath)
        generatedInDirs, _ = migrateCommon.classifyGeneratedDir(segmentDirs)
        for staleFile in sorted(set(generatedInDirs) - expectedFiles):
            print(f"Removing stale {basePath} file {staleFile}")
            os.remove(staleFile)

    def cleanup_retired_context_files(self, prj, rows):
        for staleFile in artifactPaths.getRetiredContextFiles(prj, rows):
            print(f"Removing stale retired file {staleFile}")
            os.remove(staleFile)

    def project_create_from_rows(self, fileGenerationConfig, rows, prj, args):
        # One artifact per project, anchored at the top context; only the
        # project that owns the top context scaffolds it.
        projectName = prj.config.getConfig('PROJECTNAME')
        for row in rows:
            if row['mode'] != 'project':
                continue
            if row['owner'] != projectName:
                continue
            # The per-project artifact stamps its owning projectName as
            # --project; resolveFileOwner reads it directly.
            data = dict()
            data['project'] = projectName
            self._writeRowFiles(fileGenerationConfig, row, data, prj, args)

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

    def context_create_from_rows(self, fileGenerationConfig, rows, prj, args):
        projectName = prj.config.getConfig('PROJECTNAME')
        for row in rows:
            if row['mode'] != 'context':
                continue
            # Only the owning project scaffolds a context file, so its
            # --context stamp resolves in that project's own build.
            if row['owner'] != projectName:
                continue
            for ext, fileName in row['files'].items():
                entry = row['includeEntries'][ext]
                baseName = entry['baseName']
                moduleDirAbs = os.path.dirname(fileName)
                if not os.path.exists(moduleDirAbs):
                    os.makedirs(moduleDirAbs)
                if os.path.exists(fileName) and not args.overwrite:
                    print(f"{fileName} exists so skipping, use --overwrite to overwrite")
                else:
                    print(f"Making {baseName} at {moduleDirAbs} ")
                    data = dict()
                    data['target'] = f"{row['fileType']}_{ext}"
                    data['context'] = row['context']
                    # Context files carry --context (yamlContext key, for
                    # rendering) and --project (owning project, read by
                    # resolveFileOwner).
                    data['project'] = row['owner']
                    data['headerName'] = baseName
                    # Paired header basename for source artifacts, derived from
                    # the file type's ext map in saveIncludeFiles (filespec).
                    if 'siblingHeaderName' in entry:
                        data['siblingHeaderName'] = entry['siblingHeaderName']
                    data['fileGeneration'] = fileGenerationConfig
                    vars = {'prj': prj.data, 'block': data, 'args': args}
                    newFileContents = self.renderer.render('fileGen', vars)
                    with open(fileName, "w") as f:
                        f.write(newFileContents)
