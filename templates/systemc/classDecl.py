
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
    isParameterizable = data['isParameterizable']
    # Stage 3.2 of plan-variant-config-unification.md: the parent class is
    # itself a class template only when the block has its own `params:`
    # (a "leaf parameterizable" block such as `ip` or `ipLeaf`). Containers
    # that are flagged isParameterizable solely because parameterizable
    # structures transit their interface surface (e.g., `ip_top`) become
    # non-templated.
    hasOwnParams = intf_gen_utils.block_has_own_params(prj, data['qualBlock'])
    cfg = intf_gen_utils.block_config_arg(hasOwnParams)
    defaultConfig = data['defaultConfig'] if isParameterizable else ''
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
    # Stage 6.3 of plan-variant-config-unification.md (Q10 / R2):
    # protocol-specific thunker headers. Emitted exactly when this
    # container declares at least one cross-interface thunker member
    # (sc_declare_thunkers below). The set is computed once and emitted
    # in sorted order so the generated text is deterministic.
    # Off-by-default: an empty protocol set emits no include.
    thunker_protocols = intf_gen_utils.sc_thunker_protocols(data, prj)
    for proto in sorted(thunker_protocols):
        out.append(f'#include "{proto}_port_thunker.h"')

    # Config policy include contexts are prepared by getBDIncludes().
    for context in sorted(data.get('configIncludeContext', {})):
        if context in data['includeFiles'].get('config_hdr', {}):
            out.append(f'#include "{data["includeFiles"]["config_hdr"][context]["baseName"]}"')
    
    if args.fileMapKey:
        fileMapKey = args.fileMapKey
    else:
        fileMapKey = 'include_cppm'

    for context in data['classIncludeContext']:
        if context in data['includeFiles'].get(fileMapKey, {}):
            includeName = data["includeFiles"][fileMapKey][context]["baseName"]
            if fileMapKey == 'include_cppm':
                moduleName = intf_gen_utils.module_name_from_include(includeName)
                out.append(f'import {moduleName};')
                out.append(f'using namespace {intf_gen_utils.namespace_name_from_include(includeName)};')
            else:
                out.append(f'#include "{includeName}"')
        elif fileMapKey == 'include_cppm' and context in data['includeFiles'].get('include_hdr', {}):
            # Header-mode fallback: projects that publish only
            # `include_hdr` entries (no `include_cppm`) still need the
            # context's struct types reachable from this TU.
            includeName = data["includeFiles"]['include_hdr'][context]["baseName"]
            out.append(f'#include "{includeName}"')
    if data['addressDecode']['isApbRouter']:
        out.append(f'#include "apbBusDecode.h"')

    if data["subBlocks"]:
        out.append(f'//contained instances forward class declaration')
        for key, value in data["subBlocks"].items():
            # Stage 3.2 of plan-variant-config-unification.md: a child's
            # Base class is itself a class template only when the child has
            # its own params. Children flagged isParameterizable solely
            # because parameterizable structures transit their surface are
            # forward-declared as plain classes.
            if intf_gen_utils.block_has_own_params(prj, key):
                out.append(f'template<typename Config> class { value }Base;')
            else:
                out.append(f'class { value }Base;')
    out.append('')

    if hasOwnParams:
        out.append(intf_gen_utils.block_config_decl(hasOwnParams))
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
    # Registration moved out of the class body. Parameterized and
    # non-templated blocks reach the factory through a self-registering
    # static emitted by templates/systemc/constructor.py. Non-templated
    # blocks additionally carry an active force-link function in
    # <block>Base.h so that modules-mode and static-archive linking pull
    # the implementation TU into the program. See plan-block-registration.md
    # "Force-Link Function" for the rationale.
    out.append('public:')
    if hasOwnParams:
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

        # Stage 3.1 of plan-variant-config-unification.md (D4 Option (a)):
        # the child shared_ptr is typed by the child's per-variant Config
        # (e.g., `ipBase<ipVariant0Config>`), not the parent's `Config`.
        # Falls back to the child block's legacy `<context>DefaultConfig`
        # when the descriptor's values are empty.
        instCfg = intf_gen_utils.resolve_instance_config_arg(prj, instData)
        out.append( indent + f'std::shared_ptr<{ instData["instanceType"] }Base{instCfg}> { instData["instance"] };')

    # Stage 6.3 of plan-variant-config-unification.md (Q10 / R2):
    # cross-interface thunker member declarations. Emitted AFTER the
    # subBlockInstances loop so the thunker's mem-init can reference
    # `instance->port` (C++ runs mem-inits in declaration order). When
    # no cross-interface ends are flagged, sc_declare_thunkers returns
    # [] and no line is emitted — the off-by-default invariant required
    # by the brief.
    thunkers = intf_gen_utils.sc_declare_thunkers(data, prj, indent, data)
    if thunkers:
        out.append('')
        out.append(indent + '// cross-interface thunkers')
        out.extend(thunkers)

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

