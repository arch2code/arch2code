#ifndef IP_HDL_SC_WRAPPER_H_
#define IP_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=ip
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import ip.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import ip;
using namespace ip_ns;
#include "ipVariantConfig.h"
#include "apb_bfm.h"
#include "push_ack_bfm.h"

#include "socketSync.h"
template <typename DUT_T, typename Config>
class ip_hdl_sc_wrapper: public sc_module, public blockBase, public ipBase<Config> {

public:

    DUT_T *dut_hdl;

    sc_signal<bool> clk;

    push_ack_dst_bfm<ipDataSt<Config>, sc_bv<ipDataSt<Config>::_bitWidth>> ipDataIf_bfm;
    apb_dst_bfm<ipRegAddrSt, ipRegDataSt, sc_bv<32>, sc_bv<32>> regs_bfm;

    // SC_HAS_PROCESS expects a single macro argument; the Config-templated
    // self type carries a comma in its argument list and must be aliased.
    using ip_hdl_sc_wrapper_self_t = ip_hdl_sc_wrapper<DUT_T, Config>;
    SC_HAS_PROCESS (ip_hdl_sc_wrapper_self_t);

    ip_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("ip_hdl_sc_wrapper", name(), bbMode),
        ipBase<Config>(name(), variant),
        clk("clk"),
        ipDataIf_bfm("ipDataIf_bfm"),
        regs_bfm("regs_bfm"),
        rst_n("rst_n", true),
        clk_half_(0.5, SC_NS)
    {
        dut_hdl = new DUT_T("dut_hdl");

        dut_hdl->ipDataIf_push(ipDataIf_hdl_if.push);
        dut_hdl->ipDataIf_data(ipDataIf_hdl_if.data);
        dut_hdl->ipDataIf_ack(ipDataIf_hdl_if.ack);
        dut_hdl->regs_paddr(regs_hdl_if.paddr);
        dut_hdl->regs_psel(regs_hdl_if.psel);
        dut_hdl->regs_penable(regs_hdl_if.penable);
        dut_hdl->regs_pwrite(regs_hdl_if.pwrite);
        dut_hdl->regs_pwdata(regs_hdl_if.pwdata);
        dut_hdl->regs_pready(regs_hdl_if.pready);
        dut_hdl->regs_prdata(regs_hdl_if.prdata);
        dut_hdl->regs_pslverr(regs_hdl_if.pslverr);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        ipDataIf_bfm.if_p(this->ipDataIf);
        ipDataIf_bfm.hdl_if_p(ipDataIf_hdl_if);
        ipDataIf_bfm.clk(clk);
        ipDataIf_bfm.rst_n(rst_n);

        regs_bfm.if_p(this->regs);
        regs_bfm.hdl_if_p(regs_hdl_if);
        regs_bfm.clk(clk);
        regs_bfm.rst_n(rst_n);

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

    push_ack_hdl_if<sc_bv<ipDataSt<Config>::_bitWidth>> ipDataIf_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> regs_hdl_if;

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
        // rst_n starts deasserted so the first write(false) is a negedge.
        // Verilator async reset (@(negedge rst_n)) does not run if the pin
        // is born low and only later rises.
        // Lockstep: follow socketSyncRstN (boot release + mid-sim MSG_RESET).
        // Do not wait on clk — gated lockstep deadlocks before the first quantum.
        // Only when pysocket_sync is connected; otherwise no partner releases rst_n.
        // Free-run / non-socket: assert, hold, then release.
        if (socketSyncLockstepActive()) {
            rst_n.write(socketSyncRstN());
            while (true) {
                wait(socketSyncRstNEvent());
                rst_n.write(socketSyncRstN());
            }
        } else {
            rst_n.write(false);
            wait(5, SC_NS);
            rst_n.write(true);
        }
    }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // IP_HDL_SC_WRAPPER_H_
