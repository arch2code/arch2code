from pathlib import Path
from pysrc.systemVerilogGeneratorHelper import fileNameBlockCheck, importPackages
from pysrc.processYaml import camelCase
import pysrc.intf_gen_utils as intf_gen_utils

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    out = []
    indent = ' ' * 4

    # Pass in the stem of fileName and the blockName
    out.append(fileNameBlockCheck(Path(data['fileName']).resolve().stem, data['blockName']))

    # Packages
    startingContext = prj.data['blocks'][prj.getQualBlock(data['blockName'])]['_context']
    out.append(importPackages(args, prj, startingContext, data))

    # Parameters
    if ( prj.data['blocks'][data['qualBlock']]['params'] ):
        out.append('#(')
        out.append(",\n".join([f"{indent}parameter {param['param']}" for param in prj.data['blocks'][data['qualBlock']]['params']]))
        out.append(')')

    out.append("(")

    # Ports
    out.extend(intf_gen_utils.sv_gen_ports(data, prj, indent))

    #// Interface Instances, needed for between instanced modules inside this module
    out.append(f"{indent}// Interface Instances, needed for between instanced modules inside this module")
    for channelType in data["connectDouble"]:
        for key, value in data["connectDouble"][channelType].items():
            intf_type = intf_gen_utils.get_intf_type(value['interfaceType'])
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
            # dualPort with no connection is one with name
            #   and one with Unused
            # dualPort with one connection and no portSuffix is one with name
            #   and one with Unused
            # dualPort with one connection with portSuffix is one with name
            #   and one with portSuffix
            # singlePort with no connection is one with name
            connectionsPerMemory = 0
            memoryConnectionKey = '' # clear key between memories
            ports = {0: mem_info['memory'], 1: mem_info['memory']+'_unused' } if mem_info['memoryType'] == 'dualPort' else {0: mem_info['memory']}
            portCount = len(ports)
            if mem_info['ports']:
                for port, port_data in mem_info['ports'].items():
                    ports[connectionsPerMemory] = mem_info['memory']+'_'+port_data['port']
                    connectionsPerMemory = connectionsPerMemory + 1
            if mem_info['regAccess']:
                ports[portCount-1] = mem_info['memory']+'_reg'
            for portName in ports.values():
                out.append(f"{indent}memory_if #(.data_t({mem_info['structure']}), .addr_t({mem_info['addressStruct']})) {portName}();")
            memory_ports[mem_key] = ports
        out.append("")

    #// Instances
    out.append("// Instances")
    for unusedKey, value in data['subBlockInstances'].items():

        qualBlockInst = prj.getQualBlock(value['instanceType'])

        if qualBlockInst in prj.data['parameters'].keys():
            variant_data = [v for _,v in prj.data['parameters'][qualBlockInst]['variants'].items() if v['variant'] == value['variant']]
        else:
            variant_data = None

        inst_params = ' '
        if ( variant_data ):
            inst_params += '#('
            inst_params += ", ".join([f".{param['param']}({param['value']})" for param in variant_data])
            inst_params += ') '

        out.append(f"{value['instanceType']}{inst_params}{value['instance']} (")
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
        out.append(f"{indent}.clk (clk),\n{indent}.rst_n (rst_n)\n);\n")

    #// Memory Instances if they exist
    if data['memories']:
        out.append("// Memory Instances")
    for mem_key, mem_data in data['memories'].items():
        # memories are currenlty all parameterized behavioral memories
        isLocal = mem_data['local']
        memory_type = 'memory_dp' if mem_data['memoryType'] == 'dualPort' else 'memory_sp'
        if isLocal:
            memory_type += '_ext'
            localMemInst =f"{mem_data['memory']}Mem"
            out.append(f"{mem_data['structure']} {localMemInst} [{mem_data['wordLines']}-1:0];")
        memInstName = camelCase('u', mem_data['memory'])
        out.append(f"{memory_type} #(.DEPTH({mem_data['wordLines']}), .data_t({mem_data['structure']})) {memInstName} (")
        for port_key, port_data in memory_ports[mem_key].items():
            port = chr(int(port_key) + ord('A')) if mem_data['memoryType'] == 'dualPort' else ''
            out.append(f"{indent}.mem_port{port} ({port_data}),")
        if isLocal:
            out.append(f"{indent}.mem ({localMemInst}),")
        out.append(f"{indent}.clk (clk)\n);\n")
    return "\n".join(out)
