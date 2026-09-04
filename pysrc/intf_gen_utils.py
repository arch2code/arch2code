# Interfaces Definition

# FIXME Add extra space in templated instances < > to match existing
# Remove when refactoring
LEGACY_COMPAT_MODE = False

from pysrc.arch2codeHelper import printError
import pysrc.processYaml as processYaml

def get_set_intf_types(ifType, block_data):
    """Get set of interface names, resolving any type aliases
    
    Args:
        ifType: Interface type or collection of interface types
        block_data: Block data dict containing interface_type_mappings
    
    Returns:
        Set of canonical interface type names
    """
    return {get_intf_type(intf, block_data) for intf in ifType}

def get_intf_type(ifType, block_data):
    """Resolve interface type alias to canonical interface type
    
    Args:
        ifType: Interface type (may be an alias like 'reg_ro')
        block_data: Block data dict containing interface_type_mappings
    
    Returns:
        Canonical interface type (e.g., 'reg_ro' -> 'status')
    """
    # An alias with no mapping row passes through unchanged: only register
    # interface types are aliased, every other interfaceType is already canonical.
    type_mappings = block_data['interface_type_mappings']
    return type_mappings.get(ifType, ifType)

def get_intf_data(data, prj_data):
    #ret = data.get('interfaceData', data.get('connection', {}).get('interfaceData', None))
    ret = data.get('interfaceData', None)
    if ret:
        return ret
    else:
        #interfaceKey = data.get('interfaceKey', data.get('connection', {}).get('interfaceKey', None))
        interfaceKey = data.get('interfaceKey', None)
        if interfaceKey:
            return prj_data.data['interfaces'].get(interfaceKey, None)
        else:
            ret =  {'structures': [{'structureType': 'data_t', 'structure': data['structure'], 'structureKey': data['structureKey']}],
                    'interfaceType': data['interfaceType'],
                    'desc': data.get('desc', '')}
            # Only add addressStruct if exists
            if data['addressStruct']:
                ret['structures'].append({'structureType': 'addr_t', 'structure': data['addressStruct'], 'structureKey': data['addressStructKey']})
            return ret
def get_channel_name(data):
    channel_base = data["interfaceName"]
    if data.get('channelCount', 0) > 1:
        channel_base = f"{channel_base}_{data['index']}"
    return channel_base

class intfEvalDSL:

    def __init__(self, prj_data, struct_key):
        self.prj_data = prj_data
        self.struct_key = struct_key

    def to_bytes(self):
        w = get_struct_width(self.struct_key, self.prj_data['structures'])
        return w // 8 + (1 if w % 8 != 0 else 0)

def sv_type_width_expression(type_info, prj):
    is_signed = type_info['isSigned']
    signed_extra = '+1' if is_signed else ''

    wl2 = type_info['widthLog2']
    if wl2 != '':
        return f"$clog2({wl2}+1){signed_extra}"

    wl2m1 = type_info['widthLog2minus1']
    if wl2m1 != '':
        return f"$clog2({wl2m1}){signed_extra}"

    return str(type_info['width'])

def _is_one(expr):
    try:
        return int(expr) == 1
    except (TypeError, ValueError):
        return False

def sv_struct_width_expression(struct_key, prj):
    struct = prj.data['structures'][struct_key]
    terms = []
    for _, var_data in reversed(struct['vars'].items()):
        if var_data['entryType'] in ['NamedVar', 'NamedType']:
            type_info = prj.data['types'][var_data['varTypeKey']]
            expr = sv_type_width_expression(type_info, prj)
        elif var_data['entryType'] == 'NamedStruct':
            expr = sv_struct_width_expression(var_data['subStructKey'], prj)
        elif var_data['entryType'] == 'Reserved':
            expr = str(var_data['bitwidth'])
        else:
            expr = str(var_data['bitwidth'])

        array_size = str(var_data['arraySize'])
        if array_size != '0' and not _is_one(array_size):
            if '+' in expr or '-' in expr:
                expr = f"({expr})"
            expr = f"{expr}*{array_size}"
        terms.append(expr)
    return ' + '.join(terms) if terms else '0'

def sv_boundary_struct_width_expression(struct_key, prj):
    struct = prj.data['structures'][struct_key]
    if not struct['isParameterizable']:
        return str(struct['width'])
    return sv_struct_width_expression(struct_key, prj)

def sv_packed_bit_type(width_expr):
    if _is_one(width_expr):
        return 'bit'
    try:
        width = int(width_expr)
        return f"bit [{width-1}:0]"
    except (TypeError, ValueError):
        return f"bit [({width_expr})-1:0]"

