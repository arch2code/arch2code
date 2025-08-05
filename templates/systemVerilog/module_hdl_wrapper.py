import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.systemVerilogGeneratorHelper import importPackages
import textwrap

# args from generator line
# prj object
# data set dict
def render(args, prj, data):

    return textwrap.indent(render_sv(args, prj, data), ' '*args.sectionindent)

def render_sv(args, prj, data):

    # A bit of preprocessing to filter out register ports based on block first 
    data['regPorts'] = {k: v for k, v in data['regPorts'].items() if v['interfaceData']['block'] != data['blockName']}
    # Add to the block ports for easier processing
    data['ports'].update(data['regPorts'])

    # ports blaster
    mp_sig = dict()
    for port in data['ports']:
        mp_sig[port] = intf_gen_utils.sv_gen_modport_signal_blast(data['ports'][port], prj.data)

    out = '\n'

    blk_name = data['blockName']

    if ( args.variant and args.variant in data['variants'] ):
        variant_name = args.variant
        variant_data = data['variants'][variant_name]
    else:
        variant_data = None

    if (variant_data):
        module_name = f'{blk_name}_{variant_name}_hdl_sv_wrapper'
    else:
        module_name = f'{blk_name}_hdl_sv_wrapper'

    # module

    out += f'module {module_name}\n'

    # packages
    startingContext = prj.data['blocks'][prj.getQualBlock(data['blockName'])]['_context']
    out += textwrap.indent(importPackages(args, prj, startingContext, data), ' '*4)
    out += '(\n'

    # ports
    s = ''
    for port in data['ports']:
        intf_type = data['ports'][port]['interfaceData']['interfaceType'] + '_if'
        intf_dir = data['ports'][port]['direction']
        s += f'// {intf_type}.{intf_dir}\n'
        s += ',\n'.join(mp_sig[port]['ports'])
        s += ',\n'
        s += '\n'
    s += 'input clk,\ninput rst_n\n'
    out += textwrap.indent(s, ' '*4)
    out += ');\n'

    # assigns ports<->interface
    s = ''
    for port in data['ports']:
        intf_type = data['ports'][port]['interfaceData']['interfaceType'] + '_if'
        intf_dir = data['ports'][port]['direction']
        s += f'// {intf_type}.{intf_dir}\n'
        s += mp_sig[port]['intf_decl'] + '\n'*2
        s += '\n'.join(mp_sig[port]['assign'])
        s += '\n'
        s += '\n'

    out += textwrap.indent(s, ' '*4)

    # dut parameters decl
    blk_param = ''
    if ( variant_data ):
        blk_param = ' #('
        blk_param += ", ".join([f".{var_data['param']}({var_data['value']})" for _,var_data in variant_data.items()])
        blk_param += ')'
    else:
        blk_param = ''

    # dut assign port decl

    s = f'{blk_name}{blk_param} dut (\n'
    s_1 = ''
    for port in data['ports']:
        intf_name = data['ports'][port]['name']
        intf_type = data['ports'][port]['interfaceData']['interfaceType'] + '_if'
        intf_dir = data['ports'][port]['direction']
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

    out += textwrap.indent(s, ' '*4) + '\n'

    out += f'\nendmodule : {module_name}\n'

    return out
