import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.arch2codeHelper import printError, printWarning, warningAndErrorReport

# Does not alter the rendering
intf_gen_utils.LEGACY_COMPAT_MODE = True

def addressConstName(data, item):
    blockName = item.get('block', data['blockName'])
    return f"REG_ADDR_{blockName.upper()}_{item['name'].upper()}"

def bareParameterizedType(typeStr, hasOwnParams):
    # In templated (own-params) blocks the derived class re-imports each
    # parameterized type as a bare, class-local alias (NAME aliases
    # NAME<Config>). Out-of-line member-function references must therefore drop
    # the <Config> so the qualified-id (NAME::_packedSt / NAME::_byteWidth)
    # binds the class-local alias rather than the namespace template, which the
    # alias has shadowed. `typename` is decided by the caller on the original
    # <Config>-bearing string before stripping.
    if hasOwnParams:
        return typeStr.replace('<Config>', '')
    return typeStr

def wordLinesExpr(item, prj, useConfig=False, blockData=None):
    wordLines = item['wordLines']
    wordLinesKey = item.get('wordLinesKey', '')
    if useConfig and wordLinesKey and prj.data['constants'].get(wordLinesKey, {}).get('isParameterizable', False):
        return f"Config::{wordLines}"
    if useConfig:
        for constData in prj.data.get('constants', {}).values():
            if constData.get('constant') == wordLines and constData.get('isParameterizable', False):
                return f"Config::{wordLines}"
        if blockData:
            # Block params with no backing constant are Config fields, not
            # runtime addParam entries. Read them from `Config::*` like any
            # other parameterizable constant; the per-variant Config struct
            # carries the field with the variant's override value.
            for param in blockData.get('blockInfo', {}).get('params', []):
                if param.get('param') == wordLines:
                    return f"Config::{wordLines}"
    return wordLines

# args from generator line
# prj object
# data set dict
def render(args, prj, data):
    match args.section:
        case 'init':
            return(constructorInit(args, prj, data))
        case 'body':
            return(constructorBody(args, prj, data))
        case _:
            raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are init, body")


