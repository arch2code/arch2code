// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef POP_ACK_PORT_SOCKET_H
#define POP_ACK_PORT_SOCKET_H

#include "asyncEvent.h"
#include "pop_ack_channel.h"
#include "socketFactory.h"
#include "socketTransport.h"
#include "systemc.h"

#include <atomic>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

template <class A>
void port_socket(pop_ack_out<A> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto pop_event = ThreadSafeEventFactory::newEvent((interface_name + "_pop").c_str());

    std::mutex pop_mutex;
    std::queue<uint8_t> pop_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &pop_mutex, &pop_queue, pop_event, interface_name]() {
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
            if (msg_type == MSG_POP && len == 0) {
                {
                    std::lock_guard<std::mutex> lock(pop_mutex);
                    pop_queue.push(0);
                }
                pop_event->notify();
            }
        }
        running->store(false, std::memory_order_release);
        pop_event->notify();
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    bool should_shutdown = false;
    while (running->load(std::memory_order_acquire)) {
        sc_core::wait(pop_event->default_event());
        if (!running->load(std::memory_order_acquire)) {
            should_shutdown = true;
            break;
        }

        for (;;) {
            bool have_pop = false;
            {
                std::lock_guard<std::mutex> lock(pop_mutex);
                if (!pop_queue.empty()) {
                    pop_queue.pop();
                    have_pop = true;
                }
            }
            if (!have_pop) {
                break;
            }
            A ack_data{};
            port->pop(ack_data);

            if (!socket_send_msg(fd, MSG_POP_ACK, &ack_data, static_cast<uint16_t>(sizeof(A)))) {
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

template <class A>
void port_socket(pop_ack_in<A> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto ack_event = ThreadSafeEventFactory::newEvent((interface_name + "_pop_ack").c_str());

    std::mutex ack_mutex;
    std::queue<A> ack_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &ack_mutex, &ack_queue, ack_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        A recv_buf{};
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, &recv_buf, len, static_cast<uint16_t>(sizeof(A)))) {
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
            if (msg_type == MSG_POP_ACK && len == sizeof(A)) {
                {
                    std::lock_guard<std::mutex> lock(ack_mutex);
                    ack_queue.push(recv_buf);
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
        port->popReceive();
        if (!running->load(std::memory_order_acquire)) {
            break;
        }

        if (!socket_send_msg(fd, MSG_POP, nullptr, 0)) {
            running->store(false, std::memory_order_release);
            should_shutdown = true;
            break;
        }

        for (;;) {
            sc_core::wait(ack_event->default_event());
            if (!running->load(std::memory_order_acquire)) {
                break;
            }
            A ack_data{};
            bool have_ack = false;
            {
                std::lock_guard<std::mutex> lock(ack_mutex);
                if (!ack_queue.empty()) {
                    ack_data = std::move(ack_queue.front());
                    ack_queue.pop();
                    have_ack = true;
                }
            }
            if (have_ack) {
                port->ack(ack_data);
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

#endif // POP_ACK_PORT_SOCKET_H
