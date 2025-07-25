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

    out.append(f'#include "{className}.h"\n')
    includes = dict()
    # create a dict of unique includes
    for key, value in data['subBlockInstances'].items():
        includes[value["instanceType"]] = None
    for include in includes:
        baseInclude = prj.getModuleFilename('blockBase', include, 'hdr')
        out.append(f'#include "{baseInclude}"\n')

    out.append(f'SC_HAS_PROCESS({ className });\n\n')
    out.append(f'{ className }::registerBlock { className }::registerBlock_; //register the block with the factory\n\n')

    if data['addressDecode']['isApbRouter']:
        out.append(f'void { className }::routerDecode(void) //handle apb routing for register\n{{\n')
        out.append(f'    log_.logPrint(fmt::format("SystemC Thread:{{}} started", __func__));\n')
        out.append(f'    decoder.decodeThread();\n}}\n\n')

    if data['addressDecode']['hasDecoder']:
        busInterface = data["addressDecode"]["registerBusInterface"]
        busStructs = ', '.join(data["addressDecode"]["registerBusStructs"].values())
        out.append(f'void { className }::regHandler(void) {{ //handle register decode\n')
        out.append(f'    registerHandler< {busStructs} >(regs, {busInterface}, (1<<({data["addressDecode"]["addressBits"]}-1))-1); }}\n\n')

    out.append(f'{ className }::{ className }(sc_module_name blockName, const char * variant, blockBaseMode bbMode)\n')
    out.append(f'       : sc_module(blockName)\n')
    out.append(f'        ,blockBase("{ className }", name(), bbMode)\n')
    out.append(f'        ,{ baseClassName}(name(), variant)\n')

    if data['addressDecode']['hasDecoder']:
        out.append(f'        ,regs(log_)\n')
    if data['addressDecode']['isApbRouter']:
        out += addressDecoder(args, prj, data)

    chnl_table = dict()
    for key, value in data["connections"].items():
        chnl_table[key] = intf_gen_utils.sc_gen_block_channels(value, prj)

    for key, value in data['connections'].items():
        if value["channelCount"] > 1:
            channelBase = value["channelName"] + "_" + value["src"] + "_" + value["dst"]
        else:
            channelBase = value["channelName"]
        #channelBase += "_chnl"
        for k, v in value["ends"].items():
            if v["direction"] == "src":
                src = v["instanceType"]
            else:
                dst = v["instanceType"]
        channelTitle = dst + "_" + channelBase
        extra = ''
        # we may have a multicycle interface
        interfaceInfo = prj.data['interfaces'][value['interfaceKey']]
        interfaceSize = interfaceInfo['maxTransferSize']
        # did the connection specify an interface maxTransferSize
        if value['maxTransferSize'] != "0": # check for override
            interfaceSize = value['maxTransferSize'] # override interface setting from connection
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
        autoMode = autoModeMapping.get(value['tracker'],"")

        if chnl_table[key]['multicycle_types']:
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
                    print(f"warning: interface {value['interfaceKey']} has a maxTransferSize or trackerType but no multiCycleMode")
        else:
            # check nothing set
            if not (multiCycleMode == "" and interfaceSize == "0" and trackerType == ""):
                printError(f"Interface type does support multiCycleMode, interfaceSize or trackerType")
                exit(warningAndErrorReport())

        out.append(f'        ,{ channelBase }("{ channelTitle }", "{ src }"{extra}{autoMode})\n')


    for key, value in data['subBlockInstances'].items():
        out.append(f'        ,{ value["instance"] }(std::dynamic_pointer_cast<{ value["instanceType"] }Base>( instanceFactory::createInstance(name(), "{ value["instance"]}", "{value["instanceType"]}", "{value["variant"]}")))\n')
    for reg, regData in data['registers'].items():
        out.append(f'        ,{ regData["register"] }({ regData.get("defaultValue", "") })\n')
    for mem, memData in data['memories'].items():
        if memData["local"]:
            out.append(f'        ,{ memData["memory"] }(name(), "{ memData["memory"] }", mems, {memData["wordLines"]}, HWMEMORYTYPE_LOCAL)\n')
        else:
            out.append(f'        ,{ memData["memory"] }(name(), "{ memData["memory"] }", mems, {memData["wordLines"]})\n')
    # take the list and return a string
    if out:
        last = out.pop()
        last = last[:-1]
        out.append(last)
    return("".join(out))

