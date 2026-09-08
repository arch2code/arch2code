#ifndef APBDECODE_HDL_SC_WRAPPER_H_
#define APBDECODE_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import ip_test_apbDecode.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "apbDecode_hdl_sv_wrapper.h"
#else
#include "VapbDecode_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import common_shared_types;
using namespace common_shared_types_ns;
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

    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_uBridge_bfm;
    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_uIp0_bfm;
    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_uIp1_bfm;
    apb_dst_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> cpu_main_bfm;

    SC_HAS_PROCESS (apbDecode_hdl_sc_wrapper);

    apbDecode_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("apbDecode_hdl_sc_wrapper", name(), bbMode),
        apbDecodeBase(name(), variant),
        clk("clk"),
        apbReg_uBridge_bfm("apbReg_uBridge_bfm"),
        apbReg_uIp0_bfm("apbReg_uIp0_bfm"),
        apbReg_uIp1_bfm("apbReg_uIp1_bfm"),
        cpu_main_bfm("cpu_main_bfm"),
        rst_n("rst_n", true),
        clk_half_(sc_time(1, SC_NS) / 2)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new apbDecode_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VapbDecode_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->apbReg_uBridge_paddr(apbReg_uBridge_hdl_if.paddr);
        dut_hdl->apbReg_uBridge_psel(apbReg_uBridge_hdl_if.psel);
        dut_hdl->apbReg_uBridge_penable(apbReg_uBridge_hdl_if.penable);
        dut_hdl->apbReg_uBridge_pwrite(apbReg_uBridge_hdl_if.pwrite);
        dut_hdl->apbReg_uBridge_pwdata(apbReg_uBridge_hdl_if.pwdata);
        dut_hdl->apbReg_uBridge_pready(apbReg_uBridge_hdl_if.pready);
        dut_hdl->apbReg_uBridge_prdata(apbReg_uBridge_hdl_if.prdata);
        dut_hdl->apbReg_uBridge_pslverr(apbReg_uBridge_hdl_if.pslverr);
        dut_hdl->apbReg_uIp0_paddr(apbReg_uIp0_hdl_if.paddr);
        dut_hdl->apbReg_uIp0_psel(apbReg_uIp0_hdl_if.psel);
        dut_hdl->apbReg_uIp0_penable(apbReg_uIp0_hdl_if.penable);
        dut_hdl->apbReg_uIp0_pwrite(apbReg_uIp0_hdl_if.pwrite);
        dut_hdl->apbReg_uIp0_pwdata(apbReg_uIp0_hdl_if.pwdata);
        dut_hdl->apbReg_uIp0_pready(apbReg_uIp0_hdl_if.pready);
        dut_hdl->apbReg_uIp0_prdata(apbReg_uIp0_hdl_if.prdata);
        dut_hdl->apbReg_uIp0_pslverr(apbReg_uIp0_hdl_if.pslverr);
        dut_hdl->apbReg_uIp1_paddr(apbReg_uIp1_hdl_if.paddr);
        dut_hdl->apbReg_uIp1_psel(apbReg_uIp1_hdl_if.psel);
        dut_hdl->apbReg_uIp1_penable(apbReg_uIp1_hdl_if.penable);
        dut_hdl->apbReg_uIp1_pwrite(apbReg_uIp1_hdl_if.pwrite);
        dut_hdl->apbReg_uIp1_pwdata(apbReg_uIp1_hdl_if.pwdata);
        dut_hdl->apbReg_uIp1_pready(apbReg_uIp1_hdl_if.pready);
        dut_hdl->apbReg_uIp1_prdata(apbReg_uIp1_hdl_if.prdata);
        dut_hdl->apbReg_uIp1_pslverr(apbReg_uIp1_hdl_if.pslverr);
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

        apbReg_uBridge_bfm.if_p(this->apbReg_uBridge);
        apbReg_uBridge_bfm.hdl_if_p(apbReg_uBridge_hdl_if);
        apbReg_uBridge_bfm.clk(clk);
        apbReg_uBridge_bfm.rst_n(rst_n);

        apbReg_uIp0_bfm.if_p(this->apbReg_uIp0);
        apbReg_uIp0_bfm.hdl_if_p(apbReg_uIp0_hdl_if);
        apbReg_uIp0_bfm.clk(clk);
        apbReg_uIp0_bfm.rst_n(rst_n);

        apbReg_uIp1_bfm.if_p(this->apbReg_uIp1);
        apbReg_uIp1_bfm.hdl_if_p(apbReg_uIp1_hdl_if);
        apbReg_uIp1_bfm.clk(clk);
        apbReg_uIp1_bfm.rst_n(rst_n);

        cpu_main_bfm.if_p(this->cpu_main);
        cpu_main_bfm.hdl_if_p(cpu_main_hdl_if);
        cpu_main_bfm.clk(clk);
        cpu_main_bfm.rst_n(rst_n);

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

    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_uBridge_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_uIp0_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_uIp1_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> cpu_main_hdl_if;

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
