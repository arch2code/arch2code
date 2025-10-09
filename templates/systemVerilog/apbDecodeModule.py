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
    out.append("(")

    # Ports
    out.extend(intf_gen_utils.sv_gen_ports(data, prj, indent))

    qualInstance = next(iter(data['instances']))
    addr_decode_data = data['addressDecode']
    address_group_data = addr_decode_data['addressGroupData']
    address_group = addr_decode_data['addressGroup']
    addr_decode_size = address_group_data['addressIncrement'] * address_group_data['maxAddressSpaces']
    addr_decode_mask = addr_decode_size - 1
    reg_intf_addr_st = addr_decode_data['registerBusStructs']['addr_t']
    reg_intf_data_st = addr_decode_data['registerBusStructs']['data_t']
    inst_decode_info = dict()
    for conn, conn_data in data['ports']['connections'].items():
        if conn_data['srcKey'] == qualInstance:
            inst_decode_info[conn_data['dstKey']] = {'offset': prj.data['instances'][conn_data['dstKey']]['offset'],
                                                     'name': conn_data['srcport'],
                                                     'connectionKey': conn}
        else:
            parent_interface_port = conn_data['name']
    for conn, conn_data in data['ports']['connectionMaps'].items():
        if conn_data['direction'] == 'dst':
            parent_interface_port = conn_data['name']
    sorted_keys = sorted(inst_decode_info.keys(), key=lambda k: int(inst_decode_info[k]['offset']), reverse=True)
# for now assume any selection at any address from the parent_interface_port is valid
#   there is no way to check address ranges currently
# need a selection
# need a clear of selection
# selection is held until incoming PREADY from selected port
# flop prdata and pready
# pass pWData and all other signals down without flops

    out.append(f"{reg_intf_addr_st} apb_addr;")
    out.append(f"assign apb_addr = {reg_intf_addr_st}'({parent_interface_port}.paddr) & {reg_intf_addr_st}'(32'h{addr_decode_mask:_x});")

    # Set up parent signals
    t = Template(parent_sig_decl_j2_template)

    out.append(t.render(
        parent = {
            "interfacePort" : parent_interface_port, "addrSt" : reg_intf_addr_st, "dataSt" : reg_intf_data_st
        }
    ))
    out.append('')

    for item in sorted_keys:
        t = Template(child_sig_decl_j2_template)
        out.append(t.render(
            child = {
                "interfacePort" : inst_decode_info[item]['name']
            }
        ))
        out.append('')

    # Set up parent interface for incoming address selection
    out.append(f"always_comb begin")
    for item in sorted_keys:
        out.append(f"{indent}{inst_decode_info[item]['name']}_next_psel = 1'b0;")
    out.append(f"{indent}set_trans_active = 1'b0;")
    out.append(f"{indent}if ({parent_interface_port}.psel & ~trans_active) begin")
    out.append(f"{indent*2}set_trans_active = 1'b1;")
    first = True
    for item in sorted_keys:
        if first:
            out.append(f"{indent*2}if (apb_addr >= {reg_intf_addr_st}'(32'h{int(inst_decode_info[item]['offset']):_x})) begin")
            first = False
        else:
            if (int(inst_decode_info[item]['offset']) == 0 ):
                out.append(f"{indent*2}end else begin")
            else:
                out.append(f"{indent*2}end else if (apb_addr >= {reg_intf_addr_st}'(32'h{int(inst_decode_info[item]['offset']):_x})) begin")
        out.append(f"{indent*3}{inst_decode_info[item]['name']}_next_psel = '1;")
    out.append(f"{indent*2}end")
    out.append(f"{indent}end")
    out.append("end\n")

    out.append(f"logic {parent_interface_port}_next_pready;")
    out.append(f"{reg_intf_data_st} {parent_interface_port}_next_prdata, prdata;")
    out.append(f"logic {parent_interface_port}_next_pslverr, pslverr;")
    out.append("always_comb begin")
    out.append(f"{indent}{parent_interface_port}_next_pready  = '0;")
    out.append(f"{indent}{parent_interface_port}_next_prdata  = '0;")
    out.append(f"{indent}{parent_interface_port}_next_pslverr = '0;")
    first = 0
    for port in sorted_keys:
        item = inst_decode_info[port]
        if first == 0:
            out.append(f"{indent}if ({item['name']}_psel) begin")
            out.append(f"{indent*2}{parent_interface_port}_next_pready  = {item['name']}.pready;")
            out.append(f"{indent*2}{parent_interface_port}_next_prdata  = {item['name']}.prdata;")
            out.append(f"{indent*2}{parent_interface_port}_next_pslverr = {item['name']}.pslverr;")
        else:
            out.append(f"{indent}end else if ({item['name']}_psel) begin")
            out.append(f"{indent*2}{parent_interface_port}_next_pready  = {item['name']}.pready;")
            out.append(f"{indent*2}{parent_interface_port}_next_prdata  = {item['name']}.prdata;")
            out.append(f"{indent*2}{parent_interface_port}_next_pslverr = {item['name']}.pslverr;")
        first += 1
    out.append(f"{indent}end")
    out.append("end\n")

    # Retun the parent APB signals
    out.append(f"`DFF(pready, {parent_interface_port}_next_pready)")
    out.append(f"`DFF(prdata, {parent_interface_port}_next_prdata)")
    out.append(f"`DFF(pslverr, {parent_interface_port}_next_pslverr)")
    out.append(f"assign {parent_interface_port}.pready  = pready;")
    out.append(f"assign {parent_interface_port}.prdata  = prdata;")
    out.append(f"assign {parent_interface_port}.pslverr = pslverr;")

    out.append("")

    out.append(f"endmodule: {data['blockName']}")
    return ("\n".join(out))

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
