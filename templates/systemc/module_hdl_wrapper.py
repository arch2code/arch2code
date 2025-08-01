import pysrc.intf_gen_utils as intf_gen_utils

import textwrap

from jinja2 import Template

# args from generator line
# prj object
# data set dict
def render(args, prj, data):

    return textwrap.indent(render_sc(args, prj, data), ' '*args.sectionindent)


def render_sc(args, prj, data):

    def sec_channel_decl(args, prj, data):
        s = []
        for port in data['ports']:
            if mp_sig[port]['is_skip']:
                continue
            s.append(mp_sig[port]['channel_decl'])
        s = '\n'.join(s)
        return s

    def sec_bfm_includes(args, prj, data):
        s = []
        block_intf_set = set(
            [v['interfaceData']['interfaceType'] for v in data['ports'].values()] +
            [v['interfaceType'] for v in data['connections'].values()]
        )
        for intf_type in sorted(block_intf_set):
            if intf_gen_utils.INTF_DEFS[intf_type].get('skip', None):
                continue
            s.append(f'#include "{intf_type}_bfm.h"')
        s = '\n'.join(s)
        return s

    def sec_bfm_decl(args, prj, data):
        s = []
        for port in data['ports']:
            if mp_sig[port]['is_skip']:
                continue
            s.append(mp_sig[port]['bfm_decl'])
        s = '\n'.join(s)
        return s

    def sec_bfm_ctor_init(args, prj, data):
        s = []
        for port in data['ports']:
            if mp_sig[port]['is_skip']:
                continue
            s.append(mp_sig[port]['bfm_ctor_init'])
        s = (',\n'.join(s) + ',') if s else ''
        return s

    def sec_dut_connect(args, prj, data):
        s = []
        for port in data['ports']:
            s.append('\n'.join(mp_sig[port]['dut_ports_decl']))
        s.append(f'dut_hdl->clk(clk);')
        s.append(f'dut_hdl->rst_n(rst_n);')
        s = '\n'.join(s)
        return s

    def sec_bfm_connect(args, prj, data):
        s = []
        for port in data['ports']:
            s_ = []
            if mp_sig[port]['is_skip']:
                continue
            intf_name = data['ports'][port]['name']
            bfm_name = intf_name + '_bfm'
            hdl_intf_name = intf_name + '_hdl_if'
            s_.append(f'{bfm_name}.if_p({intf_name});')
            s_.append(f'{bfm_name}.hdl_if_p({hdl_intf_name});')
            s_.append(f'{bfm_name}.clk(clk);')
            s_.append(f'{bfm_name}.rst_n(rst_n);')
            s.append('\n'.join(s_))
        s = '\n\n'.join(s)
        return s

    def sec_hdl_if_decl(args, prj, data):
        s = []
        for port in data['ports']:
            s.append(mp_sig[port]['hdl_if_decl'])
        s = '\n'.join(s)
        return s

    def sec_hdl_sc_wrapper_class(args, prj, data):
        t = Template(sec_hdl_sc_wrapper_class_template)
        s = t.render(
            blockname=data['blockName'], variants=data['variants'],
            sec_bfm_includes=sec_bfm_includes(args, prj, data),
            sec_bfm_decl=sec_bfm_decl(args, prj, data),
            sec_bfm_ctor_init=sec_bfm_ctor_init(args, prj, data),
            sec_dut_connect=sec_dut_connect(args, prj, data),
            sec_bfm_connect=sec_bfm_connect(args, prj, data),
            sec_hdl_if_decl=sec_hdl_if_decl(args, prj, data)
        )
        return(s)

    def sec_var_include_sv_wrap_header(args, prj, data):
        t = Template(sec_var_include_sv_wrap_header_template)
        return(t.render(blockname=data['blockName'], variants=data['variants']))

    def sec_variant_class_template_spec(args, prj, data):
        t = Template(sec_variant_class_template_spec_template)
        return(t.render(blockname=data['blockName'], variants=data['variants']))

    def factory_register_vl_decl(args, prj, data):
        s = []
        #print(prj.data['parametersvariants'])
        for key,data in prj.data['blocks'].items():
            hasVl, block = data['hasVl'], data['block']
            if hasVl:
                variants = prj.getQualBlockVariants(key)
                if variants:
                    for variant in variants:
                        s.append(f'template<> {block}_{variant}_hdl_sc_wrapper::registerBlock {block}_{variant}_hdl_sc_wrapper::registerBlock_("{variant}");')
                else:
                    s.append(f'{block}_hdl_sc_wrapper::registerBlock {block}_hdl_sc_wrapper::registerBlock_;')
        s = '\n'.join(s)
        return s

    def factory_register_vl_incl(args, prj, data):
        s = []
        for key,data in prj.data['blocks'].items():
            hasVl, block = data['hasVl'], data['block']
            if hasVl:
                s.append(f'#include "{block}_hdl_sc_wrapper.h"')
        s = '\n'.join(s)
        return s

    if not args.hierarchy:

        # A bit of preprocessing to filter out register ports based on block first 
        data['regPorts'] = {k: v for k, v in data['regPorts'].items() if v['interfaceData']['block'] != data['blockName']}
        # Add to the block ports for easier processing
        data['ports'].update(data['regPorts'])

    # ports blaster
    mp_sig = dict()
    for port in data['ports'] if not args.hierarchy else []:
        mp_sig[port] = intf_gen_utils.sc_gen_modport_signal_blast(data['ports'][port], prj)

    match args.section:
        case 'hdl_sc_wrapper_class' : return sec_hdl_sc_wrapper_class(args, prj, data)
        case 'channel_decl': return sec_channel_decl(args, prj, data)
        case 'bfm_decl': return sec_bfm_decl(args, prj, data)
        case 'bfm_ctor_init': return sec_bfm_ctor_init(args, prj, data)
        case 'dut_connect': return sec_dut_connect(args, prj, data)
        case 'bfm_connect': return sec_bfm_connect(args, prj, data)
        case 'hdl_if_decl': return sec_hdl_if_decl(args, prj, data)

        case 'variant_include_sv_wrapper_header' : return sec_var_include_sv_wrap_header(args, prj, data)
        case 'variant_class_template_spec' : return sec_variant_class_template_spec(args, prj, data)

        case 'factory_register_vl_decl' : return factory_register_vl_decl(args, prj, data)
        case 'factory_register_vl_incl' : return factory_register_vl_incl(args, prj, data)

        case _ : return 'xx'

