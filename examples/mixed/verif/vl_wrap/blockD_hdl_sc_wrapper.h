#ifndef BLOCKD_HDL_SC_WRAPPER_H_
#define BLOCKD_HDL_SC_WRAPPER_H_

// GENERATED_CODE_PARAM --block=blockD
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
#include "systemc.h"
#include "blockBase.h"
import mixed_blockD.base;

// A non-templated wrapper names its RTL top concretely, so it includes the
// simulator's DUT header directly.
#if defined(VCS_DUT)
#include "blockD_hdl_sv_wrapper.h"
#elif defined(XCELIUM_DUT)
#include "blockD_hdl_sv_wrapper_xcelium.h"
#else
#include "VblockD_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#ifdef VERILATOR
#include "verilated_vcd_c.h"
#endif
import mixed;
using namespace mixed_ns;
import mixed_mixedBlockC;
using namespace mixed_mixedBlockC_ns;
import mixed_mixedInclude;
using namespace mixed_mixedInclude_ns;
#include "external_reg_bfm.h"
#include "memory_bfm.h"
#include "rdy_vld_bfm.h"
#include "req_ack_bfm.h"
#include "status_bfm.h"

#include "socketSync.h"
class blockD_hdl_sc_wrapper: public sc_module, public blockBase, public blockDBase {

public:

#if defined(VCS_DUT) || defined(XCELIUM_DUT)
    blockD_hdl_sv_wrapper *dut_hdl;
#else
    VblockD_hdl_sv_wrapper *dut_hdl;
#endif

    sc_signal<bool> clk;

    rdy_vld_src_bfm<seeSt, sc_bv<5>> cStuffIf_bfm_inst;
    rdy_vld_src_bfm<dSt, sc_bv<7>> dee0_bfm_inst;
    rdy_vld_src_bfm<dSt, sc_bv<7>> dee1_bfm_inst;
    rdy_vld_src_bfm<dSt, sc_bv<7>> outD_bfm_inst;
    rdy_vld_dst_bfm<dSt, sc_bv<7>> inD_bfm_inst;
    req_ack_dst_bfm<aSt, aASt, sc_bv<4>, bool> btod_bfm_inst;
    status_dst_bfm<dRegSt, sc_bv<7>> rwD_bfm_inst;
    status_src_bfm<bSizeRegSt, sc_bv<4>> roBsize_bfm_inst;
    memory_dst_bfm<bSizeSt, seeSt, sc_bv<4>, sc_bv<5>> blockBTableExt_bfm_inst;
    memory_dst_bfm<bSizeSt, test37BitRegSt, sc_bv<4>, sc_bv<37>> blockBTable37Bit_bfm_inst;
    status_dst_bfm<dRegSt, sc_bv<7>> rwArr_bfm_inst;
    sc_vector< external_reg_dst_bfm<dRegSt, sc_bv<7>> > extArr_bfm_inst;
    memory_src_bfm<bSizeSt, bigSt, sc_bv<4>, sc_bv<64>> blockBTable1_bfm_inst;
    memory_src_bfm<bSizeSt, nestedSt, sc_bv<4>, sc_bv<18>> blockBTableSP_bfm_inst;

    SC_HAS_PROCESS (blockD_hdl_sc_wrapper);

