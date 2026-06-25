// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef REQ_ACK_PORT_SOCKET_H
#define REQ_ACK_PORT_SOCKET_H

#include "asyncEvent.h"
#include "req_ack_channel.h"
#include "socketFactory.h"
#include "socketTransport.h"
#include "systemc.h"

#include <atomic>
#include <cstring>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

template <class R, class A>
void port_socket(req_ack_out<R, A> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto req_event = ThreadSafeEventFactory::newEvent((interface_name + "_req").c_str());

    std::mutex req_mutex;
    std::queue<R> req_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &req_mutex, &req_queue, req_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        R recv_buf{};
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, &recv_buf, len, static_cast<uint16_t>(sizeof(R)))) {
                // Peer closed the TCP stream (often right after MSG_SHUTDOWN). Coordinators wait on
                // peerClosed; treat EOF like shutdown for lifecycle.
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
            if (msg_type == MSG_REQ && len == sizeof(R)) {
                {
                    std::lock_guard<std::mutex> lock(req_mutex);
                    req_queue.push(recv_buf);
                }
                req_event->notify();
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
            R req_data{};
            bool have_req = false;
            {
                std::lock_guard<std::mutex> lock(req_mutex);
                if (!req_queue.empty()) {
                    req_data = std::move(req_queue.front());
                    req_queue.pop();
                    have_req = true;
                }
            }
            if (!have_req) {
                break;
            }
            A ack_data{};
            port->req(req_data, ack_data);

            if (!socket_send_msg(fd, MSG_ACK, &ack_data, static_cast<uint16_t>(sizeof(A)))) {
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

template <class R, class A>
void port_socket(req_ack_in<R, A> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto ack_event = ThreadSafeEventFactory::newEvent((interface_name + "_ack").c_str());

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
            if (msg_type == MSG_ACK && len == sizeof(A)) {
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
        R req_data{};
        port->reqReceive(req_data);
        if (!running->load(std::memory_order_acquire)) {
            break;
        }

        if (!socket_send_msg(fd, MSG_REQ, &req_data, static_cast<uint16_t>(sizeof(R)))) {
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

#endif // REQ_ACK_PORT_SOCKET_H
