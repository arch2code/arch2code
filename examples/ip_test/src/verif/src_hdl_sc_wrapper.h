#ifndef SRC_HDL_SC_WRAPPER_H_
#define SRC_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=src
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import ip_test_src.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#ifdef VERILATOR
#include "verilated_vcd_c.h"
#endif
import ip_test_src;
using namespace ip_test_src_ns;
import ip_test_ipLeaf;
using namespace ip_test_ipLeaf_ns;
#include "ipLeafVariantConfig.h"
#include "srcVariantConfig.h"
#include "push_ack_bfm.h"

#include "socketSync.h"
template <typename DUT_T, typename Config>
class src_hdl_sc_wrapper: public sc_module, public blockBase, public srcBase<Config> {

public:

    DUT_T *dut_hdl;

    sc_signal<bool> clk;

    push_ack_src_bfm<srcOut0St<Config>, sc_bv<srcOut0St<Config>::_bitWidth>> out0_bfm;
    push_ack_src_bfm<srcOut1St<Config>, sc_bv<srcOut1St<Config>::_bitWidth>> out1_bfm;
    push_ack_src_bfm<srcOut0St<Config>, sc_bv<srcOut0St<Config>::_bitWidth>> out2_bfm;
    push_ack_src_bfm<srcOut1St<Config>, sc_bv<srcOut1St<Config>::_bitWidth>> out3_bfm;

    // SC_HAS_PROCESS expects a single macro argument; the Config-templated
    // self type carries a comma in its argument list and must be aliased.
    using src_hdl_sc_wrapper_self_t = src_hdl_sc_wrapper<DUT_T, Config>;
    SC_HAS_PROCESS (src_hdl_sc_wrapper_self_t);

    src_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("src_hdl_sc_wrapper", name(), bbMode),
        srcBase<Config>(name(), variant),
        clk("clk"),
        out0_bfm("out0_bfm"),
        out1_bfm("out1_bfm"),
        out2_bfm("out2_bfm"),
        out3_bfm("out3_bfm"),
        rst_n("rst_n", true),
        clk_half_(0.5, SC_NS)
    {
        dut_hdl = new DUT_T("dut_hdl");

        dut_hdl->out0_push(out0_hdl_if.push);
        dut_hdl->out0_data(out0_hdl_if.data);
        dut_hdl->out0_ack(out0_hdl_if.ack);
        dut_hdl->out1_push(out1_hdl_if.push);
        dut_hdl->out1_data(out1_hdl_if.data);
        dut_hdl->out1_ack(out1_hdl_if.ack);
        dut_hdl->out2_push(out2_hdl_if.push);
        dut_hdl->out2_data(out2_hdl_if.data);
        dut_hdl->out2_ack(out2_hdl_if.ack);
        dut_hdl->out3_push(out3_hdl_if.push);
        dut_hdl->out3_data(out3_hdl_if.data);
        dut_hdl->out3_ack(out3_hdl_if.ack);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        out0_bfm.if_p(this->out0);
        out0_bfm.hdl_if_p(out0_hdl_if);
        out0_bfm.clk(clk);
        out0_bfm.rst_n(rst_n);

        out1_bfm.if_p(this->out1);
        out1_bfm.hdl_if_p(out1_hdl_if);
        out1_bfm.clk(clk);
        out1_bfm.rst_n(rst_n);

        out2_bfm.if_p(this->out2);
        out2_bfm.hdl_if_p(out2_hdl_if);
        out2_bfm.clk(clk);
        out2_bfm.rst_n(rst_n);

        out3_bfm.if_p(this->out3);
        out3_bfm.hdl_if_p(out3_hdl_if);
        out3_bfm.clk(clk);
        out3_bfm.rst_n(rst_n);

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

    push_ack_hdl_if<sc_bv<srcOut0St<Config>::_bitWidth>> out0_hdl_if;
    push_ack_hdl_if<sc_bv<srcOut1St<Config>::_bitWidth>> out1_hdl_if;
    push_ack_hdl_if<sc_bv<srcOut0St<Config>::_bitWidth>> out2_hdl_if;
    push_ack_hdl_if<sc_bv<srcOut1St<Config>::_bitWidth>> out3_hdl_if;

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

#endif // SRC_HDL_SC_WRAPPER_H_
