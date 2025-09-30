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
        out.append('#(\n')
        out.append(",\n".join([f"{indent}parameter {param['param']}" for param in prj.data['blocks'][data['qualBlock']]['params']]))
        out.append('\n)\n')

    out.append("(\n")

    # Ports
    for sourceType in data['ports']:
        for port, port_data in data['ports'][sourceType].items():
            connectionData = port_data.get('connection', {})
            intf_data = intf_gen_utils.get_intf_data(connectionData, prj)
            intf_type = intf_gen_utils.get_intf_type(intf_data['interfaceType'])
            out.append(f"{indent}{intf_type}_if.{port_data['direction']} {port_data['name']},\n")
    out.append(f"{indent}input clk, rst_n\n")
    out.append(");\n\n")

    #// Interface Instances, needed for between instanced modules inside this module
    out.append(f"{indent}// Interface Instances, needed for between instanced modules inside this module\n")
    for channelType in data["connectDouble"]:
        for key, value in data["connectDouble"][channelType].items():
            intf_type = intf_gen_utils.get_intf_type(value['interfaceType'])
            intf_data = intf_gen_utils.get_intf_data(value, prj)
            out.append(f"{indent}{intf_type}_if #(")
            params = list()
            for item in intf_data['structures']:
                params.append(f".{item['structureType']}({item['structure']})")
            out.append(', '.join(params))
            out.append(f") {value['interfaceName']}")
            out.append("();\n")
    out.append("\n")

    #// Memory Interfaces if they exist
    if data['memories']:
        out.append(f"{indent}// Memory Interfaces\n")
        for unusedKey, value in data['memories'].items():
            # dualPort with no connection is one with name
            #   and one with Unused
            # dualPort with one connection and no portSuffix is one with name
            #   and one with Unused
            # dualPort with one connection with portSuffix is one with name
            #   and one with portSuffix
            # singlePort with no connection is one with name
            connectionsPerMemory = 0
            memoryConnectionKey = '' # clear key between memories
            portSuffix = None
            for memoryConnectionKey, memoryConnection in data['memoryConnections'].items():
                if (value['memory'] == memoryConnection['memory']):
                    out.append(f"{indent}memory_if #(.data_t({value['structure']}), .addr_t({value['addressStruct']})) {value['memory']}{memoryConnection['portSuffix']}();\n")
                    connectionsPerMemory = connectionsPerMemory + 1
                    if memoryConnection['portSuffix'] != '':
                        portSuffix = True
            if connectionsPerMemory == 0:
                if value['memoryType'] == 'dualPort':
                    key = memoryConnectionKey + "PortA"
                    data['memoryConnections'][key] = {'memory': value['memory'], 'instance': None, 'portSuffix': ''}
                    out.append(f"{indent}memory_if #(.data_t({value['structure']}), .addr_t({value['addressStruct']})) {value['memory']}();\n")
                    key = memoryConnectionKey + "PortB"
                    if value['regAccess']:
                        data['memoryConnections'][key] = {'memory': value['memory'], 'instance': None, 'portSuffix': 'Regs'}
                        out.append(f"{indent}memory_if #(.data_t({value['structure']}), .addr_t({value['addressStruct']})) {value['memory']}Regs();\n")
                    else:
                        data['memoryConnections'][key] = {'memory': value['memory'], 'instance': None, 'portSuffix': 'Unused'}
                        out.append(f"{indent}memory_if #(.data_t({value['structure']}), .addr_t({value['addressStruct']})) {value['memory']}Unused();\n")

                else: # singlePort
                    memoryConnectionKey = memoryConnectionKey + "Single"
                    if value['regAccess'] and value['local']:
                        out.append(f"{indent}memory_if #(.data_t({value['structure']}), .addr_t({value['addressStruct']})) {value['memory']}Regs();\n")
                        data['memoryConnections'][memoryConnectionKey] = {'memory': value['memory'], 'instance': None, 'portSuffix': 'Regs'}
                    else:
                        data['memoryConnections'][memoryConnectionKey] = {'memory': value['memory'], 'instance': None, 'portSuffix': ''}
                        out.append(f"{indent}memory_if #(.data_t({value['structure']}), .addr_t({value['addressStruct']})) {value['memory']}();\n")
            elif connectionsPerMemory == 1 and value['memoryType'] == 'dualPort' and not portSuffix:
                memoryConnectionKey = memoryConnectionKey + "PortB"
                if value['regAccess']:
                    data['memoryConnections'][memoryConnectionKey] = {'memory': value['memory'], 'instance': None, 'portSuffix': 'Regs'}
                    out.append(f"{indent}memory_if #(.data_t({value['structure']}), .addr_t({value['addressStruct']})) {value['memory']}Regs();\n")
                else:
                    data['memoryConnections'][memoryConnectionKey] = {'memory': value['memory'], 'instance': None, 'portSuffix': 'Unused'}
                    out.append(f"{indent}memory_if #(.data_t({value['structure']}), .addr_t({value['addressStruct']})) {value['memory']}Unused();\n")
            elif connectionsPerMemory == 1 and value['memoryType'] == 'dualPort' and portSuffix:
                memoryConnectionKey = memoryConnectionKey + "PortB"
                data['memoryConnections'][memoryConnectionKey] = {'memory': value['memory'], 'instance': None, 'portSuffix': ''}
                out.append(f"{indent}memory_if #(.data_t({value['structure']}), .addr_t({value['addressStruct']})) {value['memory']}();\n")
        out.append("\n")

    #// Register Interfaces if they exist
    if data['registers']:
        out.append(f"{indent}// Register Interfaces\n")
        for unusedKey, value in data['registers'].items():
            #the register interfaces get inferred and therefore are mostly hardcoded here
            if (value['regType'] in ['ro', 'rw']):
                out.append(f"{indent}status_if #(.data_t({value['structure']})) {value['register']}();\n")
            elif (value['regType'] == 'ext'):
                out.append(f"{indent}external_reg_if #(.data_t({value['structure']})) {value['register']}();\n")
        out.append("\n")

    #// Instances
    out.append("// Instances\n")
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

        if ( value['registerLeafInstance'] == 1 ):
            mask = (1<<(data['addressDecode']['addressBits']-1))-1
            out.append(f"{value['instanceType']} #(.APB_ADDR_MASK('h{mask:_x})) {value['instance']} (\n")
        else:
            out.append(f"{value['instanceType']}{inst_params}{value['instance']} (\n")
        # Declare connectionMaps that connect to this instance
        for unusedKey2, value2 in data['connectionMaps'].items():
            if (value['instance'] == value2['instance']):
                out.append(f"{indent}.{value2['instancePortName']} ({value2['parentPortName']}),\n")
        # loop through the memory connections that connect to this instance
        for unusedKey2, memValue in data['memoryConnections'].items():
            if (value['instance'] == memValue['instance']):
                out.append(f"{indent}.{memValue['memory']} ({memValue['memory']}{memValue['portSuffix']}),\n")
        # loop through the register connections that connect to this instance
        for unusedKey2, regValue in data['registerConnections'].items():
            if (value['instance'] == regValue['instance']):
                out.append(f"{indent}.{regValue['register']} ({regValue['register']}),\n")
        # loop through connection for this instance
        for unusedKey2, value2 in data['connections'].items():
            for unusedKey3, value3 in value2['ends'].items():
                if (value['instance'] == value3['instance']):
                    if value2['channelCount'] > 1:
                        out.append(f"{indent}.{value3['portName']} ({value2['interfaceName']}[{value2['channelIndex']}]),\n")
                    else:
                        out.append(f"{indent}.{value3['portName']} ({value2['interfaceName']}),\n")
        out.append(f"{indent}.clk (clk),\n{indent}.rst_n (rst_n)\n);\n\n")

    #// Memory Instances if they exist
    if data['memories']:
        out.append("// Memory Instances\n")
    for unusedKey, value in data['memories'].items():
        # memories are currenlty all parameterized behavioral memories
        if value['local']:
            isLocal = True
            ext = "_ext"
            external = " external"
            localMemInst =f"{value['memory']}Mem"
        else:
            isLocal = False
            ext = ''
            external = ''
        if value['memoryType'] == 'dualPort':
            portValue = 'A'
            out.append(f"// dual port{external}\n")
            if isLocal:
                out.append(f"{value['structure']} {localMemInst} [{value['wordLines']}-1:0];\n")
            memInstName = camelCase('u', value['memory'])
            out.append(f"memory_dp{ext} #(.DEPTH({value['wordLines']}), .data_t({value['structure']})) {memInstName} (\n")
        elif value['memoryType'] == 'singlePort':
            out.append(f"// single port{external}\n")
            if isLocal:
                out.append(f"{value['structure']} {localMemInst} [{value['wordLines']}-1:0];\n")
            memInstName = camelCase('u', value['memory'])
            out.append(f"memory_sp{ext} #(.DEPTH({value['wordLines']}), .data_t({value['structure']})) {memInstName} (\n")
        for unusedKey2, memoryConnection in data['memoryConnections'].items():
            if value['memory'] == memoryConnection['memory']:
                if value['memoryType'] == 'dualPort':
                    out.append(f"{indent}.mem_port{portValue} ({value['memory']}{memoryConnection['portSuffix']}),\n")
                    portValue = 'B'
                elif value['memoryType'] == 'singlePort':
                    out.append(f"{indent}.mem_port ({value['memory']}{memoryConnection['portSuffix']}),\n")
        if isLocal:
            out.append(f"{indent}.mem ({localMemInst}),\n")
        out.append(f"{indent}.clk (clk)\n);\n\n")
    return "".join(out)
