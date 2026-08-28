def render(args, prj, data):
    match args.section:
        case 'header':
            return render_header(args, prj, data)
        case 'python':
            return render_python(args, prj, data)
        case _:
            raise ValueError(
                f"Unknown section '{args.section}' for template '{args.template}'. "
                "Valid values are header, python")


def _catalog_view(prj, data):
    return prj.getSocketCatalogView(data['qualBlock'], block_data=data)


def _cpp_string_array(name, values):
    n = len(values)
    if n == 0:
        return f'inline constexpr std::array<const char *, 0> {name}{{}};\n'
    out = [f'inline constexpr std::array<const char *, {n}> {name}{{{{']
    for value in values:
        out.append(f'    "{value}",')
    out.append('}};\n')
    return '\n'.join(out)


def _py_string_tuple(name, values):
    if not values:
        return f'{name} = ()\n'
    lines = [f'{name} = (']
    for value in values:
        lines.append(f'    {value!r},')
    lines.append(')\n')
    return '\n'.join(lines)


def render_header(args, prj, data):
    view = _catalog_view(prj, data)
    ns = f'{view["block"]}SocketCatalog'
    out = list()
    out.append('#include "socketFactory.h"\n')
    out.append('#include "socketTransport.h"\n')
    out.append('#include <array>\n\n')
    out.append(f'namespace {ns} {{\n\n')
    out.append(_cpp_string_array('listen_names', view['listenNames']))
    if view['syncNames']:
        out.append(
            f'inline constexpr std::array<const char *, {len(view["syncNames"])}> sync_names{{{{\n'
            '    PYSOCKET_SYNC_IFC,\n'
            '}};\n')
    else:
        out.append('inline constexpr std::array<const char *, 0> sync_names{};\n')
    out.append('\n')
    for row in view['ports']:
        out.append(f'inline constexpr const char *name_{row["port"]} = "{row["name"]}";\n')
        if row['observeName']:
            out.append(f'inline constexpr const char *observe_name_{row["port"]} = "{row["observeName"]}";\n')
    out.append('\n')
    out.append('inline bool registerAll()\n')
    out.append('{\n')
    out.append('    for (const char *ifc : listen_names) {\n')
    out.append('        if (socketFactory::registerInterface(ifc) == 0) {\n')
    out.append('            socketFactory::shutdownAll();\n')
    out.append('            return false;\n')
    out.append('        }\n')
    out.append('    }\n')
    out.append('    for (const char *ifc : sync_names) {\n')
    out.append('        if (socketFactory::registerInterface(ifc) == 0) {\n')
    out.append('            socketFactory::shutdownAll();\n')
    out.append('            return false;\n')
    out.append('        }\n')
    out.append('    }\n')
    out.append('    return true;\n')
    out.append('}\n\n')
    out.append('inline bool handshakeAll()\n')
    out.append('{\n')
    out.append('    for (const char *ifc : listen_names) {\n')
    out.append('        const int fd = socketFactory::getFd(ifc);\n')
    out.append('        if (fd < 0 || !socket_send_msg(fd, MSG_SYNC, nullptr, 0)) {\n')
    out.append('            return false;\n')
    out.append('        }\n')
    out.append('    }\n')
    out.append('    for (const char *ifc : sync_names) {\n')
    out.append('        const int fd = socketFactory::getFd(ifc);\n')
    out.append('        if (fd < 0 || !socket_send_msg(fd, MSG_SYNC, nullptr, 0)) {\n')
    out.append('            return false;\n')
    out.append('        }\n')
    out.append('    }\n')
    out.append('    return true;\n')
    out.append('}\n\n')
    out.append(f'}} // namespace {ns}\n')
    return "".join(out)


def render_python(args, prj, data):
    view = _catalog_view(prj, data)
    out = list()
    out.append('CATALOG = {\n')
    for row in view['ports']:
        observe = 'None' if row['observeName'] is None else repr(row['observeName'])
        role = 'None' if row['role'] is None else repr(row['role'])
        intf = 'None' if row['interfaceType'] is None else repr(row['interfaceType'])
        out.append(f'    {row["port"]!r}: {{\n')
        out.append(f'        "port": {row["port"]!r},\n')
        out.append(f'        "name": {row["name"]!r},\n')
        out.append(f'        "interfaceType": {intf},\n')
        out.append(f'        "direction": {row["direction"]!r},\n')
        out.append(f'        "role": {role},\n')
        out.append(f'        "observeName": {observe},\n')
        out.append('    },\n')
    out.append('}\n\n')
    out.append(_py_string_tuple('LISTEN_NAMES', view['listenNames']))
    out.append(_py_string_tuple('SYNC_NAMES', view['syncNames']))
    out.append('\n')
    out.append('def required_names():\n')
    out.append('    return list(LISTEN_NAMES) + list(SYNC_NAMES)\n\n')
    out.append('def by_port(port):\n')
    out.append('    return CATALOG[port]\n\n')
    out.append('def name_for_port(port):\n')
    out.append('    return CATALOG[port]["name"]\n\n')
    out.append('def observe_name_for_port(port):\n')
    out.append('    return CATALOG[port]["observeName"]\n')
    return "".join(out)
