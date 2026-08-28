import pysrc.intf_gen_utils as intf_gen_utils


def render(args, prj, data):
    match args.section:
        case 'socket':
            return render_socket(args, prj, data)
        case _:
            raise ValueError(
                f"Unknown section '{args.section}' for template '{args.template}'. "
                "Valid value is socket")


def _catalog_rows(prj, data):
    view = prj.getSocketCatalogView(data['qualBlock'], block_data=data)
    return [row for row in view['ports'] if row['hasPortSocket']]


def _method_name(row):
    return f"{row['port']}Observe" if row['role'] == 'observe' else f"{row['port']}Socket"


def render_socket(args, prj, data):
    out = list()
    blockName = data['blockName']
    className = f'{blockName}Socket'
    hasOwnParams = data['hasOwnParams']
    cfg = intf_gen_utils.block_config_arg(hasOwnParams)
    templateDecl = intf_gen_utils.block_config_decl(hasOwnParams)
    baseClassName = f'{blockName}Base{cfg}'
    projectName = prj.config.getConfig('PROJECTNAME')
    rows = _catalog_rows(prj, data)
    include_types = sorted({row['interfaceType'] for row in rows if row['interfaceType']})

    out.append('#include "logging.h"\n')
    for intfType in include_types:
        out.append(f'#include "{intfType}_port_socket.h"\n')
    out.append('#include "instanceFactory.h"\n')
    out.append(f'import {intf_gen_utils.cpp_base_module_name(data["blockModuleName"])};\n')

    if hasOwnParams:
        for context in sorted(data.get('configIncludeContext', {})):
            if context in data['includeFiles'].get('config_hdr', {}):
                out.append(f'#include "{data["includeFiles"]["config_hdr"][context]["baseName"]}"\n')

    out.append('\n')
    if hasOwnParams:
        out.append(templateDecl + '\n')
    out.append(f'SC_MODULE({className}), public blockBase, public {baseClassName}\n')
    out.append('{\n')
    out.append('private:\n')
    indent = ' ' * 4
    out.append(indent + 'struct registerBlock\n')
    out.append(indent + '{\n')
    if hasOwnParams:
        out.append(indent + '    registerBlock(const char * variant_)\n')
        out.append(indent + '    {\n')
        out.append(indent + '        // lamda function to construct the block\n')
        out.append(indent + f'        instanceFactory::registerBlock("{blockName}_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {{ return static_cast<std::shared_ptr<blockBase>> (std::make_shared<{className}<Config>>(blockName, variant, bbMode));}}, variant_, "{projectName}");\n')
        out.append(indent + '    }\n')
    else:
        out.append(indent + '    registerBlock()\n')
        out.append(indent + '    {\n')
        out.append(indent + '        // lamda function to construct the block\n')
        out.append(indent + f'        instanceFactory::registerBlock("{blockName}_socket", [](const char * blockName, const char * variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {{ return static_cast<std::shared_ptr<blockBase>> (std::make_shared<{className}>(blockName, variant, bbMode));}}, "", "{projectName}");\n')
        out.append(indent + '    }\n')
    out.append(indent + '};\n')
    out.append(indent + 'static registerBlock registerBlock_;\n')
    out.append('public:\n')

    if hasOwnParams:
        out.append(indent + f'SC_HAS_PROCESS({className});\n')

    out.append('\n')
    out.append(indent + f'{className}(sc_module_name blockName, const char * variant, blockBaseMode bbMode);\n')
    out.append(indent + f'~{className}() override = default;\n')
    out.append('\nprivate:\n')
    for row in rows:
        out.append(indent + f'void {_method_name(row)}(void);\n')

    return "".join(out)
