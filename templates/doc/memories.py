import pysrc.arch2codeGlobals as globals
from pysrc.drawStructure import drawStructure

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    # Strings used during generation
    out          = ''     # The returned output string
    #indent       = ' ' *4 # The indentation string
    structList   = []
    # set DeleteGV
    globals.deleteGV = True

    for unUsedKey, mem in prj.data['memories'].items():
        # Check for wordLineKey and update wordLines with parameter name and size
        if mem['wordLinesKey'] != '':
            wordLines = f"{mem['wordLines']} ({prj.data['constants'][mem['wordLinesKey']]['value']})"
        else:
            wordLines = f"{mem['wordLines']}"
        # Check for countKey and update count with parameter name and size
        if mem['countKey'] != '':
            count = f"{mem['count']} ({prj.data['constants'][mem['countKey']]['value']})"
        else:
            count = f"{mem['count']}"

        # Table title
        out += f".{mem['memory']}\n"
        # Attributes and table start
        out += '[cols="1, 1, 1, 1, 1, 1, 1"]\n|===\n'
        out += '|Memory |Block Containing |wordlines |addressStruct |structure for Data |description |count\n\n'
        out += f"|{mem['memory']}\n\n|{mem['block']}\n\n|{wordLines}\n\n|xref:#{mem['addressStruct']}[{mem['addressStruct']}]\n\n|xref:#{mem['structure']}[{mem['structure']}]\n\n|{mem['desc']}\n\n|{count}\n|===\n\n\n"

        if mem['addressStruct'] not in structList:
            globals.filename = mem['addressStruct']
            drawStructure(prj, mem['addressStructKey'], globals.colors)
            out += f".{mem['addressStruct']}\n"
            out += f"[#{mem['addressStruct']}]\n"
            out += f"image::{mem['addressStruct']}.svg[width=auto,opts=interactive]\n"
            structList.append(mem['addressStruct'])
        
        if mem['structure'] not in structList:
            globals.filename = mem['structure']
            drawStructure(prj, mem['structureKey'], globals.colors)
            out += f".{mem['structure']}\n"
            out += f"[#{mem['structure']}]\n"
            out += f"image::{mem['structure']}.svg[width=auto,opts=interactive]\n"
            structList.append(mem['structure'])

    return(out)