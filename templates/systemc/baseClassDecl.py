
import textwrap
import pysrc.intf_gen_utils as intf_gen_utils

from pysrc.arch2codeHelper import printError, warningAndErrorReport

# Does not alter the rendering
intf_gen_utils.LEGACY_COMPAT_MODE = True

def render(args, prj, data):

    out = list()

    block_intf_set = intf_gen_utils.get_set_intf_types(data['interfaceTypes'], data)

    if not block_intf_set:
        out.append('#include "blockBase.h"')

    for intfType in sorted(block_intf_set):
        intf_def = intf_gen_utils.get_intf_defs(intfType, data)
        chnlType = intf_def['sc_channel']['type']
        out.append(f'#include "{chnlType}_channel.h"')

    if args.fileMapKey:
        fileMapKey = args.fileMapKey
    else:
        fileMapKey = 'include_cppm'

    for context in data['includeContext']:
        if context in data['includeFiles'].get(fileMapKey, {}):
            out.extend(intf_gen_utils.cpp_context_include_lines(prj, data, context, fileMapKey))


    isParameterizable = data['isParameterizable']
    # Base/Inverted/Channels companions inherit the parent's "leaf
    # parameterizable" status. A block is a class template only when it
    # declares its own `params:`.
    hasOwnParams = data['hasOwnParams']

    out.append('')
    blockName = data["blockName"]
    ifMapping = {
        'classNamePostfix' : 'Base',
        'parameter' : 'std::string name, const char * variant',
        'destructor' : f'virtual ~{ blockName }Base() = default;',
        'src': 'out',
        'dst': 'in',
        'swap_dir' : False,
        'ctorStringHasParam' : False,
        'addConsts' : True
    }

    out.extend( renderClass(args, prj, data, blockName, ifMapping, hasOwnParams) )
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
    out.extend( renderClass(args, prj, data, blockName, ifMapping, hasOwnParams) )

    out.extend( renderChannels(args, prj, data, hasOwnParams) )

    # No force-link declaration is emitted. Non-templated blocks self-register
    # via an A2C_REGISTRATION_RETAIN static in their own TU (see
    # templates/systemc/constructor.py and instanceFactory.h), reachable
    # through direct-.o linking. Parents and the testbench therefore hold no
    # compile-time symbol reference to the block.

    if warningAndErrorReport() != 0:
        exit(1)
    return("\n".join(out))


