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
        # vl_trace() below calls dut_hdl->trace(tfp, ...), passing the
        # VerilatedVcdC* it receives into a VerilatedTraceBaseC* parameter; that
        # derived-to-base conversion needs the complete type, which blockBase.h
        # deliberately only forward-declares (see the comment there).
        s.append('#ifdef VERILATOR')
        s.append('#include "verilated_vcd_c.h"')
        s.append('#endif')
        # A module import does not propagate the base module's own context
        # imports / using-directives the way the old textual `<block>Base.h`
        # did. The Verilated SC wrapper class spells the DUT's interface struct
        # types unqualified, so re-emit the block's interface-context imports
        # (and their using-directives) at the top of the wrapper's generated
        # region (global scope).
        for context in data['includeContext']:
            if context in data['includeFiles'].get('include_cppm', {}):
                s.extend(intf_gen_utils.cpp_context_include_lines(prj, context))
        s.extend(intf_gen_utils.cpp_own_config_import(data))
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
        return ',\n'.join(s)

    def sec_clock_decl(args, prj, data):
        # A gated sc_signal, not an sc_clock: under socket lockstep every clock
        # must stop while the Python partner holds the quantum, and an sc_clock
        # cannot be paused.
        return '\n'.join(f"sc_signal<bool> {row['clock']};" for row in data['clocks'])

    def sec_clock_ctor_init(args, prj, data):
        return ',\n'.join(f'{row["clock"]}("{row["clock"]}")' for row in data['clocks'])

    def sec_clock_half_decl(args, prj, data):
        # An `output` block clock is produced by the DUT and observed, not
        # generated: it needs no half-period to toggle on.
        return '\n'.join(f"sc_time {row['clock']}_half_;"
                         for row in data['clocks'] if row['direction'] == 'input')

    def sec_clock_half_ctor_init(args, prj, data):
        # Each clock runs at its own declared period; the half period is what the
        # generator toggles on.
        return ',\n'.join(f'{row["clock"]}_half_(sc_time({row["period"]}, '
                          f'{SC_TIME_UNIT[row["timeUnit"]]}) / 2)'
                          for row in data['clocks'] if row['direction'] == 'input')

    def sec_clock_start(args, prj, data):
        return '\n'.join(f"{row['clock']}.write(true);"
                         for row in data['clocks'] if row['direction'] == 'input')

    def sec_clock_threads(args, prj, data):
        return '\n'.join(f"SC_THREAD(clock_gen_{row['clock']});"
                         for row in data['clocks'] if row['direction'] == 'input')

    def sec_clock_gens(args, prj, data):
        return '\n'.join(f"void clock_gen_{row['clock']}() {{ clock_gen({row['clock']}, {row['clock']}_half_); }}"
                         for row in data['clocks'] if row['direction'] == 'input')

    def sec_reset_decl(args, prj, data):
        return '\n'.join(f"sc_signal<bool> {row['reset']};" for row in data['resets'])

    def sec_reset_ctor_init(args, prj, data):
        # Born released: the driver's first write(false) is then a real negedge,
        # which Verilator's async-reset processes need to see.
        return ',\n'.join(f'{row["reset"]}("{row["reset"]}", true)' for row in data['resets'])

    def sec_reset_threads(args, prj, data):
        # An `output` block reset is produced by the DUT and observed, not
        # driven: it gets no driver thread.
        return '\n'.join(f"SC_THREAD({resetDriverName(row)});"
                         for row in data['resets'] if row['direction'] == 'input')

    def sec_reset_drivers(args, prj, data):
        # One thunk per reset, counting edges of THAT reset's own clock: two
        # resets in domains of different periods must not be released together.
        return '\n'.join(f'void {resetDriverName(row)}() {{ reset_driver({row["reset"]}, '
                         f'{row["clock"]}, {row["releaseCycles"]}); }}'
                         for row in data['resets'] if row['direction'] == 'input')

    def sec_edge_track_decl(args, prj, data):
        # End-of-run report: one edge counter per OUTPUT clock this
        # wrapper observes (never drives), and one release
        # flag per OUTPUT reset. The wrapper observes the block's own output
        # clocks and resets; internal nets elsewhere in the design are not
        # visible here.
        s = [f"int {row['clock']}_edges_ = 0;"
            for row in data['clocks'] if row['direction'] == 'output']
        s += [f"bool {row['reset']}_released_ = false;"
             for row in data['resets'] if row['direction'] == 'output']
        return '\n'.join(s)

    def sec_edge_track_registrations(args, prj, data):
        s = [f"SC_METHOD({row['clock']}_edge_count); sensitive << {row['clock']}.value_changed_event(); "
            f"dont_initialize();"
            for row in data['clocks'] if row['direction'] == 'output']
        s += [f"SC_METHOD({row['reset']}_release_track); sensitive << {row['reset']}.value_changed_event(); "
             f"dont_initialize();"
             for row in data['resets'] if row['direction'] == 'output']
        return '\n'.join(s)

    def sec_edge_track_methods(args, prj, data):
        s = [f"void {row['clock']}_edge_count() {{ {row['clock']}_edges_++; }}"
            for row in data['clocks'] if row['direction'] == 'output']
        s += [f"void {row['reset']}_release_track() {{ if ({row['reset']}.read()) "
             f"{row['reset']}_released_ = true; }}"
             for row in data['resets'] if row['direction'] == 'output']
        return '\n'.join(s)

    def sec_end_of_simulation(args, prj, data):
        # An output clock with no edge or an output reset never released is
        # reported here rather than left to a silent, activity-free run.
        lines = [f'if (!{row["clock"]}_edges_) {{ std::cerr << "warning: '
                f'clock \'{row["clock"]}\' produced no edge by end of run" '
                f'<< std::endl; }}'
                for row in data['clocks'] if row['direction'] == 'output']
        lines += [f'if (!{row["reset"]}_released_) {{ std::cerr << "warning: '
                 f'output reset \'{row["reset"]}\' was never observed to '
                 f'release during the run" << std::endl; }}'
                 for row in data['resets'] if row['direction'] == 'output']
        return '\n'.join(lines)

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
        concrete = sc_concrete_dut(data['svWrapper'], data['standaloneVariants'])
        t = Template(sec_hdl_sc_wrapper_class_template)
        # A templated wrapper binds its base class to its own `Config` template
        # parameter, so the concrete Config comes from the registrar.
        isTemplate = data['svWrapper']['scWrapperConfigTemplated']
        # The end-of-run report has nothing to say for a block with no
        # OUTPUT clock or reset (there is nothing this wrapper observes
        # rather than drives), so the override is emitted only then -
        # otherwise every hasVl wrapper gets an empty override body.
        has_edge_track = any(row['direction'] == 'output' for row in data['clocks']) \
            or any(row['direction'] == 'output' for row in data['resets'])
        # Each section below returns its joined entries with no trailing
        # comma, so an empty section (e.g. no resets) drops out cleanly
        # instead of leaving a bare ',' in the initialiser list.
        sec_ctor_init = ',\n'.join(p for p in (
            sec_clock_ctor_init(args, prj, data),
            sec_bfm_ctor_init(args, prj, data),
            sec_reset_ctor_init(args, prj, data),
            sec_clock_half_ctor_init(args, prj, data),
        ) if p)
        s = t.render(
            blockname=data['blockName'],
            sc_wrapper_class=data['svWrapper']['scWrapperModule'],
            is_template=isTemplate,
            has_edge_track=has_edge_track,
            concrete_sv_module=concrete['svModule'],
            concrete_dut_class=concrete['dutClass'],
            cfg='<Config>' if isTemplate else cfg,
            sec_bfm_includes=sec_bfm_includes(args, prj, data),
            sec_bfm_decl=sec_bfm_decl(args, prj, data),
            sec_ctor_init=sec_ctor_init,
            sec_dut_connect=sec_dut_connect(args, prj, data),
            sec_bfm_connect=sec_bfm_connect(args, prj, data),
            sec_hdl_if_decl=sec_hdl_if_decl(args, prj, data),
            sec_clock_decl=sec_clock_decl(args, prj, data),
            sec_clock_half_decl=sec_clock_half_decl(args, prj, data),
            sec_clock_start=sec_clock_start(args, prj, data),
            sec_clock_threads=sec_clock_threads(args, prj, data),
            sec_clock_gens=sec_clock_gens(args, prj, data),
            sec_reset_decl=sec_reset_decl(args, prj, data),
            sec_reset_threads=sec_reset_threads(args, prj, data),
            sec_reset_drivers=sec_reset_drivers(args, prj, data),
            sec_edge_track_decl=sec_edge_track_decl(args, prj, data),
            sec_edge_track_registrations=sec_edge_track_registrations(args, prj, data),
            sec_edge_track_methods=sec_edge_track_methods(args, prj, data),
            sec_end_of_simulation=sec_end_of_simulation(args, prj, data)
        )
        return(s)

    def sec_preamble(args, prj, data):
        # File-scope preamble for the generated Verilated SC wrapper. The baseline
        # the generated class names directly - systemc.h for sc_module/sc_clock/
        # sc_signal/SC_THREAD and blockBase.h for the blockBase base class and
        # blockBaseMode ctor argument - plus the block's own Base import, all
        # emitted from this region so `make gen` re-spells them every run
        # (self-healing after the Base header->C++20-module migration).
        # blockBase.h cannot ride in on `import <block>.base;`: it sits in that
        # module's global module fragment, whose names are reachable but not
        # visible to an importer.
        # A concrete wrapper names its verilated DUT directly, so it also
        # includes that DUT header (from the svWrapper view). A templated
        # wrapper is a reusable `<DUT_T, Config>` header; its concrete DUT
        # header + `_verif` registration live in the per-assembler VlRegistrar.
        concrete = sc_concrete_dut(data['svWrapper'], data['standaloneVariants'])
        t = Template(sec_preamble_template)
        basemodule = intf_gen_utils.cpp_base_module_name(data['blockModuleName'])
        return(t.render(is_template=data['svWrapper']['scWrapperConfigTemplated'],
                        basemodule=basemodule,
                        dut_header=concrete['dutHeader'],
                        vcs_dut_header=concrete['vcsDutHeader'],
                        xcelium_dut_header=concrete['xceliumDutHeader']))

    # ports blaster
    mp_sig = dict()
    if not args.hierarchy:
        isTemplate = data['svWrapper']['scWrapperConfigTemplated']
        for port_type in data['ports']:
            for port in data['ports'][port_type] if not args.hierarchy else []:
                mp_sig[port] = intf_gen_utils.sc_gen_modport_signal_blast(data['ports'][port_type][port], prj, data)
                # A concrete wrapper inherits a NON-dependent base, whose public
                # member aliases are already concrete non-templates. The bare
                # name resolves to those through class scope; appending a
                # template argument list to one is `error: expected '>'`.
                if isParameterizable and not isTemplate:
                    for key in ['bfm_decl', 'hdl_if_decl']:
                        mp_sig[port][key] = mp_sig[port][key].replace('<Config>', '')

    match args.section:
        case 'preamble' : return sec_preamble(args, prj, data)
        case 'hdl_sc_wrapper_class' : return sec_hdl_sc_wrapper_class(args, prj, data)
        case 'channel_decl': return sec_channel_decl(args, prj, data)
        case 'bfm_decl': return sec_bfm_decl(args, prj, data)
        case 'bfm_ctor_init':
            # Emitted standalone, the section ends in a comma, ready for the
            # member initialisers that follow it.
            s = sec_bfm_ctor_init(args, prj, data)
            return s + ',' if s else ''
        case 'dut_connect': return sec_dut_connect(args, prj, data)
        case 'bfm_connect': return sec_bfm_connect(args, prj, data)
        case 'hdl_if_decl': return sec_hdl_if_decl(args, prj, data)

        case _ : raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are preamble, hdl_sc_wrapper_class, channel_decl, bfm_decl, bfm_ctor_init, dut_connect, bfm_connect, hdl_if_decl")