    blockD_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("blockD_hdl_sc_wrapper", name(), bbMode),
        blockDBase(name(), variant),
        clk("clk"),
        cStuffIf_bfm_inst("cStuffIf_bfm_inst"),
        dee0_bfm_inst("dee0_bfm_inst"),
        dee1_bfm_inst("dee1_bfm_inst"),
        outD_bfm_inst("outD_bfm_inst"),
        inD_bfm_inst("inD_bfm_inst"),
        btod_bfm_inst("btod_bfm_inst"),
        rwD_bfm_inst("rwD_bfm_inst"),
        roBsize_bfm_inst("roBsize_bfm_inst"),
        blockBTableExt_bfm_inst("blockBTableExt_bfm_inst"),
        blockBTable37Bit_bfm_inst("blockBTable37Bit_bfm_inst"),
        rwArr_bfm_inst("rwArr_bfm_inst"),
        extArr_bfm_inst("extArr_bfm_inst", REGARR_N),
        blockBTable1_bfm_inst("blockBTable1_bfm_inst"),
        blockBTableSP_bfm_inst("blockBTableSP_bfm_inst"),
        rst_n("rst_n", true),
        clk_half_(sc_time(1, SC_NS) / 2)
    {
#if defined(VCS_DUT) || defined(XCELIUM_DUT)
        dut_hdl = new blockD_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VblockD_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->cStuffIf_vld(cStuffIf_hdl_inst.vld);
        dut_hdl->cStuffIf_data(cStuffIf_hdl_inst.data);
        dut_hdl->cStuffIf_rdy(cStuffIf_hdl_inst.rdy);
        dut_hdl->dee0_vld(dee0_hdl_inst.vld);
        dut_hdl->dee0_data(dee0_hdl_inst.data);
        dut_hdl->dee0_rdy(dee0_hdl_inst.rdy);
        dut_hdl->dee1_vld(dee1_hdl_inst.vld);
        dut_hdl->dee1_data(dee1_hdl_inst.data);
        dut_hdl->dee1_rdy(dee1_hdl_inst.rdy);
        dut_hdl->outD_vld(outD_hdl_inst.vld);
        dut_hdl->outD_data(outD_hdl_inst.data);
        dut_hdl->outD_rdy(outD_hdl_inst.rdy);
        dut_hdl->inD_vld(inD_hdl_inst.vld);
        dut_hdl->inD_data(inD_hdl_inst.data);
        dut_hdl->inD_rdy(inD_hdl_inst.rdy);
        dut_hdl->btod_req(btod_hdl_inst.req);
        dut_hdl->btod_data(btod_hdl_inst.data);
        dut_hdl->btod_ack(btod_hdl_inst.ack);
        dut_hdl->btod_rdata(btod_hdl_inst.rdata);
        dut_hdl->rwD_data(rwD_hdl_inst.data);
        dut_hdl->roBsize_data(roBsize_hdl_inst.data);
        dut_hdl->blockBTableExt_write_data(blockBTableExt_hdl_inst.write_data);
        dut_hdl->blockBTableExt_read_data(blockBTableExt_hdl_inst.read_data);
        dut_hdl->blockBTableExt_addr(blockBTableExt_hdl_inst.addr);
        dut_hdl->blockBTableExt_enable(blockBTableExt_hdl_inst.enable);
        dut_hdl->blockBTableExt_wr_en(blockBTableExt_hdl_inst.wr_en);
        dut_hdl->blockBTable37Bit_write_data(blockBTable37Bit_hdl_inst.write_data);
        dut_hdl->blockBTable37Bit_read_data(blockBTable37Bit_hdl_inst.read_data);
        dut_hdl->blockBTable37Bit_addr(blockBTable37Bit_hdl_inst.addr);
        dut_hdl->blockBTable37Bit_enable(blockBTable37Bit_hdl_inst.enable);
        dut_hdl->blockBTable37Bit_wr_en(blockBTable37Bit_hdl_inst.wr_en);
        dut_hdl->rwArr_data(rwArr_hdl_inst.data);
        dut_hdl->extArr_0_wdata(extArr_hdl_inst[0].wdata);
        dut_hdl->extArr_0_rdata(extArr_hdl_inst[0].rdata);
        dut_hdl->extArr_0_write(extArr_hdl_inst[0].write);
        dut_hdl->extArr_1_wdata(extArr_hdl_inst[1].wdata);
        dut_hdl->extArr_1_rdata(extArr_hdl_inst[1].rdata);
        dut_hdl->extArr_1_write(extArr_hdl_inst[1].write);
        dut_hdl->extArr_2_wdata(extArr_hdl_inst[2].wdata);
        dut_hdl->extArr_2_rdata(extArr_hdl_inst[2].rdata);
        dut_hdl->extArr_2_write(extArr_hdl_inst[2].write);
        dut_hdl->extArr_3_wdata(extArr_hdl_inst[3].wdata);
        dut_hdl->extArr_3_rdata(extArr_hdl_inst[3].rdata);
        dut_hdl->extArr_3_write(extArr_hdl_inst[3].write);
        dut_hdl->blockBTable1_write_data(blockBTable1_hdl_inst.write_data);
        dut_hdl->blockBTable1_read_data(blockBTable1_hdl_inst.read_data);
        dut_hdl->blockBTable1_addr(blockBTable1_hdl_inst.addr);
        dut_hdl->blockBTable1_enable(blockBTable1_hdl_inst.enable);
        dut_hdl->blockBTable1_wr_en(blockBTable1_hdl_inst.wr_en);
        dut_hdl->blockBTableSP_write_data(blockBTableSP_hdl_inst.write_data);
        dut_hdl->blockBTableSP_read_data(blockBTableSP_hdl_inst.read_data);
        dut_hdl->blockBTableSP_addr(blockBTableSP_hdl_inst.addr);
        dut_hdl->blockBTableSP_enable(blockBTableSP_hdl_inst.enable);
        dut_hdl->blockBTableSP_wr_en(blockBTableSP_hdl_inst.wr_en);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        cStuffIf_bfm_inst.if_p(this->cStuffIf);
        cStuffIf_bfm_inst.hdl_if_p(cStuffIf_hdl_inst);
        cStuffIf_bfm_inst.clk(clk);
        cStuffIf_bfm_inst.rst_n(rst_n);

        dee0_bfm_inst.if_p(this->dee0);
        dee0_bfm_inst.hdl_if_p(dee0_hdl_inst);
        dee0_bfm_inst.clk(clk);
        dee0_bfm_inst.rst_n(rst_n);

        dee1_bfm_inst.if_p(this->dee1);
        dee1_bfm_inst.hdl_if_p(dee1_hdl_inst);
        dee1_bfm_inst.clk(clk);
        dee1_bfm_inst.rst_n(rst_n);

        outD_bfm_inst.if_p(this->outD);
        outD_bfm_inst.hdl_if_p(outD_hdl_inst);
        outD_bfm_inst.clk(clk);
        outD_bfm_inst.rst_n(rst_n);

        inD_bfm_inst.if_p(this->inD);
        inD_bfm_inst.hdl_if_p(inD_hdl_inst);
        inD_bfm_inst.clk(clk);
        inD_bfm_inst.rst_n(rst_n);

        btod_bfm_inst.if_p(this->btod);
        btod_bfm_inst.hdl_if_p(btod_hdl_inst);
        btod_bfm_inst.clk(clk);
        btod_bfm_inst.rst_n(rst_n);

        rwD_bfm_inst.if_p(this->rwD);
        rwD_bfm_inst.hdl_if_p(rwD_hdl_inst);
        rwD_bfm_inst.clk(clk);
        rwD_bfm_inst.rst_n(rst_n);

        roBsize_bfm_inst.if_p(this->roBsize);
        roBsize_bfm_inst.hdl_if_p(roBsize_hdl_inst);
        roBsize_bfm_inst.clk(clk);
        roBsize_bfm_inst.rst_n(rst_n);

        blockBTableExt_bfm_inst.if_p(this->blockBTableExt);
        blockBTableExt_bfm_inst.hdl_if_p(blockBTableExt_hdl_inst);
        blockBTableExt_bfm_inst.clk(clk);
        blockBTableExt_bfm_inst.rst_n(rst_n);

        blockBTable37Bit_bfm_inst.if_p(this->blockBTable37Bit);
        blockBTable37Bit_bfm_inst.hdl_if_p(blockBTable37Bit_hdl_inst);
        blockBTable37Bit_bfm_inst.clk(clk);
        blockBTable37Bit_bfm_inst.rst_n(rst_n);

        rwArr_bfm_inst.if_p(this->rwArr);
        rwArr_bfm_inst.hdl_if_p(rwArr_hdl_inst);
        rwArr_bfm_inst.clk(clk);
        rwArr_bfm_inst.rst_n(rst_n);

        for (size_t i = 0; i < REGARR_N; i++) {
            extArr_bfm_inst[i].if_p(this->extArr[i]);
            extArr_bfm_inst[i].hdl_if_p(extArr_hdl_inst[i]);
            extArr_bfm_inst[i].clk(clk);
            extArr_bfm_inst[i].rst_n(rst_n);
        }

        blockBTable1_bfm_inst.if_p(this->blockBTable1);
        blockBTable1_bfm_inst.hdl_if_p(blockBTable1_hdl_inst);
        blockBTable1_bfm_inst.clk(clk);
        blockBTable1_bfm_inst.rst_n(rst_n);

        blockBTableSP_bfm_inst.if_p(this->blockBTableSP);
        blockBTableSP_bfm_inst.hdl_if_p(blockBTableSP_hdl_inst);
        blockBTableSP_bfm_inst.clk(clk);
        blockBTableSP_bfm_inst.rst_n(rst_n);

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

    rdy_vld_hdl_if<sc_bv<5>> cStuffIf_hdl_inst;
    rdy_vld_hdl_if<sc_bv<7>> dee0_hdl_inst;
    rdy_vld_hdl_if<sc_bv<7>> dee1_hdl_inst;
    rdy_vld_hdl_if<sc_bv<7>> outD_hdl_inst;
    rdy_vld_hdl_if<sc_bv<7>> inD_hdl_inst;
    req_ack_hdl_if<sc_bv<4>, bool> btod_hdl_inst;
    status_hdl_if<sc_bv<7>> rwD_hdl_inst;
    status_hdl_if<sc_bv<4>> roBsize_hdl_inst;
    memory_hdl_if<sc_bv<4>, sc_bv<5>> blockBTableExt_hdl_inst;
    memory_hdl_if<sc_bv<4>, sc_bv<37>> blockBTable37Bit_hdl_inst;
    status_hdl_if<sc_bv<7>> rwArr_hdl_inst;
    std::array<external_reg_hdl_if<sc_bv<7>>, REGARR_N> extArr_hdl_inst;
    memory_hdl_if<sc_bv<4>, sc_bv<64>> blockBTable1_hdl_inst;
    memory_hdl_if<sc_bv<4>, sc_bv<18>> blockBTableSP_hdl_inst;

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

#endif // BLOCKD_HDL_SC_WRAPPER_H_
