// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef SOCKET_TRANSPORT_H
#define SOCKET_TRANSPORT_H

#include <cstdint>
#include <cstddef>

enum socketMsgTypeT {
    MSG_REQ=0x01,
    MSG_ACK=0x02,
    MSG_PUSH=0x03,
    MSG_PUSH_ACK=0x04,
    MSG_VLD=0x05,
    MSG_RDY=0x06,
    MSG_SYNC=0x07,
    MSG_APB_REQ=0x08,
    MSG_APB_ACK=0x09,
    MSG_AXI_RD_REQ=0x0A,
    MSG_AXI_RD_RESP=0x0B,
    MSG_AXI_WR_REQ=0x0C,
    MSG_AXI_WR_RESP=0x0D,
    MSG_APB_OBS_REQ=0x0E,
    MSG_APB_OBS_RESP=0x0F,
    MSG_AXI_RD_OBS_REQ=0x10,
    MSG_AXI_RD_OBS_RESP=0x11,
    MSG_AXI_WR_OBS_REQ=0x12,
    MSG_AXI_WR_OBS_RESP=0x13,
    MSG_SHUTDOWN=0xFE,
    MSG_ERROR=0xFF
};
inline const char* socketMsgTypeT_prt( socketMsgTypeT val )
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
        case MSG_APB_REQ: return( "MSG_APB_REQ" );
        case MSG_APB_ACK: return( "MSG_APB_ACK" );
        case MSG_AXI_RD_REQ: return( "MSG_AXI_RD_REQ" );
        case MSG_AXI_RD_RESP: return( "MSG_AXI_RD_RESP" );
        case MSG_AXI_WR_REQ: return( "MSG_AXI_WR_REQ" );
        case MSG_AXI_WR_RESP: return( "MSG_AXI_WR_RESP" );
        case MSG_APB_OBS_REQ: return( "MSG_APB_OBS_REQ" );
        case MSG_APB_OBS_RESP: return( "MSG_APB_OBS_RESP" );
        case MSG_AXI_RD_OBS_REQ: return( "MSG_AXI_RD_OBS_REQ" );
        case MSG_AXI_RD_OBS_RESP: return( "MSG_AXI_RD_OBS_RESP" );
        case MSG_AXI_WR_OBS_REQ: return( "MSG_AXI_WR_OBS_REQ" );
        case MSG_AXI_WR_OBS_RESP: return( "MSG_AXI_WR_OBS_RESP" );
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

static constexpr uint16_t SOCKET_AXI_BURST_BYTES = 4096;
static constexpr uint16_t SOCKET_AXI_OBS_PREVIEW_BYTES = 16;

bool socket_send_msg(int fd, uint8_t msg_type, const void *payload, uint16_t len);

// Reads one framed message. On success, len is the wire payload size (<= max_payload).
bool socket_recv_msg(int fd, uint8_t &msg_type, void *payload, uint16_t &len, uint16_t max_payload);

#endif // SOCKET_TRANSPORT_H
