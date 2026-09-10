#ifndef AXI_READ_BFM_H_
#define AXI_READ_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "axi_read_channel.h"
#include "optionalPayload.h"

#include <mutex>

// The ARUSER and RUSER sidebands are optional, so both of each one's template
// arguments sit in the argument tail: the payload type (ARU, RU) and the
// Verilated bridge type (VL_ARUSER_T, VL_RUSER_T). Each user signal is a real
// interface signal, so the HDL boundary keeps a port for it whether or not a
// payload is bound. When none is, the bridge type defaults to the one-bit
// placeholder the SystemVerilog interface declares and nothing ever drives or
// samples it.
template<typename VL_ADDR_T, typename VL_DATA_T,
typename VL_ARUSER_T = bool, typename VL_RUSER_T = bool>
struct axi_read_hdl_if: public sc_interface {

    static constexpr unsigned int idWidth    = axiIdWidth;
    static constexpr unsigned int lenWidth   = 8;
    static constexpr unsigned int sizeWidth  = 3;
    static constexpr unsigned int burstWidth = 2;
    static constexpr unsigned int respWidth = 2;

    sc_signal<sc_bv<idWidth>> arid;
    sc_signal<VL_ADDR_T> araddr;
    sc_signal<sc_bv<lenWidth>> arlen;
    sc_signal<sc_bv<sizeWidth>> arsize;
    sc_signal<sc_bv<burstWidth>> arburst;
    sc_signal<VL_ARUSER_T> aruser;
    sc_signal<bool> arvalid;
    sc_signal<bool> arready;

    sc_signal<sc_bv<idWidth>> rid;
    sc_signal<VL_DATA_T> rdata;
    sc_signal<bool> rlast;
    sc_signal<sc_bv<respWidth>> rresp;
    sc_signal<VL_RUSER_T> ruser;
    sc_signal<bool> rvalid;
    sc_signal<bool> rready;

};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T,
         typename VL_ARUSER_T = bool, typename VL_RUSER_T = bool,
         typename ARU = std::monostate, typename RU = std::monostate>
class axi_read_src_bfm: public sc_module {

public:

    axi_read_out<ADDR_T, DATA_T, ARU, RU> if_p;
    sc_port<axi_read_hdl_if<VL_ADDR_T, VL_DATA_T, VL_ARUSER_T, VL_RUSER_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi_read_src_bfm);

    axi_read_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_ar_thread);
        SC_THREAD(bfm_driver_r_thread);
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi_read_channel<ADDR_T, DATA_T, ARU, RU> *>(if_p.get_interface());
        if_p->setCycleTransaction(PORTTYPE_OUT);
    }

    void bfm_driver_ar_thread() {
        axiReadAddressSt<ADDR_T, ARU> ar_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->arready = m_chnl->m_addr_out->get_rdy();
            while (!(hdl_if_p->arvalid && hdl_if_p->arready)) {
                wait(clk.posedge_event());
                if (!rst_n.read()) {
                    hdl_if_p->arready = 0;
                    while (!rst_n.read()) {
                        wait(clk.posedge_event());
                    }
                    break;
                }
                hdl_if_p->arready = m_chnl->m_addr_out->get_rdy();
            }
            if (!rst_n.read() || !(hdl_if_p->arvalid && hdl_if_p->arready)) {
                continue;
            }
            ar_data.arid = (_axiIdT) hdl_if_p->arid.read().to_uint();
            ar_data.araddr.sc_unpack(hdl_if_p->araddr);
            ar_data.arlen = (uint8_t) hdl_if_p->arlen.read().to_uint();
            ar_data.arsize = (_axiSizeT) hdl_if_p->arsize.read().to_uint();
            ar_data.arburst = (_axiBurstT) hdl_if_p->arburst.read().to_uint();
            if constexpr (hasOptionalPayload<ARU>) { ar_data.user.sc_unpack(hdl_if_p->aruser); }
            {
                std::lock_guard<std::mutex> lock(m_pending_mutex);
                m_pending_r_beats = static_cast<int>(ar_data.arlen) + 1;
            }
            if_p->sendAddr(ar_data);
            wait(clk.posedge_event());
        }
    }

    void bfm_driver_r_thread() {
        axiReadRespSt<DATA_T, RU> r_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->rvalid = 0;
            hdl_if_p->rid = 0;
            hdl_if_p->rdata = VL_DATA_T(0);
            hdl_if_p->rresp = 0;
            hdl_if_p->rlast = 0;
            if constexpr (hasOptionalPayload<RU>) { hdl_if_p->ruser = VL_RUSER_T(0); }
            if_p->receiveDataCycle(r_data);
            {
                std::lock_guard<std::mutex> lock(m_pending_mutex);
                if (m_pending_r_beats > 0) {
                    --m_pending_r_beats;
                }
            }
            // During ARESETn the port_socket drains outstanding AR with dummy
            // beats. Still drive them onto the wire (DUT ignores while reset)
            // so channel beat counts stay aligned; drop RVALID if reset.
            if (!rst_n.read()) {
                hdl_if_p->rvalid = 0;
                if (r_data.rlast) {
                    std::lock_guard<std::mutex> lock(m_pending_mutex);
                    m_pending_r_beats = 0;
                }
                continue;
            }
            hdl_if_p->rvalid = 1;
            hdl_if_p->rid = r_data.rid;
            hdl_if_p->rdata = r_data.rdata.sc_pack();
            hdl_if_p->rresp = r_data.rresp;
            hdl_if_p->rlast = r_data.rlast;
            if constexpr (hasOptionalPayload<RU>) { hdl_if_p->ruser = r_data.user.sc_pack(); }
            do {
                wait(clk.posedge_event());
                if (!rst_n.read()) {
                    hdl_if_p->rvalid = 0;
                    {
                        std::lock_guard<std::mutex> lock(m_pending_mutex);
                        m_pending_r_beats = 0;
                    }
                    break;
                }
            } while (!hdl_if_p->rready);
        }
    }

