# args from generator line
# prj object
# data set dict
from pysrc.arch2codeHelper import printError, printWarning, warningAndErrorReport, printIfDebug, roundup_pow2, roundup_pow2min4

import textwrap
import pysrc.intf_gen_utils as intf_gen_utils

# Does not alter the rendering
intf_gen_utils.LEGACY_COMPAT_MODE = True

def render(args, prj, data):
    match args.section:
        case 'init':
            return(constructorInit(args, prj, data))
        case 'body':
            return(constructorBody(args, prj, data))
        case _:
            print("error missing section, valid values are implementation, externs, headerDecl")
            exit()


def constructorInit(args, prj, data):
    out = list()
    className = data["blockName"]
    baseClassName = f'{ className }Base'
    registerDecode = data['addressDecode']['hasDecoder'] and (not data['enableRegConnections'] or data['blockInfo']['isRegHandler'])
    out.append(f'#include "{className}.h"')
    
    out += intf_gen_utils.sc_instance_includes(data, prj)

    out.append(f'SC_HAS_PROCESS({ className });\n')
    out.append(f'{ className }::registerBlock { className }::registerBlock_; //register the block with the factory\n')

    if data['addressDecode']['isApbRouter']:
        out.append(f'void { className }::routerDecode(void) //handle apb routing for register\n{{')
        out.append(f'    log_.logPrint(fmt::format("SystemC Thread:{{}} started", __func__));')
        out.append(f'    decoder.decodeThread();\n}}\n')

    if registerDecode:
        busInterface = data["addressDecode"]["registerBusInterface"]
        busStructs = ', '.join(data["addressDecode"]["registerBusStructs"].values())
        out.append(f'void { className }::regHandler(void) {{ //handle register decode')
        out.append(f'    registerHandler< {busStructs} >(regs, {busInterface}, (1<<({data["addressDecode"]["addressBits"]}-1))-1); }}\n')

    out.append(f'{ className }::{ className }(sc_module_name blockName, const char * variant, blockBaseMode bbMode)')
    out.append(f'       : sc_module(blockName)')
    out.append(f'        ,blockBase("{ className }", name(), bbMode)')
    out.append(f'        ,{ baseClassName}(name(), variant)')

    if registerDecode:
        out.append(f'        ,regs(log_)')
    if data['addressDecode']['isApbRouter']:
        out += addressDecoder(args, prj, data)

    chnl_table = dict()
    for channelType in data["connectDouble"]:
        for chnl, chnlInfo in data["connectDouble"][channelType].items():
            chnl_table[chnl] = intf_gen_utils.sc_gen_block_channels(chnlInfo, prj)

            #if chnlInfo["channelCount"] > 1:
            #    channelBase = chnlInfo["interfaceName"] + "_" + chnlInfo["src"] + "_" + chnlInfo["dst"]
            #else:
            channelBase = chnlInfo["interfaceName"]
            #channelBase += "_chnl"
            for k, v in chnlInfo["ends"].items():
                if v["direction"] == "src":
                    src = v.get("instanceType") or chnlInfo.get("block", "")
                else:
                    dst = v.get("instanceType") or chnlInfo.get("block", "")
            channelTitle = dst + "_" + channelBase
            extra = ''
            # we may have a multicycle interface
            if 'interfaceKey' in chnlInfo:
                interfaceInfo = prj.data['interfaces'][chnlInfo['interfaceKey']]
                interfaceSize = interfaceInfo['maxTransferSize']
                # did the connection specify an interface maxTransferSize
                if chnlInfo['maxTransferSize'] != "0": # check for override
                    interfaceSize = chnlInfo['maxTransferSize'] # override interface setting from connection
                trackerType = interfaceInfo['trackerType']
                multiCycleMode = interfaceInfo['multiCycleMode']
                autoModeMapping = {
                    "": "",
                    "alloc": ", INTERFACE_AUTO_ALLOC",
                    "dealloc": ", INTERFACE_AUTO_DEALLOC",
                    "allocReq": ", INTERFACE_AUTO_ALLOC, INTERFACE_AUTO_OFF",
                    "deallocReq": ", INTERFACE_AUTO_DEALLOC, INTERFACE_AUTO_OFF",
                    "allocAck": ", INTERFACE_AUTO_OFF, INTERFACE_AUTO_ALLOC",
                    "deallocAck": ", INTERFACE_AUTO_OFF, INTERFACE_AUTO_DEALLOC"
                }
                autoMode = autoModeMapping.get(chnlInfo['tracker'],"")
            else:
                # register interface
                interfaceSize = 0
                trackerType = ''
                multiCycleMode = ''
                autoMode = ''

            if chnl_table[chnl]['multicycle_types']:
                #- fixed_size        #
                #- header_tracker    # for rdyVldBurst tracker tag comes from field in the header (based on field with "generator: tracker(xxx)"" in structures where xxx is the tracker name)
                #- header_size       # for rdyVldBurst size comes from field in the header (based on field with "generator: tracker(length)"" in structures)
                #- api_list_tracker  # tracker tag comes from write api and push_context
                #- api_list_size     # size comes from write api and push_context

                if multiCycleMode != "":
                    if trackerType != "":
                        trackerType = f'tracker:{trackerType}'
                    extra = f', "{multiCycleMode}", {interfaceSize}, "{trackerType}"'
                else:
                    if interfaceSize != "0" or trackerType:
                        print(f"warning: interface {chnlInfo['interfaceKey']} has a maxTransferSize or trackerType but no multiCycleMode")

            out.append(f'        ,{ channelBase }("{ channelTitle }", "{ src }"{extra}{autoMode})')


    for key, value in data['subBlockInstances'].items():
        out.append(f'        ,{ value["instance"] }(std::dynamic_pointer_cast<{ value["instanceType"] }Base>( instanceFactory::createInstance(name(), "{ value["instance"]}", "{value["instanceType"]}", "{value["variant"]}")))')
    for reg, regData in data['registers'].items():
        out.append(f'        ,{ regData["register"] }({ regData.get("defaultValue", "") })')
    for mem, memData in data['memories'].items():
        if memData["local"]:
            out.append(f'        ,{ memData["memory"] }(name(), "{ memData["memory"] }", mems, {memData["wordLines"]}, HWMEMORYTYPE_LOCAL)')
        else:
            out.append(f'        ,{ memData["memory"] }(name(), "{ memData["memory"] }", mems, {memData["wordLines"]})')
    # take the list and return a string
    return("\n".join(out))

