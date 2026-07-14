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
    uint8_t pad[3];
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
#pragma pack(pop)

static_assert(sizeof(socket_apb_obs_st) == 20, "socket_apb_obs_st wire layout");
static_assert(sizeof(socket_axi_rd_obs_req_st) == 20, "socket_axi_rd_obs_req_st wire layout");
static_assert(sizeof(socket_axi_rd_obs_resp_st) == 28, "socket_axi_rd_obs_resp_st wire layout");
static_assert(sizeof(socket_axi_wr_obs_req_st) == 36, "socket_axi_wr_obs_req_st wire layout");
static_assert(sizeof(socket_axi_wr_obs_resp_st) == 12, "socket_axi_wr_obs_resp_st wire layout");
static_assert(sizeof(socket_irq_obs_st) == 16, "socket_irq_obs_st wire layout");

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
                                    uint32_t rdata)
{
    socket_apb_obs_st obs{};
    obs.sc_time_ns = socket_sc_time_ns();
    obs.is_write = is_write ? 1 : 0;
    obs.address = addr;
    obs.data = rdata;

    logging::GetInstance().logDirect(std::format(
        "APB_OBS {} RESP @ {}ns {} addr={:#x} data={:#x}",
        interface_name,
        obs.sc_time_ns,
        is_write ? "WRITE" : "READ",
        addr,
        rdata), LOG_NORMAL);
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
                                      uint8_t awlen, uint8_t awsize, uint8_t awburst, const uint8_t *burst_data)
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

    logging::GetInstance().logDirect(std::format(
        "AXI_WR_OBS {} REQ @ {}ns awid={} awaddr={:#x} awlen={} awsize={} awburst={} preview={:02x}{:02x}{:02x}{:02x}...",
        interface_name,
        obs.sc_time_ns,
        awid,
        awaddr,
        awlen,
        awsize,
        awburst,
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

#endif // SOCKET_OBSERVE_H
