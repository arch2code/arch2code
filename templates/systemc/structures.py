from pysrc.intf_gen_utils import get_const
import os.path
dataTypeMappings = [
    {'maxSize': 1, 'type': 'uint8_t'},
    {'maxSize': 8, 'type': 'uint8_t'},
    {'maxSize': 16, 'type': 'uint16_t'},
    {'maxSize': 32, 'type': 'uint32_t'},
    {'maxSize': 64, 'type': 'uint64_t'},
    {'maxSize': 4096, 'type': 'uint64_t', 'arrayElementSize': 64}
]

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    if len(data['structures']) == 0:
        return ""
    global codeMapping
    # using list to simplify all the last loop special cases to allow simple delete of last entry
    # to effectively backup
    out = list()
    if (args.section == '' or args.section == 'cpp' or args.section == 'header'):
        if args.mode == '':
            args.mode = 'model'
        if args.mode not in codeMapping:
            print(f"Warning: mode {args.mode} not found in codeMapping, defaulting to model")
        if args.section == '':
            args.section = 'header'
        out.append("// structures\n")
        for struct, value in data['structures'].items():
            out.extend(oneStruct(args, prj, data, struct, value))
    # handle system includes
    if (args.section == 'headerIncludes' or args.section == 'cppIncludes'):
        out.extend(systemIncludes(args))
    if (args.section == 'testStructsHeader' or args.section == 'testStructsCPP'):
        out.extend(structTest(args, prj, data))
    return("".join(out))

includeMapping = {
    'prtFmt': ['"logging.h"'],
    'fw_pack': ['<algorithm>', '"bitTwiddling.h"'],
    'fw_unpack': ['<algorithm>'],
}
def systemIncludes(args):
    global codeMapping, includeMapping
    mode = args.mode
    if mode == '':
        mode = 'model'

    out = list()
    includeDict = dict()
    for key, value in codeMapping[mode].items():
        if key in includeMapping:
            if (value == 'split' and args.section == 'cppIncludes') or (value == 'inline' and args.section == 'headerIncludes'):
                # extend dict by iterating over includeMapping list
                includeDict.update({include: True for include in includeMapping[key]})

    for lib in includeDict:
        out.append(f"#include {lib}\n")
    return out


def convertToType(bitwidth, name="_packedSt"):
    global dataTypeMappings
    for myType in dataTypeMappings:
        if bitwidth <= myType['maxSize']:
            arrayElementSize = myType.get('arrayElementSize', 0)
            if arrayElementSize > 0:
                # round up to the nearest multiple using integer div, plus one if there is a modulo non zero
                typeArraySize = bitwidth // arrayElementSize + (bitwidth % arrayElementSize > 0)
                retType = f"{myType['type']} {name}[{typeArraySize}]"
                rowType = myType['type']
                baseSize = arrayElementSize
            else:
                retType = f"{myType['type']} {name}"
                rowType = myType['type']
                baseSize = myType['maxSize']
            #if we found something terminate the list as we want the smallest type
            break
    return retType, rowType, baseSize

def printOneVar(prefix, space, varName, vardata, prtoss=True):
    out = list()
    bitwidth = vardata['bitwidth']
    postfix = ''
    decorators = ''
    hexwidth = ( bitwidth + 3 ) // 4      #4 bits per hex digit
    if vardata['entryType'] == 'NamedVar' or vardata['entryType'] == 'NamedType' or vardata['entryType'] == 'Reserved':
        if vardata.get('enum', False):
            if prtoss:
                start = f'{prefix}<< "{space}{varName}:"'
                decorators = '  << '
            else:
                start = f'{space}{varName}:{{}}'
            varPrint = f'{ vardata["varType"] }_prt( {varName} )'
        else:
            if bitwidth <= 64 or vardata['generator'] == 'datapath':
                if prtoss:
                    start = f'{prefix}<< "{space}{varName}:0x"'
                    decorators = f' << std::hex << std::setw({hexwidth}) << std::setfill(\'0\') << '
                else:
                    start = f'{space}{varName}:0x'
                    decorators = f'{{:0{hexwidth}x}}'
                varPrint = f'(uint64_t) {varName}'
            else:
                if prtoss:
                    start = f'{prefix}<< "{space}{varName}:0x" '
                else:
                    start = f'{space}{varName}:0x'
                decorators = list()
                varPrint = list()
                indent = ''
                for i in range(vardata['varLoopCount']-1, -1, -1) :
                    printWidth = ( ((hexwidth + 15) % 16) + 1)
                    if prtoss:
                        decorators.append(f"{indent}<< std::hex << std::setw({ printWidth}) << std::setfill(\'0\') <<  ")
                    else:
                        decorators.append(f'{{:0{printWidth}x}}')
                    varPrint.append(f"{varName}.word[{ i }]")
                    hexwidth = hexwidth - printWidth
                    indent = ' '*len(prefix)
    elif vardata['entryType'] == 'NamedStruct':
        if prtoss:
            start = f'{prefix}<< "{space}{varName}:<"'
            decorators = ' + '

        else:
            start = f'{space}{varName}:'
            decorators = '<{}>'
        varPrint = f'{varName}.prt(all)'

    return (start, decorators, varPrint, postfix)

def printOneArray(prefix, space, varName, varData, prj, isModel, prtoss=True):
    out = list()
    postfix = ''
    decorators = ''
    if isinstance(varData['arraySize'], int):
        arraySize = varData['arraySize']
    else:
        arraySize = get_const(varData['arraySizeKey'], prj.data['constants'])
    varType = varData["varType"]
    varLoopCount = varData["varLoopCount"]
    if prtoss:
        start = f'{prefix}<< "{space}{varName}[0:{arraySize-1}]: "'
    else:
        start = f'{space}{varName}[0:{arraySize-1}]: '
    if not isModel:
        varPrint = "Not printed"
    else:
        decorators = ' << ' if prtoss else '{}'
        if varLoopCount > 1:
            varPrint = f'static2DArrayPrt<{varType}, uint64_t, {varData["arraySize"]}, {varLoopCount}>({varName}, all)'
        else:
            varPrint = f'staticArrayPrt<{varType}, {varData["arraySize"]}>({varName}, all)'

    return (start, decorators, varPrint, postfix)

