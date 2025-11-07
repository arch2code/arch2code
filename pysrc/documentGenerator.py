from pysrc.textfileHelper import codeText
from pysrc.renderer import renderer
import argparse
from pysrc.arch2codeHelper import printError, warningAndErrorReport
import os

class documentGenerator:
    prj = None
    renderer = None
    instances = None
    data = None
    code = None
    def __init__(self, prj, args) -> None:
        pass

        self.prj = prj
        self.renderer = renderer(prj, 'docConfig', docType='asciidoctor')

        # otherwise use the list of instances from the database
        self.instances = dict.fromkeys(prj.data['instances'], 0)
        prj.initConnections(self.instances)

        self.code = codeText(args.file, "//")
        fileName = os.path.basename(args.file)

        if not self.code.block:
                printError(f"In {fileName}, the block ({self.code.block}) specified in GENERATED_CODE_PARAM is either wrong or out of scope. Check the block is listed in your instances list")
                exit(warningAndErrorReport())
        else:
            qualBlock = prj.getQualBlock( self.code.block )
            if self.code.template == 'blockSpecification':
                self.data = prj.getBlockDataOld(qualBlock, self.instances)
            else:
                self.data = prj.getBlockDataHier(qualBlock, trimRegLeafInstance=True, excludeInstances=[])

        args.fileName = fileName
        parser = argparse.ArgumentParser(description="Document generated code parser", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        self.renderer.renderSections(self, self.code, parser, prj, self.data, args)

    def _handler_generic(self, args, prj, data):
        vars = {'prj': prj, 'block': data, 'args': args}
        ret = self.renderer.render(args.template, vars)
        return ret