// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef AXI4_STREAM_PORT_SOCKET_H
#define AXI4_STREAM_PORT_SOCKET_H

#include "asyncEvent.h"
#include "axi4_stream_channel.h"
#include "socketFactory.h"
#include "socketTransport.h"
#include "systemc.h"

#include <atomic>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

// Transactional sendInfo/receiveInfo over TCP (MSG_AXIS_BEAT / MSG_AXIS_RDY).
// Payload is the unpacked axi4StreamInfoSt layout (same as rdy_vld's T).

template <class TDATA, class TID, class TDEST, class TUSER = std::monostate>
void port_socket(axi4_stream_out<TDATA, TID, TDEST, TUSER> &port, const std::string &interface_name)
{
    using info_t = axi4StreamInfoSt<TDATA, TID, TDEST, TUSER>;
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto beat_event = ThreadSafeEventFactory::newEvent((interface_name + "_axis").c_str());

    std::mutex beat_mutex;
    std::queue<info_t> beat_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &beat_mutex, &beat_queue, beat_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        info_t recv_buf{};
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, &recv_buf, len, static_cast<uint16_t>(sizeof(info_t)))) {
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
            if (msg_type == MSG_AXIS_BEAT && len == sizeof(info_t)) {
                {
                    std::lock_guard<std::mutex> lock(beat_mutex);
                    beat_queue.push(recv_buf);
                }
                beat_event->notify();
            }
        }
        running->store(false, std::memory_order_release);
        beat_event->notify();
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    bool should_shutdown = false;
    while (running->load(std::memory_order_acquire)) {
        sc_core::wait(beat_event->default_event());
        if (!running->load(std::memory_order_acquire)) {
            should_shutdown = true;
            break;
        }

        for (;;) {
            info_t beat{};
            bool have_beat = false;
            {
                std::lock_guard<std::mutex> lock(beat_mutex);
                if (!beat_queue.empty()) {
                    beat = std::move(beat_queue.front());
                    beat_queue.pop();
                    have_beat = true;
                }
            }
            if (!have_beat) {
                break;
            }
            port->sendInfo(beat);

            if (!socket_send_msg(fd, MSG_AXIS_RDY, nullptr, 0)) {
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

template <class TDATA, class TID, class TDEST, class TUSER = std::monostate>
void port_socket(axi4_stream_in<TDATA, TID, TDEST, TUSER> &port, const std::string &interface_name)
{
    using info_t = axi4StreamInfoSt<TDATA, TID, TDEST, TUSER>;
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto rdy_event = ThreadSafeEventFactory::newEvent((interface_name + "_axis_rdy").c_str());

    std::mutex rdy_mutex;
    std::queue<uint8_t> rdy_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &rdy_mutex, &rdy_queue, rdy_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, nullptr, len, 0)) {
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
            if (msg_type == MSG_AXIS_RDY && len == 0) {
                {
                    std::lock_guard<std::mutex> lock(rdy_mutex);
                    rdy_queue.push(0);
                }
                rdy_event->notify();
            }
        }
        running->store(false, std::memory_order_release);
        rdy_event->notify();
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    bool should_shutdown = false;
    while (running->load(std::memory_order_acquire)) {
        info_t beat{};
        port->receiveInfo(beat);
        if (!running->load(std::memory_order_acquire)) {
            break;
        }

        if (!socket_send_msg(fd, MSG_AXIS_BEAT, &beat, static_cast<uint16_t>(sizeof(info_t)))) {
            running->store(false, std::memory_order_release);
            should_shutdown = true;
            break;
        }

        for (;;) {
            sc_core::wait(rdy_event->default_event());
            if (!running->load(std::memory_order_acquire)) {
                break;
            }
            bool have_rdy = false;
            {
                std::lock_guard<std::mutex> lock(rdy_mutex);
                if (!rdy_queue.empty()) {
                    rdy_queue.pop();
                    have_rdy = true;
                }
            }
            if (have_rdy) {
                break;
            }
        }
        if (!running->load(std::memory_order_acquire)) {
            break;
        }
    }

    if (should_shutdown) {
        socketFactory::shutdownByName(interface_name);
    }
}

#endif // AXI4_STREAM_PORT_SOCKET_H
