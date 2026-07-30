from pysrc.systemVerilogGeneratorHelper import importPackages
from pysrc.arch2codeHelper import printError, warningAndErrorReport, clog2
from templates.systemVerilog.package import parameterizedDeclLines

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

    regs_intf = data['addressDecode'].get('registerBusPort', None)
    if not regs_intf:
        printError("In your address Config file registerBusPort is not defined")
        exit(warningAndErrorReport())

    regs_addr_t = data['addressDecode']['registerBusStructs'].get('addr_t', None)
    regs_data_t = data['addressDecode']['registerBusStructs'].get('data_t', None)

    # Pre-conditioning of the register data
    for reg_key, reg_data in data['registers'].items():
        reg_data['bitwidth'] = intf_gen_utils.get_struct_width(reg_data['structureKey'], prj.data['structures'])
        # A register is parameterizable iff its storage structure is. Its
        # storage is then the variant-width module-local struct and its
        # per-word data flops/slices are elaborated away per variant via
        # generate, while the worst-case address footprint (segments) stays.
        reg_data['isParameterizable'] = prj.data['structures'][reg_data['structureKey']]['isParameterizable']
        reg_data['segments'] = list(segment_register_gen(reg_data, REG_BUS_WIDTH_BYTES, prj.getConst(reg_data['defaultValue']) if reg_data.get('regType') == 'rw' else 0))
        
        # For memory registers, compute memory-specific fields
        if reg_data.get('regType') == 'memory':
            reg_data['rowwidth'] = clog2(len(reg_data['segments']) * REG_BUS_WIDTH_BYTES)
            # decodeSize is the worst-case decoded address range in bytes,
            # persisted by projectCreate's calcAddresses. The template no
            # longer derives it from wordLines * 2^rowwidth.
            reg_data['memsize'] = reg_data['decodeSize']
            addr_l = reg_data['offset']
            addr_h = addr_l + reg_data['memsize'] - REG_BUS_WIDTH_BYTES
            reg_data['address_range'] = (addr_l, addr_h)
            reg_data['addr_const_name'] = address_const_name(data, reg_data, 'register')
            reg_data['size_const_name'] = reg_data['addr_const_name'] + '_SIZE'
            reg_data['decode_size'] = reg_data['memsize']
        else:
            reg_data['addr_const_name'] = address_const_name(data, reg_data, 'register')

    # Pre-conditioning of the memory data, when existing
    if 'memoriesParent' in data:
        ctxt_memories = dict()
        for mem_key, mem_data in data['memoriesParent'].items():
            entry = dict(mem_data)
            entry['bitwidth'] = intf_gen_utils.get_struct_width(mem_data['structureKey'], prj.data['structures'])
            entry['isParameterizable'] = prj.data['structures'][mem_data['structureKey']]['isParameterizable']
            entry['segments'] = list(segment_register_gen(entry, REG_BUS_WIDTH_BYTES, 0))
            entry['rowwidth'] = clog2(len(entry['segments']) * REG_BUS_WIDTH_BYTES)
            # decodeSize is the worst-case decoded address range in bytes,
            # persisted by projectCreate's calcAddresses.
            entry['memsize'] = entry['decodeSize']
            entry['address_range'] = ( entry['segments'][0][0], entry['segments'][0][0] + entry['memsize'] - REG_BUS_WIDTH_BYTES )
            entry['addr_const_name'] = address_const_name(data, entry, 'memory')
            entry['size_const_name'] = entry['addr_const_name'] + '_SIZE'
            entry['decode_size'] = entry['memsize']
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
        modulename=data['blockModuleName'],
        packages_imports=section_package_imports(args, prj, data),
        module_params=section_module_params(prj, data),
        param_decls=section_param_decls(prj, data),
        needs_genvar=any(r.get('isParameterizable') for r in data['registers'].values())
                     or any(m.get('isParameterizable') for m in data['memories'].values()),
        interfaces_ports=section_intf_ports(prj, data),
        address_mask=section_address_mask(prj, data),
        address_constants=section_address_constants(data),
        regs_intf=regs_intf,
        regs_addr_t=regs_addr_t,
        regs_data_t=regs_data_t,
        section_01=section_01(data),
        section_02a=section_02a(data),
        section_02b=section_02b(data),
        section_03a=section_03a(data),
        section_03b=section_03b(data)
    ))

