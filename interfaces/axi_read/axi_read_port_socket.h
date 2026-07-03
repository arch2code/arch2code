// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI_READ_PORT_SOCKET_H
#define AXI_READ_PORT_SOCKET_H

#include "axiCommon.h"
#include "axi_read_channel.h"
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
struct socket_axi_rd_req_st {
    uint8_t arid;
    uint8_t pad0[3];
    uint32_t araddr;
    uint8_t arlen;
    uint8_t arsize;
    uint8_t arburst;
    uint8_t pad1;
};
struct socket_axi_rd_resp_st {
    uint8_t rid;
    uint8_t rresp;
    uint8_t pad[2];
    uint8_t data[SOCKET_AXI_BURST_BYTES];
};
#pragma pack(pop)

static_assert(sizeof(socket_axi_rd_req_st) == 12, "socket_axi_rd_req_st wire layout");
static_assert(sizeof(socket_axi_rd_resp_st) == 4100, "socket_axi_rd_resp_st wire layout");

// axi_read_in: Python is AXI read slave; shell forwards DMA read bursts to Python memory.
template <class A, class D>
void port_socket(axi_read_in<A, D> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    port->setCycleTransaction(PORTTYPE_IN);

    auto resp_event = ThreadSafeEventFactory::newEvent((interface_name + "_axi_rd_resp").c_str());
    auto boundary_event = ThreadSafeEventFactory::newEvent((interface_name + "_axi_rd_boundary").c_str());
    if (socketSyncLockstepEnabled()) {
        socketSyncRegisterBoundaryEvent(boundary_event);
        socketSyncRegisterBoundaryEvent(resp_event);
    }

    std::mutex resp_mutex;
    std::queue<socket_axi_rd_resp_st> resp_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &resp_mutex, &resp_queue, resp_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        std::vector<uint8_t> recv_buf(sizeof(socket_axi_rd_resp_st));
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, recv_buf.data(), len,
                                 static_cast<uint16_t>(recv_buf.size()))) {
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
            if (msg_type == MSG_AXI_RD_RESP && len == sizeof(socket_axi_rd_resp_st)) {
                socket_axi_rd_resp_st wire_resp{};
                std::memcpy(&wire_resp, recv_buf.data(), sizeof(wire_resp));
                {
                    std::lock_guard<std::mutex> lock(resp_mutex);
                    resp_queue.push(wire_resp);
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
        axiReadAddressSt<A> addr{};
        port->receiveAddr(addr);

        if (!running->load(std::memory_order_acquire)) {
            should_shutdown = true;
            break;
        }

        while (socketSyncLockstepEnabled() && !socketSyncAtBoundary()) {
            sc_core::wait(boundary_event->default_event());
        }

        socket_axi_rd_req_st wire_req{};
        wire_req.arid = static_cast<uint8_t>(addr.arid);
        wire_req.araddr = static_cast<uint32_t>(addr.araddr.addr);
        wire_req.arlen = addr.arlen;
        wire_req.arsize = static_cast<uint8_t>(addr.arsize);
        wire_req.arburst = static_cast<uint8_t>(addr.arburst);

        socket_observe_axi_rd_req(interface_name, wire_req.arid, wire_req.araddr, wire_req.arlen,
                                wire_req.arsize, wire_req.arburst);

        if (!socket_send_msg(fd, MSG_AXI_RD_REQ, &wire_req, static_cast<uint16_t>(sizeof(wire_req)))) {
            running->store(false, std::memory_order_release);
            should_shutdown = true;
            break;
        }

        socket_axi_rd_resp_st wire_resp{};
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

        socket_observe_axi_rd_resp(interface_name, wire_resp.rid, wire_resp.rresp, wire_resp.data);

        const int num_beats = static_cast<int>(addr.arlen) + 1;
        const size_t beat_bytes = D::_byteWidth;
        for (int i = 0; i < num_beats; ++i) {
            axiReadRespSt<D> resp{};
            resp.rid = static_cast<_axiIdT>(wire_resp.rid);
            resp.rresp = static_cast<_axiResponseT>(wire_resp.rresp);
            resp.rlast = (i == num_beats - 1);
            std::memcpy(&resp.rdata, &wire_resp.data[i * beat_bytes], beat_bytes);
            port->sendDataCycle(resp);
        }
    }
    if (should_shutdown) {
        socketFactory::shutdownByName(interface_name);
    }
}

#endif // AXI_READ_PORT_SOCKET_H
