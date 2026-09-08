#ifndef PRODUCER_HDL_SC_WRAPPER_H_
#define PRODUCER_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import simple_producer.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "producer_hdl_sv_wrapper.h"
#else
#include "Vproducer_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import simple;
using namespace simple_ns;
#include "push_ack_bfm.h"

#include "socketSync.h"
class producer_hdl_sc_wrapper: public sc_module, public blockBase, public producerBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    producer_hdl_sv_wrapper *dut_hdl;
#else
    Vproducer_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    push_ack_src_bfm<tag_st, sc_bv<5>> tag0_bfm;
    push_ack_src_bfm<tag_st, sc_bv<5>> tag1_bfm;

    SC_HAS_PROCESS (producer_hdl_sc_wrapper);

    producer_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("producer_hdl_sc_wrapper", name(), bbMode),
        producerBase(name(), variant),
        clk("clk"),
        tag0_bfm("tag0_bfm"),
        tag1_bfm("tag1_bfm"),
        rst_n("rst_n", true),
        clk_half_(sc_time(1, SC_NS) / 2)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new producer_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new Vproducer_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->tag0_push(tag0_hdl_if.push);
        dut_hdl->tag0_data(tag0_hdl_if.data);
        dut_hdl->tag0_ack(tag0_hdl_if.ack);
        dut_hdl->tag1_push(tag1_hdl_if.push);
        dut_hdl->tag1_data(tag1_hdl_if.data);
        dut_hdl->tag1_ack(tag1_hdl_if.ack);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        tag0_bfm.if_p(this->tag0);
        tag0_bfm.hdl_if_p(tag0_hdl_if);
        tag0_bfm.clk(clk);
        tag0_bfm.rst_n(rst_n);

        tag1_bfm.if_p(this->tag1);
        tag1_bfm.hdl_if_p(tag1_hdl_if);
        tag1_bfm.clk(clk);
        tag1_bfm.rst_n(rst_n);

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

    push_ack_hdl_if<sc_bv<5>> tag0_hdl_if;
    push_ack_hdl_if<sc_bv<5>> tag1_hdl_if;

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

#endif // PRODUCER_HDL_SC_WRAPPER_H_