def sv_gen_modport_signal_blast(port_data, prj, block_data, swap_dir=False):
    out = {}
    prj_data = prj.data
    connectionData = port_data.get('connection', {})
    intf_data = get_intf_data(connectionData, prj)
    intf_type = get_intf_type(intf_data['interfaceType'], block_data)
    intf_name = port_data['name']
    intf_modp = port_data['direction']
    intf_param = dict()
    hdl_param = dict()

    interface_defs = block_data['interface_defs']
    assert(intf_type in interface_defs and
           intf_modp in interface_defs[intf_type]['modports'])

    intf_def = interface_defs[intf_type]

    if swap_dir :
        intf_modp = inverse_portdir(intf_modp)

    out['description'] = intf_data['desc']

    # Parameter
    params = intf_def.get('parameters') or {}
    for param in filter(lambda item: params[item]['datatype'] == 'struct', params):
        struct_data = list(filter(lambda item: item['structureType'] == param, intf_data['structures']))
        assert(len(struct_data) == 1); # expecting one exact match
        intf_param[param] = struct_data[0]

    hdl_params = intf_def.get('hdlparams', {}) or {}
    for param in hdl_params:
        assert(hdl_params[param]['datatype'] in ['integer'])
        if hdl_params[param]['isEval']:
            key, data = hdl_params[param]['value'].split('.')
            if key in intf_param:
                data_obj = intfEvalDSL(prj_data, intf_param[key]['structureKey'])
                eval_str = 'data_obj{}'.format('.' + data)
                hdl_param[param] = eval(eval_str)
                assert(isinstance(hdl_param[param], int))

    # Interface parameters declaration
    parameters_decl = ', '.join([".{}({})".format(param, intf_param[param]['structure']) for param in params])

    # Interface ports declaration
    intf_ports_decl = ''

    out['intf_decl'] = f"{intf_type}_if #({parameters_decl}) {intf_name}({intf_ports_decl});"

    out['intf_modp'] = intf_modp

    # Blasted interface ports. 'ports' carries the full ANSI declarations;
    # 'names' carries the bare flattened signal names, consumed by the variant
    # trampoline when wiring the canonical body instance by name.
    out['ports'] = []
    out['names'] = []
    for intf_sig in intf_def['signals']:
        modp_signals = intf_def['modports'][intf_modp]['modportGroups']
        # Safely get inputs and outputs lists
        inputs = modp_signals.get('inputs', {}).get('groups', {}) or {}
        port_dir = 'input' if intf_sig in inputs else 'output'
        port_type = intf_def['signals'][intf_sig]['signalType']
        port_name = f"{intf_name}_{intf_sig}"
        if port_type in intf_param.keys():
            width_expr = sv_boundary_struct_width_expression(intf_param[port_type]['structureKey'], prj)
            port_type = sv_packed_bit_type(width_expr)
        elif port_type in hdl_param.keys():
            w = hdl_param[port_type]
            port_type = 'bit' if w == 1 else f"bit [{w-1}:0]"
        elif port_type == 'bool':
            port_type = 'bit'
        out['ports'].append(f"{port_dir} {port_type} {port_name}")
        out['names'].append(port_name)

    # Assignment port <-> interface
    out['assign'] = []
    for intf_sig in intf_def['signals']:
        modp_signals = intf_def['modports'][intf_modp]['modportGroups']
        # Safely get inputs and outputs lists
        inputs = modp_signals.get('inputs', {}).get('groups', {}) or {}
        assign_lhs = f"{intf_name}.{intf_sig}" if intf_sig in inputs else f"{intf_name}_{intf_sig}"
        assign_rhs = f"{intf_name}_{intf_sig}" if intf_sig in inputs else f"{intf_name}.{intf_sig}"
        out['assign'].append(f"assign #0 {assign_lhs} = {assign_rhs};")

    return out

def sv_gen_ports(data, prj, indent, block_data):
    out = []
    for sourceType in data['ports']:
        for port, port_data in data['ports'][sourceType].items():
            connectionData = port_data.get('connection', {})
            intf_data = get_intf_data(connectionData, prj)
            intf_type = get_intf_type(intf_data['interfaceType'], block_data)
            out.append(f"{indent}{intf_type}_if.{port_data['direction']} {port_data['name']},")
    out.append(f"{indent}input clk, rst_n")
    out.append(");\n")
    return out

def sc_connect_channels(data, indent, block_data, prj=None):
    # Cross-interface child-end binds are annotated in the language-agnostic block view.
    # The thunker emitted in the constructor's initialiser list performs
    # the equivalent bind internally via downPort(m_chDown).
    out = []
    for channelType in data["connectDouble"]:
        out.extend(sc_connect_channel_type(data["connectDouble"][channelType], indent, block_data, prj=prj))
    return out

def sc_connect_channel_type(data, indent, block_data, prj=None):
    out = []
    interface_defs = block_data['interface_defs']
    for key, value in data.items():
        channelBase = get_channel_name(value)
        if (len(value['ends']) > 2):
            intf_type = get_intf_type(value['interfaceType'], block_data)
            multiDst = interface_defs[intf_type]['multiDst']
            if not multiDst:
                printError(f"connection {key} has more than 2 ends. Only status interfaces (including ro registers) can have multiple dst connections")
        # Suppress direct child binds already marked by getBDCrossInterfaceBinds().
        suppressed = set()
        for flagged in _resolve_cross_interface_ends(value, prj):
            if flagged['endKey']:
                suppressed.add(flagged['endKey'])
        for end, endvalue in value["ends"].items():
            if end in suppressed:
                continue
            out.append(f'{indent}{ endvalue["instance"] }->{ endvalue["portName"]}({ channelBase });')
    return out

def sc_instance_includes(data, prj):
    out = []
    includes = dict()
    # create a dict of unique includes, keyed by the child's project-qualified
    # module name so the import matches the child's own qualified `.base` export.
    for key, value in data['subBlockInstances'].items():
        includes[value["instanceTypeModuleName"]] = None
    # Each contained instance's Base is a C++20 module interface unit
    # (`<child>Base.cppm`, `export module <child>.base;`); consumers import it.
    # In a classic TU (constructor/testbench .cpp) the import sits at namespace
    # scope; in a block-module GMF caller the import must be placed after
    # `export module` (module purview), not in the global module fragment.
    for include in includes:
        out.append(f'import {cpp_base_module_name(include)};')
    return out

# Class template parameter of a parameterized BLOCK: the Config the block itself
# is instantiated at. Per-instance spellings that defer to the container name
# this symbol, so it resolves wherever they render inside the container's own
# class template.
BLOCK_CONFIG_PARAM = 'Config'

