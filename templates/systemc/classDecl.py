
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
    # The parent class is itself a class template only when the block has its
    # own `params:` (a "leaf parameterizable" block such as `ip` or `ipLeaf`).
    # Containers
    # that are flagged isParameterizable solely because parameterizable
    # structures transit their interface surface (e.g., `ip_top`) become
    # non-templated.
    hasOwnParams = data['hasOwnParams']
    cfg = intf_gen_utils.block_config_arg(hasOwnParams)
    defaultConfig = data['defaultConfig'] if isParameterizable else ''
    baseClassName = f'{ data["blockName"] }Base{cfg}'
    # registerDecode drives both the dependency includes (computed by the
    # shared helper) and the in-class register-handler members emitted below.
    registerDecode = data['addressDecode']['hasDecoder'] and (not data['enableRegConnections'] or data['blockInfo']['isRegHandler'])

    # Class dependency lines. In classic mode they are emitted inline ahead of
    # the class. In module mode the block-module global module fragment owns the
    # #includes and the `export module`/import lines
    # (templates/systemc/moduleScaffold.py blockModuleHeader); a module interface
    # forbids #include after the module declaration, so classDecl suppresses
    # them here.
    emittedDepLines = set()
    if args.mode == 'module':
        # The block-module header (moduleScaffold.blockModuleHeader / moduleExport)
        # emits the STRUCTURAL dependency imports (classIncludeContext) into the
        # module preamble but NOT the context `using namespace` lines: a
        # using-namespace closes the module preamble and every `import` must
        # precede it. Emitting the usings here, at the head of the classDecl
        # region (after the header region's trailing user gap), keeps that gap
        # inside an open, import-only preamble so a hand-added `import` stays
        # legal. They sit at module scope, before the class template, so the
        # unqualified-name coverage over the class and all user regions matches
        # classic mode.
        #
        # A C++20 module import is NOT transitive: the block module imports its
        # own Base module, but the interface-context types the base pulls in
        # (e.g. tag_st / NUM_TAGS, reached only through a payload context) do not
        # become visible in the block module just because the base has them. The
        # block BODY may spell those types unqualified, so re-emit them here for
        # every includeContext context beyond the structural classIncludeContext
        # the header already imports — mirroring what classic `.h/.cpp` mode
        # re-emitted below at the classDecl head. Emit the extra imports FIRST
        # (still inside the open, import-only preamble), then all using-namespace
        # lines. Deduplicated by line against the structural set moduleScaffold
        # already emits, so a context covered structurally is never re-imported.
        usings = list()
        for kind, line in intf_gen_utils.sc_class_dependency_includes(args, prj, data):
            emittedDepLines.add(line)
            if line.startswith('using namespace '):
                usings.append(line)
        fileMapKey = args.fileMapKey if args.fileMapKey else 'include_cppm'
        for context in data['includeContext']:
            if context in data['includeFiles'].get(fileMapKey, {}):
                for line in intf_gen_utils.cpp_context_include_lines(prj, data, context, fileMapKey):
                    if line in emittedDepLines:
                        continue
                    emittedDepLines.add(line)
                    if line.startswith('using namespace '):
                        usings.append(line)
                    else:
                        out.append(line)
        out.extend(usings)
    else:
        for kind, line in intf_gen_utils.sc_class_dependency_includes(args, prj, data):
            out.append(line)
            emittedDepLines.add(line)
        # A module import does not propagate the imported base module's own
        # context imports / using-directives the way the old textual
        # `<block>Base.h` did (a textual include re-ran those lines in the
        # includer's TU). The block implementation — this classic `.h` and the
        # `.cpp` that includes it — still spells the base's interface types
        # unqualified, so re-emit the base's interface-context imports (and their
        # using-directives) here for the ones the derived class does not already
        # reference directly. Deduplicated against the lines emitted above.
        fileMapKey = args.fileMapKey if args.fileMapKey else 'include_cppm'
        for context in data['includeContext']:
            if context in data['includeFiles'].get(fileMapKey, {}):
                for line in intf_gen_utils.cpp_context_include_lines(prj, data, context, fileMapKey):
                    if line not in emittedDepLines:
                        out.append(line)
                        emittedDepLines.add(line)

    # Contained-instance Base modules. Each child's Base/Inverted/Channels lives
    # in a C++20 module interface unit (`<child>.base`), so its class is attached
    # to that module. A global-module forward declaration of `<child>Base` would
    # name a DIFFERENT (global) entity than the module-attached class and would
    # not match the shared_ptr member's type, so classic mode imports the child
    # base module here to bring the complete, correctly-attached type into scope.
    # Module mode omits it: the block-module GMF/purview already imports each
    # child base (moduleScaffold.blockModuleHeader via sc_instance_includes).
    if data["subBlocks"] and args.mode != 'module':
        out.append(f'//contained instances base module imports')
        for line in intf_gen_utils.sc_instance_includes(data, prj):
            out.append(line)
    out.append('')

    # In module mode the block class is exported from the block-module
    # interface unit; `export` prefixes the first line of the declaration (the
    # template-head for own-params blocks, otherwise the SC_MODULE line).
    exportKw = 'export ' if args.mode == 'module' else ''
    if hasOwnParams:
        out.append(exportKw + intf_gen_utils.block_config_decl(hasOwnParams))
        out.append(f'SC_MODULE({ className }), public blockBase, public { baseClassName }')
    else:
        out.append(exportKw + f'SC_MODULE({ className }), public blockBase, public { baseClassName }')
    out.append('{')
    out.append('private:')
    if registerDecode:
        out.append('    void regHandler(void);')
        out.append('    addressMap _a2cRegs;')
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
    # the implementation TU into the program.
    out.append('public:')
    if hasOwnParams:
        out.append(indent + f'SC_HAS_PROCESS({ className });')
        out.append('')

    # Re-import inherited param constants and interface ports from the
    # templated base so block code uses the bare name (no Config:: on
    # constants, no this-> on ports). Two-phase lookup does not search a
    # dependent base, so the using-declarations are what make the bare
    # names resolve. Only templated (own-params) blocks have a dependent
    # base; non-templated blocks need no re-import.
    if hasOwnParams:
        reimports = list()
        for param in prj.data['blocks'][data['qualBlock']]['params']:
            reimports.append(f'using { baseClassName }::{ param["param"] };')
        seenPorts = set()
        for port_type in data['ports']:
            for port, port_data in data['ports'][port_type].items():
                if intf_gen_utils.sc_gen_modport_signal_blast(port_data, prj, data, swap_dir=False)['is_skip']:
                    continue
                if port_data['name'] in seenPorts:
                    continue
                seenPorts.add(port_data['name'])
                reimports.append(f'using { baseClassName }::{ port_data["name"] };')
        if reimports:
            out.append(indent + '// inherited names usable unqualified (no Config:: / this->)')
            for line in reimports:
                out.append(indent + line)
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

        # The child shared_ptr is typed by the child's per-variant Config
        # (e.g., `ipBase<ipVariant0Config>`), not the parent's `Config`.
        # Falls back to the child block's default Config when the descriptor's
        # values are empty.
        # The child Config is frozen from the child's own variant binding and
        # does NOT follow the parent's Config template parameter. A
        # Config-strict interface link from a multi-variant parent to a
        # parameterized child is therefore unsupported; use a single-variant
        # child, a Config-agnostic interface, or a thunker bind.
        instCfg = intf_gen_utils.cpp_config_arg(instData['instanceConfigSelection'])
        out.append( indent + f'std::shared_ptr<{ instData["instanceType"] }Base{instCfg}> { instData["instance"] };')

    # Cross-interface thunker member declarations. Emitted after the
    # subBlockInstances loop so the thunker's mem-init can reference
    # `instance->port` (C++ runs mem-inits in declaration order). When no
    # cross-interface ends are flagged, sc_declare_thunkers returns [] and no
    # line is emitted.
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

    if data['blockInfo']['isRegHandler']:
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

    # Re-import inherited parameterized types from the templated base so block
    # code uses the bare type name (no <Config>). Two-phase lookup does not
    # search a dependent base, so the using-declarations are what make the bare
    # names resolve; `typename` is required for type re-imports. Emitted at the
    # END of the generated region, AFTER the register/memory/instance member
    # declarations above: those declare NAME<Config> in-class, and a same-named
    # alias placed before them would turn NAME into a non-template and break
    # those decls. Only templated (own-params) blocks have a dependent base.
    if hasOwnParams and data['parameterizedDecls']:
        out.append('')
        out.append(indent + '// inherited parameterized types usable unqualified (no <Config>)')
        for decl in data['parameterizedDecls']:
            name = decl['body'][decl['declKind']]
            # An eval-derived parameterizable constant is re-imported as a value
            # (no `typename`); the base declares it as a class-local constexpr
            # drawn from Config, so the bare name resolves in this derived class.
            if decl['declKind'] == 'constant':
                out.append(indent + f'using { baseClassName }::{name};')
            else:
                out.append(indent + f'using typename { baseClassName }::{name};')

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

