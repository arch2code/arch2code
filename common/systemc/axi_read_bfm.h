#ifndef AXI_READ_BFM_H_
#define AXI_READ_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "axi_read_channel.h"

template<typename VL_ADDR_T, typename VL_DATA_T>
struct axi_read_hdl_if: public sc_interface {

    typedef axiReadAddressSt<VL_ADDR_T> _aT;
    typedef axiReadRespSt<VL_DATA_T> _dT;

    sc_signal<sc_bv<_aT::idWidth>> arid;
    sc_signal<VL_ADDR_T> araddr;
    sc_signal<sc_bv<_aT::lenWidth>> arlen;
    sc_signal<sc_bv<_aT::sizeWidth>> arsize;
    sc_signal<sc_bv<_aT::burstWidth>> arburst;
    sc_signal<bool> arvalid;
    sc_signal<bool> arready;

    sc_signal<sc_bv<_dT::idWidth>> rid;
    sc_signal<VL_DATA_T> rdata;
    sc_signal<bool> rlast;
    sc_signal<sc_bv<_dT::respWidth>> rresp;
    sc_signal<bool> rvalid;
    sc_signal<bool> rready;

};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class axi_read_src_bfm: public sc_module {

public:

    axi_read_out<ADDR_T, DATA_T> if_p;
    sc_port<axi_read_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi_read_src_bfm);

    axi_read_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_ar_thread);
        SC_THREAD(bfm_driver_r_thread);
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi_read_channel<ADDR_T, DATA_T> *>(if_p.get_interface());
        if_p->setCycleTransaction(PORTTYPE_OUT);
    }

    void bfm_driver_ar_thread() {
        axiReadAddressSt<ADDR_T> ar_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->arready = m_chnl->m_addr_out->get_rdy();
            while (!(hdl_if_p->arvalid && hdl_if_p->arready)) {
                wait(clk.posedge_event());
                hdl_if_p->arready = m_chnl->m_addr_out->get_rdy();
            }
            ar_data.arid = (_axiIdT) hdl_if_p->arid.read().to_uint();
            ar_data.araddr.sc_unpack(hdl_if_p->araddr);
            ar_data.arlen = (uint8_t) hdl_if_p->arlen.read().to_uint();
            ar_data.arsize = (_axiSizeT) hdl_if_p->arsize.read().to_uint();
            ar_data.arburst = (_axiBurstT) hdl_if_p->arburst.read().to_uint();
            if_p->sendAddr(ar_data);
            wait(clk.posedge_event());
        }
    }

    void bfm_driver_r_thread() {
        axiReadRespSt<DATA_T> r_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->rvalid = 0;
            hdl_if_p->rid = 0;
            hdl_if_p->rdata = VL_DATA_T(0);
            hdl_if_p->rresp = 0;
            hdl_if_p->rlast = 0;
            if_p->receiveDataCycle(r_data);
            hdl_if_p->rvalid = 1;
            hdl_if_p->rid = r_data.rid;
            hdl_if_p->rdata = r_data.rdata.sc_pack();
            hdl_if_p->rresp = r_data.rresp;
            hdl_if_p->rlast = r_data.rlast;
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->rready);
        }
    }

private:

    axi_read_channel<ADDR_T, DATA_T> * m_chnl;

};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class axi_read_dst_bfm: public sc_module {

public:

    axi_read_in<ADDR_T, DATA_T> if_p;
    sc_port<axi_read_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi_read_dst_bfm);

    axi_read_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_ar_thread);
        SC_THREAD(bfm_driver_r_thread);
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi_read_channel<ADDR_T, DATA_T> *>(if_p.get_interface());
        if_p->setCycleTransaction(PORTTYPE_IN);
    }

    void bfm_driver_ar_thread() {
        axiReadAddressSt<ADDR_T> ar_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->arvalid = 0;
            hdl_if_p->arid = 0;
            hdl_if_p->araddr = VL_ADDR_T(0);
            hdl_if_p->arlen = 0;
            hdl_if_p->arsize = 0;
            hdl_if_p->arburst = 0;
            if_p->receiveAddr(ar_data);
            hdl_if_p->arvalid = 1;
            hdl_if_p->arid = ar_data.arid;
            hdl_if_p->araddr = ar_data.araddr.sc_pack();
            hdl_if_p->arlen = ar_data.arlen;
            hdl_if_p->arsize = ar_data.arsize;
            hdl_if_p->arburst = ar_data.arburst;
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->arready);
        }
    }

    void bfm_driver_r_thread() {
        axiReadRespSt<DATA_T> r_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->rready = m_chnl->m_data_out->get_rdy();
            while (!(hdl_if_p->rvalid && hdl_if_p->rready)) {
                wait(clk.posedge_event());
                hdl_if_p->rready = m_chnl->m_data_out->get_rdy();
            }
            r_data.rid = (_axiIdT) hdl_if_p->rid.read().to_uint();
            r_data.rdata.sc_unpack(hdl_if_p->rdata);
            r_data.rresp = (_axiResponseT) hdl_if_p->rresp.read().to_uint();
            r_data.rlast = (bool) hdl_if_p->rlast.read();
            if_p->sendDataCycle(r_data);
            wait(clk.posedge_event());
        }
    }

private:

    axi_read_channel<ADDR_T, DATA_T> * m_chnl;

};

#endif /* AXI_READ_BFM_H_ */
