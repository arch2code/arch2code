# The UVM testbench top module of a hasUvm block. SystemC instantiates it
# through a simulator shell built from the same pin list, so its ports are the
# HDL top's pins with the port directions inverted, then the completion pins.
# A block with a model holds the RTL only when compiled with A2C_UVM_RTL_DUT,
# and otherwise carries the interfaces over the pins to the SystemC BFMs and
# the model. A block without a model always holds the RTL. Holding the RTL
# ties off the pins toward SystemC.
import itertools
import textwrap


def render(args, prj, data):
    # A block without params has one variantless top, which its scaffold
    # names with no --variant.
    variant = args.variant or ''
    top = data['uvm']['tops'][variant]
    match args.section:
        case 'header':
            out = f"\n`timescale 1ns/1ps\n\nmodule {top['tbModule']}\n    import uvm_pkg::*;\n"
        case 'body':
            out = render_body(prj, data, variant, top)
        case 'footer':
            out = f"\nendmodule : {top['tbModule']}\n"
        case _:
            raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are header, body or footer")
    return textwrap.indent(out, ' '*args.sectionindent)


def pin_decl(pin):
    if pin['kind'] == 'clockReset':
        return f"{pin['direction']} {pin['pin']}"
    # VCS gets $size wrong for parameter-derived structs, so payload widths
    # are $bits of the payload type.
    if pin['type']:
        width = f" [$bits({pin['type']['pkg']}::{pin['type']['name']})-1:0]"
    elif pin['vector']:
        width = f" [{pin['width'] - 1}:0]"
    else:
        width = ''
    return f"{pin['direction'].ljust(6)} bit{width} {pin['pin']}"


def group_comment(pin):
    match pin['kind']:
        case 'port':
            return f"// {pin['interfaceType']}_if.{pin['role']} on the DUT"
        case 'completion':
            return '// completion, read by the SystemC side'
    return None


def render_body(prj, data, variant, top):
    pins = prj.getUvmTopBoundaryPins(data, top['hdlTop'])
    portPins = [pin for pin in pins if pin['kind'] == 'port']
    hasMdl = data['blockInfo']['hasMdl']

    decls = list()
    for _, groupPins in itertools.groupby(pins, key=lambda pin: (pin['kind'], pin['port'])):
        groupPins = list(groupPins)
        if decls:
            decls.append('')
        if group_comment(groupPins[0]):
            decls.append(group_comment(groupPins[0]))
        decls += [pin_decl(pin) + ',' for pin in groupPins]
    decls[-1] = decls[-1].rstrip(',')
    out = ['(', *[f'    {line}' if line else '' for line in decls], ');', '']

    body = list()
    for port in data['uvm']['ports']:
        params = ', '.join(f".{p['param']}({p['type']['pkg']}::{p['type']['name']})"
                           for p in port['paramTypes'][variant])
        params = f" #({params})" if params else ''
        body.append(f"{port['interfaceType']}_if{params} {port['name']}();")
    for clock in data['uvm']['clocks']:
        reset = clock['reset'] or "1'b1"
        body.append(f"a2c_clk_if {clock['clock']}_if(.clk({clock['clock']}), .rst_n({reset}));")
    out += [f'    {line}' for line in body]
    out.append('')

    binds = [f".{pin['pin']}({pin['port']}.{pin['signal']})" for pin in portPins]
    binds += [f".{pin['pin']}({pin['pin']})" for pin in pins if pin['kind'] == 'clockReset']
    rtl = [f"{top['hdlTop']} dut ("]
    rtl += [f"    {bind}," for bind in binds[:-1]] + [f"    {binds[-1]}", ');', '']
    for pin in portPins:
        if pin['direction'] == 'output':
            tie = "'0" if pin['vector'] else "1'b0"
            rtl.append(f"assign {pin['pin']} = {tie};")
    rtl.append("assign rtl_dut = 1'b1;")
    if hasMdl:
        out.append('`ifdef A2C_UVM_RTL_DUT')
        out += [f'    {line}' if line else '' for line in rtl]
        out.append('`else')
        for pin in portPins:
            intfSignal = f"{pin['port']}.{pin['signal']}"
            lhs, rhs = (pin['pin'], intfSignal) if pin['direction'] == 'output' else (intfSignal, pin['pin'])
            out.append(f"    assign {lhs} = {rhs};")
        out.append("    assign rtl_dut = 1'b0;")
        out.append('`endif')
    else:
        out += [f'    {line}' if line else '' for line in rtl]
    out.append('')

    sets = [f'uvm_config_db#({top["pkgName"]}::{port["name"]}_vif_t)::set(null, "uvm_test_top.*", "{port["name"]}", {port["name"]});'
            for port in data['uvm']['ports']]
    sets += [f'uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top.*", "{clock["clock"]}", {clock["clock"]}_if);'
             for clock in data['uvm']['clocks']]
    out += [
        '    // run_test() returns after the report phase because finish_on_completion',
        '    // is off, and SystemC ends the simulation through its end-of-test vote.',
        '    // A UVM_FATAL calls $finish inside run_test(), so uvm_done stays low and',
        '    // the SystemC side fails the run.',
        '    initial begin',
        '        uvm_report_server srv;',
        "        uvm_done = 1'b0;",
        "        uvm_errors = '0;",
        *[f'        {line}' for line in sets],
        '        uvm_root::get().finish_on_completion = 0;',
        '        run_test();',
        '        srv = uvm_report_server::get_server();',
        '        uvm_errors = srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL);',
        f"        @(posedge {data['defaultClock']});",
        "        uvm_done = 1'b1;",
        '    end',
    ]
    return '\n' + '\n'.join(out) + '\n'
