# The UVM testbench top module of a hasUvm block. SystemC instantiates it
# through a simulator shell built from the same pin list, so its ports are the
# HDL top's pins with the port directions inverted, then the completion pins.
# A block whose DUTs include the model holds the RTL under A2C_UVM_RTL_DUT,
# and with no DUT define carries the interfaces over the pins to the SystemC
# BFMs and the model. A block whose DUTs include both holds, under
# A2C_UVM_BOTH_DUT, the RTL on the port interfaces and a second interface per
# port, <port>_model, over the pins. A block whose only DUT is rtl always holds
# the RTL. Holding only the RTL ties off the pins toward SystemC.
import itertools
import textwrap


def render(args, prj, data):
    # A block without params has one variantless top, which its scaffold
    # names with no --variant.
    variant = args.variant or ''
    top = data['uvm']['tops'][variant]
    match args.section:
        case 'header':
            # The factory registers only the tests of an elaborated package.
            out = (f"\n`timescale 1ns/1ps\n\nmodule {top['tbModule']}\n    import uvm_pkg::*;\n"
                   f"    import {data['uvm']['testPkgName']}::*;\n")
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
    # A scalar pin binds to the shell's bool. VCS gets $size wrong for
    # parameter-derived structs, so vector payload widths are $bits of the
    # payload type.
    if not pin['vector']:
        width = ''
    elif pin['type']:
        width = f" [$bits({pin['type']['pkg']}::{pin['type']['name']})-1:0]"
    else:
        width = f" [{pin['width'] - 1}:0]"
    return f"{pin['direction'].ljust(6)} bit{width} {pin['pin']}"


def group_comment(pin):
    match pin['kind']:
        case 'port':
            return f"// {pin['interfaceType']}_if.{pin['role']} on the DUT"
        case 'completion':
            return '// completion, read by the SystemC side'
    return None


def intf_decl(port, variant, name):
    params = ', '.join(f".{p['param']}({p['type']['pkg']}::{p['type']['name']})"
                       for p in port['paramTypes'][variant])
    params = f" #({params})" if params else ''
    return f"{port['interfaceType']}_if{params} {name}();"


def pin_assigns(portPins, suffix):
    # Each signal crosses in the direction the DUT sees it.
    out = list()
    for pin in portPins:
        intfSignal = f"{pin['port']}{suffix}.{pin['signal']}"
        lhs, rhs = (pin['pin'], intfSignal) if pin['direction'] == 'output' else (intfSignal, pin['pin'])
        out.append(f"assign {lhs} = {rhs};")
    return out


def dut_flags(rtl, model):
    return [f"assign rtl_dut = 1'b{int(rtl)};", f"assign model_dut = 1'b{int(model)};"]


def render_body(prj, data, variant, top):
    pins = prj.getUvmTopBoundaryPins(data, top['hdlTop'])
    portPins = [pin for pin in pins if pin['kind'] == 'port']
    duts = data['uvm']['duts']

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

    body = [intf_decl(port, variant, port['name']) for port in data['uvm']['ports']]
    for clock in data['uvm']['clocks']:
        reset = clock['reset'] or "1'b1"
        body.append(f"a2c_clk_if {clock['clock']}_if(.clk({clock['clock']}), .rst_n({reset}));")
    out += [f'    {line}' for line in body]
    out.append('')

    binds = [f".{pin['pin']}({pin['port']}.{pin['signal']})" for pin in portPins]
    binds += [f".{pin['pin']}({pin['pin']})" for pin in pins if pin['kind'] == 'clockReset']
    rtl = [f"{top['hdlTop']} dut ("]
    rtl += [f"    {bind}," for bind in binds[:-1]] + [f"    {binds[-1]}", ');', '']
    ties = list()
    for pin in portPins:
        if pin['direction'] == 'output':
            tie = "'0" if pin['vector'] else "1'b0"
            ties.append(f"assign {pin['pin']} = {tie};")
    if 'model' in duts:
        branches = list()
        if 'both' in duts:
            both = [intf_decl(port, variant, f"{port['name']}_model") for port in data['uvm']['ports']]
            both += ['', *rtl, *pin_assigns(portPins, '_model'), *dut_flags(True, True)]
            branches.append(('A2C_UVM_BOTH_DUT', both))
        branches.append(('A2C_UVM_RTL_DUT', rtl + ties + dut_flags(True, False)))
        for index, (define, lines) in enumerate(branches):
            out.append(f"`{'ifdef' if index == 0 else 'elsif'} {define}")
            out += [f'    {line}' if line else '' for line in lines]
        out.append('`else')
        out += [f'    {line}' for line in pin_assigns(portPins, '') + dut_flags(False, True)]
        out.append('`endif')
    else:
        out += [f'    {line}' if line else '' for line in rtl + ties + dut_flags(True, False)]
    out.append('')

    sets = [f'uvm_config_db#({top["pkgName"]}::{port["name"]}_vif_t)::set(null, "uvm_test_top.*", "{port["name"]}", {port["name"]});'
            for port in data['uvm']['ports']]
    sets += [f'uvm_config_db#(virtual a2c_clk_if)::set(null, "uvm_test_top.*", "{clock["clock"]}", {clock["clock"]}_if);'
             for clock in data['uvm']['clocks']]
    sets = [f'        {line}' for line in sets]
    dual = 'uvm_config_db#(bit)::set(null, "uvm_test_top.*", "a2c_dual_dut", 1\'b{});'
    if 'both' in duts:
        sets.append('`ifdef A2C_UVM_BOTH_DUT')
        sets += [f'        uvm_config_db#({top["pkgName"]}::{port["name"]}_vif_t)::set(null, "uvm_test_top.*", '
                 f'"{port["name"]}_model", {port["name"]}_model);' for port in data['uvm']['ports']]
        sets += [f'        {dual.format(1)}', '`else', f'        {dual.format(0)}', '`endif']
    else:
        sets.append(f'        {dual.format(0)}')
    out += [
        '    // run_test() returns after the report phase because finish_on_completion',
        '    // is off, and SystemC ends the simulation through its end-of-test vote.',
        '    // A UVM_FATAL calls $finish inside run_test(), so uvm_done stays low and',
        '    // the SystemC side fails the run.',
        '    initial begin',
        '        uvm_report_server srv;',
        "        uvm_done = 1'b0;",
        "        uvm_errors = '0;",
        *sets,
        '        uvm_root::get().finish_on_completion = 0;',
        '        run_test();',
        '        srv = uvm_report_server::get_server();',
        '        uvm_errors = srv.get_severity_count(UVM_ERROR) + srv.get_severity_count(UVM_FATAL);',
        f"        @(posedge {data['defaultClock']});",
        "        uvm_done = 1'b1;",
        '    end',
    ]
    return '\n' + '\n'.join(out) + '\n'
