from xml.etree.ElementTree import indent
from pysrc.systemVerilogGeneratorHelper import importPackages
from pysrc.arch2codeHelper import printError, warningAndErrorReport, clog2

import pysrc.intf_gen_utils as intf_gen_utils

from jinja2 import Template

REG_BUS_WIDTH_BYTES = 4

def getParentStructures(prj, d):
    for item in d['structures']:
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
    global regs_intf, regs_addr_t, regs_data_t

    regs_intf = data['addressDecode'].get('registerBusInterface', None)
    if not regs_intf:
        printError("In your address Config file registerBusInterface is not defined")
        exit(warningAndErrorReport())

    regs_addr_t = data['addressDecode']['registerBusStructs'].get('addr_t', None)
    regs_data_t = data['addressDecode']['registerBusStructs'].get('data_t', None)

    # Pre-conditioning of the register data
    for reg_key, reg_data in data['registers'].items():
        reg_data['bitwidth'] = intf_gen_utils.get_struct_width(reg_data['structureKey'], prj.data['structures'])
        reg_data['segments'] = list(segment_register_gen(reg_data, REG_BUS_WIDTH_BYTES, prj.getConst(reg_data['defaultValue'])))

    # Pre-conditioning of the memory data, when existing
    if 'memoriesParent' in data:
        ctxt_memories = dict()
        for mem_key, mem_data in data['memoriesParent'].items():
            entry = dict(mem_data)
            entry['bitwidth'] = intf_gen_utils.get_struct_width(mem_data['structureKey'], prj.data['structures'])
            entry['segments'] = list(segment_register_gen(entry, REG_BUS_WIDTH_BYTES, 0))
            entry['rowwidth'] = clog2(len(entry['segments']) * REG_BUS_WIDTH_BYTES)
            entry['memsize'] = prj.getConst(entry['wordLinesKey']) * (2** entry['rowwidth'])
            entry['address_range'] = ( entry['segments'][0][0], entry['segments'][0][0] + entry['memsize'] - REG_BUS_WIDTH_BYTES )
            ctxt_memories[mem_key] = entry
        data['memories'] = ctxt_memories

    # TODO extend support beyond 8-bytes wide for external registers
    for reg_key, reg_data in data['registers'].items():
        unsup_ = False
        if reg_data['regType'] == 'ext' and len(reg_data['segments']) * REG_BUS_WIDTH_BYTES > 8 :
            printError(f"External register {reg_data['register']} > 8 bytes is not supported by current generator")
            unsupp_ = True
        if unsup_:
            warningAndErrorReport()

    t = Template(regs_module_sv_j2_template)

    return(t.render(
        modulename=data['blockName'],
        packages_imports=section_package_imports(args, prj, data),
        interfaces_ports=section_intf_ports(prj, data),
        address_mask=section_address_mask(prj, data),
        regs_intf=regs_intf,
        regs_addr_t=regs_addr_t,
        regs_data_t=regs_data_t,
        section_01=section_01(data),
        section_02a=section_02a(data),
        section_02b=section_02b(data),
        section_03a=section_03a(data),
        section_03b=section_03b(data)
    ))

def section_package_imports(args, prj, data):
    startingContext = prj.data['blocks'][prj.getQualBlock(data['blockName'])]['_context']
    return importPackages(args, prj, startingContext, data)

def section_intf_ports(prj, data):

    out = []
    # Ports
    for sourceType in data['ports']:
        for port, port_data in data['ports'][sourceType].items():
            connectionData = port_data.get('connection', {})
            intf_data = intf_gen_utils.get_intf_data(connectionData, prj)
            intf_type = intf_gen_utils.get_intf_type(intf_data['interfaceType'], data)
            out.append(f"{intf_type}_if.{port_data['direction']} {port_data['name']},")


    return string_joiner(out, '\n')

def section_address_mask(prj, data):
    mask = (1<<(int(data['addressDecode']['addressBits'])))-1
    return f"32'h{mask:_x}"

# Signals declarations, flops and continous assignments
def section_01(data):
    return (string_joiner(
            [section_01_regs(reg_data) for _, reg_data in data['registers'].items()] +
            [section_01_mems(mem_data) for _, mem_data in data['memories'].items()], '\n\n')
    )