def constructorBody(args, prj, data):
    out = list()

    out.append('{\n')
    first = True
    # loop through the memories in offset order
    mems = dict(filter(lambda x: x[1]['regAccess'], data["memories"].items()))
    mems = dict(sorted(mems.items(), key=lambda item: item[1]["offset"]))
    for mem, memData in mems.items():
        if first:
            first=False
            out.append(f'    // register memories for FW access\n')
        if memData["regAccess"]:
            width = intf_gen_utils.get_struct_width(memData["structureKey"], prj.data["structures"])
            memSize = roundup_pow2min4((width + 7) >> 3) * intf_gen_utils.get_const(memData['wordLinesKey'], prj.data['constants'])
            out.append(f'    regs.addMemory( 0x{memData["offset"]:0x}, 0x{memSize:0x}, std::string(this->name()) + ".{memData["memory"]}", &{memData["memory"]});\n')

    first = True
    regs = dict(sorted(data["registers"].items(), key=lambda item: item[1]["offset"]))
    for reg, regData in regs.items():
        if first:
            first=False
            out.append(f'    // register registers for FW access\n')

        out.append(f'    regs.addRegister( 0x{regData["offset"]:0x}, {regData["bytes"]}, "{ regData["register"] }", &{ regData["register"] } );\n')

    first = True
    for key, value in data["connectionMaps"].items():
        if first:
            first=False
            out.append(f'// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)\n')

        out.append(f'    { value["instance"] }->{ value["instancePortName"]}({ value["parentPortName"] });\n')


    first = True
    for key, value in data["connections"].items():
        if first:
            first=False
            out.append(f'// instance to instance connections via channel\n')

        if value["channelCount"] > 1:
            channelBase = value["channelName"] + "_" + value["src"] + "_" + value["dst"]
        else:
            channelBase = value["channelName"]
        #channelBase += '_chnl'
        for end, endvalue in value["ends"].items():
            out.append(f'    { endvalue["instance"] }->{ endvalue["name"]}({ channelBase });\n')
    if data['addressDecode']['isApbRouter']:
        out.append(f'    SC_THREAD(routerDecode);\n')
    if data['addressDecode']['hasDecoder']:
        out.append(f'    SC_THREAD(regHandler);\n')
    out.append(f'    log_.logPrint(fmt::format("Instance {{}} initialized.", this->name()), LOG_IMPORTANT );\n')
    # take the list and return a string
    if out:
        last = out.pop()
        last = last[:-1]
        out.append(last)
    return("".join(out))


def addressDecoder(args, prj, data):
    out = list()
    blockName = data["blockName"]
    addressGroup = data['addressDecode']['addressGroup']
    addressGroupData = data['addressDecode']['addressGroupData']
    decoderInstance = addressGroupData['decoderInstance']
    containerBlock = data['addressDecode']['containerBlock']
    instanceWithRegApb = data['addressDecode']['instanceWithRegApb']
    busInterface = data["addressDecode"]["registerBusInterface"]
    out.append(f'        ,decoder({addressGroupData["maxAddressSpaces"]}, {addressGroupData["addressIncrement"].bit_length()-1}, {busInterface}, {{\n')
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
                out.append('            nullptr,\n')
        if instance in instanceWithRegApb:
            for channel in range(instanceData['addressMultiples']):
                out.append(f'            &apb_{instanceData["instance"]},\n')
        else:
            out.append('            nullptr,\n')

    # replace the last comma with a space
    if out:
        last = out.pop()
        last = last[:-2] + '})\n'
        out.append(last)
    return out

