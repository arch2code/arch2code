// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef NOTIFY_ACK_PORT_SOCKET_H
#define NOTIFY_ACK_PORT_SOCKET_H

#include "asyncEvent.h"
#include "notify_ack_channel.h"
#include "socketFactory.h"
#include "socketTransport.h"
#include "systemc.h"

#include <atomic>
#include <memory>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

template <class T = bool>
void port_socket(notify_ack_out<T> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto notify_event = ThreadSafeEventFactory::newEvent((interface_name + "_notify").c_str());

    std::mutex notify_mutex;
    std::queue<uint8_t> notify_queue;
    auto running = std::make_shared<std::atomic<bool>>(true);

    std::thread rx_thread([running, fd, &notify_mutex, &notify_queue, notify_event, interface_name]() {
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
            if (msg_type == MSG_NOTIFY && len == 0) {
                {
                    std::lock_guard<std::mutex> lock(notify_mutex);
                    notify_queue.push(0);
                }
                notify_event->notify();
            }
        }
        running->store(false, std::memory_order_release);
        notify_event->notify();
    });
    socketFactory::registerThread(interface_name, std::move(rx_thread));

    bool should_shutdown = false;
    while (running->load(std::memory_order_acquire)) {
        sc_core::wait(notify_event->default_event());
        if (!running->load(std::memory_order_acquire)) {
            should_shutdown = true;
            break;
        }

        for (;;) {
            bool have_notify = false;
            {
                std::lock_guard<std::mutex> lock(notify_mutex);
                if (!notify_queue.empty()) {
                    notify_queue.pop();
                    have_notify = true;
                }
            }
            if (!have_notify) {
                break;
            }
            port->notify();

            if (!socket_send_msg(fd, MSG_NOTIFY_ACK, nullptr, 0)) {
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

template <class T = bool>
void port_socket(notify_ack_in<T> &port, const std::string &interface_name)
{
    const int fd = socketFactory::getFd(interface_name);
    if (fd < 0) {
        return;
    }

    auto ack_event = ThreadSafeEventFactory::newEvent((interface_name + "_notify_ack").c_str());

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
            if (msg_type == MSG_NOTIFY_ACK && len == 0) {
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
        port->waitNotify();
        if (!running->load(std::memory_order_acquire)) {
            break;
        }

        if (!socket_send_msg(fd, MSG_NOTIFY, nullptr, 0)) {
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

#endif // NOTIFY_ACK_PORT_SOCKET_H
