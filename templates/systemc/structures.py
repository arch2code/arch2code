from pysrc.intf_gen_utils import FW_NAMESPACE, get_const, wrap_module_namespace, wrap_fw_namespace, wrap_module_test_namespace, cpp_namespace_name
from pysrc.arch2codeHelper import printError, warningAndErrorReport
from templates.systemc.includes import constReference_cpp, typeWidthExpression_cpp
dataTypeMappings = [
    {'maxSize': 1, 'unsignedType': 'uint8_t', 'signedType': 'int8_t'},
    {'maxSize': 8, 'unsignedType': 'uint8_t', 'signedType': 'int8_t'},
    {'maxSize': 16, 'unsignedType': 'uint16_t', 'signedType': 'int16_t'},
    {'maxSize': 32, 'unsignedType': 'uint32_t', 'signedType': 'int32_t'},
    {'maxSize': 64, 'unsignedType': 'uint64_t', 'signedType': 'int64_t'},
    {'maxSize': 4096, 'unsignedType': 'uint64_t', 'signedType': 'int64_t', 'arrayElementSize': 64}
]

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    valid_sections = ('', 'header', 'cpp', 'headerIncludes', 'cppIncludes', 'testStructsHeader', 'testStructsCPP')
    if args.section not in valid_sections:
        raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are header, cpp, headerIncludes, cppIncludes, testStructsHeader, testStructsCPP")
    # The include and declaration sections are independent: an fw context with only
    # constants/types/enums still needs the baseline includes those declarations use,
    # so only the struct-bearing sections short-circuit on an empty structure set.
    hasStructures = len(data['structures']) > 0
    if not hasStructures and args.section not in ('headerIncludes', 'cppIncludes'):
        return ""
    global codeMapping
    # using list to simplify all the last loop special cases to allow simple delete of last entry
    # to effectively backup
    out = list()
    if (args.section == '' or args.section == 'cpp' or args.section == 'header'):
        args.mode = resolveMode(args.mode)
        if args.section == '':
            args.section = 'header'
        out.append("// structures")
        for struct, value in data['structures'].items():
            out.extend(oneStruct(args, prj, data, struct, value))
        out = wrap_module_namespace(args, data, out)
        if args.section == 'header':
            # The cpp section spells its out-of-line definitions `fw_ns::<struct>::`
            # from args.namespace, so only the declarations are wrapped.
            out = wrap_fw_namespace(args, out)
    # handle system includes
    if (args.section == 'headerIncludes' or args.section == 'cppIncludes'):
        fwCpp = args.section == 'cppIncludes' and args.mode == 'fw'
        if fwCpp:
            # The fw source scaffold delegates its whole preamble to this region.
            out.append(f'#include "{data["includeFiles"]["includeFW_src"][data["context"]]["siblingHeaderName"]}"')
        out.extend(systemIncludes(args.mode, args.section, hasStructures))
        if fwCpp:
            # Covers a future split definition's leading return type, which is looked up
            # at namespace scope. No fw feature is 'split' today, and the declarator
            # itself stays qualified from args.namespace either way.
            out.append(f'using namespace {FW_NAMESPACE};')
    if (args.section == 'testStructsHeader' or args.section == 'testStructsCPP'):
        out.extend(structTest(args, prj, data))
        out = wrap_module_test_namespace(args, data, out)
    out.append("")
    return("\n".join(out))


includeMapping = {
    'prtFmt': ['"logging.h"'],
    'fw_pack': ['<algorithm>', '"bitTwiddling.h"'],
    'fw_unpack': ['<algorithm>'],
}
# Headers the context's own declarations need whatever the optional codeMapping
# features are, keyed by emission mode. Only fw carries entries: an fw header
# includes no framework header, while model/module get both through systemc.h.
# Emitted even for a structure-less context, whose constants and types are uint*_t
# too. Coverage is exhaustive so a new mode fails loud.
baselineIncludes = {
    'model': [],
    'fw': ['<cstdint>', '<cstring>'],
    'module': [],
}
def systemIncludes(mode, section, hasStructures):
    # The headers a context's struct declarations need, by emission mode and by
    # which artifact (header or cpp) carries the feature. Called with an explicit
    # mode/section rather than off `args` because the module unit's caller is the
    # global-module-fragment emitter, whose own section name is not one of these.
    global codeMapping, includeMapping, baselineIncludes
    mode = resolveMode(mode)

    out = list()
    includeDict = dict()
    if section == 'headerIncludes':
        includeDict.update({include: True for include in baselineIncludes[mode]})
    if hasStructures:
        # Every codeMapping feature is a struct member.
        for key, value in codeMapping[mode].items():
            if key in includeMapping:
                if (value == 'split' and section == 'cppIncludes') or (value == 'inline' and section == 'headerIncludes'):
                    # extend dict by iterating over includeMapping list
                    includeDict.update({include: True for include in includeMapping[key]})

    for lib in includeDict:
        out.append(f"#include {lib}")
    return out


def convertToType(bitwidth, name="_packedSt", isSigned=False):
    global dataTypeMappings
    for myType in dataTypeMappings:
        if bitwidth <= myType['maxSize']:
            arrayElementSize = myType.get('arrayElementSize', 0)
            # Select signed or unsigned type based on isSigned parameter
            typeStr = myType['signedType'] if isSigned else myType['unsignedType']
            if arrayElementSize > 0:
                # round up to the nearest multiple using integer div, plus one if there is a modulo non zero
                typeArraySize = bitwidth // arrayElementSize + (bitwidth % arrayElementSize > 0)
                retType = f"{typeStr} {name}[{typeArraySize}]"
                rowType = typeStr
                baseSize = arrayElementSize
            else:
                retType = f"{typeStr} {name}"
                rowType = typeStr
                baseSize = myType['maxSize']
            #if we found something terminate the list as we want the smallest type
            break
    return retType, rowType, baseSize

def structBitWidthExpression_cpp(value, prj, useConfig=False):
    """Build a C++ constexpr expression for a structure's _bitWidth.

    Iterates over vars and emits terms for each:
    - NamedVar/NamedType: uses symbolic expression from typeWidthExpression_cpp
    - NamedStruct: uses subStructName::_bitWidth reference
    - Reserved: uses integer align value
    Array vars multiply by array size.
    Terms are joined with ' + '.
    # TODO: handle variable size parameters (parameterized widths)
    """
    terms = []
    for var, vardata in reversed(value['vars'].items()):
        arraySizeValue = vardata['arraySizeValue']
        isArray = vardata['isArray']

        if vardata['entryType'] == 'NamedVar' or vardata['entryType'] == 'NamedType':
            expr = typeWidthExpression_cpp(prj.data['types'][vardata['varTypeKey']], prj, useConfig)
        elif vardata['entryType'] == 'NamedStruct':
            subStructInfo = prj.data['structures'][vardata['subStructKey']]
            if useConfig and subStructInfo['isParameterizable']:
                expr = f"{vardata['subStruct']}<Config>::_bitWidth"
            else:
                expr = f"{vardata['subStruct']}::_bitWidth"
        elif vardata['entryType'] == 'Reserved':
            expr = str(vardata['bitwidth'])
        else:
            expr = str(vardata['bitwidth'])

        if isArray and arraySizeValue > 1:
            # Wrap non-trivial expressions in parens before multiplying
            if '+' in expr or '-' in expr:
                expr = f"({expr})"
            # Use symbolic constant name if available, else literal integer
            arraySizeExpr = cppArraySize(vardata, prj, useConfig)
            expr = f"{expr}*{arraySizeExpr}"

        terms.append(expr)

    return ' + '.join(terms) if terms else '0'


def cppArraySize(vardata, prj, useConfig=False):
    # arraySizeKey is empty when arraySize is a literal rather than a constant reference
    arraySizeKey = vardata['arraySizeKey']
    if useConfig and arraySizeKey and prj.data['constants'][arraySizeKey]['isParameterizable']:
        return constReference_cpp(arraySizeKey, prj, useConfig=True)
    return vardata['arraySize']


