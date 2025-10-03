
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
    out.append('#include "logging.h"')
    out.append('#include "instanceFactory.h"')
    baseInclude = prj.getModuleFilename('blockBase', data["blockName"], 'hdr')
    out.append(f'#include "{baseInclude}"')
    if  len(data['registers']) > 0 or len(data["memories"]) > 0:
        out.append('#include "addressMap.h"')
    if  len(data['registers']) > 0:
        out.append('#include "hwRegister.h"')
    if  len(data["memories"]) > 0:
        out.append('#include "hwMemory.h"')
    if args.fileMapKey:
        fileMapKey = args.fileMapKey
    else:
        fileMapKey = 'include_hdr'
    registerDecode = data['addressDecode']['hasDecoder'] and (not data['enableRegConnections'] or data['blockInfo']['isRegHandler'])

    for context in data['includeContext']:
        if context in data['includeFiles'][fileMapKey]:
            out.append(f'#include "{data["includeFiles"][fileMapKey][context]["baseName"]}"')
    if data['addressDecode']['isApbRouter']:
        out.append(f'#include "apbBusDecode.h"')

    if data["subBlocks"]:
        out.append(f'//contained instances forward class declaration')
        for key, value in data["subBlocks"].items():
            out.append(f'class { value }Base;')
    out.append('')

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
    out.append(indent + f'        instanceFactory::registerBlock("{ className }_model", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {{ return static_cast<std::shared_ptr<blockBase>> (std::make_shared<{ className }>(blockName, variant, bbMode));}}, "" );')
    out.append(indent + '    }')
    out.append(indent + '};')
    out.append(indent + 'static registerBlock registerBlock_;')
    out.append('public:')

    channels = intf_gen_utils.sc_declare_channels(data, prj, indent)
    if len(channels):
        out.append( indent + '// channels')
        out.extend(channels)
        out.append('')


    first = True
    for instance, instData in data["subBlockInstances"].items():
        if first:
            out.append( indent + f'//instances contained in block')
            first = False

        out.append( indent + f'std::shared_ptr<{ instData["instanceType"] }Base> { instData["instance"] };')
    first = True

    for reg, regData in data["registers"].items():
        if first:
            out.append('')
            out.append( indent + f'//registers')
            first = False
        # Register data size from cpu is always 4-bytes aligned
        size = roundup_multiple(regData["bytes"], 4)
        out.append( indent + f'hwRegister< { regData["structure"] }, {size} > { regData["register"] }; // { regData["desc"] }')

    if len(data["memories"]):
        out.append('')
        out.append( indent + f'memories mems;')
        out.append( indent + f'//memories')

    for mem, memData in data["memories"].items():
        out.append( indent + f'hwMemory< { memData["structure"] } > { memData["memory"] };')

    out.append('')
    out.append( indent + f'{ className }(sc_module_name blockName, const char * variant, blockBaseMode bbMode);')
    if args.noDestructor == False:
        out.append( indent + f'~{ className }() override = default;')
    if len(data["memories"]):
        out.append( indent + f'void setTimed(int nsec, timedDelayMode mode) override')
        out.append( indent + f'{{')
        out.append( indent + f'    { className }Base::setTimed(nsec, mode);')
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

