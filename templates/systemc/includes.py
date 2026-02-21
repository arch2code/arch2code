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
            print("error missing section, valid values are constants, types, enums")
            exit()


def includeConstants(args, prj, data):
    out = list()
    out.append("//constants")

    for const, value in data['constants'].items():
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
        out.append(f"const {type_str} { value['constant'] } = { value_str };  // {value['desc']}")

    out.append("")
    return("\n".join(out))


def typeWidthExpression_cpp(value, prj):
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
        constName = prj.data['constants'][wl2Key]['constant']
        return f"clog2({constName}+1){signedExtra}"
    wl2 = value['widthLog2']
    if wl2 != '':
        return f"clog2({wl2}+1){signedExtra}"

    # Check widthLog2minus1
    wl2m1Key = value['widthLog2minus1Key']
    if wl2m1Key:
        constName = prj.data['constants'][wl2m1Key]['constant']
        return f"clog2({constName}){signedExtra}"
    wl2m1 = value['widthLog2minus1']
    if wl2m1 != '':
        return f"clog2({wl2m1}){signedExtra}"

    # Direct width — check widthKey for constant, else literal
    widthKey = value['widthKey']
    if widthKey:
        constName = prj.data['constants'][widthKey]['constant']
        return constName
    return str(value['realwidth'])


def includeTypes(args, prj, data):
    out = list()

    out.append("// types")
    for type, value in data['types'].items():
        # Comments show resolved integer bit width, not symbolic expression
        widthComment = str(value['realwidth'])
        if value['typeArraySize'] == 1:
            out.append(
                f"typedef { value['platformDataType'] } { value['type'] }; // [{widthComment}] {value['desc']}"
            )
        else:
            out.append(
                f"struct { value['type'] } {{ { value['platformDataType'] } word[ {value['typeArraySize']} ]; }}; // [{widthComment}] {value['desc']}"
            )

    out.append("")
    return("\n".join(out))


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
    return("\n".join(out))


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
