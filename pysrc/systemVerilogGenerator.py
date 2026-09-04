# systemVerilog specific generation
from pysrc.processYaml import existsLoad
from pysrc.textfileHelper import codeText
import argparse
from pathlib import Path
from pysrc.arch2codeHelper import printError, warningAndErrorReport, printWarning
from pysrc.renderer import renderer
import re

# RTL module-body templates emit `module <blockName>`; the generated file is
# expected to be named after that block. The consistency warning lives here,
# out of the template render path, so templates never inspect the output filename.
_MODULE_BODY_TEMPLATES = {'moduleInterfacesInstances', 'apbDecodeModule'}
class systemVerilogGenerator:
    renderer = None
    instances = None
    code = None
    dataTypeMappings = [
        {'maxSize': 1, 'unsignedType': 'uint8_t', 'signedType': 'int8_t'},
        {'maxSize': 8, 'unsignedType': 'uint8_t', 'signedType': 'int8_t'},
        {'maxSize': 16, 'unsignedType': 'uint16_t', 'signedType': 'int16_t'},
        {'maxSize': 32, 'unsignedType': 'uint32_t', 'signedType': 'int32_t'},
        {'maxSize': 64, 'unsignedType': 'uint64_t', 'signedType': 'int64_t'},
        {'maxSize': 1024, 'unsignedType': 'uint64_t', 'signedType': 'int64_t', 'arrayElementSize': 64}
    ]
    def __init__(self, prj, args):
        # get name of file containing renderer configuration
        # initialize the render object ready for later use
        self.renderer = renderer(prj, docType='cpp' )
        # file containing list of instances to include in the generation was provided on the command line
        if args.instances:
            printWarning("The --instances option is not supported for systemC generation")
        fileName = args.file
        # setup the user source file helper object. This object will read in the file and chop it up into generated and non-generated pieces
        # the object will also find any generic parameters eg block name that will be the same for all pieces of the file that need rendering
        self.code = codeText(fileName, "//")
        data = None
        importPackages = None
        context = None
        if not self.code.sections:
            # Gracefully skip files that do not have the appropriate GENERATED_CODE_ comments in them
            return
        # Ownership gate (mirrors systemcGen): skip a file owned by a different
        # project so a split build never regenerates (and clobbers) another
        # project's output. The owner is resolved from the DB (the file's context
        # -> contextOwningProject) keyed on the params on its GENERATED_CODE_PARAM
        # line, so it is absolute rather than relative to the current build root.
        # Files that resolve to no owning context return None and always generate,
        # preserving monolithic behaviour.
        projectName = prj.config.getConfig('PROJECTNAME')
        owner = prj.resolveFileOwner(self.code.params)
        if owner is not None and owner != projectName:
            return
        if self.code.params.importPackages:
            importPackages = self.code.params.importPackages
        if self.code.params.block and self.code.params.context:
            # get a block based view of the database. This is used for block definitions
            qualBlock = prj.getQualBlock( self.code.block )
            data = prj.getBlockData(qualBlock, trimRegLeafInstance=False)
            if not data:
                printError(f"In {fileName}, the block ({self.code.block}) specified in GENERATED_CODE_PARAM is either wrong or out of scope. Check the block is listed in your instances list")
                exit(warningAndErrorReport())
            context = self.code.params.context
            data.update(prj.getContextData(context, self.dataTypeMappings))
        elif self.code.params.block:
            qualBlock = prj.getQualBlock( self.code.block )
            data = prj.getBlockData(qualBlock, trimRegLeafInstance=False)
            if not data:
                printError(f"In {fileName}, the block ({self.code.block}) specified in GENERATED_CODE_PARAM is either wrong or out of scope. Check the block is listed in your instances list")
                exit(warningAndErrorReport())
        elif self.code.params.context:
            context = self.code.params.context
            data = prj.getContextData(context, self.dataTypeMappings)
        elif self.code.params.project:
            # Project-mode artifact (rtl.f): owns no block/context of its own; its
            # content enumerates the whole-build file list rooted at the top
            # context. The ownership gate above guarantees this file belongs to the
            # current build, so TOPCONTEXT names this build's top context directly
            # (no basename-stamp round-trip). getContextData takes a context list
            # and yields the same view the retired --context stamp produced.
            #
            # Invariant: rtl.f is the only SV project-mode artifact, and it is
            # rooted at the build's top context. That single-instance,
            # top-context-rooted contract is what lets this branch derive its
            # context from TOPCONTEXT alone; a second SV project-mode artifact, or
            # one not rooted at the top context, would break that derivation.
            context = [prj.config.getConfig('TOPCONTEXT')]
            data = prj.getContextData(context, self.dataTypeMappings)
        else:
            context = 'No context specified in GENERATED_CODE_PARAM'
        if not data:
            printError(f"In {fileName} there was no context or block specified in GENERATED_CODE_PARAM")
            exit(warningAndErrorReport())

        parser = argparse.ArgumentParser(description="SystemVerilog generated code parser", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        data['importPackages']  = importPackages
        data['context']         = context
        data['fileName']        = fileName

        self._checkFileNameMatchesBlock(prj, fileName)

        genOut = self.renderer.renderSections(self, self.code, parser, prj, data, args)

    @staticmethod
    def _sectionTemplate(section):
        for token in section['command'].split():
            if token.startswith('--template='):
                return token.split('=', 1)[1]
        return ''

    def _checkFileNameMatchesBlock(self, prj, fileName):
        if not self.code.params.block:
            return
        if not any(self._sectionTemplate(s) in _MODULE_BODY_TEMPLATES for s in self.code.sections):
            return
        blockName = prj.data['blocks'][prj.getQualBlock(self.code.block)]['block']
        stem = Path(fileName).resolve().stem
        if stem != blockName:
            printWarning(f'The file name {stem} does not match the block name {blockName}')

    def _handler_generic(self, args, prj, data):
        vars = {'prj': prj, 'block': data, 'args': args}
        ret = self.renderer.render(args.template, vars)
        return ret
