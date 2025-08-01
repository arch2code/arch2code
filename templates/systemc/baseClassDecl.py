
import textwrap
import pysrc.intf_gen_utils as intf_gen_utils

from pysrc.arch2codeHelper import printError, warningAndErrorReport

# Does not alter the rendering
intf_gen_utils.LEGACY_COMPAT_MODE = True

def render(args, prj, data):

    out = list()

    # A bit of preprocessing to filter out register ports based on block context 
    data['regPorts'] = {k: v for k, v in data['regPorts'].items() if v['interfaceData']['block'] != data['blockName']}

    block_intf_set = set(
        [v['interfaceData']['interfaceType'] for v in data['ports'].values()] +
        [v['interfaceData']['interfaceType'] for v in data['regPorts'].values()] +
        [v['interfaceType'] for v in data['connections'].values()]
    )

    if not block_intf_set:
        out.append('#include "blockBase.h"\n')

    for intfType in sorted(block_intf_set):
        chnlType = intf_gen_utils.INTF_DEFS[intfType]['sc_channel']['type']
        out.append(f'#include "{chnlType}_channel.h"\n')

    if args.fileMapKey:
        fileMapKey = args.fileMapKey
    else:
        fileMapKey = 'include_hdr'

    for context in data['includeContext']:
        if context in data['includeFiles'][fileMapKey]:
            out.append(f'#include "{data["includeFiles"][fileMapKey][context]["baseName"]}"\n')


    out.append('\n')
    blockName = data["blockName"]
    ifMapping = {
        'classNamePostfix' : 'Base',
        'parameter' : 'std::string name, const char * variant',
        'destructor' : f'virtual ~{ blockName }Base() = default;\n',
        'src': 'out',
        'dst': 'in',
        'swap_dir' : False,
        'ctorStringHasParam' : False,
        'addConsts' : True
    }

    out.extend( renderClass(args, prj, data, blockName, ifMapping) )
    blockName = data["blockName"]
    ifMapping = {
        'classNamePostfix' : 'Inverted',
        'parameter' : 'std::string name',
        'destructor' : '',
        'src': 'in',  # swap in and out for inverted class
        'dst': 'out',
        'swap_dir' : True,
        'ctorStringHasParam' : True,
        'addConsts' : False
    }
    out.extend( renderClass(args, prj, data, blockName, ifMapping) )

    out.extend( renderChannels(args, prj, data) )
    if warningAndErrorReport() != 0:
        exit(1)
    return("".join(out))