def address_const_name(data, entry, name_field):
    block_name = entry.get('block', data['blockName'])
    return f"REG_{block_name.upper()}_{entry[name_field].upper()}"

def sv_hex(value):
    return f"32'h{value:08x}"

def section_package_imports(args, prj, data):
    startingContext = prj.data['blocks'][prj.getQualBlock(data['blockName'])]['_context']
    return importPackages(args, prj, startingContext, data)

def section_module_params(prj, data):
    # Inherited module parameters (a reg handler inherits its parent block's
    # params). Emitted byte-identical to the owning module's header so a
    # parameterized handler can declare variant-width module-local storage.
    qualBlock = prj.getQualBlock(data['blockName'])
    params = prj.data['blocks'][qualBlock]['params']
    if not params:
        return ""
    return string_joiner(
        [ f"parameter {param['param']}," for param in params ], '\n')

def section_param_decls(prj, data):
    # Module-local parameterizable type/struct declarations, ordered
    # types-before-structs by orderIndex (deriveParameterizedDeclSets). These
    # are the same decls the owning module emits; they are module-local because
    # SV cannot parameterize a package. Empty for a non-parameterized handler
    # block, whose owning block has no params.
    if not data['parameterizedDecls']:
        return ""
    qualBlock = prj.getQualBlock(data['blockName'])
    return string_joiner([entry['line'] for entry in parameterizedDeclLines(data['parameterizedDecls'], prj, prj.data['blocks'][qualBlock]['params'])], '\n')

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

def section_address_constants(data):
    entries = []
    for reg_data in data['registers'].values():
        entries.append((reg_data['offset'], reg_data['addr_const_name'], sv_hex(reg_data['offset']), reg_data.get('desc', '')))
        if reg_data.get('regType') == 'memory':
            entries.append((reg_data['offset'], reg_data['size_const_name'], sv_hex(reg_data['decode_size']), 'Decode range size'))
    for mem_data in data['memories'].values():
        entries.append((mem_data['offset'], mem_data['addr_const_name'], sv_hex(mem_data['offset']), mem_data.get('desc', '')))
        entries.append((mem_data['offset'], mem_data['size_const_name'], sv_hex(mem_data['decode_size']), 'Decode range size'))

    out = []
    seen = set()
    for _, name, value, desc in sorted(entries, key=lambda item: (item[0], item[1])):
        if name in seen:
            continue
        seen.add(name)
        comment = f" // {desc}" if desc else ""
        out.append(f"localparam int unsigned {name} = {value};{comment}")
    return string_joiner(out, '\n')

def segment_addr_expr(addr_const_name, base_offset, segment_offset):
    delta = segment_offset - base_offset
    if delta == 0:
        return addr_const_name
    return f"{addr_const_name} + 32'd{delta}"

# Signals declarations, flops and continous assignments
def section_01(data):
    # Separate regular registers from memory registers
    regular_regs = {k: v for k, v in data['registers'].items() if v.get('regType') != 'memory'}
    memory_regs = {k: v for k, v in data['registers'].items() if v.get('regType') == 'memory'}
    
    return (string_joiner(
            [section_01_regs(reg_data) for _, reg_data in regular_regs.items()] +
            [section_01_mems(mem_data) for _, mem_data in data['memories'].items()] +
            [section_01_memregs(reg_data) for _, reg_data in memory_regs.items()], '\n\n')
    )

def width_lp_name(intf):
    return intf.upper() + '_W'

def top_lp_name(intf):
    return intf.upper() + '_TOP'