def sc_struct_type_name(struct_name, struct_key, prj, use_config=True, config_override=None):
    # config_override: when supplied (and the structure is parameterizable),
    # the named Config replaces the literal `Config` template parameter in
    # the emitted type. This lets channels use the connected child's
    # per-variant Config without requiring the parent to be a class template.
    if use_config and struct_key and prj.data['structures'].get(struct_key, {}).get('isParameterizable', False):
        suffix = config_override if config_override else BLOCK_CONFIG_PARAM
        return f"{struct_name}<{suffix}>"
    return struct_name

def sc_structure_field_type(row, field_name, key_field_name, prj, use_config=True, config_override=None):
    return sc_struct_type_name(row[field_name], row.get(key_field_name, ''), prj, use_config, config_override)

def sc_hdl_bridge_type(struct_param, prj):
    struct_key = struct_param['structureKey']
    struct_name = sc_struct_type_name(struct_param['structure'], struct_key, prj)
    if prj.data['structures'][struct_key]['isParameterizable']:
        return f"sc_bv<{struct_name}::_bitWidth>"
    w = get_struct_width(struct_key, prj.data['structures'])
    return 'bool' if w == 1 else f"sc_bv<{w}>"

def block_config_decl(is_parameterizable):
    return 'template<typename Config>' if is_parameterizable else ''

def block_config_arg(is_parameterizable):
    return f'<{BLOCK_CONFIG_PARAM}>' if is_parameterizable else ''

def resolve_dut_variant_selection(block_data, variant):
    # Map a generated testbench file's `GENERATED_CODE_PARAM --variant=<name>`
    # to the concrete per-variant Config and instanceFactory variant key that
    # the rest of the testbench emission threads through.
    #
    #
    # When the DUT block has own `params:`, a missing variant selects the
    # anonymous/default variant when that descriptor exists. When it has no own
    # params (containers like `ip_top`), a missing variant is tolerated and the
    # block's defaultConfig returned.
    is_parameterizable = bool(block_data['isParameterizable'])
    default_config = block_data['defaultConfig'] if is_parameterizable else ''
    variant_configs = block_data['variantConfigs']
    has_own_params = bool(block_data['hasOwnParams'])
    if not has_own_params:
        return {
            'configName':     default_config,
            'factoryVariant': variant or '',
        }
    available = [d['variant'] for d in variant_configs]
    # The variant list reported below belongs to the block this VIEW was built
    # for, so the diagnostic names that block. `blockName` is not it on the
    # External path: refactor_tbExternal repoints it at the excluded DUT before
    # any section renders, which would name the DUT while listing the testbench
    # container's variants.
    block_name = block_data['blockInfo']['block']
    variant = variant or ''
    for desc in variant_configs:
        if desc['variant'] != variant:
            continue
        config_name = cpp_descriptor_config_name(desc, default_config)
        return {'configName': config_name, 'factoryVariant': variant}
    if not variant:
        printError(
            f"Testbench generation for parameterizable block {block_name!r} "
            f"requires a file-level `--variant=<name>` on GENERATED_CODE_PARAM "
            f"because it has no anonymous/default variant. "
            f"Available variants: {available!r}."
        )
        return {'configName': '', 'factoryVariant': ''}
    printError(
        f"Testbench generation for block {block_name!r} requested unknown "
        f"variant {variant!r}. Available variants: {available!r}."
    )
    return {'configName': '', 'factoryVariant': ''}

def _resolve_cross_interface_ends(conn_data, prj):
    # Cross-interface semantics are part of the block-data view assembled
    # by processYaml.projectOpen.getBDCrossInterfaceBinds(). Keep this
    # accessor intentionally dumb so templates do not duplicate validation
    # or discovery logic.
    return conn_data.get('crossInterfaceEnds', []) or []


def cpp_module_name(includeName):
    # C++20 module name spelling for a context's project-owned include identity.
    # The identity is supplied by projectCreate/projectOpen; this helper only
    # sanitizes it into a legal module-name token. The sanitization primitive is
    # owned by core (processYaml.sanitizeIdentifierToken) so the template layer and
    # the projectCreate foreign-Config stub cannot drift.
    return processYaml.sanitizeIdentifierToken(includeName)

def cpp_block_module_name(blockName):
    # C++20 module name for a parameterizable block's own interface unit
    # (`<block>.cppm`). Spelled `<block>.block` so it stays distinct from the
    # context types module (`<context>`, from `<context>Includes.cppm`) the
    # block imports. The block identity comes from the block view
    # (`data['blockName']`), not from a filename.
    return f'{cpp_module_name(blockName)}.block'

def cpp_base_module_name(blockName):
    # C++20 module name for a block's Base/Inverted/Channels interface unit
    # (`<block>Base.cppm`). Spelled `<block>.base` so it stays distinct from the
    # block impl module (`<block>.block`, from `<block>.cppm`) and the context
    # types module (`<context>`) the base imports.
    return f'{cpp_module_name(blockName)}.base'

def cpp_tb_module_name(blockName):
    # C++20 module name for a block's testbench-top interface unit
    # (`<block>Testbench.cppm`). Spelled `<block>.testbench` so it stays distinct
    # from the block impl module (`<block>.block`), the base module
    # (`<block>.base`) and the External unit (`<block>.external`) it imports.
    return f'{cpp_module_name(blockName)}.testbench'

def cpp_tb_external_module_name(blockName):
    # C++20 module name for a block's testbench External interface unit
    # (`<block>External.cppm`). Spelled `<block>.external` so it stays distinct
    # from the testbench top (`<block>.testbench`) that imports it. For an
    # External retargeted at a `_tb` container the block identity is the excluded
    # DUT instance's module name resolved by refactor_tbExternal.
    return f'{cpp_module_name(blockName)}.external'

