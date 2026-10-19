# The variant package of a hasUvm block. SV cannot parameterize a package, so
# the package binds the variant's parameter values as localparams and declares
# the block's parameterized types from them. The testbench interfaces and the
# agents must be typed by these package types: a struct declared locally in a
# module is a different type, and its virtual interface does not assign to one
# typed by the package. The items section also holds the register model and
# the env, both generated whole; a test package extends the env.
import textwrap

from pysrc.systemVerilogGeneratorHelper import importPackages
from templates.systemVerilog.package import parameterizedDeclLines


def render(args, prj, data):
    # A block without params has one variantless top, which its scaffold
    # names with no --variant.
    variant = args.variant or ''
    top = data['uvm']['tops'][variant]
    match args.section:
        case 'header':
            out = render_header(args, prj, data, top)
        case 'items':
            out = render_items(prj, data, variant)
        case 'footer':
            out = f"\nendpackage : {top['pkgName']}\n"
        case _:
            raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are header, items or footer")
    return textwrap.indent(out, ' '*args.sectionindent)


def render_header(args, prj, data, top):
    out = f"\npackage {top['pkgName']};\n"
    lines = ['import uvm_pkg::*;', '`include "uvm_macros.svh"']
    lines += [f'import {pkg}::*;' for pkg in data['uvm']['agentPackages']]
    lines.append(importPackages(args, prj, data['blockInfo']['_context'], data))
    out += textwrap.indent('\n'.join(lines), ' '*4) + '\n'
    return out


def agent_typedefs(port):
    # Unbound optional parameters keep the class and interface defaults. A
    # port with no bound parameter names the classes with no #().
    args = ', '.join(f".{b['structureType']}({b['structure']})"
                    for b in port['paramBindings'] if not b['isNull'])
    params = f" #({args})" if args else ''
    name = port['name']
    intfType = port['interfaceType']
    return [f"typedef {intfType}_agent{params} {name}_agent_t;",
            f"typedef {name}_agent_t::item_t {name}_item_t;",
            f"typedef {name}_agent_t::config_t {name}_config_t;",
            f"typedef virtual {intfType}_if{params} {name}_vif_t;"]


def render_items(prj, data, variant):
    lines = list()
    if data['blockInfo']['params']:
        values = data['standaloneVariants'][variant]
        lines += [f"localparam {p['param']} = {values[p['param']]};" for p in data['blockInfo']['params']]
        lines += [decl['line'] for decl in parameterizedDeclLines(
            data['parameterizedDecls'], prj, data['blockInfo']['params'])]
        lines.append('')
    for port in data['uvm']['ports']:
        lines += agent_typedefs(port)
    uvm = data['uvm']
    hasRegModel = uvm['registerBus'] is not None
    if hasRegModel:
        for reg in uvm['registers']:
            lines += [''] + reg_class(reg, variant)
        lines += [''] + reg_block_class(uvm, variant)
    lines += [''] + env_class(uvm, hasRegModel, variant)
    return '\n' + textwrap.indent('\n'.join(lines), ' '*4) + '\n'


def reg_class(reg, variant):
    cls = reg['className']
    fields = reg['fields'][variant]
    lines = [f"class {cls} extends uvm_reg;"]
    lines += [f"    rand uvm_reg_field {f['name']};" for f in fields]
    lines += ['',
              f"    `uvm_object_utils({cls})",
              '',
              f'    function new(string name = "{reg["name"]}");',
              f"        super.new(name, {reg['width'][variant]}, UVM_NO_COVERAGE);",
              '    endfunction',
              '',
              '    virtual function void build();']
    access = reg['uvmAccess']
    volatile = int(reg['volatile'])
    isRand = int(access == 'RW')
    for f in fields:
        lines.append(f'        {f["name"]} = uvm_reg_field::type_id::create("{f["name"]}");')
        lines.append(f'        {f["name"]}.configure(this, {f["width"]}, {f["lsb"]}, "{access}", {volatile}, '
                     f"{f['width']}'h{f['reset']:x}, 1, {isRand}, 0);")
    lines += ['    endfunction', f"endclass : {cls}"]
    return lines


def reg_block_class(uvm, variant):
    cls = uvm['regBlockClass']
    lines = [f"class {cls} extends uvm_reg_block;"]
    lines += [f"    rand {reg['className']} {reg['name']};" for reg in uvm['registers']]
    lines += [f"    uvm_mem {mem['name']};" for mem in uvm['memories']]
    lines += ['',
              f"    `uvm_object_utils({cls})",
              '',
              f'    function new(string name = "{cls}");',
              '        super.new(name, UVM_NO_COVERAGE);',
              '    endfunction',
              '',
              '    virtual function void build();']
    for reg in uvm['registers']:
        name = reg['name']
        lines += [f'        {name} = {reg["className"]}::type_id::create("{name}");',
                  f"        {name}.configure(this);",
                  f"        {name}.build();"]
    if uvm['memories']:
        lines += ["        // n_bits pads a memory row so that UVM's stride of ceil(n_bits / 32)",
                  "        // bus words is the decoder's row stride."]
    for mem in uvm['memories']:
        name = mem['name']
        lines += [f'        {name} = new("{name}", {mem["count"][variant]}, {mem["nBits"][variant]}, '
                  f'"{mem["uvmAccess"]}", UVM_NO_COVERAGE);',
                  f"        {name}.configure(this);"]
        lines += [f'        uvm_resource_db#(bit)::set({{"REG::", {name}.get_full_name()}}, "{resource}", 1, this);'
                  for resource in mem['excludeTests'][variant]]
    lines.append("        default_map = create_map(\"default_map\", 'h0, 4, UVM_LITTLE_ENDIAN, 1);")
    for reg in uvm['registers']:
        lines.append(f'        default_map.add_reg({reg["name"]}, \'h{reg["offset"]:x}, "{reg["uvmAccess"]}");')
    for mem in uvm['memories']:
        lines.append(f'        default_map.add_mem({mem["name"]}, \'h{mem["offset"]:x}, "{mem["mapRights"]}");')
    lines += ['        lock_model();', '    endfunction', f"endclass : {cls}"]
    return lines


