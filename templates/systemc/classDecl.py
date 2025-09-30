
from pysrc.arch2codeHelper import printError, warningAndErrorReport, roundup_multiple, roundup_pow2

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
    baseClassName = f'{ data["blockName"] }Base' 
    out.append('#include "logging.h"\n')
    out.append('#include "instanceFactory.h"\n')
    baseInclude = prj.getModuleFilename('blockBase', data["blockName"], 'hdr')
    out.append(f'#include "{baseInclude}"\n')
    if  len(data['registers']) > 0 or len(data["memories"]) > 0:
        out.append('#include "addressMap.h"\n')
    if  len(data['registers']) > 0:
        out.append('#include "hwRegister.h"\n')
    if  len(data["memories"]) > 0:
        out.append('#include "hwMemory.h"\n')
    if args.fileMapKey:
        fileMapKey = args.fileMapKey
    else:
        fileMapKey = 'include_hdr'
    registerDecode = data['addressDecode']['hasDecoder'] and (not data['enableRegConnections'] or data['blockInfo']['isRegHandler'])

    for context in data['includeContext']:
        if context in data['includeFiles'][fileMapKey]:
            out.append(f'#include "{data["includeFiles"][fileMapKey][context]["baseName"]}"\n')
    if data['addressDecode']['isApbRouter']:
        out.append(f'#include "apbBusDecode.h"\n')

    if data["subBlocks"]:
        out.append(f'//contained instances forward class declaration\n')
        for key, value in data["subBlocks"].items():
            out.append(f'class { value }Base;\n')
    out.append('\n')

    out.append(f'SC_MODULE({ className }), public blockBase, public { baseClassName }\n')
    out.append('{\n')
    out.append('private:\n')
    if registerDecode:
        out.append('    void regHandler(void);\n')
        out.append('    addressMap regs;\n')
    if data['addressDecode']['isApbRouter']:
        busStructs = ', '.join(data["addressDecode"]["registerBusStructs"].values())
        out.append('    void routerDecode(void);\n')
        out.append(f'    abpBusDecode< {busStructs} > decoder;\n')
    out.append('\n')
    indent = ' '*4
    out.append(indent + 'struct registerBlock\n')
    out.append(indent + '{\n')
    out.append(indent + '    registerBlock()\n')
    out.append(indent + '    {\n')
    if data['variants']:
        out.append(textwrap.indent(addParams(args, prj, data), indent*2))
    out.append(indent + '        // lamda function to construct the block\n')
    out.append(indent + f'        instanceFactory::registerBlock("{ className }_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {{ return static_cast<std::shared_ptr<blockBase>> (std::make_shared<{ className }>(blockName, variant, bbMode));}}, "" );\n')
    out.append(indent + '    }\n')
    out.append(indent + '};\n')
    out.append(indent + 'static registerBlock registerBlock_;\n')
    out.append('public:\n')

    channels = intf_gen_utils.sc_declare_channels(data, prj, indent)
    if len(channels):
        out.append( indent + '// channels\n')
        out.extend(channels)
        out.append('\n')


    first = True
    for instance, instData in data["subBlockInstances"].items():
        if first:
            out.append( indent + f'//instances contained in block\n')
            first = False

        out.append( indent + f'std::shared_ptr<{ instData["instanceType"] }Base> { instData["instance"] };\n')
    first = True

    for reg, regData in data["registers"].items():
        if first:
            out.append('\n')
            out.append( indent + f'//registers\n')
            first = False
        # Register data size from cpu is always 4-bytes aligned
        size = roundup_multiple(regData["bytes"], 4)
        out.append( indent + f'hwRegister< { regData["structure"] }, {size} > { regData["register"] }; // { regData["desc"] }\n')

    if len(data["memories"]):
        out.append('\n')
        out.append( indent + f'memories mems;\n')
        out.append( indent + f'//memories\n')

    for mem, memData in data["memories"].items():
        out.append( indent + f'hwMemory< { memData["structure"] } > { memData["memory"] };\n')

    out.append('\n')
    out.append( indent + f'{ className }(sc_module_name blockName, const char * variant, blockBaseMode bbMode);\n')
    if args.noDestructor == False:
        out.append( indent + f'~{ className }() override = default;\n')
    if len(data["memories"]):
        out.append( indent + f'void setTimed(int nsec, timedDelayMode mode) override\n')
        out.append( indent + f'{{\n')
        out.append( indent + f'    { className }Base::setTimed(nsec, mode);\n')
        out.append( indent + f'    mems.setTimed(nsec, mode);\n')
        out.append( indent + f'}}\n')
#    else:
#        out.append( indent + f'using { className }Base::setTimed;\n')
#    out.append( indent + f'using { className }Base::setLogging;\n')
    if warningAndErrorReport() != 0:
        exit(1)
    return("".join(out))

def addParams(args, prj, data):
    out = list()
    out.append('    // Register parameter variants with factory\n')
    out.append('    instanceFactory::addParam({\n')
    for variantKey, variantData in data["variants"].items():
        for key, value in variantData.items():
            out.append(f'        {{ "{data["blockName"]}.{value["variant"]}.{value["param"]}", {value["value"]} }},\n')
    out.append('    });\n')
    return("".join(out))