def section_01_regs(reg_data):
    reg_intf = reg_data['register']
    reg_local = reg_data['register'] + '_reg'

    segments_enum = list(enumerate(reg_data['segments']))

    s_1 = [ f"{reg_data['structure']} {reg_local};" ]

    if reg_data['regType'] == 'ro':
        s_2 = [ f"assign {reg_local} = {reg_intf}.data;" ]
    elif reg_data['regType'] == 'rw':
        s_2 = [ f"assign {reg_intf}.data = {reg_local};" ]
    elif reg_data['regType'] == 'ext':
        s_2 = [ f"assign {reg_local} = {reg_intf}.rdata;" ]

    s_3, s_4 = [], []
    for seg in segments_enum:
        n, (o, u, l, w, d) = seg
        update_sig = f"{reg_local}_update_{n}"
        if reg_data['regType'] == 'rw':
            s_3 += [ f"logic {update_sig};" ]
            s_4 += [ f"`DFFREN({reg_local}[{u}:{l}], {regs_intf}.pwdata[{w-1}:0], {update_sig}, {w}'h{d:08x})" ]

    return string_joiner(s_1 + s_3 + s_2 + s_4, '\n')

def section_01_mems(mem_data):

    t = Template(section_01_mem_j2_template)

    return(t.render(
        mem_intf=mem_data['memory'],
        mem_datatype=mem_data['structure'],
        mem_addrtype=mem_data['addressStruct'],
        segments=mem_data['segments'],
        paddr_l = mem_data['rowwidth'],
        seg_last = len(mem_data['segments']) - 1
    ))

# write comb case init
def section_02a(data):
    return (string_joiner(
            [section_02a_regs(reg_data) for _, reg_data in data['registers'].items()] +
            [section_02a_mems(mem_data) for _, mem_data in data['memories'].items()], '\n')
    )

def section_02a_regs(reg_data):
    reg_intf = reg_data['register']
    reg_local = reg_data['register'] + '_reg'

    segments_enum = list(enumerate(reg_data['segments']))

    s_1 = []

    if reg_data['regType'] == 'ext':
        s_1 += [ f"{reg_intf}.write = '0;" ]
        s_1 += [ f"{reg_intf}.wdata = '0;" ]

    for seg in segments_enum:
        n, (o, u, l, w, _) = seg
        update_sig = f"{reg_local}_update_{n}"
        if reg_data['regType'] == 'rw':
            s_1 += [ f"{update_sig} = 1'b0;" ]

    return string_joiner(s_1, '\n')

def section_02a_mems(mem_data):
    mem_intf = mem_data['memory']
    data_local = mem_data['memory'] + '_data'

    segments_enum = list(enumerate(mem_data['segments']))

    s_1 = []

    for seg in segments_enum:
        n, (o, u, l, w, _) = seg
        update_sig = f"{mem_intf}_update_{n}"
        s_1 += [ f"{update_sig} = 1'b0;" ]

    s_1 += [ f"nxt_{data_local} = {data_local};" ]

    return string_joiner(s_1, '\n')

# write comb case core
def section_02b(data):
    return (string_joiner(
            [section_02b_regs(reg_data) for _, reg_data in data['registers'].items()] +
            [section_02b_mems(mem_data) for _, mem_data in data['memories'].items()], '\n')
    )

def section_02b_regs(reg_data):
    reg_intf = reg_data['register']
    reg_local = reg_data['register'] + '_reg'

    segments_enum = list(enumerate(reg_data['segments']))

    s_1 = []
    for seg in segments_enum:
        n, (o, u, l, w, _) = seg
        if reg_data['regType'] == 'rw':
            s_1 += [ f"32'h{o:x} : begin" ]
            s_1 += [ f"    {reg_local}_update_{n} = 1'b1;" ]
            s_1 += [ "end" ]
        elif reg_data['regType'] == 'ext':
            s_1 += [ f"32'h{o:x} : begin" ]
            s_1 += [ f"    {reg_intf}.write = {1<<n};" ]
            for s_seg in segments_enum:
                _, (_, s_u, s_l, _, _) = s_seg
                if s_seg == seg:
                    s_1 += [ f"    {reg_intf}.wdata[{s_u}:{s_l}] = {regs_intf}.pwdata[{w-1}:0];" ]
                else:
                    s_1 += [ f"    {reg_intf}.wdata[{s_u}:{s_l}] = {reg_intf}.rdata[{s_u}:{s_l}];" ]
            s_1 += [ "end" ]

    return string_joiner(s_1, '\n')