def cpp_registrar_module_name(projectName, parentBlock, childBlock):
    # C++20 module name for a parent-owned registrar trampoline unit. Spelled
    # `<project>.<parent>.<child>.registrar` so the same child reused under two
    # parents yields two distinct registrar modules. The identity components
    # (project, parent, child) come from persisted data.
    return f'{cpp_module_name(projectName)}.{cpp_module_name(parentBlock)}.{cpp_module_name(childBlock)}.registrar'


def cpp_child_registrar_module_name(projectName, childBlock):
    # Stable C++20 module identity for the one physical registrar aggregate
    # owned by a (project, child) pair. Parent-specific factory domains remain
    # inside the translation unit rather than multiplying physical modules.
    return f'{cpp_module_name(projectName)}.{cpp_module_name(childBlock)}.registrar'

# Template parameter of a Config emitted for a variant that sources parameters
# from its container: the Config of the block the instance sits in.
CONTAINER_CONFIG_PARAM = 'ContainerConfig'

def cpp_container_typed_instance_arg(instance):
    # Explicit template argument for `instanceFactory::createInstance<Impl>` when
    # the child is typed by the CONTAINER's Config, empty otherwise. Such a child
    # is a family of C++ types and the factory key carries no Config dimension,
    # so the container names the class directly.
    selection = instance['instanceConfigSelection']
    if not selection['containerTyped']:
        return ''
    return f'<{instance["instanceType"]}{cpp_config_arg(selection)}>'

def sc_instance_config_imports(data):
    # `import` lines a container needs for the Configs of the instances it holds:
    # the owner-qualified foreign-Config module of each child bound to an
    # assembler-declared variant, then the block module of each child typed by
    # this container's Config, whose implementation class the container names at
    # its createInstance site.
    out = []
    for key in sorted(data['foreignConfigModules']):
        mod = data['foreignConfigModules'][key]
        out.append(f'import {cpp_config_module_name(mod["project"], mod["block"])};')
    for key, moduleName in sorted(data['containerTypedChildModules'].items()):
        out.append(f'import {cpp_block_module_name(moduleName)};')
    return out

def cpp_config_module_name(projectName, childBlock):
    # C++20 module name for the owner-qualified foreign per-variant Config module
    # interface unit of a reused child. Spelled `<project>.<child>.config` so the
    # same reused child yields ONE config module per owning project (NOT per
    # parent): every parent-owned registrar and container in that project that
    # binds a foreign variant of the child imports the same module. The identity
    # components (project, child) come from persisted data / projectOpen views.
    return f'{cpp_module_name(projectName)}.{cpp_module_name(childBlock)}.config'

def cpp_variant_config_name(projectName, blockName, variant, isForeign=False):
    # C++ struct name for a per-variant Config, spelled entirely in the template
    # layer from the neutral (project, block, variant, isForeign) components a
    # projectOpen view supplies. The bare tail `<block><Variant>Config` is the
    # same-project spelling; a foreign (assembler-declared) variant is owner-
    # qualified as `<project>_<block><Variant>Config` so two projects' same-named
    # local variant of one reused child are DISTINCT C++ types. On a monolithic
    # build nothing is foreign, so the bare form is emitted.
    if variant == '':
        bare = f'{blockName}Config'
    else:
        bare = f'{blockName}{variant[:1].upper()}{variant[1:]}Config'
    if isForeign:
        return f'{cpp_module_name(projectName)}_{bare}'
    return bare


def cpp_config_expression_name(expression):
    # C++ spelling of a persisted Config expression. A containerParam binding
    # composes the child's Config template with the concrete parent Config.
    if expression['kind'] == 'default':
        return expression['name']
    descriptor = expression['descriptor']
    name = cpp_descriptor_config_name(descriptor, '')
    if expression['kind'] == 'template':
        return f'{name}<{cpp_config_expression_name(expression["container"])}>'
    return name

def cpp_descriptor_config_name(desc, defaultConfig):
    # Emitted C++ struct name for one neutral per-variant descriptor, as
    # persisted by calcVariantConfigDescriptors. A descriptor with no Config
    # fields emits as `defaultConfig`; otherwise it spells its own variant's
    # struct.
    if not desc['values']:
        return defaultConfig
    return cpp_variant_config_name(desc['declaringProject'], desc['block'],
                                   desc['variant'], desc['isForeign'])

def cpp_config_struct_name(configSelection):
    # Emitted C++ Config struct name for a neutral per-instance selection from
    # _resolveInstanceConfigFields: '' when the block is not parameterizable, the
    # selected descriptor's struct when it binds a per-variant override, else the
    # block's default Config.
    if configSelection['inheritContainer']:
        # Contained-block config inheritance: spell the container's own template
        # symbol; C++ resolves the concrete struct at the container's site.
        return BLOCK_CONFIG_PARAM
    if not configSelection['isParameterizable']:
        return ''
    desc = configSelection['descriptor']
    if desc is None:
        return configSelection['defaultConfig']
    name = cpp_descriptor_config_name(desc, configSelection['defaultConfig'])
    if desc['containerSourced']:
        # A variant that sources parameters from its container emits a Config
        # TEMPLATE, so the site names it applied to the container's own Config:
        # the concrete struct is resolved where the container is instantiated.
        # Every such site renders inside a container class template, because a
        # container that declares the sourced parameter always has own params.
        return f'{name}<{BLOCK_CONFIG_PARAM}>'
    return name

def cpp_config_arg(configSelection):
    # SystemC template-argument suffix (`<Config>`) for a neutral per-instance
    # selection: empty when the child block is not a class template (no own
    # params), even if parameterizable, since `<X>` at a cast site would name a
    # non-template class.
    name = cpp_config_struct_name(configSelection)
    return f'<{name}>' if configSelection['hasOwnParams'] and name else ''

