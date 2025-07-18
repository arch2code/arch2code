import pysrc.arch2codeGlobals as globals
from pysrc.arch2codeHelper import printError
from graphviz import Digraph
from operator import itemgetter

# Globally used variables throught functions in this file
structureColor = 'lightgrey' # color used for structures
variableColor  = '#8dd3c7'   # color used for variables
typeColor      = '#ffffb3'   # color used for types
constColor     = '#bebada'   # color used for constants
nestedStColor  = '#fb8072'   # color used for any nested or embedded structures within another structure
                             # the background color is used for bit width when constants are not used to define a type
cellborder     = 1

# Going to use a nodes list to append to a dictionary that contains
#   name, width, row, col, color, and port
#   name is the name of a structure, variable, type, or constant
#   for nested structures they must have a port of it's own name, ok for top most too since recurssion isn't possible
#   edges get drwan from top most structure's (name) at port of nested struct to nested struct at its port
#       nestedSt:dSt -> dSt:dSt
#           nodes for structures other than the top most structure are only added once since a many references to 
#           the same structure will only clutter the diagram
#           while making nodes add each structure to a list and check if it is not on the list before making an node and edges
#               we only need one reference for each structure
# Rows are always 5
#   top row is structureName
#   next row is member name
#   next row is either type or structureName of embedded structure
#   next row is either contant name, or bit width of type, or bit width of embedded structure
#   last row is the list of bits from most significant on left to 0 for structureName
def drawStructure(prj, contextPlusStructure, colors):

    structure     = Digraph(node_attr={'shape': 'plaintext', 'fontname': 'Courier'}, graph_attr={'bgcolor': globals.bgcolor, 'tooltip': 'Diagram of strcuture {}'.format(contextPlusStructure)})
    structureList = []
    parentName, label = structureAndLabel(prj, contextPlusStructure, colors)
    structure.node('{}'.format(parentName), label='{}'.format(label))
    structureList.append(parentName)

# need to go down each structures set of structures
# can structureAndLabel return a more flag, while more search more
# or should structureAndLabel return a list of structure and labels and operate recursviely ?
#   for recursion pass in structure (Digraph), structureList, prj, contextPlusStructure, colors
#       return structure (Digraph), structureList
# TODO update with recurrsion, this only goes one level of structures deep
    for k, v in prj.data['structures'][contextPlusStructure]['vars'].items():
        if v['entryType'] == 'NamedStruct' and v['subStruct'] not in structureList:
            structureName, label = structureAndLabel(prj, v['subStructKey'], colors, True)
            structure.node('{}'.format(structureName), label='{}'.format(label))
            structure.edge(tail_name='{}:{}'.format(parentName, structureName), head_name='{}:{}'.format(structureName, structureName))

    if (globals.deleteGV):
        # creates an output svg image in the specified directory
        structure.render(filename=globals.filename, directory=globals.gvdir, view=globals.debug, cleanup=globals.deleteGV, format='svg')
    else:
        # creates an output dot file with .gv and from it generates an .gv.svg image in the same directory
        structure.render(filename=globals.filename+'.gv', directory=globals.gvdir, view=globals.debug, format='svg')