def printOneSubstructArray(prefix, space, varName, varData, prtoss=True):
    out = list()
    varType = varData["subStruct"]
    postfix = ''
    decorators = ''
    start = ''
    if prtoss:
        if space:
            start = f'{prefix}<< "{space}" << '
        else:
            start = f'{prefix}<< '
    else:
        decorators = '{}'
    varPrint = f'structArrayPrt<{varType}, {varData["arraySize"]}>({varName}, "{varName}", all)'

    return (start, decorators, varPrint, postfix)
# inline = inline in header
# disable = disable in header
# split = split between header and cpp - declare in header, define in cpp
# some items may only be in the header, and so will be inline if present in the table
codeMapping = {
    'model': {
        'equal': 'split',
        'sc_trace': 'inline',
        'operatorStream': 'inline',
        'prtFmt': 'split',
        'tracker': 'inline',
        'getSet': 'inline',
        'fw_pack': 'split',
        #'fw_pack_ret': 'inline',
        'fw_unpack': 'split',
        'registerFeatures': 'inline',
        'sc_pack': 'split',
        'sc_unpack': 'split',
        'constuctor_bv': 'inline',
        'constructor': 'inline',
        'constructor_packed': 'inline',
    },
    'fw': {
        'fw_pack': 'inline',
        'fw_unpack': 'inline',
        'constructor': 'inline',
    }
}

def oneStruct(args, prj, data, struct, value):
    global codeMapping
    isCpp = (args.section == 'cpp')

    out = list()
    structName = value['structure']
    indent = '' if isCpp else ' '*4
    if not isCpp:
        # first few things are not optinal and always in the header
        out.append(f"struct {structName} {{\n")
        # declare vars
        out.extend(declareVars(value, indent))
        if args.mode == 'fw':
            out.append(f"\n{indent}{structName}() {{ memset(this, 0, sizeof({ value['structure'] })); }}\n\n")
        else:
            out.append(f"\n{indent}{structName}() {{}}\n\n")
        # consts
        out.append(f"{indent}static constexpr uint16_t _bitWidth = {value['width']};\n")
        out.append(f"{indent}static constexpr uint16_t _byteWidth = {(value['width']+7) >> 3};\n")
        retType, rowType, baseSize = convertToType(value['width'])
        out.append(f"{indent}typedef {retType};\n")

    # handle all optional components based on config table
    for feature, handle in codeMapping[args.mode].items():
        if handle == 'disable':
            continue
        match feature:
            case 'equal': # equal test
                out.extend(equalTest(handle, args, structName, value, indent))
            case 'sc_trace':
                out.extend(scTrace(handle, args, structName, value, indent))
            case 'operatorStream': # operator <<
                out.extend(operatorStream(structName, indent)) if not isCpp else None
            case 'prt':
                out.extend(prt(handle, args, value, indent, prj))
            case 'prtFmt':
                out.extend(prtFmt(handle, args, value, indent, prj))
            case 'tracker': # getTrackerType
                out.extend(tracker(value, indent)) if not isCpp else None
            case 'getSet': # getters and setters
                out.extend(getSet(value, indent)) if not isCpp else None
            case 'fw_pack':
                out.extend(processPackUnpack("fw_pack", handle, args, value, indent))
            case 'fw_pack_ret':
                out.extend(processPackRet(structName, value, indent))
            case 'fw_unpack':
                out.extend(fw_unpack(handle, args, value, indent))
            case 'registerFeatures': # register features
                if not isCpp and value['register']:
                    out.extend(registerFeatures(value, indent))
            case 'sc_pack':
                out.extend(sc_pack(handle, args, value, indent))
            case 'sc_unpack':
                if value['width'] == 1:
                    out.extend(sc_unpack(handle, args, "bool", value, indent))
                out.extend(sc_unpack(handle, args, f"sc_bv<{value['width']}>", value, indent))
            case 'constuctor_bv':
                out.extend(constuctor_bv(structName, value, indent)) if not isCpp else None
            case 'constructor':
                out.extend(constructor(structName, value, indent)) if not isCpp else None
            case 'constructor_packed':
                out.extend(constructor_packed(structName, value, indent)) if not isCpp else None
            case _:
                print("bad codeMapping entry")
                exit()

    if not isCpp:
        out.append(f'\n}};\n')
    return out

def declareVars(vars, indent):
    out = list()
    for var, vardata in reversed(vars["vars"].items()):
        if vardata['isArray']:
            myArray= f"[{vardata['arraySize']}]"
            #myArrayLoopIndex= '[i]'
        else:
            myArray= ''
            #myArrayLoopIndex= ''
        if vardata['entryType'] == 'NamedVar' or vardata['entryType'] == 'NamedType' or vardata['entryType'] == 'Reserved':
            out.append(f"{indent}{vardata['varType']} {vardata['variable'] + myArray}; //{ vardata['desc'] }\n")
        elif vardata['entryType'] == 'NamedStruct':
            out.append(f"{indent}{vardata['subStruct']} {vardata['variable'] +myArray}; //{ vardata['desc'] }\n")
    return out