# Firmware artifacts of every context share one fixed namespace. Unlike the
# per-context module namespace there is nothing to derive it from, so this is the
# single source: the fw scaffold and the fw region emitters both spell it from here.
FW_NAMESPACE = 'fw_ns'

def cpp_namespace_name(includeName):
    return f'{cpp_module_name(includeName)}_ns'

def cpp_test_namespace_name(includeName):
    # Generated structure tests are exported from a sibling namespace so they
    # stay separate from the functional types in cpp_namespace_name.
    return f'{cpp_module_name(includeName)}_test_ns'

def cpp_context_include_lines(prj, context):
    # The dependency lines for one context's types module: a C++20 `import` plus
    # its `using namespace`. Shared by the SystemC class-decl templates so the
    # import spelling stays consistent across them.
    moduleName = cpp_module_name(prj.contextModuleIdentity[context])
    return [f'import {moduleName};',
            f'using namespace {cpp_namespace_name(prj.contextModuleIdentity[context])};']

def sc_channel_header_includes(intf_types, block_data):
    # `#include "<chnl>_channel.h"` for each interface type's channel. Shared by
    # the block Base/class dependency sets and the testbench External, which each
    # supply their own interface-type set.
    return [f'#include "{get_intf_defs(intfType, block_data)["sc_channel"]["type"]}_channel.h"'
            for intfType in sorted(intf_types)]

def cpp_config_header_includes(data):
    # `#include "<context>VariantConfig.h"` for each context whose per-variant
    # Config structs this block's declarations name. Deliberately a textual header
    # (a module's global module fragment, never its purview), so every unit that
    # spells a Config type needs its own copy: names declared in another unit's
    # global module fragment are reachable but NOT visible to an importer. Shared by
    # the block class dependency set and by both testbench module units, which each
    # name the DUT's Config.
    return [f'#include "{data["includeFiles"]["config_hdr"][context]["baseName"]}"'
            for context in sorted(data['configIncludeContext'])
            if context in data['includeFiles'].get('config_hdr', {})]

def sc_base_dependency_includes(prj, data):
    # Dependency lines a block's Base/Inverted/Channels declaration
    # (baseClassDecl) needs, returned as ordered (kind, text) pairs mirroring
    # sc_class_dependency_includes. kind is 'include' for a textual #include or
    # 'import' for a C++20 module import / using-namespace line.
    #
    # Two rendering contexts share this set so they cannot drift:
    #   * baseClassDecl (classic mode) emits the lines inline ahead of the
    #     classes.
    #   * the base-module GMF scaffold (moduleScaffold.baseModuleHeader) splits
    #     them: 'include' lines go in the global module fragment, 'import' lines
    #     after `export module`.
    out = list()
    block_intf_set = get_set_intf_types(data['interfaceTypes'], data)
    # With no interfaces the channel headers (which transitively pull the common
    # factory base) are absent, so include it directly.
    if not block_intf_set:
        out.append(('include', '#include "blockBase.h"'))
    for line in sc_channel_header_includes(block_intf_set, data):
        out.append(('include', line))
    for context in data['includeContext']:
        # INCLUDEFILES carries no include_cppm key at all for a project whose
        # every context is smartInclude-empty, so the file type is optional here.
        if context in data['includeFiles'].get('include_cppm', {}):
            for line in cpp_context_include_lines(prj, context):
                out.append(('import', line))
    return out

def sc_class_dependency_includes(prj, data):
    # The dependency lines a block's class declaration needs, returned as
    # ordered (kind, text) pairs. kind is 'include' for a textual #include or
    # 'import' for a C++20 module import / using-namespace line.
    #
    # Two rendering contexts share this set so they cannot drift:
    #   * classDecl (classic mode) emits the lines inline, in order, ahead of
    #     the class, interleaving the context imports between the config-policy
    #     includes and apbBusDecode.h.
    #   * the block-module GMF scaffold (moduleScaffold.blockModuleHeader)
    #     splits them: 'include' lines go in the global module fragment, the
    #     'import' lines after `export module`.
    out = list()
    out.append(('include', '#include "logging.h"'))
    out.append(('include', '#include "instanceFactory.h"'))
    # The block's own Base is a C++20 module interface unit (`<block>Base.cppm`,
    # `export module <block>.base;`), imported rather than textually included.
    # As an 'import' pair it is emitted inline in classic mode (namespace-scope
    # import in a plain header) and, in the block-module GMF, after
    # `export module` alongside the context imports.
    out.append(('import', f'import {cpp_base_module_name(data["blockModuleName"])};'))
    # The class declaration names each port's channel type (e.g.
    # push_ack_channel<...>) directly as a member, so it needs the channel
    # header for every interface the block uses, matching sc_base_dependency_includes.
    for line in sc_channel_header_includes(get_set_intf_types(data['interfaceTypes'], data), data):
        out.append(('include', line))
    if len(data['registers']) > 0 or len(data["memories"]) > 0:
        out.append(('include', '#include "addressMap.h"'))
    if len(data['registers']) > 0:
        out.append(('include', '#include "hwRegister.h"'))
    needsHwMemory = len(data["memories"]) > 0 or len(data.get('memoriesParent', {})) > 0
    registerDecode = data['addressDecode']['hasDecoder'] and (not data['enableRegConnections'] or data['blockInfo']['isRegHandler'])
    if data['blockInfo']['isRegHandler']:
        # A reg-handler's memories are surfaced as memoryPorts or regType:memory
        # registerPorts (blockRegs.get_hwregs emits hwMemoryPort members and
        # addMemory() for both), never as data['memories'], so the scan below
        # never reaches them. Include hwMemory.h whenever any such port exists.
        if data['memoryPorts'] or any(p['regType'] == 'memory' for p in data['registerPorts'].values()):
            needsHwMemory = True
    elif registerDecode:
        for reg, regData in data['registers'].items():
            if regData['regType'] == 'memory':
                needsHwMemory = True
                break
    if needsHwMemory:
        out.append(('include', '#include "hwMemory.h"'))
    thunker_protocols = sc_thunker_protocols(data, prj)
    for proto in sorted(thunker_protocols):
        out.append(('include', f'#include "{proto}_port_thunker.h"'))
    for line in cpp_config_header_includes(data):
        out.append(('include', line))
    # As an 'import' pair each is emitted inline in classic mode and, in a
    # block-module GMF caller, after `export module` alongside the context imports.
    for line in sc_instance_config_imports(data):
        out.append(('import', line))
    for context in data['classIncludeContext']:
        if context in data['includeFiles'].get('include_cppm', {}):
            for line in cpp_context_include_lines(prj, context):
                out.append(('import', line))
    if data['addressDecode']['isApbRouter']:
        out.append(('include', '#include "apbBusDecode.h"'))
    return out