sec_preamble_template = """\
#include "systemc.h"
#include "blockBase.h"
import {{basemodule}};
{%- if not is_template %}

// A non-templated wrapper names its RTL top concretely, so it includes the
// simulator's DUT header directly.
#if defined(VCS_DUT)
#include "{{vcs_dut_header}}"
#elif defined(XCELIUM_DUT)
#include "{{xcelium_dut_header}}"
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
{%- if is_template %}
template <typename DUT_T, typename Config>
{%- endif %}
class {{sc_wrapper_class}}: public sc_module, public blockBase, public {{blockname}}Base{{cfg}} {

public:
{%- if not is_template %}

#if defined(VCS_DUT) || defined(XCELIUM_DUT)
    {{concrete_sv_module}} *dut_hdl;
#else
    {{concrete_dut_class}} *dut_hdl;
#endif
{% else %}

    DUT_T *dut_hdl;
{% endif %}
    {{ sec_clock_decl | indent(4) }}

    {{ sec_bfm_decl | indent(4) }}
{%- if not is_template %}

    SC_HAS_PROCESS ({{sc_wrapper_class}});
{%- else %}

    // SC_HAS_PROCESS expects a single macro argument; the Config-templated
    // self type carries a comma in its argument list and must be aliased.
    using {{sc_wrapper_class}}_self_t = {{sc_wrapper_class}}<DUT_T, Config>;
    SC_HAS_PROCESS ({{sc_wrapper_class}}_self_t);
{%- endif %}

    {{sc_wrapper_class}}(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("{{sc_wrapper_class}}", name(), bbMode),
        {{blockname}}Base{{cfg}}(name(), variant){% if sec_ctor_init %},
        {{ sec_ctor_init | indent(8) }}{% endif %}
    {
{%- if not is_template %}
#if defined(VCS_DUT) || defined(XCELIUM_DUT)
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
{%- if has_edge_track %}
        {{ sec_edge_track_registrations | indent(8) }}
{%- endif %}

        end_ctor_init();

    }

public:

#ifdef VERILATOR
    void vl_trace(VerilatedVcdC* tfp, int levels, int options = 0) override {
        dut_hdl->trace(tfp, levels, options);
    }
#endif

{%- if has_edge_track %}

    // An output clock with no edge or an output reset never released is
    // reported at end of run rather than left to a silent, activity-free run.
    void end_of_simulation() override {
        {{ sec_end_of_simulation | indent(8) }}
    }
{%- endif %}

private:

    {{ sec_hdl_if_decl | indent(4) }}

    {{ sec_reset_decl | indent(4) }}
    {{ sec_clock_half_decl | indent(4) }}
{%- if has_edge_track %}
    {{ sec_edge_track_decl | indent(4) }}
{%- endif %}

    // Free-run: toggle every half period until gated lockstep begins. Gated
    // lockstep: the quantum thread broadcasts one edge request per
    // socketSyncClockHalfPeriod() of advanced time, and a clock toggles once
    // its own half period has accumulated, so a slower clock keeps its period
    // at quantum resolution and no clock can free-run during wait(ack). A half
    // period that is not a whole number of lockstep steps would be silently
    // moved onto the step grid, so it is fatal on entry to gated mode. Losing
    // the sync link ends gating for good and wakes the gated wait without an
    // edge, so the clock returns to free-running.
    void clock_gen(sc_signal<bool> &sig, const sc_time &half) {
        while (!socketSyncTimeGated()) {
            wait(half);
            sig.write(!sig.read());
        }
        const sc_time step = socketSyncClockHalfPeriod();
        Q_ASSERT(half.value() % step.value() == 0,
                 std::string("clock ") + sig.name() + " half period "
                 + half.to_string() + " is not a whole multiple of the lockstep step "
                 + step.to_string() + "; lockstep co-simulation cannot represent it. "
                 "Declare a period that is a whole multiple of " + (step + step).to_string()
                 + ", or set PYSOCKET_LOCKSTEP=0 to run free-running.");
        sc_time gated = SC_ZERO_TIME;
        while (true) {
            socketSyncWaitClockEdge();
            if (!socketSyncTimeGated()) {
                break;
            }
            gated += step;
            if (gated >= half) {
                gated -= half;
                sig.write(!sig.read());
            }
        }
        while (true) {
            wait(half);
            sig.write(!sig.read());
        }
    }

    // Lockstep with a connected partner: follow socketSyncRstN (boot release
    // and mid-sim MSG_RESET) and never wait on a clock, since gated time does
    // not advance before the first quantum. Otherwise assert, hold for the
    // declared releaseCycles edges of the reset's own clock, then release.
    // The clock parameter is named reset_driver_clk, not clk: a block whose
    // own default clock is literally named clk declares a same-named member,
    // which a parameter named clk would otherwise shadow (-Wshadow).
    void reset_driver(sc_signal<bool> &rst, sc_signal<bool> &reset_driver_clk, int cycles) {
        if (socketSyncLockstepActive()) {
            rst.write(socketSyncRstN());
            while (true) {
                wait(socketSyncRstNEvent());
                rst.write(socketSyncRstN());
            }
        } else {
            rst.write(false);
            for (int cycle = 0; cycle < cycles; cycle++) {
                wait(reset_driver_clk.posedge_event());
            }
            rst.write(true);
        }
    }

    {{ sec_clock_gens | indent(4) }}
    {{ sec_reset_drivers | indent(4) }}
{%- if has_edge_track %}
    {{ sec_edge_track_methods | indent(4) }}
{%- endif %}

"""
