// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef SOCKET_FACTORY_H
#define SOCKET_FACTORY_H

#include "asyncEvent.h"

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

    static uint16_t getPort(const std::string &name);

    static std::vector<std::pair<std::string, uint16_t>> getAllPorts();

    static std::string getPortString();

    static int getFd(const std::string &name);

    static void registerThread(const std::string &name, std::thread &&t);

    static std::shared_ptr<ThreadSafeEvent> getPeerClosedEvent(const std::string &name);

    static void notifyPeerClosed(const std::string &name);

    static void shutdownAll();

private:
    struct SocketEntry {
        int listen_fd = -1;
        int conn_fd = -1;
        uint16_t port = 0;
        std::thread rx_thread;
        bool has_thread = false;
        std::shared_ptr<ThreadSafeEvent> peer_closed_event;
    };

    static std::map<std::string, SocketEntry> &getMap();
};

#endif // SOCKET_FACTORY_H
