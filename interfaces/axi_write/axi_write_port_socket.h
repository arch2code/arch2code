// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_WRITE_PORT_SOCKET_H
#define AXI_WRITE_PORT_SOCKET_H

#include "axiCommon.h"
#include "axi_write_channel.h"
#include "asyncEvent.h"
#include "socketFactory.h"
#include "socketObserve.h"
#include "socketSync.h"
#include "socketTransport.h"
#include "systemc.h"

#include <atomic>
#include <cstdint>
#include <cstring>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>
#include <vector>

#pragma pack(push, 1)
struct socket_axi_wr_req_st {
    uint8_t awid;
    uint8_t pad0[3];
    uint32_t awaddr;
    uint8_t awlen;
    uint8_t awsize;
    uint8_t awburst;
    uint8_t pad1;
    uint8_t data[SOCKET_AXI_BURST_BYTES];
    uint16_t strb[SOCKET_AXI_BURST_BYTES / 16];
};
struct socket_axi_wr_resp_st {
    uint8_t bid;
    uint8_t bresp;
    uint8_t pad[2];
};
#pragma pack(pop)

static_assert(sizeof(socket_axi_wr_req_st) == 4620, "socket_axi_wr_req_st wire layout");
static_assert(sizeof(socket_axi_wr_resp_st) == 4, "socket_axi_wr_resp_st wire layout");

// axi_write_in: Python is AXI write slave; shell forwards DMA write bursts to Python memory.
template <class A, class D, class S>
void port_socket(axi_write_in<A, D, S> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    port->setCycleTransaction(PORTTYPE_IN);

    auto resp_event = ThreadSafeEventFactory::newEvent((interface_name + "_axi_wr_resp").c_str());
    auto boundary_event = ThreadSafeEventFactory::newEvent((interface_name + "_axi_wr_boundary").c_str());
    if (socketSyncLockstepEnabled()) {
        socketSyncRegisterBoundaryEvent(boundary_event);
        socketSyncRegisterBoundaryEvent(resp_event);
    }

    std::mutex resp_mutex;
    std::queue<socket_axi_wr_resp_st> resp_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &resp_mutex, &resp_queue, resp_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        socket_axi_wr_resp_st recv_buf{};
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, &recv_buf, len, static_cast<uint16_t>(sizeof(recv_buf)))) {
                running->store(false, std::memory_order_release);
                socketFactory::shutdownByName(interface_name);
                break;
            }
            if (msg_type == MSG_SHUTDOWN) {
                running->store(false, std::memory_order_release);
                socketFactory::shutdownByName(interface_name);
                break;
            }
            if (msg_type == MSG_SYNC) {
                continue;
            }
            if (msg_type == MSG_AXI_WR_RESP && len == sizeof(socket_axi_wr_resp_st)) {
                {
                    std::lock_guard<std::mutex> lock(resp_mutex);
                    resp_queue.push(recv_buf);
                }
                if (!socketSyncLockstepEnabled()) {
                    resp_event->notify();
                } else if (socketSyncAtBoundary()) {
                    resp_event->notify();
                }
            }
        }
        running->store(false, std::memory_order_release);
        resp_event->notify();
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    bool should_shutdown = false;
    while (running->load(std::memory_order_acquire)) {
        axiWriteAddressSt<A> addr{};
        port->receiveAddr(addr);

        if (!running->load(std::memory_order_acquire)) {
            should_shutdown = true;
            break;
        }

        const int num_beats = static_cast<int>(addr.awlen) + 1;
        const size_t beat_bytes = D::_byteWidth;

        socket_axi_wr_req_st wire_req{};
        wire_req.awid = static_cast<uint8_t>(addr.awid);
        wire_req.awaddr = static_cast<uint32_t>(addr.awaddr.addr);
        wire_req.awlen = addr.awlen;
        wire_req.awsize = static_cast<uint8_t>(addr.awsize);
        wire_req.awburst = static_cast<uint8_t>(addr.awburst);

        for (int i = 0; i < num_beats; ++i) {
            axiWriteDataSt<D, S> data{};
            port->receiveDataCycle(data);
            std::memcpy(&wire_req.data[i * beat_bytes], &data.wdata, beat_bytes);
            wire_req.strb[i] = static_cast<uint16_t>(data.wstrb.strobe);
        }

        while (socketSyncLockstepEnabled() && !socketSyncAtBoundary()) {
            sc_core::wait(boundary_event->default_event());
        }

        socket_observe_axi_wr_req(interface_name, wire_req.awid, wire_req.awaddr, wire_req.awlen,
                                  wire_req.awsize, wire_req.awburst, wire_req.data);

        if (!socket_send_msg(fd, MSG_AXI_WR_REQ, &wire_req, static_cast<uint16_t>(sizeof(wire_req)))) {
            running->store(false, std::memory_order_release);
            should_shutdown = true;
            break;
        }

        socket_axi_wr_resp_st wire_resp{};
        bool have_resp = false;
        while (running->load(std::memory_order_acquire) && !have_resp) {
            sc_core::wait(resp_event->default_event());
            {
                std::lock_guard<std::mutex> lock(resp_mutex);
                if (!resp_queue.empty()) {
                    wire_resp = std::move(resp_queue.front());
                    resp_queue.pop();
                    have_resp = true;
                }
            }
        }
        if (!have_resp) {
            should_shutdown = true;
            break;
        }

        socket_observe_axi_wr_resp(interface_name, wire_resp.bid, wire_resp.bresp);

        axiWriteRespSt resp{};
        resp.bid = static_cast<_axiIdT>(wire_resp.bid);
        resp.bresp = static_cast<_axiResponseT>(wire_resp.bresp);
        port->sendRespCycle(resp);
    }
    if (should_shutdown) {
        socketFactory::shutdownByName(interface_name);
    }
}

#endif // AXI_WRITE_PORT_SOCKET_H
