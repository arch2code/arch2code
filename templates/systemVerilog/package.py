from pysrc.systemVerilogGeneratorHelper import importPackages

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    out     = ''
    indent  = ' ' *4
    if data['context'] is None:
        return out
    packageName = prj.includeName[data['context'][0]] + '_package'

    out += f"package {packageName};\n"
    pkg_str = importPackages(args, prj, data['context'][0], data, excludeSelf=True) 
    if pkg_str:
        out += pkg_str + '\n'

    # Now put in everything at this context level
    # Generate constants as localparam[s]
    for unusedKey, value in data['constants'].items():
        match value['valueType']:
            case 'int32_t':
                type_str = 'int'
                if value['value'] < 0:
                    value_str = f"-32'sh{abs(value['value']):09_X}"
                else:
                    value_str = f"32'sh{value['value']:09_X}"
            case 'uint32_t':
                type_str = 'int unsigned'
                value_str = f"32'h{value['value']:09_X}"
            case 'int64_t':
                type_str = 'longint'
                if value['value'] < 0:
                    value_str = f"-64'sh{abs(value['value']):019_X}"
                else:
                    value_str = f"64'sh{value['value']:019_X}"
            case 'uint64_t':
                type_str = 'longint unsigned'
                value_str = f"64'h{value['value']:019_X}"
            case _:
                type_str = value['valueType']
                value_str = f"{value['value']}"
        out += f"localparam {type_str} {value['constant']} = {value_str};  // {value['desc']}\n"
    # Generate types
    out += f"\n// types\n"
    for unusedKey, value in data['types'].items():
        if value['width'] in prj.data['constants']:
            value['desc'] += f" sizing from constant {prj.data['constants'][value['width']]['constant']}"
        out += f"typedef logic[{value['realwidth']}-1:0] {value['type']}; //{value['desc']}\n"

    # Generate enums
    out += f"\n// enums\n"
    for unusedKey, value in data['enums'].items():
        try:
            width = max(int(value['width']), 1)
        except (ValueError, TypeError):
            width = value['width']
            if value['width'] in prj.data['constants']:
                width = prj.data['constants'][value['width']]['constant']
        out += f"typedef enum logic[{width}-1:0] {{ {' '*value['descSpaces']}//{value['desc']}\n"
        # below loop processes enums and puts a comma after them for all in the list but the last one
        for enumData in value['enum'][:-1]:
            out += f"{indent}{enumData['enumName']} = {enumData['value']}, {' '*enumData['descSpaces']}// {enumData['desc']}\n"
        # this statement is similar to the loop but we are printing the last element in the list without a comma
        #   this style is pythonic and may look a little messy at first
        out += f"{indent}{value['enum'][-1]['enumName']} = {value['enum'][-1]['value']} {' '*value['enum'][-1]['descSpaces']}// {value['enum'][-1]['desc']}\n"
        # finally delcare the enum type and move on to any more enums or finish
        out += f"}} {value['type']};\n"

    # Generate structures
    out += f"\n// structures\n"
    for struct, value in data['structures'].items():
        out += f"typedef struct packed {{\n"
        for var, varData in value['vars'].items():
            if varData['arraySize'] == 0 or varData['arraySize'] == '0':
                arraySize = ''
            else:
                arraySize = f"[{varData['arraySize']}-1:0] "
            if varData['entryType'] == 'NamedVar' or varData['entryType'] == 'NamedType':
                out += f"{indent}{varData['varType']} {arraySize}{varData['variable']}; //{varData['desc']}\n"
            else: # varData['entryType'] == 'NamedStruct'
                out += f"{indent}{varData['subStruct']} {arraySize}{varData['variable']}; //{varData['desc']}\n"
        out += f"}} {value['structure']};\n\n"

    out += f"endpackage : {packageName}"

    return (out)
