# args from generator line
# prj object
# data set dict
from pysrc.arch2codeHelper import printError, printWarning, warningAndErrorReport, printIfDebug

def render(args, prj, data):
    match args.section:
        case 'init':
            return(constructorInit(args, prj, data))
        case 'body':
            return(constructorBody(args, prj, data))
        case _:
            print("error missing section, valid values are implementation, externs, headerDecl")
            exit()


def constructorInit(args, prj, data):
    out = list()
    if len(data['ports']) > 0:
        colon = ':'
    else:
        colon = ''
    out.append(f'{ data["blockName"] }Base::{ data["blockName"] }Base(void) {colon}\n')
    comma = ''
    # loop twice for c++ constructor init ordering reasons
    for key, value in data['ports'].items():
        if value['direction'] == 'src':
            out.append(f'        { value  ["commentOut"] }{comma}{ value["name"] }("{ value["name"] }")\n')
            if value["commentOut"] == '':
                comma = ','
    for key, value in data['ports'].items():
        if value['direction'] == 'dst':
            out.append(f'        { value  ["commentOut"] }{comma}{ value["name"] }("{ value["name"] }")\n')
            if value["commentOut"] == '':
                comma = ','

    if out:
        last = out.pop()
        last = last[:-1]
        out.append(last)
    return("".join(out))

def constructorBody(args, prj, data):
    out = list()

    out.append('{\n')
    # take the list and return a string
    if out:
        last = out.pop()
        last = last[:-1]
        out.append(last)
    return("".join(out))
