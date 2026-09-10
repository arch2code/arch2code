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
// The wire structs above carry the AXI id as uint8_t; widen them (and their
// Python ctypes mirrors) before using a wider AXI_ID_WIDTH.
static_assert(AXI_ID_WIDTH <= 8, "the socket wire format carries AXI ids as uint8_t; widen the wire structs and their Python ctypes mirrors before using a wider AXI_ID_WIDTH");

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
    std::atomic<bool> resp_expected{false};
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &resp_mutex, &resp_queue, &resp_expected, resp_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        socket_axi_wr_resp_st recv_buf{};
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
            if (msg_type == MSG_AXI_WR_RESP && len == sizeof(socket_axi_wr_resp_st)) {
                if (!resp_expected.load(std::memory_order_acquire)) {
                    continue;
                }
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
            if (socketSyncRstN() &&
                socketSyncBpShouldStallWready(burst_index, static_cast<uint16_t>(i))) {
                // Ready stays low between receiveDataCycle calls → WREADY=0.
                socketSyncStallClocks(socketSyncBpHoldCycles());
            }
            // On ARESETn the HDL write BFM synthesizes any remaining W beats so
            // this receiveDataCycle cannot hang with WVALID stuck low.
            axiWriteDataSt<D, S> data{};
            port->receiveDataCycle(data);
            std::memcpy(&wire_req.data[i * beat_bytes], &data.wdata, beat_bytes);
            wire_req.strb[i] = static_cast<uint16_t>(data.wstrb.strobe);
        }
        if (burst_index < 0xFFFF) {
            ++burst_index;
        }

        if (!socketSyncRstN()) {
            // Local BRESP so the write BFM b_thread unblocks; skip Python.
            axiWriteRespSt resp{};
            resp.bid = static_cast<_axiIdT>(addr.awid);
            resp.bresp = AXIRESP_DECERR;
            port->sendRespCycle(resp);
            drop_orphans_and_wait_reset();
            continue;
        }

        while (socketSyncLockstepEnabled() && !socketSyncAtBoundary()) {
            if (!socketSyncRstN()) {
                break;
            }
            sc_core::wait(boundary_event->default_event() | socketSyncRstNEvent());
        }
        if (!socketSyncRstN()) {
            axiWriteRespSt resp{};
            resp.bid = static_cast<_axiIdT>(addr.awid);
            resp.bresp = AXIRESP_DECERR;
            port->sendRespCycle(resp);
            drop_orphans_and_wait_reset();
            continue;
        }

        socket_observe_axi_wr_req(interface_name, wire_req.awid, wire_req.awaddr, wire_req.awlen,
                                  wire_req.awsize, wire_req.awburst, wire_req.data, wire_req.strb);

        flush_resp_queue();
        resp_expected.store(true, std::memory_order_release);
        if (!socket_send_msg(fd, MSG_AXI_WR_REQ, &wire_req, static_cast<uint16_t>(sizeof(wire_req)))) {
            resp_expected.store(false, std::memory_order_release);
            running->store(false, std::memory_order_release);
            should_shutdown = true;
            break;
        }

        socket_axi_wr_resp_st wire_resp{};
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
            axiWriteRespSt resp{};
            resp.bid = static_cast<_axiIdT>(addr.awid);
            resp.bresp = AXIRESP_DECERR;
            port->sendRespCycle(resp);
            drop_orphans_and_wait_reset();
            continue;
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

// axi_write_out: Python is AXI write master; shell drives SC AW/W/B toward the model slave.
template <class A, class D, class S>
void port_socket(axi_write_out<A, D, S> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    port->setCycleTransaction(PORTTYPE_OUT);

    auto req_event = ThreadSafeEventFactory::newEvent((interface_name + "_axi_wr_req").c_str());
    auto boundary_event = ThreadSafeEventFactory::newEvent((interface_name + "_axi_wr_boundary").c_str());
    if (socketSyncLockstepEnabled()) {
        socketSyncRegisterBoundaryEvent(boundary_event);
        socketSyncRegisterBoundaryEvent(req_event);
    }

    std::mutex req_mutex;
    std::queue<socket_axi_wr_req_st> req_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &req_mutex, &req_queue, req_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        std::vector<uint8_t> recv_buf(sizeof(socket_axi_wr_req_st));
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
            if (msg_type == MSG_AXI_WR_REQ && len == sizeof(socket_axi_wr_req_st)) {
                socket_axi_wr_req_st wire_req{};
                std::memcpy(&wire_req, recv_buf.data(), sizeof(wire_req));
                {
                    std::lock_guard<std::mutex> lock(req_mutex);
                    req_queue.push(wire_req);
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
        socket_axi_wr_req_st wire_req{};
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

        socket_observe_axi_wr_req(interface_name, wire_req.awid, wire_req.awaddr, wire_req.awlen,
                                  wire_req.awsize, wire_req.awburst, wire_req.data, wire_req.strb);

        axiWriteAddressSt<A> addr{};
        addr.awid = static_cast<_axiIdT>(wire_req.awid);
        addr.awaddr.addr = wire_req.awaddr;
        addr.awlen = wire_req.awlen;
        addr.awsize = static_cast<_axiSizeT>(wire_req.awsize);
        addr.awburst = static_cast<_axiBurstT>(wire_req.awburst);
        port->sendAddr(addr);

        const int num_beats = static_cast<int>(wire_req.awlen) + 1;
        const size_t beat_bytes = D::_byteWidth;
        for (int i = 0; i < num_beats; ++i) {
            axiWriteDataSt<D, S> data{};
            data.wid = addr.awid;
            std::memcpy(&data.wdata, &wire_req.data[i * beat_bytes], beat_bytes);
            data.wstrb.strobe = wire_req.strb[i];
            data.wlast = (i == num_beats - 1);
            port->sendDataCycle(data);
        }

        axiWriteRespSt<> resp{};
        port->receiveRespCycle(resp);

        socket_axi_wr_resp_st wire_resp{};
        wire_resp.bid = static_cast<uint8_t>(resp.bid);
        wire_resp.bresp = static_cast<uint8_t>(resp.bresp);

        socket_observe_axi_wr_resp(interface_name, wire_resp.bid, wire_resp.bresp);

        if (!socket_send_msg(fd, MSG_AXI_WR_RESP, &wire_resp, static_cast<uint16_t>(sizeof(wire_resp)))) {
            running->store(false, std::memory_order_release);
            should_shutdown = true;
            break;
        }
    }
    if (should_shutdown) {
        socketFactory::shutdownByName(interface_name);
    }
}

#endif // AXI_WRITE_PORT_SOCKET_H