def equalTest(handle, args, structName, vars, indent):
    out = list()
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}inline bool operator == (const { structName } & rhs) const {{\n")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}bool operator == (const { structName } & rhs) const;\n")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}bool {decl}{structName}::operator == (const { structName } & rhs) const {{\n")
    else:
        return out
    out.append(f"{indent}    bool ret = true; \n")
    indent += ' '*4
    for var, vardata in vars["vars"].items():
        varName = vardata['variable']
        if vardata['isArray']:
            #myArray= f"[{vardata['arraySize']}]"
            myArrayLoopIndex= '[i]'
        else:
            #myArray= ''
            myArrayLoopIndex= ''
        if vardata['isArray']:
            out.append(f"{indent}for(int i=0; i<{vardata['arraySize']}; i++) {{\n")
            indent += ' '*4

        if vardata['bitwidth'] <= 64 or vardata['generator'] == 'datapath' or vardata['entryType'] == 'NamedStruct':
            out.append(f"{indent}ret = ret && ({varName+myArrayLoopIndex} == rhs.{varName+myArrayLoopIndex});\n")
        else:
            for i in range(0, vardata['varLoopCount']):
                out.append(f"{indent}ret = ret && ({varName+myArrayLoopIndex}.word[ {i} ] == rhs.{varName+myArrayLoopIndex}.word[ {i} ]);\n")
        if vardata['isArray']:
            indent = indent[:-4]
            out.append(f"{indent}}}\n")
    out.append(f"{indent}return ( ret );\n")
    out.append(f"{indent}}}\n")
    return out

def scTrace(handle, args, structName, vars, indent):
    out = list()
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}inline friend void sc_trace(sc_trace_file *tf, const {structName} & v, const std::string & NAME ) {{\n")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}void sc_trace(sc_trace_file *tf, const {structName} & v, const std::string & NAME );\n")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}void {decl}{structName}::sc_trace(sc_trace_file *tf, const {structName} & v, const std::string & NAME ) {{\n")
    else:
        return out
    indent += ' '*4
    for var, vardata in vars["vars"].items():
        varName = vardata['variable']
        if vardata['isArray']:
            #myArray= f"[{vardata['arraySize']}]"
            myArrayLoopIndex= '[i]'
        else:
            #myArray= ''
            myArrayLoopIndex= ''
        if vardata['isArray']:
            out.append(f"{indent}for(int i=0; i<{vardata['arraySize']}; i++) {{\n")
            indent += ' '*4

        if vardata['bitwidth'] <= 64 or vardata['generator'] == 'datapath' or vardata['entryType'] == 'NamedStruct':
            out.append(f'{indent}sc_trace(tf,v.{varName+myArrayLoopIndex}, NAME + ".{varName+myArrayLoopIndex}");\n')
        else:
            for i in range(0, vardata['varLoopCount']):
                out.append(f'{indent}sc_trace(tf,v.{varName+myArrayLoopIndex}.word[ {i} ], NAME + ".{varName+myArrayLoopIndex}.word[ {i} ]");\n')
        if vardata['isArray']:
            indent = indent[:-4]
            out.append(f"{indent}}}\n")
    out.append(f"    }}\n")
    return out

def operatorStream(structName, indent):
    out = list()
    out.append(f"{indent}inline friend ostream& operator << ( ostream& os,  {structName} const & v ) {{\n")
    out.append(f'{indent}    os << v.prt();\n')
    out.append(f"{indent}    return os;\n")
    out.append(f"{indent}}}\n")
    return out

def convertToList(start, decorators, varPrint, postfix):
    out = list()
    if isinstance(varPrint, list):
        for dec, var in zip(decorators, varPrint):
            out.append(start + dec + var + '\n')
            start = ''
        out[-1] = out[-1] + postfix
    else:
        out.append(start + decorators + varPrint + postfix + '\n')
    return out

def prt(handle, args, vars, indent, prj):
    out = list()
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}std::string prt(bool all=false) const\n")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}std::string prt(bool all=false) const;\n")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}std::string {decl}{vars['structure']}::prt(bool all) const\n")
    else:
        return out
    out.append(f"{indent}{{\n")
    indent += ' '*4
    space = ''
    out.append(f'{indent}std::ostringstream oss;\n')
    newOss = True
    for var, vardata in vars['vars'].items():
        if newOss:
            prefix = f'{indent}oss '
            newOss = False
        else:
            prefix = f'{indent}    '
        varName = vardata['variable']
        if vardata['isArray'] and not vardata['subStruct']:
            isModel = (args.mode == 'model')
            out.extend(convertToList(*printOneArray(prefix, space, varName, vardata, prj, isModel)))
        elif vardata['isArray'] and vardata['subStruct']:
            out.extend(convertToList(*printOneSubstructArray(prefix, space, varName, vardata)))
        else:
            out.extend(convertToList(*printOneVar(prefix, space, varName, vardata, prj)))
        space = ' '
    # add semicolon to the last item in the list
    out[-1] = out[-1].replace('\n', ';\n')
    out.append(f"{indent}\n")
    out.append(f"{indent}return oss.str();\n")
    indent = indent[:-4]
    out.append(f"{indent}}}\n")
    return out

def prtFmt(handle, args, vars, indent, prj):
    out = list()
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}std::string prt(bool all=false) const\n")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}std::string prt(bool all=false) const;\n")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}std::string {decl}{vars['structure']}::prt(bool all) const\n")
    else:
        return out
    out.append(f"{indent}{{\n")
    indent += ' '*4
    space = ''
    prefix = '   '
    varList = list()
    for var, vardata in vars['vars'].items():
        varName = vardata['variable']
        if vardata['isArray'] and not vardata['subStruct']:
            isModel = (args.mode == 'model')
            varList.append(printOneArray(prefix, space, varName, vardata, prj, isModel, False))
        elif vardata['isArray'] and vardata['subStruct']:
            varList.append(printOneSubstructArray(prefix, space, varName, vardata, False))
        else:
            varList.append(printOneVar(prefix, space, varName, vardata, False))
        space = ' '
    varOut = list()
    fmt = ''
    for item in varList:
        if isinstance(item[2], list):
            fmt += item[0]
            for dec, var in zip(item[1], item[2]):
                fmt += dec
                varOut.append(f'{indent}   {var},\n')
        else:
            fmt += item[0] + item[1]
            varOut.append(f'{indent}   {item[2]},\n')
    # add semicolon to the last item in the list
    varOut[-1] = varOut[-1].replace(',\n', '\n')
    out.append(f'{indent}return (fmt::format("{fmt}",\n')
    out.extend(varOut)
    out.append(f"{indent}));\n")
    indent = indent[:-4]
    out.append(f"{indent}}}\n")
    return out

def tracker(vars, indent):
    out = list()
    out.append(f'{indent}static const char* getValueType(void) {{ return( "{vars["trackerType"] }" );}}\n')
    # getTrackerValue
    if vars['trackerValid']:
        ret = f"{ vars['trackerVar'] }"
    else:
        ret = f"-1"
    out.append(f"{indent}inline uint64_t getStructValue(void) const {{ return( {ret} );}}\n")
    return out

def getSet(vars, indent):
    out = list()
    for var, vardata in vars['vars'].items():
        generator = vardata['generator']
        # next features
        if generator == 'next':
            out.append(f"{indent}inline {vardata['varType']} _getNext(void) {{ return( { var }); }}\n")
            out.append(f"{indent}inline void _setNext({vardata['varType']} value) {{ { var } = value; }}\n")
        # listValid features
        if generator == 'listValid':
            out.append(f"{indent}inline {vardata['varType']} _getValid(void) {{ return( { var }); }}\n")
            out.append(f"{indent}inline void _setValid({vardata['varType']} value) {{ { var } = value; }}\n")
        # listHead features
        if generator == 'listHead':
            out.append(f"{indent}inline {vardata['varType']} _getHead(void) {{ return( { var }); }}\n")
            out.append(f"{indent}inline void _setHead({vardata['varType']} value) {{ { var } = value; }}\n")
        # listTail features
        if generator == 'listTail':
            out.append(f"{indent}inline {vardata['varType']} _getTail(void) {{ return( { var }); }}\n")
            out.append(f"{indent}inline void _setTail({vardata['varType']} value) {{ { var } = value; }}\n")
        # address field
        if generator == 'address':
            out.append(f"{indent}inline {vardata['varType']} _getAddress(void) {{ return( { var }); }}\n")
        # address field
        if generator == 'data':
            out.append(f"{indent}inline {vardata['varType']} _getData(void) {{ return( { var }); }}\n")
            out.append(f"{indent}inline void _setData({vardata['varType']} value) {{ { var } = value; }}\n")
    return out
