#ifndef PYSOCKET_HDL_SC_WRAPPER_H_
#define PYSOCKET_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import pySocket.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "pySocket_hdl_sv_wrapper.h"
#else
#include "VpySocket_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import pySocket_tb;
using namespace pySocket_tb_ns;
#include "notify_ack_bfm.h"
#include "pop_ack_bfm.h"
#include "push_ack_bfm.h"
#include "rdy_vld_bfm.h"
#include "req_ack_bfm.h"

#include "socketSync.h"
class pySocket_hdl_sc_wrapper: public sc_module, public blockBase, public pySocketBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    pySocket_hdl_sv_wrapper *dut_hdl;
#else
    VpySocket_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    req_ack_src_bfm<p2s_message_st, p2s_response_st, sc_bv<64>, sc_bv<32>> test_req_ack_bfm;
    req_ack_src_bfm<p2s_message_st, p2s_response_st, sc_bv<64>, sc_bv<32>> test2Python_req_ack_bfm;
    req_ack_dst_bfm<p2s_message_st, p2s_response_st, sc_bv<64>, sc_bv<32>> dut2Python_req_ack_bfm;
    push_ack_src_bfm<p2s_message_st, sc_bv<64>> test_push_ack_bfm;
    pop_ack_src_bfm<p2s_response_st, sc_bv<32>> test_pop_ack_bfm;
    push_ack_dst_bfm<p2s_message_st, sc_bv<64>> dut2Python_push_ack_bfm;
    pop_ack_dst_bfm<p2s_response_st, sc_bv<32>> dut2Python_pop_ack_bfm;
    notify_ack_src_bfm<> test_notify_ack_bfm;
    notify_ack_dst_bfm<> dut2Python_notify_ack_bfm;
    rdy_vld_src_bfm<p2s_message_st, sc_bv<64>> test_rdy_vld_bfm;
    rdy_vld_dst_bfm<p2s_message_st, sc_bv<64>> dut2Python_rdy_vld_bfm;

    SC_HAS_PROCESS (pySocket_hdl_sc_wrapper);

    pySocket_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("pySocket_hdl_sc_wrapper", name(), bbMode),
        pySocketBase(name(), variant),
        clk("clk"),
        test_req_ack_bfm("test_req_ack_bfm"),
        test2Python_req_ack_bfm("test2Python_req_ack_bfm"),
        dut2Python_req_ack_bfm("dut2Python_req_ack_bfm"),
        test_push_ack_bfm("test_push_ack_bfm"),
        test_pop_ack_bfm("test_pop_ack_bfm"),
        dut2Python_push_ack_bfm("dut2Python_push_ack_bfm"),
        dut2Python_pop_ack_bfm("dut2Python_pop_ack_bfm"),
        test_notify_ack_bfm("test_notify_ack_bfm"),
        dut2Python_notify_ack_bfm("dut2Python_notify_ack_bfm"),
        test_rdy_vld_bfm("test_rdy_vld_bfm"),
        dut2Python_rdy_vld_bfm("dut2Python_rdy_vld_bfm"),
        rst_n("rst_n", true),
        clk_half_(0.5, SC_NS)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new pySocket_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VpySocket_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->test_req_ack_req(test_req_ack_hdl_if.req);
        dut_hdl->test_req_ack_data(test_req_ack_hdl_if.data);
        dut_hdl->test_req_ack_ack(test_req_ack_hdl_if.ack);
        dut_hdl->test_req_ack_rdata(test_req_ack_hdl_if.rdata);
        dut_hdl->test2Python_req_ack_req(test2Python_req_ack_hdl_if.req);
        dut_hdl->test2Python_req_ack_data(test2Python_req_ack_hdl_if.data);
        dut_hdl->test2Python_req_ack_ack(test2Python_req_ack_hdl_if.ack);
        dut_hdl->test2Python_req_ack_rdata(test2Python_req_ack_hdl_if.rdata);
        dut_hdl->dut2Python_req_ack_req(dut2Python_req_ack_hdl_if.req);
        dut_hdl->dut2Python_req_ack_data(dut2Python_req_ack_hdl_if.data);
        dut_hdl->dut2Python_req_ack_ack(dut2Python_req_ack_hdl_if.ack);
        dut_hdl->dut2Python_req_ack_rdata(dut2Python_req_ack_hdl_if.rdata);
        dut_hdl->test_push_ack_push(test_push_ack_hdl_if.push);
        dut_hdl->test_push_ack_data(test_push_ack_hdl_if.data);
        dut_hdl->test_push_ack_ack(test_push_ack_hdl_if.ack);
        dut_hdl->test_pop_ack_pop(test_pop_ack_hdl_if.pop);
        dut_hdl->test_pop_ack_ack(test_pop_ack_hdl_if.ack);
        dut_hdl->test_pop_ack_rdata(test_pop_ack_hdl_if.rdata);
        dut_hdl->dut2Python_push_ack_push(dut2Python_push_ack_hdl_if.push);
        dut_hdl->dut2Python_push_ack_data(dut2Python_push_ack_hdl_if.data);
        dut_hdl->dut2Python_push_ack_ack(dut2Python_push_ack_hdl_if.ack);
        dut_hdl->dut2Python_pop_ack_pop(dut2Python_pop_ack_hdl_if.pop);
        dut_hdl->dut2Python_pop_ack_ack(dut2Python_pop_ack_hdl_if.ack);
        dut_hdl->dut2Python_pop_ack_rdata(dut2Python_pop_ack_hdl_if.rdata);
        dut_hdl->test_notify_ack_notify(test_notify_ack_hdl_if.notify);
        dut_hdl->test_notify_ack_ack(test_notify_ack_hdl_if.ack);
        dut_hdl->dut2Python_notify_ack_notify(dut2Python_notify_ack_hdl_if.notify);
        dut_hdl->dut2Python_notify_ack_ack(dut2Python_notify_ack_hdl_if.ack);
        dut_hdl->test_rdy_vld_vld(test_rdy_vld_hdl_if.vld);
        dut_hdl->test_rdy_vld_data(test_rdy_vld_hdl_if.data);
        dut_hdl->test_rdy_vld_rdy(test_rdy_vld_hdl_if.rdy);
        dut_hdl->dut2Python_rdy_vld_vld(dut2Python_rdy_vld_hdl_if.vld);
        dut_hdl->dut2Python_rdy_vld_data(dut2Python_rdy_vld_hdl_if.data);
        dut_hdl->dut2Python_rdy_vld_rdy(dut2Python_rdy_vld_hdl_if.rdy);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        test_req_ack_bfm.if_p(this->test_req_ack);
        test_req_ack_bfm.hdl_if_p(test_req_ack_hdl_if);
        test_req_ack_bfm.clk(clk);
        test_req_ack_bfm.rst_n(rst_n);

        test2Python_req_ack_bfm.if_p(this->test2Python_req_ack);
        test2Python_req_ack_bfm.hdl_if_p(test2Python_req_ack_hdl_if);
        test2Python_req_ack_bfm.clk(clk);
        test2Python_req_ack_bfm.rst_n(rst_n);

        dut2Python_req_ack_bfm.if_p(this->dut2Python_req_ack);
        dut2Python_req_ack_bfm.hdl_if_p(dut2Python_req_ack_hdl_if);
        dut2Python_req_ack_bfm.clk(clk);
        dut2Python_req_ack_bfm.rst_n(rst_n);

        test_push_ack_bfm.if_p(this->test_push_ack);
        test_push_ack_bfm.hdl_if_p(test_push_ack_hdl_if);
        test_push_ack_bfm.clk(clk);
        test_push_ack_bfm.rst_n(rst_n);

        test_pop_ack_bfm.if_p(this->test_pop_ack);
        test_pop_ack_bfm.hdl_if_p(test_pop_ack_hdl_if);
        test_pop_ack_bfm.clk(clk);
        test_pop_ack_bfm.rst_n(rst_n);

        dut2Python_push_ack_bfm.if_p(this->dut2Python_push_ack);
        dut2Python_push_ack_bfm.hdl_if_p(dut2Python_push_ack_hdl_if);
        dut2Python_push_ack_bfm.clk(clk);
        dut2Python_push_ack_bfm.rst_n(rst_n);

        dut2Python_pop_ack_bfm.if_p(this->dut2Python_pop_ack);
        dut2Python_pop_ack_bfm.hdl_if_p(dut2Python_pop_ack_hdl_if);
        dut2Python_pop_ack_bfm.clk(clk);
        dut2Python_pop_ack_bfm.rst_n(rst_n);

        test_notify_ack_bfm.if_p(this->test_notify_ack);
        test_notify_ack_bfm.hdl_if_p(test_notify_ack_hdl_if);
        test_notify_ack_bfm.clk(clk);
        test_notify_ack_bfm.rst_n(rst_n);

        dut2Python_notify_ack_bfm.if_p(this->dut2Python_notify_ack);
        dut2Python_notify_ack_bfm.hdl_if_p(dut2Python_notify_ack_hdl_if);
        dut2Python_notify_ack_bfm.clk(clk);
        dut2Python_notify_ack_bfm.rst_n(rst_n);

        test_rdy_vld_bfm.if_p(this->test_rdy_vld);
        test_rdy_vld_bfm.hdl_if_p(test_rdy_vld_hdl_if);
        test_rdy_vld_bfm.clk(clk);
        test_rdy_vld_bfm.rst_n(rst_n);

        dut2Python_rdy_vld_bfm.if_p(this->dut2Python_rdy_vld);
        dut2Python_rdy_vld_bfm.hdl_if_p(dut2Python_rdy_vld_hdl_if);
        dut2Python_rdy_vld_bfm.clk(clk);
        dut2Python_rdy_vld_bfm.rst_n(rst_n);

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

    req_ack_hdl_if<sc_bv<64>, sc_bv<32>> test_req_ack_hdl_if;
    req_ack_hdl_if<sc_bv<64>, sc_bv<32>> test2Python_req_ack_hdl_if;
    req_ack_hdl_if<sc_bv<64>, sc_bv<32>> dut2Python_req_ack_hdl_if;
    push_ack_hdl_if<sc_bv<64>> test_push_ack_hdl_if;
    pop_ack_hdl_if<sc_bv<32>> test_pop_ack_hdl_if;
    push_ack_hdl_if<sc_bv<64>> dut2Python_push_ack_hdl_if;
    pop_ack_hdl_if<sc_bv<32>> dut2Python_pop_ack_hdl_if;
    notify_ack_hdl_if<> test_notify_ack_hdl_if;
    notify_ack_hdl_if<> dut2Python_notify_ack_hdl_if;
    rdy_vld_hdl_if<sc_bv<64>> test_rdy_vld_hdl_if;
    rdy_vld_hdl_if<sc_bv<64>> dut2Python_rdy_vld_hdl_if;

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

#endif // PYSOCKET_HDL_SC_WRAPPER_H_
