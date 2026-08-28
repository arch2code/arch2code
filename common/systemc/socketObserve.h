// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef SOCKET_OBSERVE_H
#define SOCKET_OBSERVE_H

#include "logging.h"
#include "socketFactory.h"
#include "socketSync.h"
#include "socketTransport.h"
#include "systemc.h"

#include <cstdint>
#include <cstring>
#include <format>
#include <string>

#pragma pack(push, 1)
struct socket_apb_obs_st {
    uint64_t sc_time_ns;
    uint8_t is_write;
    uint8_t wait_cycles;       // access-phase cycles with PREADY low (0 = no wait states)
    uint8_t wait_cycles_valid; // 1 if counted at pin BFM; 0 if TLM socket placeholder
    uint8_t pad;
    uint32_t address;
    uint32_t data;
};

struct socket_axi_rd_obs_req_st {
    uint64_t sc_time_ns;
    uint8_t arid;
    uint8_t pad0[3];
    uint32_t araddr;
    uint8_t arlen;
    uint8_t arsize;
    uint8_t arburst;
    uint8_t pad1;
};
struct socket_axi_rd_obs_resp_st {
    uint64_t sc_time_ns;
    uint8_t rid;
    uint8_t rresp;
    uint8_t pad[2];
    uint8_t data_preview[SOCKET_AXI_OBS_PREVIEW_BYTES];
};
struct socket_axi_wr_obs_req_st {
    uint64_t sc_time_ns;
    uint8_t awid;
    uint8_t pad0[3];
    uint32_t awaddr;
    uint8_t awlen;
    uint8_t awsize;
    uint8_t awburst;
    uint8_t pad1;
    uint8_t data_preview[SOCKET_AXI_OBS_PREVIEW_BYTES];
    // Per-beat write strobes (index 0 .. awlen). Unused entries are zero.
    uint16_t strb[SOCKET_AXI_BURST_BYTES / 16];
};
struct socket_axi_wr_obs_resp_st {
    uint64_t sc_time_ns;
    uint8_t bid;
    uint8_t bresp;
    uint8_t pad[2];
};

struct socket_irq_obs_st {
    uint64_t sc_time_ns;
    uint8_t irq;
    uint8_t pad[7];
};

// DMA STATUS register sample (pushed on dma_irq_if_obs alongside IRQ observes).
struct socket_status_obs_st {
    uint64_t sc_time_ns;
    uint8_t ready;
    uint8_t busy;
    uint8_t done;
    uint8_t err;
    uint8_t pad[4];
};

// CTRL.START sample (pushed on dma_irq_if_obs for self-clear timing checks).
struct socket_ctrl_obs_st {
    uint64_t sc_time_ns;
    uint8_t start;
    uint8_t pad[7];
};
#pragma pack(pop)

static_assert(sizeof(socket_apb_obs_st) == 20, "socket_apb_obs_st wire layout");
static_assert(sizeof(socket_axi_rd_obs_req_st) == 20, "socket_axi_rd_obs_req_st wire layout");
static_assert(sizeof(socket_axi_rd_obs_resp_st) == 28, "socket_axi_rd_obs_resp_st wire layout");
static_assert(sizeof(socket_axi_wr_obs_req_st) == 548, "socket_axi_wr_obs_req_st wire layout");
static_assert(sizeof(socket_axi_wr_obs_resp_st) == 12, "socket_axi_wr_obs_resp_st wire layout");
static_assert(sizeof(socket_irq_obs_st) == 16, "socket_irq_obs_st wire layout");
static_assert(sizeof(socket_status_obs_st) == 16, "socket_status_obs_st wire layout");
static_assert(sizeof(socket_ctrl_obs_st) == 16, "socket_ctrl_obs_st wire layout");

inline uint64_t socket_sc_time_ns()
{
    return socketSyncObserveTimeNs();
}

inline void socket_observe_push(const std::string &interface_name, uint8_t msg_type, const void *payload,
                                uint16_t len)
{
    const std::string obs_name = interface_name + "_obs";
    const int fd = socketFactory::getFd(obs_name);
    if (fd >= 0) {
        (void)socket_send_msg(fd, msg_type, payload, len);
    }
}