def constructorInit(args, prj, data):
    out = list()
    className = data["blockName"]
    isParameterizable = data['isParameterizable']
    # Only leaf parameterizable blocks (those with their own `params:`) remain
    # class templates. Non-leaf containers flagged isParameterizable solely
    # because parameterizable structures transit their surface are emitted as
    # non-templated classes.
    hasOwnParams = data['hasOwnParams']
    cfg = intf_gen_utils.block_config_arg(hasOwnParams)
    templateDecl = intf_gen_utils.block_config_decl(hasOwnParams)
    qualClassName = f'{className}{cfg}'
    baseClassName = f'{ className }Base{cfg}'
    defaultConfig = data['defaultConfig'] if isParameterizable else ''
    registerDecode = data['addressDecode']['hasDecoder'] and (not data['enableRegConnections'] or data['blockInfo']['isRegHandler'])

    # In module mode the constructor bodies live in the same translation unit as
    # the class (the block-module `.cppm`), and a module interface forbids
    # #include after `export module`. The class header self-include and the
    # contained-instance includes are therefore owned by the block-module GMF
    # (moduleScaffold.blockModuleHeader); classic mode keeps emitting them here.
    if args.mode != 'module':
        out.append(f'#include "{className}.h"')
        out += intf_gen_utils.sc_instance_includes(data, prj)

    if not hasOwnParams:
        out.append(f'SC_HAS_PROCESS({ className });\n')

    # Block registration trigger.
    #
    # Non-templated blocks: a free helper function plus a self-registering
    # static at namespace scope replaces the in-class struct registerBlock
    # / static registerBlock_ pattern. The static is marked
    # A2C_REGISTRATION_RETAIN so it survives dead-code elimination and
    # --gc-sections; under the project's direct-.o link model it is reachable
    # with no force-link reference from any parent or testbench TU.
    #
    # Parameterized leaf blocks emit nothing here: their factory registration
    # is owned by the per-assembler trampoline TU under registrar/.
    out.extend(blockRegistrarInitLines(args, prj, data, className, hasOwnParams))

    if data['addressDecode']['isApbRouter']:
        if hasOwnParams:
            out.append(templateDecl)
        out.append(f'void { qualClassName }::routerDecode(void) //handle apb routing for register\n{{')
        out.append(f'    log_.logPrint(std::format("SystemC Thread:{{}} started", __func__));')
        out.append(f'    decoder.decodeThread();\n}}\n')

    if registerDecode:
        busPort = data["addressDecode"]["registerBusPort"]
        busInterfaceRef = f'this->{busPort}' if hasOwnParams else busPort
        busStructs = ', '.join(data["addressDecode"]["registerBusStructs"].values())
        if hasOwnParams:
            out.append(templateDecl)
        out.append(f'void { qualClassName }::regHandler(void) {{ //handle register decode')
        out.append(f'    registerHandler< {busStructs} >(_a2cRegs, {busInterfaceRef}, (1<<({data["addressDecode"]["addressBits"]}))-1); }}\n')

    if hasOwnParams:
        out.append(templateDecl)
    out.append(f'{ qualClassName }::{ className }(sc_module_name blockName, const char * variant, blockBaseMode bbMode)')
    out.append(f'       : sc_module(blockName)')
    out.append(f'        ,blockBase("{ className }", name(), bbMode)')
    out.append(f'        ,{ baseClassName}(name(), variant)')

    if registerDecode:
        out.append(f'        ,_a2cRegs(log_)')
    if data['addressDecode']['isApbRouter']:
        out += addressDecoder(args, prj, data)

    chnl_table = dict()
    thunker_inits = []
    for channelType in data["connectDouble"]:
        for chnl, chnlInfo in data["connectDouble"][channelType].items():
            chnl_table[chnl] = intf_gen_utils.sc_gen_block_channels(chnlInfo, prj, data)

            channelBase = chnl_table[chnl]['chnl_name']
            srcInstances = [v.get("instanceType") or chnlInfo.get("block", "") for v in chnlInfo["ends"].values() if v["direction"] == "src"]
            dstInstances = [v.get("instanceType") or chnlInfo.get("block", "") for v in chnlInfo["ends"].values() if v["direction"] == "dst"]
            if len(srcInstances) != 1 or len(dstInstances) == 0:
                printError(f"connection {chnl!r} ({channelType}) needs exactly one src and at least one dst end")
                exit(warningAndErrorReport())
            src, dst = srcInstances[0], dstInstances[0]
            uniqueDstInstances = list(dict.fromkeys(dstInstances))
            if len(uniqueDstInstances) > 1:
                printWarning(
                    f"connection {chnl!r} ({channelType}) has multiple dst ends ({dstInstances}). "
                    f"Channel naming will be arbitrarily using {dst!r} as the destination instance"
                )
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
            if chnl_table[chnl]['set_initial_value']:
                # The structure type for the channel's default-value
                # initializer must match the channel's own template
                # arguments. The channel derives those arguments from the
                # connected child's per-variant Config; pass the same override
                # here so the `_packedSt` qualified-id agrees.
                channelStruct = intf_gen_utils.sc_structure_field_type(
                    chnlInfo, 'structure', 'structureKey', prj,
                    config_override=chnl_table[chnl].get('config_override'))
                # `typename` is required when the qualified-id depends on
                # the enclosing class template parameter Config — without
                # it C++ rejects the dependent type name in the
                # mem-initializer.
                typenameKw = 'typename ' if '<Config>' in channelStruct else ''
                channelStruct = bareParameterizedType(channelStruct, hasOwnParams)
                defaultValue = f", {typenameKw}{channelStruct}::_packedSt({hex(prj.getConst(chnl_table[chnl]['default_value']))})"
            else:
                defaultValue = ''

            out.append(f'        ,{ channelBase }("{ channelTitle }", "{ src }"{extra}{autoMode}{defaultValue})')

            # Collect one thunker initialiser-list entry per flagged
            # cross-interface end. These are emitted after subBlockInstances
            # below to match classDecl.py declaration order while preserving
            # the original connection/database order within the thunker group.
            for flagged in intf_gen_utils._resolve_cross_interface_ends(chnlInfo, prj):
                memberName = intf_gen_utils._thunker_member_name(flagged, chnlInfo, is_connection_map=False)
                thunker_inits.append(
                    f'        ,{memberName}("{memberName}", {channelBase}, '
                    f'{flagged["instance"]}->{flagged["portName"]}, name())'
                )


    for key, value in data['subBlockInstances'].items():
        instIsParameterizable = value['instanceTypeIsParameterizable']
        # The cast target uses the child's per-variant Config so it matches
        # the factory's variant-specific instantiation. Without this, the cast
        # would resolve to the parent's `<Config>` or the parent's defaultConfig
        # and dynamic_pointer_cast would return nullptr at runtime.
        instCfg = intf_gen_utils.cpp_config_arg(value['instanceConfigSelection'])
        # Generated createInstance passes the variant string and the child's
        # factory-lookup projectName. The factory key is
        # `(blockType, variant, projectName)`; the variant string identifies the
        # per-variant Config policy unambiguously. `createInstanceProjectName`
        # (a projectOpen view field) is the assembler for parameterizable and
        # same-project children, and the owning project for a plain
        # cross-project child (which self-registers only under its owner). The
        # parent holds no compile-time symbol reference to the child:
        # non-templated children self-register via an A2C_REGISTRATION_RETAIN
        # static in their own TU, reachable through direct-.o linking (see
        # instanceFactory.h).
        projectName = value['createInstanceProjectName']
        createCall = (
            f'instanceFactory::createInstance(name(), "{value["instance"]}", '
            f'"{value["instanceType"]}", "{value["variant"]}", "{projectName}")'
        )
        out.append(
            f'        ,{ value["instance"] }(std::dynamic_pointer_cast'
            f'<{ value["instanceType"] }Base{instCfg}>({createCall}))'
        )

    out.extend(thunker_inits)

    # connectionMap thunker initialiser-list entries. A connectionMap binds an
    # external parent port to a child instance port; when the two interfaces
    # differ, the thunker bridges them. The thunker is declared after the child
    # instance pointer in classDecl.py so the `instance->port` reference is
    # well-formed when this entry runs. An empty flagged list emits nothing.
    for key, value in data["connectionMaps"].items():
        flagged_ends = intf_gen_utils._resolve_cross_interface_ends(value, prj)
        if not flagged_ends:
            continue
        parentPort = f'this->{value["parentPortName"]}' if hasOwnParams else value["parentPortName"]
        for flagged in flagged_ends:
            memberName = intf_gen_utils._thunker_member_name(flagged, value, is_connection_map=True)
            out.append(
                f'        ,{memberName}("{memberName}", {parentPort}, '
                f'{flagged["instance"]}->{flagged["portName"]}, name())'
            )

    for reg, regData in data['registers'].items():
        # Skip memory registers - they only have adapters, not hwRegister objects
        if regData['regType'] == 'memory':
            continue
        if regData['regType'] == 'rw':
            defaultValue = hex(prj.getConst(regData["defaultValue"]))
            regType = intf_gen_utils.sc_structure_field_type(regData, 'structure', 'structureKey', prj)
            # `typename` is required when the qualified-id depends on the
            # enclosing class template parameter Config — without it C++
            # rejects the dependent type name in the mem-initializer.
            typenameKw = 'typename ' if '<Config>' in regType else ''
            regType = bareParameterizedType(regType, hasOwnParams)
            out.append(f'        ,{ regData["register"] }({typenameKw}{regType}::_packedSt({defaultValue}))')
        else:
            out.append(f'        ,{ regData["register"] }()')
    if data['blockInfo']['isRegHandler']:
        # For register handlers, use hwMemoryPort for all register-accessible memories
        mems = intf_gen_utils.get_sorted_memories(data)
        for mem, memData in mems.items():
            out.append(f'        ,{ memData["memory"] }_adapter({memData["memory"]})')
        # Also handle memory registers - connect adapter to base class port
        for reg, regData in data['registers'].items():
            if regData.get('regType') == 'memory':
                out.append(f'        ,{ regData["register"] }_adapter({ baseClassName }::{ regData["register"] })')
    else:
        for mem, memData in data['memories'].items():
            linesExpr = wordLinesExpr(memData, prj, isParameterizable, data)
            if memData["local"]:
                out.append(f'        ,{ memData["memory"] }(name(), "{ memData["memory"] }", mems, {linesExpr}, HWMEMORYTYPE_LOCAL)')
            else:
                out.append(f'        ,{ memData["memory"] }(name(), "{ memData["memory"] }", mems, {linesExpr})')
        
        # Initialize LOCAL memory registers
        if registerDecode:
            for reg, regData in data['registers'].items():
                if regData['regType'] == 'memory':
                    # LOCAL memory register - initialize channel, port, and adapter
                    channelName = f'{data["blockName"]}_{regData["register"]}'
                    out.append(f'        ,{ regData["register"] }_channel("{ channelName }", "{ data["blockName"] }")')
                    out.append(f'        ,{ regData["register"] }_port("{ regData["register"] }_port")')
                    out.append(f'        ,{ regData["register"] }_adapter({ regData["register"] }_port)')

    # Memory connections (channel initialization would happen here if variables declared in header)
    if len(data['memoryConnections']) > 0:
        for key, val in data['memoryConnections'].items():
            channelName = f'{val["interfaceName"]}'
            out.append(f'        ,{ channelName }("{ channelName }", "{ data["blockName"] }")')

    # take the list and return a string
    return("\n".join(out))

