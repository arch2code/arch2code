#ifndef UVMMEM_UVM_SC_WRAPPER_H_
#define UVMMEM_UVM_SC_WRAPPER_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmMem
// GENERATED_CODE_BEGIN --template=module_uvm_sc_wrapper --section=class

#include <format>
#include <memory>
#include <string>
#include <type_traits>
#include "systemc.h"
#include "blockBase.h"
#include "instanceFactory.h"
#include "q_assert.h"
#include "memory_bfm.h"
#include "rdy_vld_bfm.h"
import uvmMem.base;
import uvmMem;
using namespace uvmMem_ns;
import a2c.endOfTest;

// The testbench config creates the wrapper through the instanceFactory,
// which passes no DUT choice, and reads the outcome in final(), so both
// pass through here. A run holds one wrapper.
struct uvmMem_uvm_run {
    static constexpr const char *notFinished = "UVM testbench did not finish: uvm_done never rose";
    static inline bool rtlDut = false;
    static inline bool modelDut = false;
    static inline bool completed = false;
};

template <typename TB_T>
class uvmMem_uvm_sc_wrapper : public sc_module, public blockBase {
    // The shell takes each pin width from the boundary pin list, and the
    // BFMs take theirs from the payload types.
    static_assert(std::is_same_v<decltype(TB_T::cmd_data), sc_out<sc_bv<40>>>,
                  "cmd_data in the testbench shell is not sc_out<sc_bv<40>>");
    static_assert(std::is_same_v<decltype(TB_T::out_data), sc_in<sc_bv<32>>>,
                  "out_data in the testbench shell is not sc_in<sc_bv<32>>");
    static_assert(std::is_same_v<decltype(TB_T::wr_write_data), sc_in<sc_bv<32>>>,
                  "wr_write_data in the testbench shell is not sc_in<sc_bv<32>>");
    static_assert(std::is_same_v<decltype(TB_T::wr_read_data), sc_out<sc_bv<32>>>,
                  "wr_read_data in the testbench shell is not sc_out<sc_bv<32>>");
    static_assert(std::is_same_v<decltype(TB_T::wr_addr), sc_in<sc_bv<4>>>,
                  "wr_addr in the testbench shell is not sc_in<sc_bv<4>>");
    static_assert(std::is_same_v<decltype(TB_T::rd_write_data), sc_in<sc_bv<32>>>,
                  "rd_write_data in the testbench shell is not sc_in<sc_bv<32>>");
    static_assert(std::is_same_v<decltype(TB_T::rd_read_data), sc_out<sc_bv<32>>>,
                  "rd_read_data in the testbench shell is not sc_out<sc_bv<32>>");
    static_assert(std::is_same_v<decltype(TB_T::rd_addr), sc_in<sc_bv<4>>>,
                  "rd_addr in the testbench shell is not sc_in<sc_bv<4>>");
public:
    using self_t = uvmMem_uvm_sc_wrapper<TB_T>;
    SC_HAS_PROCESS(self_t);

