#ifndef CONSUMER_HDL_SC_WRAPPER_H_
#define CONSUMER_HDL_SC_WRAPPER_H_

#include "systemc.h"

#include "instanceFactory.h"

#include "axi_write_bfm.h"
#include "axi_read_bfm.h"

// GENERATED_CODE_PARAM --block=consumer

#include "consumer_base.h"

// Verilated RTL top (SystemC)
#if !defined(VERILATOR) && defined(VCS)
#include "consumer_hdl_sv_wrapper.h"
#else
#include "Vconsumer_hdl_sv_wrapper.h"
#endif

// GENERATED_CODE_BEGIN --template=module_hdl_sc_wrapper --section=hdl_sc_wrapper_class

#include "axi4_stream_bfm.h"
#include "axi_read_bfm.h"
#include "axi_write_bfm.h"

class consumer_hdl_sc_wrapper: public sc_module, public blockBase, public consumerBase {

public:

    struct registerBlock
    {
        registerBlock()
        {
            // lamda function to construct the block
            instanceFactory::registerBlock(
                "consumer_verif", [](const char *blockName, const char *variant, blockBaseMode bbMode) -> std::shared_ptr<blockBase> {
                    return static_cast<std::shared_ptr<blockBase>>(std::make_shared < consumer_hdl_sc_wrapper > (blockName, variant, bbMode));
                });
        }
    };

    static registerBlock registerBlock_;

#if !defined(VERILATOR) && defined(VCS)
    consumer_hdl_sv_wrapper *dut_hdl;
#else
    Vconsumer_hdl_sv_wrapper *dut_hdl;
#endif

    sc_clock clk;

    axi_read_dst_bfm<axiAddrSt, axiDataSt, sc_bv<32>, sc_bv<32>> axiRd0_bfm;
    axi_read_dst_bfm<axiAddrSt, axiDataSt, sc_bv<32>, sc_bv<32>> axiRd1_bfm;
    axi_read_dst_bfm<axiAddrSt, axiDataSt, sc_bv<32>, sc_bv<32>> axiRd2_bfm;
    axi_read_dst_bfm<axiAddrSt, axiDataSt, sc_bv<32>, sc_bv<32>> axiRd3_bfm;
    axi_write_dst_bfm<axiAddrSt, axiDataSt, axiStrobeSt, sc_bv<32>, sc_bv<32>, sc_bv<4>> axiWr0_bfm;
    axi_write_dst_bfm<axiAddrSt, axiDataSt, axiStrobeSt, sc_bv<32>, sc_bv<32>, sc_bv<4>> axiWr1_bfm;
    axi_write_dst_bfm<axiAddrSt, axiDataSt, axiStrobeSt, sc_bv<32>, sc_bv<32>, sc_bv<4>> axiWr2_bfm;
    axi_write_dst_bfm<axiAddrSt, axiDataSt, axiStrobeSt, sc_bv<32>, sc_bv<32>, sc_bv<4>> axiWr3_bfm;
    axi4_stream_dst_bfm<axiDataSt, axiAddrSt, axiAddrSt, axiAddrSt, sc_bv<32>, sc_bv<32>, sc_bv<32>, sc_bv<32>> axiStr0_bfm;
    axi4_stream_dst_bfm<axiDataSt, axiAddrSt, axiAddrSt, axiAddrSt, sc_bv<32>, sc_bv<32>, sc_bv<32>, sc_bv<32>> axiStr1_bfm;

    SC_HAS_PROCESS (consumer_hdl_sc_wrapper);

