#from pysrc.arch2codeHelper import printError

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    out     = '\n'
    indent  = ' ' *4
    out     += f"//constants as defined by scope: {data['context']}\n"
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
        if value['width'] in prj['constants']:
            value['desc'] += f" sizing from constant {prj['constants'][value['width']]['constant']}"
        # Check if type is signed
        isSigned = value.get('isSigned', False)
        signedStr = " signed" if isSigned else ""
        out += f"typedef logic{signedStr}[{value['realwidth']}-1:0] {value['type']}; //{value['desc']}\n"

    # Generate enums
    out += f"\n// enums\n"
    for unusedKey, value in data['enums'].items():
        out += f"typedef enum logic[{value['width']}-1:0] {{ {' '*value['descSpaces']}//{value['desc']}\n"
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

    return (out)