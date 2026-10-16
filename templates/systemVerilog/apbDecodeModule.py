from pysrc.systemVerilogGeneratorHelper import moduleDeclaration, importPackages
from templates.systemVerilog.package import moduleParameterDecl, parameterizedDeclLines
import pysrc.intf_gen_utils as intf_gen_utils

from jinja2 import Template

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    out = []
    indentSize = 4
    indent = ' ' * indentSize

    # Module declaration is emitted from the project-qualified module name;
    # filename/block consistency is validated by the generator before rendering.
    out.append(moduleDeclaration(data['blockSvModuleName']))

    # Packages
    startingContext = data['blockInfo']['_context']
    out.append(importPackages(args, prj, startingContext, data))

    # Parameters
    if ( data['blockInfo']['params'] ):
        out.append('#(')
        out.append(",\n".join([f"{indent}{moduleParameterDecl(prj, param)}" for param in data['blockInfo']['params']]))
        out.append(')')

    out.append("(")

    # The router's ports keep their declared names, like any other block's;
    # its parent binds them to the container nets. Every flop below runs on
    # the declared port carrying the register bus (busClockPort/busResetPort).
    decode_clk = data['busClockPort']
    decode_rst = data['busResetPort']

    # Ports
    out.extend(intf_gen_utils.sv_gen_ports(data, prj, indent))

    # Module-local parameterizable type/struct declarations. SV cannot
    # parameterize a package, so a parameterized router declares the
    # types/structs sized from its own module parameters here.
    if data['parameterizedDecls']:
        out.append(f"{indent}// Module-local parameterizable type/struct declarations")
        for entry in parameterizedDeclLines(data['parameterizedDecls'], prj, data['blockInfo']['params']):
            out.append(f"{indent}{entry['line']}")
        out.append("")

    qualInstance = next(iter(data['instances']))
    addr_decode_data = data['addressDecode']
    address_group_data = addr_decode_data['addressGroupData']
    addr_decode_size = address_group_data['addressIncrement'] * address_group_data['maxAddressSpaces']
    addr_decode_mask = addr_decode_size - 1
    reg_intf_addr_st = addr_decode_data['registerBusStructs']['addr_t']['structure']
    reg_intf_data_st = addr_decode_data['registerBusStructs']['data_t']['structure']
    child_ports = dict()
    for conn_data in data['ports']['connections'].values():
        if conn_data['srcKey'] == qualInstance:
            child_ports[conn_data['dstKey']] = conn_data['srcport']
        else:
            parent_interface_port = conn_data['name']
    for conn_data in data['ports']['connectionMaps'].values():
        if conn_data['direction'] == 'dst':
            parent_interface_port = conn_data['name']
    # Decode arms as (start address, child key), highest start first. A range
    # no child covers is an arm with child None that selects nothing, so the
    # response mux falls through to 32'hBADD_C0DE and the write is dropped.
    inst_decode_info = dict()
    decode_arms = []
    next_free = 0
    for instanceData in addr_decode_data['routedInstances']:
        item = instanceData['instanceKey']
        if item not in child_ports:
            continue
        offset = instanceData['offset']
        inst_decode_info[item] = {'name': child_ports[item]}
        if offset > next_free:
            decode_arms.append((next_free, None))
        decode_arms.append((offset, item))
        next_free = offset + address_group_data['addressIncrement'] * instanceData['addressMultiples']
    if next_free < addr_decode_size:
        decode_arms.append((next_free, None))
    decode_arms.reverse()
    sorted_keys = list(reversed(inst_decode_info))
    has_gap = len(decode_arms) > len(sorted_keys)

    out.append(f"{reg_intf_addr_st} apb_addr;")
    out.append(f"assign apb_addr = {reg_intf_addr_st}'({parent_interface_port}.paddr) & {reg_intf_addr_st}'(32'h{addr_decode_mask:_x});")

    # Set up parent signals
    t = Template(parent_sig_decl_j2_template)

    out.append(t.render(
        parent = {
            "interfacePort" : parent_interface_port, "addrSt" : reg_intf_addr_st, "dataSt" : reg_intf_data_st,
            "clk" : decode_clk, "rst" : decode_rst
        }
    ))
    out.append('')

    for item in sorted_keys:
        t = Template(child_sig_decl_j2_template)
        out.append(t.render(
            child = {
                "interfacePort" : inst_decode_info[item]['name'],
                "clk" : decode_clk, "rst" : decode_rst
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
    if len(decode_arms) == 1:
        # A single child needs no address compare: whatever address the
        # parent selected on, that child is the only place it can go.
        item = sorted_keys[0]
        out.append(f"{indent*2}{inst_decode_info[item]['name']}_next_psel = '1;")
    else:
        for index, (start, item) in enumerate(decode_arms):
            if index == 0:
                out.append(f"{indent*2}if (apb_addr >= {reg_intf_addr_st}'(32'h{start:_x})) begin")
            elif index == len(decode_arms) - 1:
                out.append(f"{indent*2}end else begin")
            else:
                out.append(f"{indent*2}end else if (apb_addr >= {reg_intf_addr_st}'(32'h{start:_x})) begin")
            if item is None:
                out.append(f"{indent*3}// unmapped, selects no child")
            else:
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
    if has_gap:
        # trans_active with no child selected and no response yet is an
        # unmapped access. A child's select clears on its pready, the edge
        # that registers pready, so ~pready excludes that last clock.
        out.append(f"{indent}end else if (trans_active & ~pready) begin")
        out.append(f"{indent*2}{parent_interface_port}_next_pready  = 1'b1;")
        out.append(f"{indent*2}{parent_interface_port}_next_prdata  = {reg_intf_data_st}'(32'hBADD_C0DE);")
    out.append(f"{indent}end")
    out.append("end\n")

    # Retun the parent APB signals
    out.append(f"`DFF_DOM({decode_clk}, {decode_rst}, pready, {parent_interface_port}_next_pready)")
    out.append(f"`DFF_DOM({decode_clk}, {decode_rst}, prdata, {parent_interface_port}_next_prdata)")
    out.append(f"`DFF_DOM({decode_clk}, {decode_rst}, pslverr, {parent_interface_port}_next_pslverr)")
    out.append(f"assign {parent_interface_port}.pready  = pready;")
    out.append(f"assign {parent_interface_port}.prdata  = prdata;")
    out.append(f"assign {parent_interface_port}.pslverr = pslverr;")

    out.append("")

    out.append(f"endmodule: {data['blockSvModuleName']}")
    return ("\n".join(out))

#------------------------------------------------------------------------------
# Jinja2 templates
#------------------------------------------------------------------------------

parent_sig_decl_j2_template = """\
//signals for interface {{ parent.interfacePort }}
{{ parent.addrSt }} paddr_q;
`DFF_DOM({{ parent.clk }}, {{ parent.rst }}, paddr_q, {{ parent.interfacePort }}.paddr)
{{ parent.dataSt }} pwdata_q;
`DFF_DOM({{ parent.clk }}, {{ parent.rst }}, pwdata_q, {{ parent.interfacePort }}.pwdata)
logic penable_q;
`DFF_DOM({{ parent.clk }}, {{ parent.rst }}, penable_q, {{ parent.interfacePort }}.penable)
logic pwrite_q;
`DFF_DOM({{ parent.clk }}, {{ parent.rst }}, pwrite_q, {{ parent.interfacePort }}.pwrite)

logic pready;
logic set_trans_active;
logic trans_active;
`SCFF_DOM({{ parent.clk }}, {{ parent.rst }}, trans_active, set_trans_active, pready)
"""

child_sig_decl_j2_template = """\
//signals for interface {{ child.interfacePort }}
logic {{ child.interfacePort }}_psel;
logic {{ child.interfacePort }}_next_psel;
`SCFF_DOM({{ child.clk }}, {{ child.rst }}, {{ child.interfacePort }}_psel, {{ child.interfacePort }}_next_psel, {{ child.interfacePort }}.pready)

assign {{ child.interfacePort }}.paddr   = paddr_q;
assign {{ child.interfacePort }}.penable = penable_q & {{ child.interfacePort }}_psel;
assign {{ child.interfacePort }}.psel    = {{ child.interfacePort }}_psel;
assign {{ child.interfacePort }}.pwrite  = pwrite_q;
assign {{ child.interfacePort }}.pwdata  = pwdata_q;
"""