    consumer_hdl_sc_wrapper(sc_module_name modulename, const char *variant, blockBaseMode bbMode) :
        sc_module(modulename),
        blockBase("consumer_hdl_sc_wrapper", name(), bbMode),
        consumerBase(name(), variant),
        clk("clk", sc_time(1, SC_NS), 0.5, sc_time(3, SC_NS), true),
        axiRd0_bfm("axiRd0_bfm"),
        axiRd1_bfm("axiRd1_bfm"),
        axiRd2_bfm("axiRd2_bfm"),
        axiRd3_bfm("axiRd3_bfm"),
        axiWr0_bfm("axiWr0_bfm"),
        axiWr1_bfm("axiWr1_bfm"),
        axiWr2_bfm("axiWr2_bfm"),
        axiWr3_bfm("axiWr3_bfm"),
        axiStr0_bfm("axiStr0_bfm"),
        axiStr1_bfm("axiStr1_bfm"),
        rst_n(0)
    {
#if !defined(VERILATOR) && defined(VCS)
        dut_hdl = new consumer_hdl_sv_wrapper("dut_hdl");
#else
        dut_hdl = new Vconsumer_hdl_sv_wrapper("dut_hdl");
#endif

        dut_hdl->axiRd0_araddr(axiRd0_hdl_if.araddr);
        dut_hdl->axiRd0_arid(axiRd0_hdl_if.arid);
        dut_hdl->axiRd0_arlen(axiRd0_hdl_if.arlen);
        dut_hdl->axiRd0_arsize(axiRd0_hdl_if.arsize);
        dut_hdl->axiRd0_arburst(axiRd0_hdl_if.arburst);
        dut_hdl->axiRd0_arvalid(axiRd0_hdl_if.arvalid);
        dut_hdl->axiRd0_arready(axiRd0_hdl_if.arready);
        dut_hdl->axiRd0_rdata(axiRd0_hdl_if.rdata);
        dut_hdl->axiRd0_rid(axiRd0_hdl_if.rid);
        dut_hdl->axiRd0_rresp(axiRd0_hdl_if.rresp);
        dut_hdl->axiRd0_rlast(axiRd0_hdl_if.rlast);
        dut_hdl->axiRd0_rvalid(axiRd0_hdl_if.rvalid);
        dut_hdl->axiRd0_rready(axiRd0_hdl_if.rready);
        dut_hdl->axiRd1_araddr(axiRd1_hdl_if.araddr);
        dut_hdl->axiRd1_arid(axiRd1_hdl_if.arid);
        dut_hdl->axiRd1_arlen(axiRd1_hdl_if.arlen);
        dut_hdl->axiRd1_arsize(axiRd1_hdl_if.arsize);
        dut_hdl->axiRd1_arburst(axiRd1_hdl_if.arburst);
        dut_hdl->axiRd1_arvalid(axiRd1_hdl_if.arvalid);
        dut_hdl->axiRd1_arready(axiRd1_hdl_if.arready);
        dut_hdl->axiRd1_rdata(axiRd1_hdl_if.rdata);
        dut_hdl->axiRd1_rid(axiRd1_hdl_if.rid);
        dut_hdl->axiRd1_rresp(axiRd1_hdl_if.rresp);
        dut_hdl->axiRd1_rlast(axiRd1_hdl_if.rlast);
        dut_hdl->axiRd1_rvalid(axiRd1_hdl_if.rvalid);
        dut_hdl->axiRd1_rready(axiRd1_hdl_if.rready);
        dut_hdl->axiRd2_araddr(axiRd2_hdl_if.araddr);
        dut_hdl->axiRd2_arid(axiRd2_hdl_if.arid);
        dut_hdl->axiRd2_arlen(axiRd2_hdl_if.arlen);
        dut_hdl->axiRd2_arsize(axiRd2_hdl_if.arsize);
        dut_hdl->axiRd2_arburst(axiRd2_hdl_if.arburst);
        dut_hdl->axiRd2_arvalid(axiRd2_hdl_if.arvalid);
        dut_hdl->axiRd2_arready(axiRd2_hdl_if.arready);
        dut_hdl->axiRd2_rdata(axiRd2_hdl_if.rdata);
        dut_hdl->axiRd2_rid(axiRd2_hdl_if.rid);
        dut_hdl->axiRd2_rresp(axiRd2_hdl_if.rresp);
        dut_hdl->axiRd2_rlast(axiRd2_hdl_if.rlast);
        dut_hdl->axiRd2_rvalid(axiRd2_hdl_if.rvalid);
        dut_hdl->axiRd2_rready(axiRd2_hdl_if.rready);
        dut_hdl->axiRd3_araddr(axiRd3_hdl_if.araddr);
        dut_hdl->axiRd3_arid(axiRd3_hdl_if.arid);
        dut_hdl->axiRd3_arlen(axiRd3_hdl_if.arlen);
        dut_hdl->axiRd3_arsize(axiRd3_hdl_if.arsize);
        dut_hdl->axiRd3_arburst(axiRd3_hdl_if.arburst);
        dut_hdl->axiRd3_arvalid(axiRd3_hdl_if.arvalid);
        dut_hdl->axiRd3_arready(axiRd3_hdl_if.arready);
        dut_hdl->axiRd3_rdata(axiRd3_hdl_if.rdata);
        dut_hdl->axiRd3_rid(axiRd3_hdl_if.rid);
        dut_hdl->axiRd3_rresp(axiRd3_hdl_if.rresp);
        dut_hdl->axiRd3_rlast(axiRd3_hdl_if.rlast);
        dut_hdl->axiRd3_rvalid(axiRd3_hdl_if.rvalid);
        dut_hdl->axiRd3_rready(axiRd3_hdl_if.rready);
        dut_hdl->axiWr0_awaddr(axiWr0_hdl_if.awaddr);
        dut_hdl->axiWr0_awid(axiWr0_hdl_if.awid);
        dut_hdl->axiWr0_awlen(axiWr0_hdl_if.awlen);
        dut_hdl->axiWr0_awsize(axiWr0_hdl_if.awsize);
        dut_hdl->axiWr0_awburst(axiWr0_hdl_if.awburst);
        dut_hdl->axiWr0_awvalid(axiWr0_hdl_if.awvalid);
        dut_hdl->axiWr0_awready(axiWr0_hdl_if.awready);
        dut_hdl->axiWr0_wdata(axiWr0_hdl_if.wdata);
        dut_hdl->axiWr0_wid(axiWr0_hdl_if.wid);
        dut_hdl->axiWr0_wstrb(axiWr0_hdl_if.wstrb);
        dut_hdl->axiWr0_wlast(axiWr0_hdl_if.wlast);
        dut_hdl->axiWr0_wvalid(axiWr0_hdl_if.wvalid);
        dut_hdl->axiWr0_wready(axiWr0_hdl_if.wready);
        dut_hdl->axiWr0_bresp(axiWr0_hdl_if.bresp);
        dut_hdl->axiWr0_bid(axiWr0_hdl_if.bid);
        dut_hdl->axiWr0_bvalid(axiWr0_hdl_if.bvalid);
        dut_hdl->axiWr0_bready(axiWr0_hdl_if.bready);
        dut_hdl->axiWr1_awaddr(axiWr1_hdl_if.awaddr);
        dut_hdl->axiWr1_awid(axiWr1_hdl_if.awid);
        dut_hdl->axiWr1_awlen(axiWr1_hdl_if.awlen);
        dut_hdl->axiWr1_awsize(axiWr1_hdl_if.awsize);
        dut_hdl->axiWr1_awburst(axiWr1_hdl_if.awburst);
        dut_hdl->axiWr1_awvalid(axiWr1_hdl_if.awvalid);
        dut_hdl->axiWr1_awready(axiWr1_hdl_if.awready);
        dut_hdl->axiWr1_wdata(axiWr1_hdl_if.wdata);
        dut_hdl->axiWr1_wid(axiWr1_hdl_if.wid);
        dut_hdl->axiWr1_wstrb(axiWr1_hdl_if.wstrb);
        dut_hdl->axiWr1_wlast(axiWr1_hdl_if.wlast);
        dut_hdl->axiWr1_wvalid(axiWr1_hdl_if.wvalid);
        dut_hdl->axiWr1_wready(axiWr1_hdl_if.wready);
        dut_hdl->axiWr1_bresp(axiWr1_hdl_if.bresp);
        dut_hdl->axiWr1_bid(axiWr1_hdl_if.bid);
        dut_hdl->axiWr1_bvalid(axiWr1_hdl_if.bvalid);
        dut_hdl->axiWr1_bready(axiWr1_hdl_if.bready);
        dut_hdl->axiWr2_awaddr(axiWr2_hdl_if.awaddr);
        dut_hdl->axiWr2_awid(axiWr2_hdl_if.awid);
        dut_hdl->axiWr2_awlen(axiWr2_hdl_if.awlen);
        dut_hdl->axiWr2_awsize(axiWr2_hdl_if.awsize);
        dut_hdl->axiWr2_awburst(axiWr2_hdl_if.awburst);
        dut_hdl->axiWr2_awvalid(axiWr2_hdl_if.awvalid);
        dut_hdl->axiWr2_awready(axiWr2_hdl_if.awready);
        dut_hdl->axiWr2_wdata(axiWr2_hdl_if.wdata);
        dut_hdl->axiWr2_wid(axiWr2_hdl_if.wid);
        dut_hdl->axiWr2_wstrb(axiWr2_hdl_if.wstrb);
        dut_hdl->axiWr2_wlast(axiWr2_hdl_if.wlast);
        dut_hdl->axiWr2_wvalid(axiWr2_hdl_if.wvalid);
        dut_hdl->axiWr2_wready(axiWr2_hdl_if.wready);
        dut_hdl->axiWr2_bresp(axiWr2_hdl_if.bresp);
        dut_hdl->axiWr2_bid(axiWr2_hdl_if.bid);
        dut_hdl->axiWr2_bvalid(axiWr2_hdl_if.bvalid);
        dut_hdl->axiWr2_bready(axiWr2_hdl_if.bready);
        dut_hdl->axiWr3_awaddr(axiWr3_hdl_if.awaddr);
        dut_hdl->axiWr3_awid(axiWr3_hdl_if.awid);
        dut_hdl->axiWr3_awlen(axiWr3_hdl_if.awlen);
        dut_hdl->axiWr3_awsize(axiWr3_hdl_if.awsize);
        dut_hdl->axiWr3_awburst(axiWr3_hdl_if.awburst);
        dut_hdl->axiWr3_awvalid(axiWr3_hdl_if.awvalid);
        dut_hdl->axiWr3_awready(axiWr3_hdl_if.awready);
        dut_hdl->axiWr3_wdata(axiWr3_hdl_if.wdata);
        dut_hdl->axiWr3_wid(axiWr3_hdl_if.wid);
        dut_hdl->axiWr3_wstrb(axiWr3_hdl_if.wstrb);
        dut_hdl->axiWr3_wlast(axiWr3_hdl_if.wlast);
        dut_hdl->axiWr3_wvalid(axiWr3_hdl_if.wvalid);
        dut_hdl->axiWr3_wready(axiWr3_hdl_if.wready);
        dut_hdl->axiWr3_bresp(axiWr3_hdl_if.bresp);
        dut_hdl->axiWr3_bid(axiWr3_hdl_if.bid);
        dut_hdl->axiWr3_bvalid(axiWr3_hdl_if.bvalid);
        dut_hdl->axiWr3_bready(axiWr3_hdl_if.bready);
        dut_hdl->axiStr0_tvalid(axiStr0_hdl_if.tvalid);
        dut_hdl->axiStr0_tready(axiStr0_hdl_if.tready);
        dut_hdl->axiStr0_tdata(axiStr0_hdl_if.tdata);
        dut_hdl->axiStr0_tstrb(axiStr0_hdl_if.tstrb);
        dut_hdl->axiStr0_tkeep(axiStr0_hdl_if.tkeep);
        dut_hdl->axiStr0_tlast(axiStr0_hdl_if.tlast);
        dut_hdl->axiStr0_tid(axiStr0_hdl_if.tid);
        dut_hdl->axiStr0_tdest(axiStr0_hdl_if.tdest);
        dut_hdl->axiStr0_tuser(axiStr0_hdl_if.tuser);
        dut_hdl->axiStr1_tvalid(axiStr1_hdl_if.tvalid);
        dut_hdl->axiStr1_tready(axiStr1_hdl_if.tready);
        dut_hdl->axiStr1_tdata(axiStr1_hdl_if.tdata);
        dut_hdl->axiStr1_tstrb(axiStr1_hdl_if.tstrb);
        dut_hdl->axiStr1_tkeep(axiStr1_hdl_if.tkeep);
        dut_hdl->axiStr1_tlast(axiStr1_hdl_if.tlast);
        dut_hdl->axiStr1_tid(axiStr1_hdl_if.tid);
        dut_hdl->axiStr1_tdest(axiStr1_hdl_if.tdest);
        dut_hdl->axiStr1_tuser(axiStr1_hdl_if.tuser);
        dut_hdl->clk(clk);
        dut_hdl->rst_n(rst_n);

        axiRd0_bfm.if_p(axiRd0);
        axiRd0_bfm.hdl_if_p(axiRd0_hdl_if);
        axiRd0_bfm.clk(clk);
        axiRd0_bfm.rst_n(rst_n);

        axiRd1_bfm.if_p(axiRd1);
        axiRd1_bfm.hdl_if_p(axiRd1_hdl_if);
        axiRd1_bfm.clk(clk);
        axiRd1_bfm.rst_n(rst_n);

        axiRd2_bfm.if_p(axiRd2);
        axiRd2_bfm.hdl_if_p(axiRd2_hdl_if);
        axiRd2_bfm.clk(clk);
        axiRd2_bfm.rst_n(rst_n);

        axiRd3_bfm.if_p(axiRd3);
        axiRd3_bfm.hdl_if_p(axiRd3_hdl_if);
        axiRd3_bfm.clk(clk);
        axiRd3_bfm.rst_n(rst_n);

        axiWr0_bfm.if_p(axiWr0);
        axiWr0_bfm.hdl_if_p(axiWr0_hdl_if);
        axiWr0_bfm.clk(clk);
        axiWr0_bfm.rst_n(rst_n);

        axiWr1_bfm.if_p(axiWr1);
        axiWr1_bfm.hdl_if_p(axiWr1_hdl_if);
        axiWr1_bfm.clk(clk);
        axiWr1_bfm.rst_n(rst_n);

        axiWr2_bfm.if_p(axiWr2);
        axiWr2_bfm.hdl_if_p(axiWr2_hdl_if);
        axiWr2_bfm.clk(clk);
        axiWr2_bfm.rst_n(rst_n);

        axiWr3_bfm.if_p(axiWr3);
        axiWr3_bfm.hdl_if_p(axiWr3_hdl_if);
        axiWr3_bfm.clk(clk);
        axiWr3_bfm.rst_n(rst_n);

        axiStr0_bfm.if_p(axiStr0);
        axiStr0_bfm.hdl_if_p(axiStr0_hdl_if);
        axiStr0_bfm.clk(clk);
        axiStr0_bfm.rst_n(rst_n);

        axiStr1_bfm.if_p(axiStr1);
        axiStr1_bfm.hdl_if_p(axiStr1_hdl_if);
        axiStr1_bfm.clk(clk);
        axiStr1_bfm.rst_n(rst_n);

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

    axi_read_hdl_if<sc_bv<32>, sc_bv<32>> axiRd0_hdl_if;
    axi_read_hdl_if<sc_bv<32>, sc_bv<32>> axiRd1_hdl_if;
    axi_read_hdl_if<sc_bv<32>, sc_bv<32>> axiRd2_hdl_if;
    axi_read_hdl_if<sc_bv<32>, sc_bv<32>> axiRd3_hdl_if;
    axi_write_hdl_if<sc_bv<32>, sc_bv<32>, sc_bv<4>> axiWr0_hdl_if;
    axi_write_hdl_if<sc_bv<32>, sc_bv<32>, sc_bv<4>> axiWr1_hdl_if;
    axi_write_hdl_if<sc_bv<32>, sc_bv<32>, sc_bv<4>> axiWr2_hdl_if;
    axi_write_hdl_if<sc_bv<32>, sc_bv<32>, sc_bv<4>> axiWr3_hdl_if;
    axi4_stream_hdl_if<sc_bv<32>, sc_bv<32>, sc_bv<32>, sc_bv<32>> axiStr0_hdl_if;
    axi4_stream_hdl_if<sc_bv<32>, sc_bv<32>, sc_bv<32>, sc_bv<32>> axiStr1_hdl_if;

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

#endif // CONSUMER_HDL_SC_WRAPPER_H_
