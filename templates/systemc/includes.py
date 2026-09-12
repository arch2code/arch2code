from pysrc.intf_gen_utils import wrap_module_namespace
import pysrc.emissionUtils as emissionUtils

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
        case _:
            raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are constants, types, enums, addresses, regAddresses")


def _fwConstSymSpelling(prj, evalMemberNames):
    """Per-symbol speller for an eval-derived parameterizable constant emitted as
    a flat FW header constant. A referent that is itself such an emitted FW
    constant stays symbolic as its bare name (so the chain reads
    IP_DATA_WIDTH_X4 = IP_DATA_WIDTH_X2 * 2); any other referent (a block param
    or fixed constant, which the FW header does not emit as its own symbol) is
    spelled from its persisted value as a literal. FW headers have no per-variant
    Config, so the persisted default is the single firmware value."""
    def symSpelling(symKey):
        if symKey in prj.data['constants']:
            name = prj.data['constants'][symKey]['constant']
            if name in evalMemberNames:
                return name
        return str(prj.getConst(symKey))
    return symSpelling


def includeConstants(args, prj, data):
    out = list()
    out.append("//constants")

    # The SystemC path carries parameterizable constants in the per-variant
    # Config structs, so they are skipped here. FW headers have no Config struct,
    # so in fw mode eval-derived parameterizable constants are emitted as flat
    # consts whose RHS is the canonical eval expression re-spelled in C.
    fwMode = args.mode == 'fw'
    fwEvalMembers = {
        value['constant']
        for value in data['constants'].values()
        if value['isParameterizable'] and value['evalCanonical']
    } if fwMode else set()
    fwSymSpelling = _fwConstSymSpelling(prj, fwEvalMembers) if fwMode else None

    for const, value in data['constants'].items():
        if value['isParameterizable'] and value['constant'] not in fwEvalMembers:
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
        if value['isParameterizable']:
            value_str = emissionUtils.emitExpr(value['evalCanonical'], fwSymSpelling, emissionUtils.C)
        # `inline constexpr` (not plain `const`) so these namespace-scope constants
        # have external linkage. In a C++20 module purview a `const` variable has
        # internal linkage, and GCC rejects an exported template (e.g. a type's
        # `static constexpr _bitWidth`) that references an internal-linkage entity.
        # `inline constexpr` is ODR-safe across TUs and remains usable in the
        # constant expressions these constants feed.
        out.append(f"inline constexpr {type_str} { value['constant'] } = { value_str };  // {value['desc'].strip()}")

    out.append("")
    return("\n".join(wrap_module_namespace(args, data, out)))


def typeWidthExpression_cpp(value, prj, useConfig=False):
    """Build a C++ constexpr-compatible bit-width expression for a type.
    Delegates the language-neutral width decision tree to
    emissionUtils.typeWidthExpr, binding C++ constant spelling
    (emissionUtils.constReference_cpp, Config::-aware) and the C++
    literal-width fallback (prj.resolveTypeWidth)."""
    return emissionUtils.typeWidthExpr(
        value, emissionUtils.C,
        constSpelling=lambda key: emissionUtils.constReference_cpp(key, prj, useConfig),
        literalWidth=lambda v: str(prj.resolveTypeWidth(v)))


def includeTypes(args, prj, data):
    out = list()

    out.append("// types")
    for type, value in data['types'].items():
        # Comments show resolved integer bit width, not symbolic expression
        widthComment = str(value['realwidth'])
        if value['isParameterizable']:
            if value['maxBitwidth'] <= 64:
                # The container is fixed 64-bit because a parameterizable type must
                # hold its worst case across variants (maxBitwidth), not its width at
                # default parameter values (realwidth, which platformDataType encodes).
                # Only the signedness varies, so arithmetic on the alias (>>, <, /, %)
                # matches the declared type.
                containerType = 'int64_t' if value['isSigned'] else 'uint64_t'
                out.append(
                    f"template<typename Config> using { value['type'] } = {containerType}; // [max:{value['maxBitwidth']}] {value['desc']}"
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
        # Restrict to this build's design tree; a referenced child project's
        # standalone harness instances are parsed into the same database but do
        # not descend from the active topInstance.
        if key not in prj.reachableInstances:
            continue
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
