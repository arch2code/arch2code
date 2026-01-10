# Interfaces Definition

# FIXME Add extra space in templated instances < > to match existing
# Remove when refactoring
LEGACY_COMPAT_MODE = False

from pysrc.arch2codeHelper import printError

def get_set_intf_types(ifType, block_data):
    """Get set of interface names, resolving any type aliases
    
    Args:
        ifType: Interface type or collection of interface types
        block_data: Block data dict containing interface_type_mappings
    
    Returns:
        Set of canonical interface type names
    """
    return {get_intf_type(intf, block_data) for intf in ifType}

def get_intf_type(ifType, block_data):
    """Resolve interface type alias to canonical interface type
    
    Args:
        ifType: Interface type (may be an alias like 'reg_ro')
        block_data: Block data dict containing interface_type_mappings
    
    Returns:
        Canonical interface type (e.g., 'reg_ro' -> 'status')
    """
    type_mappings = block_data.get('interface_type_mappings', {})
    return type_mappings.get(ifType, ifType)

def get_intf_data(data, prj_data):
    #ret = data.get('interfaceData', data.get('connection', {}).get('interfaceData', None))
    ret = data.get('interfaceData', None)
    if ret:
        return ret
    else:
        #interfaceKey = data.get('interfaceKey', data.get('connection', {}).get('interfaceKey', None))
        interfaceKey = data.get('interfaceKey', None)
        if interfaceKey:
            return prj_data.data['interfaces'].get(interfaceKey, None)
        else:
            ret =  {'structures': [{'structureType': 'data_t', 'structure': data['structure'], 'structureKey': data['structureKey']}],
                    'interfaceType': data['interfaceType'],
                    'desc': data.get('desc', '')}
            # Only add addressStruct if exists
            if data['addressStruct']:
                ret['structures'].append({'structureType': 'addr_t', 'structure': data['addressStruct'], 'structureKey': data['addressStructKey']})
            return ret
def get_channel_name(data):
    channel_base = data["interfaceName"]
    if data.get('channelCount', 0) > 1:
        channel_base = f"{channel_base}_{data['index']}"
    return channel_base

class intfEvalDSL:

    def __init__(self, prj_data, struct_key):
        self.prj_data = prj_data
        self.struct_key = struct_key

    def to_bytes(self):
        w = get_struct_width(self.struct_key, self.prj_data['structures'])
        return w // 8 + (1 if w % 8 != 0 else 0)

def sv_gen_modport_signal_blast(port_data, prj, block_data, swap_dir=False):
    out = {}
    prj_data = prj.data
    connectionData = port_data.get('connection', {})
    intf_data = get_intf_data(connectionData, prj)
    intf_type = get_intf_type(intf_data['interfaceType'], block_data)
    intf_name = port_data['name']
    intf_modp = port_data['direction']
    intf_param = dict()
    hdl_param = dict()

    # Get interface definition from block_data
    interface_defs = block_data.get('interface_defs', {})
    assert(intf_type in interface_defs and
           intf_modp in interface_defs[intf_type]['modports'])

    intf_def = interface_defs[intf_type]

    if swap_dir :
        intf_modp = inverse_portdir(intf_modp)

    out['description'] = intf_data['desc']

    # Parameter
    params = intf_def.get('parameters') or {}
    for param in filter(lambda item: params[item]['datatype'] == 'struct', params):
        struct_data = list(filter(lambda item: item['structureType'] == param, intf_data['structures']))
        assert(len(struct_data) == 1); # expecting one exact match
        intf_param[param] = struct_data[0]

    hdl_params = intf_def.get('hdlparams', {}) or {}
    for param in hdl_params:
        assert(hdl_params[param]['datatype'] in ['integer'])
        if hdl_params[param]['isEval']:
            key, data = hdl_params[param]['value'].split('.')
            if key in intf_param:
                data_obj = intfEvalDSL(prj_data, intf_param[key]['structureKey'])
                eval_str = 'data_obj{}'.format('.' + data)
                hdl_param[param] = eval(eval_str)
                assert(isinstance(hdl_param[param], int))

    # Interface parameters declaration
    parameters_decl = ', '.join([".{}({})".format(param, intf_param[param]['structure']) for param in params])

    # Interface ports declaration
    intf_ports_decl = ''

    out['intf_decl'] = f"{intf_type}_if #({parameters_decl}) {intf_name}({intf_ports_decl});"

    out['intf_modp'] = intf_modp

    # Blasted interface ports
    out['ports'] = []
    for intf_sig in intf_def['signals']:
        modp_signals = intf_def['modports'][intf_modp]['modportGroups']
        # Safely get inputs and outputs lists
        inputs = modp_signals.get('inputs', {}).get('groups', {}) or {}
        port_dir = 'input' if intf_sig in inputs else 'output'
        port_type = intf_def['signals'][intf_sig]['signalType']
        port_name = f"{intf_name}_{intf_sig}"
        if port_type in intf_param.keys():
            w = get_struct_width(intf_param[port_type]['structureKey'], prj_data['structures'])
            port_type = 'bit' if w == 1 else f"bit [{w-1}:0]"
        elif port_type in hdl_param.keys():
            w = hdl_param[port_type]
            port_type = 'bit' if w == 1 else f"bit [{w-1}:0]"
        elif port_type == 'bool':
            port_type = 'bit'
        out['ports'].append(f"{port_dir} {port_type} {port_name}")

    # Assignment port <-> interface
    out['assign'] = []
    for intf_sig in intf_def['signals']:
        modp_signals = intf_def['modports'][intf_modp]['modportGroups']
        # Safely get inputs and outputs lists
        inputs = modp_signals.get('inputs', {}).get('groups', {}) or {}
        assign_lhs = f"{intf_name}.{intf_sig}" if intf_sig in inputs else f"{intf_name}_{intf_sig}"
        assign_rhs = f"{intf_name}_{intf_sig}" if intf_sig in inputs else f"{intf_name}.{intf_sig}"
        out['assign'].append(f"assign #0 {assign_lhs} = {assign_rhs};")

    return out

