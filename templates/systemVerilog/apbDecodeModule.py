from pysrc.processYaml import existsLoad
from pysrc.arch2codeHelper import printError, warningAndErrorReport, clog2
from pathlib import Path
from pysrc.systemVerilogGeneratorHelper import fileNameBlockCheck, importPackages

from jinja2 import Template

# sorts a list of dictionaries by the key 'offset'
def keySort(d):
    return int(d['offset'])

def getParentStructures(prj, d):
    for item in prj.data['interfaces'][d['interfaceKey']]['structures']:
        if (item['structureType'] == 'addr_t'):
            addrSt = item['structure']
        elif (item['structureType'] == 'data_t'):
            dataSt = item['structure']
        else:
            printError(f"APB address and or data structures do not match template structure {item['structure']} with structureType {item['structureType']}")
            exit(warningAndErrorReport())
    return addrSt, dataSt

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    out = ''
    indentSize = 4
    indent = ' ' * indentSize

    # Pass in the stem of fileName and the blockName
    out += fileNameBlockCheck(Path(data['fileName']).resolve().stem, data['blockName'])

    # Packages
    startingContext = prj.data['blocks'][prj.getQualBlock(data['blockName'])]['_context']
    out += importPackages(args, prj, startingContext, data)
    out += "(\n"

# Seach container / parent's address group and find the instance for that group
#  to start processing
#  container's address is the incomingn apb interface
#  all other's attached are the address range of the instance not
#  matching the container
    # Ports
    for unusedKey, value in data['ports'].items():
        out += f"{indent}{value['interfaceData']['interfaceType']}_if.{value['direction']} {value['name']},\n"
    out += f"{indent}input clk, rst_n\n"
    out += ");\n\n"

    qualBlock = prj.getQualBlock(data['blockName'])
    qualInstance = None
    for unusedKey, value in prj.data['instances'].items():
        if value['instanceTypeKey'] == qualBlock:
            if qualInstance:
                printError(f"Detected multiple instances of {qualBlock}, only one instance of decoder type is allowed")
                exit(warningAndErrorReport())
            qualInstance = value['instance']
            parentBlock = prj.getQualBlock(value['container'])
            if args.instances:
                instFile = args.instances
                # so load it
                instances = existsLoad(instFile)
                # convert the list of user fieldly instances into context qualified instances
                instances = prj.getQualInstances( instances['instances'] )
            else:
                # otherwise use the list of instances from the database
                instances = dict.fromkeys(prj.data['instances'], 0)
            prj.initConnections(instances)
            parentData = prj.getBlockData(parentBlock, instances)

    addressGroupData = data['addressDecode']['addressGroupData']
    addrDecodeSize = addressGroupData['addressIncrement'] * addressGroupData['maxAddressSpaces']
    addrDecodeMask = addrDecodeSize - 1

    # Find the parent interface port name
    # Find a list of child interface port name(s)
    childInterfacePorts = []
    parentInterfacePort = None
    for unusedKey, value in parentData['connections'].items():
        if value['dst'] == qualInstance:
            if value['name'] != '':
                parentInterfacePort = value['name']
            elif value['dstport'] != '':
                parentInterfacePort = value['dstport']
            else:
                parentInterfacePort = value['interface']
            parentAddrSt, parentDataSt = getParentStructures(prj, value)
        elif value['src'] == qualInstance:
            inst = prj.instances[value['dst']]
            if value['name'] != '':
                d = {"name": f"{value['name']}", "offset": f"{prj.data['instances'][inst]['offset']}"}
            elif value['srcport'] != '':
                d = {"name": f"{value['srcport']}", "offset": f"{prj.data['instances'][inst]['offset']}"}
            else:
                d = {"name": f"{value['interface']}", "offset": f"{prj.data['instances'][inst]['offset']}"}
            childInterfacePorts.append(d)

    # Search connectionMaps for parent port
    #  no need to build childInterfacePorts because those most be at a connection at the level of the parent
    if parentInterfacePort is None:
        for unusedKey, value in parentData['connectionMaps'].items():
            if value['direction'] == 'dst' and value['instance'] == qualInstance:
                if value['name'] != '':
                    parentInterfacePort = value['name']
                else:
                    parentInterfacePort = value['instancePortName']
                parentAddrSt, parentDataSt = getParentStructures(prj, value)

