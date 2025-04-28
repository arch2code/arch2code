def render(args, prj, data):
    out = ''
    out += f"Connection: {data['connection']['src']} -> {data['connection']['dst']}\n"
    # TODO Probably needs to be name, port, interface in that order, interfaceName?
    out += f"Interface: {data['connection']['interface']}\n"
    out += f"{data['connection']['desc']}\n"

    return (out)