def constructorBody(args, prj, data):
    out = list()
    isParameterizable = data['isParameterizable']
    # Only leaf parameterizable blocks remain class templates. The body emits
    # `this->` qualifiers for dependent base-class member names, which is only
    # required inside class templates.
    hasOwnParams = data['hasOwnParams']

    out.append('{')
    first = True
    registerDecode = data['addressDecode']['hasDecoder'] and (not data['enableRegConnections'] or data['blockInfo']['isRegHandler'])
    if registerDecode:
        # Collect all register-accessible items and sort by offset
        mem_reg_items = []
        
        # Add memories
        mems = intf_gen_utils.get_sorted_memories(data)
        for mem, memData in mems.items():
            mem_reg_items.append({
                'type': 'memory',
                'offset': memData["offset"],
                'offset_value': f'0x{memData["offset"]:0x}',
                'name': memData["memory"],
                'block': memData["block"],
                'structure': memData["structure"],
                'structureKey': memData["structureKey"],
                'wordLines': memData["wordLines"],
                'wordLinesKey': memData.get("wordLinesKey", ""),
                'is_reg_handler': data['blockInfo']['isRegHandler']
            })
        
        # Add memory registers
        for reg, regData in data['registers'].items():
            if regData.get('regType') == 'memory':
                mem_reg_items.append({
                    'type': 'memory_register',
                    'offset': regData["offset"],
                    'offset_value': f'0x{regData["offset"]:0x}',
                    'name': regData["register"],
                    'block': regData["block"],
                    'structure': regData["structure"],
                    'structureKey': regData["structureKey"],
                    'wordLines': regData["wordLines"],
                    'wordLinesKey': regData.get("wordLinesKey", "")
                })
        
        # Add regular registers
        for reg, regData in data['registers'].items():
            if regData.get('regType') != 'memory':
                mem_reg_items.append({
                    'type': 'register',
                    'offset': regData["offset"],
                    'offset_value': f'0x{regData["offset"]:0x}',
                    'name': regData["register"],
                    'block': regData["block"],
                    'size': regData["bytes"]
                })
        
        # Sort all items by offset
        mem_reg_items.sort(key=lambda x: x['offset'])
        
        # Generate addMemory and addRegister calls in sorted order
        if mem_reg_items:
            out.append(f'    // Generated register/memory address offsets')
            for item in mem_reg_items:
                out.append(f'    constexpr uint64_t {addressConstName(data, item)} = {item["offset_value"]};')
            out.append('')
        memory_comment_written = False
        register_comment_written = False
        for item in mem_reg_items:
            constName = addressConstName(data, item)
            if item['type'] in ['memory', 'memory_register']:
                if not memory_comment_written:
                    memory_comment_written = True
                    out.append(f'    // register memories for FW access')
                if item['type'] == 'memory':
                    memType = intf_gen_utils.sc_structure_field_type(item, 'structure', 'structureKey', prj)
                    memType = bareParameterizedType(memType, hasOwnParams)
                    linesExpr = wordLinesExpr(item, prj, isParameterizable, data)
                    if item['is_reg_handler']:
                        out.append(f'    _a2cRegs.addMemory( {constName}, {memType}::_byteWidth, {linesExpr}, std::string(this->name()) + ".{item["name"]}", &{item["name"]}_adapter);')
                    else:
                        out.append(f'    _a2cRegs.addMemory( {constName}, {memType}::_byteWidth, {linesExpr}, std::string(this->name()) + ".{item["name"]}", &{item["name"]});')
                else:  # memory_register
                    memType = intf_gen_utils.sc_structure_field_type(item, 'structure', 'structureKey', prj)
                    memType = bareParameterizedType(memType, hasOwnParams)
                    out.append(f'    _a2cRegs.addMemory( {constName}, {memType}::_byteWidth, {wordLinesExpr(item, prj, isParameterizable, data)}, std::string(this->name()) + ".{item["name"]}", &{item["name"]}_adapter);')
            else:  # regular register
                if not register_comment_written:
                    register_comment_written = True
                    out.append(f'    // register registers for FW access')
                out.append(f'    _a2cRegs.addRegister( {constName}, {item["size"]}, "{item["name"]}", &{item["name"]} );')

        first = True
    for key, value in data["connectionMaps"].items():
        if first:
            first=False
            out.append(f'// hierarchical connections: instance port->parent port (dst->dst, src-src without channels)')

        # `this->` qualifier is required only when the surrounding class
        # is itself a template (so the inherited member is a dependent
        # name). The template head is kept only on blocks with their own params;
        # non-leaf parents no longer need the qualifier.
        parentPortName = f'this->{value["parentPortName"]}' if hasOwnParams else value["parentPortName"]
        # getBDCrossInterfaceBinds() marks maps whose direct child bind is
        # replaced by the thunker's downPort(m_chDown) bind. The thunker
        # initialiser is emitted earlier in the constructor's init list. An
        # empty flagged list leaves this loop's emission untouched.
        if intf_gen_utils._resolve_cross_interface_ends(value, prj):
            continue
        out.append(f'    { value["instance"] }->{ value["instancePortName"]}({ parentPortName });')


    connections = intf_gen_utils.sc_connect_channels(data, ' '*4, data, prj=prj)
    if connections:
        out.append(f'    // instance to instance connections via channel')
        out += connections

    # Memory connections
    if len(data['memoryConnections']) > 0:
        out.append(f'    // memory connections')
        for key, val in data['memoryConnections'].items():
            channelName = f'{val["interfaceName"]}'
            out.append(f'    {val["instance"]}->{val["memory"]}({channelName});')
            out.append(f'    {val["memory"]}.bindPort({channelName});')
    
    # Bind LOCAL memory register ports to channels
    if registerDecode and not data['blockInfo']['isRegHandler']:
        hasLocalMemReg = False
        for reg, regData in data['registers'].items():
            if regData['regType'] == 'memory':
                if not hasLocalMemReg:
                    out.append(f'    // bind local memory register ports to channels')
                    hasLocalMemReg = True
                out.append(f'    {regData["register"]}_port({regData["register"]}_channel);')

    first = True

    if data['addressDecode']['isApbRouter']:
        out.append(f'    SC_THREAD(routerDecode);')
    if registerDecode:
        out.append(f'    SC_THREAD(regHandler);')
    out.append(f'    log_.logPrint(std::format("Instance {{}} initialized.", this->name()), LOG_IMPORTANT );')
    # take the list and return a string
    return("\n".join(out))

