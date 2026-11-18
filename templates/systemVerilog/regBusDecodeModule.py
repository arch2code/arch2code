from pysrc.systemVerilogGeneratorHelper import moduleDeclaration, importPackages
from templates.systemVerilog.package import moduleParameterDecl, parameterizedDeclLines
import pysrc.intf_gen_utils as intf_gen_utils

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

    # Every protocol signal comes from the front end; this core decodes the
    # captured address into a child select and muxes the child responses.
    frontEnd = intf_gen_utils.sv_reg_bus_front_end(data)
    upstream = frontEnd.decoderUpstream(parent_interface_port, reg_intf_addr_st, reg_intf_data_st,
                                        addr_decode_mask, decode_clk, decode_rst)
    downstream = {item: frontEnd.decoderDownstream(inst_decode_info[item]['name'], decode_clk, decode_rst)
                  for item in sorted_keys}
    response = frontEnd.decoderResponse(parent_interface_port, reg_intf_data_st, decode_clk, decode_rst)
    bus_addr = upstream['addr']

    out.extend(upstream['lines'])
    for item in sorted_keys:
        out.extend(downstream[item]['lines'])

    # Set up parent interface for incoming address selection
    out.append(f"always_comb begin")
    for item in sorted_keys:
        out.append(f"{indent}{downstream[item]['selectNext']} = 1'b0;")
    out.append(f"{indent}{upstream['accept']} = 1'b0;")
    out.append(f"{indent}if ({upstream['start']}) begin")
    out.append(f"{indent*2}{upstream['accept']} = 1'b1;")
    if len(decode_arms) == 1:
        # A single child needs no address compare: whatever address the
        # parent selected on, that child is the only place it can go.
        item = sorted_keys[0]
        out.append(f"{indent*2}{downstream[item]['selectNext']} = '1;")
    else:
        for index, (start, item) in enumerate(decode_arms):
            if index == 0:
                out.append(f"{indent*2}if ({bus_addr} >= {reg_intf_addr_st}'(32'h{start:_x})) begin")
            elif index == len(decode_arms) - 1:
                out.append(f"{indent*2}end else begin")
            else:
                out.append(f"{indent*2}end else if ({bus_addr} >= {reg_intf_addr_st}'(32'h{start:_x})) begin")
            if item is None:
                out.append(f"{indent*3}// unmapped, selects no child")
            else:
                out.append(f"{indent*3}{downstream[item]['selectNext']} = '1;")
        out.append(f"{indent*2}end")
    out.append(f"{indent}end")
    out.append("end\n")

    # Response assignments, the names padded to one width
    width = max(len(response[field]) for field in ('ready', 'rdata', 'error'))
    def respond(field, value):
        return f"{response[field].ljust(width)} = {value};"

    out.extend(response['declLines'])
    out.append("always_comb begin")
    out.append(indent + respond('ready', "'0"))
    out.append(indent + respond('rdata', "'0"))
    out.append(indent + respond('error', "'0"))
    for index, item in enumerate(sorted_keys):
        child = downstream[item]
        out.append(f"{indent}{'if' if index == 0 else 'end else if'} ({child['selected']}) begin")
        out.append(indent*2 + respond('ready', child['ready']))
        out.append(indent*2 + respond('rdata', child['rdata']))
        out.append(indent*2 + respond('error', child['error']))
    if has_gap:
        # An outstanding access with no child selected and no response yet
        # is unmapped.
        out.append(f"{indent}end else if ({upstream['pending']}) begin")
        out.append(indent*2 + respond('ready', "1'b1"))
        out.append(indent*2 + respond('rdata', f"{reg_intf_data_st}'(32'hBADD_C0DE)"))
        if prj.config.getConfig('FILEGENERATION')['regBusErrorResponses']:
            out.append(indent*2 + respond('error', "1'b1"))
    out.append(f"{indent}end")
    out.append("end\n")

    out.extend(response['driveLines'])

    out.append("")

    out.append(f"endmodule: {data['blockSvModuleName']}")
    return ("\n".join(out))
