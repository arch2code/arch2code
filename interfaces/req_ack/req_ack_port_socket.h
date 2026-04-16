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

    R req_buf{};
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &req_buf, req_event, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, &req_buf, len, static_cast<uint16_t>(sizeof(R)))) {
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
                req_event->notify();
            }
        }
        running->store(false, std::memory_order_release);
        req_event->notify();
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    while (running->load(std::memory_order_acquire)) {
        sc_core::wait(req_event->default_event());
        if (!running->load(std::memory_order_acquire)) {
            break;
        }

        R req_data = req_buf;
        A ack_data{};
        port->req(req_data, ack_data);

        if (!socket_send_msg(fd, MSG_ACK, &ack_data, static_cast<uint16_t>(sizeof(A)))) {
            running->store(false, std::memory_order_release);
            break;
        }
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

    A ack_buf{};
    auto running = std::make_shared<std::atomic<bool>>(true);

    port->bindSocketBridgeLiveness(running.get());

    std::thread rx_thread([running, fd, &ack_buf, ack_event, &port, interface_name]() {
        uint8_t msg_type = 0;
        uint16_t len = 0;
        while (running->load(std::memory_order_acquire)) {
            if (!socket_recv_msg(fd, msg_type, &ack_buf, len, static_cast<uint16_t>(sizeof(A)))) {
                running->store(false, std::memory_order_release);
                port->requestReaderWakeFromExternalThread();
                socketFactory::notifyPeerClosed(interface_name);
                break;
            }
            if (msg_type == MSG_SHUTDOWN) {
                running->store(false, std::memory_order_release);
                port->requestReaderWakeFromExternalThread();
                socketFactory::notifyPeerClosed(interface_name);
                break;
            }
            if (msg_type == MSG_SYNC) {
                continue;
            }
            if (msg_type == MSG_ACK && len == sizeof(A)) {
                ack_event->notify();
            }
        }
        running->store(false, std::memory_order_release);
        ack_event->notify();
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    while (running->load(std::memory_order_acquire)) {
        R req_data{};
        port->reqReceive(req_data);
        if (!running->load(std::memory_order_acquire)) {
            break;
        }

        if (!socket_send_msg(fd, MSG_REQ, &req_data, static_cast<uint16_t>(sizeof(R)))) {
            running->store(false, std::memory_order_release);
            break;
        }

        sc_core::wait(ack_event->default_event());
        if (!running->load(std::memory_order_acquire)) {
            break;
        }

        A ack_data = ack_buf;
        port->ack(ack_data);
    }

    port->bindSocketBridgeLiveness(nullptr);
}

#endif // REQ_ACK_PORT_SOCKET_H