def blockRegistrarInitLines(args, prj, data, className, hasOwnParams):
    """Emit SC block registration lines at namespace scope, immediately
    following the SC_HAS_PROCESS line.

    * **Non-templated SC blocks** register themselves via a free helper
      plus a self-registering static at namespace scope in this TU. The
      static carries A2C_REGISTRATION_RETAIN (see instanceFactory.h) so it
      survives dead-code elimination and the linker's --gc-sections pass;
      under the direct-.o link model the registration is reachable with no
      force-link reference. The predicate is "non-templated" so parent
      containers flagged isParameterizable solely because parameterizable
      structures transit their surface (e.g., `ip_top`) also self-register
      this way.

    * **Parameterized leaf blocks (hasOwnParams)** are class templates that
      live in a `<block>.cppm` module interface unit. Their factory
      registration is owned by the per-assembler trampoline TU
      (`registrar/<assembler>/<block>Registrar.cpp`, see
      `templates/systemc/blockRegistrar.py`), which `import`s the block
      module and instantiates `<block><Config>` directly. The module export
      makes the template member bodies visible to that consumer, so no
      instantiation anchor is needed in the module unit; this function emits
      nothing for them.
    """
    out = list()

    # Parameterized leaf blocks carry no registration material in their own
    # module unit — the per-assembler trampoline owns it.
    if hasOwnParams:
        return out

    # No `instanceFactory::addParam` calls are emitted. Block constructors read
    # parameter values from `Config::*` directly; there is no runtime parameter
    # table. The trailing projectName scopes the registration to this assembler
    # so the container's projectName-qualified createInstance lookup matches.
    projectName = prj.config.getConfig('PROJECTNAME')
    if data['variants']:
        registerCalls = []
        for variant in sorted(data['variants']):
            registerCalls.append(
                f'    instanceFactory::registerBlock("{className}_model", '
                f'[](const char * blockName, const char * variant, blockBaseMode bbMode) '
                f'-> std::shared_ptr<blockBase> {{ return static_cast<std::shared_ptr<blockBase>>'
                f'(std::make_shared<{className}>(blockName, variant, bbMode)); }}, '
                f'"{variant}", "{projectName}");'
            )
    else:
        registerCalls = [
            f'    instanceFactory::registerBlock("{className}_model", '
            f'[](const char * blockName, const char * variant, blockBaseMode bbMode) '
            f'-> std::shared_ptr<blockBase> {{ return static_cast<std::shared_ptr<blockBase>>'
            f'(std::make_shared<{className}>(blockName, variant, bbMode)); }}, '
            f'"", "{projectName}");'
        ]

    out.append(f'// === Block factory registration ({className}) ===')
    out.append(f'void register_{className}_variants() {{')
    out.extend(registerCalls)
    out.append('}')
    out.append('')
    out.append('namespace {')
    out.append(f'[[maybe_unused]] A2C_REGISTRATION_RETAIN int _{className}_registered = '
               f'(register_{className}_variants(), 0);')
    out.append('} // namespace')
    out.append('// === End block factory registration ===')
    out.append('')
    return out

