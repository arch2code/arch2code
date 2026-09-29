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


def _cpp_name_function(name, suffix):
    return (f'inline std::string {name}(std::string_view instance) '
            f'{{ return std::string(instance) + "{suffix}"; }}\n')


# A socket name is the shell's instance path plus a per-port suffix, so every
# name is a function of the instance. The testbench registers pysocket_sync
# itself, once, when uses_lockstep says the block needs it.
def render_header(args, prj, data):
    view = _catalog_view(prj, data)
    ns = f'{view["block"]}SocketCatalog'
    out = list()
    out.append('#include "socketFactory.h"\n')
    out.append('#include <array>\n')
    out.append('#include <iostream>\n')
    out.append('#include <string>\n')
    out.append('#include <string_view>\n\n')
    out.append(f'namespace {ns} {{\n\n')
    out.append(f'inline constexpr bool uses_lockstep = {"true" if view["usesLockstep"] else "false"};\n\n')
    out.append(_cpp_string_array('listen_suffixes', view['listenSuffixes']))
    out.append('\n')
    for row in view['ports']:
        out.append(_cpp_name_function(f'name_{row["port"]}', row['nameSuffix']))
        if row['observeSuffix']:
            out.append(_cpp_name_function(f'observe_name_{row["port"]}', row['observeSuffix']))
    out.append('\n')
    out.append('// Listens on every drive and observe name of one shell instance. A name\n')
    out.append('// already registered is an error: two shells would share one connection.\n')
    out.append('inline bool registerInstance(std::string_view instance)\n')
    out.append('{\n')
    out.append('    for (const char *suffix : listen_suffixes) {\n')
    out.append('        const std::string ifc = std::string(instance) + suffix;\n')
    out.append('        if (socketFactory::registerInterface(ifc) == 0) {\n')
    out.append(f'            std::cerr << "{ns}: cannot register socket " << ifc\n')
    out.append('                      << " (already registered, or no listen port)" << std::endl;\n')
    out.append('            socketFactory::shutdownAll();\n')
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
        observe = 'None' if row['observeSuffix'] is None else repr(row['observeSuffix'])
        role = 'None' if row['role'] is None else repr(row['role'])
        intf = 'None' if row['interfaceType'] is None else repr(row['interfaceType'])
        out.append(f'    {row["port"]!r}: {{\n')
        out.append(f'        "port": {row["port"]!r},\n')
        out.append(f'        "nameSuffix": {row["nameSuffix"]!r},\n')
        out.append(f'        "interfaceType": {intf},\n')
        out.append(f'        "direction": {row["direction"]!r},\n')
        out.append(f'        "role": {role},\n')
        out.append(f'        "observeSuffix": {observe},\n')
        out.append('    },\n')
    out.append('}\n\n')
    out.append(_py_string_tuple('LISTEN_SUFFIXES', view['listenSuffixes']))
    out.append(_py_string_tuple('SYNC_NAMES', view['syncNames']))
    out.append('\n')
    out.append('def required_names(instance):\n')
    out.append('    return [instance + suffix for suffix in LISTEN_SUFFIXES] + list(SYNC_NAMES)\n\n')
    out.append('def by_port(port):\n')
    out.append('    return CATALOG[port]\n\n')
    out.append('def name_for_port(port, instance):\n')
    out.append('    return instance + CATALOG[port]["nameSuffix"]\n\n')
    out.append('def observe_name_for_port(port, instance):\n')
    out.append('    suffix = CATALOG[port]["observeSuffix"]\n')
    out.append('    return None if suffix is None else instance + suffix\n')
    return "".join(out)
