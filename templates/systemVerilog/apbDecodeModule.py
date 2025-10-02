from pysrc.processYaml import existsLoad, getPortChannelName
from pysrc.arch2codeHelper import printError, warningAndErrorReport, clog2
from pathlib import Path
from pysrc.systemVerilogGeneratorHelper import fileNameBlockCheck, importPackages
import pysrc.intf_gen_utils as intf_gen_utils

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
    out = []
    indentSize = 4
    indent = ' ' * indentSize

    # Pass in the stem of fileName and the blockName
    out.append(fileNameBlockCheck(Path(data['fileName']).resolve().stem, data['blockName']))

    # Packages
    startingContext = prj.data['blocks'][prj.getQualBlock(data['blockName'])]['_context']
    out.append(importPackages(args, prj, startingContext, data))
    out.append("(\n")

    # Ports
    out.extend(intf_gen_utils.sv_gen_ports(data, prj, indent))

# Seach container / parent's address group and find the instance for that group
#  to start processing
#  container's address is the incomingn apb interface
#  all other's attached are the address range of the instance not
#  matching the container
#    qualBlock = prj.getQualBlock(data['blockName'])
#    qualInstance = None
#    for unusedKey, value in prj.data['instances'].items():
#        if value['instanceTypeKey'] == qualBlock:
#            if qualInstance:
#                printError(f"Detected multiple instances of {qualBlock}, only one instance of decoder type is allowed")
#                exit(warningAndErrorReport())
#            qualInstance = value['instance']
#            parentBlock = prj.getQualBlock(value['container'])
#            if args.instances:
#                instFile = args.instances
#                # so load it
#                instances = existsLoad(instFile)
#                # convert the list of user fieldly instances into context qualified instances
#                instances = prj.getQualInstances( instances['instances'] )
#            else:
#                # otherwise use the list of instances from the database
#                instances = dict.fromkeys(prj.data['instances'], 0)
#            prj.initConnections(instances)
#            parentData = prj.getBlockDataOld(parentBlock, instances)
    qualInstance = next(iter(data['instances']))
    parentBlock = next(iter(data['containerBlocks']))
    parentData = prj.getBlockData(parentBlock)
    addressGroupData = data['addressDecode']['addressGroupData']
    addrDecodeSize = addressGroupData['addressIncrement'] * addressGroupData['maxAddressSpaces']
    addrDecodeMask = addrDecodeSize - 1

    # Find the parent interface port name
    # Find a list of child interface port name(s)
    childInterfacePorts = []
    parentInterfacePort = None
    for unusedKey, value in parentData['connections'].items():
        if value['dstKey'] == qualInstance:
            parentInterfacePort = getPortChannelName(value, 'dstport')
            parentAddrSt, parentDataSt = getParentStructures(prj, value)
        elif value['srcKey'] == qualInstance:
            myPort = getPortChannelName(value, 'srcport')
            childInterfacePorts.append({"name": myPort, "offset": f"{prj.data['instances'][value['dstKey']]['offset']}"})

    # Search connectionMaps for parent port
    #  no need to build childInterfacePorts because those most be at a connection at the level of the parent
    if parentInterfacePort is None:
        for unusedKey, value in parentData['connectionMaps'].items():
            if value['direction'] == 'dst' and value['instance'] == qualInstance:
                parentInterfacePort = getPortChannelName(value, 'instancePortName')
                parentAddrSt, parentDataSt = getParentStructures(prj, value)

