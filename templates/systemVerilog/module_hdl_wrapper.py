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
    if args.section != '':
        raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are body or empty")
    # A parent-owned foreign wrapper carries --parent on its param line: the top
    # is owner-qualified and instantiates the child's canonical .svh body. A bare
    # same-project variant trampoline has no --parent.
    # Dispatch on the block's DECLARED variants: one standalone .sv top is
    # scaffolded per declared variant, whether or not an instance selects it. A
    # parameterized hasVl leaf reached only via inheritContainerParam has an empty
    # instantiated-variant view, so keying on declared variants keeps its
    # per-variant tops on the parameterized trampoline path instead of the
    # non-parameterizable fallback.
    if args.parent and args.variant and args.variant in data['declaredVariants']:
        return render_trampoline(args, prj, data, mp_sig, foreign=True)
    if args.variant and args.variant in data['declaredVariants']:
        return render_trampoline(args, prj, data, mp_sig)
    return render_non_parameterizable(args, prj, data, mp_sig, blk_name)

def param_names(data):
    # Default-less DUT parameter names, from the block's declared params on the
    # view (data['blockInfo'] is the block row). The parameter set is a property
    # of the block (identical across variants) and is present whether the block
    # is reached by an explicit variant: selector or by inheritContainerParam
    # (which leaves the instantiated-variant view empty).
    return [p['param'] for p in data['blockInfo']['params']]

def parameterized_decls(prj, data):
    # Split the block's module-local parameterized declaration set into the
    # eval-derived constant localparams and the type/struct declarations. The
    # flattened port widths reuse the constants, so they go in the parameter
    # port list; the typedefs follow the port list in module scope.
    if not data['parameterizedDecls']:
        return [], []
    entries = parameterizedDeclLines(
        data['parameterizedDecls'], prj, data['blockInfo']['params'])
    constDecls = [e for e in entries if e['declKind'] == 'constant']
    typeDecls = [e for e in entries if e['declKind'] != 'constant']
    return constDecls, typeDecls

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
    s += intf_gen_utils.sv_clock_reset_input_lines(data) + '\n'
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
    # The DUT is the (project-qualified) design-block module, so instantiate it
    # by its qualified module name. The wrapper's own body/top module names stay
    # plain (filename-coupled verilated tops); only the instantiated DUT tracks
    # the block rename.
    s = f"{data['blockModuleName']}{blk_param} dut (\n"
    s_1 = ''
    for port_type in data['ports']:
        for port, port_data in data['ports'][port_type].items():
            intf_name = port_data['name']
            connectionData = port_data.get('connection', {})
            intf_data = intf_gen_utils.get_intf_data(connectionData, prj)
            intf_type = intf_gen_utils.get_intf_type(intf_data['interfaceType'], data) + '_if'
            intf_dir = port_data['direction']
            s_1 += f".{intf_name}({intf_name}), // {intf_type}.{intf_dir}\n"
    s_1 += ',\n'.join(intf_gen_utils.sv_clock_reset_binds(data)) + '\n'
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
    module_name = data['svWrapper']['bodyModule']
    out = '\n'
    out += f'module {module_name}\n'

    startingContext = data['blockInfo']['_context']
    out += textwrap.indent(importPackages(args, prj, startingContext, data), ' '*4)

    params = param_names(data)
    constDecls, typeDecls = parameterized_decls(prj, data)

    # Eval-derived localparams that a flattened port width references (e.g. a
    # grid width used as an array size) must be in scope in the port list, so
    # they are declared as localparams in the parameter port list after the
    # #() parameters they depend on.
    param_list = [f'parameter {p}' for p in params]
    param_list += [f"localparam {c['name']} = {c['rhs']}" for c in constDecls]
    out += '\n#(\n'
    out += textwrap.indent(',\n'.join(param_list), ' '*4)
    out += '\n) (\n'
    out += textwrap.indent(port_decl_block(prj, data, mp_sig), ' '*4)
    out += ');\n'

    # Module-local parameterizable type/struct declarations. C3.1 moved the
    # parameterized boundary types/structs out of the package into module
    # scope, so the wrapper cannot resolve them through its package import.
    # They follow the port list (typedefs cannot live in the parameter port
    # list) and resolve the #() parameters and the localparams declared above.
    if typeDecls:
        s = ''.join(decl['line'] + '\n' for decl in typeDecls)
        out += textwrap.indent(s, ' '*4) + '\n'

    out += textwrap.indent(intf_reconstruction(prj, data, mp_sig), ' '*4)

    blk_param = ' #(' + ", ".join([f".{p}({p})" for p in params]) + ')'
    out += textwrap.indent(dut_instantiation(prj, data, blk_name, blk_param), ' '*4) + '\n'

    out += f'\nendmodule : {module_name}\n'
    return out

