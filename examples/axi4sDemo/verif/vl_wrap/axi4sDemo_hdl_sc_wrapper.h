#ifndef AXI4SDEMO_HDL_SC_WRAPPER_H_
#define AXI4SDEMO_HDL_SC_WRAPPER_H_

#include "systemc.h"
#include "instanceFactory.h"

// GENERATED_CODE_PARAM --block=axi4sDemo

#include "axi4sDemoBase.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "axi4sDemo_hdl_sv_wrapper.h"
#else
#include "Vaxi4sDemo_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "axi4_stream_bfm.h"

class axi4sDemo_hdl_sc_wrapper: public sc_module, public blockBase, public axi4sDemoBase {

public:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "axi4sDemo_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < axi4sDemo_hdl_sc_wrapper > (blockName, variant, bbMode));
                });
        }
    };

    static registerBlock registerBlock_;

#if !defined(VERILATOR) && defined(VCS)
    axi4sDemo_hdl_sv_wrapper *dut_hdl;
#else
    Vaxi4sDemo_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    axi4_stream_dst_bfm<data_t1_t, tid_t1_t, tdest_t1_t, tuser_t1_t, sc_bv<256>, sc_bv<4>, sc_bv<4>, sc_bv<16>, sc_bv<32>, sc_bv<32>> axis4_t1_bfm;
    axi4_stream_src_bfm<data_t2_t, tid_t2_t, tdest_t2_t, tuser_t2_t, sc_bv<64>, sc_bv<4>, sc_bv<4>, sc_bv<4>, sc_bv<8>, sc_bv<8>> axis4_t2_bfm;

    SC_HAS_PROCESS (axi4sDemo_hdl_sc_wrapper);

    axi4sDemo_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("axi4sDemo_hdl_sc_wrapper", name(), bbMode),
        axi4sDemoBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        axis4_t1_bfm("axis4_t1_bfm"),
        axis4_t2_bfm("axis4_t2_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new axi4sDemo_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new Vaxi4sDemo_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->axis4_t1_tvalid(axis4_t1_hdl_if.tvalid);
        dut_hdl->axis4_t1_tready(axis4_t1_hdl_if.tready);
        dut_hdl->axis4_t1_tdata(axis4_t1_hdl_if.tdata);
        dut_hdl->axis4_t1_tstrb(axis4_t1_hdl_if.tstrb);
        dut_hdl->axis4_t1_tkeep(axis4_t1_hdl_if.tkeep);
        dut_hdl->axis4_t1_tlast(axis4_t1_hdl_if.tlast);
        dut_hdl->axis4_t1_tid(axis4_t1_hdl_if.tid);
        dut_hdl->axis4_t1_tdest(axis4_t1_hdl_if.tdest);
        dut_hdl->axis4_t1_tuser(axis4_t1_hdl_if.tuser);
        dut_hdl->axis4_t2_tvalid(axis4_t2_hdl_if.tvalid);
        dut_hdl->axis4_t2_tready(axis4_t2_hdl_if.tready);
        dut_hdl->axis4_t2_tdata(axis4_t2_hdl_if.tdata);
        dut_hdl->axis4_t2_tstrb(axis4_t2_hdl_if.tstrb);
        dut_hdl->axis4_t2_tkeep(axis4_t2_hdl_if.tkeep);
        dut_hdl->axis4_t2_tlast(axis4_t2_hdl_if.tlast);
        dut_hdl->axis4_t2_tid(axis4_t2_hdl_if.tid);
        dut_hdl->axis4_t2_tdest(axis4_t2_hdl_if.tdest);
        dut_hdl->axis4_t2_tuser(axis4_t2_hdl_if.tuser);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        axis4_t1_bfm.if_p(axis4_t1);
        axis4_t1_bfm.hdl_if_p(axis4_t1_hdl_if);
        axis4_t1_bfm.clk(clk);
        axis4_t1_bfm.rst_n(rst_n);

        axis4_t2_bfm.if_p(axis4_t2);
        axis4_t2_bfm.hdl_if_p(axis4_t2_hdl_if);
        axis4_t2_bfm.clk(clk);
        axis4_t2_bfm.rst_n(rst_n);

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

    axi4_stream_hdl_if<sc_bv<256>, sc_bv<4>, sc_bv<4>, sc_bv<16>, sc_bv<32>, sc_bv<32>> axis4_t1_hdl_if;
    axi4_stream_hdl_if<sc_bv<64>, sc_bv<4>, sc_bv<4>, sc_bv<4>, sc_bv<8>, sc_bv<8>> axis4_t2_hdl_if;

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

#endif // AXI4SDEMO_HDL_SC_WRAPPER_H_
