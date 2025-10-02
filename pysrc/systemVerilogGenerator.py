# systemVerilog specific generation
from pysrc.processYaml import existsLoad
from pysrc.textfileHelper import codeText
import argparse
from pysrc.arch2codeHelper import printError, warningAndErrorReport, printWarning
from pysrc.renderer import renderer
import re
class systemVerilogGenerator:
    renderer = None
    instances = None
    code = None
    dataTypeMappings = [
        {'maxSize': 1, 'type': 'uint8_t'},
        {'maxSize': 8, 'type': 'uint8_t'},
        {'maxSize': 16, 'type': 'uint16_t'},
        {'maxSize': 32, 'type': 'uint32_t'},
        {'maxSize': 64, 'type': 'uint64_t'},
        {'maxSize': 1024, 'type': 'uint64_t', 'arrayElementSize': 64}
    ]
    def __init__(self, prj, args):
        # get name of file containing renderer configuration
        # initialize the render object ready for later use
        self.renderer = renderer(prj, 'svConfig', docType='cpp' )
        # file containing list of instances to include in the generation was provided on the command line
        if args.instances:
            printWarning("The --instances option is not supported for systemC generation")
        fileName = args.file
        # setup the user source file helper object. This object will read in the file and chop it up into generated and non-generated pieces
        # the object will also find any generic parameters eg block name that will be the same for all pieces of the file that need rendering
        self.code = codeText(fileName, "//")
        print(f"Processing {fileName}")
        data = None
        importPackages = None
        context = None
        if not self.code.sections:
            # Gracefully skip files that do not have the appropriate GENERATED_CODE_ comments in them
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
        else:
            context = 'No context specified in GENERATED_CODE_PARAM'
        if not data:
            printError(f"In {fileName} there was no context or block specified in GENERATED_CODE_PARAM")
            exit(warningAndErrorReport())

        parser = argparse.ArgumentParser(description="SystemVerilog generated code parser", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        data['importPackages']  = importPackages
        data['context']         = context
        data['fileName']        = fileName

        genOut = self.renderer.renderSections(self, self.code, parser, prj, data, args)

    def _handler_generic(self, args, prj, data):
        vars = {'prj': prj, 'block': data, 'args': args}
        ret = self.renderer.render(args.template, vars)
        return ret