def sc_class_module_usings(prj, data):
    # The `using namespace` lines a block's class body needs to spell imported
    # interface-context types unqualified, ordered and deduplicated. A
    # using-directive CLOSES the C++20 module preamble, so these are emitted at
    # the head of the CLASS region (after the `// user imports here` slot) rather
    # than in moduleExport, which keeps that slot a legal preamble slot for
    # hand-authored imports. Shared by classDecl and blockRegs so the two class
    # emitters cannot drift; mirrors moduleExport's own using sources
    # (dependency set + interface-context set).
    out = list()
    seen = set()
    for kind, line in sc_class_dependency_includes(prj, data):
        if line.startswith('using namespace ') and line not in seen:
            out.append(line)
            seen.add(line)
    for context in data['includeContext']:
        if context in data['includeFiles'].get('include_cppm', {}):
            for line in cpp_context_include_lines(prj, context):
                if line.startswith('using namespace ') and line not in seen:
                    out.append(line)
                    seen.add(line)
    return out

def wrap_module_namespace(args, data, lines):
    if args.mode != 'module':
        return lines
    namespaceName = cpp_namespace_name(data['contextModuleIdentity'])
    return [f'export namespace {namespaceName} {{'] + lines + [f'}} // namespace {namespaceName}']

def wrap_fw_namespace(args, lines):
    # Each fw header region carries its own complete `namespace fw_ns { ... }`
    # block rather than sharing one opened outside the regions, so a region that
    # emits nothing leaves no unbalanced brace behind. Adjacent blocks reopen the
    # same namespace, so later regions still see earlier regions' declarations.
    # Emission mode is exclusive, so this and wrap_module_namespace never both fire.
    if args.mode != 'fw':
        return lines
    return [f'namespace {FW_NAMESPACE} {{'] + lines + [f'}} // namespace {FW_NAMESPACE}']

def wrap_module_test_namespace(args, data, lines):
    if args.mode != 'module':
        return lines
    namespaceName = cpp_test_namespace_name(data['contextModuleIdentity'])
    return [f'export namespace {namespaceName} {{'] + lines + [f'}} // namespace {namespaceName}']

