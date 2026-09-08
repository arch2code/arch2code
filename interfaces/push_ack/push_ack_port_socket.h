// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef PUSH_ACK_PORT_SOCKET_H
#define PUSH_ACK_PORT_SOCKET_H

#include "asyncEvent.h"
#include "push_ack_channel.h"
#include "socketFactory.h"
#include "socketTransport.h"
#include "systemc.h"

#include <atomic>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

template <class T>
void port_socket(push_ack_out<T> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto push_event = ThreadSafeEventFactory::newEvent((interface_name + "_push").c_str());

    std::mutex push_mutex;
    std::queue<T> push_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &push_mutex, &push_queue, push_event, interface_name]() {
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
            if (msg_type == MSG_PUSH && len == sizeof(T)) {
                {
                    std::lock_guard<std::mutex> lock(push_mutex);
                    push_queue.push(recv_buf);
                }
                push_event->notify();
            }
        }
        running->store(false, std::memory_order_release);
        push_event->notify();
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    bool should_shutdown = false;
    while (running->load(std::memory_order_acquire)) {
        sc_core::wait(push_event->default_event());
        if (!running->load(std::memory_order_acquire)) {
            should_shutdown = true;
            break;
        }

        for (;;) {
            T push_data{};
            bool have_push = false;
            {
                std::lock_guard<std::mutex> lock(push_mutex);
                if (!push_queue.empty()) {
                    push_data = std::move(push_queue.front());
                    push_queue.pop();
                    have_push = true;
                }
            }
            if (!have_push) {
                break;
            }
            port->push(push_data);

            if (!socket_send_msg(fd, MSG_PUSH_ACK, nullptr, 0)) {
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
void port_socket(push_ack_in<T> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto ack_event = ThreadSafeEventFactory::newEvent((interface_name + "_push_ack").c_str());

    std::mutex ack_mutex;
    std::queue<uint8_t> ack_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &ack_mutex, &ack_queue, ack_event, interface_name]() {
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
            if (msg_type == MSG_PUSH_ACK && len == 0) {
                {
                    std::lock_guard<std::mutex> lock(ack_mutex);
                    ack_queue.push(0);
                }
                ack_event->notify();
            }
        }
        running->store(false, std::memory_order_release);
        ack_event->notify();
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    bool should_shutdown = false;
    while (running->load(std::memory_order_acquire)) {
        T push_data{};
        port->pushReceive(push_data);
        if (!running->load(std::memory_order_acquire)) {
            break;
        }

        if (!socket_send_msg(fd, MSG_PUSH, &push_data, static_cast<uint16_t>(sizeof(T)))) {
            running->store(false, std::memory_order_release);
            should_shutdown = true;
            break;
        }

        for (;;) {
            sc_core::wait(ack_event->default_event());
            if (!running->load(std::memory_order_acquire)) {
                break;
            }
            bool have_ack = false;
            {
                std::lock_guard<std::mutex> lock(ack_mutex);
                if (!ack_queue.empty()) {
                    ack_queue.pop();
                    have_ack = true;
                }
            }
            if (have_ack) {
                port->ack();
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

#endif // PUSH_ACK_PORT_SOCKET_H