def cppVarBitwidth(vardata, prj, useConfig=False):
    if vardata['entryType'] == 'NamedVar' or vardata['entryType'] == 'NamedType':
        return typeWidthExpression_cpp(prj.data['types'][vardata['varTypeKey']], prj, useConfig)
    if vardata['entryType'] == 'NamedStruct':
        subStructInfo = prj.data['structures'][vardata['subStructKey']]
        if useConfig and subStructInfo['isParameterizable']:
            return f"{vardata['subStruct']}<Config>::_bitWidth"
        return f"{vardata['subStruct']}::_bitWidth"
    return str(vardata['bitwidth'])


def cppTypeName(vardata, prj, useConfig=False):
    if vardata['entryType'] == 'NamedStruct':
        subStructInfo = prj.data['structures'][vardata['subStructKey']]
        if useConfig and subStructInfo['isParameterizable']:
            return f"{vardata['subStruct']}<Config>"
        return vardata['subStruct']
    varType = vardata['varType']
    # varTypeKey is empty for fields that name no type - Reserved, and a subStruct
    # field rewritten to NamedType by the datapath backdoor - so it keys no types row
    typeKey = vardata['varTypeKey']
    if useConfig and typeKey and prj.data['types'][typeKey]['isParameterizable']:
        return f"{varType}<Config>"
    return varType


def packedStType(varType):
    # ::_packedSt on a templated (parameterized) type such as rgb_pixel_t<Config>
    # is a dependent type, so C++ requires the typename keyword. Non-parameterized
    # types (e.g. ipFixedArraySt) must NOT use typename in these non-dependent contexts.
    prefix = 'typename ' if '<' in varType else ''
    return f"{prefix}{varType}::_packedSt"


def cppWidthMask(widthExpr):
    if isinstance(widthExpr, int):
        widthExpr = str(widthExpr)
    if str(widthExpr) == '1':
        return ' & 1'
    return f" & ((1ULL << ({widthExpr})) - 1)"

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

def printOneArray(prefix, space, varName, varData, prj, isModel, prtoss=True, useConfig=False):
    out = list()
    postfix = ''
    decorators = ''
    arraySize = varData['arraySizeValue']
    arraySizeExpr = cppArraySize(varData, prj, useConfig)
    varType = cppTypeName(varData, prj, useConfig)
    varLoopCount = varData["varLoopCount"]
    if prtoss:
        start = f'{prefix}<< "{space}{varName}[0:{arraySize-1}]: "'
    else:
        start = f'{space}{varName}[0:{arraySize-1}]: '
    if not isModel:
        if not prtoss:
            start += 'Not printed'
        varPrint = '"Not printed"'
    else:
        decorators = ' << ' if prtoss else '{}'
        if varLoopCount > 1:
            varPrint = f'static2DArrayPrt<{varType}, uint64_t, {arraySizeExpr}, {varLoopCount}>({varName}, all)'
        else:
            varPrint = f'staticArrayPrt<{varType}, {arraySizeExpr}>({varName}, all)'

    return (start, decorators, varPrint, postfix)

def printOneSubstructArray(prefix, space, varName, varData, prj=None, prtoss=True, useConfig=False):
    out = list()
    varType = cppTypeName(varData, prj, useConfig) if prj else varData["subStruct"]
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
    arraySizeExpr = cppArraySize(varData, prj, useConfig) if prj else varData["arraySize"]
    varPrint = f'structArrayPrt<{varType}, {arraySizeExpr}>({varName}, "{varName}", all)'

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
    },
    'module': {
        'equal': 'inline',
        'sc_trace': 'inline',
        'operatorStream': 'inline',
        'prtFmt': 'inline',
        'tracker': 'inline',
        'getSet': 'inline',
        'fw_pack': 'inline',
        'fw_unpack': 'inline',
        'registerFeatures': 'inline',
        'sc_pack': 'inline',
        'sc_unpack': 'inline',
        'constuctor_bv': 'inline',
        'constructor': 'inline',
        'constructor_packed': 'inline',
    }
}

# The emission flavor a render is keyed by. Absent means the model flavor; anything
# else must key BOTH mode-keyed tables. Rejected here rather than at the three lookups
# downstream, each of which would raise KeyError far from the cause.
def resolveMode(mode):
    if mode == '':
        return 'model'
    if mode not in codeMapping or mode not in baselineIncludes:
        printError(f"emission mode '{mode}' is not registered in the codeMapping and "
                   f"baselineIncludes tables in templates/systemc/structures.py. "
                   f"Either correct the --mode token on the file's "
                   f"GENERATED_CODE_PARAM line, or register the mode by adding it to "
                   f"both tables there (a context artifact's token is fixed by "
                   f"pysrc/genFileParam.py::_CONTEXT_FILE_MODE).")
        exit(warningAndErrorReport())
    return mode

def oneStruct(args, prj, data, struct, value):
    global codeMapping
    isCpp = (args.section == 'cpp')
    isParam = value['isParameterizable']
    if isCpp and isParam:
        return []

    out = list()
    structName = value['structure']
    indent = '' if isCpp else ' '*4
    if not isCpp:
        # first few things are not optinal and always in the header
        if isParam:
            out.append("template<typename Config>")
        out.append(f"struct {structName} {{")
        # declare vars
        out.extend(declareVars(value, indent, prj, isParam))
        if args.mode == 'fw':
            out.append(f"\n{indent}{structName}() {{ memset(this, 0, sizeof({ value['structure'] })); }}\n")
        else:
            out.append(f"\n{indent}{structName}() {{}}\n")
        # consts
        bitWidthExpr = structBitWidthExpression_cpp(value, prj, isParam)
        prefix = f"{indent}static constexpr uint16_t _bitWidth = "
        maxLineLen = 120
        fullLine = f"{prefix}{bitWidthExpr};"
        if len(fullLine) <= maxLineLen:
            out.append(fullLine)
        else:
            # Wrap at ' + ' term boundaries
            terms = bitWidthExpr.split(' + ')
            contIndent = ' ' * len(prefix)
            lines = []
            curLine = prefix + terms[0]
            for term in terms[1:]:
                candidate = curLine + ' + ' + term
                if len(candidate) > maxLineLen and curLine != prefix + terms[0]:
                    lines.append(curLine)
                    curLine = contIndent + '+ ' + term
                else:
                    curLine = candidate
            lines.append(curLine + ';')
            out.extend(lines)
        out.append(f"{indent}static constexpr uint16_t _byteWidth = (_bitWidth + 7) >> 3;")
        packedWidth = value['maxBitwidth'] if isParam else value['width']
        retType, rowType, baseSize = convertToType(packedWidth)
        if isParam and packedWidth <= 64:
            retType = 'uint64_t _packedSt'
        out.append(f"{indent}typedef {retType};")

    # handle all optional components based on config table
    featureMapping = codeMapping[args.mode].copy()
    if isParam:
        for feature, handle in featureMapping.items():
            if handle == 'split':
                featureMapping[feature] = 'inline'
    for feature, handle in featureMapping.items():
        if handle == 'disable':
            continue
        match feature:
            case 'equal': # equal test
                args._prj = prj
                out.extend(equalTest(handle, args, structName, value, indent))
            case 'sc_trace':
                args._prj = prj
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
                out.extend(getSet(value, indent, prj, isParam)) if not isCpp else None
            case 'fw_pack':
                out.extend(processPackUnpack("fw_pack", handle, args, value, indent, prj, isParam))
            case 'fw_pack_ret':
                out.extend(processPackRet(structName, value, indent))
            case 'fw_unpack':
                out.extend(fw_unpack(handle, args, value, indent, prj, isParam))
            case 'registerFeatures': # register features
                if not isCpp and value['register']:
                    out.extend(registerFeatures(value, indent))
            case 'sc_pack':
                out.extend(sc_pack(handle, args, value, indent, prj))
            case 'sc_unpack':
                if value['width'] == 1:
                    out.extend(sc_unpack(handle, args, "bool", value, indent, prj, isParam))
                structTypeName = f"{structName}<Config>" if isParam else structName
                out.extend(sc_unpack(handle, args, f"sc_bv<{structTypeName}::_bitWidth>", value, indent, prj, isParam))
            case 'constuctor_bv':
                out.extend(constuctor_bv(structName, value, indent)) if not isCpp else None
            case 'constructor':
                out.extend(constructor(structName, value, indent, prj, isParam)) if not isCpp else None
            case 'constructor_packed':
                out.extend(constructor_packed(structName, value, indent)) if not isCpp else None
            # Internal-consistency guard: a codeMapping feature with no arm above has
            # no renderer, so it cannot be emitted. Must abort NON-ZERO - exiting here
            # unwinds before the artifact is written, so a zero status would report
            # success on a file that was never updated.
            case _:
                printError(f"codeMapping feature '{feature}' (mode '{args.mode}', "
                           f"handling '{handle}') has no case arm in "
                           f"templates/systemc/structures.py::oneStruct, so it cannot "
                           f"be rendered for struct '{structName}'. Add the arm there "
                           f"alongside the codeMapping entry.")
                exit(warningAndErrorReport())

    if not isCpp:
        out.append(f'\n}};')
    return out

