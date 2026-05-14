from pysrc.intf_gen_utils import wrap_module_namespace

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    match args.section:
        case 'constants':
            return(includeConstants(args, prj, data))
        case 'types':
            return(includeTypes(args, prj, data))
        case 'enums':
            return(includeEnum(args, prj, data))
        case 'addresses':
            return(includeAddresses(args, prj, data))
        case 'regAddresses':
            return(includeRegAddresses(args, prj, data))
        case 'config':
            return(includeConfig(args, prj, data))
        case _:
            print("error missing section, valid values are constants, types, enums")
            exit()


def includeConstants(args, prj, data):
    out = list()
    out.append("//constants")

    for const, value in data['constants'].items():
        if value.get('isParameterizable', False):
            continue
        match value['valueType']:
            case 'uint':
                if value['value'] <= 0xFFFFFFFF:
                    type_str = 'uint32_t'
                    value_str = f"{value['value']}"
                else:
                    type_str = 'uint64_t'
                    value_str = f"{hex(value['value']).upper()}UL"
            case 'int':
                if abs(value['value']) <= 0x7FFFFFFF:
                    type_str = 'int32_t'
                    value_str = f"{value['value']}"
                else:
                    type_str = 'int64_t'
                    value_str = f"{hex(value['value']).upper()}L"
            case 'real':
                type_str = 'double'
                value_str = f"{value['value']}"
            case _:
                type_str = value['valueType']
                value_str = f"{value['value']}"
        out.append(f"const {type_str} { value['constant'] } = { value_str };  // {value['desc'].strip()}")

    out.append("")
    return("\n".join(wrap_module_namespace(args, data, out)))


def constReference_cpp(constKey, prj, useConfig=False):
    constName = prj.data['constants'][constKey]['constant']
    if useConfig and prj.data['constants'][constKey].get('isParameterizable', False):
        return f"Config::{constName}"
    return constName


def typeWidthExpression_cpp(value, prj, useConfig=False):
    """Build a C++ constexpr-compatible expression for a type's bit width.

    For widthLog2 with constant C:       clog2(C+1)
    For widthLog2minus1 with constant C: clog2(C)
    For width with constant C:           C
    For literal integer N:               N
    If isSigned + log2: appends +1

    Returns: string expression suitable for use in constexpr calculations.
    # TODO: handle variable size parameters (parameterized widths)
    """
    isSigned = value['isSigned']
    signedExtra = '+1' if isSigned else ''

    # Check widthLog2
    wl2Key = value['widthLog2Key']
    if wl2Key:
        constName = constReference_cpp(wl2Key, prj, useConfig)
        return f"clog2({constName}+1){signedExtra}"
    wl2 = value['widthLog2']
    if wl2 != '':
        return f"clog2({wl2}+1){signedExtra}"

    # Check widthLog2minus1
    wl2m1Key = value['widthLog2minus1Key']
    if wl2m1Key:
        constName = constReference_cpp(wl2m1Key, prj, useConfig)
        return f"clog2({constName}){signedExtra}"
    wl2m1 = value['widthLog2minus1']
    if wl2m1 != '':
        return f"clog2({wl2m1}){signedExtra}"

    # Direct width — check widthKey for constant, else literal
    widthKey = value['widthKey']
    if widthKey:
        return constReference_cpp(widthKey, prj, useConfig)
    return str(prj.resolveTypeWidth(value))


def includeTypes(args, prj, data):
    out = list()

    out.append("// types")
    for type, value in data['types'].items():
        # Comments show resolved integer bit width, not symbolic expression
        widthComment = str(value['realwidth'])
        if value.get('isParameterizable', False):
            if value['maxBitwidth'] <= 64:
                out.append(
                    f"template<typename Config> using { value['type'] } = uint64_t; // [max:{value['maxBitwidth']}] {value['desc']}"
                )
            else:
                typeArraySize = (value['maxBitwidth'] + 63) // 64
                out.append(
                    f"template<typename Config> struct { value['type'] } {{ uint64_t word[ {typeArraySize} ]; }}; // [max:{value['maxBitwidth']}] {value['desc']}"
                )
            continue
        if value['typeArraySize'] == 1:
            out.append(
                f"typedef { value['platformDataType'] } { value['type'] }; // [{widthComment}] {value['desc']}"
            )
        else:
            out.append(
                f"struct { value['type'] } {{ { value['platformDataType'] } word[ {value['typeArraySize']} ]; }}; // [{widthComment}] {value['desc']}"
            )

    out.append("")
    return("\n".join(wrap_module_namespace(args, data, out)))


