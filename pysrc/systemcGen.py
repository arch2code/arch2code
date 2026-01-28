# systemC specific generation
from pysrc.processYaml import existsLoad
from pysrc.textfileHelper import codeText
import argparse
from pysrc.arch2codeHelper import printError, warningAndErrorReport, printWarning
from pysrc.renderer import renderer
import re
import os
class genSystemC:
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
        if not self.code.sections:
            # Gracefully skip files that do not have the appropriate GENERATED_CODE_ comments in them
            return
        projectName = prj.config.getConfig('PROJECTNAME')
        if "project" not in self.code.params:
            print (f"Project name is {projectName}")
            print(self.code.params)
        if (projectName in self.code.params.project or not self.code.params.project ):
            # setup the data for the renderer
            data = None
            if self.code.params.block:
                if self.code.params.excludeInst:
                    exclude = {self.code.params.excludeInst}
                else:
                    exclude = set()
                # get a block based view of the database. This is used for block definitions
                qualBlock = prj.getQualBlock( self.code.block)
                block = prj.data['blocks'][qualBlock]['block']
                data = prj.getBlockData(qualBlock, trimRegLeafInstance=True, excludeInstances=exclude)
                if not data:
                    printError(f"In {fileName}, the block ({self.code.block}) specified in GENERATED_CODE_PARAM is either wrong or out of scope. Check the block is listed in your instances list")
                    exit(warningAndErrorReport())
            else:
                block = 'No block specified in GENERATED_CODE_PARAM'
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
                    varData['arraySizeValue'] = arraySize
                    if arraySize == 0:
                        varData['isArray'] = False
                    else:
                        varData['isArray'] = True
                    if varData['entryType'] == 'Reserved':
                        bitwidth = varData['align']
                        typeInfo = {'enum': False}
                        varData['isSigned'] = False  # Reserved fields are always unsigned
                        for myType in self.dataTypeMappings:
                            if bitwidth <= myType['maxSize']:
                                # Reserved fields are always unsigned
                                varData['varType'] = myType['unsignedType']
                                break

                    elif varData['entryType'] == 'NamedStruct':
                        structInfo = prj.data['structures'][varData['subStructKey']]
                        bitwidth = structInfo['width']
                        varData['isSigned'] = False  # Structures are not signed
                    else:
                        typeInfo = prj.data['types'][varData['varTypeKey']]
                        bitwidth = typeInfo['width']
                        # Capture isSigned status from type (defaults to False)
                        varData['isSigned'] = typeInfo.get('isSigned', False)
                    bitwidth = prj.getConst( bitwidth )
                    varData['bitwidth'] = bitwidth
                    varData['arraywidth'] = bitwidth * arraySize if varData['isArray'] else bitwidth
                    varData['bitshift'] = offset
                    offset = offset + varData['arraywidth']

                    # build a format string here to avoid doing it in jinja
                    if arraySize :
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
