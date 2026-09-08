import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.intf_gen_utils import sc_concrete_dut

import textwrap

from jinja2 import Template

# sc_time unit spelling per timeUnit the clocks: schema admits. A unit added to
# the schema without a spelling here fails loudly at generation.
SC_TIME_UNIT = {'ps': 'SC_PS', 'ns': 'SC_NS', 'us': 'SC_US'}

def resetDriverName(resetRow):
    # One driver thread per reset, so the method name carries the reset it drives.
    return f"reset_driver_{resetRow['reset']}"

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
            variantConfigForName[desc['variant']] = intf_gen_utils.cpp_descriptor_config_name(desc, defaultConfig)
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
        # A module import does not propagate the base module's own context
        # imports / using-directives the way the old textual `<block>Base.h`
        # did. The Verilated SC wrapper class spells the DUT's interface struct
        # types unqualified, so re-emit the block's interface-context imports
        # (and their using-directives) at the top of the wrapper's generated
        # region (global scope).
        for context in data['includeContext']:
            if context in data['includeFiles'].get('include_cppm', {}):
                s.extend(intf_gen_utils.cpp_context_include_lines(prj, data, context, 'include_cppm'))
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

    def sec_clock_decl(args, prj, data):
        # A gated sc_signal, not an sc_clock: under socket lockstep every clock
        # must stop while the Python partner holds the quantum, and an sc_clock
        # cannot be paused.
        return '\n'.join(f"sc_signal<bool> {row['clock']};" for row in data['clocks'])

    def sec_clock_ctor_init(args, prj, data):
        return ',\n'.join(f'{row["clock"]}("{row["clock"]}")' for row in data['clocks']) + ','

    def sec_clock_half_decl(args, prj, data):
        return '\n'.join(f"sc_time {row['clock']}_half_;" for row in data['clocks'])

    def sec_clock_half_ctor_init(args, prj, data):
        # Each clock runs at its own declared period; the half period is what the
        # generator toggles on.
        return ',\n'.join(f'{row["clock"]}_half_(sc_time({row["period"]}, '
                          f'{SC_TIME_UNIT[row["timeUnit"]]}) / 2)' for row in data['clocks'])

    def sec_clock_start(args, prj, data):
        return '\n'.join(f"{row['clock']}.write(true);" for row in data['clocks'])

    def sec_clock_threads(args, prj, data):
        return '\n'.join(f"SC_THREAD(clock_gen_{row['clock']});" for row in data['clocks'])

    def sec_clock_gens(args, prj, data):
        return '\n'.join(f"void clock_gen_{row['clock']}() {{ clock_gen({row['clock']}, {row['clock']}_half_); }}"
                         for row in data['clocks'])

    def sec_reset_decl(args, prj, data):
        return '\n'.join(f"sc_signal<bool> {row['reset']};" for row in data['resets'])

    def sec_reset_ctor_init(args, prj, data):
        # Born released: the driver's first write(false) is then a real negedge,
        # which Verilator's async-reset processes need to see.
        return ',\n'.join(f'{row["reset"]}("{row["reset"]}", true)' for row in data['resets'])

    def sec_reset_threads(args, prj, data):
        return '\n'.join(f"SC_THREAD({resetDriverName(row)});" for row in data['resets'])

    def sec_reset_drivers(args, prj, data):
        # One thunk per reset, counting edges of THAT reset's own clock: two
        # resets in domains of different periods must not be released together.
        return '\n'.join(f'void {resetDriverName(row)}() {{ reset_driver({row["reset"]}, '
                         f'{row["clock"]}, {row["releaseCycles"]}); }}' for row in data['resets'])

    def sec_dut_connect(args, prj, data):
        s = []
        for port_type in data['ports']:
            for port in data['ports'][port_type]:
                s.append('\n'.join(mp_sig[port]['dut_ports_decl']))
        for name in intf_gen_utils.clock_reset_port_names(data):
            s.append(f'dut_hdl->{name}({name});')
        s = '\n'.join(s)
        return s

    def sec_bfm_connect(args, prj, data):
        s = []
        # A BFM drives one interface, so both its clock and its reset are that
        # interface's own domain: the block view resolves each port's connection
        # clock into this block's derived clock set as `domainClock` and the
        # block's reset of that domain as `domainReset`, and every clock and reset
        # of those sets is a member declared here, so the binds compile.
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
                port_data = data['ports'][port_type][port]
                intf_name = port_data['name']
                bfm_name = intf_name + '_bfm'
                hdl_intf_name = intf_name + '_hdl_if'
                s_.append(f'{bfm_name}.if_p(this->{intf_name});')
                s_.append(f'{bfm_name}.hdl_if_p({hdl_intf_name});')
                s_.append(f'{bfm_name}.clk({port_data["domainClock"]});')
                s_.append(f'{bfm_name}.rst_n({port_data["domainReset"]});')
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
        concrete = sc_concrete_dut(data['svWrapper'], data['declaredVariants'])
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
            concrete_sv_module=concrete['svModule'],
            concrete_dut_class=concrete['dutClass'],
            cfg=baseCfg,
            default_config=defaultConfig,
            use_own_variant_config=useOwnVariantTemplateArg,
            sec_bfm_includes=sec_bfm_includes(args, prj, data),
            sec_bfm_decl=sec_bfm_decl(args, prj, data),
            sec_bfm_ctor_init=sec_bfm_ctor_init(args, prj, data),
            sec_dut_connect=sec_dut_connect(args, prj, data),
            sec_bfm_connect=sec_bfm_connect(args, prj, data),
            sec_hdl_if_decl=sec_hdl_if_decl(args, prj, data),
            sec_clock_decl=sec_clock_decl(args, prj, data),
            sec_clock_ctor_init=sec_clock_ctor_init(args, prj, data),
            sec_clock_half_decl=sec_clock_half_decl(args, prj, data),
            sec_clock_half_ctor_init=sec_clock_half_ctor_init(args, prj, data),
            sec_clock_start=sec_clock_start(args, prj, data),
            sec_clock_threads=sec_clock_threads(args, prj, data),
            sec_clock_gens=sec_clock_gens(args, prj, data),
            sec_reset_decl=sec_reset_decl(args, prj, data),
            sec_reset_ctor_init=sec_reset_ctor_init(args, prj, data),
            sec_reset_threads=sec_reset_threads(args, prj, data),
            sec_reset_drivers=sec_reset_drivers(args, prj, data)
        )
        return(s)

    def sec_preamble(args, prj, data):
        # File-scope preamble for the generated Verilated SC wrapper: the block's
        # own Base import, emitted from this region so `make gen` re-spells it
        # every run (self-healing after the Base header->C++20-module migration).
        # A block with no instance-bound variants keeps a concrete wrapper that
        # names its verilated DUT directly, so it also includes that DUT header
        # (from the svWrapper view). A parameterizable wrapper is a reusable
        # `<DUT_T, Config>` template; its concrete DUT header + `_verif`
        # registration live in the per-assembler VlRegistrar, not here.
        concrete = sc_concrete_dut(data['svWrapper'], data['declaredVariants'])
        t = Template(sec_preamble_template)
        basemodule = intf_gen_utils.cpp_base_module_name(data['blockModuleName'])
        return(t.render(variants=data['variants'], basemodule=basemodule,
                        dut_header=concrete['dutHeader'],
                        sv_wrapper_header=f"{concrete['svModule']}.h"))

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
                        mp_sig[port][key] = mp_sig[port][key].replace('<Config>', '')

    match args.section:
        case 'preamble' : return sec_preamble(args, prj, data)
        case 'hdl_sc_wrapper_class' : return sec_hdl_sc_wrapper_class(args, prj, data)
        case 'channel_decl': return sec_channel_decl(args, prj, data)
        case 'bfm_decl': return sec_bfm_decl(args, prj, data)
        case 'bfm_ctor_init': return sec_bfm_ctor_init(args, prj, data)
        case 'dut_connect': return sec_dut_connect(args, prj, data)
        case 'bfm_connect': return sec_bfm_connect(args, prj, data)
        case 'hdl_if_decl': return sec_hdl_if_decl(args, prj, data)

        case _ : raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are preamble, hdl_sc_wrapper_class, channel_decl, bfm_decl, bfm_ctor_init, dut_connect, bfm_connect, hdl_if_decl")