def param_word_generate(reg_intf, struct, width_lp, max_words, flop_macro, flop_src, rword_src):
    # Emit a generate loop over the worst-case words. Present words get their
    # variant-width data flop (when flop_macro is set) and 32-bit read view;
    # absent words (narrow variant) are elaborated away and read 0. The decode
    # always_comb only ever touches the fixed-width <intf>_rword/_update arrays,
    # so no parameterized part-select appears outside this guard.
    reg_local = reg_intf + '_reg'
    reset_arg = ", '0" if flop_macro == 'DFFREN' else ''  # DFFREN takes a reset value, DFFEN does not
    s = []
    s += [ f"generate" ]
    s += [ f"    for (gi = 0; gi < {max_words}; gi++) begin : g_{reg_intf}" ]
    s += [ f"        if ({width_lp} > 32*gi) begin : present" ]
    s += [ f"            if ({width_lp} >= 32*(gi+1)) begin : full" ]
    if flop_macro:
        s += [ f"                `{flop_macro}({reg_local}[32*gi +: 32], {flop_src}[31:0], {reg_intf}_update[gi]{reset_arg})" ]
    s += [ f"                assign {reg_intf}_rword[gi] = {rword_src}[32*gi +: 32];" ]
    s += [ f"            end else begin : partial" ]
    if flop_macro:
        s += [ f"                `{flop_macro}({reg_local}[32*gi +: ({width_lp}-32*gi)], {flop_src}[{width_lp}-32*gi-1:0], {reg_intf}_update[gi]{reset_arg})" ]
    s += [ f"                assign {reg_intf}_rword[gi] = 32'({rword_src}[32*gi +: ({width_lp}-32*gi)]);" ]
    s += [ f"            end" ]
    s += [ f"        end else begin : absent" ]
    s += [ f"            assign {reg_intf}_rword[gi] = '0; // absent word reads 0" ]
    s += [ f"        end" ]
    s += [ f"    end" ]
    s += [ f"endgenerate" ]
    return s

def section_01_regs_param(reg_data):
    reg_intf = reg_data['register']
    reg_local = reg_intf + '_reg'
    struct = reg_data['structure']
    width_lp = width_lp_name(reg_intf)
    max_words = len(reg_data['segments'])

    s = [ f"{struct} {reg_local};" ]
    s += [ f"localparam int unsigned {width_lp} = $bits({struct});" ]
    s += [ f"logic [31:0] {reg_intf}_rword [0:{max_words-1}];" ]
    if reg_data['regType'] == 'rw':
        s += [ f"logic [{max_words-1}:0] {reg_intf}_update;" ]
        s += [ f"assign {reg_intf}.data = {reg_local};" ]
        s += param_word_generate(reg_intf, struct, width_lp, max_words, 'DFFREN',
                                 f"{regs_intf}.pwdata", reg_local)
    else: # ro
        s += [ f"assign {reg_local} = {reg_intf}.data;" ]
        s += param_word_generate(reg_intf, struct, width_lp, max_words, None,
                                 None, reg_local)
    return string_joiner(s, '\n')

def section_01_regs(reg_data):
    if reg_data['isParameterizable'] and reg_data['regType'] in ('rw', 'ro'):
        return section_01_regs_param(reg_data)

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
    elif reg_data['regType'] == 'memory':
        # Memory registers are handled separately, no assignment needed
        s_2 = []
    else:
        s_2 = []

    s_3, s_4 = [], []
    for seg in segments_enum:
        n, (o, u, l, w, d) = seg
        update_sig = f"{reg_local}_update_{n}"
        if reg_data['regType'] == 'rw':
            s_3 += [ f"logic {update_sig};" ]
            s_4 += [ f"`DFFREN({reg_local}[{u}:{l}], {regs_intf}.pwdata[{w-1}:0], {update_sig}, {w}'h{d:08x})" ]

    return string_joiner(s_1 + s_3 + s_2 + s_4, '\n')