def renderClass(args, prj, data, blockName, ifMapping, isParameterizable=False):
    out = list()
    className = blockName + ifMapping['classNamePostfix']
    if isParameterizable:
        out.append('template<typename Config>')
    out.append(f'class { className } : public virtual blockPortBase')
    out.append('{')
    out.append('public:')
    indent = ' '*4
    if ifMapping['destructor'] != '':
        out.append( indent + ifMapping['destructor'] )

    if ifMapping['addConsts']:
        if prj.data['blocks'][data['qualBlock']]['params']:
            # Block params are exposed as compile-time constants drawn from the
            # Config policy. static constexpr (rather than a runtime const member)
            # lets derived/user code use the bare name in constexpr contexts
            # (if constexpr, template/width arguments) after re-importing it.
            for param in prj.data['blocks'][data['qualBlock']]['params']:
                out.append(f'    static constexpr auto {param["param"]} = Config::{param["param"]};')

    mp_sig = dict()
    portNames = dict()
    for sourceType in data['ports']:
        for port, port_data in data['ports'][sourceType].items():
            mp_sig[port] = intf_gen_utils.sc_gen_modport_signal_blast(port_data, prj, data, swap_dir=ifMapping['swap_dir'])
            if port not in portNames:
                portNames[port] = 0
            else:
                if port_data['interfaceData']['interfaceType'] != 'status':
                    printError(f"Port {port} is defined multiple times in block {data['qualBlock']} and not a status interface")
                    exit(warningAndErrorReport())
    # add condition for including register ports
    regs = dict()
    port_count = 0
    def get_sc_if_comment(args, port_type, port_data, intf_data, direction):
        if port_type in ['connections', 'connectionMaps']:
            if args.noExternalComments:
                partner_inst = "External"
            else:
                partner_inst = port_data.get(intf_gen_utils.inverse_portdir(direction), "External")
            ifString = intf_data.get('interface', intf_data.get('interfaceType',''))
            if direction == 'src':
                return (f"// {ifString}->{partner_inst}: {intf_data['desc']}")
            else:
                return (f"// {partner_inst}->{ifString}: {intf_data['desc']}")
        else:
            if port_type == 'registers':
                return (f"// {port_data['connection']['block']}->reg({port_data['connection']['register']}) {port_data['connection']['desc']}")
            if port_type == 'memories':
                return (f"// {port_data['connection']['block']}->mem({port_data['connection']['memory']}) {port_data['connection']['desc']}")
            return (f"//   {port_type}")

    def gen_sc_ports_decl(args, prj, data):
        nonlocal port_count
        s = []
        for direction in ['src', 'dst']:
            section = []
            have_port = False
            section.append(f'// {direction} ports')
            for port_type in data['ports']:
                for port in filter(lambda p : data['ports'][port_type][p]['direction'] == direction, data['ports'][port_type].keys()):
                    if mp_sig[port]['is_skip']:
                        continue
                    have_port = True
                    port_count += 1
                    port_data = data['ports'][port_type][port]
                    intf_data = intf_gen_utils.get_intf_data(port_data['connection'], prj)
                    section.append(get_sc_if_comment(args, port_type, port_data, intf_data, direction))
                    section.append(mp_sig[port]['port_decl'])
            section.append('')
            if have_port:
                s.extend(section)
        s = '\n'.join(s)
        return s

    out.append(textwrap.indent(gen_sc_ports_decl(args, prj, data), indent))

    out.append('')
    # Param constants are static constexpr (see above), so they carry no
    # mem-initialiser; only ports are constructed here.
    colon = ':' if port_count > 0 else ''
    out.append( indent + f'{ className }({ ifMapping["parameter"] }) {colon}')
    comma = ''
    if ifMapping['ctorStringHasParam']:
        prefix = '('
        postfix = '+name).c_str()'
    else:
        prefix = ''
        postfix = ''

    for direction in ['src', 'dst']:
        for port_type in data['ports']:
            for key, value in data['ports'][port_type].items():
                if mp_sig[key]['is_skip']:
                    continue
                if value['direction'] == direction:
                    out.append(f'        {comma}{ value["name"] }({prefix}"{ value["name"] }"{postfix})')
                    comma = ','
    out.append( indent + '{};')

    out.append( indent + f'void setTimed(int nsec, timedDelayMode mode) override')
    out.append( indent + '{')
    # loop twice for cleanliness with other parts
    for direction in ['src', 'dst']:
        for port_type in data['ports']:
            for key, value in data['ports'][port_type].items():
                if mp_sig[key]['is_skip']:
                    continue
                if value['direction'] == direction:
                    out.append(f'        { value["name"] }->setTimed(nsec, mode);')
    out.append( indent + '    setTimedLocal(nsec, mode);')
    out.append( indent + '};')
    out.append( indent + f'void setLogging(verbosity_e verbosity) override')
    out.append( indent + '{')
    for direction in ['src', 'dst']:
        for port_type in data['ports']:
            for key, value in data['ports'][port_type].items():
                if mp_sig[key]['is_skip']:
                    continue
                if value['direction'] == direction:
                    out.append(f'        { value["name"] }->setLogging(verbosity);')
    out.append( indent + '};')

    if ifMapping['addConsts']:
        # Class-local type aliases let derived/user code use the bare type name
        # (no <Config>). Emitted at the END of the class body, AFTER the port
        # declarations above: those ports declare NAME<Config>, and a same-named
        # alias introduced before them would shadow the namespace template and
        # break the port decls. An alias-declaration's own name is not in scope
        # within its right-hand side, so `using NAME = NAME<Config>;` resolves
        # NAME<Config> to the namespace template (brought in via using-namespace).
        for decl in data['parameterizedDecls']:
            name = decl['body'][decl['declKind']]
            # An eval-derived parameterizable constant lives on Config (like a
            # block param); expose it as a class-local compile-time constant drawn
            # from Config so bare-name use resolves, mirroring the block-param
            # constants above. It is a value, not a type, so it takes no <Config>
            # alias.
            if decl['declKind'] == 'constant':
                out.append( indent + f'static constexpr auto {name} = Config::{name};')
            else:
                out.append( indent + f'using {name} = {name}<Config>;')

    out.append( '};')
    return out