def sv_gen_ports(data, prj, indent, block_data):
    out = []
    for sourceType in data['ports']:
        for port, port_data in data['ports'][sourceType].items():
            connectionData = port_data.get('connection', {})
            intf_data = get_intf_data(connectionData, prj)
            intf_type = get_intf_type(intf_data['interfaceType'], block_data)
            out.append(f"{indent}{intf_type}_if.{port_data['direction']} {port_data['name']},")
    out.append(f"{indent}input clk, rst_n")
    out.append(");\n")
    return out

def sc_connect_channels(data, indent, block_data):
    out = []
    for channelType in data["connectDouble"]:
        out.extend(sc_connect_channel_type(data["connectDouble"][channelType], indent, block_data))
    return out

def sc_connect_channel_type(data, indent, block_data):
    out = []
    interface_defs = block_data.get('interface_defs', {})
    for key, value in data.items():
        channelBase = get_channel_name(value)
        if (len(value['ends']) > 2):
            intf_type = get_intf_type(value['interfaceType'], block_data)
            multiDst = interface_defs.get(intf_type, {}).get('multiDst', False)
            if not multiDst:
                printError(f"connection {key} has more than 2 ends. Only status interfaces (including ro registers) can have multiple dst connections")
        for end, endvalue in value["ends"].items():
            out.append(f'{indent}{ endvalue["instance"] }->{ endvalue["portName"]}({ channelBase });')
    return out

def sc_instance_includes(data, prj):
    out = []
    includes = dict()
    # create a dict of unique includes
    for key, value in data['subBlockInstances'].items():
        includes[value["instanceType"]] = None
    for include in includes:
        baseInclude = prj.getModuleFilename('blockBase', include, 'hdr')
        out.append(f'#include "{baseInclude}"')
    return out

