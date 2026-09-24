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


def _port_ref(port, hasOwnParams):
    return f'this->{port}' if hasOwnParams else port


# The connection name is this shell instance's SystemC path plus the port.
def _name_expr(blockName, port):
    return f'{blockName}SocketCatalog::name_{port}(this->name())'


def _observe_name_expr(blockName, port):
    return f'{blockName}SocketCatalog::observe_name_{port}(this->name())'


# port_socket and port_observe do nothing for a name with no listen port, so a
# testbench that registered a different instance path would run green with no
# traffic. Registration, not the connection, is checked so a run with no
# sidecar still starts.
def _registered_check(listen_expr):
    return (
        f'    Q_ASSERT(socketFactory::getPort({listen_expr}) != 0,\n'
        f'             "socket " + {listen_expr} + " is not registered; '
        'the testbench must registerInstance this shell\'s instance path");\n'
    )


def _drive_body(port_ref, name):
    return _registered_check(name) + f'    port_socket({port_ref}, {name});\n'


def _observe_body(port_ref, name, observe_name):
    # status_in: blocking read, then push irq observe when the payload has irq.
    # if constexpr keeps register-mapped status ports on unused shells compiling.
    return _registered_check(observe_name) + (
        f'    port_observe({port_ref}, {name}, '
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

    # A Config-templated shell is registered by the trampoline registrar.
    if not hasOwnParams:
        projectName = prj.config.getConfig('PROJECTNAME')
        out.append(f'SC_HAS_PROCESS({className});\n\n')
        out.append(f'// === Socket shell factory registration ({className}) ===\n')
        out.append(f'void register_{className}() {{\n')
        out.append(f'    instanceFactory::registerBlock("{blockName}_socket", '
                   '[](const char * blockName, const char * variant, blockBaseMode bbMode) '
                   '-> std::shared_ptr<blockBase> { return static_cast<std::shared_ptr<blockBase>>'
                   f'(std::make_shared<{className}>(blockName, variant, bbMode)); }}, "", "{projectName}");\n')
        out.append('}\n\n')
        out.append('namespace {\n')
        out.append(f'[[maybe_unused]] A2C_REGISTRATION_RETAIN int _{className}_registered = '
                   f'(register_{className}(), 0);\n')
        out.append('} // namespace\n')
        out.append(f'// === End socket shell factory registration ===\n\n')

    for row in rows:
        method = _method_name(row)
        port_ref = _port_ref(row['port'], hasOwnParams)
        if hasOwnParams:
            out.append(templateDecl + '\n')
        out.append(f'void {qualClassName}::{method}(void) {{\n')
        name = _name_expr(blockName, row['port'])
        if row['role'] == 'observe':
            out.append(_observe_body(port_ref, name, _observe_name_expr(blockName, row['port'])))
        else:
            out.append(_drive_body(port_ref, name))
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