def declareVars(vars, indent, prj, useConfig=False):
    out = list()
    for var, vardata in reversed(vars["vars"].items()):
        if vardata['isArray']:
            myArray= f"[{cppArraySize(vardata, prj, useConfig)}]"
            #myArrayLoopIndex= '[i]'
        else:
            myArray= ''
            #myArrayLoopIndex= ''
        if vardata['entryType'] == 'NamedVar' or vardata['entryType'] == 'NamedType' or vardata['entryType'] == 'Reserved':
            out.append(f"{indent}{cppTypeName(vardata, prj, useConfig)} {vardata['variable'] + myArray}; //{ vardata['desc'] }")
        elif vardata['entryType'] == 'NamedStruct':
            out.append(f"{indent}{cppTypeName(vardata, prj, useConfig)} {vardata['variable'] +myArray}; //{ vardata['desc'] }")
    return out

def equalTest(handle, args, structName, vars, indent):
    out = list()
    isParam = vars['isParameterizable']
    qualifiedStructName = f"{structName}<Config>" if isParam else structName
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}inline bool operator == (const { qualifiedStructName } & rhs) const {{")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}bool operator == (const { qualifiedStructName } & rhs) const;")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}bool {decl}{structName}::operator == (const { qualifiedStructName } & rhs) const {{")
    else:
        return out
    out.append(f"{indent}    bool ret = true;")
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
            arraySizeExpr = cppArraySize(vardata, args._prj, isParam) if hasattr(args, '_prj') else vardata['arraySize']
            out.append(f"{indent}for(unsigned int i=0; i<{arraySizeExpr}; i++) {{")
            indent += ' '*4

        if vardata['bitwidth'] <= 64 or vardata['generator'] == 'datapath' or vardata['entryType'] == 'NamedStruct':
            out.append(f"{indent}ret = ret && ({varName+myArrayLoopIndex} == rhs.{varName+myArrayLoopIndex});")
        else:
            for i in range(0, vardata['varLoopCount']):
                out.append(f"{indent}ret = ret && ({varName+myArrayLoopIndex}.word[ {i} ] == rhs.{varName+myArrayLoopIndex}.word[ {i} ]);")
        if vardata['isArray']:
            indent = indent[:-4]
            out.append(f"{indent}}}")
    out.append(f"{indent}return ( ret );")
    out.append(f"{indent}}}")
    return out

def scTrace(handle, args, structName, vars, indent):
    out = list()
    isParam = vars['isParameterizable']
    qualifiedStructName = f"{structName}<Config>" if isParam else structName
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}inline friend void sc_trace(sc_trace_file *tf, const {qualifiedStructName} & v, const std::string & NAME ) {{")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}void sc_trace(sc_trace_file *tf, const {qualifiedStructName} & v, const std::string & NAME );")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}void {decl}{structName}::sc_trace(sc_trace_file *tf, const {structName} & v, const std::string & NAME ) {{")
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
            arraySizeExpr = cppArraySize(vardata, args._prj, isParam) if hasattr(args, '_prj') else vardata['arraySize']
            out.append(f"{indent}for(unsigned int i=0; i<{arraySizeExpr}; i++) {{")
            indent += ' '*4

        if vardata['bitwidth'] <= 64 or vardata['generator'] == 'datapath' or vardata['entryType'] == 'NamedStruct':
            out.append(f'{indent}sc_trace(tf,v.{varName+myArrayLoopIndex}, NAME + ".{varName+myArrayLoopIndex}");')
        else:
            for i in range(0, vardata['varLoopCount']):
                out.append(f'{indent}sc_trace(tf,v.{varName+myArrayLoopIndex}.word[ {i} ], NAME + ".{varName+myArrayLoopIndex}.word[ {i} ]");')
        if vardata['isArray']:
            indent = indent[:-4]
            out.append(f"{indent}}}")
    out.append(f"    }}")
    return out

def operatorStream(structName, indent):
    out = list()
    out.append(f"{indent}inline friend ostream& operator << ( ostream& os,  {structName} const & v ) {{")
    out.append(f'{indent}    os << v.prt();')
    out.append(f"{indent}    return os;")
    out.append(f"{indent}}}")
    return out

def convertToList(start, decorators, varPrint, postfix):
    out = list()
    if isinstance(varPrint, list):
        for dec, var in zip(decorators, varPrint):
            out.append(start + dec + var )
            start = ''
        out[-1] = out[-1] + postfix
    else:
        out.append(start + decorators + varPrint + postfix )
    return out

def prt(handle, args, vars, indent, prj):
    out = list()
    useConfig = vars['isParameterizable']
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}std::string prt(bool all=false) const")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}std::string prt(bool all=false) const;")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}std::string {decl}{vars['structure']}::prt(bool all) const")
    else:
        return out
    out.append(f"{indent}{{")
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
            isModel = (args.mode in ('model', 'module'))
            out.extend(convertToList(*printOneArray(prefix, space, varName, vardata, prj, isModel, useConfig=useConfig)))
        elif vardata['isArray'] and vardata['subStruct']:
            out.extend(convertToList(*printOneSubstructArray(prefix, space, varName, vardata, prj, useConfig=useConfig)))
        else:
            out.extend(convertToList(*printOneVar(prefix, space, varName, vardata, prj)))
        space = ' '
    # add semicolon to the last item in the list
    out[-1] = out[-1] +';'
    out.append(f"{indent}")
    out.append(f"{indent}return oss.str();")
    indent = indent[:-4]
    out.append(f"{indent}}}")
    return out

def prtFmt(handle, args, vars, indent, prj):
    out = list()
    useConfig = vars['isParameterizable']
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}std::string prt(bool all=false) const")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}std::string prt(bool all=false) const;")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}std::string {decl}{vars['structure']}::prt(bool all) const")
    else:
        return out
    out.append(f"{indent}{{")
    indent += ' '*4
    space = ''
    prefix = '   '
    varList = list()
    for var, vardata in vars['vars'].items():
        varName = vardata['variable']
        if vardata['isArray'] and not vardata['subStruct']:
            isModel = (args.mode in ('model', 'module'))
            varList.append(printOneArray(prefix, space, varName, vardata, prj, isModel, False, useConfig))
        elif vardata['isArray'] and vardata['subStruct']:
            varList.append(printOneSubstructArray(prefix, space, varName, vardata, prj, False, useConfig))
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
                varOut.append(f'{indent}   {var},')
        else:
            fmt += item[0] + item[1]
            # Non-model arrays intentionally emit a literal "Not printed"
            # label with no replacement field. Keep that special case from
            # adding an unused argument while preserving args for fields such
            # as enums whose format specifier is embedded in item[0].
            if item[1] or item[2] != '"Not printed"':
                varOut.append(f'{indent}   {item[2]},')
    if varOut:
        # add semicolon to the last item in the list
        varOut[-1] = varOut[-1][:-1]
        out.append(f'{indent}return (std::format("{fmt}",')
        out.extend(varOut)
        out.append(f"{indent}));")
    else:
        out.append(f'{indent}return ("{fmt}");')
    indent = indent[:-4]
    out.append(f"{indent}}}")
    return out

def tracker(vars, indent):
    out = list()
    out.append(f'{indent}static const char* getValueType(void) {{ return( "{vars["trackerType"] }" );}}')
    # getTrackerValue
    if vars['trackerValid']:
        ret = f"{ vars['trackerVar'] }"
    else:
        ret = f"-1"
    out.append(f"{indent}inline uint64_t getStructValue(void) const {{ return( {ret} );}}")
    return out

