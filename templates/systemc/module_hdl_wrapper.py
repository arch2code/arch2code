import pysrc.intf_gen_utils as intf_gen_utils

import textwrap

from jinja2 import Template

# args from generator line
# prj object
# data set dict
def render(args, prj, data):

    return textwrap.indent(render_sc(args, prj, data), ' '*args.sectionindent)


def render_sc(args, prj, data):
    # `data` is per-block when this template renders block-mode files
    # (`<block>_hdl_sc_wrapper.h`) and project/hierarchy-level when it
    # renders `vl_wrap.cpp`. Per-block keys are absent in the latter,
    # so defaults keep hierarchy-mode rendering working.
    isParameterizable = data.get('isParameterizable', False)
    defaultConfig = data.get('defaultConfig', '') if isParameterizable else ''
    # `<block>Base` is emitted as a class template only when the block
    # declares own `params:` (see intf_gen_utils.block_config_decl /
    # block_config_arg). When the block is parameterizable only through
    # contained children (e.g. `ip_top`), `<block>Base` is a plain class
    # and the wrapper's base-class inheritance line must omit the
    # template-argument list.
    cfg = f'<{defaultConfig}>' if (isParameterizable and data.get('hasOwnParams')) else ''

    # When the block declares its own `params:`, the wrapper class itself is
    # templated on a second `Config` type parameter. Each per-variant `using`
    # typedef binds `Config` to the variant's emitted `<block><Variant>Config`
    # struct, so the wrapper inherits `<block>Base<Config>` and its BFM /
    # hdl_if declarations carry `<Config>` through to the instantiation site
    # rather than collapsing onto a project-wide default. Blocks that are
    # parameterizable only through contained children (no own params) keep
    # the non-Config-templated wrapper and continue to bind the project-wide
    # `defaultConfig` so BFM, hdl_if, and base-class types stay self-consistent.
    qualBlock = data.get('qualBlock', '')
    hasOwnParams = bool(data.get('hasOwnParams', False))
    useOwnVariantConfig = bool(isParameterizable and qualBlock and hasOwnParams)
    variantConfigForName = dict()
    if useOwnVariantConfig:
        for desc in data['variantConfigs']:
            if desc['values']:
                variantConfigForName[desc['variant']] = desc['configName']
            else:
                variantConfigForName[desc['variant']] = defaultConfig
    wrapperCfgTemplateArg = 'Config' if useOwnVariantConfig else ''
    # The wrapper class is genuinely emitted as a class template only when
    # variants exist to specialize it (otherwise the non-templated branch of
    # `sec_hdl_sc_wrapper_class_template` is used). The BFM / hdl_if
    # substitution below has to match: keep `<Config>` literal when the
    # wrapper is Config-templated, otherwise substitute the project-wide
    # default so the non-templated class body type-checks.
    wrapperIsConfigTemplated = useOwnVariantConfig and bool(data.get('variants'))

    def sec_channel_decl(args, prj, data):
        s = []
        for port_type in data['ports']:
            for port, port_data in data['ports'][port_type].items():
                if mp_sig[port]['is_skip']:
                    continue
                s.append(mp_sig[port]['channel_decl'])
        s = '\n'.join(s)
        return s

    def sec_bfm_includes(args, prj, data):
        s = []
        for context in sorted(data.get('configIncludeContext', {})):
            if context in data['includeFiles'].get('config_hdr', {}):
                s.append(f'#include "{data["includeFiles"]["config_hdr"][context]["baseName"]}"')
        block_intf_set = intf_gen_utils.get_set_intf_types(data['interfaceTypes'], data)
        for intf_type in sorted(block_intf_set):
            intf_def = intf_gen_utils.get_intf_defs(intf_type, data)
            if intf_def.get('skip', None):
                continue
            s.append(f'#include "{intf_type}_bfm.h"')
        s = '\n'.join(s)
        return s

    def sec_bfm_decl(args, prj, data):
        s = []
        for port_type in data['ports']:
            for port in data['ports'][port_type]:
                if mp_sig[port]['is_skip']:
                    continue
                s.append(mp_sig[port]['bfm_decl'])
        s = '\n'.join(s)
        return s

    def sec_bfm_ctor_init(args, prj, data):
        s = []
        for port_type in data['ports']:
            for port in data['ports'][port_type]:
                if mp_sig[port]['is_skip']:
                    continue
                s.append(mp_sig[port]['bfm_ctor_init'])
        s = (',\n'.join(s) + ',') if s else ''
        return s

    def sec_dut_connect(args, prj, data):
        s = []
        for port_type in data['ports']:
            for port in data['ports'][port_type]:
                s.append('\n'.join(mp_sig[port]['dut_ports_decl']))
        s.append(f'dut_hdl->clk(clk);')
        s.append(f'dut_hdl->rst_n(rst_n);')
        s = '\n'.join(s)
        return s

    def sec_bfm_connect(args, prj, data):
        s = []
        # Inherited ports (e.g. `ipDataIf`, `out0`) live on the
        # `<block>Base{cfg}` base class. When the wrapper is Config-templated
        # (cfg names a template parameter) those names are dependent and
        # require `this->` to be looked up. `this->` is also legal on the
        # non-templated path, so it is emitted unconditionally.
        for port_type in data['ports']:
            for port in data['ports'][port_type]:
                if mp_sig[port]['is_skip']:
                    continue
                s_ = []
                intf_name = data['ports'][port_type][port]['name']
                bfm_name = intf_name + '_bfm'
                hdl_intf_name = intf_name + '_hdl_if'
                s_.append(f'{bfm_name}.if_p(this->{intf_name});')
                s_.append(f'{bfm_name}.hdl_if_p({hdl_intf_name});')
                s_.append(f'{bfm_name}.clk(clk);')
                s_.append(f'{bfm_name}.rst_n(rst_n);')
                s.append('\n'.join(s_))
        s = '\n\n'.join(s)
        return s

    def sec_hdl_if_decl(args, prj, data):
        s = []
        for port_type in data['ports']:
            for port in data['ports'][port_type]:
                s.append(mp_sig[port]['hdl_if_decl'])
        s = '\n'.join(s)
        return s

    def sec_hdl_sc_wrapper_class(args, prj, data):
        t = Template(sec_hdl_sc_wrapper_class_template)
        # When the wrapper exposes Config as a second template
        # parameter, the base-class binding uses that template name
        # rather than the block default. Verifies at compile time that
        # each variant typedef provides a Config with the per-variant
        # override fields.
        variants = data.get('variants', {})
        useOwnVariantTemplateArg = useOwnVariantConfig and bool(variants)
        baseCfg = f'<{wrapperCfgTemplateArg}>' if useOwnVariantTemplateArg else cfg
        s = t.render(
            blockname=data['blockName'], variants=variants,
            is_parameterizable=isParameterizable,
            cfg=baseCfg,
            default_config=defaultConfig,
            use_own_variant_config=useOwnVariantTemplateArg,
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
        return(t.render(
            blockname=data['blockName'], variants=data['variants'],
            use_own_variant_config=useOwnVariantConfig,
            variant_cfg=variantConfigForName,
            default_config=defaultConfig,
        ))

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

    # ports blaster
    mp_sig = dict()
    if not args.hierarchy:
        for port_type in data['ports']:
            for port in data['ports'][port_type] if not args.hierarchy else []:
                mp_sig[port] = intf_gen_utils.sc_gen_modport_signal_blast(data['ports'][port_type][port], prj, data)
                # Leave `<Config>` literal when the wrapper class itself is
                # templated on `Config` (its per-variant typedefs supply the
                # concrete Config). Substitute the project-wide default Config
                # only on the non-Config-templated path so BFM and hdl_if
                # decls in a non-templated wrapper body still name a concrete
                # type.
                if isParameterizable and not wrapperIsConfigTemplated:
                    for key in ['bfm_decl', 'hdl_if_decl']:
                        mp_sig[port][key] = mp_sig[port][key].replace('<Config>', f'<{defaultConfig}>')

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

        case _ : raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are hdl_sc_wrapper_class, channel_decl, bfm_decl, bfm_ctor_init, dut_connect, bfm_connect, hdl_if_decl, variant_include_sv_wrapper_header, variant_class_template_spec, factory_register_vl_decl, factory_register_vl_incl")

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
{% if use_own_variant_config -%}
using {{blockname}}_{{var}}_hdl_sc_wrapper = {{blockname}}_hdl_sc_wrapper<{{blockname}}_{{var}}_hdl_sv_wrapper, {{variant_cfg.get(var, default_config)}}>;
{% else -%}
using {{blockname}}_{{var}}_hdl_sc_wrapper = {{blockname}}_hdl_sc_wrapper<{{blockname}}_{{var}}_hdl_sv_wrapper>;
{% endif -%}
{% endfor -%}
#else
{% for var in variants -%}
{% if use_own_variant_config -%}
using {{blockname}}_{{var}}_hdl_sc_wrapper = {{blockname}}_hdl_sc_wrapper<V{{blockname}}_{{var}}_hdl_sv_wrapper, {{variant_cfg.get(var, default_config)}}>;
{% else -%}
using {{blockname}}_{{var}}_hdl_sc_wrapper = {{blockname}}_hdl_sc_wrapper<V{{blockname}}_{{var}}_hdl_sv_wrapper>;
{% endif -%}
{% endfor -%}
#endif\
"""

sec_hdl_sc_wrapper_class_template = """\
{% if sec_bfm_includes %}
{{ sec_bfm_includes }}
{% endif %}
{%- if variants %}
{%- if use_own_variant_config %}
template <typename DUT_T, typename Config>
{%- else %}
template <typename DUT_T>
{%- endif %}
{%- endif %}
class {{blockname}}_hdl_sc_wrapper: public sc_module, public blockBase, public {{blockname}}Base{{cfg}} {

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
{%- if use_own_variant_config %}
                "{{blockname}}_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < {{blockname}}_hdl_sc_wrapper<DUT_T, Config> > (blockName, variant, bbMode));
                }, variant_);
{%- else %}
                "{{blockname}}_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < {{blockname}}_hdl_sc_wrapper<DUT_T> > (blockName, variant, bbMode));
                }, variant_);
{%- endif %}
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

{% if use_own_variant_config %}    // SC_HAS_PROCESS expects a single macro argument; the Config-templated
    // self type carries a comma in its argument list and must be aliased.
    using {{blockname}}_hdl_sc_wrapper_self_t = {{blockname}}_hdl_sc_wrapper<DUT_T, Config>;
    SC_HAS_PROCESS ({{blockname}}_hdl_sc_wrapper_self_t);
{%- else %}    SC_HAS_PROCESS ({{blockname}}_hdl_sc_wrapper<DUT_T>);
{%- endif %}
{%- endif %}

    {{blockname}}_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("{{blockname}}_hdl_sc_wrapper", name(), bbMode),
        {{blockname}}Base{{cfg}}(name(), variant),
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