def addressDecoder(args, prj, data):
    out = list()
    addressGroup = data['addressDecode']['addressGroup']
    addressGroupData = data['addressDecode']['addressGroupData']
    instanceWithRegApb = data['addressDecode']['instanceWithRegApb']
    qualInstance = next(iter(data['instances']))
    for conn, conn_data in data['ports']['connections'].items():
        if conn_data['dstKey'] == qualInstance:
            parent_interface_port = conn_data['name']
    for conn, conn_data in data['ports']['connectionMaps'].items():
        if conn_data['direction'] == 'dst':
            parent_interface_port = conn_data['name']


    # New-schema routers carry registerDecoderPort on the
    # addressBlock; the per-instance dispatch port name follows
    # `<registerDecoderPort>_<instance>` (e.g. `apbReg_uIp0`). Legacy
    # AddressGroups rows do not carry this field, so the legacy port
    # naming convention `apb_<instance>` remains the default.
    portPrefix = addressGroupData.get('registerDecoderPort') or 'apb'
    out.append(f'        ,decoder({addressGroupData["maxAddressSpaces"]}, {addressGroupData["addressIncrement"].bit_length()-1}, {parent_interface_port}, {{')
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
                out.append(f'            &{portPrefix}_{instanceData["instance"]},')
        else:
            out.append('            nullptr,')

    # replace the last comma with a space
    if out:
        last = out.pop()
        last = last[:-1] + '})'
        out.append(last)
    return out
