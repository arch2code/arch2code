from pathlib import Path
from pysrc.systemVerilogGeneratorHelper import importPackages

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    out     = ''
    indent  = ' ' *4
    if data['contexts'] is None:
        return out
    packageName = prj.includeName[data['contexts'][0]] + '_package'

    out     += f"package {packageName};\n"
    out     += importPackages(args, prj, data['contexts'][0], data, excludeSelf=True)

    # Now put in everything at this context level
    # print list in f string without braces; https://stackoverflow.com/a/62225685/8980882
    out += f"//constants as defined by the scope of the following context(s): {*data['contexts'],}\n"
    # Generate constants as localparam[s]
    for unusedKey, value in data['constants'].items():
        if value['value'] > 0xFFFFFFFF:
            out += f"//         {value['constant']} = {' '*value['valueSpaces']}   'd{value['value']};  // {value['desc']}\n"
            out += f"localparam {value['constant']} = {' '*value['valueSpaces']} 64'h{value['value']:019_X};  // {value['desc']}\n"
        else:
            out += f"//         {value['constant']} = {' '*value['valueSpaces']}   'd{value['value']};  // {value['desc']}\n"
            out += f"localparam {value['constant']} = {' '*value['valueSpaces']} 32'h{value['value']:09_X};  // {value['desc']}\n"
    # Generate types
    out += f"\n// types\n"
    for unusedKey, value in data['types'].items():
        if value['width'] in prj.data['constants']:
            value['desc'] += f" sizing from constant {prj.data['constants'][value['width']]['constant']}"
        out += f"typedef logic[{value['realwidth']}-1:0] {value['type']}; //{value['desc']}\n"

    # Generate enums
    out += f"\n// enums\n"
    for unusedKey, value in data['enums'].items():
        if isinstance(value['width'], int):
            width = max(value['width'], 1)
        else:
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
            if varData['arraySize'] == 1 or varData['arraySize'] == '1':
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
