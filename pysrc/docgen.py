from collections import OrderedDict
from sqlite3 import connect
from pysrc.arch2codeHelper import printIfDebug
import pysrc.processYaml as processYaml
from jinja2 import Template
from pysrc.renderer import renderer 


class makeDoc:
    prj = None
    renderer = None
    def __init__(self, prj, args) -> None:
        pass

        outFile = args.docout
        instanceTop = args.instance
        docDepth = args.depth
        self.prj = prj
        self.renderer = renderer(prj, 'docConfig', docType='asciidoctor')

        qualTop = prj.getQualTop(instanceTop)

        printIfDebug(f'Generating document {outFile} from {qualTop}')

        prj.setRangeOfInstances(qualTop, docDepth)
        for data, dataitem in prj.data['instances'].items():
            print(self.renderer.render('block', dataitem))

        prj.initConnections()
        for blockname, block  in prj.rangeOfInstances.items():
            self.docBlock(blockname, block)


    def docBlock(self, instname, block):
        print(self.renderer.render('blockHeader', block))
        self.docConnections(instname, block)


    def docConnections(self, instname, block):
        for connkey in self.prj.connections[instname]:
            data = dict()
            data['block'] = block # ?
            data['block']['connection'] = self.prj.data['connections'][connkey]
            data['block']['interface'] = self.prj.data['connections'][connkey]['interface']
            interfaceKey = data['block']['connection']['interfaceKey']
            data['block']['connection']['desc'] = self.prj.data['interfaces'][interfaceKey]['desc']
            data['args'] = None
            data['prj'] = None
            print(self.renderer.render('connectionHeader', data))
            structures = self.prj.data['interfaces'][interfaceKey]['structures']
            if structures is not None:
                self.docStructures(structures)


    def docStructures(self, structures):

        for struct in structures:
            self.docStruct(struct['structureKey'])

            
    def docStruct(self, structKey):
        additionalStructs = OrderedDict()
        data = OrderedDict()
        structData = self.prj.data['structures'][structKey]
        data['struct'] = structData
        data['desc'] = dict()
        for structName, struct in structData['vars'].items():
            if struct['entryType'] == "NamedStruct":
                additionalStructs[struct['substructureKey']] = None
                data['desc'][structName] = 'Embedded struct see below'
            elif struct['entryType'] == "NamedVar": 
                data['desc'][structName] = self.prj.data['variables'][struct['variableKey']]['desc']
            else:
                #namedType
                data['desc'][structName] = self.prj.data['types'][struct['varTypeKey']]['desc']
 
        print(self.renderer.render('structure', data))
        for more in additionalStructs:
            self.docStruct(more)
