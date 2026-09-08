#ifndef APBDECODE_HDL_SC_WRAPPER_H_
#define APBDECODE_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import apbDecode.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "apbDecode_hdl_sv_wrapper.h"
#else
#include "VapbDecode_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import apbDecode;
using namespace apbDecode_ns;
#include "apb_bfm.h"

#include "socketSync.h"
class apbDecode_hdl_sc_wrapper: public sc_module, public blockBase, public apbDecodeBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    apbDecode_hdl_sv_wrapper *dut_hdl;
#else
    VapbDecode_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_uBlockA_bfm;
    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_uBlockB_bfm;
    apb_dst_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_bfm;

    SC_HAS_PROCESS (apbDecode_hdl_sc_wrapper);

    apbDecode_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("apbDecode_hdl_sc_wrapper", name(), bbMode),
        apbDecodeBase(name(), variant),
        clk("clk"),
        apbReg_uBlockA_bfm("apbReg_uBlockA_bfm"),
        apbReg_uBlockB_bfm("apbReg_uBlockB_bfm"),
        apbReg_bfm("apbReg_bfm"),
        rst_n("rst_n", true),
        clk_half_(sc_time(1, SC_NS) / 2)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new apbDecode_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VapbDecode_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->apbReg_uBlockA_paddr(apbReg_uBlockA_hdl_if.paddr);
        dut_hdl->apbReg_uBlockA_psel(apbReg_uBlockA_hdl_if.psel);
        dut_hdl->apbReg_uBlockA_penable(apbReg_uBlockA_hdl_if.penable);
        dut_hdl->apbReg_uBlockA_pwrite(apbReg_uBlockA_hdl_if.pwrite);
        dut_hdl->apbReg_uBlockA_pwdata(apbReg_uBlockA_hdl_if.pwdata);
        dut_hdl->apbReg_uBlockA_pready(apbReg_uBlockA_hdl_if.pready);
        dut_hdl->apbReg_uBlockA_prdata(apbReg_uBlockA_hdl_if.prdata);
        dut_hdl->apbReg_uBlockA_pslverr(apbReg_uBlockA_hdl_if.pslverr);
        dut_hdl->apbReg_uBlockB_paddr(apbReg_uBlockB_hdl_if.paddr);
        dut_hdl->apbReg_uBlockB_psel(apbReg_uBlockB_hdl_if.psel);
        dut_hdl->apbReg_uBlockB_penable(apbReg_uBlockB_hdl_if.penable);
        dut_hdl->apbReg_uBlockB_pwrite(apbReg_uBlockB_hdl_if.pwrite);
        dut_hdl->apbReg_uBlockB_pwdata(apbReg_uBlockB_hdl_if.pwdata);
        dut_hdl->apbReg_uBlockB_pready(apbReg_uBlockB_hdl_if.pready);
        dut_hdl->apbReg_uBlockB_prdata(apbReg_uBlockB_hdl_if.prdata);
        dut_hdl->apbReg_uBlockB_pslverr(apbReg_uBlockB_hdl_if.pslverr);
        dut_hdl->apbReg_paddr(apbReg_hdl_if.paddr);
        dut_hdl->apbReg_psel(apbReg_hdl_if.psel);
        dut_hdl->apbReg_penable(apbReg_hdl_if.penable);
        dut_hdl->apbReg_pwrite(apbReg_hdl_if.pwrite);
        dut_hdl->apbReg_pwdata(apbReg_hdl_if.pwdata);
        dut_hdl->apbReg_pready(apbReg_hdl_if.pready);
        dut_hdl->apbReg_prdata(apbReg_hdl_if.prdata);
        dut_hdl->apbReg_pslverr(apbReg_hdl_if.pslverr);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        apbReg_uBlockA_bfm.if_p(this->apbReg_uBlockA);
        apbReg_uBlockA_bfm.hdl_if_p(apbReg_uBlockA_hdl_if);
        apbReg_uBlockA_bfm.clk(clk);
        apbReg_uBlockA_bfm.rst_n(rst_n);

        apbReg_uBlockB_bfm.if_p(this->apbReg_uBlockB);
        apbReg_uBlockB_bfm.hdl_if_p(apbReg_uBlockB_hdl_if);
        apbReg_uBlockB_bfm.clk(clk);
        apbReg_uBlockB_bfm.rst_n(rst_n);

        apbReg_bfm.if_p(this->apbReg);
        apbReg_bfm.hdl_if_p(apbReg_hdl_if);
        apbReg_bfm.clk(clk);
        apbReg_bfm.rst_n(rst_n);

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

    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_uBlockA_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_uBlockB_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_hdl_if;

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

#endif // APBDECODE_HDL_SC_WRAPPER_H_
