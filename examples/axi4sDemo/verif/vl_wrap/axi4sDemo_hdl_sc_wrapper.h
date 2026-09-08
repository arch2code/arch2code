#ifndef AXI4SDEMO_HDL_SC_WRAPPER_H_
#define AXI4SDEMO_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=axi4sDemo
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import axi4sDemo.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "axi4sDemo_hdl_sv_wrapper.h"
#else
#include "Vaxi4sDemo_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import axi4sDemo_tb;
using namespace axi4sDemo_tb_ns;
#include "axi4_stream_bfm.h"

#include "socketSync.h"
class axi4sDemo_hdl_sc_wrapper: public sc_module, public blockBase, public axi4sDemoBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    axi4sDemo_hdl_sv_wrapper *dut_hdl;
#else
    Vaxi4sDemo_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    axi4_stream_dst_bfm<data_t1_t, tid_t1_t, tdest_t1_t, sc_bv<256>, sc_bv<4>, sc_bv<4>, sc_bv<32>, sc_bv<32>, sc_bv<16>, tuser_t1_t> axis4_t1_bfm;
    axi4_stream_src_bfm<data_t2_t, tid_t2_t, tdest_t2_t, sc_bv<64>, sc_bv<4>, sc_bv<4>, sc_bv<8>, sc_bv<8>, sc_bv<4>, tuser_t2_t> axis4_t2_bfm;

    SC_HAS_PROCESS (axi4sDemo_hdl_sc_wrapper);

    axi4sDemo_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("axi4sDemo_hdl_sc_wrapper", name(), bbMode),
        axi4sDemoBase(name(), variant),
        clk("clk"),
        axis4_t1_bfm("axis4_t1_bfm"),
        axis4_t2_bfm("axis4_t2_bfm"),
        rst_n("rst_n", true),
        clk_half_(sc_time(1, SC_NS) / 2)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new axi4sDemo_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new Vaxi4sDemo_hdl_sv_wrapper("dut_hdl");
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
        SC_THREAD(clock_gen_clk);
        SC_THREAD(reset_driver_rst_n);

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

    void clock_gen_clk() { clock_gen(clk, clk_half_); }
    void reset_driver_rst_n() { reset_driver(rst_n, clk, 3); }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // AXI4SDEMO_HDL_SC_WRAPPER_H_
