# The SystemC wrapper of a hasUvm block's UVM testbench top, a class template
# over the simulator shell of one variant's tb module and, for a block with
# params, that variant's Config. It drives the clocks and resets into the
# shell and ends the run once UVM finishes. With the model DUT it also holds
# the model and BFMs that carry each port over the shell's pins; their roles
# are the DUT's swapped, because the BFMs face the agents' side of the pins.
import textwrap

import pysrc.intf_gen_utils as intf_gen_utils
from templates.systemc.module_hdl_wrapper import (
    sec_clock_ctor_init, sec_clock_decl, sec_clock_gens, sec_clock_half_ctor_init, sec_clock_half_decl,
    sec_clock_start, sec_clock_threads, sec_reset_decl, sec_reset_drivers, sec_reset_threads)


def render(args, prj, data):
    if args.section != 'class':
        raise ValueError(f"Unknown section '{args.section}' for template '{args.template}'. Valid values are class")
    return textwrap.indent(render_class(args, prj, data), ' '*args.sectionindent)


def indented(text, spaces):
    return textwrap.indent(text, ' '*spaces) if text else ''


def render_class(args, prj, data):
    uvm = data['uvm']
    blockName = data['blockName']
    hasMdl = data['blockInfo']['hasMdl']
    hasOwnParams = data['hasOwnParams']
    cfg = '<Config>' if hasOwnParams else ''
    wrapper = uvm['scWrapperClass']
    run = uvm['runClass']
    project = prj.config.getConfig('PROJECTNAME')

    ports = [(portData, intf_gen_utils.sc_gen_modport_signal_blast(portData, prj, data, swap_dir=True))
             for portGroup in data['ports'].values() for portData in portGroup.values()]
    pins = [pin for _, sig in ports for pin in sig['hdl_pins']]

    out = ['#include <format>', '#include <memory>', '#include <string>',
           '#include <type_traits>', '#include "systemc.h"', '#include "blockBase.h"',
           '#include "instanceFactory.h"', '#include "q_assert.h"']
    # The BFM headers also declare the <type>_hdl_if bridges the pins bind to.
    out += [f'#include "{intfType}_bfm.h"'
            for intfType in sorted(intf_gen_utils.get_set_intf_types(data['interfaceTypes'], data))]
    if hasMdl:
        out.append(f'import {intf_gen_utils.cpp_base_module_name(data["blockModuleName"])};')
        if hasOwnParams:
            out.append(f'import {intf_gen_utils.cpp_block_module_name(data["blockModuleName"])};')
    out += intf_gen_utils.cpp_block_context_include_lines(prj, data)
    out += intf_gen_utils.cpp_own_config_import(data)
    out.append('import a2c.endOfTest;')
    out.append('')

    out += [
        "// The testbench config creates the wrapper through the instanceFactory,",
        "// which passes no DUT choice, and reads the outcome in final(), so both",
        "// pass through here. A run holds one wrapper.",
        f'struct {run} {{',
        '    static constexpr const char *notFinished = "UVM testbench did not finish: uvm_done never rose";',
        '    static inline bool rtlDut = false;',
        '    static inline bool completed = false;',
        '};',
        '',
    ]

    templateParams = 'typename TB_T, typename Config' if hasOwnParams else 'typename TB_T'
    selfArgs = 'TB_T, Config' if hasOwnParams else 'TB_T'
    out += [f'template <{templateParams}>',
            f'class {wrapper} : public sc_module, public blockBase {{',
            "    // The shell takes each pin width from the boundary pin list, and the",
            "    // BFMs take theirs from the payload types.",]
    for pin in pins:
        if pin['kind'] == 'fixed':
            continue
        expected = f"{pin['scPort']}<{pin['type']}>"
        out += [f"    static_assert(std::is_same_v<decltype(TB_T::{pin['pin']}), {expected}>,",
                f'                  "{pin["pin"]} in the testbench shell is not {expected}");']

    ctorInit = [f'sc_module(modulename)', f'blockBase("{wrapper}", name(), bbMode)', 'tb_hdl("tb_hdl")',
                sec_clock_ctor_init(args, prj, data),
                # Born asserted, so the agents see reset from time 0.
                ',\n'.join(f'{row["reset"]}("{row["reset"]}", false)' for row in data['resets']),
                sec_clock_half_ctor_init(args, prj, data),
                'uvm_done("uvm_done")', 'uvm_errors("uvm_errors")', 'rtl_dut("rtl_dut")', 'm_eot(true)']
    ctorInit = ',\n'.join(entry for entry in ctorInit if entry)

    binds = [f"tb_hdl.{pin['pin']}({sig['hdl_inst_name']}.{pin['signal']});"
             for _, sig in ports for pin in sig['hdl_pins']]
    binds += [f'tb_hdl.{name}({name});' for name in intf_gen_utils.clock_reset_port_names(data)]
    binds += [f'tb_hdl.{name}({name});' for name in ('uvm_done', 'uvm_errors', 'rtl_dut')]

    out += ['public:',
            f'    using self_t = {wrapper}<{selfArgs}>;',
            '    SC_HAS_PROCESS(self_t);',
            '',
            f'    {wrapper}(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :',
            indented(ctorInit, 8),
            '    {',
            indented('\n'.join(binds), 8)]
    if hasMdl:
        # A child typed by its container's Config has no factory registration,
        # so a block with params names its class as its container does; a
        # registration under the variant still wins.
        impl = f'<{blockName}<Config>>' if hasOwnParams else ''
        model = [
            f'chnl = std::make_unique<{blockName}Channels{cfg}>("Chnl", "uvm");',
            f'dut = std::dynamic_pointer_cast<{blockName}Base{cfg}>(',
            f'    instanceFactory::createInstance{impl}(name(), "{blockName}", "{blockName}", variant, "{project}"));',
            f'Q_ASSERT(dut != nullptr, "{blockName} model instance was not created");',
        ]
        model += [f"dut->{portData['name']}(chnl->{portData['name']});" for portData, _ in ports]
        for portData, sig in ports:
            bfm = sig['bfm_inst_name']
            model += ['',
                      f'{bfm} = std::make_unique<{sig["bfm_type"]}>("{bfm}");',
                      f"{bfm}->if_p(chnl->{portData['name']});",
                      f"{bfm}->hdl_if_p({sig['hdl_inst_name']});",
                      f"{bfm}->clk({portData['domainClock']});",
                      f"{bfm}->rst_n({portData['domainReset']});"]
        out += ['',
                '        // With the RTL DUT the SV testbench holds it, and the pins toward',
                '        // SystemC stay bound to idle signals.',
                f'        if (!{run}::rtlDut) {{',
                indented('\n'.join(model), 12),
                '        }']
    out += ['',
            indented(sec_clock_start(args, prj, data), 8),
            indented(sec_clock_threads(args, prj, data), 8),
            indented(sec_reset_threads(args, prj, data), 8),
            '        SC_THREAD(uvm_watch);',
            '        SC_THREAD(eot_thread);',
            '    }',
            '',
            '    void setTimed(int nsec, timedDelayMode mode) override {}',
            '    void setLogging(verbosity_e verbosity) override {}',
            '',
            'private:',
            '    TB_T tb_hdl;',
            indented(sec_clock_decl(args, prj, data), 4),
            indented(sec_reset_decl(args, prj, data), 4),
            indented(sec_clock_half_decl(args, prj, data), 4),
            '    sc_signal<bool> uvm_done;',
            '    sc_signal<sc_bv<32>> uvm_errors;',
            '    sc_signal<bool> rtl_dut;',
            '',
            indented('\n'.join(sig['hdl_if_decl'] for _, sig in ports), 4)]
    if hasMdl:
        out += ['',
                f'    std::unique_ptr<{blockName}Channels{cfg}> chnl;',
                f'    std::shared_ptr<{blockName}Base{cfg}> dut;']
        out += [f"    std::unique_ptr<{sig['bfm_type']}> {sig['bfm_inst_name']};" for _, sig in ports]
    out += ['',
            '    endOfTest m_eot;',
            '',
            '    void clock_gen(sc_signal<bool> &sig, const sc_time &half) {',
            '        while (true) {',
            '            wait(half);',
            '            sig.write(!sig.read());',
            '        }',
            '    }',
            '',
            '    // The clock parameter is named reset_driver_clk, not clk, so it does not',
            '    // shadow a member clock named clk.',
            '    void reset_driver(sc_signal<bool> &rst, sc_signal<bool> &reset_driver_clk, int cycles) {',
            '        for (int cycle = 0; cycle < cycles; cycle++) {',
            '            wait(reset_driver_clk.posedge_event());',
            '        }',
            '        rst.write(true);',
            '    }',
            '',
            indented(sec_clock_gens(args, prj, data), 4),
            indented(sec_reset_drivers(args, prj, data), 4),
            '',
            '    void uvm_watch(void) {',
            '        while (!uvm_done.read()) {',
            '            wait(uvm_done.value_changed_event());',
            '        }',
            '        const bool svRtl = rtl_dut.read();',
            '        const uint32_t errors = uvm_errors.read().to_uint();',
            '        log_.logPrint(std::format("UVM finished with {} UVM_ERROR/UVM_FATAL; the SV testbench was built with the {} DUT",',
            '                                  errors, svRtl ? "RTL" : "model"), LOG_ALWAYS);',
            '        std::string failure;',
            f'        if (svRtl != {run}::rtlDut) {{',
            '            failure = std::format(',
            '                "--uvmDut {} does not match the snapshot, whose SV testbench holds the {} DUT",',
            f'                {run}::rtlDut ? "rtl" : "model", svRtl ? "RTL" : "model");',
            '        } else if (errors != 0) {',
            '            failure = std::format("UVM reported {} UVM_ERROR/UVM_FATAL", errors);',
            '        }',
            '        if (!failure.empty()) {',
            '            log_.logPrint(failure, LOG_ALWAYS);',
            '            errorCode::fail(failure);',
            '        }',
            f'        {run}::completed = true;',
            '        m_eot.setEndOfTest(true);',
            '    }',
            '',
            '    // A SystemC testbench ends the simulation from its External, which this',
            '    // testbench does not have.',
            '    void eot_thread(void) {',
            '        wait(endOfTestState::GetInstance().eotEvent);',
            '        sc_stop();',
            '    }',
            '};']
    return '\n' + '\n'.join(out) + '\n'