def registerFeatures(vars, indent):
    out = list()
    out.append(f"{indent}// register functions\n")
    out.append(f"{indent}inline int _size(void) {{return( ({ vars['width'] } + 7) >> 4 ); }}\n")
    out.append(f"{indent}uint64_t _getValue(void)\n")
    out.append(f"{indent}{{\n")
    indent = ' '*8
    out.append(f"{indent}uint64_t ret =\n")
    for var, vardata in vars['vars'].items():
        varName = vardata['variable']
    if vardata['isArray']:
        myArray= f"[{vardata['arraySize']}]"
        myArrayLoopIndex= '[i]'
    else:
        myArray= ''
        myArrayLoopIndex= ''

        if vardata['entryType'] == 'NamedStruct':
            out.append(f"{indent}( {varName}._getValue() ) << { vardata['bitshift'] }")
        else:
            if vardata['bitwidth'] < 64:
                out.append(f"{indent}( {varName} & ((1ULL<<{ vardata['bitwidth'] } )-1) << { vardata['bitshift'] })")
            else:
                out.append(f"{indent}( {varName} << { vardata['bitshift'] } )")
        out.append(f" +\n")
    out.pop()
    out.append(f";\n")
    out.append(f"{indent}return( ret );\n")
    indent = ' '*4
    out.append(f"{indent}}}\n")
    out.append(f"{indent}void _setValue(uint64_t value)\n")
    out.append(f"{indent}{{\n")
    indent = ' '*8
    for var, vardata in vars['vars'].items():
        varName = vardata['variable']
        if vardata['isArray']:
            myArray= f"[{vardata['arraySize']}]"
            myArrayLoopIndex= '[i]'
        else:
            myArray= ''
            myArrayLoopIndex= ''
        if vardata['entryType'] == 'NamedStruct':
            if vardata['bitwidth'] >= 64:
                out.append(f"{indent}{ varName }._setValue( (( value >> { vardata['bitshift'] } ) )) ;\n")
            else:
                out.append(f"{indent}{ varName }._setValue( (( value >> { vardata['bitshift'] } ) & (( (uint64_t)1 << { vardata['bitwidth'] } ) - 1)) ) ;\n")
        else:
            if vardata['bitwidth'] >= 64:
                out.append(f"{indent}{ varName } = ( { vardata['varType'] } ) (( value >> { vardata['bitshift'] } ) ) ;\n")
            else:
                out.append(f"{indent}{ varName } = ( { vardata['varType'] } ) (( value >> { vardata['bitshift'] } ) & (( (uint64_t)1 << { vardata['bitwidth'] } ) - 1)) ;\n")
    out.append(f"{indent}}}\n")
    return out

# sc_pack
def sc_pack(handle, args, vars, indent):
    out = list()
    if vars['width'] > 1:
        structType = f"sc_bv<{vars['width']}>"
    else:
        structType = 'bool'
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}inline {structType} sc_pack(void) const\n")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}{structType} sc_pack(void) const;\n")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}{structType} {decl}{vars['structure']}::sc_pack(void) const\n")
    else:
        return out
    out.append(f'{indent}{{\n')
    indent += ' '*4
    out.append(f"{indent}{structType} packed_data;\n")
    high,low = 0,0
    for _, data in reversed(vars['vars'].items()):
        varName = data['variable']
        varIndex = ''
        high = low + data['arraywidth'] - 1
        if data['generator'] == 'datapath':
            num_bytes = int(data['bitwidth'] / 8)
            out.append(f'{indent}for(int unsigned bsl=0; bsl<{num_bytes}; bsl++) {{\n')
            rng_high, rng_low  = f"{low}+bsl*8+7", f"{low}+bsl*8"
            indent += ' '*4
            out.append(f'{indent}packed_data.range({rng_high}, {rng_low}) = {varName}[bsl];\n')
            indent = indent[:-4]
            out.append(f"{indent}}}\n")
        else:
            if data['isArray']:
                varIndex = f"[i]"
                out.append(f"{indent}for(int i=0; i<{data['arraySize']}; i++) {{\n")
                rng_high, rng_low  = f"{low}+(i+1)*{data['bitwidth']}-1", f"{low}+i*{data['bitwidth']}"
                indent += ' '*4
            else:
                rng_high, rng_low  = f"{high}", f"{low}"
            if data['entryType'] == 'NamedVar' or data['entryType'] == 'NamedType' or data['entryType'] == 'Reserved':
                if structType != 'bool':
                    if data['bitwidth'] >= 64 and data['entryType'] != 'NamedStruct' and data['varLoopCount'] > 1:
                        if not data['isArray']:
                            loop_stride = 64
                        else:
                            loop_stride = data['bitwidth'] // data['varLoopCount']
                        loop_low = low
                        for wix in range(data['varLoopCount']):
                            if not data['isArray']:
                                loop_high = loop_low + loop_stride - 1
                                loop_high = min(loop_high, high)
                                rng_high, rng_low  = f"{loop_high}", f"{loop_low}"
                                loop_low = loop_high + 1
                            else:
                                rng_high, rng_low  = f"{low}+i*{data['bitwidth']}+{loop_stride}*{wix+1}-1", f"{low}+i*{data['bitwidth']}+{loop_stride}*{wix}"
                            out.append(f'{indent}packed_data.range({rng_high}, {rng_low}) = {varName}{varIndex}.word[{wix}];\n')
                    else:
                        out.append(f'{indent}packed_data.range({rng_high}, {rng_low}) = {varName}{varIndex};\n')
                else:
                    out.append(f'{indent}packed_data = ({structType}) {varName}{varIndex};\n')
            elif data['entryType'] == 'NamedStruct':
                out.append(f'{indent}packed_data.range({rng_high}, {rng_low}) = {varName}{varIndex}.sc_pack();\n')
            else:
                assert(0)
            if data['isArray']:
                indent = indent[:-4]
                out.append(f"{indent}}}\n")

        low = high + 1
    out.append(f"{indent}return packed_data;\n")
    indent = indent[:-4]
    out.append(f'{indent}}}\n')
    return out

