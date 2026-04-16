// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef SOCKET_TRANSPORT_H
#define SOCKET_TRANSPORT_H

#include <cstdint>
#include <cstddef>

constexpr uint8_t MSG_REQ = 0x01;
constexpr uint8_t MSG_ACK = 0x02;
constexpr uint8_t MSG_PUSH = 0x03;
constexpr uint8_t MSG_PUSH_ACK = 0x04;
constexpr uint8_t MSG_VLD = 0x05;
constexpr uint8_t MSG_RDY = 0x06;
constexpr uint8_t MSG_SYNC = 0x07; // TB → Python: simulation ready (startup handshake)
constexpr uint8_t MSG_SHUTDOWN = 0xFE;
constexpr uint8_t MSG_ERROR = 0xFF;

#pragma pack(push, 1)
struct SocketMsgHeader {
    uint8_t msg_type;
    uint8_t reserved;
    uint16_t payload_len;
};
#pragma pack(pop)

static_assert(sizeof(SocketMsgHeader) == 4, "SocketMsgHeader must be 4 bytes");

bool socket_send_msg(int fd, uint8_t msg_type, const void *payload, uint16_t len);

// Reads one framed message. On success, len is the wire payload size (<= max_payload).
bool socket_recv_msg(int fd, uint8_t &msg_type, void *payload, uint16_t &len, uint16_t max_payload);

#endif // SOCKET_TRANSPORT_H
