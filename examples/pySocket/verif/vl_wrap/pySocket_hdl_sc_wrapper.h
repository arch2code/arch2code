#ifndef PYSOCKET_HDL_SC_WRAPPER_H_
#define PYSOCKET_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
#include "systemc.h"
#include "blockBase.h"
import pySocket.base;

// A non-templated wrapper names its RTL top concretely, so it includes the
// simulator's DUT header directly.
#if defined(VCS_DUT)
#include "pySocket_hdl_sv_wrapper.h"
#elif defined(XCELIUM_DUT)
#include "pySocket_hdl_sv_wrapper_xcelium.h"
#else
#include "VpySocket_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#ifdef VERILATOR
#include "verilated_vcd_c.h"
#endif
import pySocket_tb;
using namespace pySocket_tb_ns;
#include "axi4_stream_bfm.h"
#include "notify_ack_bfm.h"
#include "pop_ack_bfm.h"
#include "push_ack_bfm.h"
#include "rdy_vld_bfm.h"
#include "req_ack_bfm.h"

#include "socketSync.h"
class pySocket_hdl_sc_wrapper: public sc_module, public blockBase, public pySocketBase {

public:

#if defined(VCS_DUT) || defined(XCELIUM_DUT)
    pySocket_hdl_sv_wrapper *dut_hdl;
#else
    VpySocket_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    req_ack_src_bfm<p2s_message_st, p2s_response_st, sc_bv<64>, sc_bv<32>> test_req_ack_bfm_inst;
    req_ack_src_bfm<p2s_message_st, p2s_response_st, sc_bv<64>, sc_bv<32>> test2Python_req_ack_bfm_inst;
    req_ack_dst_bfm<p2s_message_st, p2s_response_st, sc_bv<64>, sc_bv<32>> dut2Python_req_ack_bfm_inst;
    push_ack_src_bfm<p2s_message_st, sc_bv<64>> test_push_ack_bfm_inst;
    pop_ack_src_bfm<p2s_response_st, sc_bv<32>> test_pop_ack_bfm_inst;
    push_ack_dst_bfm<p2s_message_st, sc_bv<64>> dut2Python_push_ack_bfm_inst;
    pop_ack_dst_bfm<p2s_response_st, sc_bv<32>> dut2Python_pop_ack_bfm_inst;
    notify_ack_src_bfm<> test_notify_ack_bfm_inst;
    notify_ack_dst_bfm<> dut2Python_notify_ack_bfm_inst;
    rdy_vld_src_bfm<p2s_message_st, sc_bv<64>> test_rdy_vld_bfm_inst;
    rdy_vld_dst_bfm<p2s_message_st, sc_bv<64>> dut2Python_rdy_vld_bfm_inst;
    axi4_stream_src_bfm<p2s_message_st, axis_tid_st, axis_tdest_st, sc_bv<64>, sc_bv<8>, sc_bv<8>, sc_bv<8>, sc_bv<8>, bool> test_axi4_stream_bfm_inst;
    axi4_stream_dst_bfm<p2s_message_st, axis_tid_st, axis_tdest_st, sc_bv<64>, sc_bv<8>, sc_bv<8>, sc_bv<8>, sc_bv<8>, bool> dut2Python_axi4_stream_bfm_inst;

    SC_HAS_PROCESS (pySocket_hdl_sc_wrapper);

