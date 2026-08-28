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
        clk_half_(0.5, SC_NS)
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

    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_uBlockA_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_uBlockB_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_hdl_if;

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

#endif // APBDECODE_HDL_SC_WRAPPER_H_