def includeConfig(args, prj, data):
    out = []
    params = [value for value in data['constants'].values() if value.get('isParameterizable', False)]
    # Stage 4.3 of plan-variant-config-unification.md: pure block params
    # (declared via `params:` with no backing constant — the
    # IP_NONCONST_DEPTH pattern) also surface as Config fields. Discover
    # them via the descriptor lists for blocks whose primary context
    # matches this file. Their value type is uint32_t — wide enough for
    # any wordLines / depth-style block param under the project's worst-
    # case variant — and inferred lazily from descriptor.values rather
    # than from `data['constants']`.
    context = data.get('context', '')
    constants_by_name = {p['constant']: p for p in params}
    block_param_synthetic = dict()
    for qualBlock, blockRow in prj.data['blocks'].items():
        if blockRow.get('_context', '') != context:
            continue
        for param_row in blockRow.get('params', []) or []:
            name = param_row.get('param')
            if not name or name in constants_by_name or name in block_param_synthetic:
                continue
            block_param_synthetic[name] = {'valueType': 'uint'}
    if not params and not block_param_synthetic:
        return ""
    # Legacy per-context Config struct. Retained during the Stage 1.1
    # transition for blocks that still ride on <context>DefaultConfig
    # (those without their own variants but parameterizable transitively).
    # Pure block params (block_param_synthetic) are intentionally NOT
    # emitted here: there is no constant default, so any caller reading
    # them through the legacy default fallback is a usage bug. Per-variant
    # Config structs (below) carry the override values.
    configName = data.get('configName', '')
    if not configName:
        configName = data['context'].rsplit('/', 1)[-1].rsplit('.', 1)[0].replace('-', '_') + 'DefaultConfig'
    out.append(f"struct {configName} {{")
    for value in params:
        type_str = _config_type(value)
        out.append(f"    static constexpr {type_str} {value['constant']} = {value['value']};")
    out.append("};")
    out.append("")
    # Per-variant Config structs for any parameterizable block whose primary
    # context matches this file's context. Variant labels and resolved values
    # come from prj.getBlockConfigView()['variantConfigs']; intra-block dedup
    # folds byte-identical variants onto a single canonical struct.
    seen_struct_names = set()
    for qualBlock, blockRow in prj.data['blocks'].items():
        if blockRow.get('_context', '') != context:
            continue
        descriptors = prj.getBlockConfigView(qualBlock)['variantConfigs']
        for desc in descriptors:
            if desc['duplicateOf'] is not None:
                continue
            if not desc['values']:
                continue
            structName = desc['configName']
            if structName in seen_struct_names:
                continue
            seen_struct_names.add(structName)
            out.append(f"struct {structName} {{")
            for constName, resolved in desc['values'].items():
                if constName in constants_by_name:
                    constData = constants_by_name[constName]
                else:
                    # Stage 4.3 synthetic block-param entry. Treated as an
                    # unsigned 32-bit field; the variant override is the
                    # value source.
                    constData = block_param_synthetic.get(constName, {'valueType': 'uint'})
                    constData = dict(constData, value=resolved)
                type_str = _config_type(constData)
                out.append(f"    static constexpr {type_str} {constName} = {resolved};")
            out.append("};")
            out.append("")
    return("\n".join(out))


def _config_type(value):
    valueType = value['valueType']
    if valueType == 'uint':
        maxValue = max(value['value'], value.get('maxValue', value['value']))
        return 'uint32_t' if maxValue <= 0xFFFFFFFF else 'uint64_t'
    if valueType == 'int':
        maxAbs = max(abs(value['value']), abs(value.get('maxValue', value['value'])))
        return 'int32_t' if maxAbs <= 0x7FFFFFFF else 'int64_t'
    if valueType == 'real':
        return 'double'
    return valueType


def includeEnum(args, prj, data):
    out = list()

    out.append("// enums")
    for type, value in data['enums'].items():
        out.append(f"enum  { value['type'] } {{ { ' '*value['descSpaces'] }//{value['desc']}")
        length = len(value['enum'])
        count = 0
        for enumData in value['enum']:
            count += 1
            if count == length:
                out.append(f"    { enumData['enumName'] }={ enumData['value'] } }}; { ' '*enumData['descSpaces'] }// { enumData['desc'] }")
            else:
                out.append(f"    { enumData['enumName'] }={ enumData['value'] },   { ' '*enumData['descSpaces'] }// { enumData['desc'] }")

        out.append(f"inline const char* { value['type'] }_prt( { value['type'] } val )")
        out.append("{")
        out.append("    switch( val )")
        out.append("    {")
        for enumData in value['enum']:
            out.append(f"        case { enumData['enumName'] }: return( \"{ enumData['enumName'] }\" );")
        out.append("    }")
        out.append("    return(\"!!!BADENUM!!!\");")
        out.append("}")

    out.append("")
    return("\n".join(wrap_module_namespace(args, data, out)))


def includeAddresses(args, prj, data):
    out = list()
    out.append("//instance base addresses")

    for key, value in prj.data['instances'].items():
        out.append(f"#define BASE_ADDR_{ value['instance'].upper() } {  ' ' * ( 20 - (len(value['instance']) ))}0x{int(value['offset']):x}")

    return("\n".join(out))


def includeRegAddresses(args, prj, data):
    out = list()
    out.append("//register addresses")

    for key, value in prj.data['registers'].items():
        out.append(f"#define REG_{ value['block'].upper() }_{ value['register'].upper() } {  ' ' * ( 30 - (len(value['block'])) - (len(value['register']))) }0x{(int(value['offset'])):x}")

    out.append("//memories base addresses")
    for key, value in prj.data['memories'].items():
        if value['regAccess']:
            out.append(f"#define REG_{ value['block'].upper() }_{ value['memory'].upper() } {  ' ' * ( 30 - (len(value['block'])) - (len(value['memory']))) }0x{(int(value['offset'])):x}")

    return("\n".join(out))