    pySocket_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("pySocket_hdl_sc_wrapper", name(), bbMode),
        pySocketBase(name(), variant),
        clk("clk"),
        test_req_ack_bfm_inst("test_req_ack_bfm_inst"),
        test2Python_req_ack_bfm_inst("test2Python_req_ack_bfm_inst"),
        dut2Python_req_ack_bfm_inst("dut2Python_req_ack_bfm_inst"),
        test_push_ack_bfm_inst("test_push_ack_bfm_inst"),
        test_pop_ack_bfm_inst("test_pop_ack_bfm_inst"),
        dut2Python_push_ack_bfm_inst("dut2Python_push_ack_bfm_inst"),
        dut2Python_pop_ack_bfm_inst("dut2Python_pop_ack_bfm_inst"),
        test_notify_ack_bfm_inst("test_notify_ack_bfm_inst"),
        dut2Python_notify_ack_bfm_inst("dut2Python_notify_ack_bfm_inst"),
        test_rdy_vld_bfm_inst("test_rdy_vld_bfm_inst"),
        dut2Python_rdy_vld_bfm_inst("dut2Python_rdy_vld_bfm_inst"),
        test_axi4_stream_bfm_inst("test_axi4_stream_bfm_inst"),
        dut2Python_axi4_stream_bfm_inst("dut2Python_axi4_stream_bfm_inst"),
        rst_n("rst_n", true),
        clk_half_(sc_time(1, SC_NS) / 2)
    {
#if defined(VCS_DUT) || defined(XCELIUM_DUT)
        dut_hdl = new pySocket_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VpySocket_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->test_req_ack_req(test_req_ack_hdl_inst.req);
        dut_hdl->test_req_ack_data(test_req_ack_hdl_inst.data);
        dut_hdl->test_req_ack_ack(test_req_ack_hdl_inst.ack);
        dut_hdl->test_req_ack_rdata(test_req_ack_hdl_inst.rdata);
        dut_hdl->test2Python_req_ack_req(test2Python_req_ack_hdl_inst.req);
        dut_hdl->test2Python_req_ack_data(test2Python_req_ack_hdl_inst.data);
        dut_hdl->test2Python_req_ack_ack(test2Python_req_ack_hdl_inst.ack);
        dut_hdl->test2Python_req_ack_rdata(test2Python_req_ack_hdl_inst.rdata);
        dut_hdl->dut2Python_req_ack_req(dut2Python_req_ack_hdl_inst.req);
        dut_hdl->dut2Python_req_ack_data(dut2Python_req_ack_hdl_inst.data);
        dut_hdl->dut2Python_req_ack_ack(dut2Python_req_ack_hdl_inst.ack);
        dut_hdl->dut2Python_req_ack_rdata(dut2Python_req_ack_hdl_inst.rdata);
        dut_hdl->test_push_ack_push(test_push_ack_hdl_inst.push);
        dut_hdl->test_push_ack_data(test_push_ack_hdl_inst.data);
        dut_hdl->test_push_ack_ack(test_push_ack_hdl_inst.ack);
        dut_hdl->test_pop_ack_pop(test_pop_ack_hdl_inst.pop);
        dut_hdl->test_pop_ack_ack(test_pop_ack_hdl_inst.ack);
        dut_hdl->test_pop_ack_rdata(test_pop_ack_hdl_inst.rdata);
        dut_hdl->dut2Python_push_ack_push(dut2Python_push_ack_hdl_inst.push);
        dut_hdl->dut2Python_push_ack_data(dut2Python_push_ack_hdl_inst.data);
        dut_hdl->dut2Python_push_ack_ack(dut2Python_push_ack_hdl_inst.ack);
        dut_hdl->dut2Python_pop_ack_pop(dut2Python_pop_ack_hdl_inst.pop);
        dut_hdl->dut2Python_pop_ack_ack(dut2Python_pop_ack_hdl_inst.ack);
        dut_hdl->dut2Python_pop_ack_rdata(dut2Python_pop_ack_hdl_inst.rdata);
        dut_hdl->test_notify_ack_notify(test_notify_ack_hdl_inst.notify);
        dut_hdl->test_notify_ack_ack(test_notify_ack_hdl_inst.ack);
        dut_hdl->dut2Python_notify_ack_notify(dut2Python_notify_ack_hdl_inst.notify);
        dut_hdl->dut2Python_notify_ack_ack(dut2Python_notify_ack_hdl_inst.ack);
        dut_hdl->test_rdy_vld_vld(test_rdy_vld_hdl_inst.vld);
        dut_hdl->test_rdy_vld_data(test_rdy_vld_hdl_inst.data);
        dut_hdl->test_rdy_vld_rdy(test_rdy_vld_hdl_inst.rdy);
        dut_hdl->dut2Python_rdy_vld_vld(dut2Python_rdy_vld_hdl_inst.vld);
        dut_hdl->dut2Python_rdy_vld_data(dut2Python_rdy_vld_hdl_inst.data);
        dut_hdl->dut2Python_rdy_vld_rdy(dut2Python_rdy_vld_hdl_inst.rdy);
        dut_hdl->test_axi4_stream_tvalid(test_axi4_stream_hdl_inst.tvalid);
        dut_hdl->test_axi4_stream_tready(test_axi4_stream_hdl_inst.tready);
        dut_hdl->test_axi4_stream_tdata(test_axi4_stream_hdl_inst.tdata);
        dut_hdl->test_axi4_stream_tstrb(test_axi4_stream_hdl_inst.tstrb);
        dut_hdl->test_axi4_stream_tkeep(test_axi4_stream_hdl_inst.tkeep);
        dut_hdl->test_axi4_stream_tlast(test_axi4_stream_hdl_inst.tlast);
        dut_hdl->test_axi4_stream_tid(test_axi4_stream_hdl_inst.tid);
        dut_hdl->test_axi4_stream_tdest(test_axi4_stream_hdl_inst.tdest);
        dut_hdl->test_axi4_stream_tuser(test_axi4_stream_hdl_inst.tuser);
        dut_hdl->dut2Python_axi4_stream_tvalid(dut2Python_axi4_stream_hdl_inst.tvalid);
        dut_hdl->dut2Python_axi4_stream_tready(dut2Python_axi4_stream_hdl_inst.tready);
        dut_hdl->dut2Python_axi4_stream_tdata(dut2Python_axi4_stream_hdl_inst.tdata);
        dut_hdl->dut2Python_axi4_stream_tstrb(dut2Python_axi4_stream_hdl_inst.tstrb);
        dut_hdl->dut2Python_axi4_stream_tkeep(dut2Python_axi4_stream_hdl_inst.tkeep);
        dut_hdl->dut2Python_axi4_stream_tlast(dut2Python_axi4_stream_hdl_inst.tlast);
        dut_hdl->dut2Python_axi4_stream_tid(dut2Python_axi4_stream_hdl_inst.tid);
        dut_hdl->dut2Python_axi4_stream_tdest(dut2Python_axi4_stream_hdl_inst.tdest);
        dut_hdl->dut2Python_axi4_stream_tuser(dut2Python_axi4_stream_hdl_inst.tuser);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        test_req_ack_bfm_inst.if_p(this->test_req_ack);
        test_req_ack_bfm_inst.hdl_if_p(test_req_ack_hdl_inst);
        test_req_ack_bfm_inst.clk(clk);
        test_req_ack_bfm_inst.rst_n(rst_n);

        test2Python_req_ack_bfm_inst.if_p(this->test2Python_req_ack);
        test2Python_req_ack_bfm_inst.hdl_if_p(test2Python_req_ack_hdl_inst);
        test2Python_req_ack_bfm_inst.clk(clk);
        test2Python_req_ack_bfm_inst.rst_n(rst_n);

        dut2Python_req_ack_bfm_inst.if_p(this->dut2Python_req_ack);
        dut2Python_req_ack_bfm_inst.hdl_if_p(dut2Python_req_ack_hdl_inst);
        dut2Python_req_ack_bfm_inst.clk(clk);
        dut2Python_req_ack_bfm_inst.rst_n(rst_n);

        test_push_ack_bfm_inst.if_p(this->test_push_ack);
        test_push_ack_bfm_inst.hdl_if_p(test_push_ack_hdl_inst);
        test_push_ack_bfm_inst.clk(clk);
        test_push_ack_bfm_inst.rst_n(rst_n);

        test_pop_ack_bfm_inst.if_p(this->test_pop_ack);
        test_pop_ack_bfm_inst.hdl_if_p(test_pop_ack_hdl_inst);
        test_pop_ack_bfm_inst.clk(clk);
        test_pop_ack_bfm_inst.rst_n(rst_n);

        dut2Python_push_ack_bfm_inst.if_p(this->dut2Python_push_ack);
        dut2Python_push_ack_bfm_inst.hdl_if_p(dut2Python_push_ack_hdl_inst);
        dut2Python_push_ack_bfm_inst.clk(clk);
        dut2Python_push_ack_bfm_inst.rst_n(rst_n);

        dut2Python_pop_ack_bfm_inst.if_p(this->dut2Python_pop_ack);
        dut2Python_pop_ack_bfm_inst.hdl_if_p(dut2Python_pop_ack_hdl_inst);
        dut2Python_pop_ack_bfm_inst.clk(clk);
        dut2Python_pop_ack_bfm_inst.rst_n(rst_n);

        test_notify_ack_bfm_inst.if_p(this->test_notify_ack);
        test_notify_ack_bfm_inst.hdl_if_p(test_notify_ack_hdl_inst);
        test_notify_ack_bfm_inst.clk(clk);
        test_notify_ack_bfm_inst.rst_n(rst_n);

        dut2Python_notify_ack_bfm_inst.if_p(this->dut2Python_notify_ack);
        dut2Python_notify_ack_bfm_inst.hdl_if_p(dut2Python_notify_ack_hdl_inst);
        dut2Python_notify_ack_bfm_inst.clk(clk);
        dut2Python_notify_ack_bfm_inst.rst_n(rst_n);

        test_rdy_vld_bfm_inst.if_p(this->test_rdy_vld);
        test_rdy_vld_bfm_inst.hdl_if_p(test_rdy_vld_hdl_inst);
        test_rdy_vld_bfm_inst.clk(clk);
        test_rdy_vld_bfm_inst.rst_n(rst_n);

        dut2Python_rdy_vld_bfm_inst.if_p(this->dut2Python_rdy_vld);
        dut2Python_rdy_vld_bfm_inst.hdl_if_p(dut2Python_rdy_vld_hdl_inst);
        dut2Python_rdy_vld_bfm_inst.clk(clk);
        dut2Python_rdy_vld_bfm_inst.rst_n(rst_n);

        test_axi4_stream_bfm_inst.if_p(this->test_axi4_stream);
        test_axi4_stream_bfm_inst.hdl_if_p(test_axi4_stream_hdl_inst);
        test_axi4_stream_bfm_inst.clk(clk);
        test_axi4_stream_bfm_inst.rst_n(rst_n);

        dut2Python_axi4_stream_bfm_inst.if_p(this->dut2Python_axi4_stream);
        dut2Python_axi4_stream_bfm_inst.hdl_if_p(dut2Python_axi4_stream_hdl_inst);
        dut2Python_axi4_stream_bfm_inst.clk(clk);
        dut2Python_axi4_stream_bfm_inst.rst_n(rst_n);

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

    req_ack_hdl_if<sc_bv<64>, sc_bv<32>> test_req_ack_hdl_inst;
    req_ack_hdl_if<sc_bv<64>, sc_bv<32>> test2Python_req_ack_hdl_inst;
    req_ack_hdl_if<sc_bv<64>, sc_bv<32>> dut2Python_req_ack_hdl_inst;
    push_ack_hdl_if<sc_bv<64>> test_push_ack_hdl_inst;
    pop_ack_hdl_if<sc_bv<32>> test_pop_ack_hdl_inst;
    push_ack_hdl_if<sc_bv<64>> dut2Python_push_ack_hdl_inst;
    pop_ack_hdl_if<sc_bv<32>> dut2Python_pop_ack_hdl_inst;
    notify_ack_hdl_if<> test_notify_ack_hdl_inst;
    notify_ack_hdl_if<> dut2Python_notify_ack_hdl_inst;
    rdy_vld_hdl_if<sc_bv<64>> test_rdy_vld_hdl_inst;
    rdy_vld_hdl_if<sc_bv<64>> dut2Python_rdy_vld_hdl_inst;
    axi4_stream_hdl_if<sc_bv<64>, sc_bv<8>, sc_bv<8>, sc_bv<8>, sc_bv<8>> test_axi4_stream_hdl_inst;
    axi4_stream_hdl_if<sc_bv<64>, sc_bv<8>, sc_bv<8>, sc_bv<8>, sc_bv<8>> dut2Python_axi4_stream_hdl_inst;

    sc_signal<bool> rst_n;
    sc_time clk_half_;

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

    void clock_gen_clk() { clock_gen(clk, clk_half_); }
    void reset_driver_rst_n() { reset_driver(rst_n, clk, 3); }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // PYSOCKET_HDL_SC_WRAPPER_H_
