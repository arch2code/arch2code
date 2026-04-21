// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "socketFactory.h"
#include "socketTransport.h"

#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cerrno>
#include <cstring>
#include <sstream>

std::map<std::string, socketFactory::SocketEntry> &socketFactory::getMap()
{
    static std::map<std::string, SocketEntry> map;
    return map;
}

static bool bind_listen_loopback(int &listen_fd, uint16_t &out_port)
{
    listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd < 0) {
        return false;
    }
    int one = 1;
    (void)setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));

    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = htons(0);
    if (bind(listen_fd, reinterpret_cast<sockaddr *>(&addr), sizeof(addr)) != 0) {
        close(listen_fd);
        listen_fd = -1;
        return false;
    }
    if (listen(listen_fd, 1) != 0) {
        close(listen_fd);
        listen_fd = -1;
        return false;
    }
    if (fcntl(listen_fd, F_SETFD, FD_CLOEXEC) != 0) {
        close(listen_fd);
        listen_fd = -1;
        return false;
    }
    socklen_t len = sizeof(addr);
    if (getsockname(listen_fd, reinterpret_cast<sockaddr *>(&addr), &len) != 0) {
        close(listen_fd);
        listen_fd = -1;
        return false;
    }
    out_port = ntohs(addr.sin_port);
    return true;
}

uint16_t socketFactory::registerInterface(const std::string &name)
{
    auto &map = getMap();
    SocketEntry ent;
    int lf = -1;
    uint16_t p = 0;
    if (!bind_listen_loopback(lf, p)) {
        return 0;
    }
    ent.listen_fd = lf;
    ent.port = p;
    ent.peer_closed_event = ThreadSafeEventFactory::newEvent((name + "_socket_peerClosed").c_str());
    map[name] = std::move(ent);
    return p;
}

void socketFactory::acceptConnection(const std::string &name)
{
    auto &map = getMap();
    auto it = map.find(name);
    if (it == map.end()) {
        return;
    }
    SocketEntry &e = it->second;
    if (e.listen_fd < 0) {
        return;
    }
    const int c = accept(e.listen_fd, nullptr, nullptr);
    if (c < 0) {
        return;
    }
    if (fcntl(c, F_SETFD, FD_CLOEXEC) != 0) {
        close(c);
        return;
    }
    close(e.listen_fd);
    e.listen_fd = -1;
    e.conn_fd = c;
}

void socketFactory::acceptAll()
{
    for (auto &kv : getMap()) {
        acceptConnection(kv.first);
    }
}

uint16_t socketFactory::getPort(const std::string &name)
{
    auto it = getMap().find(name);
    if (it == getMap().end()) {
        return 0;
    }
    return it->second.port;
}

std::vector<std::pair<std::string, uint16_t>> socketFactory::getAllPorts()
{
    std::vector<std::pair<std::string, uint16_t>> out;
    for (const auto &kv : getMap()) {
        out.emplace_back(kv.first, kv.second.port);
    }
    return out;
}

std::string socketFactory::getPortString()
{
    std::ostringstream oss;
    bool first = true;
    for (const auto &kv : getMap()) {
        if (!first) {
            oss << ',';
        }
        first = false;
        oss << kv.first << ':' << kv.second.port;
    }
    return oss.str();
}

int socketFactory::getFd(const std::string &name)
{
    auto it = getMap().find(name);
    if (it == getMap().end()) {
        return -1;
    }
    return it->second.conn_fd;
}

void socketFactory::registerThread(const std::string &name, std::thread &&t)
{
    auto it = getMap().find(name);
    if (it == getMap().end()) {
        return;
    }
    SocketEntry &e = it->second;
    if (e.has_thread && e.rx_thread.joinable()) {
        e.rx_thread.join();
    }
    e.rx_thread = std::move(t);
    e.has_thread = true;
}

std::shared_ptr<ThreadSafeEvent> socketFactory::getPeerClosedEvent(const std::string &name)
{
    auto it = getMap().find(name);
    if (it == getMap().end()) {
        return nullptr;
    }
    return it->second.peer_closed_event;
}

void socketFactory::notifyPeerClosed(const std::string &name)
{
    auto ev = getPeerClosedEvent(name);
    if (ev) {
        ev->notify();
    }
}

void socketFactory::shutdownByName(const std::string &name)
{
    auto it = getMap().find(name);
    if (it == getMap().end()) {
        return;
    }
    shutdown_socket(it->second);
    notifyPeerClosed(it->first);
}

void socketFactory::shutdownAll()
{
    auto &map = getMap();
    for (auto &kv : map) {
        SocketEntry &e = kv.second;
        if (e.conn_fd >= 0) {
            (void)socket_send_msg(e.conn_fd, MSG_SHUTDOWN, nullptr, 0);
            shutdown(e.conn_fd, SHUT_RDWR);
            close(e.conn_fd);
            e.conn_fd = -1;
        }
        if (e.listen_fd >= 0) {
            close(e.listen_fd);
            e.listen_fd = -1;
        }
        if (e.has_thread && e.rx_thread.joinable()) {
            e.rx_thread.join();
            e.has_thread = false;
        }
        notifyPeerClosed(kv.first);
    }
    map.clear();
}

void socketFactory::shutdown_socket(SocketEntry &e)
{
    if (e.conn_fd >= 0) {
        (void)socket_send_msg(e.conn_fd, MSG_SHUTDOWN, nullptr, 0);
        shutdown(e.conn_fd, SHUT_RDWR);
        close(e.conn_fd);
        e.conn_fd = -1;
    }
    if (e.listen_fd >= 0) {
        close(e.listen_fd);
        e.listen_fd = -1;
    }
    if (e.has_thread && e.rx_thread.joinable()) {
        e.rx_thread.join();
        e.has_thread = false;
    }
}