# sc_unpack
def sc_unpack(handle, args, structType, vars, indent):
    out = list()
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}inline void sc_unpack({structType} packed_data)\n")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}void sc_unpack({structType} packed_data);\n")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}void {decl}{vars['structure']}::sc_unpack({structType} packed_data)\n")
    else:
        return out
    out.append(f'{indent}{{\n')
    high,low = 0,0
    indent += ' '*4
    for _, data in reversed(vars['vars'].items()):
        varName = data['variable']
        varType = data['varType'] if data['entryType'] != 'NamedStruct' else data['subStruct']
        varIndex = ''
        high = low + data['arraywidth'] - 1
        if data['generator'] == 'datapath':
            num_bytes = int(data['bitwidth'] / 8)
            out.append(f'{indent}for(int unsigned bsl=0; bsl<{num_bytes}; bsl++) {{\n')
            rng_high, rng_low  = f"{low}+bsl*8+7", f"{low}+bsl*8"
            indent += ' '*4
            out.append(f'{indent}{varName}[bsl] = (uint8_t) packed_data.range({rng_high}, {rng_low}).to_uint64();\n')
            indent = indent[:-4]
            out.append(f"{indent}}}\n")
        else:
            if data['isArray']:
                varIndex = f"[i]"
                out.append(f"{indent}for(int i=0; i<{data['arraySize']}; i++) {{\n")
                rng_high, rng_low  = f"{low}+(i+1)*{data['bitwidth']}-1", f"{low}+i*{data['bitwidth']}"
                indent += ' '*4
            else:
                rng_high, rng_low  = f"{high}", f"{low}"
            if data['entryType'] == 'NamedVar' or data['entryType'] == 'NamedType' or data['entryType'] == 'Reserved':
                if structType != 'bool':
                    if data['bitwidth'] >= 64 and data['entryType'] != 'NamedStruct' and data['varLoopCount'] > 1:
                        if not data['isArray']:
                            loop_stride = 64
                        else:
                            loop_stride = data['bitwidth'] // data['varLoopCount']
                        loop_low = low
                        varType = 'uint64_t'
                        for wix in range(data['varLoopCount']):
                            if not data['isArray']:
                                loop_high = loop_low + loop_stride - 1
                                loop_high = min(loop_high, high)
                                rng_high, rng_low  = f"{loop_high}", f"{loop_low}"
                                loop_low = loop_high + 1
                            else:
                                rng_high, rng_low  = f"{low}+i*{data['bitwidth']}+{loop_stride}*{wix+1}-1", f"{low}+i*{data['bitwidth']}+{loop_stride}*{wix}"
                            out.append(f'{indent}{varName}{varIndex}.word[{wix}] = ({varType}) packed_data.range({rng_high}, {rng_low}).to_uint64();\n')
                    else:
                        out.append(f'{indent}{varName}{varIndex} = ({varType}) packed_data.range({rng_high}, {rng_low}).to_uint64();\n')
                else :
                    out.append(f'{indent}{varName}{varIndex} = ({varType}) packed_data;\n')
            elif data['entryType'] == 'NamedStruct':
                out.append(f'{indent}{varName}{varIndex}.sc_unpack(packed_data.range({rng_high}, {rng_low}));\n')
            else :
                assert(False)
            if data['isArray']:
                indent = indent[:-4]
                out.append(f"{indent}}}\n")

        low = high + 1
    indent = indent[:-4]
    out.append(f'{indent}}}\n')
    return out

    # constructor
def constuctor_bv(structName, vars, indent):
    out = list()
    if vars['width'] > 1:
        structType = f"sc_bv<{vars['width']}>"
    else:
        structType = 'bool'
    out.append(f"{indent}explicit {structName}({structType} packed_data) {{ sc_unpack(packed_data); }}\n")
    return out

def constructor(structName, vars, indent):
    out = list()
    indent = ' '*4
    out.append(f"{indent}explicit {structName}(\n")
    indent = ' '*8
    params = list()
    initializers = list()
    memcpys = list()
    for var, vardata in reversed(vars["vars"].items()):
        if vardata['isArray']:
            myArray= f"[{vardata['arraySize']}]"
            myArrayLoopIndex= '[i]'
        else:
            myArray= ''
            myArrayLoopIndex= ''
        if vardata['entryType'] == 'NamedVar' or vardata['entryType'] == 'NamedType' or vardata['entryType'] == 'Reserved':
            params.append(f"{indent}{vardata['varType']} {vardata['variable'] + '_' + myArray},\n")
        elif vardata['entryType'] == 'NamedStruct':
            params.append(f"{indent}{vardata['subStruct']} {vardata['variable'] + '_' + myArray},\n")
        if myArray == '':
            initializers.append(f"{indent}{vardata['variable']}({vardata['variable'] + '_'}),\n")
        else:
            memcpys.append(f"{indent}memcpy(&{vardata['variable']}, &{vardata['variable'] + '_'}, sizeof({vardata['variable']}));\n")

    if len(initializers) > 0:
        params[-1] = params[-1].replace(',\n', ') :\n')
    else:
        params[-1] = params[-1].replace(',\n', ')\n')
    out.extend(params)
    if len(initializers) > 0:
        initializers[-1] = initializers[-1].replace(',\n', '\n')
        out.extend(initializers)
    indent = ' '*4
    if len(memcpys) > 0:
        out.append(f"{indent}{{\n")
        out.extend(memcpys)
        out.append(f"{indent}}}\n")
    else:
        out.append(f"{indent}{{}}\n")

    return out

def constructor_packed(structName, vars, indent):
    out = list()
    out.append(f"{indent}explicit {structName}(const _packedSt &packed_data) {{ unpack(const_cast<_packedSt&>(packed_data)); }}\n")
    return out

def get_unpack_mask_str(needBits, baseSize):
    mask = ''
    # truncate the mask to the needed bits case
    if (needBits < baseSize):
        mask = f" & ((1ULL << {needBits}) - 1)"
    if (baseSize == 1 or needBits == 1):
        mask = ' & 1'
    return mask