def renderClass(args, prj, data, blockName, ifMapping):
    out = list()
    className = blockName + ifMapping['classNamePostfix']
    out.append(f'class { className } : public virtual blockPortBase\n')
    out.append('{\n')
    out.append('public:\n')
    indent = ' '*4
    if ifMapping['destructor'] != '':
        out.append( indent + ifMapping['destructor'] )

    if ifMapping['addConsts']:
        if prj.data['blocks'][data['qualBlock']]['params']:
            for param in prj.data['blocks'][data['qualBlock']]['params']:
                out.append(f'    const uint64_t {param["param"]};\n')

    mp_sig = dict()
    for port in data['ports']:
        mp_sig[port] = intf_gen_utils.sc_gen_modport_signal_blast(data['ports'][port], prj, swap_dir=ifMapping['swap_dir'])
    # add condition for including register ports
    regs = dict()
    for port in data['regPorts']:
        regName = data['regPorts'][port]['name']
        if regName not in regs:
            regs[regName] = 0
            mp_sig[port] = intf_gen_utils.sc_gen_modport_signal_blast(data['regPorts'][port], prj, swap_dir=ifMapping['swap_dir'])
            # add the regPort to the ports dict
            data['ports'][port] = data['regPorts'][port]
        else:
            if data['regPorts'][port]['interfaceData']['interfaceType'] != 'status':
                printError(f"Register port {regName} is defined multiple times in block {data['qualBlock']} and not a status interface")
                exit(warningAndErrorReport())
    
    def gen_sc_ports_decl(args, prj, data):
        s = []
        s.append('// src ports')
        for port in filter(lambda p : data['ports'][p]['direction'] == 'src', data['ports'].keys()):
            if mp_sig[port]['is_skip']:
                continue
            intf_data = data['ports'][port]['interfaceData']
            if args.noExternalComments:
                partner_inst = "External"
            else:
                partner_inst = data['ports'][port]['connectionData'].get('dst', "External")
            s.append('// {}->{}: {}'.format(intf_data['interface'], partner_inst, intf_data['desc']))
            s.append(mp_sig[port]['port_decl'])
        s.append('')
        s.append('// dst ports')
        for port in filter(lambda p : data['ports'][p]['direction'] == 'dst', data['ports'].keys()):
            if mp_sig[port]['is_skip']:
                continue
            intf_data = data['ports'][port]['interfaceData']
            if args.noExternalComments:
                partner_inst = "External"
            else:
                partner_inst = data['ports'][port]['connectionData'].get('src', "External")
            s.append('// {}->{}: {}'.format(partner_inst, intf_data['interface'], intf_data['desc']))
            s.append(mp_sig[port]['port_decl'])
        s.append('')
        s = '\n'.join(s)
        return s

    out.append(textwrap.indent(gen_sc_ports_decl(args, prj, data), indent))

    out.append('\n'*2)
    colon = ''
    if len(data['ports']) > 0:
        for key, value in data['ports'].items():
            if value["commentOut"] == '':
                colon = ':'
                break
    out.append( indent + f'{ className }({ ifMapping["parameter"] }) {colon}\n')
    comma = ''
    if ifMapping['ctorStringHasParam']:
        prefix = '('
        postfix = '+name).c_str()'
    else:
        prefix = ''
        postfix = ''
    if ifMapping['addConsts']:
        if prj.data['blocks'][data['qualBlock']]['params']:
            for param in prj.data['blocks'][data['qualBlock']]['params']:
                out.append(f'        {comma}{param["param"]}(instanceFactory::getParam("{ blockName }", variant, "{param["param"]}"))\n')
                comma = ','

    # loop twice for c++ constructor init ordering reasons
    for key, value in data['ports'].items():
        if mp_sig[key]['is_skip']:
            continue
        if value['direction'] == 'src':
            out.append(f'        { value  ["commentOut"] }{comma}{ value["name"] }({prefix}"{ value["name"] }"{postfix})\n')
            if value["commentOut"] == '':
                comma = ','
    for key, value in data['ports'].items():
        if mp_sig[key]['is_skip']:
            continue
        if value['direction'] == 'dst':
            out.append(f'        { value  ["commentOut"] }{comma}{ value["name"] }({prefix}"{ value["name"] }"{postfix})\n')
            if value["commentOut"] == '':
                comma = ','
    out.append( indent + '{};\n')

    out.append( indent + f'void setTimed(int nsec, timedDelayMode mode) override\n')
    out.append( indent + '{\n')
    # loop twice for cleanliness with other parts
    for key, value in data['ports'].items():
        if mp_sig[key]['is_skip']:
            continue
        if value['direction'] == 'src':
            out.append(f'        { value  ["commentOut"] }{ value["name"] }->setTimed(nsec, mode);\n')
    for key, value in data['ports'].items():
        if mp_sig[key]['is_skip']:
            continue
        if value['direction'] == 'dst':
            out.append(f'        { value  ["commentOut"] }{ value["name"] }->setTimed(nsec, mode);\n')
    out.append( indent + '    setTimedLocal(nsec, mode);\n')
    out.append( indent + '};\n')
    out.append( indent + f'void setLogging(verbosity_e verbosity) override\n')
    out.append( indent + '{\n')
    # loop twice for cleanliness with other parts
    for key, value in data['ports'].items():
        if mp_sig[key]['is_skip']:
            continue
        if value['direction'] == 'src':
            out.append(f'        { value  ["commentOut"] }{ value["name"] }->setLogging(verbosity);\n')
    for key, value in data['ports'].items():
        if mp_sig[key]['is_skip']:
            continue
        if value['direction'] == 'dst':
            out.append(f'        { value  ["commentOut"] }{ value["name"] }->setLogging(verbosity);\n')
    out.append( indent + '};\n')

    out.append( '};\n')
    return out