def env_class(uvm, hasRegModel, variant):
    cls = uvm['envClass']
    ports = uvm['ports']
    counters = [port for port in ports if port['counter']]
    lines = [f"class {cls} extends uvm_env;"]
    lines += [f"    {port['name']}_agent_t {port['agent']};" for port in ports]
    lines += [f"    a2c_uvm_pkg::a2c_txn_counter #({port['name']}_item_t) {port['counter']};" for port in counters]
    lines += [f"    virtual a2c_clk_if {clock['vif']};" for clock in uvm['clocks']]
    bus = uvm['registerBus']
    if hasRegModel:
        lines += [f"    {uvm['regBlockClass']} regmodel;",
                  f"    {bus['adapterClass']} adapter;",
                  f"    uvm_reg_predictor #({bus['port']}_item_t) predictor;"]
    lines += ['',
              f"    `uvm_component_utils({cls})",
              '',
              '    function new(string name, uvm_component parent);',
              '        super.new(name, parent);',
              '    endfunction',
              '',
              '    virtual function void build_phase(uvm_phase phase);']
    lines += [f"        {port['name']}_config_t {port['name']}_cfg;" for port in ports]
    lines.append('        super.build_phase(phase);')
    for clock in uvm['clocks']:
        name = clock['clock']
        lines += [f'        if (!uvm_config_db#(virtual a2c_clk_if)::get(this, "", "{name}", {clock["vif"]})) begin',
                  f'            `uvm_fatal("A2C_CFG", "no virtual a2c_clk_if \'{name}\'")',
                  '        end']
    for port in ports:
        lines += [''] + agent_build(port, variant)
    if hasRegModel:
        lines += ['',
                  f'        regmodel = {uvm["regBlockClass"]}::type_id::create("regmodel");',
                  '        regmodel.build();',
                  '        regmodel.reset();',
                  f'        adapter = {bus["adapterClass"]}::type_id::create("adapter");',
                  f'        predictor = uvm_reg_predictor#({bus["port"]}_item_t)::type_id::create("predictor", this);']
    lines += ['    endfunction']
    if counters or hasRegModel:
        lines += ['']
        if hasRegModel:
            lines += ["    // The register model's mirror follows the bus through the explicit",
                      "    // predictor, not the register calls' own prediction."]
        lines.append('    virtual function void connect_phase(uvm_phase phase);')
        lines += [f"        {port['agent']}.mon.ap.connect({port['counter']}.analysis_export);" for port in counters]
        if hasRegModel:
            agent = bus['agent']
            lines += [f"        regmodel.default_map.set_sequencer({agent}.sqr, adapter);",
                      '        regmodel.default_map.set_auto_predict(0);',
                      '        predictor.map     = regmodel.default_map;',
                      '        predictor.adapter = adapter;',
                      f"        {agent}.mon.ap.connect(predictor.bus_in);"]
        lines.append('    endfunction')
    lines.append(f"endclass : {cls}")
    return lines


def agent_build(port, variant):
    # An agent plays the side opposite the DUT port's modport.
    name = port['name']
    cfg = f"{name}_cfg"
    lines = [f'        {cfg} = {name}_config_t::type_id::create("{cfg}");',
             f'        if (!uvm_config_db#({name}_vif_t)::get(this, "", "{name}", {cfg}.vif)) begin',
             f'            `uvm_fatal("A2C_CFG", "no virtual {port["interfaceType"]}_if \'{name}\'")',
             '        end',
             f"        {cfg}.clk_vif = {port['clockVif']};",
             f"        {cfg}.role = a2c_uvm_pkg::{'A2C_SRC' if port['role'] == 'dst' else 'A2C_DST'};",
             f'        {cfg}.port_name = "{name}";']
    if port['backpressureOverridable']:
        lines.append(f"        {cfg}.no_backpressure = {int(not port['backpressure'])};")
    if port['maxTransferBytes'] is not None:
        lines.append(f"        {cfg}.max_transfer_bytes = {port['maxTransferBytes'][variant]};")
    if port['idUnbound']:
        lines.append(f"        {cfg}.id_unbound = 1;")
    agent = port['agent']
    lines += [f'        uvm_config_db#({name}_config_t)::set(this, "{agent}", "cfg", {cfg});',
              f'        {agent} = {name}_agent_t::type_id::create("{agent}", this);']
    if port['counter']:
        counter = port['counter']
        lines += [f'        {counter} = a2c_uvm_pkg::a2c_txn_counter#({name}_item_t)::type_id::create("{counter}", this);',
                  f'        {counter}.port_name = "{name}";']
    return lines