private:

    axi_read_channel<ADDR_T, DATA_T, ARU, RU> * m_chnl;
    std::mutex m_pending_mutex;
    int m_pending_r_beats = 0;

};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T,
         typename VL_ARUSER_T = bool, typename VL_RUSER_T = bool,
         typename ARU = std::monostate, typename RU = std::monostate>
class axi_read_dst_bfm: public sc_module {

public:

    axi_read_in<ADDR_T, DATA_T, ARU, RU> if_p;
    sc_port<axi_read_hdl_if<VL_ADDR_T, VL_DATA_T, VL_ARUSER_T, VL_RUSER_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi_read_dst_bfm);

    axi_read_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_ar_thread);
        SC_THREAD(bfm_driver_r_thread);
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi_read_channel<ADDR_T, DATA_T, ARU, RU> *>(if_p.get_interface());
        if_p->setCycleTransaction(PORTTYPE_IN);
    }

    void bfm_driver_ar_thread() {
        axiReadAddressSt<ADDR_T, ARU> ar_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->arvalid = 0;
            hdl_if_p->arid = 0;
            hdl_if_p->araddr = VL_ADDR_T(0);
            hdl_if_p->arlen = 0;
            hdl_if_p->arsize = 0;
            hdl_if_p->arburst = 0;
            if constexpr (hasOptionalPayload<ARU>) { hdl_if_p->aruser = VL_ARUSER_T(0); }
            if_p->receiveAddr(ar_data);
            hdl_if_p->arvalid = 1;
            hdl_if_p->arid = ar_data.arid;
            hdl_if_p->araddr = ar_data.araddr.sc_pack();
            hdl_if_p->arlen = ar_data.arlen;
            hdl_if_p->arsize = ar_data.arsize;
            hdl_if_p->arburst = ar_data.arburst;
            if constexpr (hasOptionalPayload<ARU>) { hdl_if_p->aruser = ar_data.user.sc_pack(); }
            do {
                wait(clk.posedge_event());
            } while (!hdl_if_p->arready);
        }
    }

    void bfm_driver_r_thread() {
        axiReadRespSt<DATA_T, RU> r_data;
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
            if constexpr (hasOptionalPayload<RU>) { r_data.user.sc_unpack(hdl_if_p->ruser); }
            if_p->sendDataCycle(r_data);
            wait(clk.posedge_event());
        }
    }

private:

    axi_read_channel<ADDR_T, DATA_T, ARU, RU> * m_chnl;

};

#endif /* AXI_READ_BFM_H_ */