def renderChannels(args, prj, data, isParameterizable=False):
    out = list()
    className = data["blockName"] + 'Channels'
    if isParameterizable:
        out.append('template<typename Config>')
    out.append(f'class { className }')
    out.append('{')
    out.append('public:')
    indent = ' '*4
    port_count = 0
    mp_sig = dict()
    for direction in ['src', 'dst']:
        for port_type in data['ports']:
            for port, value in data['ports'][port_type].items():
                mp_sig[port] = intf_gen_utils.sc_gen_modport_signal_blast(value, prj, data, swap_dir=False)

    def gen_sc_channels_decl(args, prj, data):
        nonlocal port_count
        s = []
        for direction in ['src', 'dst']:
            section = []
            have_port = False
            section.append(f'// {direction} ports')
            for port_type in data['ports']:
                for port in filter(lambda p : data['ports'][port_type][p]['direction'] == direction, data['ports'][port_type].keys()):
                    if mp_sig[port]['is_skip']:
                        continue
                    have_port = True
                    port_count += 1
                    port_data = data['ports'][port_type][port]
                    intf_data = intf_gen_utils.get_intf_data(port_data['connection'], prj)
                    section.append(f"// {intf_data['desc']}")
                    section.append(mp_sig[port]['channel_decl'])
            section.append('')
            if have_port:
                s.extend(section)
        s = '\n'.join(s)
        return s

    out.append(textwrap.indent(gen_sc_channels_decl(args, prj, data), indent))

    out.append('')

    colon = ':' if port_count > 0 else ''
    out.append( indent + f'{ className }(std::string name, std::string srcName) {colon}')
    comma = ''
    for direction in ['src', 'dst']:
        for port_type in data['ports']:
            for port, value in data['ports'][port_type].items():
                if mp_sig[port]['is_skip']:
                    continue
                if value['direction'] == direction:
                    out.append(indent + comma + channelConstructor(args, prj, data, value, mp_sig[port]['multicycle_types']) )
                    comma = ','
    out.append( indent + '{};')
    cfg = '<Config>' if isParameterizable else ''
    out.append( indent + f'void bind( {data["blockName"]}Base{cfg} *a, {data["blockName"]}Inverted{cfg} *b)')
    out.append( indent + '{')
    indent = indent + ' '*4
    for direction in ['src', 'dst']:
        for port_type in data['ports']:
            for port, value in data['ports'][port_type].items():
                if mp_sig[port]['is_skip']:
                    continue
                if value['direction'] == direction:
                    out.append( indent + f'a->{ value["name"] }( { value["name"] } );')
                    out.append( indent + f'b->{ value["name"] }( { value["name"] } );')
    indent = ' '*4
    out.append( indent +'};')
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
    intf_data = intf_gen_utils.get_intf_data(line['connection'], prj)
    interface_size = intf_data.get('maxTransferSize',0)
    tracker_type = intf_data.get('trackerType',"")
    multi_cycle_mode = intf_data.get('multiCycleMode',"")
    tracker = line.get('tracker',"")
    auto_mode = autoModeMapping.get(tracker,"")

    if multicycle_types:
        #- fixed_size        #
        #- header_tracker    # for rdyVldBurst tracker tag comes from field in the header (based on field with "generator: tracker(xxx)"" in structures where xxx is the tracker name)
        #- header_size       # for rdyVldBurst size comes from field in the header (based on field with "generator: tracker(length)"" in structures)
        #- api_list_tracker  # tracker tag comes from write api and push_context
        #- api_list_size     # size comes from write api and push_context

        if multi_cycle_mode != "":
            if multi_cycle_mode not in multicycle_types:
                printError(f"Interface type does not support multiCycleMode {multi_cycle_mode}")
                exit(warningAndErrorReport())
            if tracker_type != "":
                tracker_type = f'tracker:{tracker_type}'
            extra = f', "{multi_cycle_mode}", {interface_size}, "{tracker_type}"'
        else:
            if interface_size != "0" or tracker_type:
                print(f"warning: interface {line['interfaceKey']} has a maxTransferSize or trackerType but no multiCycleMode")

    return(f'{ line["name"] }(("{ line["name"] }"+name).c_str(), srcName{extra}{auto_mode})')
