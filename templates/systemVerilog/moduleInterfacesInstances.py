from pysrc.systemVerilogGeneratorHelper import moduleDeclaration, importPackages
from pysrc.processYaml import camelCase
from templates.systemVerilog.package import instanceParameterSpelling, moduleParameterDecl, parameterizedDeclLines
import pysrc.intf_gen_utils as intf_gen_utils

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    out = []
    indent = ' ' * 4

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

    # Ports
    out.extend(intf_gen_utils.sv_gen_ports(data, prj, indent))

    # Module-local parameterizable type/struct declarations. SV cannot
    # parameterize a package, so a parameterized block declares the
    # types/structs sized from its own module parameters here (the same
    # deriveParameterizedDeclSets set the package omits). Empty for
    # non-parameterized blocks.
    if data['parameterizedDecls']:
        out.append(f"{indent}// Module-local parameterizable type/struct declarations")
        for entry in parameterizedDeclLines(data['parameterizedDecls'], prj, data['blockInfo']['params']):
            out.append(f"{indent}{entry['line']}")
        out.append("")

    # One internal wire per net a child instance's output drives under a name
    # this block does not declare. Emitted before the aliases, which may read
    # a local net.
    if data['localNets']:
        out.append(f"{indent}// Local clock/reset nets, driven by a child instance's output")
        out.extend(f"{indent}wire {net['name']};" for net in data['localNets'])
        out.append("")

    alias_lines = intf_gen_utils.sv_default_domain_aliases(data)
    if alias_lines:
        out.append(f"{indent}// Default-domain aliases: the bare flop macros expand to clk / rst_n")
        out.extend(f"{indent}{line}" for line in alias_lines)
        out.append("")

    #// Interface Instances, needed for between instanced modules inside this module
    out.append(f"{indent}// Interface Instances, needed for between instanced modules inside this module")
    for channelType in data["connectDouble"]:
        for key, value in data["connectDouble"][channelType].items():
            intf_type = intf_gen_utils.get_intf_type(value['interfaceType'], data)
            intf_data = intf_gen_utils.get_intf_data(value, prj)
            s = f"{indent}{intf_type}_if #("
            params = list()
            if intf_data['structures']:
                for item in intf_data['structures']:
                    params.append(f".{item['structureType']}({item['structure']})")
            s += ', '.join(params)
            s += f") {intf_gen_utils.get_channel_name(value)}();"
            out.append(s)
    out.append("")

    #// Memory Interfaces if they exist
    memory_ports = {}
    if data['memories']:
        out.append(f"{indent}// Memory Interfaces")
        for mem_key, mem_info in data['memories'].items():
            # Block-side ports take the ports: list in order; a block-side
            # port with no listed port is named after the memory, then _unused.
            listed = [mem_info['memory']+'_'+port_data['port'] for port_data in mem_info['ports'].values()] if mem_info['ports'] else []
            blockNames = iter(listed + [mem_info['memory'], mem_info['memory']+'_unused'][len(listed):])
            ports = {port: mem_info['memory']+'_reg' if port == mem_info['regPort'] else next(blockNames)
                     for port in mem_info['portAccess']}
            for portName in ports.values():
                out.append(f"{indent}memory_if #(.data_t({mem_info['structure']}), .addr_t({mem_info['addressStruct']})) {portName}();")
            memory_ports[mem_key] = ports
        out.append("")

    #// Instances
    out.append("// Instances")
    for unusedKey, value in data['subBlockInstances'].items():

        # svInstanceParams (from the projectOpen view) gives each child param's
        # override spelling: a parent param symbol when the parent forwards it,
        # otherwise the bound literal. Empty for non-parameterized children.
        inst_params = ' '
        if value['svInstanceParams']:
            inst_params += '#('
            inst_params += ", ".join([f".{param['param']}({instanceParameterSpelling(prj, param)})" for param in value['svInstanceParams']])
            inst_params += ') '

        out.append(f"{value['instanceTypeSvModuleName']}{inst_params}{value['instance']} (")
        # Declare connectionMaps that connect to this instance
        for unusedKey2, value2 in data['connectionMaps'].items():
            if (value['instance'] == value2['instance']):
                out.append(f"{indent}.{value2['instancePortName']} ({value2['parentPortName']}),")
        # loop through the memory connections that connect to this instance
        for unusedKey2, memValue in data['memoryConnections'].items():
            if (value['instance'] == memValue['instance']):
                out.append(f"{indent}.{memValue['memory']} ({intf_gen_utils.get_channel_name(memValue)}),")
        # loop through the register connections that connect to this instance
        for sourceType in data['connectDouble']:
            for connKey, connValue in data['connectDouble'][sourceType].items():
                for end, endValue in connValue['ends'].items():
                    if (value['instance'] == endValue['instance']):
                        out.append(f"{indent}.{endValue['portName']} ({intf_gen_utils.get_channel_name(connValue)}),")
        # clockResetBinds (from the projectOpen view) pairs each of the child's own
        # clock/reset port names with the parent signal driving it, already in the
        # child's port-list order.
        out.append(",\n".join(f"{indent}.{bind['port']} ({bind['signal']})"
                              for bind in value['clockResetBinds']) + "\n);\n")

    #// Memory Instances if they exist
    if data['memories']:
        out.append("// Memory Instances")
    for mem_key, mem_data in data['memories'].items():
        # memories are currenlty all parameterized behavioral memories
        isLocal = mem_data['local']
        portAccess = mem_data['portAccess']
        isDualPort = len(portAccess) == 2
        memory_type = 'memory_dp' if isDualPort else 'memory_sp'
        if isLocal:
            memory_type += '_ext'
            localMemInst =f"{mem_data['memory']}Mem"
            out.append(f"{mem_data['structure']} {localMemInst} [{mem_data['wordLines']}-1:0];")
        memInstName = camelCase('u', mem_data['memory'])
        mem_params = f".DEPTH({mem_data['wordLines']}), .data_t({mem_data['structure']})"
        if isDualPort:
            mem_params += (f", .PORTA_READ_ONLY(1'b{int(portAccess['A'] == 'ro')})"
                           f", .PORTB_WRITE_ONLY(1'b{int(portAccess['B'] == 'wo')})")
        out.append(f"{memory_type} #({mem_params}) {memInstName} (")
        for port, port_data in memory_ports[mem_key].items():
            out.append(f"{indent}.mem_port{port} ({port_data}),")
        if isLocal:
            out.append(f"{indent}.mem ({localMemInst}),")
        # Each port's clock is spelled clk plus its port suffix: clkA/clkB, or
        # clk on a single-port memory.
        out.append(",\n".join(f"{indent}.clk{port} ({clock})"
                              for port, clock in mem_data['portClock'].items()) + "\n);\n")
    return "\n".join(out)