    uvmMem_uvm_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("uvmMem_uvm_sc_wrapper", name(), bbMode),
        tb_hdl("tb_hdl"),
        clk("clk"),
        rst_n("rst_n", false),
        clk_half_(sc_time(1, SC_NS) / 2),
        uvm_done("uvm_done"),
        uvm_errors("uvm_errors"),
        rtl_dut("rtl_dut"),
        model_dut("model_dut"),
        wr_model_credit("wr_model_credit"),
        wr_model_held("wr_model_held"),
        rd_model_credit("rd_model_credit"),
        rd_model_held("rd_model_held"),
        m_eot(true)
    {
        tb_hdl.cmd_vld(cmd_hdl_inst.vld);
        tb_hdl.cmd_data(cmd_hdl_inst.data);
        tb_hdl.cmd_rdy(cmd_hdl_inst.rdy);
        tb_hdl.out_vld(out_hdl_inst.vld);
        tb_hdl.out_data(out_hdl_inst.data);
        tb_hdl.out_rdy(out_hdl_inst.rdy);
        tb_hdl.wr_write_data(wr_hdl_inst.write_data);
        tb_hdl.wr_read_data(wr_hdl_inst.read_data);
        tb_hdl.wr_addr(wr_hdl_inst.addr);
        tb_hdl.wr_enable(wr_hdl_inst.enable);
        tb_hdl.wr_wr_en(wr_hdl_inst.wr_en);
        tb_hdl.rd_write_data(rd_hdl_inst.write_data);
        tb_hdl.rd_read_data(rd_hdl_inst.read_data);
        tb_hdl.rd_addr(rd_hdl_inst.addr);
        tb_hdl.rd_enable(rd_hdl_inst.enable);
        tb_hdl.rd_wr_en(rd_hdl_inst.wr_en);
        tb_hdl.clk(clk);
        tb_hdl.rst_n(rst_n);
        tb_hdl.wr_model_credit(wr_model_credit);
        tb_hdl.wr_model_held(wr_model_held);
        tb_hdl.rd_model_credit(rd_model_credit);
        tb_hdl.rd_model_held(rd_model_held);
        tb_hdl.uvm_done(uvm_done);
        tb_hdl.uvm_errors(uvm_errors);
        tb_hdl.rtl_dut(rtl_dut);
        tb_hdl.model_dut(model_dut);

        // The model and its BFMs exist when the run's DUT set holds the model;
        // with the RTL alone the pins toward SystemC stay bound to idle signals.
        if (uvmMem_uvm_run::modelDut) {
            chnl = std::make_unique<uvmMemChannels>("Chnl", "uvm");
            dut = std::dynamic_pointer_cast<uvmMemBase>(
                instanceFactory::createInstance(name(), "uvmMem", "uvmMem", variant, "uvmMem"));
            Q_ASSERT(dut != nullptr, "uvmMem model instance was not created");
            dut->cmd(chnl->cmd);
            dut->out(chnl->out);
            dut->wr(chnl->wr);
            dut->rd(chnl->rd);

            cmd_bfm_inst = std::make_unique<rdy_vld_src_bfm<uvmMemCmdSt, sc_bv<40>>>("cmd_bfm_inst");
            cmd_bfm_inst->if_p(chnl->cmd);
            cmd_bfm_inst->hdl_if_p(cmd_hdl_inst);
            cmd_bfm_inst->clk(clk);
            cmd_bfm_inst->rst_n(rst_n);

            out_bfm_inst = std::make_unique<rdy_vld_dst_bfm<uvmMemWordSt, sc_bv<32>>>("out_bfm_inst");
            out_bfm_inst->if_p(chnl->out);
            out_bfm_inst->hdl_if_p(out_hdl_inst);
            out_bfm_inst->clk(clk);
            out_bfm_inst->rst_n(rst_n);

            wr_bfm_inst = std::make_unique<memory_dst_bfm<uvmMemAddrSt, uvmMemWordSt, sc_bv<4>, sc_bv<32>>>("wr_bfm_inst");
            wr_bfm_inst->if_p(chnl->wr);
            wr_bfm_inst->hdl_if_p(wr_hdl_inst);
            wr_bfm_inst->clk(clk);
            wr_bfm_inst->rst_n(rst_n);
            if (uvmMem_uvm_run::rtlDut) {
                wr_bfm_inst->setModelCredit(&wr_model_credit, &wr_model_held);
            }
            if (!uvmMem_uvm_run::rtlDut) {
                wr_bfm_inst->setWriteOrder(&m_writeOrder);
            }

            rd_bfm_inst = std::make_unique<memory_dst_bfm<uvmMemAddrSt, uvmMemWordSt, sc_bv<4>, sc_bv<32>>>("rd_bfm_inst");
            rd_bfm_inst->if_p(chnl->rd);
            rd_bfm_inst->hdl_if_p(rd_hdl_inst);
            rd_bfm_inst->clk(clk);
            rd_bfm_inst->rst_n(rst_n);
            if (uvmMem_uvm_run::rtlDut) {
                rd_bfm_inst->setModelCredit(&rd_model_credit, &rd_model_held);
            }
            if (!uvmMem_uvm_run::rtlDut) {
                rd_bfm_inst->setWriteOrder(&m_writeOrder);
            }
        }

        clk.write(true);
        SC_THREAD(clock_gen_clk);
        SC_THREAD(reset_driver_rst_n);
        SC_THREAD(uvm_watch);
        SC_THREAD(eot_thread);
    }

