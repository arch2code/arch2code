#ifndef AHB_BFM_H_
#define AHB_BFM_H_

// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "systemc.h"
#include "ahb_channel.h"
#include "q_assert.h"

#include <cstdint>
#include <format>

// AHB-Lite pins of one link. The channel carries word transfers only, so both
// BFMs use HSIZE 2 and treat HTRANS NONSEQ and SEQ alike as a single transfer.
template<typename VL_ADDR_T, typename VL_DATA_T>
struct ahb_hdl_if: public sc_interface {
    sc_signal<bool> hsel;
    sc_signal<VL_ADDR_T> haddr;
    sc_signal<sc_bv<2>> htrans;
    sc_signal<bool> hwrite;
    sc_signal<sc_bv<3>> hsize;
    sc_signal<VL_DATA_T> hwdata;
    sc_signal<bool> hready;
    sc_signal<bool> hreadyout;
    sc_signal<bool> hresp;
    sc_signal<VL_DATA_T> hrdata;
};

static constexpr unsigned AHB_HTRANS_NONSEQ = 2;
static constexpr unsigned AHB_HSIZE_WORD = 2;

// The RTL is the master: each transfer it starts becomes a response-aware
// request on if_p. HREADYOUT is low while the model works on a request. A
// read goes to the model on the edge that takes its address phase, so a
// model that answers in that timestep adds no wait state. A write's HWDATA
// goes on the wire after that edge, and the BFM reads it at the falling edge,
// so a model that answers there adds no wait state. This assumes the RTL
// drives HWDATA from rising-edge flops, so it has settled by then; AHB holds
// it through the data phase. An address phase in the last cycle of a data
// phase is taken as the next transfer.
template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class ahb_src_bfm: public sc_module {

public:

    ahb_out<ADDR_T, DATA_T> if_p;
    sc_port<ahb_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (ahb_src_bfm);

    ahb_src_bfm(sc_module_name modulename) {
        SC_THREAD(bfm_driver_thread);
    }

    // Reads the pins as they were before the edge that woke the caller.
    bool addressPhase(ADDR_T &addr, bool &is_write) {
        if (!(hdl_if_p->hsel && hdl_if_p->htrans.read()[1].to_bool() && hdl_if_p->hready)) {
            return false;
        }
        addr.sc_unpack(hdl_if_p->haddr);
        Q_ASSERT_CTX(hdl_if_p->hsize.read().to_uint() == AHB_HSIZE_WORD, name(),
                     std::format("HSIZE {} at address 0x{:x}: a model AHB slave takes word transfers only",
                                 hdl_if_p->hsize.read().to_uint(), (uint64_t)addr._getAddress()));
        is_write = hdl_if_p->hwrite;
        return true;
    }

    void bfm_driver_thread() {
        hdl_if_p->hreadyout = true;
        hdl_if_p->hresp = false;
        hdl_if_p->hrdata = VL_DATA_T(0);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            ADDR_T addr;
            bool is_write = false;
            wait(clk.posedge_event());
            bool started = addressPhase(addr, is_write);
            while (started) {
                hdl_if_p->hreadyout = false;
                DATA_T data;
                if (is_write) {
                    wait(clk.negedge_event());
                    data.sc_unpack(hdl_if_p->hwdata);
                }
                const bool error = if_p->requestWithResponse(is_write, addr, data);
                if (error) {
                    hdl_if_p->hresp = true;
                    wait(clk.posedge_event());
                }
                hdl_if_p->hreadyout = true;
                if (!is_write) {
                    hdl_if_p->hrdata = VL_DATA_T(data.sc_pack());
                }
                wait(clk.posedge_event());
                hdl_if_p->hresp = false;
                hdl_if_p->hrdata = VL_DATA_T(0);
                started = addressPhase(addr, is_write);
            }
        }
    }

};

// The RTL is the slave: each request received on if_p becomes one transfer,
// an address phase and then a data phase that lasts until HREADYOUT is high.
// The slave's HREADY input follows its HREADYOUT, as on a one-slave bus.
// reqReceive() releases a posted write, so the next request's address phase
// runs alongside the write's data phase. A read or a response-aware write
// holds the channel until complete(), so the next request starts after it.
template<typename ADDR_T, typename DATA_T, typename VL_ADDR_T, typename VL_DATA_T>
class ahb_dst_bfm: public sc_module {

public:

    ahb_in<ADDR_T, DATA_T> if_p;
    sc_port<ahb_hdl_if<VL_ADDR_T, VL_DATA_T>> hdl_if_p;

    sc_in<bool> clk;
    sc_in<bool> rst_n;

    SC_HAS_PROCESS (ahb_dst_bfm);

    ahb_dst_bfm(sc_module_name modulename) {
        SC_THREAD(address_thread);
        SC_THREAD(data_thread);
    }

    void end_of_elaboration() override {
        sc_spawn_options opts;
        opts.spawn_method();
        opts.set_sensitivity(&hdl_if_p->hreadyout.value_changed_event());
        sc_spawn([this]() { hdl_if_p->hready = hdl_if_p->hreadyout.read(); }, "hready_follows_hreadyout", &opts);
    }

    // Drives each address phase until an edge with HREADY, which starts its
    // data phase.
    void address_thread() {
        hdl_if_p->hsel = false;
        hdl_if_p->htrans = sc_bv<2>(0);
        hdl_if_p->hsize = sc_bv<3>(AHB_HSIZE_WORD);
        do { wait(clk.posedge_event()); } while (!rst_n);
        while (true) {
            ADDR_T addr;
            DATA_T data;
            bool is_write;
            if_p->reqReceive(is_write, addr, data);
            const bool posted = is_write && !if_p->receivedWantsResponse();
            hdl_if_p->hsel = true;
            hdl_if_p->htrans = sc_bv<2>(AHB_HTRANS_NONSEQ);
            hdl_if_p->haddr = addr.sc_pack();
            hdl_if_p->hwrite = is_write;
            do { wait(clk.posedge_event()); } while (!hdl_if_p->hready);
            hdl_if_p->hsel = false;
            hdl_if_p->htrans = sc_bv<2>(0);
            hdl_if_p->haddr = VL_ADDR_T(0);
            hdl_if_p->hwrite = false;
            hdl_if_p->hwdata = is_write ? VL_DATA_T(data.sc_pack()) : VL_DATA_T(0);
            data_phase = {is_write, posted, data};
            data_pending = true;
            data_start.notify(SC_ZERO_TIME);
            if (!posted) {
                wait(data_done);
            }
        }
    }

    // Ends each data phase on an edge with HREADYOUT. complete() acts on the
    // last request received, which after a posted write may already be the
    // next one, so the thread does not complete a posted write.
    void data_thread() {
        while (true) {
            while (!data_pending) {
                wait(data_start);
            }
            data_pending = false;
            dataPhase phase = data_phase;
            do { wait(clk.posedge_event()); } while (!hdl_if_p->hreadyout);
            if (phase.posted) {
                continue;
            }
            if (!phase.is_write) {
                phase.data.sc_unpack(hdl_if_p->hrdata);
            }
            if_p->complete(phase.data, hdl_if_p->hresp);
            data_done.notify();
        }
    }

private:
    struct dataPhase {
        bool is_write;
        bool posted;
        DATA_T data;
    };
    dataPhase data_phase{};
    bool data_pending = false;
    sc_event data_start;
    sc_event data_done;

};

#endif /* AHB_BFM_H_ */
