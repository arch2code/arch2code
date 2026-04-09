from pathlib import Path
from pysrc.systemVerilogGeneratorHelper import fileNameBlockCheck,getImportPackages
from pysrc.processYaml import camelCase
import pysrc.intf_gen_utils as intf_gen_utils
import pysrc.sv_model as svm

# args from generator line
# prj object
# data set dict
def render(args, prj, data):

    # check file name and block name match
    fileNameBlockCheck(data)

    # Module declaration
    module = svm.ModuleDecl(name=data['blockName'], emit_end=False)

    # Packages
    startingContext = prj.data['blocks'][prj.getQualBlock(data['blockName'])]['_context']

    module.imports = [f"{pkg}::*" for pkg in getImportPackages(args, prj, startingContext, data)]

    # Parameters
    if ( prj.data['blocks'][data['qualBlock']]['params'] ):
        for param in prj.data['blocks'][data['qualBlock']]['params']:
            module.parameters.append(svm.ParamDecl(name=param['param']))

    # Ports
    module.ports = intf_gen_utils.sv_gen_ports_svm(data, prj, data)
    module.ports += [svm.PortDecl(name='clk', direction='input'), svm.PortDecl(name='rst_n', direction='input')]

    #// Interface Instances, needed for between instanced modules inside this module
    module.body.append(svm.CommentBlock(text="Interface Instances, needed for between instanced modules inside this module"))

    for channelType in data["connectDouble"]:
        for key, value in data["connectDouble"][channelType].items():
            intf_type = intf_gen_utils.get_intf_type(value['interfaceType'], data)
            intf_data = intf_gen_utils.get_intf_data(value, prj)
            if not intf_data['structures']:
                intf_data['structures'] = []
            module.body.append(svm.InterfaceInst(
                    instance_name=intf_gen_utils.get_channel_name(value),
                    interface_name=intf_type + '_if',
                    parameters=[svm.ParamConn(param=item['structureType'], value=item['structure']) for item in intf_data['structures']]
                )
            )

    module.body.append(svm.CommentBlock(text=""))

    #// Memory Interfaces if they exist
    memory_ports = {}
    if data['memories']:
        module.body.append(svm.CommentBlock(text="Memory Interfaces"))

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
                module.body.append(
                    svm.InterfaceInst(
                        instance_name=portName,
                        interface_name='memory_if',
                        parameters=[
                            svm.ParamConn(param='data_t', value=mem_info['structure']),
                            svm.ParamConn(param='addr_t', value=mem_info['addressStruct'])
                        ]
                    )
                )
            memory_ports[mem_key] = ports

    #// Instances
    module.body.append(svm.CommentBlock(text="Instances"))

    for unusedKey, value in data['subBlockInstances'].items():

        qualBlockInst = prj.getQualBlock(value['instanceType'])

        inst = svm.ModuleInst(instance_name=value['instance'], module_name=value['instanceType'])

        if qualBlockInst in prj.data['parameters'].keys():
            variant_data = [v for _,v in prj.data['parameters'][qualBlockInst]['variants'].items() if v['variant'] == value['variant']]
        else:
            variant_data = None

        if ( variant_data ):
            inst.parameters = [svm.ParamConn(param=param['param'], value=str(param['value'])) for param in variant_data]


        # Declare connectionMaps that connect to this instance
        for unusedKey2, value2 in data['connectionMaps'].items():
            if (value['instance'] == value2['instance']):
                inst.ports.append(
                    svm.PortConn(port=value2['instancePortName'], expression=svm.InterfaceRef(name=value2['parentPortName']))
                )
        # loop through the memory connections that connect to this instance
        for unusedKey2, memValue in data['memoryConnections'].items():
            if (value['instance'] == memValue['instance']):
                inst.ports.append(
                    svm.PortConn(port=memValue['memory'], expression=svm.InterfaceRef(name=intf_gen_utils.get_channel_name(memValue)))
                )
        # loop through the register connections that connect to this instance
        for sourceType in data['connectDouble']:
            for connKey, connValue in data['connectDouble'][sourceType].items():
                for end, endValue in connValue['ends'].items():
                    if (value['instance'] == endValue['instance']):
                        inst.ports.append(
                            svm.PortConn(port=endValue['portName'], expression=svm.InterfaceRef(name=intf_gen_utils.get_channel_name(connValue)))
                        )
        inst.ports.append(svm.PortConn(port='clk', expression=svm.SignalRef(name='clk')))
        inst.ports.append(svm.PortConn(port='rst_n', expression=svm.SignalRef(name='rst_n')))

        module.body.append(inst)

    #// Memory Instances if they exist
    if data['memories']:
        module.body.append(svm.CommentBlock(text="Memory Instances"))
    for mem_key, mem_data in data['memories'].items():
        # memories are currenlty all parameterized behavioral memories
        isLocal = mem_data['local']
        memory_type = 'memory_dp' if mem_data['memoryType'] == 'dualPort' else 'memory_sp'
        if isLocal:
            memory_type += '_ext'
            localMemInst =f"{mem_data['memory']}Mem"
            module.body.append(svm.TypedVarDecl(
                name=localMemInst,
                user_type=mem_data['structure'],
                unpacked_dims=[svm.UnpackedDim(msb=f"{mem_data['wordLines']}-1", lsb="0")])
            )
        memInstName = camelCase('u', mem_data['memory'])
        mem_inst = svm.ModuleInst(
            instance_name=memInstName,
            module_name=memory_type,
            parameters=[
                svm.ParamConn(param="DEPTH", value=mem_data['wordLines']),
                svm.ParamConn(param="data_t", value=mem_data['structure'])
            ]
        )

        for port_key, port_data in memory_ports[mem_key].items():
            port = chr(int(port_key) + ord('A')) if mem_data['memoryType'] == 'dualPort' else ''
            mem_inst.ports.append(
                svm.PortConn(port=f"mem_port{port}", expression=svm.InterfaceRef(name=port_data))
            )
        if isLocal:
            mem_inst.ports.append(
                svm.PortConn(port=f"mem", expression=svm.SignalRef(name=localMemInst))
            )

        mem_inst.ports.append(
            svm.PortConn(port=f"clk", expression=svm.SignalRef(name="clk"))
        )

        module.body.append(mem_inst)

    return module.render()