sec_var_include_sv_wrap_header_template = """\
#if !defined(VERILATOR) && defined(VCS)
{% for var in variants -%}
#include "{{blockname}}_{{var}}_hdl_sv_wrapper.h"
{% endfor -%}
#else
{% for var in variants -%}
#include "V{{blockname}}_{{var}}_hdl_sv_wrapper.h"
{% endfor -%}
#endif\
"""

sec_variant_class_template_spec_template = """\
#if !defined(VERILATOR) && defined(VCS)
{% for var in variants -%}
using {{blockname}}_{{var}}_hdl_sc_wrapper = {{blockname}}_hdl_sc_wrapper<{{blockname}}_{{var}}_hdl_sv_wrapper>;
{% endfor -%}
#else
{% for var in variants -%}
using {{blockname}}_{{var}}_hdl_sc_wrapper = {{blockname}}_hdl_sc_wrapper<V{{blockname}}_{{var}}_hdl_sv_wrapper>;
{% endfor -%}
#endif\
"""

sec_hdl_sc_wrapper_class_template = """\
{% if sec_bfm_includes %}
{{ sec_bfm_includes }}
{% endif %}
{%- if variants %}
template <typename DUT_T>
{%- endif %}
class {{blockname}}_hdl_sc_wrapper: public sc_module, public blockBase, public {{blockname}}Base {

public:

    struct registerBlock
    {
{%- if not variants %}
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "{{blockname}}_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < {{blockname}}_hdl_sc_wrapper > (blockName, variant, bbMode));
                });
        }
{%- else %}
        registerBlock(const char *variant_)
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "{{blockname}}_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < {{blockname}}_hdl_sc_wrapper<DUT_T> > (blockName, variant, bbMode));
                }, variant_);
        }
{%- endif %}
    };

    static registerBlock registerBlock_;
{%- if not variants %}

#if !defined(VERILATOR) && defined(VCS)
    {{blockname}}_hdl_sv_wrapper *dut_hdl;
#else
    V{{blockname}}_hdl_sv_wrapper *dut_hdl;
#endif
{% else %}

    DUT_T *dut_hdl;
{% endif %}
    sc_clock clk;

    {{ sec_bfm_decl | indent(4) }}
{%- if not variants %}

    SC_HAS_PROCESS ({{blockname}}_hdl_sc_wrapper);
{%- else %}

    SC_HAS_PROCESS ({{blockname}}_hdl_sc_wrapper<DUT_T>);
{%- endif %}

    {{blockname}}_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("{{blockname}}_hdl_sc_wrapper", name(), bbMode),
        {{blockname}}Base(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        {{ sec_bfm_ctor_init | indent(8) }}
        rst_n(0)
    {
{%- if not variants %}
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new {{blockname}}_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new V{{blockname}}_hdl_sv_wrapper("dut_hdl");
#endif
{%- else %}
        dut_hdl = new DUT_T("dut_hdl");
{%- endif %}

        {{ sec_dut_connect | indent(8) }}

        {{ sec_bfm_connect | indent(8) }}

        SC_THREAD(reset_driver);

        end_ctor_init();

    }

public:

#ifdef VERILATOR
    void vl_trace(VerilatedVcdC* tfp, int levels, int options = 0) override {
        dut_hdl->trace(tfp, levels, options);
    }
#endif

private:

    {{ sec_hdl_if_decl | indent(4) }}

    sc_signal<bool> rst_n;

    void reset_driver() {
        wait(5, SC_NS);
        rst_n = true;
    }

"""