def section_02b_mems(mem_data):
    mem_intf = mem_data['memory']
    data_local = 'nxt_' + mem_data['memory'] + '_data'

    segments_enum = list(enumerate(mem_data['segments']))

    addr_l, addr_h = mem_data['address_range']

    s_1 = []

    s_1 += [ f"[32'h{addr_l:x}:32'h{addr_h:x}]: begin" ]
    s_1 += [ f"    case (apb_addr[{mem_data['rowwidth']-1}:0])" ]
    for seg in segments_enum:
        n, (o, u, l, w, _) = seg
        o -= addr_l # offset relative to base of mem mod bus width
        s_1 += [ f"        {mem_data['rowwidth']}'h{o:x}: begin" ]
        s_1 += [ f"            {mem_intf}_update_{n} = 1'b1;" ]
        s_1 += [ f"            {data_local}[{u}:{l}] = {regs_intf}.pwdata[{w-1}:0];" ]
        s_1 += [ f"        end" ]
    s_1 +=     [ f"        default: ;" ]
    s_1 += [ f"    endcase" ]
    s_1 += [ f"end" ]

    return string_joiner(s_1, '\n')

# read comb case init
def section_03a(data):
    return (string_joiner(
            [section_03a_mems(mem_data) for _, mem_data in data['memories'].items()], '\n')
    )

def section_03a_mems(mem_data):
    mem_intf = mem_data['memory']
    enable_sig = f"nxt_{mem_intf}_rd_enable"

    s_1 = [ f"{enable_sig} = 1'b0;" ]

    return string_joiner(s_1, '\n')

# read comb case core
def section_03b(data):
    return (string_joiner(
            [section_03b_regs(reg_data) for _, reg_data in data['registers'].items()] +
            [section_03b_mems(mem_data) for _, mem_data in data['memories'].items()], '\n')
    )

def section_03b_regs(reg_data):
    reg_intf = reg_data['register']
    reg_local = reg_data['register'] + '_reg'

    segments_enum = list(enumerate(reg_data['segments']))

    s_1 = []
    for seg in segments_enum:
        n, (o, u, l, w, _) = seg
        update_sig = f"{reg_local}_update_{n}"
        if reg_data['regType'] in [ 'ro', 'rw', 'ext' ]:
            s_1 += [ f"32'h{o:x} : begin" ]
            s_1 += [ f"    nxt_rd_ready = 1'b1;" ]
            s_1 += [ f"    nxt_rd_data = {regs_data_t}'({reg_local}[{u}:{l}]);" ]
            s_1 += [ "end" ]

    return string_joiner(s_1, '\n')

def section_03b_mems(mem_data):
    mem_intf = mem_data['memory']
    data_local = 'nxt_' + mem_data['memory'] + '_data'

    segments_enum = list(enumerate(mem_data['segments']))

    addr_l, addr_h = mem_data['address_range']

    s_1 = []

    s_1 += [ f"[32'h{addr_l:x}:32'h{addr_h:x}]: begin" ]
    s_1 += [ f"    case (apb_addr[{mem_data['rowwidth']-1}:0])" ]
    for seg in segments_enum:
        n, (o, u, l, w, _) = seg
        o -= addr_l # offset relative to base of mem mod bus width
        s_1 += [ f"        {mem_data['rowwidth']}'h{o:x}: begin" ]
        s_1 += [ f"            if ({mem_intf}_rd_capture) begin" ]
        s_1 += [ f"                nxt_rd_ready = 1'b1;" ]
        s_1 += [ f"                nxt_rd_data = {regs_data_t}'({mem_intf}.read_data[{u}:{l}]);" ]
        s_1 += [ f"            end" ]
        s_1 += [ f"        end" ]
    s_1 +=     [ f"        default: ;" ]
    s_1 += [ f"    endcase" ]
    s_1 += [ f"    nxt_{mem_intf}_rd_enable = ~{mem_intf}_rd_capture;" ]
    s_1 += [ f"end" ]

    return string_joiner(s_1, '\n')

# generator yields quadruplets segments split at bus_width_bytes
# (addr-offset, bit-upper, bit-lower, bit-width, reset-value)
def segment_register_gen(reg_data, bus_width_bytes, default_value):
    offset = reg_data['offset']
    bitwidth = reg_data['bitwidth']
    bus_width = bus_width_bytes * 8
    (o,u,l,w,r) = (offset, 0, 0, 0, bitwidth)
    while r > 0:
      w = bus_width if r >= bus_width else r
      u = w + l - 1
      d = (default_value >> l) & ((1<<w)-1)
      seg = (o, u, l, w, d)
      l = u + 1
      o += bus_width_bytes
      r -= w
      yield seg


def string_joiner(l:[], join_str='\n', trim_empty=True):
    if trim_empty:
        l = list(filter(lambda x: x != '', l))
    return join_str.join(l)

#------------------------------------------------------------------------------
# Jinja2 templates
#------------------------------------------------------------------------------

