#ifndef AXI_READ_BFM_H_
#define AXI_READ_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "axi_read_channel.h"
#include "rdy_vld_src_driver.h"
#include "optionalPayload.h"

#include <mutex>
#include <optional>

// The ARUSER and RUSER sidebands are optional, so both of each one's template
// arguments sit in the argument tail: the payload type (ARU, RU) and the
// Verilated bridge type (VL_ARUSER_T, VL_RUSER_T). Each user signal is a real
// interface signal, so the HDL boundary keeps a port for it whether or not a
// payload is bound. When none is, the bridge type defaults to the one-bit
// placeholder the SystemVerilog interface declares and nothing ever drives or
// samples it. id_t is optional too, so the ARID/RID bridge type VL_ID_T sits
// after the USER bridge types, defaulting to the 4-bit vector the SystemVerilog
// interface declares when id_t is left unbound; the ID payload type and its
// bit width sit last, defaulting to _axiIdT and 4.
template<typename VL_ADDR_T, typename VL_DATA_T,
typename VL_ARUSER_T = bool, typename VL_RUSER_T = bool, typename VL_ID_T = sc_bv<4>>
struct axi_read_hdl_if: public sc_interface {

    static constexpr unsigned int lenWidth   = 8;
    static constexpr unsigned int sizeWidth  = 3;
    static constexpr unsigned int burstWidth = 2;
    static constexpr unsigned int respWidth = 2;

    sc_signal<VL_ID_T> arid;
    sc_signal<VL_ADDR_T> araddr;
    sc_signal<sc_bv<lenWidth>> arlen;
    sc_signal<sc_bv<sizeWidth>> arsize;
    sc_signal<sc_bv<burstWidth>> arburst;
    sc_signal<VL_ARUSER_T> aruser;
    sc_signal<bool> arvalid;
    sc_signal<bool> arready;

    sc_signal<VL_ID_T> rid;
    sc_signal<VL_DATA_T> rdata;
    sc_signal<bool> rlast;
    sc_signal<sc_bv<respWidth>> rresp;
    sc_signal<VL_RUSER_T> ruser;
    sc_signal<bool> rvalid;
    sc_signal<bool> rready;

};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T,
         typename VL_ARUSER_T = bool, typename VL_RUSER_T = bool, typename VL_ID_T = sc_bv<4>,
         typename ARU = std::monostate, typename RU = std::monostate, typename ID = _axiIdT, unsigned IDW = 4>
class axi_read_src_bfm: public sc_module {

public:

    axi_read_out<ADDR_T, DATA_T, ARU, RU, ID, IDW> if_p;
    sc_port<axi_read_hdl_if<VL_ADDR_T, VL_DATA_T, VL_ARUSER_T, VL_RUSER_T, VL_ID_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi_read_src_bfm);

    axi_read_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_ar_thread);
        SC_THREAD(bfm_driver_r_thread);
        SC_METHOD(sample_edges);
        sensitive << clk.pos();
        dont_initialize();
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi_read_channel<ADDR_T, DATA_T, ARU, RU, ID, IDW> *>(if_p.get_interface());
        if_p->setCycleTransaction(PORTTYPE_OUT);
        m_ar.emplace(m_chnl->m_addr_out, clk, rst_n, hdl_if_p->arvalid, hdl_if_p->arready, [this](arT &ar_data) {
            ar_data.arid = (ID) hdl_if_p->arid.read().to_uint();
            ar_data.araddr.sc_unpack(hdl_if_p->araddr);
            ar_data.arlen = (uint8_t) hdl_if_p->arlen.read().to_uint();
            ar_data.arsize = (_axiSizeT) hdl_if_p->arsize.read().to_uint();
            ar_data.arburst = (_axiBurstT) hdl_if_p->arburst.read().to_uint();
            if constexpr (hasOptionalPayload<ARU>) { ar_data.user.sc_unpack(hdl_if_p->aruser); }
        });
    }

    void bfm_driver_ar_thread() {
        wait(SC_ZERO_TIME);
        m_ar->run([this](arT &ar_data) {
            {
                std::lock_guard<std::mutex> lock(m_pending_mutex);
                m_pending_r_beats = static_cast<int>(ar_data.arlen) + 1;
            }
            if_p->sendAddr(ar_data);
        }, [this] {
            m_ar->waitOutReset();
            return true;
        });
    }

    void sample_edges() {
        m_ar->sampleEdge();
    }

    void bfm_driver_r_thread() {
        axiReadRespSt<DATA_T, RU, ID, IDW> r_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->rvalid = 0;
            hdl_if_p->rid = VL_ID_T(0);
            hdl_if_p->rdata = VL_DATA_T(0);
            hdl_if_p->rresp = 0;
            hdl_if_p->rlast = 0;
            if constexpr (hasOptionalPayload<RU>) { hdl_if_p->ruser = VL_RUSER_T(0); }
            m_chnl->m_data_in->peek(r_data);
            // During ARESETn the port_socket drains outstanding AR with dummy
            // beats. Still drive them onto the wire (DUT ignores while reset)
            // so channel beat counts stay aligned; drop RVALID if reset.
            if (!rst_n.read()) {
                takeR(r_data);
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
            // The model's send returns at the edge where the RTL takes the beat,
            // or where reset drops it.
            takeR(r_data);
        }
    }

