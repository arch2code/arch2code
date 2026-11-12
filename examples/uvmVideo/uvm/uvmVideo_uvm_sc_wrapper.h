#ifndef UVMVIDEO_UVM_SC_WRAPPER_H_
#define UVMVIDEO_UVM_SC_WRAPPER_H_
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=uvmVideo
// GENERATED_CODE_BEGIN --template=module_uvm_sc_wrapper --section=class

#include <format>
#include <memory>
#include <string>
#include <type_traits>
#include "systemc.h"
#include "blockBase.h"
#include "instanceFactory.h"
#include "q_assert.h"
#include "axi4_stream_bfm.h"
#include "raw_bfm.h"
import uvmVideo.base;
import uvmVideo;
using namespace uvmVideo_ns;
import a2c.endOfTest;

// The testbench config creates the wrapper through the instanceFactory,
// which passes no DUT choice, and reads the outcome in final(), so both
// pass through here. A run holds one wrapper.
struct uvmVideo_uvm_run {
    static constexpr const char *notFinished = "UVM testbench did not finish: uvm_done never rose";
    static inline bool rtlDut = false;
    static inline bool modelDut = false;
    static inline bool completed = false;
};

template <typename TB_T>
class uvmVideo_uvm_sc_wrapper : public sc_module, public blockBase {
    // The shell takes each pin width from the boundary pin list, and the
    // BFMs take theirs from the payload types.
    static_assert(std::is_same_v<decltype(TB_T::vin_data), sc_out<sc_bv<18>>>,
                  "vin_data in the testbench shell is not sc_out<sc_bv<18>>");
    static_assert(std::is_same_v<decltype(TB_T::vout_tdata), sc_in<sc_bv<16>>>,
                  "vout_tdata in the testbench shell is not sc_in<sc_bv<16>>");
    static_assert(std::is_same_v<decltype(TB_T::vout_tid), sc_in<bool>>,
                  "vout_tid in the testbench shell is not sc_in<bool>");
    static_assert(std::is_same_v<decltype(TB_T::vout_tdest), sc_in<bool>>,
                  "vout_tdest in the testbench shell is not sc_in<bool>");
    static_assert(std::is_same_v<decltype(TB_T::vout_tuser), sc_in<bool>>,
                  "vout_tuser in the testbench shell is not sc_in<bool>");
public:
    using self_t = uvmVideo_uvm_sc_wrapper<TB_T>;
    SC_HAS_PROCESS(self_t);

    uvmVideo_uvm_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("uvmVideo_uvm_sc_wrapper", name(), bbMode),
        tb_hdl("tb_hdl"),
        clk("clk"),
        rst_n("rst_n", false),
        clk_half_(sc_time(1, SC_NS) / 2),
        uvm_done("uvm_done"),
        uvm_errors("uvm_errors"),
        rtl_dut("rtl_dut"),
        model_dut("model_dut"),
        m_eot(true)
    {
        tb_hdl.vin_data(vin_hdl_inst.data);
        tb_hdl.vout_tvalid(vout_hdl_inst.tvalid);
        tb_hdl.vout_tready(vout_hdl_inst.tready);
        tb_hdl.vout_tdata(vout_hdl_inst.tdata);
        tb_hdl.vout_tstrb(vout_hdl_inst.tstrb);
        tb_hdl.vout_tkeep(vout_hdl_inst.tkeep);
        tb_hdl.vout_tlast(vout_hdl_inst.tlast);
        tb_hdl.vout_tid(vout_hdl_inst.tid);
        tb_hdl.vout_tdest(vout_hdl_inst.tdest);
        tb_hdl.vout_tuser(vout_hdl_inst.tuser);
        tb_hdl.clk(clk);
        tb_hdl.rst_n(rst_n);
        tb_hdl.uvm_done(uvm_done);
        tb_hdl.uvm_errors(uvm_errors);
        tb_hdl.rtl_dut(rtl_dut);
        tb_hdl.model_dut(model_dut);

        // The model and its BFMs exist when the run's DUT set holds the model;
        // with the RTL alone the pins toward SystemC stay bound to idle signals.
        if (uvmVideo_uvm_run::modelDut) {
            chnl = std::make_unique<uvmVideoChannels>("Chnl", "uvm");
            dut = std::dynamic_pointer_cast<uvmVideoBase>(
                instanceFactory::createInstance(name(), "uvmVideo", "uvmVideo", variant, "uvmVideo"));
            Q_ASSERT(dut != nullptr, "uvmVideo model instance was not created");
            dut->vin(chnl->vin);
            dut->vout(chnl->vout);

            vin_bfm_inst = std::make_unique<raw_src_bfm<uvmVideoRawSt, sc_bv<18>>>("vin_bfm_inst");
            vin_bfm_inst->if_p(chnl->vin);
            vin_bfm_inst->hdl_if_p(vin_hdl_inst);
            vin_bfm_inst->clk(clk);
            vin_bfm_inst->rst_n(rst_n);

            vout_bfm_inst = std::make_unique<axi4_stream_dst_bfm<uvmVideoBeatSt, uvmVideoIdSt, uvmVideoIdSt, sc_bv<16>, bool, bool, sc_bv<2>, sc_bv<2>, bool, uvmVideoUserSt>>("vout_bfm_inst");
            vout_bfm_inst->if_p(chnl->vout);
            vout_bfm_inst->hdl_if_p(vout_hdl_inst);
            vout_bfm_inst->clk(clk);
            vout_bfm_inst->rst_n(rst_n);
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

    raw_hdl_if<sc_bv<18>> vin_hdl_inst;
    axi4_stream_hdl_if<sc_bv<16>, bool, bool, sc_bv<2>, sc_bv<2>, bool> vout_hdl_inst;

    std::unique_ptr<uvmVideoChannels> chnl;
    std::shared_ptr<uvmVideoBase> dut;
    std::unique_ptr<raw_src_bfm<uvmVideoRawSt, sc_bv<18>>> vin_bfm_inst;
    std::unique_ptr<axi4_stream_dst_bfm<uvmVideoBeatSt, uvmVideoIdSt, uvmVideoIdSt, sc_bv<16>, bool, bool, sc_bv<2>, sc_bv<2>, bool, uvmVideoUserSt>> vout_bfm_inst;

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
        if (svRtl != uvmVideo_uvm_run::rtlDut || svModel != uvmVideo_uvm_run::modelDut) {
            const char *option = uvmVideo_uvm_run::rtlDut && uvmVideo_uvm_run::modelDut ? "both" : uvmVideo_uvm_run::rtlDut ? "rtl" : "model";
            failure = std::format(
                "--uvmDut {} does not match the snapshot: the run expects the {}, and the SV testbench holds the {}",
                option, dutSet(uvmVideo_uvm_run::rtlDut, uvmVideo_uvm_run::modelDut), dutSet(svRtl, svModel));
        } else if (errors != 0) {
            failure = std::format("UVM reported {} UVM_ERROR/UVM_FATAL", errors);
        }
        if (!failure.empty()) {
            log_.logPrint(failure, LOG_ALWAYS);
            errorCode::fail(failure);
        }
        uvmVideo_uvm_run::completed = true;
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

#endif // UVMVIDEO_UVM_SC_WRAPPER_H_
