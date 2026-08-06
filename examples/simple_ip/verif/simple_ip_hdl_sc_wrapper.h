#ifndef SIMPLE_IP_HDL_SC_WRAPPER_H_
#define SIMPLE_IP_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=simple_ip
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import simple_ip.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "simple_ip_hdl_sv_wrapper.h"
#else
#include "Vsimple_ip_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import common_shared_types;
using namespace common_shared_types_ns;
import simple_ip;
using namespace simple_ip_ns;
import ip;
using namespace ip_ns;
#include "ipVariantConfig.h"
#include "apb_bfm.h"
#include "push_ack_bfm.h"

#include "socketSync.h"
class simple_ip_hdl_sc_wrapper: public sc_module, public blockBase, public simple_ipBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    simple_ip_hdl_sv_wrapper *dut_hdl;
#else
    Vsimple_ip_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    apb_dst_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> cpu_main_bfm;

    SC_HAS_PROCESS (simple_ip_hdl_sc_wrapper);

    simple_ip_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("simple_ip_hdl_sc_wrapper", name(), bbMode),
        simple_ipBase(name(), variant),
        clk("clk"),
        cpu_main_bfm("cpu_main_bfm"),
        rst_n(0),
        clk_half_(0.5, SC_NS)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new simple_ip_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new Vsimple_ip_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->cpu_main_paddr(cpu_main_hdl_if.paddr);
        dut_hdl->cpu_main_psel(cpu_main_hdl_if.psel);
        dut_hdl->cpu_main_penable(cpu_main_hdl_if.penable);
        dut_hdl->cpu_main_pwrite(cpu_main_hdl_if.pwrite);
        dut_hdl->cpu_main_pwdata(cpu_main_hdl_if.pwdata);
        dut_hdl->cpu_main_pready(cpu_main_hdl_if.pready);
        dut_hdl->cpu_main_prdata(cpu_main_hdl_if.prdata);
        dut_hdl->cpu_main_pslverr(cpu_main_hdl_if.pslverr);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        cpu_main_bfm.if_p(this->cpu_main);
        cpu_main_bfm.hdl_if_p(cpu_main_hdl_if);
        cpu_main_bfm.clk(clk);
        cpu_main_bfm.rst_n(rst_n);

        clk.write(true);
        SC_THREAD(clock_gen);
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

    apb_hdl_if<sc_bv<32>, sc_bv<32>> cpu_main_hdl_if;

    sc_signal<bool> rst_n;
    sc_time clk_half_;

    void clock_gen() {
        // 1 ns period, 50% duty. Under lockstep gated mode the quantum thread
        // owns timed waits; we only toggle when an edge is requested.
        while (true) {
            if (socketSyncTimeGated()) {
                socketSyncWaitClockEdge();
                clk.write(!clk.read());
            } else {
                wait(clk_half_);
                clk.write(!clk.read());
            }
        }
    }

    void reset_driver() {
        for (int i = 0; i < 5; ++i) {
            wait(clk.posedge_event());
        }
        rst_n = true;
    }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // SIMPLE_IP_HDL_SC_WRAPPER_H_
