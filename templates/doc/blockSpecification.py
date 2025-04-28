import pysrc.arch2codeGlobals as globals
from pysrc.drawStructure import drawStructure

structList   = []

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    # Strings used during generation
    out          = ''     # The returned output string
    indent       = ' ' *4 # The indentation string
    # set DeleteGV
    globals.deleteGV = True

    blockName = f"{data['blockName']}"
    out += f"## Block Diagram for {blockName}\n\n"
    out += "jira issue: https://arch2code.atlassian.net/browse/A2C-288[A2C-288], _todo_.\n\n"
    out += f"## Interfaces for {blockName}\n\n"

    # Ports
    out += '[cols="1, 1, 1, 1, 1, 1"]\n|===\n'
    direction = None
    out += '|Interface Name |Interface Type |Direction |Structure Type |Structure Name |Description\n\n'
    for unusedKey, value in data['ports'].items():
        if (value['direction'] == 'dst'):
            direction = f"{blockName} is Destination"
        else: # assumes only two choices
            direction = f"{blockName} is Initiator"
        out += f"|{value['name']} |{value['interfaceData']['interfaceType']} |{direction}"
        strucureNum = 0
        if (value['interfaceData']['structures']):
            for s in value['interfaceData']['structures']:
                addStructure(s['structure'], s['structureKey'])
                if (strucureNum > 0):
                    out += f"|||| {s['structureType']} |xref:#{s['structure']}[{s['structure']}]|\n"
                else:
                    out += f"| {s['structureType']} |xref:#{s['structure']}[{s['structure']}]| {value['interfaceData']['desc']}\n"
                strucureNum+=1
        else:
            out += f"| None| None| {value['interfaceData']['desc']}\n"

    out += f"|===\n\n\n"

# TODO draw memories, same as memories module
    out += f"## Memories Instances in {blockName}\n\n"
    out += "jira issue: https://arch2code.atlassian.net/browse/A2C-289[A2C-289], _todo_.\n\n"
# TODO draw registers as a table
    out += f"## Registers Delcared in {blockName}\n\n"
    out += "jira issue: https://arch2code.atlassian.net/browse/A2C-290[A2C-290], _todo_.\n\n"
# TODO draw instances, one table each with interface list
    out += f"## Module Instances in {blockName}\n\n"
    out += "jira issue: https://arch2code.atlassian.net/browse/A2C-291[A2C-291], _todo_.\n\n"
# TODO list included packages
    out += f"## Packages included in {blockName}\n\n"
    out += "jira issue: https://arch2code.atlassian.net/browse/A2C-292[A2C-292], _todo_.\n\n"
# structures inline at the end of the specification
#   TODO consider displaying in each sub category
#        if previously delcared skip but have link to image
    out += f"## Structures througout {blockName}\n\n"
    out += drawStructures(prj, structList)

    return(out)

# better as a single line, or function call
## if name not in structList
def addStructure(name, key):
    if name not in structList:
        structList.append([name, key])

# change name to documentStructures
## share with memories
def drawStructures(prj, listToDraw):
    output = ''
    for s in listToDraw:
        # s is a list from the structList
        ## item 0 is the name / structure
        ## item 1 is the structureKey
        globals.filename = s[0]
        drawStructure(prj, s[1], globals.colors)
        output += f".{s[0]}\n"
        output += f"[#{s[0]}]\n"
        output += f"image::{s[0]}.svg[width=auto,opts=interactive]\n"
    return output