def section_01_mem_param(mem_intf, mem_data):
    """Parameterizable memory/memory-register: variant-width line storage,
    per-word data flops elaborated away per variant, worst-case address
    footprint. mem_intf is the channel name ('memory' or 'register')."""
    struct = mem_data['structure']
    addr_struct = mem_data['addressStruct']
    width_lp = width_lp_name(mem_intf)
    top_lp = top_lp_name(mem_intf)
    max_words = len(mem_data['segments'])
    rowwidth = mem_data['rowwidth']
    mem_local = mem_intf + '_reg'

    s = [ f"// {mem_intf}" ]
    s += [ f"{struct} {mem_local};" ]
    s += [ f"localparam int unsigned {width_lp} = $bits({struct});" ]
    s += [ f"localparam int unsigned {top_lp} = ({width_lp}-1)/32; // top present word for this variant" ]
    s += [ f"logic [{max_words-1}:0] {mem_intf}_update;" ]
    s += [ f"logic [31:0] {mem_intf}_rword [0:{max_words-1}];" ]
    s += [ f"{addr_struct} {mem_intf}_addr;" ]
    s += [ f"logic nxt_{mem_intf}_rd_enable, {mem_intf}_rd_enable, {mem_intf}_rd_capture;" ]
    s += [ f"logic {mem_intf}_wr_enable;" ]
    s += [ "" ]
    s += [ f"`DFF({mem_intf}_addr, {addr_struct}'(apb_addr[31:{rowwidth}]))" ]
    s += [ f"`DFF({mem_intf}_wr_enable, {mem_intf}_update[{top_lp}])" ]
    s += [ f"`DFF({mem_intf}_rd_enable, nxt_{mem_intf}_rd_enable)" ]
    s += [ f"`DFF({mem_intf}_rd_capture, {mem_intf}_rd_enable)" ]
    s += [ "" ]
    s += param_word_generate(mem_intf, struct, width_lp, max_words, 'DFFEN',
                             f"{regs_intf}.pwdata", f"{mem_intf}.read_data")
    s += [ "" ]
    s += [ f"assign {mem_intf}.enable      = {mem_intf}_rd_enable | {mem_intf}_wr_enable;" ]
    s += [ f"assign {mem_intf}.wr_en       = {mem_intf}_wr_enable;" ]
    s += [ f"assign {mem_intf}.addr        = {mem_intf}_addr;" ]
    s += [ f"assign {mem_intf}.write_data  = {mem_local};" ]
    return string_joiner(s, '\n')

def section_01_memregs(reg_data):
    """Handle memory register declarations similar to external memories"""
    if reg_data['isParameterizable']:
        return section_01_mem_param(reg_data['register'], reg_data)

    mem_intf = reg_data['register']

    t = Template(section_01_mem_j2_template)

    return(t.render(
        mem_intf=mem_intf,
        mem_datatype=reg_data['structure'],
        mem_addrtype=reg_data['addressStruct'],
        segments=reg_data['segments'],
        paddr_l = reg_data['rowwidth'],
        seg_last = len(reg_data['segments']) - 1
    ))

def section_01_mems(mem_data):
    if mem_data['isParameterizable']:
        return section_01_mem_param(mem_data['memory'], mem_data)

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
    # Separate regular registers from memory registers
    regular_regs = {k: v for k, v in data['registers'].items() if v.get('regType') != 'memory'}
    memory_regs = {k: v for k, v in data['registers'].items() if v.get('regType') == 'memory'}
    
    return (string_joiner(
            [section_02a_regs(reg_data) for _, reg_data in regular_regs.items()] +
            [section_02a_mems(mem_data) for _, mem_data in data['memories'].items()] +
            [section_02a_memregs(reg_data) for _, reg_data in memory_regs.items()], '\n')
    )

def section_02a_regs(reg_data):
    reg_intf = reg_data['register']
    reg_local = reg_data['register'] + '_reg'

    if reg_data['isParameterizable'] and reg_data['regType'] == 'rw':
        return f"{reg_intf}_update = '0;"
    if reg_data['isParameterizable'] and reg_data['regType'] == 'ro':
        return ''

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

