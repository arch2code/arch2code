import pysrc.intf_gen_utils as intf_gen_utils


def render(args, prj, data):
    match args.section:
        case 'initSocket':
            return constructorInitSocket(args, prj, data)
        case 'bodySocket':
            return constructorBodySocket(args, prj, data)
        case _:
            raise ValueError(
                f"Unknown section '{args.section}' for template '{args.template}'. "
                "Valid values are initSocket, bodySocket")


def _catalog_rows(prj, data):
    view = prj.getSocketCatalogView(data['qualBlock'], block_data=data)
    return [row for row in view['ports'] if row['hasPortSocket']]


def _method_name(row):
    return f"{row['port']}Observe" if row['role'] == 'observe' else f"{row['port']}Socket"


def _variant_config_names(data, defaultConfig):
    variantConfigName = dict()
    for desc in data['variantConfigs']:
        variantConfigName[desc['variant']] = intf_gen_utils.cpp_descriptor_config_name(desc, defaultConfig)
    return variantConfigName


def _port_ref(port, hasOwnParams):
    return f'this->{port}' if hasOwnParams else port


def _drive_body(port_ref, name):
    return f'    port_socket({port_ref}, "{name}");\n'


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
    defaultConfig = data['defaultConfig']
    rows = _catalog_rows(prj, data)

    out.append(f'#include "{prj.getModuleFilename("socket", blockName, "hdr")}"\n\n')

    if hasOwnParams:
        variantConfigName = _variant_config_names(data, defaultConfig)
        if data['variants']:
            for variant in sorted(data['variants']):
                perVariantConfig = variantConfigName.get(variant, defaultConfig)
                out.append(f'template<> {className}<{perVariantConfig}>::registerBlock {className}<{perVariantConfig}>::registerBlock_("{variant}"); //register the block with the factory\n')
        else:
            out.append(f'template<> {className}<{defaultConfig}>::registerBlock {className}<{defaultConfig}>::registerBlock_(""); //register the block with the factory\n')
        out.append('\n')
    else:
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
            out.append(_drive_body(port_ref, row['name']))
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
