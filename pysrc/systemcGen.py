# systemC specific generation
from pysrc.processYaml import existsLoad
from pysrc.textfileHelper import codeText
import argparse
from pysrc.arch2codeHelper import printError, warningAndErrorReport
from pysrc.renderer import renderer
import re
import os
class genSystemC:
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
        self.renderer = renderer(prj, 'cppConfig', docType='cpp' )
        # file containing list of instances to include in the generation was provided on the command line
        if args.instances:
            instFile = args.instances
            # so load it
            instances = existsLoad(instFile)
            # convert the list of user fieldly instances into context qualified instances
            self.instances = prj.getQualInstances( instances['instances'] )
        else:
            # otherwise use the list of instances from the database
            self.instances = dict.fromkeys(prj.data['instances'], 0)
        # set up connection info
        prj.initConnections(self.instances)
        fileName = args.file
        # setup the user source file helper object. This object will read in the file and chop it up into generated and non-generated pieces
        # the object will also find any generic parameters eg block name that will be the same for all pieces of the file that need rendering
        self.code = codeText(fileName, "//")
        projectName = prj.config.getConfig('PROJECTNAME')
        if "project" not in self.code.params:
            print (f"Project name is {projectName}")
            print(self.code.params)
        if (projectName in self.code.params.project or not self.code.params.project ):
            # setup the data for the renderer
            data = None
            if self.code.params.block:
                # get a block based view of the database. This is used for block definitions
                qualBlock = prj.getQualBlock( self.code.block )
                block = prj.data['blocks'][qualBlock]['block']
                data = prj.getBlockData(qualBlock, self.instances)
                if not data:
                    printError(f"In {fileName}, the block ({self.code.block}) specified in GENERATED_CODE_PARAM is either wrong or out of scope. Check the block is listed in your instances list")
                    exit(warningAndErrorReport())
            else:
                block = 'No block specified in GENERATED_CODE_PARAM'
            if self.code.params.inst:
                if not self.code.params.block:
                    printError(f"In {fileName}, the --inst requires the corresponding --block for the specified instance")
                    exit(warningAndErrorReport())
                try:
                    cblock, cinst = self.code.params.inst.split('.')
                except ValueError:
                    printError(f"In {fileName}, the format of --inst={self.code.params.inst}, specified in GENERATED_CODE_PARAM is invalid (--inst=<block>.<instance> expected)")
                    exit(warningAndErrorReport())
                # get a block based view of the database. This is used for block definitions
                qualCBlock = prj.getQualBlock( cblock )
                data = prj.getBlockData(qualCBlock, self.instances)
                if not data:
                    printError(f"In {fileName}, the container block ({cblock}) specified in GENERATED_CODE_PARAM is either wrong or out of scope. Check the block is listed in your instances list")
                    exit(warningAndErrorReport())
                # Instance in container block
                subinst = [v for v in data['subBlockInstances'].values() if v['instance'] == cinst]
                if not subinst:
                    printError(f"In {fileName}, the container instance ({cinst}) specified in GENERATED_CODE_PARAM is either wrong or undefined.")
                    exit(warningAndErrorReport())
                else:
                    subinst = subinst[0]
                if subinst['instanceTypeKey'] != qualBlock:
                    printError(f"In {fileName}, the container instance type ({subinst['instanceType']}) specified in GENERATED_CODE_PARAM does not match specified block")
                    exit(warningAndErrorReport())
                data['cinst'] = cinst
            if self.code.params.context:
                # get a context view of the database. This is used for shared header files
                context = self.code.params.context
                data = prj.getContextData(context, self.dataTypeMappings)
                self.calcStructure(data, prj)
            else:
                context = 'No context specified in GENERATED_CODE_PARAM'
            if self.code.params.scope:
                scope = self.code.params.scope
                data = prj.getSubHier(scope)
            if self.code.params.hierarchy:
                qualTop = prj.getQualInstance( prj.config.getConfig('TOPINSTANCE'))
                data = {"qualTop": qualTop}
            if not data:
                printError(f"In {fileName} there was no context, block or scope specified in GENERATED_CODE_PARAM")
                exit(warningAndErrorReport())

            parser = argparse.ArgumentParser(description="SystemC generated code parser", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
            parser.add_argument('--noDestructor', action='store_true', help='Dont add the destructor')
            parser.add_argument('--namespace', type=str, help='c++ option', default='')
            data['fileNameBase'] = os.path.basename(fileName)

            genOut = self.renderer.renderSections(self, self.code, parser, prj, data, args)

    def calcStructure(self, data, prj):
        # handle all the custom elements of the data specific to cpp
        # this is very much specific to a given implementation
        trackerFind = re.compile("tracker\(([^\)]*)\)")
        for myStruct in ['structures', 'specialStructures']:
            for struct, structData in data[myStruct].items():
                tracker = False
                trackerType = ""
                trackerVar = ""
                datapathVar = ""
                nextVar = ""
                register = False
                offset = 0
                for var, varData in structData['vars'].items():
                    # much of the customization of the output is controlled through the generator key
                    if varData['generator']:
                        if varData['generator'][:7]=='tracker':
                            # trackers are used for improved logging output in the code
                            tracker = True
                            trackerVar = var
                            braceContents = trackerFind.search(varData['generator'])
                            if braceContents:
                                trackerType = f"{braceContents.group(1).strip()}"
                                if trackerType != 'length':
                                    trackerType = f"tracker:{trackerType}"
                        if varData['generator'] == 'datapath':
                            # support for data transfer backdoor
                            datapathVar = var
                        if varData['generator'] == 'next':
                            # inplaceList customization
                            nextVar = var
                        if varData['generator'] == 'register':
                            # structure is used in a register, so we will want to add some stuff in the struct
                            register = True
                    # if arraySize is already an integer use it as is
                    try:
                        arraySize = int(varData['arraySize'])
                    except ValueError:
                        # otherwise lookup the constant based on the key version
                        arraySize = prj.getConst(varData['arraySizeKey'])
                    if arraySize == 1:
                        varData['isArray'] = False
                    else:
                        varData['isArray'] = True
                    if varData['entryType'] == 'Reserved':
                        bitwidth = varData['align']
                        typeInfo = {'enum': False}
                        for myType in self.dataTypeMappings:
                            if bitwidth <= myType['maxSize']:
                                varData['varType'] = myType['type']
                                break

                    elif varData['entryType'] == 'NamedStruct':
                        structInfo = prj.data['structures'][varData['subStructKey']]
                        bitwidth = structInfo['width']
                    else:
                        typeInfo = prj.data['types'][varData['varTypeKey']]
                        bitwidth = typeInfo['width']
                    bitwidth = prj.getConst( bitwidth )
                    varData['bitwidth'] = bitwidth
                    varData['arraywidth'] = bitwidth * arraySize
                    varData['bitshift'] = offset
                    offset = offset + varData['arraywidth']

                    # build a format string here to avoid doing it in jinja
                    if arraySize > 1:
                        varData['format'] = f"Array:{varData['variable']}:NotShown "
                        varloopCount = (bitwidth + 63) // 64  #16hex digits per 64bit value
                        varData['varLoopCount'] = varloopCount
                    else:
                        if varData["entryType"]=="NamedStruct":
                            varData['format'] = f"{varData['variable']}:[%s]"
                        else:
                            varData['enum']=False
                            if var == datapathVar:
                                varData['format'] = f"{varData['variable']}:%p"
                            else:
                                if typeInfo['enum']:
                                    varData['format'] = f"{varData['variable']}:%s"
                                    varData['enum']=True
                                else:
                                    if bitwidth == 1:
                                        varData['format'] = f"{varData['variable']}:%i"
                                    else:

                                        # convert to closest hex width
                                        hexwidth = ( bitwidth + 3 ) // 4      #4 bits per hex digit
                                        varloopCount = (bitwidth + 63) // 64  #16hex digits per 64bit value
                                        varData['varLoopCount'] = varloopCount

                                        varData['format'] = f"{varData['variable']}:"
                                        varData['hexwidth'] = hexwidth

                # remove space from the end of format string
                structData['trackerValid'] = tracker
                structData['trackerVar'] = trackerVar
                structData['trackerType'] = trackerType
                structData['register'] = register
                if datapathVar:
                    structData['vars'][datapathVar]['entryType'] = 'NamedType'
                    structData['vars'][datapathVar]['varType'] = 'uint8_t *'
                    structData['vars'][datapathVar]['desc'] = 'Datapath backdoor'
                structData['next'] = nextVar

    def _handler_generic(self, args, prj, data):
        vars = {'prj': prj, 'block': data, 'args': args}
        ret = self.renderer.render(args.template, vars)
        return ret