def processPackRet(structName, value, indent):
    out = list()
    out.append(f"{indent}inline _packedSt pack(void) const\n")
    out.append(f"{indent}{{\n")
    out.append(f"{indent}    _packedSt ret;\n")
    out.append(f"{indent}    pack(ret);\n")
    out.append(f"{indent}    return ret;\n")
    out.append(f"{indent}}}\n")
    return out


def fw_unpack(handle, args, vars, indent):
    out = list()
    global dataTypeMappings
    # figure out return type
    bitwidth = vars['width']
    paramType, rowType, baseSize = convertToType(bitwidth)
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}inline void unpack(_packedSt &_src)\n")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}void unpack(_packedSt &_src);\n")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}void {decl}{vars['structure']}::unpack(_packedSt &_src)\n")
    else:
        return out
    out.append(f'{indent}{{\n')
    indent += ' '*4
    count = len(vars['vars'])
    src = "_src"
    isPtr = False
    baseMask = baseSize - 1
    log2BaseSize = baseMask.bit_length()
    usePos = False
    isSingleArray = (count == 1 and vars['vars'][next(iter(vars['vars']))]['arraySizeValue'] == 1) # detect array with only single element
    offsetShift = ""
    if bitwidth > baseSize:
        src = f"_src[ _pos >> {log2BaseSize} ]"
        isPtr = True
    if isPtr or count > 1 or (count == 1 and vars['vars'][next(iter(vars['vars']))]['isArray'] and not isSingleArray):
        out.append(f"{indent}uint16_t _pos{{0}};\n")
        usePos = True
        offsetShift = f" >> (_pos & {baseMask})"
    currentPos = 0
    nextPos = 0
    for _, data in reversed(vars['vars'].items()):
        count -= 1
        is_last = (0 == count)
        varName = data['variable']
        varIndex = ''
        nextPos = currentPos + data['arraywidth']
        bitsLeft = data['arraywidth']
        varType = data['varType'] if data['entryType'] != 'NamedStruct' else data['subStruct']
        calcAlign = False  # does code need to calc alignment
        # for array case, create an outer loop
        if data['isArray']:
            varIndex = f"[i]"
            out.append(f"{indent}for(int i=0; i<{data['arraySize']}; i++) {{\n")
            indent += ' '*4
            calcAlign = (not isSingleArray) or usePos
            bitsLeft = data['bitwidth']
            out.append(f"{indent}uint16_t _bits = {bitsLeft};\n")
            out.append(f"{indent}uint16_t _consume;\n")
        if data['entryType'] == 'NamedVar' or data['entryType'] == 'NamedType' or data['entryType'] == 'Reserved':
            if data['bitwidth'] >= 64 and data['entryType'] != 'NamedStruct' and data['varLoopCount'] > 1:
                if not data['isArray']:
                    loop_stride = 64
                else:
                    loop_stride = data['bitwidth'] // data['varLoopCount']
                loop_current = currentPos
                totalConsume = data['bitwidth']
                for wix in range(data['varLoopCount']):
                    actual_bits = min(loop_stride, totalConsume)
                    totalConsume -= actual_bits
                    loop_bits_left = actual_bits
                    srcMask = ''
                    # we could be consuming the rest of the word or just the loop bits left
                    if (calcAlign):
                        out.append(f"{indent}_consume = std::min(_bits, (uint16_t)({baseSize}-(_pos & {baseMask})));\n")
                    consumeBits = min(loop_bits_left, baseSize - (loop_current % baseSize))
                    srcMask = get_unpack_mask_str(loop_bits_left, baseSize)
                    loop_next = loop_current + actual_bits
                    out.append(f'{indent}{varName}{varIndex}.word[{wix}] = (({src}{offsetShift}){srcMask});\n')
                    if (calcAlign):
                        out.append(f'{indent}_pos += _consume;\n') if usePos else None
                    else:
                        out.append(f'{indent}_pos += {consumeBits};\n') if usePos else None
                    loop_bits_left -= consumeBits
                    # if the source is a pointer and we consumed the whole word, increment the pointer
                    if (calcAlign):
                        out.append(f"{indent}_bits -= _consume;\n")
                        out.append(f"{indent}if ((_bits > 0) && (_consume != {baseSize})) {{\n")
                        out.append(f'{indent}    {varName}{varIndex}.word[{wix}] = {varName}{varIndex}.word[{wix}] | (({src} << _consume){srcMask});\n')
                        out.append(f'{indent}    _pos += {actual_bits} - _consume;\n') if usePos else None
                        out.append(f"{indent}}}\n")
                    elif (loop_bits_left >0 and consumeBits != baseSize):
                        out.append(f'{indent}{varName}{varIndex}.word[{wix}] = {varName}{varIndex}.word[{wix}] | (({src} << {consumeBits}){srcMask});\n')
                        out.append(f'{indent}_pos += {actual_bits-consumeBits};\n') if usePos else None
                    loop_current = loop_next

            else:
                srcMask = ''
                if (calcAlign):
                    out.append(f"{indent}_consume = std::min(_bits, (uint16_t)({baseSize}-(_pos & {baseMask})));\n")
                consumeBits = min(bitsLeft, baseSize - (currentPos % baseSize))
                srcMask = get_unpack_mask_str(bitsLeft, baseSize)
                out.append(f'{indent}{varName}{varIndex} = ({varType})(({src}{offsetShift}){srcMask});\n')
                bitsLeft -= consumeBits
                if (calcAlign):
                    out.append(f'{indent}_pos += _consume;\n') if usePos else None
                else:
                    out.append(f'{indent}_pos += {consumeBits};\n') if usePos else None
                if (calcAlign):
                    out.append(f"{indent}_bits -= _consume;\n")
                    out.append(f"{indent}if ((_bits > 0) && (_consume != {baseSize})) {{\n")
                    out.append(f'{indent}    {varName}{varIndex} = ({varType})({varName}{varIndex} | (({src} << _consume){srcMask}));\n')
                    out.append(f'{indent}    _pos += _bits;\n') if usePos else None
                    out.append(f"{indent}}}\n")
                elif (bitsLeft >0 and consumeBits != baseSize):
                    out.append(f'{indent}{varName}{varIndex} = ({varType})({varName}{varIndex} | (({src} << {consumeBits}){srcMask}));\n')
                    out.append(f'{indent}_pos += {bitsLeft};\n') if usePos else None
        elif data['entryType'] == 'NamedStruct':
            # nested structure, declare a tmp variable to hold the value and copy it to the destination
            tmpType, tmpRowType, tmpBaseSize = convertToType(data['arraywidth'])
            loop_current = currentPos
            # we are aligned if the current position is a multiple of the base size
            # except for the array case, unless the array case is the single element array case)
            isAligned = ((currentPos & (baseMask)) == 0) and not (data['isArray'] and not isSingleArray) 
            out.append(f'{indent}{{\n')
            indent += ' '*4
            if (isAligned):
                out.append(f'{indent}{varName}{varIndex}.unpack(*({varType}::_packedSt*)&{src});\n')
            else:
                out.append(f"{indent}{varType}::_packedSt _tmp{{0}};\n")
                if (bitwidth >= 64):
                    out.append(f"{indent}pack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, {data['bitwidth']});\n")
                else:
                    out.append(f"{indent}_tmp = (_src >> _pos) & ((1ULL << {data['bitwidth']}) - 1);\n")
                out.append(f'{indent}{varName}{varIndex}.unpack(_tmp);\n')
                # when we copied we used a tmp ptr to prevent overrun, reset point to correct place
            indent = indent[:-4]
            out.append(f'{indent}}}\n')
            out.append(f'{indent}_pos += {data["bitwidth"]};\n') if usePos else None
        else:
            assert(0)
        if data['isArray']:
            indent = indent[:-4]
            out.append(f"{indent}}}\n")
        currentPos = nextPos
    # if the last statement was an increment its dead code - delete it
    if out[-1].strip().startswith('_pos +='):
        out.pop()
    indent = indent[:-4]
    out.append(f'{indent}}}\n')

    return out

