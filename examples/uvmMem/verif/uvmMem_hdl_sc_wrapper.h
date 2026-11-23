#ifndef UVMMEM_HDL_SC_WRAPPER_H_
#define UVMMEM_HDL_SC_WRAPPER_H_

// GENERATED_CODE_PARAM --block=uvmMem
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
#include "systemc.h"
#include "blockBase.h"
import uvmMem.base;

// A non-templated wrapper names its RTL top concretely, so it includes the
// simulator's DUT header directly.
#if defined(VCS_DUT)
#include "uvmMem_hdl_sv_wrapper.h"
#elif defined(XCELIUM_DUT)
#include "uvmMem_hdl_sv_wrapper_xcelium.h"
#else
#include "VuvmMem_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#ifdef VERILATOR
#include "verilated_vcd_c.h"
#endif
import uvmMem;
using namespace uvmMem_ns;
#include "memory_bfm.h"
#include "rdy_vld_bfm.h"

#include "socketSync.h"
class uvmMem_hdl_sc_wrapper: public sc_module, public blockBase, public uvmMemBase {

public:

#if defined(VCS_DUT) || defined(XCELIUM_DUT)
    uvmMem_hdl_sv_wrapper *dut_hdl;
#else
    VuvmMem_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    rdy_vld_dst_bfm<uvmMemCmdSt, sc_bv<40>> cmd_bfm_inst;
    rdy_vld_src_bfm<uvmMemWordSt, sc_bv<32>> out_bfm_inst;
    memory_src_bfm<uvmMemAddrSt, uvmMemWordSt, sc_bv<4>, sc_bv<32>> wr_bfm_inst;
    memory_src_bfm<uvmMemAddrSt, uvmMemWordSt, sc_bv<4>, sc_bv<32>> rd_bfm_inst;

    SC_HAS_PROCESS (uvmMem_hdl_sc_wrapper);

    uvmMem_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("uvmMem_hdl_sc_wrapper", name(), bbMode),
        uvmMemBase(name(), variant),
        clk("clk"),
        cmd_bfm_inst("cmd_bfm_inst"),
        out_bfm_inst("out_bfm_inst"),
        wr_bfm_inst("wr_bfm_inst"),
        rd_bfm_inst("rd_bfm_inst"),
        rst_n("rst_n", true),
        clk_half_(sc_time(1, SC_NS) / 2)
    {
#if defined(VCS_DUT) || defined(XCELIUM_DUT)
        dut_hdl = new uvmMem_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VuvmMem_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->cmd_vld(cmd_hdl_inst.vld);
        dut_hdl->cmd_data(cmd_hdl_inst.data);
        dut_hdl->cmd_rdy(cmd_hdl_inst.rdy);
        dut_hdl->out_vld(out_hdl_inst.vld);
        dut_hdl->out_data(out_hdl_inst.data);
        dut_hdl->out_rdy(out_hdl_inst.rdy);
        dut_hdl->wr_write_data(wr_hdl_inst.write_data);
        dut_hdl->wr_read_data(wr_hdl_inst.read_data);
        dut_hdl->wr_addr(wr_hdl_inst.addr);
        dut_hdl->wr_enable(wr_hdl_inst.enable);
        dut_hdl->wr_wr_en(wr_hdl_inst.wr_en);
        dut_hdl->rd_write_data(rd_hdl_inst.write_data);
        dut_hdl->rd_read_data(rd_hdl_inst.read_data);
        dut_hdl->rd_addr(rd_hdl_inst.addr);
        dut_hdl->rd_enable(rd_hdl_inst.enable);
        dut_hdl->rd_wr_en(rd_hdl_inst.wr_en);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        cmd_bfm_inst.if_p(this->cmd);
        cmd_bfm_inst.hdl_if_p(cmd_hdl_inst);
        cmd_bfm_inst.clk(clk);
        cmd_bfm_inst.rst_n(rst_n);

        out_bfm_inst.if_p(this->out);
        out_bfm_inst.hdl_if_p(out_hdl_inst);
        out_bfm_inst.clk(clk);
        out_bfm_inst.rst_n(rst_n);

        wr_bfm_inst.if_p(this->wr);
        wr_bfm_inst.hdl_if_p(wr_hdl_inst);
        wr_bfm_inst.clk(clk);
        wr_bfm_inst.rst_n(rst_n);

        rd_bfm_inst.if_p(this->rd);
        rd_bfm_inst.hdl_if_p(rd_hdl_inst);
        rd_bfm_inst.clk(clk);
        rd_bfm_inst.rst_n(rst_n);

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

    rdy_vld_hdl_if<sc_bv<40>> cmd_hdl_inst;
    rdy_vld_hdl_if<sc_bv<32>> out_hdl_inst;
    memory_hdl_if<sc_bv<4>, sc_bv<32>> wr_hdl_inst;
    memory_hdl_if<sc_bv<4>, sc_bv<32>> rd_hdl_inst;

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

#endif // UVMMEM_HDL_SC_WRAPPER_H_