def section_02a_memregs(reg_data):
    """Init logic for memory registers"""
    mem_intf = reg_data['register']
    data_local = reg_data['register'] + '_data'

    if reg_data['isParameterizable']:
        return f"{mem_intf}_update = '0;"

    segments_enum = list(enumerate(reg_data['segments']))
    
    s_1 = []
    
    for seg in segments_enum:
        n, (o, u, l, w, _) = seg
        update_sig = f"{mem_intf}_update_{n}"
        s_1 += [ f"{update_sig} = 1'b0;" ]
    
    s_1 += [ f"nxt_{data_local} = {data_local};" ]
    
    return string_joiner(s_1, '\n')

def section_02a_mems(mem_data):
    mem_intf = mem_data['memory']
    data_local = mem_data['memory'] + '_data'

    if mem_data['isParameterizable']:
        return f"{mem_intf}_update = '0;"

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
    # Separate regular registers from memory registers
    regular_regs = {k: v for k, v in data['registers'].items() if v.get('regType') != 'memory'}
    memory_regs = {k: v for k, v in data['registers'].items() if v.get('regType') == 'memory'}
    
    return (string_joiner(
            [section_02b_regs(reg_data) for _, reg_data in regular_regs.items()] +
            [section_02b_mems(mem_data) for _, mem_data in data['memories'].items()] +
            [section_02b_memregs(reg_data) for _, reg_data in memory_regs.items()], '\n')
    )

def section_02b_regs(reg_data):
    reg_intf = reg_data['register']
    reg_local = reg_data['register'] + '_reg'

    segments_enum = list(enumerate(reg_data['segments']))

    if reg_data['isParameterizable']:
        # rw only writes; ro has no write strobes (a write falls through to the
        # always-ACK global default and is silently ignored). One top-level case
        # entry per worst-case word drives the _update vector; the flop it
        # gates is elaborated away for absent words, so the strobe is harmless.
        s_1 = []
        if reg_data['regType'] == 'rw':
            for seg in segments_enum:
                n, (o, _u, _l, _w, _) = seg
                addr_expr = segment_addr_expr(reg_data['addr_const_name'], reg_data['offset'], o)
                s_1 += [ f"{addr_expr} : begin" ]
                s_1 += [ f"    {reg_intf}_update[{n}] = 1'b1;" ]
                s_1 += [ "end" ]
        return string_joiner(s_1, '\n')

    s_1 = []
    for seg in segments_enum:
        n, (o, u, l, w, _) = seg
        addr_expr = segment_addr_expr(reg_data['addr_const_name'], reg_data['offset'], o)
        if reg_data['regType'] == 'rw':
            s_1 += [ f"{addr_expr} : begin" ]
            s_1 += [ f"    {reg_local}_update_{n} = 1'b1;" ]
            s_1 += [ "end" ]
        elif reg_data['regType'] == 'ext':
            s_1 += [ f"{addr_expr} : begin" ]
            s_1 += [ f"    {reg_intf}.write = {1<<n};" ]
            for s_seg in segments_enum:
                _, (_, s_u, s_l, _, _) = s_seg
                if s_seg == seg:
                    s_1 += [ f"    {reg_intf}.wdata[{s_u}:{s_l}] = {regs_intf}.pwdata[{w-1}:0];" ]
                else:
                    s_1 += [ f"    {reg_intf}.wdata[{s_u}:{s_l}] = {reg_intf}.rdata[{s_u}:{s_l}];" ]
            s_1 += [ "end" ]

    return string_joiner(s_1, '\n')

def section_02b_mem_param(mem_intf, mem_data):
    """Parameterizable memory write decode: the variant-width data flop reads
    pwdata directly inside the generate, so the write case only drives the
    per-word _update strobe vector. Absent words ACK via the always-on ready."""
    addr_l, _ = mem_data['address_range']
    rowwidth = mem_data['rowwidth']
    s_1 = []
    s_1 += [ f"[{mem_data['addr_const_name']}:{mem_data['addr_const_name']} + {mem_data['size_const_name']} - 32'd{REG_BUS_WIDTH_BYTES}]: begin" ]
    s_1 += [ f"    case (apb_addr[{rowwidth-1}:0])" ]
    for seg in list(enumerate(mem_data['segments'])):
        n, (o, _u, _l, _w, _) = seg
        o_rel = o - addr_l
        s_1 += [ f"        {rowwidth}'h{o_rel:x}: {mem_intf}_update[{n}] = 1'b1;" ]
    s_1 += [ f"        default: ;" ]
    s_1 += [ f"    endcase" ]
    s_1 += [ f"end" ]
    return string_joiner(s_1, '\n')

