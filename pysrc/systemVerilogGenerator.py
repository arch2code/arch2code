# systemVerilog specific generation
from pysrc.processYaml import existsLoad
from pysrc.textfileHelper import codeText
import argparse
from pysrc.arch2codeHelper import printError, warningAndErrorReport
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

        # docType ?
        self.renderer = renderer(prj, 'svConfig', docType='cpp' )
        if args.instances:
            instFile = args.instances
            # so load it
            instances = existsLoad(instFile)
            # convert the list of user fieldly instances into context qualified instances
            self.instances = prj.getQualInstances( instances['instances'] )
        else:
            # otherwise use the list of instances from the database
            self.instances = dict.fromkeys(prj.data['instances'], 0)

        prj.initConnections(self.instances)
        fileName = args.file
        self.code = codeText(fileName, "//")
        data = None
        parentModule = None
        importPackages = None
        contexts = None
        if not self.code.sections:
            # Gracefully skip files that do not have the appropriate GENERATED_CODE_ comments in them
            return
        if self.code.params.parentModule:
            parentModule = self.code.params.parentModule
        if self.code.params.importPackages:
            importPackages = self.code.params.importPackages
        if self.code.params.block and self.code.params.contexts:
            qualBlock = prj.getQualBlock( self.code.block )
            data = prj.getBlockData(qualBlock, self.instances)
            if not data:
                printError(f"In {fileName}, the block ({self.code.block}) specified in GENERATED_CODE_PARAM is either wrong or out of scope. Check the block is listed in your instances list")
                exit(warningAndErrorReport())
            contexts = self.code.params.contexts
            data.update(prj.getContextData(contexts, self.dataTypeMappings))
        elif self.code.params.block:
            qualBlock = prj.getQualBlock( self.code.block )
            data = prj.getBlockData(qualBlock, self.instances)
            if not data:
                printError(f"In {fileName}, the block ({self.code.block}) specified in GENERATED_CODE_PARAM is either wrong or out of scope. Check the block is listed in your instances list")
                exit(warningAndErrorReport())
        elif self.code.params.contexts:
            contexts = self.code.params.contexts
            data = prj.getContextData(contexts, self.dataTypeMappings)
        else:
            contexts = 'No context specified in GENERATED_CODE_PARAM'
        if not data:
            printError(f"In {fileName} there was no context or block specified in GENERATED_CODE_PARAM")
            exit(warningAndErrorReport())

        parser = argparse.ArgumentParser(description="SystemVerilog generated code parser", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

        data['parentModule']    = parentModule
        data['importPackages']  = importPackages
        data['contexts']        = contexts
        data['fileName']        = fileName
        if 'registerLeafInstance' in data:
            qualBlock = prj.getQualBlock(data['registerLeafInstance']['container'])
            data2 = prj.getBlockData(qualBlock, self.instances)
            data['includeContext'].update(data2['includeContext'])
            data['registers'] = data2['registers']

        genOut = self.renderer.renderSections(self, self.code, parser, prj, data, args)      

    def _handler_generic(self, args, prj, data):
        vars = {'prj': prj, 'block': data, 'args': args}
        ret = self.renderer.render(args.template, vars)
        return ret