# for now assume any selection at any address from the parentInterfacePort is valid
#   there is no way to check address ranges currently
# need a selection
# need a clear of selection
# selection is held until incoming PREADY from selected port
# flop prdata and pready
# pass pWData and all other signals down without flops

    out.append(f"{parentAddrSt} apb_addr;\n")
    out.append(f"assign apb_addr = {parentAddrSt}'({parentInterfacePort}.paddr) & {parentAddrSt}'(32'h{addrDecodeMask:_x});\n")

    # Set up parent signals
    t = Template(parent_sig_decl_j2_template)

    out.append(t.render(
        parent = {
            "interfacePort" : parentInterfacePort, "addrSt" : parentAddrSt, "dataSt" : parentDataSt
        }
    ))
    out.append('\n\n')

    childInterfacePorts.sort(reverse=True, key=keySort)
    for item in childInterfacePorts:
        t = Template(child_sig_decl_j2_template)
        out.append(t.render(
            child = {
                "interfacePort" : item['name']
            }
        ))
        out.append('\n\n')

    # Set up parent interface for incoming address selection
    out.append(f"always_comb begin\n")
    for item in childInterfacePorts:
        out.append(f"{indent}{item['name']}_next_psel = 1'b0;\n")
    out.append(f"{indent}set_trans_active = 1'b0;\n")
    out.append(f"{indent}if ({parentInterfacePort}.psel & ~trans_active) begin\n")
    out.append(f"{indent*2}set_trans_active = 1'b1;\n")
    first = True
    for item in childInterfacePorts:
        if first:
            out.append(f"{indent*2}if (apb_addr >= {parentAddrSt}'(32'h{int(item['offset']):_x})) begin\n")
            first = False
        else:
            if (item['offset'] == 0 or item['offset'] == '0'):
                out.append(f"{indent*2}end else begin\n")
            else:
                out.append(f"{indent*2}end else if (apb_addr >= {parentAddrSt}'(32'h{int(item['offset']):_x})) begin\n")
        out.append(f"{indent*3}{item['name']}_next_psel = '1;\n")
    out.append(f"{indent*2}end\n")
    out.append(f"{indent}end\n")
    out.append("end\n\n")

    out.append(f"logic {parentInterfacePort}_next_pready;\n")
    out.append(f"{parentDataSt} {parentInterfacePort}_next_prdata, prdata;\n")
    out.append(f"logic {parentInterfacePort}_next_pslverr, pslverr;\n")
    out.append("always_comb begin\n")
    out.append(f"{indent}{parentInterfacePort}_next_pready  = '0;\n")
    out.append(f"{indent}{parentInterfacePort}_next_prdata  = '0;\n")
    out.append(f"{indent}{parentInterfacePort}_next_pslverr = '0;\n")
    first = 0
    for item in childInterfacePorts:
        if first == 0:
            out.append(f"{indent}if ({item['name']}_psel) begin\n")
            out.append(f"{indent*2}{parentInterfacePort}_next_pready  = {item['name']}.pready;\n")
            out.append(f"{indent*2}{parentInterfacePort}_next_prdata  = {item['name']}.prdata;\n")
            out.append(f"{indent*2}{parentInterfacePort}_next_pslverr = {item['name']}.pslverr;\n")
        else:
            out.append(f" else if ({item['name']}_psel) begin\n")
            out.append(f"{indent*2}{parentInterfacePort}_next_pready  = {item['name']}.pready;\n")
            out.append(f"{indent*2}{parentInterfacePort}_next_prdata  = {item['name']}.prdata;\n")
            out.append(f"{indent*2}{parentInterfacePort}_next_pslverr = {item['name']}.pslverr;\n")
        out.append(f"{indent}end")
        first += 1
    out.append("\nend\n\n")

    # Retun the parent APB signals
    out.append(f"`DFF(pready, {parentInterfacePort}_next_pready)\n")
    out.append(f"`DFF(prdata, {parentInterfacePort}_next_prdata)\n")
    out.append(f"`DFF(pslverr, {parentInterfacePort}_next_pslverr)\n")
    out.append(f"assign {parentInterfacePort}.pready  = pready;\n")
    out.append(f"assign {parentInterfacePort}.prdata  = prdata;\n")
    out.append(f"assign {parentInterfacePort}.pslverr = pslverr;\n")

    out.append("\n")

    out.append(f"endmodule: {data['blockName']}")
    return ("".join(out))

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
