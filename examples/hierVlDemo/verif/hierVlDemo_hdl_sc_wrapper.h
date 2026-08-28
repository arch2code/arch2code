#ifndef HIERVLDEMO_HDL_SC_WRAPPER_H_
#define HIERVLDEMO_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=hierVlDemo
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import hierVlDemo.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "hierVlDemo_hdl_sv_wrapper.h"
#else
#include "VhierVlDemo_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import hierVlDemo_tb;
using namespace hierVlDemo_tb_ns;
#include "axi4_stream_bfm.h"

#include "socketSync.h"
class hierVlDemo_hdl_sc_wrapper: public sc_module, public blockBase, public hierVlDemoBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    hierVlDemo_hdl_sv_wrapper *dut_hdl;
#else
    VhierVlDemo_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    axi4_stream_dst_bfm<data_t1_t, tid_t1_t, tdest_t1_t, sc_bv<256>, sc_bv<4>, sc_bv<4>, sc_bv<32>, sc_bv<32>, sc_bv<16>, tuser_t1_t> axis4_t1_bfm;
    axi4_stream_src_bfm<data_t2_t, tid_t2_t, tdest_t2_t, sc_bv<64>, sc_bv<4>, sc_bv<4>, sc_bv<8>, sc_bv<8>, sc_bv<4>, tuser_t2_t> axis4_t2_bfm;

    SC_HAS_PROCESS (hierVlDemo_hdl_sc_wrapper);

    hierVlDemo_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("hierVlDemo_hdl_sc_wrapper", name(), bbMode),
        hierVlDemoBase(name(), variant),
        clk("clk"),
        axis4_t1_bfm("axis4_t1_bfm"),
        axis4_t2_bfm("axis4_t2_bfm"),
        rst_n("rst_n", true),
        clk_half_(0.5, SC_NS)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new hierVlDemo_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VhierVlDemo_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->axis4_t1_tvalid(axis4_t1_hdl_if.tvalid);
        dut_hdl->axis4_t1_tready(axis4_t1_hdl_if.tready);
        dut_hdl->axis4_t1_tdata(axis4_t1_hdl_if.tdata);
        dut_hdl->axis4_t1_tstrb(axis4_t1_hdl_if.tstrb);
        dut_hdl->axis4_t1_tkeep(axis4_t1_hdl_if.tkeep);
        dut_hdl->axis4_t1_tlast(axis4_t1_hdl_if.tlast);
        dut_hdl->axis4_t1_tid(axis4_t1_hdl_if.tid);
        dut_hdl->axis4_t1_tdest(axis4_t1_hdl_if.tdest);
        dut_hdl->axis4_t1_tuser(axis4_t1_hdl_if.tuser);
        dut_hdl->axis4_t2_tvalid(axis4_t2_hdl_if.tvalid);
        dut_hdl->axis4_t2_tready(axis4_t2_hdl_if.tready);
        dut_hdl->axis4_t2_tdata(axis4_t2_hdl_if.tdata);
        dut_hdl->axis4_t2_tstrb(axis4_t2_hdl_if.tstrb);
        dut_hdl->axis4_t2_tkeep(axis4_t2_hdl_if.tkeep);
        dut_hdl->axis4_t2_tlast(axis4_t2_hdl_if.tlast);
        dut_hdl->axis4_t2_tid(axis4_t2_hdl_if.tid);
        dut_hdl->axis4_t2_tdest(axis4_t2_hdl_if.tdest);
        dut_hdl->axis4_t2_tuser(axis4_t2_hdl_if.tuser);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        axis4_t1_bfm.if_p(this->axis4_t1);
        axis4_t1_bfm.hdl_if_p(axis4_t1_hdl_if);
        axis4_t1_bfm.clk(clk);
        axis4_t1_bfm.rst_n(rst_n);

        axis4_t2_bfm.if_p(this->axis4_t2);
        axis4_t2_bfm.hdl_if_p(axis4_t2_hdl_if);
        axis4_t2_bfm.clk(clk);
        axis4_t2_bfm.rst_n(rst_n);

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

    axi4_stream_hdl_if<sc_bv<256>, sc_bv<4>, sc_bv<4>, sc_bv<32>, sc_bv<32>, sc_bv<16>> axis4_t1_hdl_if;
    axi4_stream_hdl_if<sc_bv<64>, sc_bv<4>, sc_bv<4>, sc_bv<8>, sc_bv<8>, sc_bv<4>> axis4_t2_hdl_if;

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

#endif // HIERVLDEMO_HDL_SC_WRAPPER_H_