def sc_gen_modport_signal_blast(port_data, prj, block_data, swap_dir=False):

    out = {}
    connectionData = port_data.get('connection', {})
    intf_data = get_intf_data(connectionData, prj)
    intf_type = get_intf_type(intf_data['interfaceType'], block_data)
    intf_name = port_data['name']
    intf_modp = port_data['direction']
    intf_param = dict()

    interface_defs = block_data['interface_defs']
    assert(intf_type in interface_defs and
           intf_modp in interface_defs[intf_type]['modports'])

    intf_def = interface_defs[intf_type]


    if swap_dir :
        intf_modp = inverse_portdir(intf_modp)

    out['is_skip'] = intf_def.get('skip', False)
    out['multicycle_types'] = intf_def['sc_channel']['multicycle_types']
    out['description'] = intf_data['desc']
    out['intf_name'] = intf_name

    # Parameter
    params = intf_def.get('parameters') or {}
    for param in filter(lambda item: params[item]['datatype'] == 'struct', params):
        struct_data = list(filter(lambda item: item['structureType'] == param, intf_data['structures']))
        assert(len(struct_data) == 1); # expecting one exact match
        intf_param[param] = struct_data[0]

    # Interface parameters declaration
    chnl_params = ', '.join([sc_structure_field_type(intf_param[param], 'structure', 'structureKey', prj) for param in params])

    if intf_def['sc_channel']['param_cast']:
        if LEGACY_COMPAT_MODE:
            chnl_params = intf_def['sc_channel']['param_cast'] + ' < ' + chnl_params + ' >'
        else:
            chnl_params = intf_def['sc_channel']['param_cast'] + '<' + chnl_params + '>'

    if LEGACY_COMPAT_MODE:
        if chnl_params == '':
            chnl_params = ' '
        else:
            chnl_params = ' ' + chnl_params + ' '

    chnl_dir = 'in' if intf_modp == 'dst' else 'out'
    chnl_type = intf_def['sc_channel']['type'] + '_channel'
    port_type = intf_def['sc_channel']['type'] + '_' + chnl_dir

    #out['channel_decl'] = f"{chnl_type}<{chnl_params}> {intf_name}_chnl;"
    out['channel_decl'] = f"{chnl_type}<{chnl_params}> {intf_name};"
    out['port_decl'] = f"{port_type}<{chnl_params}> {intf_name};"

    hdl_intf_type = intf_def['sc_channel']['type'] + '_hdl_if'
    hdl_intf_name = intf_name + '_hdl_if'

    hdl_if_bv_types = []
    for param in filter(lambda item: params[item]['datatype'] == 'struct', params):
        hdl_if_bv_types.append(sc_hdl_bridge_type(intf_param[param], prj))
    hdl_params = intf_def.get('hdlparams', {}) or {}
    for param in hdl_params:
        assert(hdl_params[param]['datatype'] in ['integer'])
        if hdl_params[param]['isEval']:
            key, data = hdl_params[param]['value'].split('.')
            if key in intf_param:
                data_obj = intfEvalDSL(prj.data, intf_param[key]['structureKey'])
                eval_str = 'data_obj{}'.format('.' + data)
                w = eval(eval_str)
                assert(isinstance(w, int))
                sc_bv_type = 'bool' if w == 1 else f"sc_bv<{w}>"
                hdl_if_bv_types.append(sc_bv_type)

    hdl_if_params = ', '.join(hdl_if_bv_types)

    out['hdl_if_decl'] = f"{hdl_intf_type}<{hdl_if_params}> {hdl_intf_name};"

    chnl_params = ', '.join([sc_structure_field_type(intf_param[param], 'structure', 'structureKey', prj) for param in params] + hdl_if_bv_types)

    chnl_dir = intf_modp
    chnl_type = intf_def['sc_channel']['type'] + '_' + chnl_dir + '_bfm'

    bfm_name = intf_name + '_bfm'

    out['bfm_decl'] = f"{chnl_type}<{chnl_params}> {bfm_name};"
    out['bfm_ctor_init'] = f"{bfm_name}(\"" + bfm_name + "\")"

    out['intf_modp'] = intf_modp

    # Blasted interface ports
    out['dut_ports_decl'] = []
    for intf_sig in intf_def['signals']:
        dut_port_name = f"{intf_name}_{intf_sig}"
        hdl_if_sig_name = f"{hdl_intf_name}.{intf_sig}"
        out['dut_ports_decl'].append(f"dut_hdl->{dut_port_name}({hdl_if_sig_name});")

    # Assignment port <-> interface
    out['assign'] = []
    for intf_sig in intf_def['signals']:
        modp_signals = intf_def['modports'][intf_modp]['modportGroups']
        # Safely get inputs and outputs lists
        inputs = modp_signals.get('inputs', {}).get('groups', {}) or {}
        outputs = modp_signals.get('outputs', {}).get('groups', {}) or {}
        assign_lhs = f"{intf_name}.{intf_sig}" if intf_sig in inputs else f"{intf_name}_{intf_sig}"
        assign_rhs = f"{intf_name}_{intf_sig}" if intf_sig in inputs else f"{intf_name}.{intf_sig}"
        out['assign'].append(f"assign {assign_lhs} = {assign_rhs};")

    return out

def sc_gen_block_channels(conn_data, prj, block_data):

    out = {}

    intf_type = get_intf_type(conn_data['interfaceType'], block_data)
    intf_data = get_intf_data(conn_data, prj)
    chnl_name = get_channel_name(conn_data)
    intf_structs = intf_data['structures']
    intf_param = dict()

    interface_defs = block_data['interface_defs']
    assert(intf_type in interface_defs)

    intf_def = interface_defs[intf_type]

    out['is_skip'] = intf_def.get('skip', False)
    out['multicycle_types'] = intf_def['sc_channel']['multicycle_types']
    out['intf_name'] = chnl_name
    out['chnl_name'] = chnl_name
    out['desc'] = intf_data['desc']
    out['set_initial_value'] = intf_def['sc_channel'].get('set_initial_value', False) and 'register' in conn_data
    out['default_value'] = conn_data.get('defaultValue', 0)

    # The channel's struct template arguments are typed by the connected
    # child's per-variant Config. `configOverride` is the winning end's neutral
    # Config selection (or None when no end of the connection is
    # parameterizable); spell it here into the C++ struct name. When None,
    # sc_struct_type_name falls back to its `<Config>` placeholder, which is
    # appropriate inside leaf parameterizable parents that remain class
    # templates.
    config_override_selection = conn_data['configOverride']
    config_override = cpp_config_struct_name(config_override_selection) if config_override_selection else None
    out['config_override'] = config_override

    # Parameter
    parameters = intf_def.get('parameters', {}) or {}
    for param in filter(lambda item: parameters[item]['datatype'] == 'struct', parameters):
        struct_data = list(filter(lambda item: item['structureType'] == param, intf_structs))
        if len(struct_data) == 0:
            print(f"Interface {chnl_name} is {intf_type} and expected structure types {param} not found")
        assert(len(struct_data) == 1) # the structure type on your interface is not the expected type
        intf_param[param] = struct_data[0]

    # Interface parameters declaration
    chnl_params = ', '.join([sc_structure_field_type(intf_param[param], 'structure', 'structureKey', prj, config_override=config_override) for param in parameters])

    if intf_def['sc_channel']['param_cast']:
        if LEGACY_COMPAT_MODE:
            chnl_params = intf_def['sc_channel']['param_cast'] + ' < ' + chnl_params + ' >'
        else:
            chnl_params = intf_def['sc_channel']['param_cast'] + '<' + chnl_params + '>'

    if LEGACY_COMPAT_MODE:
        if chnl_params == '':
            chnl_params = ' '
        else:
            chnl_params = ' ' + chnl_params + ' '

    chnl_type = intf_def['sc_channel']['type'] + '_channel'

    #out['channel_decl'] = f"{chnl_type}<{chnl_params}> {chnl_name}_chnl;"
    out['channel_decl'] = f"{chnl_type}<{chnl_params}> {chnl_name};"

    return out


