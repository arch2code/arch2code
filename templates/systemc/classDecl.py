
from pysrc.arch2codeHelper import warningAndErrorReport, roundup_multiple

import textwrap
import pysrc.intf_gen_utils as intf_gen_utils

# Does not alter the rendering
intf_gen_utils.LEGACY_COMPAT_MODE = True

def render(args, prj, data):
    match args.section:
        case _ : return render_default(args, prj, data)


def render_default(args, prj, data):
    out = list()
    className = f'{ data["blockName"] }'
    usesConfig = intf_gen_utils.block_uses_config(data, prj)
    cfg = intf_gen_utils.block_config_arg(usesConfig)
    defaultConfig = intf_gen_utils.block_default_config_type(data, prj) if usesConfig else ''
    baseClassName = f'{ data["blockName"] }Base{cfg}' 
    out.append('#include "logging.h"')
    out.append('#include "instanceFactory.h"')
    baseInclude = prj.getModuleFilename('blockBase', data["blockName"], 'hdr')
    out.append(f'#include "{baseInclude}"')
    if  len(data['registers']) > 0 or len(data["memories"]) > 0:
        out.append('#include "addressMap.h"')
    if  len(data['registers']) > 0:
        out.append('#include "hwRegister.h"')
    
    # Check if we need hwMemory.h include
    needsHwMemory = len(data["memories"]) > 0 or len(data.get('memoriesParent', {})) > 0
    # Also need it if block has local memory registers (not isRegHandler but has registerDecode and memory registers)
    registerDecode = data['addressDecode']['hasDecoder'] and (not data['enableRegConnections'] or data['blockInfo']['isRegHandler'])
    if registerDecode and not data['blockInfo'].get('isRegHandler'):
        for reg, regData in data['registers'].items():
            if regData['regType'] == 'memory':
                needsHwMemory = True
                break
    if needsHwMemory:
        out.append('#include "hwMemory.h"')
    if usesConfig:
        for context in data['includeContext']:
            if context in data['includeFiles'].get('config_hdr', {}):
                out.append(f'#include "{data["includeFiles"]["config_hdr"][context]["baseName"]}"')
    
    if args.fileMapKey:
        fileMapKey = args.fileMapKey
    else:
        fileMapKey = 'include_cppm'

    for context in data['includeContext']:
        if context in data['includeFiles'].get(fileMapKey, {}):
            includeName = data["includeFiles"][fileMapKey][context]["baseName"]
            moduleName = intf_gen_utils.module_name_from_include(includeName)
            out.append(f'import {moduleName};')
            out.append(f'using namespace {intf_gen_utils.namespace_name_from_include(includeName)};')
    if data['addressDecode']['isApbRouter']:
        out.append(f'#include "apbBusDecode.h"')

    if data["subBlocks"]:
        out.append(f'//contained instances forward class declaration')
        for key, value in data["subBlocks"].items():
            if intf_gen_utils.block_uses_config(prj.getBlockData(key), prj):
                out.append(f'template<typename Config> class { value }Base;')
            else:
                out.append(f'class { value }Base;')
    out.append('')

    if usesConfig:
        out.append(intf_gen_utils.block_config_decl(usesConfig))
    out.append(f'SC_MODULE({ className }), public blockBase, public { baseClassName }')
    out.append('{')
    out.append('private:')
    if registerDecode:
        out.append('    void regHandler(void);')
        out.append('    addressMap regs;')
    if data['addressDecode']['isApbRouter']:
        busStructs = ', '.join(data["addressDecode"]["registerBusStructs"].values())
        out.append('    void routerDecode(void);')
        out.append(f'    abpBusDecode< {busStructs} > decoder;')
    out.append('')
    indent = ' '*4
    out.append(indent + 'struct registerBlock')
    out.append(indent + '{')
    out.append(indent + '    registerBlock()')
    out.append(indent + '    {')
    if data['variants']:
        out.append(textwrap.indent(addParams(args, prj, data), indent*2))
    out.append(indent + '        // lamda function to construct the block')
    if usesConfig:
        if data['variants']:
            for variant in sorted(data['variants']):
                out.append(indent + f'        instanceFactory::registerBlock("{ className }_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {{ return static_cast<std::shared_ptr<blockBase>> (std::make_shared<{ className }<{defaultConfig}>>(blockName, variant, bbMode));}}, "{variant}" );')
        else:
            out.append(indent + f'        instanceFactory::registerBlock("{ className }_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {{ return static_cast<std::shared_ptr<blockBase>> (std::make_shared<{ className }<{defaultConfig}>>(blockName, variant, bbMode));}}, "" );')
    else:
        out.append(indent + f'        instanceFactory::registerBlock("{ className }_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {{ return static_cast<std::shared_ptr<blockBase>> (std::make_shared<{ className }>(blockName, variant, bbMode));}}, "" );')
    out.append(indent + '    }')
    out.append(indent + '};')
    out.append(indent + 'static registerBlock registerBlock_;')
    out.append('public:')
    if usesConfig:
        out.append(indent + f'SC_HAS_PROCESS({ className });')
        out.append('')

    channels = intf_gen_utils.sc_declare_channels(data, prj, indent, data)
    if len(channels):
        out.append( indent + '// channels')
        out.extend(channels)
        out.append('')


    first = True
    for instance, instData in data["subBlockInstances"].items():
        if first:
            out.append( indent + f'//instances contained in block')
            first = False

        instUsesConfig = intf_gen_utils.block_uses_config(prj.getBlockData(instData['instanceTypeKey']), prj)
        instCfg = cfg if instUsesConfig else ''
        out.append( indent + f'std::shared_ptr<{ instData["instanceType"] }Base{instCfg}> { instData["instance"] };')
    first = True

    for reg, regData in data["registers"].items():
        # Skip memory registers - they only have adapters, not hwRegister objects
        if regData['regType'] == 'memory':
            continue
        if first:
            out.append('')
            out.append( indent + f'//registers')
            first = False
        # Register data size from cpu is always 4-bytes aligned
        size = roundup_multiple(regData.get("maxBytes", regData["bytes"]), 4)
        regType = intf_gen_utils.sc_structure_field_type(regData, 'structure', 'structureKey', prj)
        out.append( indent + f'hwRegister< { regType }, {size} > { regData["register"] }; // { regData["desc"] }')

    if len(data["memories"]):
        out.append('')
        out.append( indent + f'memories mems;')
        out.append( indent + f'//memories')

    if data['blockInfo'].get('isRegHandler'):
        # For register handlers, use hwMemoryPort for all register-accessible memories
        mems = intf_gen_utils.get_sorted_memories(data)
        for mem, memData in mems.items():
            addrType = intf_gen_utils.sc_structure_field_type(memData, 'addressStruct', 'addressStructKey', prj)
            dataType = intf_gen_utils.sc_structure_field_type(memData, 'structure', 'structureKey', prj)
            out.append( indent + f'hwMemoryPort< { addrType }, { dataType } > { memData["memory"] }_adapter;')
        # Also handle memory registers
        for reg, regData in data['registers'].items():
            if regData.get('regType') == 'memory':
                addrType = intf_gen_utils.sc_structure_field_type(regData, 'addressStruct', 'addressStructKey', prj)
                dataType = intf_gen_utils.sc_structure_field_type(regData, 'structure', 'structureKey', prj)
                out.append( indent + f'hwMemoryPort< { addrType }, { dataType } > { regData["register"] }_adapter;')
    else:
        for mem, memData in data["memories"].items():
            dataType = intf_gen_utils.sc_structure_field_type(memData, 'structure', 'structureKey', prj)
            out.append( indent + f'hwMemory< { dataType } > { memData["memory"] };')
        
        # Handle LOCAL memory registers (block has registerDecode but not isRegHandler)
        if registerDecode:
            first = True
            for reg, regData in data['registers'].items():
                if regData['regType'] == 'memory':
                    # LOCAL memory register - needs channel, port, and adapter
                    if first:
                        out.append('')
                        out.append( indent + f'//local memory register infrastructure')
                        first = False
                    addrType = intf_gen_utils.sc_structure_field_type(regData, 'addressStruct', 'addressStructKey', prj)
                    dataType = intf_gen_utils.sc_structure_field_type(regData, 'structure', 'structureKey', prj)
                    out.append( indent + f'memory_channel< { addrType }, { dataType } > { regData["register"] }_channel;')
                    out.append( indent + f'memory_out< { addrType }, { dataType } > { regData["register"] }_port;')
                    out.append( indent + f'hwMemoryPort< { addrType }, { dataType } > { regData["register"] }_adapter;')

    # Memory connections (channel declarations)
    if 'memoryConnections' in data:
        for key, val in data['memoryConnections'].items():
            channelName = f'{val["interfaceName"]}'
            memKey = val['memoryBlockKey']
            memData = data['memories'][memKey]
            addrStruct = intf_gen_utils.sc_structure_field_type(memData, 'addressStruct', 'addressStructKey', prj)
            dataStruct = intf_gen_utils.sc_structure_field_type(memData, 'structure', 'structureKey', prj)
            out.append( indent + f'memory_channel<{addrStruct}, {dataStruct}> {channelName};')

    out.append('')
    out.append( indent + f'{ className }(sc_module_name blockName, const char * variant, blockBaseMode bbMode);')
    if args.noDestructor == False:
        out.append( indent + f'~{ className }() override = default;')
    if len(data["memories"]):
        out.append( indent + f'void setTimed(int nsec, timedDelayMode mode) override')
        out.append( indent + f'{{')
        out.append( indent + f'    { baseClassName }::setTimed(nsec, mode);')
        out.append( indent + f'    mems.setTimed(nsec, mode);')
        out.append( indent + f'}}')
#    else:
#        out.append( indent + f'using { className }Base::setTimed;')
#    out.append( indent + f'using { className }Base::setLogging;')
    if warningAndErrorReport() != 0:
        exit(1)
    out.append('')
    return("\n".join(out))

def addParams(args, prj, data):
    out = list()
    out.append('    // Register parameter variants with factory')
    out.append('    instanceFactory::addParam({')
    for variantKey, variantData in data["variants"].items():
        for key, value in variantData.items():
            out.append(f'        {{ "{data["blockName"]}.{value["variant"]}.{value["param"]}", {value["value"]} }},')
    out.append('    });')
    return("\n".join(out))