def getSet(vars, indent, prj=None, useConfig=False):
    out = list()
    for var, vardata in vars['vars'].items():
        generator = vardata['generator']
        # Route through cppTypeName so parameterizable field types keep their
        # <Config> template argument; non-parameterizable types emit bare name.
        varType = cppTypeName(vardata, prj, useConfig) if prj else vardata['varType']
        # next features
        if generator == 'next':
            out.append(f"{indent}inline {varType} _getNext(void) {{ return( { var }); }}")
            out.append(f"{indent}inline void _setNext({varType} value) {{ { var } = value; }}")
        # listValid features
        if generator == 'listValid':
            out.append(f"{indent}inline {varType} _getValid(void) {{ return( { var }); }}")
            out.append(f"{indent}inline void _setValid({varType} value) {{ { var } = value; }}")
        # listHead features
        if generator == 'listHead':
            out.append(f"{indent}inline {varType} _getHead(void) {{ return( { var }); }}")
            out.append(f"{indent}inline void _setHead({varType} value) {{ { var } = value; }}")
        # listTail features
        if generator == 'listTail':
            out.append(f"{indent}inline {varType} _getTail(void) {{ return( { var }); }}")
            out.append(f"{indent}inline void _setTail({varType} value) {{ { var } = value; }}")
        # address field
        if generator == 'address':
            out.append(f"{indent}inline {varType} _getAddress(void) {{ return( { var }); }}")
        # address field
        if generator == 'data':
            out.append(f"{indent}inline {varType} _getData(void) {{ return( { var }); }}")
            out.append(f"{indent}inline void _setData({varType} value) {{ { var } = value; }}")
    return out
def registerFeatures(vars, indent):
    out = list()
    out.append(f"{indent}// register functions")
    out.append(f"{indent}inline int _size(void) {{return( (_bitWidth + 7) >> 4 ); }}")
    out.append(f"{indent}uint64_t _getValue(void)")
    out.append(f"{indent}{{")
    indent = ' '*8
    out.append(f"{indent}uint64_t ret =")
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
        out.append(f" +")
    out.pop()
    out[-1] = out[-1] + ";"
    out.append(f"{indent}return( ret );")
    indent = ' '*4
    out.append(f"{indent}}}")
    out.append(f"{indent}void _setValue(uint64_t value)")
    out.append(f"{indent}{{")
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
                out.append(f"{indent}{ varName }._setValue( (( value >> { vardata['bitshift'] } ) )) ;")
            else:
                out.append(f"{indent}{ varName }._setValue( (( value >> { vardata['bitshift'] } ) & (( (uint64_t)1 << { vardata['bitwidth'] } ) - 1)) ) ;")
        else:
            if vardata['bitwidth'] >= 64:
                out.append(f"{indent}{ varName } = ( { vardata['varType'] } ) (( value >> { vardata['bitshift'] } ) ) ;")
            else:
                out.append(f"{indent}{ varName } = ( { vardata['varType'] } ) (( value >> { vardata['bitshift'] } ) & (( (uint64_t)1 << { vardata['bitwidth'] } ) - 1)) ;")
    out.append(f"{indent}}}")
    return out

# sc_pack
def sc_pack(handle, args, vars, indent, prj=None):
    out = list()
    structName = vars['structure']
    isParam = vars['isParameterizable']
    qualifiedStructName = f"{structName}<Config>" if isParam else structName
    if vars['width'] > 1:
        structType = f"sc_bv<{qualifiedStructName}::_bitWidth>"
    else:
        structType = 'bool'
    posUpdate = None
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}inline {structType} sc_pack(void) const")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}{structType} sc_pack(void) const;")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}{structType} {decl}{vars['structure']}::sc_pack(void) const")
    else:
        return out
    out.append(f'{indent}{{')
    indent += ' '*4
    out.append(f"{indent}{structType} packed_data;")
    high,low = 0,0
    if isParam:
        out.append(f"{indent}uint16_t _pos{{0}};")
    for _, data in reversed(vars['vars'].items()):
        varName = data['variable']
        varIndex = ''
        high = low + data['arraywidth'] - 1
        widthExpr = cppVarBitwidth(data, prj, isParam) if prj else data['bitwidth']
        if data['generator'] == 'datapath':
            num_bytes = int(data['bitwidth'] / 8)
            out.append(f'{indent}for(unsigned int bsl=0; bsl<{num_bytes}; bsl++) {{')
            rng_high, rng_low  = f"{low}+bsl*8+7", f"{low}+bsl*8"
            indent += ' '*4
            out.append(f'{indent}packed_data.range({rng_high}, {rng_low}) = {varName}[bsl];')
            indent = indent[:-4]
            out.append(f"{indent}}}")
        else:
            if data['isArray']:
                varIndex = f"[i]"
                arraySizeExpr = data['arraySize']
                if isParam:
                    arraySizeExpr = cppArraySize(data, prj, True)
                    widthExpr = cppVarBitwidth(data, prj, True)
                out.append(f"{indent}for(unsigned int i=0; i<{arraySizeExpr}; i++) {{")
                if isParam:
                    rng_high, rng_low  = f"_pos+{widthExpr}-1", "_pos"
                    posUpdate = f"_pos += {widthExpr};"
                else:
                    rng_high, rng_low  = f"{low}+(i+1)*{widthExpr}-1", f"{low}+i*{widthExpr}"
                indent += ' '*4
            else:
                if isParam:
                    widthExpr = cppVarBitwidth(data, prj, True)
                    rng_high, rng_low  = f"_pos+{widthExpr}-1", "_pos"
                else:
                    rng_high, rng_low  = f"{high}", f"{low}"
            if data['entryType'] == 'NamedVar' or data['entryType'] == 'NamedType' or data['entryType'] == 'Reserved':
                if structType != 'bool':
                    if data['bitwidth'] >= 64 and data['entryType'] != 'NamedStruct' and data['varLoopCount'] > 1 and isParam:
                        widthExpr = cppVarBitwidth(data, prj, True)
                        for wix in range(data['varLoopCount']):
                            out.append(f'{indent}if ({widthExpr} > {wix * 64}) {{')
                            out.append(f'{indent}    uint16_t _bits = std::min((uint16_t)64, (uint16_t)({widthExpr} - {wix * 64}));')
                            out.append(f'{indent}    packed_data.range(_pos + {wix * 64} + _bits - 1, _pos + {wix * 64}) = {varName}{varIndex}.word[{wix}];')
                            out.append(f'{indent}}}')
                    elif data['bitwidth'] >= 64 and data['entryType'] != 'NamedStruct' and data['varLoopCount'] > 1:
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
                            out.append(f'{indent}packed_data.range({rng_high}, {rng_low}) = {varName}{varIndex}.word[{wix}];')
                    else:
                        out.append(f'{indent}packed_data.range({rng_high}, {rng_low}) = {varName}{varIndex};')
                else:
                    out.append(f'{indent}packed_data = ({structType}) {varName}{varIndex};')
            elif data['entryType'] == 'NamedStruct':
                out.append(f'{indent}packed_data.range({rng_high}, {rng_low}) = {varName}{varIndex}.sc_pack();')
            else:
                assert(0)
            if data['isArray']:
                if isParam and posUpdate:
                    out.append(f"{indent}{posUpdate}")
                    posUpdate = None
                indent = indent[:-4]
                out.append(f"{indent}}}")
            elif isParam:
                out.append(f"{indent}_pos += {widthExpr};")

        low = high + 1
    out.append(f"{indent}return packed_data;")
    indent = indent[:-4]
    out.append(f'{indent}}}')
    return out

