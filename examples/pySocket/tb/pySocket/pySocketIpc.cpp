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

int g_listen_sc_to_py = -1;
int g_listen_py_to_sc = -1;
int g_fd_sc_to_py = -1;
int g_fd_py_to_sc = -1;

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

bool start_servers(std::uint16_t &port_sc_to_py, std::uint16_t &port_py_to_sc)
{
    close_channels();
    if (!bind_listen_loopback(g_listen_sc_to_py, port_sc_to_py)) {
        return false;
    }
    if (!bind_listen_loopback(g_listen_py_to_sc, port_py_to_sc)) {
        close(g_listen_sc_to_py);
        g_listen_sc_to_py = -1;
        return false;
    }
    return true;
}

bool accept_clients()
{
    if (g_listen_sc_to_py < 0 || g_listen_py_to_sc < 0) {
        return false;
    }

    int n_done = 0;
    while (n_done < 2) {
        pollfd pfds[2]{};
        pfds[0].fd = g_listen_sc_to_py;
        pfds[0].events = POLLIN;
        pfds[1].fd = g_listen_py_to_sc;
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
            if (p.fd == g_listen_sc_to_py) {
                if (g_fd_sc_to_py >= 0) {
                    close(c);
                    return false;
                }
                g_fd_sc_to_py = c;
                ++n_done;
            } else if (p.fd == g_listen_py_to_sc) {
                if (g_fd_py_to_sc >= 0) {
                    close(c);
                    return false;
                }
                g_fd_py_to_sc = c;
                ++n_done;
            }
        }
    }

    close(g_listen_sc_to_py);
    g_listen_sc_to_py = -1;
    close(g_listen_py_to_sc);
    g_listen_py_to_sc = -1;
    return true;
}

int fd_sc_to_py()
{
    return g_fd_sc_to_py;
}

int fd_py_to_sc()
{
    return g_fd_py_to_sc;
}

void close_channels()
{
    auto close_fd = [](int &fd) {
        if (fd >= 0) {
            close(fd);
            fd = -1;
        }
    };
    close_fd(g_listen_sc_to_py);
    close_fd(g_listen_py_to_sc);
    close_fd(g_fd_sc_to_py);
    close_fd(g_fd_py_to_sc);
}

} // namespace pySocketIpc