inline void socket_observe_apb_push(const std::string &interface_name, uint8_t msg_type,
                                    const socket_apb_obs_st &obs)
{
    socket_observe_push(interface_name, msg_type, &obs, static_cast<uint16_t>(sizeof(obs)));
}

inline void socket_observe_apb_req(const std::string &interface_name, bool is_write, uint32_t addr,
                                   uint32_t wdata)
{
    socket_apb_obs_st obs{};
    obs.sc_time_ns = socket_sc_time_ns();
    obs.is_write = is_write ? 1 : 0;
    obs.wait_cycles = 0;
    obs.wait_cycles_valid = 0;
    obs.address = addr;
    obs.data = is_write ? wdata : 0;

    logging::GetInstance().logDirect(std::format(
        "APB_OBS {} REQ @ {}ns {} addr={:#x} data={:#x}",
        interface_name,
        obs.sc_time_ns,
        is_write ? "WRITE" : "READ",
        addr,
        obs.data), LOG_NORMAL);

    socket_observe_apb_push(interface_name, MSG_APB_OBS_REQ, obs);
}

inline void socket_observe_apb_resp(const std::string &interface_name, bool is_write, uint32_t addr,
                                    uint32_t rdata, uint8_t wait_cycles = 0,
                                    bool wait_cycles_valid = false)
{
    socket_apb_obs_st obs{};
    obs.sc_time_ns = socket_sc_time_ns();
    obs.is_write = is_write ? 1 : 0;
    obs.wait_cycles = wait_cycles;
    obs.wait_cycles_valid = wait_cycles_valid ? 1 : 0;
    obs.address = addr;
    obs.data = rdata;

    logging::GetInstance().logDirect(std::format(
        "APB_OBS {} RESP @ {}ns {} addr={:#x} data={:#x} wait_cycles={}{}",
        interface_name,
        obs.sc_time_ns,
        is_write ? "WRITE" : "READ",
        addr,
        rdata,
        wait_cycles,
        wait_cycles_valid ? "" : " (n/a)"), LOG_NORMAL);

    socket_observe_apb_push(interface_name, MSG_APB_OBS_RESP, obs);
}

inline void socket_observe_axi_rd_req(const std::string &interface_name, uint8_t arid, uint32_t araddr,
                                      uint8_t arlen, uint8_t arsize, uint8_t arburst)
{
    socket_axi_rd_obs_req_st obs{};
    obs.sc_time_ns = socket_sc_time_ns();
    obs.arid = arid;
    obs.araddr = araddr;
    obs.arlen = arlen;
    obs.arsize = arsize;
    obs.arburst = arburst;

    logging::GetInstance().logDirect(std::format(
        "AXI_RD_OBS {} REQ @ {}ns arid={} araddr={:#x} arlen={} arsize={} arburst={}",
        interface_name,
        obs.sc_time_ns,
        arid,
        araddr,
        arlen,
        arsize,
        arburst), LOG_NORMAL);

    socket_observe_push(interface_name, MSG_AXI_RD_OBS_REQ, &obs, static_cast<uint16_t>(sizeof(obs)));
}

inline void socket_observe_axi_rd_resp(const std::string &interface_name, uint8_t rid, uint8_t rresp,
                                       const uint8_t *burst_data)
{
    socket_axi_rd_obs_resp_st obs{};
    obs.sc_time_ns = socket_sc_time_ns();
    obs.rid = rid;
    obs.rresp = rresp;
    if (burst_data != nullptr) {
        std::memcpy(obs.data_preview, burst_data, SOCKET_AXI_OBS_PREVIEW_BYTES);
    }

    logging::GetInstance().logDirect(std::format(
        "AXI_RD_OBS {} RESP @ {}ns rid={} rresp={} preview={:02x}{:02x}{:02x}{:02x}...",
        interface_name,
        obs.sc_time_ns,
        rid,
        rresp,
        obs.data_preview[0],
        obs.data_preview[1],
        obs.data_preview[2],
        obs.data_preview[3]), LOG_NORMAL);

    socket_observe_push(interface_name, MSG_AXI_RD_OBS_RESP, &obs, static_cast<uint16_t>(sizeof(obs)));
}