def sc_gen_modport_signal_blast(port_data, prj, block_data, swap_dir=False):

    out = {}
    connectionData = port_data.get('connection', {})
    intf_data = get_intf_data(connectionData, prj)
    intf_type = get_intf_type(intf_data['interfaceType'], block_data)
    intf_name = port_data['name']
    intf_modp = port_data['direction']
    intf_param = dict()

    # Get interface definition from block_data
    interface_defs = block_data.get('interface_defs', {})
    assert(intf_type in interface_defs and
           intf_modp in interface_defs[intf_type]['modports'])

    intf_def = interface_defs[intf_type]


    if swap_dir :
        intf_modp = inverse_portdir(intf_modp)

    out['is_skip'] = intf_def.get('skip', False)
    out['multicycle_types'] = intf_def['sc_channel']['multicycle_types']
    out['description'] = intf_data['desc']
    out['intf_name'] = intf_name

    # Parameter
    params = intf_def.get('parameters') or {}
    for param in filter(lambda item: params[item]['datatype'] == 'struct', params):
        struct_data = list(filter(lambda item: item['structureType'] == param, intf_data['structures']))
        assert(len(struct_data) == 1); # expecting one exact match
        intf_param[param] = struct_data[0]

    # Interface parameters declaration
    chnl_params = ', '.join(["{}".format(intf_param[param]['structure']) for param in params])

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

    hdl_intf_type = intf_def['sc_channel']['type'] + '_hdl_if'
    hdl_intf_name = intf_name + '_hdl_if'

    hdl_if_bv_types = []
    params = intf_def.get('parameters') or {}
    for param in params:
        w = get_struct_width(intf_param[param]['structureKey'], prj.data['structures'])
        sc_bv_type = 'bool' if w == 1 else f"sc_bv<{w}>"
        hdl_if_bv_types.append(sc_bv_type)
    hdl_params = intf_def.get('hdlparams', {}) or {}
    for param in hdl_params:
        assert(hdl_params[param]['datatype'] in ['integer'])
        if hdl_params[param]['isEval']:
            key, data = hdl_params[param]['value'].split('.')
            if key in intf_param:
                data_obj = intfEvalDSL(prj.data, intf_param[key]['structureKey'])
                eval_str = 'data_obj{}'.format('.' + data)
                w = eval(eval_str)
                assert(isinstance(w, int))
                sc_bv_type = 'bool' if w == 1 else f"sc_bv<{w}>"
                hdl_if_bv_types.append(sc_bv_type)

    hdl_if_params = ', '.join(hdl_if_bv_types)

    out['hdl_if_decl'] = f"{hdl_intf_type}<{hdl_if_params}> {hdl_intf_name};"

    chnl_params = ', '.join(["{}".format(intf_param[param]['structure']) for param in params] + hdl_if_bv_types)

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
        modp_signals = intf_def['modports'][intf_modp]['modportGroups']
        # Safely get inputs and outputs lists
        inputs = modp_signals.get('inputs', {}).get('groups', {}) or {}
        outputs = modp_signals.get('outputs', {}).get('groups', {}) or {}
        assign_lhs = f"{intf_name}.{intf_sig}" if intf_sig in inputs else f"{intf_name}_{intf_sig}"
        assign_rhs = f"{intf_name}_{intf_sig}" if intf_sig in inputs else f"{intf_name}.{intf_sig}"
        out['assign'].append(f"assign {assign_lhs} = {assign_rhs};")

    return out

def sc_gen_block_channels(conn_data, prj, block_data):

    out = {}

    intf_type = get_intf_type(conn_data['interfaceType'], block_data)
    intf_data = get_intf_data(conn_data, prj)
    chnl_name = get_channel_name(conn_data)
    intf_structs = intf_data['structures']
    intf_param = dict()

    # Get interface definition from block_data
    interface_defs = block_data.get('interface_defs', {})
    assert(intf_type in interface_defs)

    intf_def = interface_defs[intf_type]

    out['is_skip'] = intf_def.get('skip', False)
    out['multicycle_types'] = intf_def['sc_channel']['multicycle_types']
    out['intf_name'] = chnl_name
    out['chnl_name'] = chnl_name
    out['desc'] = intf_data['desc']
    out['set_initial_value'] = intf_def['sc_channel'].get('set_initial_value', False) and 'register' in conn_data
    out['default_value'] = conn_data.get('defaultValue', 0)

    # Parameter
    parameters = intf_def.get('parameters', {}) or {}
    for param in filter(lambda item: parameters[item]['datatype'] == 'struct', parameters):
        struct_data = list(filter(lambda item: item['structureType'] == param, intf_structs))
        if len(struct_data) == 0:
            print(f"Interface {chnl_name} is {intf_type} and expected structure types {param} not found")
        assert(len(struct_data) == 1) # the structure type on your interface is not the expected type
        intf_param[param] = struct_data[0]

    # Interface parameters declaration
    chnl_params = ', '.join(["{}".format(intf_param[param]['structure']) for param in parameters])

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


def sc_declare_channels(data, prj, indent, block_data):
    out = []
    for channelType in data["connectDouble"]:
        for key, value in data["connectDouble"][channelType].items():
            chnlInfo = sc_gen_block_channels(value, prj, block_data)
            if not chnlInfo['is_skip']:
                out.append(f'{indent}// {chnlInfo["desc"]}')
                out.append(indent + chnlInfo['channel_decl'])
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

def get_sorted_memories(data):
    if 'memoriesParent' in data:
        memoryKey = 'memoriesParent'
    else:
        memoryKey = 'memories'
    mems = dict(filter(lambda x: x[1]['regAccess'], data[memoryKey].items()))
    mems = dict(sorted(mems.items(), key=lambda item: item[1]["offset"]))
    return mems

def get_intf_defs(intf_type, block_data):
    """Get interface definition for given interface type
    
    Args:
        intf_type: Interface type name
        block_data: Block data dict containing interface_defs
    
    Returns:
        Interface definition dict or None if not found
    """
    interface_defs = block_data.get('interface_defs', {})
    return interface_defs.get(intf_type, None)