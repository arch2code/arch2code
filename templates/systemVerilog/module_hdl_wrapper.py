import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.systemVerilogGeneratorHelper import importPackages
from templates.systemVerilog.package import parameterizedDeclLines
import textwrap

# args from generator line
# prj object
# data set dict
def render(args, prj, data):

    return textwrap.indent(render_sv(args, prj, data), ' '*args.sectionindent)

def render_sv(args, prj, data):

    # ports blaster
    mp_sig = dict()
    for port_type in data['ports']:
        for port in data['ports'][port_type]:
            mp_sig[port] = intf_gen_utils.sv_gen_modport_signal_blast(data['ports'][port_type][port], prj, data)

    blk_name = data['blockName']

    # The parameterizable wrapper is emitted in two pieces: one canonical
    # default-less parameterized body (the .svh, --section=body) that owns the
    # typedefs, interface reconstruction, and DUT instantiation, plus one tiny
    # top-module trampoline per variant (the .sv, --variant=...) that binds the
    # variant's parameter values and wires the flattened ports through by name.
    # Non-parameterizable blocks have no variants and emit a single
    # self-contained wrapper body.
    if args.section == 'body':
        return render_body(args, prj, data, mp_sig, blk_name)
    if args.variant and args.variant in data['variants']:
        return render_trampoline(args, prj, data, mp_sig, blk_name)
    return render_non_parameterizable(args, prj, data, mp_sig, blk_name)

def param_names(data):
    # Default-less DUT parameter names. The parameter set is identical across a
    # block's variants, so read the first variant's bound-parameter rows.
    first_variant = next(iter(data['variants'].values()))
    return [var_data['param'] for var_data in first_variant.values()]

def port_decl_block(prj, data, mp_sig):
    # ANSI flattened port list shared by the canonical body and the variant
    # trampoline.
    s = ''
    for port_type in data['ports']:
        for port, port_data in data['ports'][port_type].items():
            connectionData = port_data.get('connection', {})
            intf_data = intf_gen_utils.get_intf_data(connectionData, prj)
            intf_type = intf_gen_utils.get_intf_type(intf_data['interfaceType'], data) + '_if'
            intf_dir = port_data['direction']
            s += f'// {intf_type}.{intf_dir}\n'
            s += ',\n'.join(mp_sig[port]['ports'])
            s += ',\n'
            s += '\n'
    s += 'input clk,\ninput rst_n\n'
    return s

def intf_reconstruction(prj, data, mp_sig):
    # Interface declarations and the port<->interface assigns.
    s = ''
    for port_type in data['ports']:
        for port, port_data in data['ports'][port_type].items():
            connectionData = port_data.get('connection', {})
            intf_data = intf_gen_utils.get_intf_data(connectionData, prj)
            intf_type = intf_gen_utils.get_intf_type(intf_data['interfaceType'], data) + '_if'
            intf_dir = port_data['direction']
            s += f'// {intf_type}.{intf_dir}\n'
            s += mp_sig[port]['intf_decl'] + '\n'*2
            s += '\n'.join(mp_sig[port]['assign'])
            s += '\n'
            s += '\n'
    return s

def dut_instantiation(prj, data, blk_name, blk_param):
    s = f'{blk_name}{blk_param} dut (\n'
    s_1 = ''
    for port_type in data['ports']:
        for port, port_data in data['ports'][port_type].items():
            intf_name = port_data['name']
            connectionData = port_data.get('connection', {})
            intf_data = intf_gen_utils.get_intf_data(connectionData, prj)
            intf_type = intf_gen_utils.get_intf_type(intf_data['interfaceType'], data) + '_if'
            intf_dir = port_data['direction']
            s_1 += f".{intf_name}({intf_name}), // {intf_type}.{intf_dir}\n"
    s_1 += '.clk(clk),\n.rst_n(rst_n)\n'
    s_1 = textwrap.indent(s_1, ' '*4)
    s += s_1 + ');'

    s += '''\n
`ifdef VCS
initial if ($test$plusargs("fsdbTrace")) begin
    $fsdbDumpvars($sformatf("%m"), "+all");
end
`endif'''
    return s

