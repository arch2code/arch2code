import pysrc.intf_gen_utils as intf_gen_utils


def render(args, prj, data):
    match args.section:
        case 'initSocket':
            return constructorInitSocket(args, prj, data)
        case 'bodySocket':
            return constructorBodySocket(args, prj, data)
        case 'instantiateSocket':
            return constructorInstantiateSocket(args, prj, data)
        case _:
            raise ValueError(
                f"Unknown section '{args.section}' for template '{args.template}'. "
                "Valid values are initSocket, bodySocket, instantiateSocket")


def _catalog_rows(prj, data):
    view = prj.getSocketCatalogView(data['qualBlock'], block_data=data)
    return [row for row in view['ports'] if row['hasPortSocket']]


def _method_name(row):
    return f"{row['port']}Observe" if row['role'] == 'observe' else f"{row['port']}Socket"


def _port_ref(port, hasOwnParams):
    return f'this->{port}' if hasOwnParams else port


def _drive_body(port_ref, name, mapped_offsets=None, addr_mask=None):
    if mapped_offsets is None:
        return f'    port_socket({port_ref}, "{name}");\n'
    offs = ', '.join(f'{offset:#x}u' for offset in mapped_offsets)
    return (
        f'    port_socket({port_ref}, "{name}", {{{offs}}}, {addr_mask:#x}u);\n'
    )


def _observe_body(port_ref, name):
    # status_in: blocking read, then push irq observe when the payload has irq.
    # if constexpr keeps register-mapped status ports on unused shells compiling.
    return (
        f'    port_observe({port_ref}, "{name}", '
        '[](const std::string &obs_name, const auto &val) {\n'
        '        if constexpr (requires { val.irq; }) {\n'
        '            socket_observe_irq(obs_name, static_cast<bool>(val.irq));\n'
        '        }\n'
        '    });\n'
    )


def constructorInitSocket(args, prj, data):
    out = list()
    blockName = data['blockName']
    className = f'{blockName}Socket'
    hasOwnParams = data['hasOwnParams']
    cfg = intf_gen_utils.block_config_arg(hasOwnParams)
    templateDecl = intf_gen_utils.block_config_decl(hasOwnParams)
    qualClassName = f'{className}{cfg}'
    baseClassName = f'{blockName}Base{cfg}'
    rows = _catalog_rows(prj, data)

    out.append(f'#include "{prj.getModuleFilename("socket", blockName, "hdr")}"\n\n')

    # A Config-templated shell is registered by the trampoline registrar.
    if not hasOwnParams:
        out.append(f'SC_HAS_PROCESS({className});\n\n')
        out.append(f'{className}::registerBlock {className}::registerBlock_; //register the block with the factory\n\n')

    for row in rows:
        method = _method_name(row)
        port_ref = _port_ref(row['port'], hasOwnParams)
        if hasOwnParams:
            out.append(templateDecl + '\n')
        out.append(f'void {qualClassName}::{method}(void) {{\n')
        if row['role'] == 'observe':
            out.append(_observe_body(port_ref, row['name']))
        else:
            out.append(_drive_body(port_ref, row['name'],
                                   row['apbMappedOffsets'], row['apbAddrMask']))
        out.append('}\n\n')

    if hasOwnParams:
        out.append(templateDecl + '\n')
    out.append(f'{qualClassName}::{className}(sc_module_name blockName, const char * variant, blockBaseMode bbMode)\n')
    out.append('       : sc_module(blockName)\n')
    out.append(f'        ,blockBase("{blockName}", name(), bbMode)\n')
    out.append(f'        ,{baseClassName}(name(), variant)')
    return "".join(out)


def constructorBodySocket(args, prj, data):
    out = list()
    rows = _catalog_rows(prj, data)
    out.append('{\n')
    out.append('    log_.logPrint(std::format("Socket shell {} initialized.", this->name()), LOG_IMPORTANT );\n')
    for row in rows:
        out.append(f'    SC_THREAD({_method_name(row)});\n')
    return "".join(out)


def constructorInstantiateSocket(args, prj, data):
    # The registrar constructs the shell from another translation unit, so the
    # constructor is instantiated here for every Config this project binds. A
    # container-sourced Config is a template over the parent's and binds none.
    if not data['hasOwnParams']:
        return ''
    blockName = data['blockName']
    className = f'{blockName}Socket'
    configNames = list(dict.fromkeys(
        desc['structName'] for desc in data['variantConfigs']
        if not desc['containerSourced']))
    out = list()
    for configName in configNames:
        out.append(f'template {className}<{configName}>::{className}'
                   '(sc_module_name, const char *, blockBaseMode);\n')
    return "".join(out)