def section_02b_memregs(reg_data):
    """Write case decode for memory registers"""
    mem_intf = reg_data['register']
    data_local = 'nxt_' + reg_data['register'] + '_data'

    segments_enum = list(enumerate(reg_data['segments']))

    addr_l, _ = reg_data['address_range']
    rowwidth = reg_data['rowwidth']

    if reg_data['isParameterizable']:
        return section_02b_mem_param(mem_intf, reg_data)

    s_1 = []

    s_1 += [ f"[{reg_data['addr_const_name']}:{reg_data['addr_const_name']} + {reg_data['size_const_name']} - 32'd{REG_BUS_WIDTH_BYTES}]: begin" ]
    s_1 += [ f"    case (apb_addr[{rowwidth}-1:0])" ]
    for seg in segments_enum:
        n, (o, u, l, w, _) = seg
        o_rel = o - addr_l  # offset relative to base of mem mod bus width
        s_1 += [ f"        {rowwidth}'h{o_rel:x}: begin" ]
        s_1 += [ f"            {mem_intf}_update_{n} = 1'b1;" ]
        s_1 += [ f"            {data_local}[{u}:{l}] = {regs_intf}.pwdata[{w-1}:0];" ]
        s_1 += [ f"        end" ]
    s_1 +=     [ f"        default: ;" ]
    s_1 += [ f"    endcase" ]
    s_1 += [ f"end" ]
    
    return string_joiner(s_1, '\n')

def section_02b_mems(mem_data):
    mem_intf = mem_data['memory']
    data_local = 'nxt_' + mem_data['memory'] + '_data'

    if mem_data['isParameterizable']:
        return section_02b_mem_param(mem_intf, mem_data)

    segments_enum = list(enumerate(mem_data['segments']))

    addr_l, _ = mem_data['address_range']

    s_1 = []

    s_1 += [ f"[{mem_data['addr_const_name']}:{mem_data['addr_const_name']} + {mem_data['size_const_name']} - 32'd{REG_BUS_WIDTH_BYTES}]: begin" ]
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
    memory_regs = {k: v for k, v in data['registers'].items() if v.get('regType') == 'memory'}
    
    return (string_joiner(
            [section_03a_mems(mem_data) for _, mem_data in data['memories'].items()] +
            [section_03a_memregs(reg_data) for _, reg_data in memory_regs.items()], '\n')
    )

def section_03a_mems(mem_data):
    mem_intf = mem_data['memory']
    enable_sig = f"nxt_{mem_intf}_rd_enable"

    s_1 = [ f"{enable_sig} = 1'b0;" ]

    return string_joiner(s_1, '\n')

def section_03a_memregs(reg_data):
    """Read init for memory registers"""
    mem_intf = reg_data['register']
    enable_sig = f"nxt_{mem_intf}_rd_enable"
    
    s_1 = [ f"{enable_sig} = 1'b0;" ]
    
    return string_joiner(s_1, '\n')

# read comb case core
def section_03b(data):
    regular_regs = {k: v for k, v in data['registers'].items() if v.get('regType') != 'memory'}
    memory_regs = {k: v for k, v in data['registers'].items() if v.get('regType') == 'memory'}
    
    return (string_joiner(
            [section_03b_regs(reg_data) for _, reg_data in regular_regs.items()] +
            [section_03b_mems(mem_data) for _, mem_data in data['memories'].items()] +
            [section_03b_memregs(reg_data) for _, reg_data in memory_regs.items()], '\n')
    )

