// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef SOCKET_FACTORY_H
#define SOCKET_FACTORY_H

#include "asyncEvent.h"

#include <atomic>
#include <cstdint>
#include <map>
#include <memory>
#include <string>
#include <thread>
#include <utility>
#include <vector>

class socketFactory {
public:
    static uint16_t registerInterface(const std::string &name);

    static void acceptConnection(const std::string &name);

    static void acceptAll();

    // Sends the startup MSG_SYNC on every registered connection. False when
    // any registered name has no accepted connection or the send fails.
    static bool handshakeAll();

    static uint16_t getPort(const std::string &name);

    static std::vector<std::pair<std::string, uint16_t>> getAllPorts();

    static std::string getPortString();

    static int getFd(const std::string &name);

    static void registerThread(const std::string &name, std::thread &&t);

    static std::shared_ptr<ThreadSafeEvent> getPeerClosedEvent(const std::string &name);

    // True once notifyPeerClosed() has run. Check it before waiting on the
    // peer-closed event, which keeps no state: a thread that reaches the wait
    // after the notification would wait forever.
    static bool isPeerClosed(const std::string &name);

    static void notifyPeerClosed(const std::string &name);

    static void shutdownByName(const std::string &name);

    static void shutdownAll();

private:
    struct SocketEntry {
        int listen_fd = -1;
        int conn_fd = -1;
        uint16_t port = 0;
        std::thread rx_thread;
        bool has_thread = false;
        std::shared_ptr<ThreadSafeEvent> peer_closed_event;
        // shared_ptr, not a bare atomic<bool>, so SocketEntry stays movable for
        // map[name] = std::move(ent) in registerInterface().
        std::shared_ptr<std::atomic<bool>> peer_closed = std::make_shared<std::atomic<bool>>(false);
    };

    static std::map<std::string, SocketEntry> &getMap();
    static void shutdown_socket(SocketEntry &e);
};

#endif // SOCKET_FACTORY_H
