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

int g_listen_py2sc_request = -1;
int g_listen_py2sc_response = -1;
int g_listen_sc2py_request = -1;
int g_listen_sc2py_response = -1;
int g_fd_py2sc_request = -1;
int g_fd_py2sc_response = -1;
int g_fd_sc2py_request = -1;
int g_fd_sc2py_response = -1;

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

bool start_servers(std::uint16_t &port_py2sc_request, std::uint16_t &port_py2sc_response, std::uint16_t &port_sc2py_request, std::uint16_t &port_sc2py_response)
{
    close_channels();
    // TODO: cleanup flow and error handling
    if (!bind_listen_loopback(g_listen_py2sc_request, port_py2sc_request)) {
        return false;
    }
    if (!bind_listen_loopback(g_listen_py2sc_response, port_py2sc_response)) {
        close(g_listen_py2sc_request);
        g_listen_py2sc_request = -1;
        return false;
    }
    if (!bind_listen_loopback(g_listen_sc2py_request, port_sc2py_request)) {
        close(g_listen_py2sc_request);
        g_listen_py2sc_request = -1;
        close(g_listen_py2sc_response);
        g_listen_py2sc_response = -1;
        return false;
    }
    if (!bind_listen_loopback(g_listen_sc2py_response, port_sc2py_response)) {
        close(g_listen_py2sc_request);
        g_listen_py2sc_request = -1;
        close(g_listen_py2sc_response);
        g_listen_py2sc_response = -1;
        close(g_listen_sc2py_request);
        g_listen_sc2py_request = -1;
        return false;
    }
    return true;
}

bool accept_clients()
{
    if (g_listen_py2sc_request < 0 || g_listen_py2sc_response < 0 || g_listen_sc2py_request < 0 || g_listen_sc2py_response < 0) {
        return false;
    }

    int n_done = 0;
    while (n_done < 4) {
        pollfd pfds[4]{};
        pfds[0].fd = g_listen_py2sc_request;
        pfds[0].events = POLLIN;
        pfds[1].fd = g_listen_py2sc_response;
        pfds[1].events = POLLIN;
        pfds[2].fd = g_listen_sc2py_request;
        pfds[2].events = POLLIN;
        pfds[3].fd = g_listen_sc2py_response;
        pfds[3].events = POLLIN;

        int pr = poll(pfds, 4, -1);
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
            if (p.fd == g_listen_py2sc_request) {
                if (g_fd_py2sc_request >= 0) {
                    close(c);
                    return false;
                }
                g_fd_py2sc_request = c;
                ++n_done;
            } else if (p.fd == g_listen_py2sc_response) {
                if (g_fd_py2sc_response >= 0) {
                    close(c);
                    return false;
                }
                g_fd_py2sc_response = c;
                ++n_done;
            } else if (p.fd == g_listen_sc2py_request) {
                if (g_fd_sc2py_request >= 0) {
                    close(c);
                    return false;
                }
                g_fd_sc2py_request = c;
                ++n_done;
            } else if (p.fd == g_listen_sc2py_response) {
                if (g_fd_sc2py_response >= 0) {
                    close(c);
                    return false;
                }
                g_fd_sc2py_response = c;
                ++n_done;
            }
        }
    }

    close(g_listen_py2sc_request);
    g_listen_py2sc_request = -1;
    close(g_listen_py2sc_response);
    g_listen_py2sc_response = -1;
    close(g_listen_sc2py_request);
    g_listen_sc2py_request = -1;
    close(g_listen_sc2py_response);
    g_listen_sc2py_response = -1;
    return true;
}

int fd_py2sc_request()
{
    return g_fd_py2sc_request;
}

int fd_py2sc_response()
{
    return g_fd_py2sc_response;
}

int fd_sc2py_request()
{
    return g_fd_sc2py_request;
}

int fd_sc2py_response()
{
    return g_fd_sc2py_response;
}

void close_channels()
{
    auto close_fd = [](int &fd) {
        if (fd >= 0) {
            close(fd);
            fd = -1;
        }
    };
    close_fd(g_listen_py2sc_request);
    close_fd(g_listen_py2sc_response);
    close_fd(g_listen_sc2py_request);
    close_fd(g_listen_sc2py_response);
    close_fd(g_fd_py2sc_request);
    close_fd(g_fd_py2sc_response);
    close_fd(g_fd_sc2py_request);
    close_fd(g_fd_sc2py_response);
}

} // namespace pySocketIpc