private:

    void takeR(axiReadRespSt<DATA_T, RU, ID, IDW> &r_data) {
        if_p->receiveDataCycle(r_data);
        std::lock_guard<std::mutex> lock(m_pending_mutex);
        if (m_pending_r_beats > 0) {
            --m_pending_r_beats;
        }
    }

    using arT = axiReadAddressSt<ADDR_T, ARU, ID, IDW>;

    axi_read_channel<ADDR_T, DATA_T, ARU, RU, ID, IDW> * m_chnl;
    std::optional<rdyVldSrcDriver<arT>> m_ar;
    std::mutex m_pending_mutex;
    int m_pending_r_beats = 0;

};

template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T,
         typename VL_ARUSER_T = bool, typename VL_RUSER_T = bool, typename VL_ID_T = sc_bv<4>,
         typename ARU = std::monostate, typename RU = std::monostate, typename ID = _axiIdT, unsigned IDW = 4>
class axi_read_dst_bfm: public sc_module {

public:

    axi_read_in<ADDR_T, DATA_T, ARU, RU, ID, IDW> if_p;
    sc_port<axi_read_hdl_if<VL_ADDR_T, VL_DATA_T, VL_ARUSER_T, VL_RUSER_T, VL_ID_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (axi_read_dst_bfm);

    axi_read_dst_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_ar_thread);
        SC_THREAD(bfm_driver_r_thread);
        SC_METHOD(sample_edges);
        sensitive << clk.pos();
        dont_initialize();
    }

    virtual void end_of_elaboration() {
        m_chnl = dynamic_cast<axi_read_channel<ADDR_T, DATA_T, ARU, RU, ID, IDW> *>(if_p.get_interface());
        if_p->setCycleTransaction(PORTTYPE_IN);
        m_r.emplace(m_chnl->m_data_out, clk, rst_n, hdl_if_p->rvalid, hdl_if_p->rready, [this](rT &r_data) {
            r_data.rid = (ID) hdl_if_p->rid.read().to_uint();
            r_data.rdata.sc_unpack(hdl_if_p->rdata);
            r_data.rresp = (_axiResponseT) hdl_if_p->rresp.read().to_uint();
            r_data.rlast = (bool) hdl_if_p->rlast.read();
            if constexpr (hasOptionalPayload<RU>) { r_data.user.sc_unpack(hdl_if_p->ruser); }
        });
    }

    void bfm_driver_ar_thread() {
        axiReadAddressSt<ADDR_T, ARU, ID, IDW> ar_data;
        wait(SC_ZERO_TIME);
        while (true) {
            hdl_if_p->arvalid = 0;
            hdl_if_p->arid = VL_ID_T(0);
            hdl_if_p->araddr = VL_ADDR_T(0);
            hdl_if_p->arlen = 0;
            hdl_if_p->arsize = 0;
            hdl_if_p->arburst = 0;
            if constexpr (hasOptionalPayload<ARU>) { hdl_if_p->aruser = VL_ARUSER_T(0); }
            m_chnl->m_addr_in->peek(ar_data);
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
            // The model's send returns at the edge where the RTL takes the beat.
            if_p->receiveAddr(ar_data);
        }
    }

    void bfm_driver_r_thread() {
        wait(SC_ZERO_TIME);
        m_r->run([this](rT &r_data) { if_p->sendDataCycle(r_data); }, [] { return false; });
    }

    void sample_edges() {
        m_r->sampleEdge();
    }

private:

    using rT = axiReadRespSt<DATA_T, RU, ID, IDW>;

    axi_read_channel<ADDR_T, DATA_T, ARU, RU, ID, IDW> * m_chnl;
    std::optional<rdyVldSrcDriver<rT>> m_r;

};

#endif /* AXI_READ_BFM_H_ */
