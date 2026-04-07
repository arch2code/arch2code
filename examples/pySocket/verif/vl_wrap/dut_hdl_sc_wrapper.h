#ifndef DUT_HDL_SC_WRAPPER_H_
#define DUT_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=dut

#include "dutBase.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "dut_hdl_sv_wrapper.h"
#else
#include "Vdut_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "req_ack_bfm.h"

class dut_hdl_sc_wrapper: public sc_module, public blockBase, public dutBase {

public:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "dut_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < dut_hdl_sc_wrapper > (blockName, variant, bbMode));
                });
        }
    };

    static registerBlock registerBlock_;

#if !defined(VERILATOR) && defined(VCS)
    dut_hdl_sv_wrapper *dut_hdl;
#else
    Vdut_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    req_ack_dst_bfm<p2s_message_st, p2s_response_st, sc_bv<64>, sc_bv<32>> test_req_ack_bfm;
    req_ack_dst_bfm<p2s_message_st, p2s_response_st, sc_bv<64>, sc_bv<32>> test2Python_req_ack_bfm;
    req_ack_src_bfm<p2s_message_st, p2s_response_st, sc_bv<64>, sc_bv<32>> dut2Python_req_ack_bfm;

    SC_HAS_PROCESS (dut_hdl_sc_wrapper);

    dut_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("dut_hdl_sc_wrapper", name(), bbMode),
        dutBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        test_req_ack_bfm("test_req_ack_bfm"),
        test2Python_req_ack_bfm("test2Python_req_ack_bfm"),
        dut2Python_req_ack_bfm("dut2Python_req_ack_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new dut_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new Vdut_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->test_req_ack_req(test_req_ack_hdl_if.req);
        dut_hdl->test_req_ack_data(test_req_ack_hdl_if.data);
        dut_hdl->test_req_ack_ack(test_req_ack_hdl_if.ack);
        dut_hdl->test_req_ack_rdata(test_req_ack_hdl_if.rdata);
        dut_hdl->test2Python_req_ack_req(test2Python_req_ack_hdl_if.req);
        dut_hdl->test2Python_req_ack_data(test2Python_req_ack_hdl_if.data);
        dut_hdl->test2Python_req_ack_ack(test2Python_req_ack_hdl_if.ack);
        dut_hdl->test2Python_req_ack_rdata(test2Python_req_ack_hdl_if.rdata);
        dut_hdl->dut2Python_req_ack_req(dut2Python_req_ack_hdl_if.req);
        dut_hdl->dut2Python_req_ack_data(dut2Python_req_ack_hdl_if.data);
        dut_hdl->dut2Python_req_ack_ack(dut2Python_req_ack_hdl_if.ack);
        dut_hdl->dut2Python_req_ack_rdata(dut2Python_req_ack_hdl_if.rdata);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        test_req_ack_bfm.if_p(test_req_ack);
        test_req_ack_bfm.hdl_if_p(test_req_ack_hdl_if);
        test_req_ack_bfm.clk(clk);
        test_req_ack_bfm.rst_n(rst_n);

        test2Python_req_ack_bfm.if_p(test2Python_req_ack);
        test2Python_req_ack_bfm.hdl_if_p(test2Python_req_ack_hdl_if);
        test2Python_req_ack_bfm.clk(clk);
        test2Python_req_ack_bfm.rst_n(rst_n);

        dut2Python_req_ack_bfm.if_p(dut2Python_req_ack);
        dut2Python_req_ack_bfm.hdl_if_p(dut2Python_req_ack_hdl_if);
        dut2Python_req_ack_bfm.clk(clk);
        dut2Python_req_ack_bfm.rst_n(rst_n);

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

    req_ack_hdl_if<sc_bv<64>, sc_bv<32>> test_req_ack_hdl_if;
    req_ack_hdl_if<sc_bv<64>, sc_bv<32>> test2Python_req_ack_hdl_if;
    req_ack_hdl_if<sc_bv<64>, sc_bv<32>> dut2Python_req_ack_hdl_if;

    sc_signal<bool> rst_n;

    void reset_driver() {
        wait(5, SC_NS);
        rst_n = true;
    }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // DUT_HDL_SC_WRAPPER_H_
