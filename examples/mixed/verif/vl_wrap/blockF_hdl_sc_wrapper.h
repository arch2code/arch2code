#ifndef BLOCKF_HDL_SC_WRAPPER_H_
#define BLOCKF_HDL_SC_WRAPPER_H_

// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
#include "systemc.h"
#include "blockBase.h"
import mixed_blockF.base;
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#ifdef VERILATOR
#include "verilated_vcd_c.h"
#endif
import mixed_mixedBlockC;
using namespace mixed_mixedBlockC_ns;
import mixed;
using namespace mixed_ns;
import mixed.blockF.config;
#include "rdy_vld_bfm.h"
#include "status_bfm.h"

#include "socketSync.h"
template <typename DUT_T, typename Config>
class blockF_hdl_sc_wrapper: public sc_module, public blockBase, public blockFBase<Config> {

public:

    DUT_T *dut_hdl;

    sc_signal<bool> clk;

    rdy_vld_src_bfm<seeSt, sc_bv<5>> cStuffIf_bfm_inst;
    rdy_vld_dst_bfm<dSt, sc_bv<7>> dStuffIf_bfm_inst;
    rdy_vld_dst_bfm<dSt, sc_bv<7>> dSin_bfm_inst;
    rdy_vld_src_bfm<dSt, sc_bv<7>> dSout_bfm_inst;
    status_dst_bfm<dRegSt, sc_bv<7>> rwD_bfm_inst;

    // SC_HAS_PROCESS expects a single macro argument; the Config-templated
    // self type carries a comma in its argument list and must be aliased.
    using blockF_hdl_sc_wrapper_self_t = blockF_hdl_sc_wrapper<DUT_T, Config>;
    SC_HAS_PROCESS (blockF_hdl_sc_wrapper_self_t);

    blockF_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("blockF_hdl_sc_wrapper", name(), bbMode),
        blockFBase<Config>(name(), variant),
        clk("clk"),
        cStuffIf_bfm_inst("cStuffIf_bfm_inst"),
        dStuffIf_bfm_inst("dStuffIf_bfm_inst"),
        dSin_bfm_inst("dSin_bfm_inst"),
        dSout_bfm_inst("dSout_bfm_inst"),
        rwD_bfm_inst("rwD_bfm_inst"),
        rst_n("rst_n", true),
        clk_half_(0.5, SC_NS)
    {
        dut_hdl = new DUT_T("dut_hdl");

        dut_hdl->cStuffIf_vld(cStuffIf_hdl_inst.vld);
        dut_hdl->cStuffIf_data(cStuffIf_hdl_inst.data);
        dut_hdl->cStuffIf_rdy(cStuffIf_hdl_inst.rdy);
        dut_hdl->dStuffIf_vld(dStuffIf_hdl_inst.vld);
        dut_hdl->dStuffIf_data(dStuffIf_hdl_inst.data);
        dut_hdl->dStuffIf_rdy(dStuffIf_hdl_inst.rdy);
        dut_hdl->dSin_vld(dSin_hdl_inst.vld);
        dut_hdl->dSin_data(dSin_hdl_inst.data);
        dut_hdl->dSin_rdy(dSin_hdl_inst.rdy);
        dut_hdl->dSout_vld(dSout_hdl_inst.vld);
        dut_hdl->dSout_data(dSout_hdl_inst.data);
        dut_hdl->dSout_rdy(dSout_hdl_inst.rdy);
        dut_hdl->rwD_data(rwD_hdl_inst.data);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        cStuffIf_bfm_inst.if_p(this->cStuffIf);
        cStuffIf_bfm_inst.hdl_if_p(cStuffIf_hdl_inst);
        cStuffIf_bfm_inst.clk(clk);
        cStuffIf_bfm_inst.rst_n(rst_n);

        dStuffIf_bfm_inst.if_p(this->dStuffIf);
        dStuffIf_bfm_inst.hdl_if_p(dStuffIf_hdl_inst);
        dStuffIf_bfm_inst.clk(clk);
        dStuffIf_bfm_inst.rst_n(rst_n);

        dSin_bfm_inst.if_p(this->dSin);
        dSin_bfm_inst.hdl_if_p(dSin_hdl_inst);
        dSin_bfm_inst.clk(clk);
        dSin_bfm_inst.rst_n(rst_n);

        dSout_bfm_inst.if_p(this->dSout);
        dSout_bfm_inst.hdl_if_p(dSout_hdl_inst);
        dSout_bfm_inst.clk(clk);
        dSout_bfm_inst.rst_n(rst_n);

        rwD_bfm_inst.if_p(this->rwD);
        rwD_bfm_inst.hdl_if_p(rwD_hdl_inst);
        rwD_bfm_inst.clk(clk);
        rwD_bfm_inst.rst_n(rst_n);

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

    rdy_vld_hdl_if<sc_bv<5>> cStuffIf_hdl_inst;
    rdy_vld_hdl_if<sc_bv<7>> dStuffIf_hdl_inst;
    rdy_vld_hdl_if<sc_bv<7>> dSin_hdl_inst;
    rdy_vld_hdl_if<sc_bv<7>> dSout_hdl_inst;
    status_hdl_if<sc_bv<7>> rwD_hdl_inst;

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

#endif // BLOCKF_HDL_SC_WRAPPER_H_