def section_03b_regs(reg_data):
    reg_intf = reg_data['register']
    reg_local = reg_data['register'] + '_reg'

    segments_enum = list(enumerate(reg_data['segments']))

    if reg_data['isParameterizable']:
        # One top-level case entry per worst-case word, reading the precomputed
        # 32-bit _rword array (absent words read 0). No parameterized slice
        # appears in always_comb.
        s_1 = []
        for seg in segments_enum:
            n, (o, _u, _l, _w, _) = seg
            addr_expr = segment_addr_expr(reg_data['addr_const_name'], reg_data['offset'], o)
            s_1 += [ f"{addr_expr} : begin" ]
            s_1 += [ f"    nxt_rd_ready = 1'b1;" ]
            s_1 += [ f"    nxt_rd_data = {regs_data_t}'({reg_intf}_rword[{n}]);" ]
            s_1 += [ "end" ]
        return string_joiner(s_1, '\n')

    s_1 = []
    for seg in segments_enum:
        n, (o, u, l, w, _) = seg
        update_sig = f"{reg_local}_update_{n}"
        addr_expr = segment_addr_expr(reg_data['addr_const_name'], reg_data['offset'], o)
        if reg_data['regType'] in [ 'ro', 'rw', 'ext' ]:
            s_1 += [ f"{addr_expr} : begin" ]
            s_1 += [ f"    nxt_rd_ready = 1'b1;" ]
            s_1 += [ f"    nxt_rd_data = {regs_data_t}'({reg_local}[{u}:{l}]);" ]
            s_1 += [ "end" ]

    return string_joiner(s_1, '\n')

def section_03b_mem_param(mem_intf, mem_data):
    """Parameterizable memory read decode: select the precomputed 32-bit
    _rword views (absent words are '0). Range + inner per-word case."""
    addr_l, _ = mem_data['address_range']
    rowwidth = mem_data['rowwidth']
    word_offsets = []
    s_1 = []
    s_1 += [ f"[{mem_data['addr_const_name']}:{mem_data['addr_const_name']} + {mem_data['size_const_name']} - 32'd{REG_BUS_WIDTH_BYTES}]: begin" ]
    s_1 += [ f"    case (apb_addr[{rowwidth-1}:0])" ]
    for seg in list(enumerate(mem_data['segments'])):
        n, (o, _u, _l, _w, _) = seg
        o_rel = o - addr_l
        word_offsets.append(f"{rowwidth}'h{o_rel:x}")
        s_1 += [ f"        {rowwidth}'h{o_rel:x}: begin" ]
        s_1 += [ f"            if ({mem_intf}_rd_capture) begin" ]
        s_1 += [ f"                nxt_rd_ready = 1'b1;" ]
        s_1 += [ f"                nxt_rd_data = {regs_data_t}'({mem_intf}_rword[{n}]);" ]
        s_1 += [ f"            end" ]
        s_1 += [ f"        end" ]
    s_1 += [ f"        default: begin" ]
    s_1 += [ f"            nxt_rd_ready = 1'b1;" ]
    s_1 += [ f"            nxt_rd_data = '0;" ]
    s_1 += [ f"        end" ]
    s_1 += [ f"    endcase" ]
    s_1 += [ f"    nxt_{mem_intf}_rd_enable = (apb_addr[{rowwidth-1}:0] inside {{{', '.join(word_offsets)}}}) & ~{mem_intf}_rd_capture;" ]
    s_1 += [ f"end" ]
    return string_joiner(s_1, '\n')

def section_03b_mems(mem_data):
    mem_intf = mem_data['memory']
    data_local = 'nxt_' + mem_data['memory'] + '_data'

    if mem_data['isParameterizable']:
        return section_03b_mem_param(mem_intf, mem_data)

    segments_enum = list(enumerate(mem_data['segments']))

    addr_l, _ = mem_data['address_range']

    s_1 = []

    s_1 += [ f"[{mem_data['addr_const_name']}:{mem_data['addr_const_name']} + {mem_data['size_const_name']} - 32'd{REG_BUS_WIDTH_BYTES}]: begin" ]
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