# sc_unpack
def sc_unpack(handle, args, structType, vars, indent, prj=None, useConfig=False):
    out = list()
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}inline void sc_unpack({structType} packed_data)")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}void sc_unpack({structType} packed_data);")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}void {decl}{vars['structure']}::sc_unpack({structType} packed_data)")
    else:
        return out
    out.append(f'{indent}{{')
    high,low = 0,0
    if useConfig:
        out.append(f"{indent}uint16_t _pos{{0}};")
    indent += ' '*4
    posUpdate = None
    for _, data in reversed(vars['vars'].items()):
        varName = data['variable']
        varType = cppTypeName(data, prj, useConfig) if prj else (data['varType'] if data['entryType'] != 'NamedStruct' else data['subStruct'])
        varIndex = ''
        high = low + data['arraywidth'] - 1
        if data['generator'] == 'datapath':
            num_bytes = int(data['bitwidth'] / 8)
            out.append(f'{indent}for(unsigned int bsl=0; bsl<{num_bytes}; bsl++) {{')
            rng_high, rng_low  = f"{low}+bsl*8+7", f"{low}+bsl*8"
            indent += ' '*4
            out.append(f'{indent}{varName}[bsl] = (uint8_t) packed_data.range({rng_high}, {rng_low}).to_uint64();')
            indent = indent[:-4]
            out.append(f"{indent}}}")
        else:
            if data['isArray']:
                varIndex = f"[i]"
                arraySizeExpr = cppArraySize(data, prj, useConfig) if prj else data['arraySize']
                widthExpr = cppVarBitwidth(data, prj, useConfig) if prj else data['bitwidth']
                out.append(f"{indent}for(unsigned int i=0; i<{arraySizeExpr}; i++) {{")
                if useConfig:
                    rng_high, rng_low  = f"_pos+{widthExpr}-1", "_pos"
                    posUpdate = f"_pos += {widthExpr};"
                else:
                    rng_high, rng_low  = f"{low}+(i+1)*{widthExpr}-1", f"{low}+i*{widthExpr}"
                indent += ' '*4
            else:
                if useConfig:
                    widthExpr = cppVarBitwidth(data, prj, useConfig) if prj else data['bitwidth']
                    rng_high, rng_low  = f"_pos+{widthExpr}-1", "_pos"
                    posUpdate = f"_pos += {widthExpr};"
                else:
                    rng_high, rng_low  = f"{high}", f"{low}"
            if data['entryType'] == 'NamedVar' or data['entryType'] == 'NamedType' or data['entryType'] == 'Reserved':
                if structType != 'bool':
                    if data['bitwidth'] >= 64 and data['entryType'] != 'NamedStruct' and data['varLoopCount'] > 1 and useConfig:
                        widthExpr = cppVarBitwidth(data, prj, useConfig) if prj else data['bitwidth']
                        # Zero the destination first: a Config whose width is an
                        # exact multiple of 64 skips the guarded write of the
                        # top word(s), so any preexisting garbage there would
                        # survive. unpack() memsets for the same reason.
                        out.append(f'{indent}memset((uint64_t *)&{varName}{varIndex}, 0, sizeof({varName}{varIndex}));')
                        for wix in range(data['varLoopCount']):
                            out.append(f'{indent}if ({widthExpr} > {wix * 64}) {{')
                            out.append(f'{indent}    uint16_t _bits = std::min((uint16_t)64, (uint16_t)({widthExpr} - {wix * 64}));')
                            out.append(f'{indent}    {varName}{varIndex}.word[{wix}] = (uint64_t) packed_data.range(_pos + {wix * 64} + _bits - 1, _pos + {wix * 64}).to_uint64();')
                            out.append(f'{indent}}}')
                    elif data['bitwidth'] >= 64 and data['entryType'] != 'NamedStruct' and data['varLoopCount'] > 1:
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
                            out.append(f'{indent}{varName}{varIndex}.word[{wix}] = ({varType}) packed_data.range({rng_high}, {rng_low}).to_uint64();')
                    else:
                        out.append(f'{indent}{varName}{varIndex} = ({varType}) packed_data.range({rng_high}, {rng_low}).to_uint64();')
                        # Add sign extension for signed types
                        isSigned = data['isSigned']
                        widthExpr = cppVarBitwidth(data, prj, useConfig) if prj else data['bitwidth']
                        out.extend(get_sign_extension_code(varName, varIndex, varType, widthExpr, indent, isSigned))
                else :
                    out.append(f'{indent}{varName}{varIndex} = ({varType}) packed_data;')
            elif data['entryType'] == 'NamedStruct':
                out.append(f'{indent}{varName}{varIndex}.sc_unpack(packed_data.range({rng_high}, {rng_low}));')
            else :
                assert(False)
            if data['isArray']:
                if useConfig and posUpdate:
                    out.append(f"{indent}{posUpdate}")
                    posUpdate = None
                indent = indent[:-4]
                out.append(f"{indent}}}")
            elif useConfig:
                out.append(f"{indent}_pos += {widthExpr};")

        low = high + 1
    indent = indent[:-4]
    out.append(f'{indent}}}')
    return out

    # constructor
def constuctor_bv(structName, vars, indent):
    out = list()
    qualifiedStructName = f"{structName}<Config>" if vars['isParameterizable'] else structName
    if vars['width'] > 1:
        structType = f"sc_bv<{qualifiedStructName}::_bitWidth>"
    else:
        structType = 'bool'
    out.append(f"{indent}explicit {structName}({structType} packed_data) {{ sc_unpack(packed_data); }}")
    return out

def constructor(structName, vars, indent, prj=None, useConfig=False):
    out = list()
    indent = ' '*4
    out.append(f"{indent}explicit {structName}(")
    indent = ' '*8
    params = list()
    initializers = list()
    memcpys = list()
    for var, vardata in reversed(vars["vars"].items()):
        if vardata['isArray']:
            myArray= f"[{cppArraySize(vardata, prj, useConfig) if prj else vardata['arraySize']}]"
            myArrayLoopIndex= '[i]'
        else:
            myArray= ''
            myArrayLoopIndex= ''
        if vardata['entryType'] == 'NamedVar' or vardata['entryType'] == 'NamedType' or vardata['entryType'] == 'Reserved':
            varType = cppTypeName(vardata, prj, useConfig) if prj else vardata['varType']
            params.append(f"{indent}{varType} {vardata['variable'] + '_' + myArray},")
        elif vardata['entryType'] == 'NamedStruct':
            varType = cppTypeName(vardata, prj, useConfig) if prj else vardata['subStruct']
            params.append(f"{indent}{varType} {vardata['variable'] + '_' + myArray},")
        if myArray == '':
            initializers.append(f"{indent}{vardata['variable']}({vardata['variable'] + '_'}),")
        else:
            memcpys.append(f"{indent}memcpy(&{vardata['variable']}, &{vardata['variable'] + '_'}, sizeof({vardata['variable']}));")

    if len(initializers) > 0:
        params[-1] = params[-1].replace(',', ') :')
    else:
        params[-1] = params[-1].replace(',', ')')
    out.extend(params)
    if len(initializers) > 0:
        initializers[-1] = initializers[-1].replace(',', '')
        out.extend(initializers)
    indent = ' '*4
    if len(memcpys) > 0:
        out.append(f"{indent}{{")
        out.extend(memcpys)
        out.append(f"{indent}}}")
    else:
        out.append(f"{indent}{{}}")

    return out

def constructor_packed(structName, vars, indent):
    out = list()
    out.append(f"{indent}explicit {structName}(const _packedSt &packed_data) {{ unpack(const_cast<_packedSt&>(packed_data)); }}")
    return out

def get_unpack_mask_str(needBits, baseSize):
    if not isinstance(needBits, int):
        return cppWidthMask(needBits)
    mask = ''
    # truncate the mask to the needed bits case
    if (needBits < baseSize):
        mask = f" & ((1ULL << {needBits}) - 1)"
    if (baseSize == 1 or needBits == 1):
        mask = ' & 1'
    return mask

def get_sign_extension_code(varName, varIndex, varType, bitwidth, indent, isSigned):
    """Generate sign extension code for signed types"""
    out = []
    if isSigned and (not isinstance(bitwidth, int) or bitwidth < 64):
        # Need to perform sign extension if the sign bit is set
        out.append(f"{indent}// Sign extension for signed type")
        out.append(f"{indent}if ({varName}{varIndex} & (1ULL << ({bitwidth} - 1))) {{")
        out.append(f"{indent}    {varName}{varIndex} = ({varType})({varName}{varIndex} | ~((1ULL << ({bitwidth})) - 1));")
        out.append(f"{indent}}}")
    return out

