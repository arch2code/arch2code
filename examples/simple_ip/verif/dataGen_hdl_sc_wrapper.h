#ifndef DATAGEN_HDL_SC_WRAPPER_H_
#define DATAGEN_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=dataGen
// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=preamble
#include "systemc.h"
#include "blockBase.h"
import simple_ip_dataGen.base;

// A non-templated wrapper names its Verilated RTL top concretely, so it
// includes the DUT header directly.
#if !defined(VERILATOR) && defined(VCS)
#include "dataGen_hdl_sv_wrapper.h"
#else
#include "VdataGen_hdl_sv_wrapper.h"
#endif
// GENERATED_CODE_END

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

import simple_ip;
using namespace simple_ip_ns;
#include "push_ack_bfm.h"

class dataGen_hdl_sc_wrapper: public sc_module, public blockBase, public dataGenBase {

public:

#if !defined(VERILATOR) && defined(VCS)
    dataGen_hdl_sv_wrapper *dut_hdl;
#else
    VdataGen_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    push_ack_src_bfm<simpleData8St, sc_bv<9>> out_bfm;

    SC_HAS_PROCESS (dataGen_hdl_sc_wrapper);

    dataGen_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("dataGen_hdl_sc_wrapper", name(), bbMode),
        dataGenBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        out_bfm("out_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new dataGen_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new VdataGen_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->out_push(out_hdl_if.push);
        dut_hdl->out_data(out_hdl_if.data);
        dut_hdl->out_ack(out_hdl_if.ack);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        out_bfm.if_p(this->out);
        out_bfm.hdl_if_p(out_hdl_if);
        out_bfm.clk(clk);
        out_bfm.rst_n(rst_n);

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

    push_ack_hdl_if<sc_bv<9>> out_hdl_if;

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

#endif // DATAGEN_HDL_SC_WRAPPER_H_
