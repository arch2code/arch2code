#ifndef TWOCLKDECODE_HDL_SC_WRAPPER_H_
#define TWOCLKDECODE_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=twoClkDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
#include "systemc.h"
#include "blockBase.h"
import twoClk_twoClkDecode.base;

// A non-templated wrapper names its RTL top concretely, so it includes the
// simulator's DUT header directly.
#if defined(VCS_DUT)
#include "twoClkDecode_hdl_sv_wrapper.h"
#elif defined(XCELIUM_DUT)
#include "twoClkDecode_hdl_sv_wrapper_xcelium.h"
#else
#include "VtwoClkDecode_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#ifdef VERILATOR
#include "verilated_vcd_c.h"
#endif
import twoClk;
using namespace twoClk_ns;
#include "apb_bfm.h"

#include "socketSync.h"
class twoClkDecode_hdl_sc_wrapper: public sc_module, public blockBase, public twoClkDecodeBase {

public:

#if defined(VCS_DUT) || defined(XCELIUM_DUT)
    twoClkDecode_hdl_sv_wrapper *dut_hdl;
#else
    VtwoClkDecode_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    apb_src_bfm<twoClkRegAddrSt, twoClkRegDataSt, sc_bv<32>, sc_bv<32>> twoClkReg_uTable_bfm_inst;
    apb_dst_bfm<twoClkRegAddrSt, twoClkRegDataSt, sc_bv<32>, sc_bv<32>> twoClkReg_bfm_inst;

    SC_HAS_PROCESS (twoClkDecode_hdl_sc_wrapper);

    twoClkDecode_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("twoClkDecode_hdl_sc_wrapper", name(), bbMode),
        twoClkDecodeBase(name(), variant),
        clk("clk"),
        twoClkReg_uTable_bfm_inst("twoClkReg_uTable_bfm_inst"),
        twoClkReg_bfm_inst("twoClkReg_bfm_inst"),
        rst_n("rst_n", true),
        clk_half_(sc_time(1, SC_NS) / 2)
    {
#if defined(VCS_DUT) || defined(XCELIUM_DUT)
        dut_hdl = new twoClkDecode_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VtwoClkDecode_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->twoClkReg_uTable_paddr(twoClkReg_uTable_hdl_inst.paddr);
        dut_hdl->twoClkReg_uTable_psel(twoClkReg_uTable_hdl_inst.psel);
        dut_hdl->twoClkReg_uTable_penable(twoClkReg_uTable_hdl_inst.penable);
        dut_hdl->twoClkReg_uTable_pwrite(twoClkReg_uTable_hdl_inst.pwrite);
        dut_hdl->twoClkReg_uTable_pwdata(twoClkReg_uTable_hdl_inst.pwdata);
        dut_hdl->twoClkReg_uTable_pready(twoClkReg_uTable_hdl_inst.pready);
        dut_hdl->twoClkReg_uTable_prdata(twoClkReg_uTable_hdl_inst.prdata);
        dut_hdl->twoClkReg_uTable_pslverr(twoClkReg_uTable_hdl_inst.pslverr);
        dut_hdl->twoClkReg_paddr(twoClkReg_hdl_inst.paddr);
        dut_hdl->twoClkReg_psel(twoClkReg_hdl_inst.psel);
        dut_hdl->twoClkReg_penable(twoClkReg_hdl_inst.penable);
        dut_hdl->twoClkReg_pwrite(twoClkReg_hdl_inst.pwrite);
        dut_hdl->twoClkReg_pwdata(twoClkReg_hdl_inst.pwdata);
        dut_hdl->twoClkReg_pready(twoClkReg_hdl_inst.pready);
        dut_hdl->twoClkReg_prdata(twoClkReg_hdl_inst.prdata);
        dut_hdl->twoClkReg_pslverr(twoClkReg_hdl_inst.pslverr);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        twoClkReg_uTable_bfm_inst.if_p(this->twoClkReg_uTable);
        twoClkReg_uTable_bfm_inst.hdl_if_p(twoClkReg_uTable_hdl_inst);
        twoClkReg_uTable_bfm_inst.clk(clk);
        twoClkReg_uTable_bfm_inst.rst_n(rst_n);

        twoClkReg_bfm_inst.if_p(this->twoClkReg);
        twoClkReg_bfm_inst.hdl_if_p(twoClkReg_hdl_inst);
        twoClkReg_bfm_inst.clk(clk);
        twoClkReg_bfm_inst.rst_n(rst_n);

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

    apb_hdl_if<sc_bv<32>, sc_bv<32>> twoClkReg_uTable_hdl_inst;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> twoClkReg_hdl_inst;

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

#endif // TWOCLKDECODE_HDL_SC_WRAPPER_H_