def processPackRet(structName, value, indent):
    out = list()
    out.append(f"{indent}inline _packedSt pack(void) const")
    out.append(f"{indent}{{")
    out.append(f"{indent}    _packedSt ret;")
    out.append(f"{indent}    pack(ret);")
    out.append(f"{indent}    return ret;")
    out.append(f"{indent}}}")
    return out


def fw_unpack(handle, args, vars, indent, prj=None, useConfig=False):
    out = list()
    global dataTypeMappings
    # figure out return type
    bitwidth = vars['maxBitwidth'] if useConfig else vars['width']
    paramType, rowType, baseSize = convertToType(bitwidth)
    if useConfig:
        baseSize = 64
    if args.section == 'header' and handle == 'inline':
        out.append(f"{indent}inline void unpack(const _packedSt &_src)")
    elif args.section == 'header' and handle == 'split':
        out.append(f"{indent}void unpack(const _packedSt &_src);")
        return out
    elif args.section == 'cpp' and handle == 'split':
        decl = f"{args.namespace}::" if args.namespace else ''
        out.append(f"{indent}void {decl}{vars['structure']}::unpack(const _packedSt &_src)")
    else:
        return out
    out.append(f'{indent}{{')
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
        out.append(f"{indent}uint16_t _pos{{0}};")
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
        varType = cppTypeName(data, prj, useConfig) if prj else (data['varType'] if data['entryType'] != 'NamedStruct' else data['subStruct'])
        bitwidthExpr = cppVarBitwidth(data, prj, useConfig) if prj else data['bitwidth']
        calcAlign = False  # does code need to calc alignment
        # for array case, create an outer loop
        if data['isArray']:
            varIndex = f"[i]"
            arraySizeExpr = cppArraySize(data, prj, useConfig) if prj else data['arraySize']
            out.append(f"{indent}for(unsigned int i=0; i<{arraySizeExpr}; i++) {{")
            indent += ' '*4
            calcAlign = (not isSingleArray) or usePos
            bitsLeft = data['bitwidth']
            out.append(f"{indent}uint16_t _bits = {bitwidthExpr};")
            out.append(f"{indent}uint16_t _consume;")
        if data['entryType'] == 'NamedVar' or data['entryType'] == 'NamedType' or data['entryType'] == 'Reserved':
            if data['bitwidth'] >= 64 and data['entryType'] != 'NamedStruct' and data['varLoopCount'] > 1 and useConfig:
                # Templated array-backed field. Zero the destination so the
                # subsequent OR-based copy lands cleanly, and use unpack_bits
                # (masking variant of pack_bits) so adjacent packed-form
                # fields' bits cannot propagate into this field's storage.
                # See common/systemc/bitTwiddling.h for the pack_bits /
                # unpack_bits contract.
                out.append(f'{indent}memset((uint64_t *)&{varName}{varIndex}, 0, sizeof({varName}{varIndex}));')
                out.append(f'{indent}unpack_bits((uint64_t *)&{varName}{varIndex}, 0, (uint64_t *)&_src, _pos, {bitwidthExpr});')
                out.append(f'{indent}_pos += {bitwidthExpr};') if usePos else None
            elif data['bitwidth'] >= 64 and data['entryType'] != 'NamedStruct' and data['varLoopCount'] > 1:
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
                        out.append(f"{indent}_consume = std::min(_bits, (uint16_t)({baseSize}-(_pos & {baseMask})));")
                    consumeBits = min(loop_bits_left, baseSize - (loop_current % baseSize))
                    srcMask = get_unpack_mask_str(loop_bits_left, baseSize)
                    loop_next = loop_current + actual_bits
                    out.append(f'{indent}{varName}{varIndex}.word[{wix}] = (({src}{offsetShift}){srcMask});')
                    if (calcAlign):
                        out.append(f'{indent}_pos += _consume;') if usePos else None
                    else:
                        out.append(f'{indent}_pos += {consumeBits};') if usePos else None
                    loop_bits_left -= consumeBits
                    # if the source is a pointer and we consumed the whole word, increment the pointer
                    if (calcAlign):
                        out.append(f"{indent}_bits -= _consume;")
                        out.append(f"{indent}if ((_bits > 0) && (_consume != {baseSize})) {{")
                        out.append(f'{indent}    {varName}{varIndex}.word[{wix}] = {varName}{varIndex}.word[{wix}] | (({src} << _consume){srcMask});')
                        out.append(f'{indent}    _pos += {actual_bits} - _consume;') if usePos else None
                        out.append(f"{indent}}}")
                    elif (loop_bits_left >0 and consumeBits != baseSize):
                        out.append(f'{indent}{varName}{varIndex}.word[{wix}] = {varName}{varIndex}.word[{wix}] | (({src} << {consumeBits}){srcMask});')
                        out.append(f'{indent}_pos += {actual_bits-consumeBits};') if usePos else None
                    loop_current = loop_next

            else:
                srcMask = ''
                if (calcAlign):
                    out.append(f"{indent}_consume = std::min(_bits, (uint16_t)({baseSize}-(_pos & {baseMask})));")
                consumeBits = min(bitsLeft, baseSize - (currentPos % baseSize))
                srcMask = get_unpack_mask_str(bitwidthExpr if useConfig else bitsLeft, baseSize)
                out.append(f'{indent}{varName}{varIndex} = ({varType})(({src}{offsetShift}){srcMask});')
                bitsLeft -= consumeBits
                if (calcAlign):
                    out.append(f'{indent}_pos += _consume;') if usePos else None
                else:
                    posAdvance = bitwidthExpr if useConfig else consumeBits
                    out.append(f'{indent}_pos += {posAdvance};') if usePos else None
                if (calcAlign):
                    out.append(f"{indent}_bits -= _consume;")
                    out.append(f"{indent}if ((_bits > 0) && (_consume != {baseSize})) {{")
                    out.append(f'{indent}    {varName}{varIndex} = ({varType})({varName}{varIndex} | (({src} << _consume){srcMask}));')
                    out.append(f'{indent}    _pos += _bits;') if usePos else None
                    out.append(f"{indent}}}")
                elif (not useConfig and bitsLeft >0 and consumeBits != baseSize):
                    out.append(f'{indent}{varName}{varIndex} = ({varType})({varName}{varIndex} | (({src} << {consumeBits}){srcMask}));')
                    out.append(f'{indent}_pos += {bitsLeft};') if usePos else None
                # Add sign extension for signed types
                isSigned = data['isSigned']
                out.extend(get_sign_extension_code(varName, varIndex, varType, bitwidthExpr, indent, isSigned))
        elif data['entryType'] == 'NamedStruct':
            # nested structure, declare a tmp variable to hold the value and copy it to the destination
            tmpType, tmpRowType, tmpBaseSize = convertToType(data['arraywidth'])
            loop_current = currentPos
            # parameterized (templated) sub-struct types like rgb_pixel_t<Config>
            # make ::_packedSt a dependent type, which requires the typename keyword
            packedSt = packedStType(varType)
            # we are aligned if the current position is a multiple of the base size
            # except for the array case, unless the array case is the single element array case)
            isAligned = ((currentPos & (baseMask)) == 0) and not (data['isArray'] and not isSingleArray)
            out.append(f'{indent}{{')
            indent += ' '*4
            if (isAligned):
                out.append(f'{indent}{varName}{varIndex}.unpack(*({packedSt}*)&{src});')
            else:
                # cases include whether src or dst is >=64 bits
                # if tmp is <= 32 bit we want to use a 64 bit temp to prevent alignment issues and cast for the unpack
                if data['bitwidth'] <= 32:
                    out.append(f"{indent}uint64_t _tmp{{0}};")
                    unpackCast = f"*(({packedSt}*)&_tmp)"
                else:
                    out.append(f"{indent}{packedSt} _tmp{{0}};")
                    unpackCast = f"_tmp"
                if (bitwidth >= 64):
                    # src is using 64 bit words so use pass by pointer.
                    # _tmp is value-initialised above (line ~1166), so the
                    # "dest is clean" half of the unpack_bits contract is
                    # already satisfied; this rename only adds the source
                    # mask so adjacent parent-struct fields' bits do not
                    # leak into the nested struct's _tmp staging area.
                    out.append(f"{indent}unpack_bits((uint64_t *)&_tmp, 0, (uint64_t *)&_src, _pos, {bitwidthExpr});")
                else:
                    # src is using < 64 bit so we can just use bit shifting
                    out.append(f"{indent}_tmp = (_src >> _pos) & ((1ULL << ({bitwidthExpr})) - 1);")
                out.append(f'{indent}{varName}{varIndex}.unpack({unpackCast});')
                # when we copied we used a tmp ptr to prevent overrun, reset point to correct place
            indent = indent[:-4]
            out.append(f'{indent}}}')
            out.append(f'{indent}_pos += {bitwidthExpr};') if usePos else None
        else:
            assert(0)
        if data['isArray']:
            indent = indent[:-4]
            out.append(f"{indent}}}")
        currentPos = nextPos
    # if the last statement was an increment its dead code - delete it
    if out[-1].strip().startswith('_pos +='):
        out.pop()
    indent = indent[:-4]
    out.append(f'{indent}}}')

    return out