def renderChannels(args, prj, data):
    out = list()
    className = data["blockName"] + 'Channels'
    out.append(f'class { className }\n')
    out.append('{\n')
    out.append('public:\n')
    indent = ' '*4

    mp_sig = dict()
    for port in data['ports']:
        mp_sig[port] = intf_gen_utils.sc_gen_modport_signal_blast(data['ports'][port], prj, swap_dir=False)

    def gen_sc_channels_decl(args, prj, data):
        s = []
        s.append('// src ports')
        for port in filter(lambda p : data['ports'][p]['direction'] == 'src', data['ports'].keys()):
            if mp_sig[port]['is_skip']:
                continue
            intf_data = data['ports'][port]['interfaceData']
            s.append('//   {}'.format(intf_data['interface']))
            s.append(mp_sig[port]['channel_decl'])
        s.append('')
        s.append('// dst ports')
        for port in filter(lambda p : data['ports'][p]['direction'] == 'dst', data['ports'].keys()):
            if mp_sig[port]['is_skip']:
                continue
            intf_data = data['ports'][port]['interfaceData']
            s.append('//   {}'.format(intf_data['interface']))
            s.append(mp_sig[port]['channel_decl'])
        s.append('')
        s = '\n'.join(s)
        return s

    out.append(textwrap.indent(gen_sc_channels_decl(args, prj, data), indent))

    out.append('\n'*2)

    colon = ''
    if len(data['ports']) > 0:
        for key, value in data['ports'].items():
            if value["commentOut"] == '':
                colon = ':'
                break
    out.append( indent + f'{ className }(std::string name, std::string srcName) {colon}\n')
    comma = ''
    # loop twice for c++ constructor init ordering reasons
    for key, value in data['ports'].items():
        if mp_sig[key]['is_skip']:
            continue
        if value['direction'] == 'src':
            out.append(indent + value["commentOut"] + comma + channelConstructor(args, prj, data, value, mp_sig[key]['multicycle_types']) + '\n')
            if value["commentOut"] == '':
                comma = ','
    for key, value in data['ports'].items():
        if mp_sig[key]['is_skip']:
            continue
        if value['direction'] == 'dst':
            out.append(indent + value["commentOut"] + comma + channelConstructor(args, prj, data, value, mp_sig[key]['multicycle_types']) + '\n')
            if value["commentOut"] == '':
                comma = ','
    out.append( indent + '{};\n')
    out.append( indent + f'void bind( {data["blockName"]}Base *a, {data["blockName"]}Inverted *b)\n')
    out.append( indent + '{\n')
    indent = indent + ' '*4
    for key, value in data['ports'].items():
        if mp_sig[key]['is_skip']:
            continue
        if value['direction'] == 'src':
            out.append( indent + f'{ value["commentOut"]  }a->{ value["name"] }( { value["name"] } );\n')
            out.append( indent + f'{ value["commentOut"]  }b->{ value["name"] }( { value["name"] } );\n')
    for key, value in data['ports'].items():
        if mp_sig[key]['is_skip']:
            continue
        if value['direction'] == 'dst':
            out.append( indent + f'{ value["commentOut"]  }a->{ value["name"] }( { value["name"] } );\n')
            out.append( indent + f'{ value["commentOut"]  }b->{ value["name"] }( { value["name"] } );\n')
    indent = ' '*4
    out.append( indent +'};\n')
    out.append( '};\n')
    return out
autoModeMapping = {
    "": "",
    "alloc": ", INTERFACE_AUTO_ALLOC",
    "dealloc": ", INTERFACE_AUTO_DEALLOC",
    "allocReq": ", INTERFACE_AUTO_ALLOC, INTERFACE_AUTO_OFF",
    "deallocReq": ", INTERFACE_AUTO_DEALLOC, INTERFACE_AUTO_OFF",
    "allocAck": ", INTERFACE_AUTO_OFF, INTERFACE_AUTO_ALLOC",
    "deallocAck": ", INTERFACE_AUTO_OFF, INTERFACE_AUTO_DEALLOC"
}

def channelConstructor(args, prj, data, line, multicycle_types):
    extra = ''

    # we may have a multicycle interface
    interfaceInfo = line['interfaceData']
    interfaceSize = interfaceInfo.get('maxTransferSize',0)
    trackerType = interfaceInfo.get('trackerType',"")
    multiCycleMode = interfaceInfo.get('multiCycleMode',"")
    tracker = line['connectionData'].get('tracker',"")
    autoMode = autoModeMapping.get(tracker,"")

    if multicycle_types:
        #- fixed_size        #
        #- header_tracker    # for rdyVldBurst tracker tag comes from field in the header (based on field with "generator: tracker(xxx)"" in structures where xxx is the tracker name)
        #- header_size       # for rdyVldBurst size comes from field in the header (based on field with "generator: tracker(length)"" in structures)
        #- api_list_tracker  # tracker tag comes from write api and push_context
        #- api_list_size     # size comes from write api and push_context

        if multiCycleMode != "":
            if multiCycleMode not in multicycle_types:
                printError(f"Interface type does not support multiCycleMode {multiCycleMode}")
                exit(warningAndErrorReport())
            if trackerType != "":
                trackerType = f'tracker:{trackerType}'
            extra = f', "{multiCycleMode}", {interfaceSize}, "{trackerType}"'
        else:
            if interfaceSize != "0" or trackerType:
                print(f"warning: interface {line['interfaceKey']} has a maxTransferSize or trackerType but no multiCycleMode")

    return(f'{ line["name"] }(("{ line["name"] }"+name).c_str(), srcName{extra}{autoMode})')
