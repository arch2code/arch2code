// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "pySocketIpc.h"

#include <arpa/inet.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <poll.h>
#include <sys/socket.h>
#include <unistd.h>

#include <cerrno>

namespace pySocketIpc {

namespace {

    struct listen_pair_t {
        int listen_request;
        int listen_response;
        int request_fd;
        int response_fd;
    };
    listen_pair_t g_py2sc_pair = {-1, -1, -1, -1};
    listen_pair_t g_sc2py_pair = {-1, -1, -1, -1};



bool bind_listen_loopback(int &listen_fd, std::uint16_t &out_port)
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

} // namespace


bool start_servers_pair(listen_pair_t &pair, std::uint16_t &port_request, std::uint16_t &port_response)
{
    if (!bind_listen_loopback(pair.listen_request, port_request)) {
        return false;
    }
    if (!bind_listen_loopback(pair.listen_response, port_response)) {
        close(pair.listen_request);
        pair.listen_request = -1;
        pair.request_fd = -1;
        return false;
    }
    return true;
}

bool start_servers_py2sc(std::uint16_t &port_request, std::uint16_t &port_response)
{
    close_channels_py2sc();
    return start_servers_pair(g_py2sc_pair, port_request, port_response);
}

bool start_servers_sc2py(std::uint16_t &port_request, std::uint16_t &port_response)
{
    close_channels_sc2py();
    return start_servers_pair(g_sc2py_pair, port_request, port_response);
}


bool accept_clients_pair(listen_pair_t &pair)
{
    if (pair.listen_request < 0 || pair.listen_response < 0) {
        return false;
    }

    int n_done = 0;
    while (n_done < 2) {
        pollfd pfds[2]{};
        pfds[0].fd = pair.listen_request;
        pfds[0].events = POLLIN;
        pfds[1].fd = pair.listen_response;
        pfds[1].events = POLLIN;

        int pr = poll(pfds, 2, -1);
        if (pr < 0) {
            if (errno == EINTR) {
                continue;
            }
            return false;
        }

        for (pollfd &p : pfds) {
            if (!(p.revents & POLLIN)) {
                continue;
            }
            const int c = accept(p.fd, nullptr, nullptr);
            if (c < 0) {
                if (errno == EINTR) {
                    continue;
                }
                return false;
            }
            if (p.fd == pair.listen_request) {
                if (pair.request_fd >= 0) {
                    close(c);
                    return false;
                }
                pair.request_fd = c;
                ++n_done;
            } else if (p.fd == pair.listen_response) {
                if (pair.response_fd >= 0) {
                    close(c);
                    return false;
                }
                pair.response_fd = c;
                ++n_done;
            } 
        }
    }

    close(pair.listen_request);
    pair.listen_request = -1;
    close(pair.listen_response);
    pair.listen_response = -1;
    return true;
}

bool accept_clients_py2sc()
{
    return accept_clients_pair(g_py2sc_pair);
}

bool accept_clients_sc2py()
{
    return accept_clients_pair(g_sc2py_pair);
}

int fd_py2sc_request()
{
    return g_py2sc_pair.request_fd;
}

int fd_py2sc_response()
{
    return g_py2sc_pair.response_fd;
}

int fd_sc2py_request()
{
    return g_sc2py_pair.request_fd;
}

int fd_sc2py_response()
{
    return g_sc2py_pair.response_fd;
}

void close_channels_pair(listen_pair_t &pair)
{
    auto close_fd = [](int &fd) {
        if (fd >= 0) {
            close(fd);
            fd = -1;
        }
    };
    close_fd(pair.listen_request);
    close_fd(pair.listen_response);
    close_fd(pair.request_fd);
    close_fd(pair.response_fd);
}

void close_channels_py2sc()
{
    close_channels_pair(g_py2sc_pair);
}

void close_channels_sc2py()
{
    close_channels_pair(g_sc2py_pair);
}

void close_all_channels()
{
    close_channels_py2sc();
    close_channels_sc2py();
}

} // namespace pySocketIpc