def fw_pack_setup(args, vars, indent):
    out = list()
    fw_pack_vars = dict()
    bitwidth = vars['width']
    out.append(f"{indent}memset(&_ret, 0, {vars['structure']}::_byteWidth);\n")
    retType, rowType, baseSize = convertToType(bitwidth)
    fw_pack_vars['bitwidth'] = bitwidth
    fw_pack_vars['retType'] = retType
    fw_pack_vars['rowType'] = rowType
    fw_pack_vars['baseSize'] = baseSize
    fw_pack_vars['cast'] = '(' + rowType + ')'
    fw_pack_vars['log2BaseSize'] = (baseSize-1).bit_length()
    return out, fw_pack_vars

def fw_pack_oneVar(fw_pack_vars, pos, args, data, indent):
    out = list()
    if fw_pack_vars['bitwidth'] > 64:
        ret = f"_ret[ {pos >> fw_pack_vars['log2BaseSize']} ]"
    else:
        ret = "_ret"
    isArray = data['isArray']
    baseMask = fw_pack_vars['baseSize'] - 1
    if isArray:
        srcPos = '_pos'
        incPos = f"_pos += {data['bitwidth']};\n"
        arrayIndex = "[i]"
    else:
        srcPos = pos
        incPos = None
        arrayIndex = ''
    if pos + data['arraywidth'] <= 64 and not isArray:
        if pos==0:
            out.append(f"{indent}{ret} = {data['variable']};\n")
        else:
            out.append(f"{indent}{ret} |= {fw_pack_vars['cast']}{data['variable']}{arrayIndex} << ({srcPos} & {baseMask});\n")
    else:
        if data['bitwidth'] <= 64:
            if data['bitwidth'] == 1 and not isArray:
                out.append(f"{indent}{ret} |= ({fw_pack_vars['cast']}{data['variable']} << ({srcPos} & {baseMask}));\n")
            else:
                # use pass by value
                out.append(f"{indent}pack_bits((uint64_t *)&_ret, {srcPos}, {data['variable']}{arrayIndex}, {data['bitwidth']});\n")
        else:
            # use pass by reference
            out.append(f'{indent}pack_bits((uint64_t *)&_ret, {srcPos}, (uint64_t *)&{data["variable"]}{arrayIndex}, {data["bitwidth"]});\n')
    out.append(f'{indent}{incPos}') if incPos else None
    return out

def fw_pack_oneNamedStruct(fw_pack_vars, pos, args, data, indent):
    out = list()
    # nested structure, declare a tmp variable to hold the value and copy it to the destination
    tmpType, tmpRowType, tmpBaseSize = convertToType(data['bitwidth'])
    baseSize = fw_pack_vars['baseSize']
    baseMask = baseSize - 1
    isArray = data['isArray']
    isAligned = ((pos & (baseMask)) == 0) and (not isArray or (data['arraywidth'] & baseMask == 0))

    if isArray:
        srcPos = '_pos'
        incPos = f"_pos += {data['bitwidth']};\n"
    else:
        srcPos = pos
        incPos = None
    if isAligned:
        # for aligned data we can go straight to the destination
        if data['arraywidth'] > 64:
            log2BaseSize = baseMask.bit_length()
            if isArray:
                dest = f"_ret[ _pos >> {log2BaseSize} ]"
            else:
                dest = f"_ret[ {pos >> log2BaseSize} ]"
        else:
            dest = "_ret"
    else:
        if data['bitwidth'] > 64:
            tmp = f"(uint64_t *)&_tmp"
        else:
            tmp = "_tmp"

    varType = data['subStruct']
    varName = data['variable']

    if isArray:
        varIndex = "[i]"
        blockClose = None
    else:
        varIndex = ''
        out.append(f'{indent}{{\n') #indent block to contain vars
        blockClose = f'{indent}}}\n'
        indent += ' '*4

    if (isAligned):
        # for aligned data we can go straight to the destination
        out.append(f'{indent}{varName}{varIndex}.pack(*({varType}::_packedSt*)&{dest});\n')
    else:
        # unaligned cases got through tmp value
        out.append(f"{indent}{data['subStruct']}::_packedSt _tmp{{0}};\n")
        out.append(f'{indent}{varName}{varIndex}.pack(_tmp);\n')
        if pos + data['arraywidth'] <= 64:
            out.append(f"{indent}_ret |= {fw_pack_vars['cast']}_tmp << ({srcPos} & {baseMask});\n")
        else:
            out.append(f'{indent}pack_bits((uint64_t *)&_ret, {srcPos}, {tmp}, {data["bitwidth"]});\n')
    out.append(f'{indent}{incPos}') if incPos else None
    out.append(blockClose) if blockClose else None
    return out