inline void socket_observe_axi_wr_req(const std::string &interface_name, uint8_t awid, uint32_t awaddr,
                                      uint8_t awlen, uint8_t awsize, uint8_t awburst, const uint8_t *burst_data,
                                      const uint16_t *burst_strb = nullptr)
{
    socket_axi_wr_obs_req_st obs{};
    obs.sc_time_ns = socket_sc_time_ns();
    obs.awid = awid;
    obs.awaddr = awaddr;
    obs.awlen = awlen;
    obs.awsize = awsize;
    obs.awburst = awburst;
    if (burst_data != nullptr) {
        std::memcpy(obs.data_preview, burst_data, SOCKET_AXI_OBS_PREVIEW_BYTES);
    }
    const unsigned beat_count = static_cast<unsigned>(awlen) + 1u;
    if (burst_strb != nullptr && beat_count <= (SOCKET_AXI_BURST_BYTES / 16)) {
        std::memcpy(obs.strb, burst_strb, beat_count * sizeof(uint16_t));
    }

    logging::GetInstance().logDirect(std::format(
        "AXI_WR_OBS {} REQ @ {}ns awid={} awaddr={:#x} awlen={} awsize={} awburst={} "
        "strb0={:#06x} preview={:02x}{:02x}{:02x}{:02x}...",
        interface_name,
        obs.sc_time_ns,
        awid,
        awaddr,
        awlen,
        awsize,
        awburst,
        obs.strb[0],
        obs.data_preview[0],
        obs.data_preview[1],
        obs.data_preview[2],
        obs.data_preview[3]), LOG_NORMAL);

    socket_observe_push(interface_name, MSG_AXI_WR_OBS_REQ, &obs, static_cast<uint16_t>(sizeof(obs)));
}

inline void socket_observe_axi_wr_resp(const std::string &interface_name, uint8_t bid, uint8_t bresp)
{
    socket_axi_wr_obs_resp_st obs{};
    obs.sc_time_ns = socket_sc_time_ns();
    obs.bid = bid;
    obs.bresp = bresp;

    logging::GetInstance().logDirect(std::format(
        "AXI_WR_OBS {} RESP @ {}ns bid={} bresp={}",
        interface_name,
        obs.sc_time_ns,
        bid,
        bresp), LOG_NORMAL);

    socket_observe_push(interface_name, MSG_AXI_WR_OBS_RESP, &obs, static_cast<uint16_t>(sizeof(obs)));
}

inline void socket_observe_irq(const std::string &interface_name, bool irq)
{
    socket_irq_obs_st obs{};
    obs.sc_time_ns = socket_sc_time_ns();
    obs.irq = irq ? 1 : 0;

    logging::GetInstance().logDirect(std::format(
        "IRQ_OBS {} @ {}ns irq={}",
        interface_name,
        obs.sc_time_ns,
        obs.irq), LOG_NORMAL);

    socket_observe_push(interface_name, MSG_IRQ_OBS, &obs, static_cast<uint16_t>(sizeof(obs)));
}

inline void socket_observe_status(const std::string &interface_name, bool ready, bool busy, bool done,
                                  bool err)
{
    socket_status_obs_st obs{};
    obs.sc_time_ns = socket_sc_time_ns();
    obs.ready = ready ? 1 : 0;
    obs.busy = busy ? 1 : 0;
    obs.done = done ? 1 : 0;
    obs.err = err ? 1 : 0;

    logging::GetInstance().logDirect(std::format(
        "STATUS_OBS {} @ {}ns ready={} busy={} done={} err={}",
        interface_name,
        obs.sc_time_ns,
        obs.ready,
        obs.busy,
        obs.done,
        obs.err), LOG_NORMAL);

    socket_observe_push(interface_name, MSG_STATUS_OBS, &obs, static_cast<uint16_t>(sizeof(obs)));
}

inline void socket_observe_ctrl(const std::string &interface_name, bool start)
{
    socket_ctrl_obs_st obs{};
    obs.sc_time_ns = socket_sc_time_ns();
    obs.start = start ? 1 : 0;

    logging::GetInstance().logDirect(std::format(
        "CTRL_OBS {} @ {}ns start={}",
        interface_name,
        obs.sc_time_ns,
        obs.start), LOG_NORMAL);

    socket_observe_push(interface_name, MSG_CTRL_OBS, &obs, static_cast<uint16_t>(sizeof(obs)));
}

#endif // SOCKET_OBSERVE_H