# Register access module template
regs_module_sv_j2_template = """\
module {{ modulename }}
{%- if packages_imports %}
    {{ packages_imports | indent(4) }}
{%- endif %}
    #(
        parameter bit APB_READY_1WS = 0
    )
    (
        {{ interfaces_ports | indent(8) }}
        input clk,
        input rst_n
    );

    {{regs_addr_t}} apb_addr;
    assign apb_addr = {{regs_addr_t}}'({{regs_intf}}.paddr) & {{ address_mask }};

    {{ section_01 | indent(4) }}

    logic wr_select;
    logic rd_select;
    assign wr_select = {{regs_intf}}.psel & {{regs_intf}}.penable & {{regs_intf}}.pwrite & rst_n;
    assign rd_select = {{regs_intf}}.psel & {{regs_intf}}.penable & !{{regs_intf}}.pwrite & rst_n;

    logic nxt_wr_pslverr, wr_pslverr;
    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_pslverr = 1'b0;
        nxt_wr_ready = 1'b0;
        {{ section_02a | indent(8) }}
        if (wr_select) begin
            case (apb_addr) inside
                {{ section_02b | indent(16) }}
                default: begin
                    nxt_wr_pslverr = 1'b1;
                end
            endcase
            nxt_wr_ready = 1'b1;
        end
    end

    logic nxt_rd_pslverr, rd_pslverr;
    logic nxt_rd_ready, rd_ready;
    {{regs_data_t}} nxt_rd_data, rd_data;
    always_comb begin
        nxt_rd_pslverr = 1'b0;
        nxt_rd_ready = 1'b0;
        nxt_rd_data = '0;
        {{ section_03a | indent(8) }}
        if (rd_select) begin
            case (apb_addr) inside
                {{ section_03b | indent(16) }}
                default: begin
                    nxt_rd_data = {{regs_data_t}}'(32'hBADD_C0DE);
                    nxt_rd_pslverr = 1'b1;
                end
            endcase
        end
    end

    // Update APB ready, pslverr, and read data
    generate if (APB_READY_1WS)
        begin
            `DFFR(wr_ready,   nxt_wr_ready,   '0)
            `DFFR(wr_pslverr, nxt_wr_pslverr, '0)
            `DFFR(rd_ready,   nxt_rd_ready,   '0)
            `DFFR(rd_data,    nxt_rd_data,    '0)
            `DFFR(rd_pslverr, nxt_rd_pslverr, '0)
        end else begin
            assign wr_ready   = nxt_wr_ready;
            assign wr_pslverr = nxt_wr_pslverr;
            assign rd_ready   = nxt_rd_ready;
            assign rd_data    = nxt_rd_data;
            assign rd_pslverr = nxt_rd_pslverr;
        end
    endgenerate

    // Update the APB interface
    assign {{regs_intf}}.prdata  = rd_data;
    assign {{regs_intf}}.pready  = rd_ready | wr_ready;
    assign {{regs_intf}}.pslverr = rd_pslverr | wr_pslverr;

endmodule : {{ modulename }}
"""

# Section 01 - Signals declarations, flops and continous assignments for memory access
section_01_mem_j2_template = """\
// {{mem_intf}}
{{mem_datatype}} nxt_{{mem_intf}}_data, {{mem_intf}}_data;
{{mem_addrtype}} {{mem_intf}}_addr;

{% for seg in segments -%}
logic {{mem_intf}}_update_{{loop.index0}};
{% endfor -%}
logic nxt_{{mem_intf}}_rd_enable, {{mem_intf}}_rd_enable, {{mem_intf}}_rd_capture;
logic {{mem_intf}}_wr_enable;

`DFF({{mem_intf}}_addr, {{mem_addrtype}}'(apb_addr[31:{{paddr_l}}]))
`DFF({{mem_intf}}_wr_enable, {{mem_intf}}_update_{{seg_last}})
`DFF({{mem_intf}}_rd_enable, nxt_{{mem_intf}}_rd_enable)
`DFF({{mem_intf}}_rd_capture, {{mem_intf}}_rd_enable)

{% for seg in segments -%}{% set ul %}[{{seg[1]}}:{{seg[2]}}]{% endset -%}
`DFFEN({{mem_intf}}_data{{ul}}, nxt_{{mem_intf}}_data{{ul}}, {{mem_intf}}_update_{{loop.index0}})
{% endfor %}
assign {{mem_intf}}.enable      = {{mem_intf}}_rd_enable | {{mem_intf}}_wr_enable;
assign {{mem_intf}}.wr_en       = {{mem_intf}}_wr_enable;
assign {{mem_intf}}.addr        = {{mem_intf}}_addr;
assign {{mem_intf}}.write_data  = {{mem_intf}}_data;
"""
