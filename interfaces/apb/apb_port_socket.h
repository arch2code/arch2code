// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef APB_PORT_SOCKET_H
#define APB_PORT_SOCKET_H

#include "apb_channel.h"
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

#pragma pack(push, 1)
struct socket_apb_req_st {
    uint8_t is_write;
    uint8_t pad[3];
    uint32_t address;
    uint32_t data;
};
struct socket_apb_ack_st {
    uint32_t data;
    uint8_t pslverr;
    uint8_t pad[3];
};
#pragma pack(pop)

static_assert(sizeof(socket_apb_req_st) == 12, "socket_apb_req_st wire layout");
static_assert(sizeof(socket_apb_ack_st) == 8, "socket_apb_ack_st wire layout");

// DMA regs decode paddr[4:0] (axi_dma_top_regs). Unmapped → PSLVERR on the ACK
// (TLM writes complete before the slave can return status; match RTL decode here).
inline bool socket_apb_dma_unmapped(uint32_t address)
{
    switch (address & 0x1fu) {
    case 0x00u:
    case 0x04u:
    case 0x08u:
    case 0x0cu:
    case 0x10u:
    case 0x14u:
    case 0x18u:
        return false;
    default:
        return true;
    }
}
// apb_out: Python is APB master; shell forwards to SystemC slaves via port->request().
template <class R, class D>
void port_socket(apb_out<R, D> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto req_event = ThreadSafeEventFactory::newEvent((interface_name + "_apb_req").c_str());
    if (socketSyncLockstepEnabled()) {
        socketSyncRegisterApbReqEvent(req_event);
    }

    std::mutex req_mutex;
    std::queue<socket_apb_req_st> req_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &req_mutex, &req_queue, req_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        socket_apb_req_st recv_buf{};
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, &recv_buf, len, static_cast<uint16_t>(sizeof(socket_apb_req_st)))) {
                running->store(false, std::memory_order_release);
                socketFactory::notifyPeerClosed(interface_name);
                break;
            }
            if (msg_type == MSG_SHUTDOWN) {
                running->store(false, std::memory_order_release);
                socketFactory::notifyPeerClosed(interface_name);
                break;
            }
            if (msg_type == MSG_SYNC) {
                continue;
            }
            if (msg_type == MSG_APB_REQ && len == sizeof(socket_apb_req_st)) {
                {
                    std::lock_guard<std::mutex> lock(req_mutex);
                    req_queue.push(recv_buf);
                }
                if (!socketSyncLockstepEnabled()) {
                    req_event->notify();
                } else if (socketSyncAtBoundary()) {
                    req_event->notify();
                }
            }
        }
        running->store(false, std::memory_order_release);
        req_event->notify();
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    bool should_shutdown = false;
    while (running->load(std::memory_order_acquire)) {
        sc_core::wait(req_event->default_event());
        if (!running->load(std::memory_order_acquire)) {
            should_shutdown = true;
            break;
        }

        for (;;) {
            socket_apb_req_st wire_req{};
            bool have_req = false;
            {
                std::lock_guard<std::mutex> lock(req_mutex);
                if (!req_queue.empty()) {
                    wire_req = std::move(req_queue.front());
                    req_queue.pop();
                    have_req = true;
                }
            }
            if (!have_req) {
                break;
            }

            const bool is_write = wire_req.is_write != 0;
            R addr{};
            D data{};
            addr.address = wire_req.address;
            data.data = wire_req.data;

            socket_observe_apb_req(interface_name, is_write, wire_req.address, wire_req.data);

            port->request(is_write, addr, data);

            socket_observe_apb_resp(interface_name, is_write, wire_req.address, data.data);

            socket_apb_ack_st wire_ack{};
            wire_ack.data = data.data;
            wire_ack.pslverr = socket_apb_dma_unmapped(wire_req.address) ? 1 : 0;
            if (!socket_send_msg(fd, MSG_APB_ACK, &wire_ack, static_cast<uint16_t>(sizeof(socket_apb_ack_st)))) {
                running->store(false, std::memory_order_release);
                should_shutdown = true;
                break;
            }
        }
        if (should_shutdown) {
            break;
        }
    }
    if (should_shutdown) {
        socketFactory::shutdownByName(interface_name);
    }
}

#endif // APB_PORT_SOCKET_H