def constructorBody(args, prj, data):
    out = list()

    out.append('{')
    first = True
    registerDecode = data['addressDecode']['hasDecoder'] and (not data['enableRegConnections'] or data['blockInfo']['isRegHandler'])
    if registerDecode:
        # loop through the memories in offset order
        if 'memoriesParent' in data:
            memoryKey = 'memoriesParent'
        else:
            memoryKey = 'memories'
        mems = dict(filter(lambda x: x[1]['regAccess'], data[memoryKey].items()))
        mems = dict(sorted(mems.items(), key=lambda item: item[1]["offset"]))
        for mem, memData in mems.items():
            if first:
                first=False
                out.append(f'    // register memories for FW access')
            if memData["regAccess"]:
                width = intf_gen_utils.get_struct_width(memData["structureKey"], prj.data["structures"])
                memSize = roundup_pow2min4((width + 7) >> 3) * intf_gen_utils.get_const(memData['wordLinesKey'], prj.data['constants'])
                if memoryKey == 'memoriesParent':
                    out.append(f'    regs.addMemory( 0x{memData["offset"]:0x}, 0x{memSize:0x}, std::string(this->name()) + ".{memData["memory"]}");') # TODO add access function
                else:
                    out.append(f'    regs.addMemory( 0x{memData["offset"]:0x}, 0x{memSize:0x}, std::string(this->name()) + ".{memData["memory"]}", &{memData["memory"]});')

        first = True
        regs = dict(sorted(data["registers"].items(), key=lambda item: item[1]["offset"]))
        for reg, regData in regs.items():
            if first:
                first=False
                out.append(f'    // register registers for FW access')

            out.append(f'    regs.addRegister( 0x{regData["offset"]:0x}, {regData["bytes"]}, "{ regData["register"] }", &{ regData["register"] } );')

        first = True
    for key, value in data["connectionMaps"].items():
        if first:
            first=False
            out.append(f'// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)')

        out.append(f'    { value["instance"] }->{ value["instancePortName"]}({ value["parentPortName"] });')


    connections = intf_gen_utils.sc_connect_channels(data, ' '*4)
    if connections:
        out.append(f'    // instance to instance connections via channel')
        out += connections
    first = True

    if data['addressDecode']['isApbRouter']:
        out.append(f'    SC_THREAD(routerDecode);')
    if registerDecode:
        out.append(f'    SC_THREAD(regHandler);')
    out.append(f'    log_.logPrint(fmt::format("Instance {{}} initialized.", this->name()), LOG_IMPORTANT );')
    # take the list and return a string
    return("\n".join(out))

def addressDecoder(args, prj, data):
    out = list()
    blockName = data["blockName"]
    addressGroup = data['addressDecode']['addressGroup']
    addressGroupData = data['addressDecode']['addressGroupData']
    decoderInstance = addressGroupData['decoderInstance']
    containerBlock = data['addressDecode']['containerBlock']
    instanceWithRegApb = data['addressDecode']['instanceWithRegApb']
    busInterface = data["addressDecode"]["registerBusInterface"]
    out.append(f'        ,decoder({addressGroupData["maxAddressSpaces"]}, {addressGroupData["addressIncrement"].bit_length()-1}, {busInterface}, {{')
    addressChannels = dict()
    for instance, instanceData in prj.data['instances'].items():
        if instanceData['addressGroup'] == addressGroup:
            addressChannels[instance] = instanceData
    # create sorted list of addressChannel instances by addressID
    sortedInstances = dict(sorted(addressChannels.items(), key=lambda item: item[1]["addressID"]))
    # take the sorted list and create channel names
    addressID = 0
    for instance, instanceData in sortedInstances.items():
        if instanceData['addressID'] < addressID:
            for channel in range(addressID, instanceData['addressID']):
                out.append('            nullptr,')
        if instance in instanceWithRegApb:
            for channel in range(instanceData['addressMultiples']):
                out.append(f'            &apb_{instanceData["instance"]},')
        else:
            out.append('            nullptr,')

    # replace the last comma with a space
    if out:
        last = out.pop()
        last = last[:-1] + '\n})'
        out.append(last)
    return out