def render_trampoline(args, prj, data, mp_sig, foreign=False):
    # Variant top trampoline (.sv). The canonical body is made visible by the
    # `include in the scaffold. The trampoline declares the variant's concrete
    # parameter values as localparams, reuses the Stage-1 symbolic port widths,
    # and wires every flattened port through to the canonical body by name.
    #
    # `foreign`: a PARENT-OWNED owner-qualified top for a variant the assembler
    # declares foreign to a reused child (the file carries --parent). The top
    # name is owner-qualified by the emitting (declaring) project so it stays a
    # distinct Verilator design unit across projects; a same-project variant
    # keeps the bare child-emitted top name. The body module (the `include`d
    # .svh) is the child's canonical wrapper either way.
    variant_name = args.variant
    # Declared-variant bindings (with resolved literal values); a standalone top
    # exists for every declared variant, not only instance-bound ones.
    variant_data = data['declaredVariants'][variant_name]
    if foreign:
        module_name = data['svWrapper']['foreignVariantTops'][variant_name]
    else:
        module_name = data['svWrapper']['variantTops'][variant_name]
    body_module = data['svWrapper']['bodyModule']

    out = '\n'
    out += f'`include "{data["svWrapper"]["bodyInclude"]}"\n\n'
    out += f'module {module_name}\n'
    # Import the block's packages so a binding value written as a project
    # constant (e.g. bob bound to BOB0) resolves by name in the parameter port
    # list. The parent instantiation and the canonical body already import
    # these; the trampoline names the bound values directly, so it needs them
    # in scope too.
    startingContext = data['blockInfo']['_context']
    out += textwrap.indent(importPackages(args, prj, startingContext, data), ' '*4)
    # Bind the variant's concrete parameter values as localparams in the
    # parameter port list, then declare the eval-derived constant localparams
    # the flattened port widths reuse (e.g. a grid width used as an array
    # size). Both precede (and are in scope for) the port list; the derived
    # constants follow the bound root parameters they depend on.
    constDecls, _unusedTypeDecls = parameterized_decls(prj, data)
    # One binding row per parameter, first occurrence wins. A reused child bound
    # to the same variant name by more than one declaring context (the foreign
    # case) surfaces duplicate per-param rows in the view; a single-context
    # variant is already unique, so this preserves its order and output exactly.
    variant_params = []
    seen_params = set()
    for _, var_data in variant_data.items():
        if var_data['param'] in seen_params:
            continue
        seen_params.add(var_data['param'])
        variant_params.append(var_data)
    # The per-variant wrapper is a standalone Verilator top with no parent
    # scope, so bind the resolved concrete value: a symbol binding such as
    # value: OUT0_DATA_WIDTH would otherwise leak an out-of-scope parent symbol.
    param_list = [f"localparam {var_data['param']} = {var_data['resolvedValue']}" for var_data in variant_params]
    param_list += [f"localparam {c['name']} = {c['rhs']}" for c in constDecls]
    out += '\n#(\n'
    out += textwrap.indent(',\n'.join(param_list), ' '*4)
    out += '\n)(\n'
    out += textwrap.indent(port_decl_block(prj, data, mp_sig), ' '*4)
    out += ');\n'

    inst = f'{body_module} #(\n'
    inst += textwrap.indent(',\n'.join([f".{var_data['param']}({var_data['param']})" for var_data in variant_params]), ' '*4)
    inst += '\n) u_wrapper (\n'
    names = []
    for port_type in data['ports']:
        for port in data['ports'][port_type]:
            names += mp_sig[port]['names']
    conns = [f".{name}({name})" for name in names]
    conns += intf_gen_utils.sv_clock_reset_binds(data)
    inst += textwrap.indent(',\n'.join(conns), ' '*4) + '\n'
    inst += ');\n'
    out += textwrap.indent(inst, ' '*4)

    out += f'\nendmodule : {module_name}\n'
    return out

def render_non_parameterizable(args, prj, data, mp_sig, blk_name):
    # Single self-contained wrapper body for a non-parameterizable block: no
    # parameters and no variants, so the wrapper instantiates the DUT directly.
    module_name = data['svWrapper']['bodyModule']

    out = '\n'
    out += f'module {module_name}\n'

    # packages
    startingContext = data['blockInfo']['_context']
    out += textwrap.indent(importPackages(args, prj, startingContext, data), ' '*4)
    out += '\n(\n'

    out += textwrap.indent(port_decl_block(prj, data, mp_sig), ' '*4)
    out += ');\n'

    out += textwrap.indent(intf_reconstruction(prj, data, mp_sig), ' '*4)

    out += textwrap.indent(dut_instantiation(prj, data, blk_name, ''), ' '*4) + '\n'

    out += f'\nendmodule : {module_name}\n'
    return out
