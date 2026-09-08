// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef RDY_VLD_PORT_SOCKET_H
#define RDY_VLD_PORT_SOCKET_H

#include "asyncEvent.h"
#include "rdy_vld_channel.h"
#include "socketFactory.h"
#include "socketTransport.h"
#include "systemc.h"

#include <atomic>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

// Transactional write/read over TCP (MSG_VLD / MSG_RDY). Not cycle-accurate.

template <class T>
void port_socket(rdy_vld_out<T> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto vld_event = ThreadSafeEventFactory::newEvent((interface_name + "_vld").c_str());

    std::mutex vld_mutex;
    std::queue<T> vld_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &vld_mutex, &vld_queue, vld_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        T recv_buf{};
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, &recv_buf, len, static_cast<uint16_t>(sizeof(T)))) {
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
            if (msg_type == MSG_VLD && len == sizeof(T)) {
                {
                    std::lock_guard<std::mutex> lock(vld_mutex);
                    vld_queue.push(recv_buf);
                }
                vld_event->notify();
            }
        }
        running->store(false, std::memory_order_release);
        vld_event->notify();
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    bool should_shutdown = false;
    while (running->load(std::memory_order_acquire)) {
        sc_core::wait(vld_event->default_event());
        if (!running->load(std::memory_order_acquire)) {
            should_shutdown = true;
            break;
        }

        for (;;) {
            T vld_data{};
            bool have_vld = false;
            {
                std::lock_guard<std::mutex> lock(vld_mutex);
                if (!vld_queue.empty()) {
                    vld_data = std::move(vld_queue.front());
                    vld_queue.pop();
                    have_vld = true;
                }
            }
            if (!have_vld) {
                break;
            }
            port->write(vld_data);

            if (!socket_send_msg(fd, MSG_RDY, nullptr, 0)) {
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

template <class T>
void port_socket(rdy_vld_in<T> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto rdy_event = ThreadSafeEventFactory::newEvent((interface_name + "_rdy").c_str());

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
            if (msg_type == MSG_RDY && len == 0) {
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
        T vld_data{};
        port->read(vld_data);
        if (!running->load(std::memory_order_acquire)) {
            break;
        }

        if (!socket_send_msg(fd, MSG_VLD, &vld_data, static_cast<uint16_t>(sizeof(T)))) {
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

#endif // RDY_VLD_PORT_SOCKET_H
