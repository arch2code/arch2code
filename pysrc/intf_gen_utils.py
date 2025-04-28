# Interfaces Definition

# FIXME Add extra space in templated instances < > to match existing
# Remove when refactoring
LEGACY_COMPAT_MODE = False

from pysrc.interfaces_defs import INTF_DEFS

def sv_gen_modport_signal_blast(port_data, prj_data, swap_dir=False):
    out = {}

    intf_data = port_data['interfaceData']
    intf_type = intf_data['interfaceType']
    intf_name = port_data['name']
    intf_modp = port_data['direction']
    intf_param = dict()

    assert(intf_type in INTF_DEFS and
           intf_modp in INTF_DEFS[intf_type]['modports'])

    intf_def = INTF_DEFS[intf_type]

    if swap_dir :
        intf_modp = inverse_portdir(intf_modp)

    out['description'] = intf_data['desc']

    # Parameter
    for param in filter(lambda item: intf_def['parameters'][item]['datatype'] == 'struct', intf_def['parameters']):
        struct_data = list(filter(lambda item: item['structureType'] == param, intf_data['structures']))
        assert(len(struct_data) == 1); # expecting one exact match
        intf_param[param] = struct_data[0]

    # Interface parameters declaration
    parameters_decl = ', '.join([".{}({})".format(param, intf_param[param]['structure']) for param in intf_def['parameters']])

    # Interface ports declaration
    intf_ports_decl = ''

    out['intf_decl'] = f"{intf_type}_if #({parameters_decl}) {intf_name}({intf_ports_decl});"

    out['intf_modp'] = intf_modp

    # Blasted interface ports
    out['ports'] = []
    for intf_sig in intf_def['signals']:
        modp_signals = intf_def['modports'][intf_modp]
        port_dir = 'input' if intf_sig in modp_signals['inputs'] else 'output'
        port_type = intf_def['signals'][intf_sig]
        port_name = f"{intf_name}_{intf_sig}"
        if port_type in intf_param.keys():
            w = get_struct_width(intf_param[port_type]['structureKey'], prj_data['structures'])
            port_type = 'bit' if w == 1 else f"bit [{w-1}:0]"
        elif port_type == 'bool':
            port_type = 'bit'
        out['ports'].append(f"{port_dir} {port_type} {port_name}")

    # Assignment port <-> interface
    out['assign'] = []
    for intf_sig in intf_def['signals']:
        modp_signals = intf_def['modports'][intf_modp]
        assign_lhs = f"{intf_name}.{intf_sig}" if intf_sig in modp_signals['inputs'] else f"{intf_name}_{intf_sig}"
        assign_rhs = f"{intf_name}_{intf_sig}" if intf_sig in modp_signals['inputs'] else f"{intf_name}.{intf_sig}"
        out['assign'].append(f"assign #0 {assign_lhs} = {assign_rhs};")

    return out