def structureAndLabel(prj, contextPlusStructure, bitColors, addPort=None):
    indent          = ' ' * 4
    # make a label and add it to the node
    structureDict   = prj.data['structures'][contextPlusStructure]
    width           = structureDict['width']
    bitNum          = width-1
    structureName   = structureDict['structure']
    # table with no border and no spacing, distinguished with cellborder and color
    label = f'<<table border="0" cellborder="{cellborder}" cellspacing="0" cellpadding="2">\n'
    # first row with structureName, each additional row after is variable, type, constant, or a mix
    if addPort:
        label += f'{indent}<tr><td port="{structureName}" bgcolor="{structureColor}" colspan="{width}">{structureName}</td></tr>\n'
    else:
        label += f'{indent}<tr><td bgcolor="{structureColor}" colspan="{width}">{structureName}</td></tr>\n'

    rows = []
    c = 0
    for k, v in prj.data['structures'][contextPlusStructure]['vars'].items():
        r = 0
        # check if arraySize is a constant or not
        if v['arraySizeKey'] == '':
            arraySize = int(v['arraySize'])
        else:
            arraySize = prj.data['constants'][v['arraySizeKey']]['value']
        if v['entryType'] == 'NamedStruct':
            width = prj.data['structures'][v['subStructKey']]['width']
            if arraySize:
                for i in range(arraySize-1, -1, -1):
                    arrayString = f'[{i}]'
                    name = f'{v["variable"]}{arrayString}'
                    if i == arraySize-1:
                        port = v['subStruct']
                    else:
                        port = None
                    rows.append({'name': name, 'width': width, 'row': r, 'col': c, 'color': variableColor, 'port': None})
                    rows.append({'name': v['subStruct'], 'width': width, 'row': r+1, 'col': c, 'color': nestedStColor, 'port': port})
                    rows.append({'name': width, 'width': width, 'row': r+2, 'col': c, 'color': globals.bgcolor, 'port': None})
                    c = c + 1
            else:
                arrayString = ''
                name = f'{v["variable"]}{arrayString}'
                port = v['subStruct']
                rows.append({'name': name, 'width': width, 'row': r, 'col': c, 'color': variableColor, 'port': None})
                rows.append({'name': v['subStruct'], 'width': width, 'row': r+1, 'col': c, 'color': nestedStColor, 'port': port})
                rows.append({'name': width, 'width': width, 'row': r+2, 'col': c, 'color': globals.bgcolor, 'port': None})
                c = c + 1

            r = r + 3
        elif v['entryType'] == 'NamedVar' or v['entryType'] == 'NamedType':
            # variable has to have a type
            typeKey = prj.data['types'][v['varTypeKey']]
            typeName = prj.data['types'][v['varTypeKey']]['type']
            constKeyOrWidth = typeKey['width']
            if isinstance(constKeyOrWidth, int):
                width = constKeyOrWidth
                constName = constKeyOrWidth
                colorForConstRow = globals.bgcolor
            else:
                width = prj.data['constants'][constKeyOrWidth]['value']
                constName = f"{prj.data['constants'][constKeyOrWidth]['constant']} ({width})"
                colorForConstRow = constColor
            if arraySize:
                for i in range(arraySize-1, -1, -1):
                    name = f'{v["variable"]}[{i}]'
                    rows.append({'name': name, 'width': width, 'row': r, 'col': c, 'color': variableColor, 'port': None})
                    rows.append({'name': typeName, 'width': width, 'row': r+1, 'col': c, 'color': typeColor, 'port': None})
                    rows.append({'name': constName, 'width': width, 'row': r+2, 'col': c, 'color': colorForConstRow, 'port': None})
                    c = c + 1
            else:
                name = f'{v["variable"]}'
                rows.append({'name': name, 'width': width, 'row': r, 'col': c, 'color': variableColor, 'port': None})
                rows.append({'name': typeName, 'width': width, 'row': r+1, 'col': c, 'color': typeColor, 'port': None})
                rows.append({'name': constName, 'width': width, 'row': r+2, 'col': c, 'color': colorForConstRow, 'port': None})
                c = c + 1
            r = r + 3
        else:
            printError(f"entryType of {v['entryType']} is unexpected, only NamedStruct and NamedVar coded")
        c = c + 1

    # sort by col, then row
    for row in sorted(rows, key=itemgetter('row', 'col')):
        if row['row'] == 0 and row['col'] == 0:
            label += f'{indent}<tr>\n'
        elif row['col'] == 0:
            label += f'{indent}</tr>\n{indent}<tr>\n'
        if row['port']:
            label += f'{indent*2}<td port="{row["port"]}" bgcolor="{row["color"]}" colspan="{row["width"]}">{row["name"]}</td>\n'
        else:
            label += f'{indent*2}<td bgcolor="{row["color"]}" colspan="{row["width"]}">{row["name"]}</td>\n'

    # if number of colors is nibble aligned align left most bit so 
    #   the zeroth position of every nibble is the same starting color
    #   colors lists with 8 colors is nibble aligned and the same starting
    #   color will be on the zeroth position of every byte
    if len(bitColors) % 4 == 0:
        # bitnum + 1 is total width
        shiftNum = len(bitColors) - (bitNum + 1) % len(bitColors)
        bitColors = bitColors[shiftNum:] + bitColors[:shiftNum]
    color = bitColors[0]

    # build last row that shows the bits consumed for this structure
    label += f'{indent}</tr>\n{indent}<tr>\n'
    while True:
        # single space &nbsp;
        # two spaces &ensp;
        # three spaces &emsp;
        if bitNum < 10:
            if bitNum == 0:
                label += f'{indent*2}<td bgcolor="{color}">&emsp;{bitNum:d}</td>\n'
            else:
                label += f'{indent*2}<td bgcolor="{color}">&nbsp;{bitNum:d}</td>\n'
        elif bitNum < 100:
            label += f'{indent*2}<td bgcolor="{color}">&nbsp;{bitNum:d}</td>\n'
        else:
            label += f'{indent*2}<td bgcolor="{color}">{bitNum:d}</td>\n'
        if bitNum == 0:
            break
        bitNum = bitNum-1

        # rotate colors
        bitColors = bitColors[1:] + bitColors[:1]
        color     = bitColors[0]
    label += f'{indent}</tr>\n'
    label += '</table>>\n'
    return structureName, label