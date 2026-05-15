import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.arch2codeHelper import printError, printWarning, warningAndErrorReport

# Does not alter the rendering
intf_gen_utils.LEGACY_COMPAT_MODE = True

def addressConstName(data, item):
    blockName = item.get('block', data['blockName'])
    return f"REG_ADDR_{blockName.upper()}_{item['name'].upper()}"

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
            print("error missing section, valid values are implementation, externs, headerDecl")
            exit()


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
    out.append(f'#include "{className}.h"')

    out += intf_gen_utils.sc_instance_includes(data, prj)

    if not hasOwnParams:
        out.append(f'SC_HAS_PROCESS({ className });\n')

    # Block registration trigger.
    #
    # Non-templated blocks: a free helper function plus a self-registering
    # static at namespace scope replaces the in-class struct registerBlock
    # / static registerBlock_ pattern. An active force-link function is
    # also emitted so generated parent / testbench code can guarantee that the
    # implementation TU is linked into the program under C++20 modules and
    # static-archive linking.
    #
    # Parameterized blocks: a self-registering static is emitted that
    # registers <className><DefaultConfig> for each variant the block
    # declares. Multi-Config-per-project bindings are deferred to a later
    # iteration that propagates per-instance Config tuples in
    # processYaml.py and emits a per-project trampoline TU.
    out.extend(blockRegistrarInitLines(args, prj, data, className, isParameterizable, hasOwnParams, defaultConfig))

    if data['addressDecode']['isApbRouter']:
        if hasOwnParams:
            out.append(templateDecl)
        out.append(f'void { qualClassName }::routerDecode(void) //handle apb routing for register\n{{')
        out.append(f'    log_.logPrint(std::format("SystemC Thread:{{}} started", __func__));')
        out.append(f'    decoder.decodeThread();\n}}\n')

    if registerDecode:
        busInterface = data["addressDecode"]["registerBusInterface"]
        busInterfaceRef = f'this->{busInterface}' if hasOwnParams else busInterface
        busStructs = ', '.join(data["addressDecode"]["registerBusStructs"].values())
        if hasOwnParams:
            out.append(templateDecl)
        out.append(f'void { qualClassName }::regHandler(void) {{ //handle register decode')
        out.append(f'    registerHandler< {busStructs} >(regs, {busInterfaceRef}, (1<<({data["addressDecode"]["addressBits"]}))-1); }}\n')

    if hasOwnParams:
        out.append(templateDecl)
    out.append(f'{ qualClassName }::{ className }(sc_module_name blockName, const char * variant, blockBaseMode bbMode)')
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
                defaultValue = f", {typenameKw}{channelStruct}::_packedSt({hex(prj.getConst(chnl_table[chnl]['default_value']))})"
            else:
                defaultValue = ''

            out.append(f'        ,{ channelBase }("{ channelTitle }", "{ src }"{extra}{autoMode}{defaultValue})')

            # Emit one thunker initialiser-list entry per flagged
            # cross-interface end. The thunker constructor receives (name,
            # parent-side channel, child port reference, block name).
            # Member-init order in C++ follows declaration order in the class
            # body; the thunker member is declared after the child instance
            # pointer in classDecl.py so the child->port reference is valid by
            # the time this entry runs. When no ends are flagged, no entry is
            # emitted.
            for flagged in intf_gen_utils._resolve_cross_interface_ends(chnlInfo, prj):
                memberName = intf_gen_utils._thunker_member_name(flagged, chnlInfo, is_connection_map=False)
                out.append(
                    f'        ,{memberName}("{memberName}", {channelBase}, '
                    f'{flagged["instance"]}->{flagged["portName"]}, name())'
                )


    for key, value in data['subBlockInstances'].items():
        instIsParameterizable = value['instanceTypeIsParameterizable']
        # The cast target uses the child's per-variant Config so it matches
        # the factory's variant-specific instantiation. Without this, the cast
        # would resolve to the parent's `<Config>` or the parent's defaultConfig
        # and dynamic_pointer_cast would return nullptr at runtime.
        instCfg = value['instanceConfigArg']
        # Generated createInstance passes the variant string only. The factory
        # key is `(blockType, variant)`; the variant string identifies the
        # per-variant Config policy unambiguously. Non-templated children also
        # emit an active force_link_<child>() call before the lookup so the
        # linker pulls the child implementation TU into the program.
        createCall = (
            f'instanceFactory::createInstance(name(), "{value["instance"]}", '
            f'"{value["instanceType"]}", "{value["variant"]}")'
        )
        if not instIsParameterizable:
            createCall = f'(force_link_{value["instanceType"]}(), {createCall})'
        out.append(
            f'        ,{ value["instance"] }(std::dynamic_pointer_cast'
            f'<{ value["instanceType"] }Base{instCfg}>({createCall}))'
        )

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
            out.append(f'        ,{ regData["register"] }({typenameKw}{regType}::_packedSt({defaultValue}))')
        else:
            out.append(f'        ,{ regData["register"] }()')
    if data['blockInfo'].get('isRegHandler'):
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
                'is_reg_handler': data['blockInfo'].get('isRegHandler')
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
                    linesExpr = wordLinesExpr(item, prj, isParameterizable, data)
                    if item['is_reg_handler']:
                        out.append(f'    regs.addMemory( {constName}, {memType}::_byteWidth, {linesExpr}, std::string(this->name()) + ".{item["name"]}", &{item["name"]}_adapter);')
                    else:
                        out.append(f'    regs.addMemory( {constName}, {memType}::_byteWidth, {linesExpr}, std::string(this->name()) + ".{item["name"]}", &{item["name"]});')
                else:  # memory_register
                    memType = intf_gen_utils.sc_structure_field_type(item, 'structure', 'structureKey', prj)
                    out.append(f'    regs.addMemory( {constName}, {memType}::_byteWidth, {wordLinesExpr(item, prj, isParameterizable, data)}, std::string(this->name()) + ".{item["name"]}", &{item["name"]}_adapter);')
            else:  # regular register
                if not register_comment_written:
                    register_comment_written = True
                    out.append(f'    // register registers for FW access')
                out.append(f'    regs.addRegister( {constName}, {item["size"]}, "{item["name"]}", &{item["name"]} );')

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
    if registerDecode and not data['blockInfo'].get('isRegHandler'):
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

