# args from generator line
# prj object
# data set dict
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
    out.append(f'{ data["blockName"] }Base::{ data["blockName"] }Base(void) {colon}')
    comma = ''
    # loop twice for c++ constructor init ordering reasons
    for key, value in data['ports'].items():
        if value['direction'] == 'src':
            out.append(f'        { value  ["commentOut"] }{comma}{ value["name"] }("{ value["name"] }")')
            if value["commentOut"] == '':
                comma = ','
    for key, value in data['ports'].items():
        if value['direction'] == 'dst':
            out.append(f'        { value  ["commentOut"] }{comma}{ value["name"] }("{ value["name"] }")')
            if value["commentOut"] == '':
                comma = ','

    if out:
        last = out.pop()
        last = last[:-1]
        out.append(last)
    return("\n".join(out))

def constructorBody(args, prj, data):
    out = list()

    out.append('{')
    # take the list and return a string
    if out:
        last = out.pop()
        last = last[:-1]
        out.append(last)
    return("\n".join(out))