def fw_pack_setup(args, vars, indent):
    out = list()
    fw_pack_vars = dict()
    useConfig = vars['isParameterizable']
    bitwidth = vars['maxBitwidth'] if useConfig else vars['width']
    structName = f"{vars['structure']}<Config>" if useConfig else vars['structure']
    out.append(f"{indent}memset(&_ret, 0, {structName}::_byteWidth);")
    retType, rowType, baseSize = convertToType(bitwidth)
    if useConfig:
        rowType = 'uint64_t'
        baseSize = 64
    fw_pack_vars['bitwidth'] = bitwidth
    fw_pack_vars['retType'] = retType
    fw_pack_vars['rowType'] = rowType
    fw_pack_vars['baseSize'] = baseSize
    fw_pack_vars['cast'] = '(' + rowType + ')'
    fw_pack_vars['log2BaseSize'] = (baseSize-1).bit_length()
    return out, fw_pack_vars

def fw_pack_oneVar(fw_pack_vars, pos, args, data, indent):
    out = list()
    prj = fw_pack_vars['prj']
    useConfig = fw_pack_vars['useConfig']
    bitwidthExpr = cppVarBitwidth(data, prj, useConfig) if prj else data['bitwidth']
    isArray = data['isArray']
    if fw_pack_vars['bitwidth'] > 64:
        ret = f"_ret[ {pos >> fw_pack_vars['log2BaseSize']} ]"
    else:
        ret = "_ret"
    if useConfig and not isArray:
        ret = "_ret[ _pos >> 6 ]" if fw_pack_vars['bitwidth'] > 64 else "_ret"
    isSigned = data['isSigned']
    baseMask = fw_pack_vars['baseSize'] - 1
    if isArray:
        srcPos = '_pos'
        incPos = f"_pos += {bitwidthExpr};"
        arrayIndex = "[i]"
    elif useConfig:
        srcPos = '_pos'
        incPos = f"_pos += {bitwidthExpr};"
        arrayIndex = ''
    else:
        srcPos = pos
        incPos = None
        arrayIndex = ''
    # Generate mask for signed types to strip sign-extended bits after cast to uint64_t
    # For unsigned types, the cast naturally zero-extends so no mask is needed
    if isSigned and (useConfig or data['bitwidth'] < 64):
        valueMask = cppWidthMask(bitwidthExpr)
    else:
        valueMask = ""
    fitsDirect = (pos + data['arraywidth'] <= 64 and not isArray and not useConfig)
    if fitsDirect:
        if useConfig:
            out.append(f"{indent}{ret} |= {fw_pack_vars['cast']}{data['variable']}{arrayIndex}{valueMask} << ({srcPos} & {baseMask});")
        elif pos==0:
            out.append(f"{indent}{ret} = {data['variable']}{valueMask};")
        else:
            if valueMask:
                out.append(f"{indent}{ret} |= ({fw_pack_vars['cast']}({data['variable']}{arrayIndex}{valueMask})) << ({srcPos} & {baseMask});")
            else:
                out.append(f"{indent}{ret} |= {fw_pack_vars['cast']}{data['variable']}{arrayIndex} << ({srcPos} & {baseMask});")
    else:
        if data['bitwidth'] <= 64:
            if data['bitwidth'] == 1 and not isArray and not useConfig:
                out.append(f"{indent}{ret} |= ({fw_pack_vars['cast']}{data['variable']} << ({srcPos} & {baseMask}));")
            else:
                # use pass by value - mask for signed types to strip sign-extended bits
                out.append(f"{indent}pack_bits((uint64_t *)&_ret, {srcPos}, {data['variable']}{arrayIndex}{valueMask}, {bitwidthExpr});")
        else:
            # use pass by reference
            out.append(f'{indent}pack_bits((uint64_t *)&_ret, {srcPos}, (uint64_t *)&{data["variable"]}{arrayIndex}, {bitwidthExpr});')
    out.append(f'{indent}{incPos}') if incPos else None
    return out

def fw_pack_oneNamedStruct(fw_pack_vars, pos, args, data, indent):
    out = list()
    prj = fw_pack_vars['prj']
    useConfig = fw_pack_vars['useConfig']
    bitwidthExpr = cppVarBitwidth(data, prj, useConfig) if prj else data['bitwidth']
    # nested structure, declare a tmp variable to hold the value and copy it to the destination
    tmpType, tmpRowType, tmpBaseSize = convertToType(data['bitwidth'])
    baseSize = fw_pack_vars['baseSize']
    baseMask = baseSize - 1
    isArray = data['isArray']
    isAligned = ((pos & (baseMask)) == 0) and (not isArray or ((data['arraywidth'] & baseMask == 0) and (data['bitwidth'] & baseMask == 0)))

    if isArray:
        srcPos = '_pos'
        incPos = f"_pos += {bitwidthExpr};"
    elif useConfig:
        srcPos = '_pos'
        incPos = f"_pos += {bitwidthExpr};"
    else:
        srcPos = pos
        incPos = None
    if isAligned:
        # for aligned data we can go straight to the destination
        if data['arraywidth'] > 64:
            log2BaseSize = baseMask.bit_length()
            if isArray:
                dest = f"_ret[ _pos >> {log2BaseSize} ]"
            elif useConfig:
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

    varType = cppTypeName(data, prj, useConfig) if prj else data['subStruct']
    varName = data['variable']
    # parameterized (templated) sub-struct types like rgb_pixel_t<Config>
    # make ::_packedSt a dependent type, which requires the typename keyword
    packedSt = packedStType(varType)

    if isArray:
        varIndex = "[i]"
        blockClose = None
    else:
        varIndex = ''
        out.append(f'{indent}{{') #indent block to contain vars
        blockClose = f'{indent}}}'
        indent += ' '*4

    if (isAligned):
        # for aligned data we can go straight to the destination
        out.append(f'{indent}{varName}{varIndex}.pack(*({packedSt}*)&{dest});')
    else:
        # unaligned cases got through tmp value
        out.append(f"{indent}{packedSt} _tmp{{0}};")
        out.append(f'{indent}{varName}{varIndex}.pack(_tmp);')
        if pos + data['arraywidth'] <= 64 and fw_pack_vars['bitwidth'] <= 64:
            out.append(f"{indent}_ret |= {fw_pack_vars['cast']}_tmp << ({srcPos} & {baseMask});")
        else:
            out.append(f'{indent}pack_bits((uint64_t *)&_ret, {srcPos}, {tmp}, {bitwidthExpr});')
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
            'header_inline': 'inline void pack(_packedSt &_ret) const',
            'header_split': 'void pack(_packedSt &_ret) const;',
            'cpp_split': "void {decl}{structure}::pack(_packedSt &_ret) const",
        },
        'posDeclare' : 'uint16_t _pos{{{}}};',
        'posCorrection' : '_pos = {};'
    },
    'fw_unpack': None,

}

def processPackUnpack(fname, handle, args, vars, indent, prj=None, useConfig=False):
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
    out.append(f'{indent}{{')
    indent += ' '*4

    # perform any setup
    setupFn = p['functions'].get('setup', None)
    setupOut, setupVars = setupFn(args, vars, indent) if setupFn else ([], {})
    setupVars['prj'] = prj
    setupVars['useConfig'] = useConfig
    out.extend(setupOut)
    posDeclare = p.get('posDeclare', None)
    posCorrection = p.get('posCorrection', None)
    if useConfig and posDeclare:
        out.append(indent + posDeclare.format(0))
        posDeclare = None

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
            arraySizeExpr = cppArraySize(data, prj, useConfig) if prj else data['arraySize']
            out.append(f"{indent}for(unsigned int i=0; i<{arraySizeExpr}; i++) {{")
            loopClose = f"{indent}}}"
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
    out.append(f'{indent}}}')
    return out