def render_body(args, prj, data, mp_sig, blk_name):
    # Canonical default-less parameterized wrapper body (include-only .svh). The
    # parameters precede the ports, so the Stage-1 active-width expressions are
    # legal in the ANSI port list. The typedefs reference the #() parameters
    # directly, and the DUT parameters are passed through by name.
    module_name = f'{blk_name}_hdl_sv_wrapper'
    out = '\n'
    out += f'module {module_name}\n'

    startingContext = prj.data['blocks'][prj.getQualBlock(blk_name)]['_context']
    out += textwrap.indent(importPackages(args, prj, startingContext, data), ' '*4)

    params = param_names(data)
    out += '\n#(\n'
    out += textwrap.indent(',\n'.join(f'parameter {p}' for p in params), ' '*4)
    out += '\n) (\n'
    out += textwrap.indent(port_decl_block(prj, data, mp_sig), ' '*4)
    out += ');\n'

    # Module-local parameterizable type/struct declarations. C3.1 moved the
    # parameterized boundary types/structs out of the package into module
    # scope, so the wrapper cannot resolve them through its package import. In
    # the canonical body they are declared from the #() parameters directly.
    if data['parameterizedDecls']:
        s = ''
        for line in parameterizedDeclLines(data['parameterizedDecls'], prj):
            s += line + '\n'
        out += textwrap.indent(s, ' '*4) + '\n'

    out += textwrap.indent(intf_reconstruction(prj, data, mp_sig), ' '*4)

    blk_param = ' #(' + ", ".join([f".{p}({p})" for p in params]) + ')'
    out += textwrap.indent(dut_instantiation(prj, data, blk_name, blk_param), ' '*4) + '\n'

    out += f'\nendmodule : {module_name}\n'
    return out

def render_trampoline(args, prj, data, mp_sig, blk_name):
    # Variant top trampoline (.sv). The canonical body is made visible by the
    # `include in the scaffold. The trampoline declares the variant's concrete
    # parameter values as localparams, reuses the Stage-1 symbolic port widths,
    # and wires every flattened port through to the canonical body by name.
    variant_name = args.variant
    variant_data = data['variants'][variant_name]
    module_name = f'{blk_name}_{variant_name}_hdl_sv_wrapper'
    body_module = f'{blk_name}_hdl_sv_wrapper'

    out = '\n'
    out += f'`include "{body_module}.svh"\n\n'
    out += f'module {module_name}\n'
    # Bind the variant's concrete parameter values as localparams in the
    # parameter port list, so they precede (and are in scope for) the flattened
    # port widths that reuse the Stage-1 symbolic expressions.
    out += '#(\n'
    out += textwrap.indent(',\n'.join([f"localparam {var_data['param']} = {var_data['value']}" for _, var_data in variant_data.items()]), ' '*4)
    out += '\n)(\n'
    out += textwrap.indent(port_decl_block(prj, data, mp_sig), ' '*4)
    out += ');\n'

    inst = f'{body_module} #(\n'
    inst += textwrap.indent(',\n'.join([f".{var_data['param']}({var_data['param']})" for _, var_data in variant_data.items()]), ' '*4)
    inst += '\n) u_wrapper (\n'
    names = []
    for port_type in data['ports']:
        for port in data['ports'][port_type]:
            names += mp_sig[port]['names']
    conns = [f".{name}({name})" for name in names]
    conns += ['.clk(clk)', '.rst_n(rst_n)']
    inst += textwrap.indent(',\n'.join(conns), ' '*4) + '\n'
    inst += ');\n'
    out += textwrap.indent(inst, ' '*4)

    out += f'\nendmodule : {module_name}\n'
    return out

def render_non_parameterizable(args, prj, data, mp_sig, blk_name):
    # Single self-contained wrapper body for a non-parameterizable block: no
    # parameters and no variants, so the wrapper instantiates the DUT directly.
    module_name = f'{blk_name}_hdl_sv_wrapper'

    out = '\n'
    out += f'module {module_name}\n'

    # packages
    startingContext = prj.data['blocks'][prj.getQualBlock(blk_name)]['_context']
    out += textwrap.indent(importPackages(args, prj, startingContext, data), ' '*4)
    out += '\n(\n'

    out += textwrap.indent(port_decl_block(prj, data, mp_sig), ' '*4)
    out += ');\n'

    out += textwrap.indent(intf_reconstruction(prj, data, mp_sig), ' '*4)

    out += textwrap.indent(dut_instantiation(prj, data, blk_name, ''), ' '*4) + '\n'

    out += f'\nendmodule : {module_name}\n'
    return out
