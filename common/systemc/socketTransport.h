// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef SOCKET_TRANSPORT_H
#define SOCKET_TRANSPORT_H

#include <cstdint>
#include <cstddef>

enum _socketMsgTypeT{ MSG_REQ=0x01, MSG_ACK=0x02, MSG_PUSH=0x03, MSG_PUSH_ACK=0x04, MSG_VLD=0x05, MSG_RDY=0x06, MSG_SYNC=0x07, MSG_SHUTDOWN=0xFE, MSG_ERROR=0xFF };
inline const char* _socketMsgTypeT_prt( _socketMsgTypeT val )
{
    switch( val )
    {
        case MSG_REQ: return( "MSG_REQ" );
        case MSG_ACK: return( "MSG_ACK" );
        case MSG_PUSH: return( "MSG_PUSH" );
        case MSG_PUSH_ACK: return( "MSG_PUSH_ACK" );
        case MSG_VLD: return( "MSG_VLD" );
        case MSG_RDY: return( "MSG_RDY" );
        case MSG_SYNC: return( "MSG_SYNC" );
        case MSG_SHUTDOWN: return( "MSG_SHUTDOWN" );
        case MSG_ERROR: return( "MSG_ERROR" );
    }
    return("!!!BADENUM!!!");
}

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