def structContainsSignedTypes(structValue, prj, data):
    """Check if a structure contains any signed type fields"""
    for varKey, varData in structValue['vars'].items():
        if varData['entryType'] == 'NamedVar' or varData['entryType'] == 'NamedType':
            # Check if the type is signed
            if prj.data['types'][varData['varTypeKey']]['isSigned']:
                return True
        elif varData['entryType'] == 'NamedStruct':
            # Recursively check nested structures
            nestedStruct = prj.data['structures'][varData['subStructKey']]
            if structContainsSignedTypes(nestedStruct, prj, data):
                return True
    return False

def _roundTripHelperLines(indent):
    """The struct round-trip body, parameterized over the struct type T and a
    runtime struct-name string. Emitted once per context (Option C) so test()
    is a deterministic list of calls rather than inlined-per-struct bodies."""
    out = list()
    out.append(f'{indent}template<typename T>')
    out.append(f'{indent}static void roundTrip(const char* sName, const std::vector<uint8_t>& patterns) {{')
    indent += ' '*4
    out.append(f'{indent}for(auto pattern : patterns) {{')
    indent += ' '*4
    out.append(f'{indent}typename T::_packedSt packed;')
    out.append(f'{indent}memset(&packed, pattern, T::_byteWidth);')
    out.append(f'{indent}sc_bv<T::_bitWidth> aInit;')
    out.append(f'{indent}sc_bv<T::_bitWidth> aTest;')
    out.append(f'{indent}for (int i = 0; i < T::_byteWidth; i++) {{')
    out.append(f'{indent}    int end = std::min((i+1)*8-1, T::_bitWidth-1);')
    out.append(f'{indent}    aInit.range(end, i*8) = pattern;')
    out.append(f'{indent}}}')
    out.append(f'{indent}T a;')
    out.append(f'{indent}a.sc_unpack(aInit);')
    out.append(f'{indent}T b;')
    out.append(f'{indent}b.unpack(packed);')
    out.append(f'{indent}if (!(b == a)) {{;')
    out.append(f'{indent}    cout << a.prt();')
    out.append(f'{indent}    cout << b.prt();')
    out.append(f'{indent}    Q_ASSERT(false, sName);')
    out.append(f'{indent}}}')
    out.append(f'{indent}uint64_t test;')
    out.append(f'{indent}memset(&test, pattern, 8);')
    out.append(f'{indent}b.pack(packed);')
    out.append(f'{indent}aTest = a.sc_pack();')
    out.append(f'{indent}if (!(aTest == aInit)) {{;')
    out.append(f'{indent}    cout << a.prt();')
    out.append(f'{indent}    cout << aTest;')
    out.append(f'{indent}    Q_ASSERT(false, sName);')
    out.append(f'{indent}}}')
    out.append(f'{indent}uint64_t *ptr = (uint64_t *)&packed;')
    out.append(f'{indent}uint16_t bitsLeft = T::_bitWidth;')
    out.append(f'{indent}do {{')
    out.append(f'{indent}    int bits = std::min((uint16_t)64, bitsLeft);')
    out.append(f'{indent}    uint64_t mask = (bits == 64) ? -1 : ((1ULL << bits)-1);')
    out.append(f'{indent}    if ((*ptr & mask) != (test & mask)) {{;')
    out.append(f'{indent}        cout << a.prt();')
    out.append(f'{indent}        cout << b.prt();')
    out.append(f'{indent}        Q_ASSERT(false, sName);')
    out.append(f'{indent}    }}')
    out.append(f'{indent}    bitsLeft -= bits;')
    out.append(f'{indent}    ptr++;')
    out.append(f'{indent}}} while(bitsLeft > 0);')
    indent = indent[:-4]
    out.append(f'{indent}}}')
    indent = indent[:-4]
    out.append(f'{indent}}}')
    return out


def _sampleConfigs(prj, data):
    """Deterministic Default/Mid/Max sample points for a context's base
    parameterizable constants. Sample points are variant-independent: every
    point is derived ONLY from the ipParameter declaration (its `value` and
    `maxValue`), never from variant-bound Config values. Default = declared
    value, Max = declared maxValue, Mid = maxValue // 2 (integer floor). Each
    sample is a (Role, configName, baseValues) triple; identical value-dicts are
    de-duplicated keeping first occurrence so a degenerate param does not emit
    redundant Configs. baseValues carries only base (non-eval) parameterizable
    constants; eval-derived members recompute symbolically inside the Config
    struct."""
    baseParams = [v for v in data['constants'].values()
                  if v['isParameterizable'] and not v['evalCanonical']]
    if not baseParams:
        return []
    defaultVals = {v['constant']: v['value'] for v in baseParams}
    maxVals = {v['constant']: v['maxValue'] for v in baseParams}
    # Mid is clamped to a minimum of 1 so maxValue == 1 cannot yield a 0 base
    # value (which would emit a zero-width type / zero-size array). When the
    # clamp hits, Mid == Max and the dedup below collapses it.
    midVals = {v['constant']: max(1, v['maxValue'] // 2) for v in baseParams}
    stem = data['contextStem'].replace('-', '_')
    ordered = [('Default', defaultVals), ('Mid', midVals), ('Max', maxVals)]
    samples = list()
    seen = list()
    for role, vals in ordered:
        if vals in seen:
            continue
        seen.append(vals)
        samples.append((role, f'{stem}TestConfig{role}', vals))
    return samples


def structTest(args, prj, data):
    from templates.systemc import config
    out = list()
    fn = data['contextStem'] + '_structs'
    useConfig = args.mode == 'module'
    if args.section == 'testStructsHeader':
        # The class is always non-templated (Option C): test() instantiates
        # concrete sample-point Configs internally, so callers invoke
        # test_<ctx>_structs::test() without supplying a Config.
        out.append(f'class test_{fn} {{')
        out.append(f'public:')
        out.append(f'    static std::string name(void);')
        out.append(f'    static void test(void);')
        out.append(f'private:')
        out.extend(_roundTripHelperLines(' '*4))
        out.append(f'}};')
        return out

    if not useConfig:
        out.append(f'#include "q_assert.h"')
    else:
        # The test lives in the sibling test namespace; pull the functional
        # types into scope so struct names resolve unqualified.
        out.append(f'using namespace {cpp_namespace_name(data["contextModuleIdentity"])};')

    # Sample-point Config structs for the parameterizable structs. Only emitted
    # in module mode (no Config in a non-module TU).
    samples = _sampleConfigs(prj, data) if useConfig else []
    for _, configName, baseValues in samples:
        out.extend(config.configStructLines(prj, data, configName, baseValues))

    out.append(f'std::string test_{fn}::name(void) {{ return "test_{fn}"; }}')
    out.append(f'void test_{fn}::test(void) {{')
    indent = ' '*4
    out.append(f'{indent}std::vector<uint8_t> patterns{{0x6a, 0xa6}};')
    out.append(f'{indent}std::vector<uint8_t> signedPatterns{{0x00, 0x6a, 0xa6, 0x77, 0x88, 0x55, 0xAA, 0xFF}};')
    out.append(f'{indent}cout << "Running " << name() << endl;')
    # Deterministic call list in struct declaration order. Concrete structs emit
    # one call; parameterizable structs emit one call per de-duplicated sample
    # point at the fixed Config names.
    for _, value in data['structures'].items():
        isParam = value['isParameterizable']
        if isParam and not useConfig:
            continue
        struct = value['structure']
        patternVar = 'signedPatterns' if structContainsSignedTypes(value, prj, data) else 'patterns'
        if isParam:
            for _, configName, _ in samples:
                out.append(f'{indent}roundTrip<{struct}<{configName}>>("{struct}", {patternVar});')
        else:
            out.append(f'{indent}roundTrip<{struct}>("{struct}", {patternVar});')
    out.append(f'}}')
    return out