sec_preamble_template = """\
import {{basemodule}};
{%- if not variants %}

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "{{sv_wrapper_header}}"
#else
#include "{{dut_header}}"
#endif
{%- endif %}\
"""

sec_hdl_sc_wrapper_class_template = """\
{% if sec_bfm_includes %}
{{ sec_bfm_includes }}
{% endif %}
#include "socketSync.h"
{%- if variants %}
{%- if use_own_variant_config %}
template <typename DUT_T, typename Config>
{%- else %}
template <typename DUT_T>
{%- endif %}
{%- endif %}
class {{blockname}}_hdl_sc_wrapper: public sc_module, public blockBase, public {{blockname}}Base{{cfg}} {

public:
{%- if not variants %}

#if !defined(VERILATOR) && defined(VCS)
    {{concrete_sv_module}} *dut_hdl;
#else
    {{concrete_dut_class}} *dut_hdl;
#endif
{% else %}

    DUT_T *dut_hdl;
{% endif %}
    {{ sec_clock_decl | indent(4) }}

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
        {{ sec_clock_ctor_init | indent(8) }}
        {{ sec_bfm_ctor_init | indent(8) }}
        {{ sec_reset_ctor_init | indent(8) }},
        {{ sec_clock_half_ctor_init | indent(8) }}
    {
{%- if not variants %}
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new {{concrete_sv_module}}("dut_hdl");
#else
        dut_hdl = new {{concrete_dut_class}}("dut_hdl");
#endif
{%- else %}
        dut_hdl = new DUT_T("dut_hdl");
{%- endif %}

        {{ sec_dut_connect | indent(8) }}

        {{ sec_bfm_connect | indent(8) }}

        {{ sec_clock_start | indent(8) }}
        {{ sec_clock_threads | indent(8) }}
        {{ sec_reset_threads | indent(8) }}

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

    {{ sec_reset_decl | indent(4) }}
    {{ sec_clock_half_decl | indent(4) }}

    // Free-run: toggle every half period. Gated lockstep: the quantum thread
    // broadcasts one edge request per socketSyncClockHalfPeriod() of advanced
    // time, and a clock toggles once its own half period has accumulated, so a
    // slower clock keeps its period at quantum resolution and no clock can
    // free-run during wait(ack).
    void clock_gen(sc_signal<bool> &sig, const sc_time &half) {
        sc_time gated = SC_ZERO_TIME;
        while (true) {
            if (socketSyncTimeGated()) {
                socketSyncWaitClockEdge();
                gated += socketSyncClockHalfPeriod();
                if (gated >= half) {
                    gated -= half;
                    sig.write(!sig.read());
                }
            } else {
                wait(half);
                sig.write(!sig.read());
            }
        }
    }

    // Lockstep with a connected partner: follow socketSyncRstN (boot release
    // and mid-sim MSG_RESET) and never wait on a clock, since gated time does
    // not advance before the first quantum. Otherwise assert, hold for the
    // declared releaseCycles edges of the reset's own clock, then release.
    void reset_driver(sc_signal<bool> &rst, sc_signal<bool> &clk, int cycles) {
        if (socketSyncLockstepActive()) {
            rst.write(socketSyncRstN());
            while (true) {
                wait(socketSyncRstNEvent());
                rst.write(socketSyncRstN());
            }
        } else {
            rst.write(false);
            for (int cycle = 0; cycle < cycles; cycle++) {
                wait(clk.posedge_event());
            }
            rst.write(true);
        }
    }

    {{ sec_clock_gens | indent(4) }}
    {{ sec_reset_drivers | indent(4) }}

"""
