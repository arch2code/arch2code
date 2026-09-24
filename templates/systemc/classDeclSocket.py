import pysrc.intf_gen_utils as intf_gen_utils


# The socket shell is one C++20 module interface unit, `<block>Socket.cppm`,
# laid out like the block's own `<block>.cppm`: moduleHeader is the global
# module fragment, moduleExport the preamble, socket the exported class. A
# Config-templated shell's member definitions live in the same unit, so any
# importer can instantiate it at a Config the owner build never sees.
def render(args, prj, data):
    match args.section:
        case 'moduleHeader':
            return render_module_header(args, prj, data)
        case 'moduleExport':
            return render_module_export(args, prj, data)
        case 'socket':
            return render_socket(args, prj, data)
        case _:
            raise ValueError(
                f"Unknown section '{args.section}' for template '{args.template}'. "
                "Valid values are moduleHeader, moduleExport, socket")


def _catalog_rows(prj, data):
    view = prj.getSocketCatalogView(data['qualBlock'], block_data=data)
    return [row for row in view['ports'] if row['hasPortSocket']]


def _method_name(row):
    return f"{row['port']}Observe" if row['role'] == 'observe' else f"{row['port']}Socket"


def render_module_header(args, prj, data):
    rows = _catalog_rows(prj, data)
    include_types = sorted({row['interfaceType'] for row in rows if row['interfaceType']})
    out = ['module;',
           '#include "systemc.h"',
           '#include "logging.h"',
           '#include "instanceFactory.h"']
    for intfType in include_types:
        out.append(f'#include "{intfType}_port_socket.h"')
    out.append(f'#include "{prj.getModuleFilename("socketCatalog", data["blockName"], "hdr")}"')
    return '\n'.join(out)


def render_module_export(args, prj, data):
    out = [f'export module {intf_gen_utils.cpp_socket_module_name(data["blockModuleName"])};',
           f'import {intf_gen_utils.cpp_base_module_name(data["blockModuleName"])};']
    if data['hasOwnParams']:
        out.extend(intf_gen_utils.cpp_own_config_import(data))
    # The context imports the model unit makes, so user code in the shell sees
    # the block's types; a C++20 import is not transitive through `.base`.
    for context in data['includeContext']:
        if context in data['includeFiles'].get('include_cppm', {}):
            for line in intf_gen_utils.cpp_context_include_lines(prj, context):
                if line.startswith('import ') and line not in out:
                    out.append(line)
    return '\n'.join(out)


def render_socket(args, prj, data):
    out = list()
    blockName = data['blockName']
    className = f'{blockName}Socket'
    hasOwnParams = data['hasOwnParams']
    cfg = intf_gen_utils.block_config_arg(hasOwnParams)
    baseClassName = f'{blockName}Base{cfg}'
    rows = _catalog_rows(prj, data)

    if hasOwnParams:
        out.append('export ' + intf_gen_utils.block_config_decl(hasOwnParams) + '\n')
        out.append(f'SC_MODULE({className}), public blockBase, public {baseClassName}\n')
    else:
        out.append(f'export SC_MODULE({className}), public blockBase, public {baseClassName}\n')
    out.append('{\n')
    out.append('public:\n')
    indent = ' ' * 4
    if hasOwnParams:
        out.append(indent + f'SC_HAS_PROCESS({className});\n')
    out.append('\n')
    out.append(indent + f'{className}(sc_module_name blockName, const char * variant, blockBaseMode bbMode);\n')
    out.append(indent + f'~{className}() override = default;\n')
    out.append('\nprivate:\n')
    for row in rows:
        out.append(indent + f'void {_method_name(row)}(void);\n')

    return "".join(out)