def blockRegistrarInitLines(args, prj, data, className, isParameterizable, hasOwnParams, defaultConfig):
    """Emit SC block registration lines at namespace scope, immediately
    following the SC_HAS_PROCESS line.

    Two registration triggers coexist in the interim shape:

    * **Parameterized SC blocks** are registered by the per-block
      trampoline TU emitted via `<block>Registrar.cpp` (see
      `templates/systemc/blockRegistrar.py`). The trampoline owns the
      project-specific `(blockType, variant)` pairs that generated
      callers look up. The variant string identifies the per-variant Config
      policy unambiguously.

      A self-registering static is *additionally* emitted in this TU
      for parameterized blocks. Its purpose is the load-bearing
      trigger for *implicit* template instantiation of every
      per-variant `<B><PerVariantConfig>` in this TU. The
      self-registering lambda's `make_shared<<B><Config>>(...)` forces
      the compiler to instantiate the constructor body, regHandler
      body, and any other template members defined later in this
      `.cpp`. The trampoline TU sees only declarations from
      `<block>.h`; without this implicit instantiation the
      trampoline's `make_shared` would be an unresolved external at
      link time. The factory keys used by these in-block lambdas
      shadow the trampoline-registered entries — `std::map::emplace`
      keeps the first insertion, so whichever static initialises
      first wins; both lambdas construct the same target type, so
      either ordering is functionally equivalent. Once modules-mode
      lets the trampoline `import <block>;` and see the full template
      definitions directly (long-term plan), this in-block static is
      removed and the trampoline becomes the sole registration
      trigger.

    * **Non-templated SC blocks** continue to register themselves via
      a free helper plus a self-registering static at namespace scope in this
      TU, with an active force-link function declared in `<block>Base.h`.
    """
    out = list()

    # The in-block self-registering static no longer emits
    # `instanceFactory::addParam` calls. Block constructors read parameter
    # values from `Config::*` directly; the runtime parameter table is
    # decommissioned.

    # Per-variant Config descriptors. The in-block static's job is to force
    # implicit template instantiation of every per-variant
    # `<B><PerVariantConfig>` so the trampoline TU's `make_shared` does not
    # become an unresolved external at link time. We therefore emit one lambda
    # per variant, each targeting its own per-variant Config or the default
    # Config when no descriptor is available. The factory keys here use
    # `(blockType, variant)`, matching the trampoline-registered entries.
    #
    # Only leaf parameterizable blocks (hasOwnParams) are class templates.
    # Non-leaf parents that are flagged isParameterizable solely because
    # parameterizable structures transit their surface are emitted as a single
    # non-templated class; the registration lambda omits the template argument
    # list.
    variantConfigName = dict()
    if hasOwnParams:
        for desc in data['variantConfigs']:
            if desc['values']:
                variantConfigName[desc['variant']] = desc['configName']
            else:
                variantConfigName[desc['variant']] = defaultConfig

    def _targetClass(variant):
        if not hasOwnParams:
            return className
        configName = variantConfigName.get(variant, defaultConfig)
        return f'{className}<{configName}>'

    if data['variants']:
        registerCalls = []
        for variant in sorted(data['variants']):
            targetClass = _targetClass(variant)
            registerCalls.append(
                f'    instanceFactory::registerBlock("{className}_model", '
                f'[](const char * blockName, const char * variant, blockBaseMode bbMode) '
                f'-> std::shared_ptr<blockBase> {{ return static_cast<std::shared_ptr<blockBase>>'
                f'(std::make_shared<{targetClass}>(blockName, variant, bbMode)); }}, '
                f'"{variant}");'
            )
    else:
        targetClass = _targetClass('')
        registerCalls = [
            f'    instanceFactory::registerBlock("{className}_model", '
            f'[](const char * blockName, const char * variant, blockBaseMode bbMode) '
            f'-> std::shared_ptr<blockBase> {{ return static_cast<std::shared_ptr<blockBase>>'
            f'(std::make_shared<{targetClass}>(blockName, variant, bbMode)); }}, '
            f'"");'
        ]

    out.append(f'// === Block factory registration ({className}) ===')
    if not hasOwnParams:
        # Active force-link function. Declaration lives in <block>Base.h.
        # Generated parent / testbench code calls force_link_<B>() before
        # any factory lookup that may construct this block. The call
        # creates a real symbol reference into this TU, forcing the
        # linker to pull this object into the program even when nothing
        # else references symbols from it. This is required under C++20
        # modules and static-archive linking, where importing a base
        # interface or using string-keyed factory lookup does not
        # guarantee that this TU's static initializers run. Without the
        # active call, the self-registering static below can remain
        # unfired and instanceFactory::createInstance can fail at runtime.
        #
        # The predicate is "non-templated" so parent containers that are
        # flagged isParameterizable solely because parameterizable structures
        # transit their surface (e.g., `ip_top`) also receive the force-link
        # anchor.
        out.append(f'void force_link_{className}() {{}}')
        out.append('')
        out.append(f'void register_{className}_variants() {{')
        out.extend(registerCalls)
        out.append('}')
        out.append('')
        out.append('namespace {')
        out.append(f'[[maybe_unused]] int _{className}_registered = '
                   f'(register_{className}_variants(), 0);')
        out.append('} // namespace')
    else:
        # Parameterized block: the per-block trampoline owns the factory
        # registrations. This implementation TU keeps factory-shaped anchor
        # functions so the compiler instantiates the same block specializations
        # without inserting duplicate factory keys.
        instantiationVariants = sorted(data['variants']) if data['variants'] else ['']
        out.append('namespace {')
        for index, variant in enumerate(instantiationVariants):
            targetClass = _targetClass(variant)
            out.append(f'[[gnu::used]] std::shared_ptr<blockBase> _{className}_instantiate_variant_{index}(')
            out.append('    const char * blockName, const char * variant, blockBaseMode bbMode) {')
            out.append(f'    return static_cast<std::shared_ptr<blockBase>>(std::make_shared<{targetClass}>(blockName, variant, bbMode));')
            out.append('}')
            out.append(f'[[maybe_unused, gnu::used]] auto _{className}_instantiate_variant_{index}_anchor = &_{className}_instantiate_variant_{index};')
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
                out.append(f'            &apb_{instanceData["instance"]},')
        else:
            out.append('            nullptr,')

    # replace the last comma with a space
    if out:
        last = out.pop()
        last = last[:-1] + '})'
        out.append(last)
    return out
