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
    std::atomic<bool> resp_expected{false};
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &resp_mutex, &resp_queue, &resp_expected, resp_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        std::vector<uint8_t> recv_buf(sizeof(socket_axi_rd_resp_st));
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, recv_buf.data(), len,
                                 static_cast<uint16_t>(recv_buf.size()))) {
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
            if (msg_type == MSG_AXI_RD_RESP && len == sizeof(socket_axi_rd_resp_st)) {
                // A RESP with no outstanding REQ is an orphan from an abandoned AR.
                if (!resp_expected.load(std::memory_order_acquire)) {
                    continue;
                }
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

    auto flush_resp_queue = [&]() {
        std::lock_guard<std::mutex> lock(resp_mutex);
        while (!resp_queue.empty()) {
            resp_queue.pop();
        }
    };
    auto drop_orphans_and_wait_reset = [&]() {
        resp_expected.store(false, std::memory_order_release);
        flush_resp_queue();
        while (running->load(std::memory_order_acquire) && !socketSyncRstN()) {
            sc_core::wait(socketSyncRstNEvent());
        }
        flush_resp_queue();
    };

    bool should_shutdown = false;
    uint16_t burst_index = 0;
    while (running->load(std::memory_order_acquire)) {
        axiReadAddressSt<A> addr{};
        port->receiveAddr(addr);

        if (!running->load(std::memory_order_acquire)) {
            should_shutdown = true;
            break;
        }

        // Must watch ARESETn: waiting only on the lockstep boundary lets a
        // pre-reset AR be forwarded after the pulse, which wedges the HDL BFM.
        while (socketSyncLockstepEnabled() && !socketSyncAtBoundary()) {
            if (!socketSyncRstN()) {
                break;
            }
            sc_core::wait(boundary_event->default_event() | socketSyncRstNEvent());
        }
        if (!socketSyncRstN()) {
            const int num_beats = static_cast<int>(addr.arlen) + 1;
            for (int i = 0; i < num_beats; ++i) {
                axiReadRespSt<D> resp{};
                resp.rid = static_cast<_axiIdT>(addr.arid);
                resp.rresp = AXIRESP_DECERR;
                resp.rlast = (i == num_beats - 1);
                port->sendDataCycle(resp);
            }
            drop_orphans_and_wait_reset();
            continue;
        }

        socket_axi_rd_req_st wire_req{};
        wire_req.arid = static_cast<uint8_t>(addr.arid);
        wire_req.araddr = static_cast<uint32_t>(addr.araddr.addr);
        wire_req.arlen = addr.arlen;
        wire_req.arsize = static_cast<uint8_t>(addr.arsize);
        wire_req.arburst = static_cast<uint8_t>(addr.arburst);

        socket_observe_axi_rd_req(interface_name, wire_req.arid, wire_req.araddr, wire_req.arlen,
                                wire_req.arsize, wire_req.arburst);

        flush_resp_queue();
        resp_expected.store(true, std::memory_order_release);
        if (!socket_send_msg(fd, MSG_AXI_RD_REQ, &wire_req, static_cast<uint16_t>(sizeof(wire_req)))) {
            resp_expected.store(false, std::memory_order_release);
            running->store(false, std::memory_order_release);
            should_shutdown = true;
            break;
        }

        socket_axi_rd_resp_st wire_resp{};
        bool have_resp = false;
        bool abandoned = false;
        while (running->load(std::memory_order_acquire) && !have_resp && !abandoned) {
            if (!socketSyncRstN()) {
                abandoned = true;
                break;
            }
            sc_core::wait(resp_event->default_event() | socketSyncRstNEvent());
            if (!socketSyncRstN()) {
                abandoned = true;
                break;
            }
            {
                std::lock_guard<std::mutex> lock(resp_mutex);
                if (!resp_queue.empty()) {
                    wire_resp = std::move(resp_queue.front());
                    resp_queue.pop();
                    have_resp = true;
                }
            }
        }
        resp_expected.store(false, std::memory_order_release);
        if (abandoned || !socketSyncRstN()) {
            // Complete the outstanding AR with dummy beats so the HDL BFM unblocks.
            const int num_beats = static_cast<int>(addr.arlen) + 1;
            for (int i = 0; i < num_beats; ++i) {
                axiReadRespSt<D> resp{};
                resp.rid = static_cast<_axiIdT>(addr.arid);
                resp.rresp = AXIRESP_DECERR;
                resp.rlast = (i == num_beats - 1);
                port->sendDataCycle(resp);
            }
            drop_orphans_and_wait_reset();
            continue;
        }
        if (!have_resp) {
            should_shutdown = true;
            break;
        }

        socket_observe_axi_rd_resp(interface_name, wire_resp.rid, wire_resp.rresp, wire_resp.data);

        const int num_beats = static_cast<int>(addr.arlen) + 1;
        const size_t beat_bytes = D::_byteWidth;
        bool beat_abandon = false;
        for (int i = 0; i < num_beats; ++i) {
            if (!socketSyncRstN()) {
                beat_abandon = true;
                for (int j = i; j < num_beats; ++j) {
                    axiReadRespSt<D> resp{};
                    resp.rid = static_cast<_axiIdT>(wire_resp.rid);
                    resp.rresp = AXIRESP_DECERR;
                    resp.rlast = (j == num_beats - 1);
                    port->sendDataCycle(resp);
                }
                break;
            }
            if (socketSyncBpShouldStallRvalid(burst_index, static_cast<uint16_t>(i))) {
                // Delay before sendDataCycle keeps RVALID low on the HDL BFM.
                socketSyncStallClocks(socketSyncBpHoldCycles());
            }
            axiReadRespSt<D> resp{};
            resp.rid = static_cast<_axiIdT>(wire_resp.rid);
            resp.rresp = static_cast<_axiResponseT>(wire_resp.rresp);
            resp.rlast = (i == num_beats - 1);
            std::memcpy(&resp.rdata, &wire_resp.data[i * beat_bytes], beat_bytes);
            port->sendDataCycle(resp);
        }
        if (beat_abandon) {
            drop_orphans_and_wait_reset();
            continue;
        }
        if (burst_index < 0xFFFF) {
            ++burst_index;
        }
    }
    if (should_shutdown) {
        socketFactory::shutdownByName(interface_name);
    }
}

// axi_read_out: Python is AXI read master; shell drives SC AR/R toward the model slave.
template <class A, class D>
void port_socket(axi_read_out<A, D> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    port->setCycleTransaction(PORTTYPE_OUT);

    auto req_event = ThreadSafeEventFactory::newEvent((interface_name + "_axi_rd_req").c_str());
    auto boundary_event = ThreadSafeEventFactory::newEvent((interface_name + "_axi_rd_boundary").c_str());
    if (socketSyncLockstepEnabled()) {
        socketSyncRegisterBoundaryEvent(boundary_event);
        socketSyncRegisterBoundaryEvent(req_event);
    }

    std::mutex req_mutex;
    std::queue<socket_axi_rd_req_st> req_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &req_mutex, &req_queue, req_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        socket_axi_rd_req_st recv_buf{};
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, &recv_buf, len, static_cast<uint16_t>(sizeof(recv_buf)))) {
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
            if (msg_type == MSG_AXI_RD_REQ && len == sizeof(socket_axi_rd_req_st)) {
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
        socket_axi_rd_req_st wire_req{};
        bool have_req = false;
        while (running->load(std::memory_order_acquire) && !have_req) {
            if (!socketSyncRstN()) {
                sc_core::wait(socketSyncRstNEvent());
                continue;
            }
            while (socketSyncLockstepEnabled() && !socketSyncAtBoundary()) {
                if (!socketSyncRstN()) {
                    break;
                }
                sc_core::wait(boundary_event->default_event() | socketSyncRstNEvent());
            }
            if (!socketSyncRstN()) {
                continue;
            }
            sc_core::wait(req_event->default_event() | socketSyncRstNEvent());
            if (!socketSyncRstN()) {
                continue;
            }
            {
                std::lock_guard<std::mutex> lock(req_mutex);
                if (!req_queue.empty()) {
                    wire_req = std::move(req_queue.front());
                    req_queue.pop();
                    have_req = true;
                }
            }
        }
        if (!have_req) {
            should_shutdown = true;
            break;
        }

        socket_observe_axi_rd_req(interface_name, wire_req.arid, wire_req.araddr, wire_req.arlen,
                                  wire_req.arsize, wire_req.arburst);

        axiReadAddressSt<A> addr{};
        addr.arid = static_cast<_axiIdT>(wire_req.arid);
        addr.araddr.addr = wire_req.araddr;
        addr.arlen = wire_req.arlen;
        addr.arsize = static_cast<_axiSizeT>(wire_req.arsize);
        addr.arburst = static_cast<_axiBurstT>(wire_req.arburst);
        port->sendAddr(addr);

        const int num_beats = static_cast<int>(wire_req.arlen) + 1;
        const size_t beat_bytes = D::_byteWidth;
        socket_axi_rd_resp_st wire_resp{};
        wire_resp.rid = wire_req.arid;
        wire_resp.rresp = 0;
        for (int i = 0; i < num_beats; ++i) {
            axiReadRespSt<D> resp{};
            port->receiveDataCycle(resp);
            if (i == 0) {
                wire_resp.rid = static_cast<uint8_t>(resp.rid);
                wire_resp.rresp = static_cast<uint8_t>(resp.rresp);
            }
            std::memcpy(&wire_resp.data[i * beat_bytes], &resp.rdata, beat_bytes);
        }

        socket_observe_axi_rd_resp(interface_name, wire_resp.rid, wire_resp.rresp, wire_resp.data);

        if (!socket_send_msg(fd, MSG_AXI_RD_RESP, &wire_resp, static_cast<uint16_t>(sizeof(wire_resp)))) {
            running->store(false, std::memory_order_release);
            should_shutdown = true;
            break;
        }
    }
    if (should_shutdown) {
        socketFactory::shutdownByName(interface_name);
    }
}

#endif // AXI_READ_PORT_SOCKET_H