packUnpack = {
    'sc_pack': None,
    'sc_unpack': None,
    'fw_pack': {
        'functions': {
            'setup': fw_pack_setup,
            'oneVar' : fw_pack_oneVar,
            'namedStruct' : fw_pack_oneNamedStruct,
        },
        'declaration': {
            'header_inline': 'inline void pack(_packedSt &_ret) const\n',
            'header_split': 'void pack(_packedSt &_ret) const;\n',
            'cpp_split': "void {decl}{structure}::pack(_packedSt &_ret) const\n",
        },
        'posDeclare' : 'uint16_t _pos{{{}}};\n',
        'posCorrection' : '_pos = {};\n'
    },
    'fw_unpack': None,

}

def processPackUnpack(fname, handle, args, vars, indent):
    global packUnpack
    p = packUnpack[fname]
    out = list()

    # handle the declaration
    decl = f"{args.namespace}::" if args.namespace else ''
    if args.section == 'cpp' and handle == 'inline':
        return out
    declFn = p['declaration'].get(args.section + '_' + handle, None)
    out.append(indent + declFn.format(decl=decl, structure=vars['structure'])) if declFn else None
    if args.section == 'header' and handle == 'split':
        return out
    out.append(f'{indent}{{\n')
    indent += ' '*4

    # perform any setup
    setupFn = p['functions'].get('setup', None)
    setupOut, setupVars = setupFn(args, vars, indent) if setupFn else ([], {})
    out.extend(setupOut)
    posDeclare = p.get('posDeclare', None)
    posCorrection = p.get('posCorrection', None)

    # loop through the vars
    pos = 0
    posCorrect = True

    count = len(vars['vars'])
    varFn = p['functions'].get('oneVar', None)
    namedStructFn = p['functions'].get('namedStruct', varFn) # note use varFn if not defined

    for _, data in reversed(vars['vars'].items()):
        count -= 1
        setupVars['last'] = (0 == count)
        loopClose = None
        if data['isArray']:
            if posDeclare:
                # this is the first time so declare the position, one time
                out.append(indent + posDeclare.format(pos))
                posDeclare = None
            else:
                out.append(indent + posCorrection.format(pos)) if not posCorrect and posCorrection else None
            out.append(f"{indent}for(int i=0; i<{data['arraySize']}; i++) {{\n")
            loopClose = f"{indent}}}\n"
            indent += ' '*4
        if data['entryType'] == 'NamedStruct':
            out.extend(namedStructFn(setupVars, pos, args, data, indent))
        else:
            out.extend(varFn(setupVars, pos, args, data, indent))
        pos += data['arraywidth']
        posCorrect = data['isArray']

        if loopClose:
            out.append(loopClose)
            indent = indent[:-4]
    # closing
    ret = p.get('return', None)
    out.append(indent + ret) if ret else None
    indent = indent[:-4]
    out.append(f'{indent}}}\n')
    return out


def structTest(args, prj, data):
    out = list()
    fn = os.path.splitext(os.path.basename(data['context']))[0] + '_structs'
    if args.section == 'testStructsHeader':
        out.append(f'class test_{fn} {{\n')
        out.append(f'public:\n')
        out.append(f'    static std::string name(void);\n')
        out.append(f'    static void test(void);\n')
        out.append(f'}};\n')
        return out

    out.append(f'#include "q_assert.h"\n')
    out.append(f'std::string test_{fn}::name(void) {{ return "test_{fn}"; }}\n')
    out.append(f'void test_{fn}::test(void) {{\n')
    indent = ' '*4
    out.append(f'{indent}std::vector<uint8_t> patterns{{0x6a, 0xa6}};\n')
    out.append(f'{indent}cout << "Running " << name() << endl;\n')
    for _, value in data['structures'].items():
        struct = value['structure']
        out.append(f'{indent}for(auto pattern : patterns) {{\n')
        indent += ' '*4
        out.append(f'{indent}{struct}::_packedSt packed;\n')
        out.append(f'{indent}memset(&packed, pattern, {struct}::_byteWidth);\n')
        out.append(f'{indent}sc_bv<{struct}::_bitWidth> aInit;\n')
        out.append(f'{indent}sc_bv<{struct}::_bitWidth> aTest;\n')
        out.append(f'{indent}for (int i = 0; i < {struct}::_byteWidth; i++) {{\n')
        out.append(f'{indent}    int end = std::min((i+1)*8-1, {struct}::_bitWidth-1);\n')
        out.append(f'{indent}    aInit.range(end, i*8) = pattern;\n')
        out.append(f'{indent}}}\n')
        out.append(f'{indent}{struct} a;\n')
        out.append(f'{indent}a.sc_unpack(aInit);\n')
        out.append(f'{indent}{struct} b;\n')
        out.append(f'{indent}b.unpack(packed);\n')
        out.append(f'{indent}if (!(b == a)) {{;\n')
        out.append(f'{indent}    cout << a.prt();\n')
        out.append(f'{indent}    cout << b.prt();\n')
        out.append(f'{indent}    Q_ASSERT(false,"{struct} fail");\n')
        out.append(f'{indent}}}\n')
        out.append(f'{indent}uint64_t test;\n')
        out.append(f'{indent}memset(&test, pattern, 8);\n')
        out.append(f'{indent}b.pack(packed);\n')
        out.append(f'{indent}aTest = a.sc_pack();\n')
        out.append(f'{indent}if (!(aTest == aInit)) {{;\n')
        out.append(f'{indent}    cout << a.prt();\n')
        out.append(f'{indent}    cout << aTest;\n')
        out.append(f'{indent}    Q_ASSERT(false,"{struct} fail");\n')
        out.append(f'{indent}}}\n')
        out.append(f'{indent}uint64_t *ptr = (uint64_t *)&packed;\n')
        out.append(f'{indent}uint16_t bitsLeft = {struct}::_bitWidth;\n')
        out.append(f'{indent}do {{\n')
        out.append(f'{indent}    int bits = std::min((uint16_t)64, bitsLeft);\n')
        out.append(f'{indent}    uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);\n')
        out.append(f'{indent}    if ((*ptr & mask) != (test & mask)) {{;\n')
        out.append(f'{indent}        cout << a.prt();\n')
        out.append(f'{indent}        cout << b.prt();\n')
        out.append(f'{indent}        Q_ASSERT(false,"{struct} fail");\n')
        out.append(f'{indent}    }}\n')
        out.append(f'{indent}    bitsLeft -= bits;\n')
        out.append(f'{indent}    ptr++;\n')
        out.append(f'{indent}}} while(bitsLeft > 0);\n')
        indent = indent[:-4]
        out.append(f'{indent}}}\n')
    out.append(f'}}\n')
    return out