    void setTimed(int nsec, timedDelayMode mode) override {}
    void setLogging(verbosity_e verbosity) override {}

private:
    TB_T tb_hdl;
    sc_signal<bool> clk;
    sc_signal<bool> rst_n;
    sc_time clk_half_;
    sc_signal<bool> uvm_done;
    sc_signal<sc_bv<32>> uvm_errors;
    sc_signal<bool> rtl_dut;
    sc_signal<bool> model_dut;
    sc_signal<sc_bv<32>> wr_model_credit;
    sc_signal<bool> wr_model_held;
    sc_signal<sc_bv<32>> rd_model_credit;
    sc_signal<bool> rd_model_held;

    rdy_vld_hdl_if<sc_bv<40>> cmd_hdl_inst;
    rdy_vld_hdl_if<sc_bv<32>> out_hdl_inst;
    memory_hdl_if<sc_bv<4>, sc_bv<32>> wr_hdl_inst;
    memory_hdl_if<sc_bv<4>, sc_bv<32>> rd_hdl_inst;

    std::unique_ptr<uvmMemChannels> chnl;
    std::shared_ptr<uvmMemBase> dut;
    std::unique_ptr<rdy_vld_src_bfm<uvmMemCmdSt, sc_bv<40>>> cmd_bfm_inst;
    std::unique_ptr<rdy_vld_dst_bfm<uvmMemWordSt, sc_bv<32>>> out_bfm_inst;
    std::unique_ptr<memory_dst_bfm<uvmMemAddrSt, uvmMemWordSt, sc_bv<4>, sc_bv<32>>> wr_bfm_inst;
    std::unique_ptr<memory_dst_bfm<uvmMemAddrSt, uvmMemWordSt, sc_bv<4>, sc_bv<32>>> rd_bfm_inst;
    memory_write_order m_writeOrder;

    endOfTest m_eot;

    void clock_gen(sc_signal<bool> &sig, const sc_time &half) {
        while (true) {
            wait(half);
            sig.write(!sig.read());
        }
    }

    // The clock parameter is named reset_driver_clk, not clk, so it does not
    // shadow a member clock named clk.
    void reset_driver(sc_signal<bool> &rst, sc_signal<bool> &reset_driver_clk, int cycles) {
        for (int cycle = 0; cycle < cycles; cycle++) {
            wait(reset_driver_clk.posedge_event());
        }
        rst.write(true);
    }

    void clock_gen_clk() { clock_gen(clk, clk_half_); }
    void reset_driver_rst_n() { reset_driver(rst_n, clk, 3); }

    void uvm_watch(void) {
        while (!uvm_done.read()) {
            wait(uvm_done.value_changed_event());
        }
        auto dutSet = [](bool rtl, bool model) {
            return rtl && model ? "model and RTL DUTs" : rtl ? "RTL DUT" : "model DUT";
        };
        const bool svRtl = rtl_dut.read();
        const bool svModel = model_dut.read();
        const uint32_t errors = uvm_errors.read().to_uint();
        log_.logPrint(std::format("UVM finished with {} UVM_ERROR/UVM_FATAL; the SV testbench was built with the {}",
                                  errors, dutSet(svRtl, svModel)), LOG_ALWAYS);
        std::string failure;
        if (svRtl != uvmMem_uvm_run::rtlDut || svModel != uvmMem_uvm_run::modelDut) {
            const char *option = uvmMem_uvm_run::rtlDut && uvmMem_uvm_run::modelDut ? "both" : uvmMem_uvm_run::rtlDut ? "rtl" : "model";
            failure = std::format(
                "--uvmDut {} does not match the snapshot: the run expects the {}, and the SV testbench holds the {}",
                option, dutSet(uvmMem_uvm_run::rtlDut, uvmMem_uvm_run::modelDut), dutSet(svRtl, svModel));
        } else if (errors != 0) {
            failure = std::format("UVM reported {} UVM_ERROR/UVM_FATAL", errors);
        }
        if (!failure.empty()) {
            log_.logPrint(failure, LOG_ALWAYS);
            errorCode::fail(failure);
        }
        uvmMem_uvm_run::completed = true;
        m_eot.setEndOfTest(true);
    }

    // A SystemC testbench ends the simulation from its External, which this
    // testbench does not have.
    void eot_thread(void) {
        wait(endOfTestState::GetInstance().eotEvent);
        sc_stop();
    }
};

// GENERATED_CODE_END

#endif // UVMMEM_UVM_SC_WRAPPER_H_
