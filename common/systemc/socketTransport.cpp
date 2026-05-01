// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#include "socketTransport.h"

#include <cerrno>
#include <cstring>
#include <unistd.h>

namespace {

bool write_full(int fd, const void *buf, size_t count)
{
    const auto *p = static_cast<const uint8_t *>(buf);
    size_t off = 0;
    while (off < count) {
        const ssize_t n = ::write(fd, p + off, count - off);
        if (n <= 0) {
            if (n < 0 && errno == EINTR) {
                continue;
            }
            return false;
        }
        off += static_cast<size_t>(n);
    }
    return true;
}

bool read_full(int fd, void *buf, size_t count)
{
    auto *p = static_cast<uint8_t *>(buf);
    size_t off = 0;
    while (off < count) {
        const ssize_t n = ::read(fd, p + off, count - off);
        if (n == 0) {
            return false;
        }
        if (n < 0) {
            if (errno == EINTR) {
                continue;
            }
            return false;
        }
        off += static_cast<size_t>(n);
    }
    return true;
}

} // namespace

bool socket_send_msg(int fd, uint8_t msg_type, const void *payload, uint16_t len)
{
    SocketMsgHeader hdr{};
    hdr.msg_type = msg_type;
    hdr.reserved = 0;
    hdr.payload_len = len;
    if (!write_full(fd, &hdr, sizeof(hdr))) {
        return false;
    }
    if (len > 0 && payload != nullptr) {
        return write_full(fd, payload, len);
    }
    return true;
}

bool socket_recv_msg(int fd, uint8_t &msg_type, void *payload, uint16_t &len, uint16_t max_payload)
{
    SocketMsgHeader hdr{};
    if (!read_full(fd, &hdr, sizeof(hdr))) {
        return false;
    }
    msg_type = hdr.msg_type;
    len = hdr.payload_len;
    if (len > max_payload) {
        return false;
    }
    if (len > 0) {
        if (payload == nullptr) {
            return false;
        }
        if (!read_full(fd, payload, len)) {
            return false;
        }
    }
    return true;
}