def sc_gen_modport_signal_blast(port_data, prj, swap_dir=False):

    out = {}

    intf_data = port_data['interfaceData']
    intf_type = intf_data['interfaceType']
    intf_name = port_data['name']
    intf_modp = port_data['direction']
    intf_param = dict()

    assert(intf_type in INTF_DEFS and
           intf_modp in INTF_DEFS[intf_type]['modports'])

    intf_def = INTF_DEFS[intf_type]

    in_scope = port_data['inScope']

    if swap_dir :
        intf_modp = inverse_portdir(intf_modp)

    out['is_skip'] = intf_def.get('skip', False)
    out['in_scope'] = in_scope
    out['multicycle_types'] = intf_def['sc_channel']['multicycle_types']
    out['description'] = intf_data['desc']
    out['intf_name'] = intf_name

    # Parameter
    for param in filter(lambda item: intf_def['parameters'][item]['datatype'] == 'struct', intf_def['parameters']):
        struct_data = list(filter(lambda item: item['structureType'] == param, intf_data['structures']))
        assert(len(struct_data) == 1); # expecting one exact match
        intf_param[param] = struct_data[0]

    # Interface parameters declaration
    chnl_params = ', '.join(["{}".format(intf_param[param]['structure']) for param in intf_def['parameters']])

    if intf_def['sc_channel']['param_cast']:
        if LEGACY_COMPAT_MODE:
            chnl_params = intf_def['sc_channel']['param_cast'] + ' < ' + chnl_params + ' >'
        else:
            chnl_params = intf_def['sc_channel']['param_cast'] + '<' + chnl_params + '>'

    if LEGACY_COMPAT_MODE:
        if chnl_params == '':
            chnl_params = ' '
        else:
            chnl_params = ' ' + chnl_params + ' '

    chnl_dir = 'in' if intf_modp == 'dst' else 'out'
    chnl_type = intf_def['sc_channel']['type'] + '_channel'
    port_type = intf_def['sc_channel']['type'] + '_' + chnl_dir

    #out['channel_decl'] = f"{chnl_type}<{chnl_params}> {intf_name}_chnl;"
    out['channel_decl'] = f"{chnl_type}<{chnl_params}> {intf_name};"
    out['port_decl'] = f"{port_type}<{chnl_params}> {intf_name};"

    if not in_scope:
        out['channel_decl'] = '//' + out['channel_decl']
        out['port_decl'] = '//' + out['port_decl']

    hdl_intf_type = intf_def['sc_channel']['type'] + '_hdl_if'
    hdl_intf_name = intf_name + '_hdl_if'

    hdl_if_bv_types = []
    for param in intf_def['parameters']:
        w = get_struct_width(intf_param[param]['structureKey'], prj.data['structures'])
        sc_bv_type = 'bool' if w == 1 else f"sc_bv<{w}>"
        hdl_if_bv_types.append(sc_bv_type)

    hdl_if_params = ', '.join(hdl_if_bv_types)

    out['hdl_if_decl'] = f"{hdl_intf_type}<{hdl_if_params}> {hdl_intf_name};"

    chnl_params = ', '.join(["{}".format(intf_param[param]['structure']) for param in intf_def['parameters']] + hdl_if_bv_types)

    chnl_dir = intf_modp
    chnl_type = intf_def['sc_channel']['type'] + '_' + chnl_dir + '_bfm'

    bfm_name = intf_name + '_bfm'

    out['bfm_decl'] = f"{chnl_type}<{chnl_params}> {bfm_name};"
    out['bfm_ctor_init'] = f"{bfm_name}(\"" + bfm_name + "\")"

    out['intf_modp'] = intf_modp

    # Blasted interface ports
    out['dut_ports_decl'] = []
    for intf_sig in intf_def['signals']:
        dut_port_name = f"{intf_name}_{intf_sig}"
        hdl_if_sig_name = f"{hdl_intf_name}.{intf_sig}"
        out['dut_ports_decl'].append(f"dut_hdl->{dut_port_name}({hdl_if_sig_name});")

    # Assignment port <-> interface
    out['assign'] = []
    for intf_sig in intf_def['signals']:
        modp_signals = intf_def['modports'][intf_modp]
        assign_lhs = f"{intf_name}.{intf_sig}" if intf_sig in modp_signals['inputs'] else f"{intf_name}_{intf_sig}"
        assign_rhs = f"{intf_name}_{intf_sig}" if intf_sig in modp_signals['inputs'] else f"{intf_name}.{intf_sig}"
        out['assign'].append(f"assign {assign_lhs} = {assign_rhs};")

    return out

def sc_gen_block_channels(conn_data, prj):

    out = {}

    intf_type = conn_data['interfaceType']
    intf_name = conn_data['interface']
    chnl_name = conn_data['channelName']
    intf_structs = lookup_struct(conn_data['interfaceKey'], prj.data["interfacesstructures"])

    if conn_data['channelCount'] > 1:
        chnl_name += '_' + '_'.join([conn_data['src'], conn_data['dst']])

    intf_param = dict()

    assert(intf_type in INTF_DEFS)

    intf_def = INTF_DEFS[intf_type]

    out['is_skip'] = intf_def.get('skip', False)
    out['multicycle_types'] = intf_def['sc_channel']['multicycle_types']
    out['intf_name'] = intf_name
    out['chnl_name'] = chnl_name

    # Parameter
    for param in filter(lambda item: intf_def['parameters'][item]['datatype'] == 'struct', intf_def['parameters']):
        struct_data = list(filter(lambda item: item['structureType'] == param, intf_structs))
        if len(struct_data) == 0:
            print(f"Interface {intf_name} is {intf_type} and expected structure types {param} not found")
        assert(len(struct_data) == 1); # the structure type on your interface is not the expected type
        intf_param[param] = struct_data[0];

    # Interface parameters declaration
    chnl_params = ', '.join(["{}".format(intf_param[param]['structure']) for param in intf_def['parameters']])

    if intf_def['sc_channel']['param_cast']:
        if LEGACY_COMPAT_MODE:
            chnl_params = intf_def['sc_channel']['param_cast'] + ' < ' + chnl_params + ' >'
        else:
            chnl_params = intf_def['sc_channel']['param_cast'] + '<' + chnl_params + '>'

    if LEGACY_COMPAT_MODE:
        if chnl_params == '':
            chnl_params = ' '
        else:
            chnl_params = ' ' + chnl_params + ' '

    chnl_type = intf_def['sc_channel']['type'] + '_channel'

    #out['channel_decl'] = f"{chnl_type}<{chnl_params}> {chnl_name}_chnl;"
    out['channel_decl'] = f"{chnl_type}<{chnl_params}> {chnl_name};"

    return out

def inverse_portdir(port):
    assert(port in ['src', 'dst'])
    return 'src' if port == 'dst' else 'dst'

def lookup_struct(struct_key, struct_dict):
    return struct_dict.get(struct_key, None)

def get_struct_width(struct_key, struct_dict):
    struct = lookup_struct(struct_key, struct_dict)
    return struct['width'] if struct else 0

def lookup_const(const_key, const_dict):
    return const_dict.get(const_key, None)

def get_const(const_key, const_dict):
    const = lookup_const(const_key, const_dict)
    return const['value'] if const else 0
