# args from generator line
# prj object
# data set dict
from pysrc.arch2codeHelper import printError, printWarning, warningAndErrorReport, printIfDebug, roundup_pow2
from pysrc.intf_gen_utils import get_struct_width, get_const

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
    out.append("//constants\n")

    for const, value in data['constants'].items():
        match value['valueType']:
            case 'int32_t' | 'uint32_t':
                value_str = f"{value['value']}"
            case 'int64_t':
                value_str = f"{hex(value['value']).upper()}L"
            case 'uint64_t':
                value_str = f"{hex(value['value']).upper()}UL"
            case _:
                value_str = f"{value['value']}"
        out.append(f"const {value['valueType']} { value['constant'] } = { value_str };  // {value['desc']}\n")

    return("".join(out))

def includeTypes(args, prj, data):
    out = list()

    out.append(f"// types\n")
    for type, value in data['types'].items():
        if value['typeArraySize'] == 1:
            out.append(f"typedef { value['platformDataType'] } { value['type'] }; // [{prj.getConst( value['width'] )}] {value['desc']}\n")
        else:
            out.append(f"struct { value['type'] } {{ { value['platformDataType'] } word[ {value['typeArraySize']} ]; }}; // [{prj.getConst( value['width'] )}] {value['desc']}\n")

    return("".join(out))

def includeEnum(args, prj, data):
    out = list()

    out.append("// enums\n")
    for type, value in data['enums'].items():
        out.append(f"enum  { value['type'] } {{ { ' '*value['descSpaces'] }//{value['desc']}\n")
        length = len(value['enum'])
        count = 0
        for enumData in value['enum']:
            count += 1
            if count == length:
                out.append(f"    { enumData['enumName'] }={ enumData['value'] } }}; { ' '*enumData['descSpaces'] }// { enumData['desc'] }\n")
            else:
                out.append(f"    { enumData['enumName'] }={ enumData['value'] },   { ' '*enumData['descSpaces'] }// { enumData['desc'] }\n")

        out.append(f"inline const char* { value['type'] }_prt( { value['type'] } val )\n")
        out.append("{\n")
        out.append("    switch( val )\n")
        out.append("    {\n")
        for enumData in value['enum']:
            out.append(f"        case { enumData['enumName'] }: return( \"{ enumData['enumName'] }\" );\n")
        out.append("    }\n")
        out.append("    return(\"!!!BADENUM!!!\");\n")
        out.append("}\n")

    return("".join(out))

def includeAddresses(args, prj, data):
    out = list()
    out.append("//instance base addresses\n")



    for key, value in prj.data['instances'].items():
        out.append(f"#define BASE_ADDR_{ value['instance'].upper() } {  ' ' * ( 20 - (len(value['instance']) ))}0x{int(value['offset']):x}\n")

    return("".join(out))

def includeRegAddresses(args, prj, data):
    out = list()
    out.append("//register addresses\n")

    for key, value in prj.data['registers'].items():
        out.append(f"#define REG_{ value['block'].upper() }_{ value['register'].upper() } {  ' ' * ( 30 - (len(value['block'])) - (len(value['register']))) }0x{(int(value['offset'])):x}\n")

    out.append("//memories base addresses\n")
    for key, value in prj.data['memories'].items():
        if value['regAccess']:
            out.append(f"#define REG_{ value['block'].upper() }_{ value['memory'].upper() } {  ' ' * ( 30 - (len(value['block'])) - (len(value['memory']))) }0x{(int(value['offset'])):x}\n")

    return("".join(out))
