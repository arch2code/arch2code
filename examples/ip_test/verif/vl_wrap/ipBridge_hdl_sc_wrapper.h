#ifndef IPBRIDGE_HDL_SC_WRAPPER_H_
#define IPBRIDGE_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=ipBridge

#include "ipBridgeBase.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "ipBridge_hdl_sv_wrapper.h"
#else
#include "VipBridge_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "ipConfig.h"
#include "apb_bfm.h"
#include "push_ack_bfm.h"

class ipBridge_hdl_sc_wrapper: public sc_module, public blockBase, public ipBridgeBase {

public:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "ipBridge_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < ipBridge_hdl_sc_wrapper > (blockName, variant, bbMode));
                });
        }
    };

    static registerBlock registerBlock_;

#if !defined(VERILATOR) && defined(VCS)
    ipBridge_hdl_sv_wrapper *dut_hdl;
#else
    VipBridge_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    push_ack_dst_bfm<data8St, sc_bv<9>> data8In_bfm;
    push_ack_dst_bfm<data70St, sc_bv<71>> data70In_bfm;
    apb_dst_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_bfm;

    SC_HAS_PROCESS (ipBridge_hdl_sc_wrapper);

    ipBridge_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("ipBridge_hdl_sc_wrapper", name(), bbMode),
        ipBridgeBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        data8In_bfm("data8In_bfm"),
        data70In_bfm("data70In_bfm"),
        apbReg_bfm("apbReg_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new ipBridge_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VipBridge_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->data8In_push(data8In_hdl_if.push);
        dut_hdl->data8In_data(data8In_hdl_if.data);
        dut_hdl->data8In_ack(data8In_hdl_if.ack);
        dut_hdl->data70In_push(data70In_hdl_if.push);
        dut_hdl->data70In_data(data70In_hdl_if.data);
        dut_hdl->data70In_ack(data70In_hdl_if.ack);
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

        data8In_bfm.if_p(data8In);
        data8In_bfm.hdl_if_p(data8In_hdl_if);
        data8In_bfm.clk(clk);
        data8In_bfm.rst_n(rst_n);

        data70In_bfm.if_p(data70In);
        data70In_bfm.hdl_if_p(data70In_hdl_if);
        data70In_bfm.clk(clk);
        data70In_bfm.rst_n(rst_n);

        apbReg_bfm.if_p(apbReg);
        apbReg_bfm.hdl_if_p(apbReg_hdl_if);
        apbReg_bfm.clk(clk);
        apbReg_bfm.rst_n(rst_n);

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

    push_ack_hdl_if<sc_bv<9>> data8In_hdl_if;
    push_ack_hdl_if<sc_bv<71>> data70In_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_hdl_if;

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

#endif // IPBRIDGE_HDL_SC_WRAPPER_H_