def sc_declare_channels(data, prj, indent, block_data):
    out = []
    for channelType in data["connectDouble"]:
        for key, value in data["connectDouble"][channelType].items():
            chnlInfo = sc_gen_block_channels(value, prj, block_data)
            if not chnlInfo['is_skip']:
                out.append(f'{indent}// {chnlInfo["desc"]}')
                out.append(indent + chnlInfo['channel_decl'])
    return out


def _payload_config_name(payload):
    # Spell the C++ Config struct name for a thunker payload's neutral Config
    # selection. buildThunkerView sets 'configSelection' on every payload; its value
    # is None for a non-parameterizable side, which spells to empty.
    configSelection = payload['configSelection']
    return cpp_config_struct_name(configSelection) if configSelection else ''


def _thunker_member_type(flagged, prj):
    # The payload types in view order, then one trailing bool per payload pair in
    # the same order. Each bool tells the thunker's copy
    # sites for that payload that the two declarations emit identical member
    # storage, so the value may be transferred whole rather than packed and
    # unpacked field by field. The class template defaults every flag to false, so
    # a false verdict is spelled explicitly only to keep the slots positional.
    thunker = flagged['thunker']
    channel_type = thunker['channelType']
    args = [sc_struct_type_name(payload['structure'],
                                payload['structureKey'],
                                prj,
                                config_override=(_payload_config_name(payload) or None))
            for payload in thunker['payloads']]
    args += ['true' if pair['directCopy'] else 'false'
             for pair in thunker['payloadPairs']]
    return f"{channel_type}_port_thunker<{', '.join(args)}>"


def _thunker_member_name(flagged, conn_data, is_connection_map):
    # Stable thunker member naming:
    #   * connectionMap (one child end per map): thunker_<instanceName>
    #   * connection (peer-to-peer): thunker_<channelName>_<endInstance>
    inst = flagged.get('instance') or ''
    if is_connection_map:
        return f"thunker_{inst}"
    return f"thunker_{get_channel_name(conn_data)}_{inst}"


def _flagged_thunker_ends(data, prj):
    # Every cross-interface end this container adapts, in emission order, as
    # (flagged end, owning connection row, is_connection_map). Three collections
    # carry them: peer-to-peer channel connections, connectionMap binds whose
    # child end is the local end of the map, and testbench External DUT-boundary
    # binds (connections pruned to an excluded DUT instance, a flat dict rather
    # than grouped by channelType, whose surviving end is a contained instance
    # port and so takes the peer-to-peer member naming).
    if prj is None:
        return
    for channelType in data.get("connectDouble", {}):
        for value in data["connectDouble"][channelType].values():
            for flagged in _resolve_cross_interface_ends(value, prj):
                yield flagged, value, False
    for value in data.get("connectionMaps", {}).values():
        for flagged in _resolve_cross_interface_ends(value, prj):
            yield flagged, value, True
    for value in data.get("prunedConnections", {}).values():
        for flagged in _resolve_cross_interface_ends(value, prj):
            yield flagged, value, False


def sc_declare_thunkers(data, prj, indent, block_data):
    # Emit one thunker member declaration per flagged cross-interface end.
    out = []
    for flagged, value, is_connection_map in _flagged_thunker_ends(data, prj):
        member_type = _thunker_member_type(flagged, prj)
        member_name = _thunker_member_name(flagged, value, is_connection_map)
        out.append(f"{indent}{member_type} {member_name};")
    return out


def sc_thunker_protocols(data, prj):
    # Return the set of SystemC channel type stems (e.g. 'rdy_vld',
    # 'req_ack') for which this container emits at least one thunker. Callers
    # use the set to emit the matching `<channel_type>_port_thunker.h` include.
    protocols = set()
    for flagged, _value, _is_connection_map in _flagged_thunker_ends(data, prj):
        protocols.add(flagged['thunker']['channelType'])
    return protocols

def inverse_portdir(port):
    assert(port in ['src', 'dst'])
    return 'src' if port == 'dst' else 'dst'

def lookup_struct(struct_key, struct_dict):
    return struct_dict.get(struct_key, None)

def get_struct_width(struct_key, struct_dict):
    struct = lookup_struct(struct_key, struct_dict)
    return struct['width'] if struct else 0

def lookup_const(const_key, const_dict):
    return const_dict.get(const_key, None)

def get_const(const_key, const_dict):
    const = lookup_const(const_key, const_dict)
    return const['value'] if const else 0

def get_sorted_memories(data):
    if 'memoriesParent' in data:
        memoryKey = 'memoriesParent'
    else:
        memoryKey = 'memories'
    mems = dict(filter(lambda x: x[1]['regAccess'], data[memoryKey].items()))
    mems = dict(sorted(mems.items(), key=lambda item: item[1]["offset"]))
    return mems

def sc_concrete_dut(sv_wrapper, standalone_variants):
    # Select the non-templated SC wrapper's single DUT top: the first standalone
    # variant's trampoline when the block has any, the body DUT otherwise.
    if standalone_variants:
        v = next(iter(standalone_variants))
        return {
            'svModule':  sv_wrapper['variantTops'][v],
            'dutClass':  sv_wrapper['variantDutClasses'][v],
            'dutHeader': sv_wrapper['variantDutHeaders'][v],
        }
    return {
        'svModule':  sv_wrapper['bodyModule'],
        'dutClass':  sv_wrapper['dutClass'],
        'dutHeader': sv_wrapper['dutHeader'],
    }

def get_intf_defs(intf_type, block_data):
    """Get interface definition for given interface type
    
    Args:
        intf_type: Canonical interface type name (resolve aliases with
                   get_intf_type first)
        block_data: Block data dict containing interface_defs

    Returns:
        Interface definition dict. Raises KeyError naming the type when the
        block's view carries no row for it.
    """
    return block_data['interface_defs'][intf_type]
