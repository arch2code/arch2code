#ifndef BRIDGEAPBDECODE_HDL_SC_WRAPPER_H_
#define BRIDGEAPBDECODE_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=bridgeApbDecode
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
import ipBridge_bridgeApbDecode.base;

// Verilated RTL top (SystemC): a wrapper with no instance-bound variants names
// its DUT concretely, so it includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "bridgeApbDecode_hdl_sv_wrapper.h"
#else
#include "VbridgeApbDecode_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import common_shared_types;
using namespace common_shared_types_ns;
#include "apb_bfm.h"

class bridgeApbDecode_hdl_sc_wrapper: public sc_module, public blockBase, public bridgeApbDecodeBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    bridgeApbDecode_hdl_sv_wrapper *dut_hdl;
#else
    VbridgeApbDecode_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_uBridgeIp0_bfm;
    apb_src_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_uBridgeIp1_bfm;
    apb_dst_bfm<apbAddrSt, apbDataSt, sc_bv<32>, sc_bv<32>> apbReg_bfm;

    SC_HAS_PROCESS (bridgeApbDecode_hdl_sc_wrapper);

    bridgeApbDecode_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("bridgeApbDecode_hdl_sc_wrapper", name(), bbMode),
        bridgeApbDecodeBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        apbReg_uBridgeIp0_bfm("apbReg_uBridgeIp0_bfm"),
        apbReg_uBridgeIp1_bfm("apbReg_uBridgeIp1_bfm"),
        apbReg_bfm("apbReg_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new bridgeApbDecode_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VbridgeApbDecode_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->apbReg_uBridgeIp0_paddr(apbReg_uBridgeIp0_hdl_if.paddr);
        dut_hdl->apbReg_uBridgeIp0_psel(apbReg_uBridgeIp0_hdl_if.psel);
        dut_hdl->apbReg_uBridgeIp0_penable(apbReg_uBridgeIp0_hdl_if.penable);
        dut_hdl->apbReg_uBridgeIp0_pwrite(apbReg_uBridgeIp0_hdl_if.pwrite);
        dut_hdl->apbReg_uBridgeIp0_pwdata(apbReg_uBridgeIp0_hdl_if.pwdata);
        dut_hdl->apbReg_uBridgeIp0_pready(apbReg_uBridgeIp0_hdl_if.pready);
        dut_hdl->apbReg_uBridgeIp0_prdata(apbReg_uBridgeIp0_hdl_if.prdata);
        dut_hdl->apbReg_uBridgeIp0_pslverr(apbReg_uBridgeIp0_hdl_if.pslverr);
        dut_hdl->apbReg_uBridgeIp1_paddr(apbReg_uBridgeIp1_hdl_if.paddr);
        dut_hdl->apbReg_uBridgeIp1_psel(apbReg_uBridgeIp1_hdl_if.psel);
        dut_hdl->apbReg_uBridgeIp1_penable(apbReg_uBridgeIp1_hdl_if.penable);
        dut_hdl->apbReg_uBridgeIp1_pwrite(apbReg_uBridgeIp1_hdl_if.pwrite);
        dut_hdl->apbReg_uBridgeIp1_pwdata(apbReg_uBridgeIp1_hdl_if.pwdata);
        dut_hdl->apbReg_uBridgeIp1_pready(apbReg_uBridgeIp1_hdl_if.pready);
        dut_hdl->apbReg_uBridgeIp1_prdata(apbReg_uBridgeIp1_hdl_if.prdata);
        dut_hdl->apbReg_uBridgeIp1_pslverr(apbReg_uBridgeIp1_hdl_if.pslverr);
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

        apbReg_uBridgeIp0_bfm.if_p(this->apbReg_uBridgeIp0);
        apbReg_uBridgeIp0_bfm.hdl_if_p(apbReg_uBridgeIp0_hdl_if);
        apbReg_uBridgeIp0_bfm.clk(clk);
        apbReg_uBridgeIp0_bfm.rst_n(rst_n);

        apbReg_uBridgeIp1_bfm.if_p(this->apbReg_uBridgeIp1);
        apbReg_uBridgeIp1_bfm.hdl_if_p(apbReg_uBridgeIp1_hdl_if);
        apbReg_uBridgeIp1_bfm.clk(clk);
        apbReg_uBridgeIp1_bfm.rst_n(rst_n);

        apbReg_bfm.if_p(this->apbReg);
        apbReg_bfm.hdl_if_p(apbReg_hdl_if);
        apbReg_bfm.clk(clk);
        apbReg_bfm.rst_n(rst_n);

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

    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_uBridgeIp0_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_uBridgeIp1_hdl_if;
    apb_hdl_if<sc_bv<32>, sc_bv<32>> apbReg_hdl_if;

    sc_signal<bool> rst_n;

    void reset_driver_rst_n() {
        for (int cycle = 0; cycle < 3; cycle++) {
            wait(clk.posedge_event());
        }
        rst_n = true;
    }

// GENERATED_CODE_END

    // Callback executed at the end of module constructor
    void end_ctor_init() {
        // Register synchLock,...
    }

};

#endif // BRIDGEAPBDECODE_HDL_SC_WRAPPER_H_