# for now assume any selection at any address from the parentInterfacePort is valid
#   there is no way to check address ranges currently
# need a selection
# need a clear of selection
# selection is held until incoming PREADY from selected port
# flop prdata and pready
# pass pWData and all other signals down without flops

    out += f"{parentAddrSt} apb_addr;\n"
    out += f"assign apb_addr = {parentAddrSt}'({parentInterfacePort}.paddr) & {parentAddrSt}'(32'h{addrDecodeMask:_x});\n"

    # Set up parent signals
    t = Template(parent_sig_decl_j2_template)

    out += t.render(
        parent = {
            "interfacePort" : parentInterfacePort, "addrSt" : parentAddrSt, "dataSt" : parentDataSt
        }
    )
    out += '\n\n'

    childInterfacePorts.sort(reverse=True, key=keySort)
    for item in childInterfacePorts:
        t = Template(child_sig_decl_j2_template)
        out += t.render(
            child = {
                "interfacePort" : item['name']
            }
        )
        out += '\n\n'

    # Set up parent interface for incoming address selection
    out += f"always_comb begin\n"
    for item in childInterfacePorts:
        out += f"{indent}{item['name']}_next_psel = 1'b0;\n"
    out += f"{indent}set_trans_active = 1'b0;\n"
    out += f"{indent}if ({parentInterfacePort}.psel & ~trans_active) begin\n"
    out += f"{indent*2}set_trans_active = 1'b1;\n"
    first = 0
    for item in childInterfacePorts:
        if first == 0:
            # for clarity append hex address in comments after begin
            comment = int(f"{item['offset']}")
            out += f"{indent*2}if (apb_addr >= {parentAddrSt}'(32'h{int(item['offset']):_x})) begin\n"
        else:
            if (item['offset'] == 0 or item['offset'] == '0'):
                # for formatting remove the end and add back in after \n
                out = out[:-(3+(indentSize*2))]
                out += f"{indent*2}end"
            comment = int(f"{item['offset']}")
            if (item['offset'] == 0 or item['offset'] == '0'):
                out += f" else begin\n"
            else:
                out += f" else if (apb_addr >= {parentAddrSt}'(32'h{int(item['offset']):_x})) begin\n"
        out += f"{indent*3}{item['name']}_next_psel = '1;\n"
        out += f"{indent*2}end"
        first += 1
    out += f"\n{indent}end\n"
    out += "end\n\n"

    out += f"logic {parentInterfacePort}_next_pready;\n"
    out += f"{parentDataSt} {parentInterfacePort}_next_prdata, prdata;\n"
    out += f"logic {parentInterfacePort}_next_pslverr, pslverr;\n"
    out += "always_comb begin\n"
    out += f"{indent}{parentInterfacePort}_next_pready  = '0;\n"
    out += f"{indent}{parentInterfacePort}_next_prdata  = '0;\n"
    out += f"{indent}{parentInterfacePort}_next_pslverr = '0;\n"
    first = 0
    for item in childInterfacePorts:
        if first == 0:
            out += f"{indent}if ({item['name']}_psel) begin\n"
            out += f"{indent*2}{parentInterfacePort}_next_pready  = {item['name']}.pready;\n"
            out += f"{indent*2}{parentInterfacePort}_next_prdata  = {item['name']}.prdata;\n"
            out += f"{indent*2}{parentInterfacePort}_next_pslverr = {item['name']}.pslverr;\n"
        else:
            out += f" else if ({item['name']}_psel) begin\n"
            out += f"{indent*2}{parentInterfacePort}_next_pready  = {item['name']}.pready;\n"
            out += f"{indent*2}{parentInterfacePort}_next_prdata  = {item['name']}.prdata;\n"
            out += f"{indent*2}{parentInterfacePort}_next_pslverr = {item['name']}.pslverr;\n"
        out += f"{indent}end"
        first += 1
    out += "\nend\n\n"

    # Retun the parent APB signals
    out += f"`DFF(pready, {parentInterfacePort}_next_pready)\n"
    out += f"`DFF(prdata, {parentInterfacePort}_next_prdata)\n"
    out += f"`DFF(pslverr, {parentInterfacePort}_next_pslverr)\n"
    out += f"assign {parentInterfacePort}.pready  = pready;\n"
    out += f"assign {parentInterfacePort}.prdata  = prdata;\n"
    out += f"assign {parentInterfacePort}.pslverr = pslverr;\n"

    out += "\n"

    out += f"endmodule: {data['blockName']}"

    return (out)

#------------------------------------------------------------------------------
# Jinja2 templates
#------------------------------------------------------------------------------

parent_sig_decl_j2_template = """\
//signals for interface {{ parent.interfacePort }}
{{ parent.addrSt }} paddr_q;
`DFF (paddr_q, {{ parent.interfacePort }}.paddr)
{{ parent.dataSt }} pwdata_q;
`DFF (pwdata_q, {{ parent.interfacePort }}.pwdata)
logic penable_q;
`DFF (penable_q, {{ parent.interfacePort }}.penable)
logic pwrite_q;
`DFF (pwrite_q, {{ parent.interfacePort }}.pwrite)

logic pready;
logic set_trans_active;
logic trans_active;
`SCFF(trans_active, set_trans_active, pready)
"""

child_sig_decl_j2_template = """\
//signals for interface {{ child.interfacePort }}
logic {{ child.interfacePort }}_psel;
logic {{ child.interfacePort }}_next_psel;
`SCFF({{ child.interfacePort }}_psel, {{ child.interfacePort }}_next_psel, {{ child.interfacePort }}.pready)

assign {{ child.interfacePort }}.paddr   = paddr_q;
assign {{ child.interfacePort }}.penable = penable_q & {{ child.interfacePort }}_psel;
assign {{ child.interfacePort }}.psel    = {{ child.interfacePort }}_psel;
assign {{ child.interfacePort }}.pwrite  = pwrite_q;
assign {{ child.interfacePort }}.pwdata  = pwdata_q;
"""