def section_03b_memregs(reg_data):
    """Read case decode for memory registers"""
    mem_intf = reg_data['register']

    segments_enum = list(enumerate(reg_data['segments']))

    # Use preprocessed address range and rowwidth
    addr_l, _ = reg_data['address_range']
    rowwidth = reg_data['rowwidth']

    if reg_data['isParameterizable']:
        return section_03b_mem_param(mem_intf, reg_data)

    s_1 = []

    s_1 += [ f"[{reg_data['addr_const_name']}:{reg_data['addr_const_name']} + {reg_data['size_const_name']} - 32'd{REG_BUS_WIDTH_BYTES}]: begin" ]
    s_1 += [ f"    case (apb_addr[{rowwidth}-1:0])" ]
    for seg in segments_enum:
        _, (o, u, l, w, _) = seg
        o_rel = o - addr_l  # offset relative to base of mem mod bus width
        s_1 += [ f"        {rowwidth}'h{o_rel:x}: begin" ]
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
        {%- if module_params %}
        {{ module_params | indent(8) }}
        {%- endif %}
        parameter bit APB_READY_1WS = 0
    )
    (
        {{ interfaces_ports | indent(8) }}
        input clk,
        input rst_n
    );

    {%- if param_decls %}
    // Module-local parameterizable type/struct declarations (SV cannot
    // parameterize a package, so these live in the owning module).
    {{ param_decls | indent(4) }}
    {%- endif %}

    {{regs_addr_t}} apb_addr;
    assign apb_addr = {{regs_addr_t}}'({{regs_intf}}.paddr) & {{ address_mask }};

    {%- if address_constants %}
    // Register/memory address offsets for decode documentation
    {{ address_constants | indent(4) }}
    {%- endif %}

    {%- if needs_genvar %}

    genvar gi;
    {%- endif %}

    {{ section_01 | indent(4) }}

    logic wr_select;
    logic rd_select;
    assign wr_select = {{regs_intf}}.psel & {{regs_intf}}.penable & {{regs_intf}}.pwrite & rst_n;
    assign rd_select = {{regs_intf}}.psel & {{regs_intf}}.penable & !{{regs_intf}}.pwrite & rst_n;

    logic nxt_wr_ready, wr_ready;
    always_comb begin
        nxt_wr_ready = 1'b0;
        {{ section_02a | indent(8) }}
        if (wr_select) begin
            case (apb_addr) inside
                {{ section_02b | indent(16) }}
                default: ; // unmapped/ro write: silently ignored (ACK below)
            endcase
            nxt_wr_ready = 1'b1;
        end
    end

    logic nxt_rd_ready, rd_ready;
    {{regs_data_t}} nxt_rd_data, rd_data;
    always_comb begin
        nxt_rd_ready = 1'b0;
        nxt_rd_data = '0;
        {{ section_03a | indent(8) }}
        if (rd_select) begin
            case (apb_addr) inside
                {{ section_03b | indent(16) }}
                default: begin // unmapped read: ACK with 0 (never stall, never error)
                    nxt_rd_ready = 1'b1;
                    nxt_rd_data = '0;
                end
            endcase
        end
    end

    // Update APB ready and read data. The bus is never stalled and slave
    // error is never asserted: every access ACKs, unmapped reads return 0.
    generate if (APB_READY_1WS)
        begin
            `DFFR(wr_ready,   nxt_wr_ready,   '0)
            `DFFR(rd_ready,   nxt_rd_ready,   '0)
            `DFFR(rd_data,    nxt_rd_data,    '0)
        end else begin
            assign wr_ready   = nxt_wr_ready;
            assign rd_ready   = nxt_rd_ready;
            assign rd_data    = nxt_rd_data;
        end
    endgenerate

    // Update the APB interface
    assign {{regs_intf}}.prdata  = rd_data;
    assign {{regs_intf}}.pready  = rd_ready | wr_ready;
    assign {{regs_intf}}.pslverr = 1'b0;

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
