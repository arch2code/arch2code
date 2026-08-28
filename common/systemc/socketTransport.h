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
    MSG_IRQ_OBS=0x14,
    MSG_STATUS_OBS=0x15,
    MSG_RESET=0x16,
    MSG_RESET_ACK=0x17,
    MSG_CTRL_OBS=0x18,
    MSG_POP=0x19,
    MSG_POP_ACK=0x1A,
    MSG_NOTIFY=0x1B,
    MSG_NOTIFY_ACK=0x1C,
    MSG_BP_CFG=0x1D,
    MSG_BP_CFG_ACK=0x1E,
    MSG_AXIS_BEAT=0x1F,
    MSG_AXIS_RDY=0x20,
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
        case MSG_IRQ_OBS: return( "MSG_IRQ_OBS" );
        case MSG_STATUS_OBS: return( "MSG_STATUS_OBS" );
        case MSG_RESET: return( "MSG_RESET" );
        case MSG_RESET_ACK: return( "MSG_RESET_ACK" );
        case MSG_CTRL_OBS: return( "MSG_CTRL_OBS" );
        case MSG_POP: return( "MSG_POP" );
        case MSG_POP_ACK: return( "MSG_POP_ACK" );
        case MSG_NOTIFY: return( "MSG_NOTIFY" );
        case MSG_NOTIFY_ACK: return( "MSG_NOTIFY_ACK" );
        case MSG_BP_CFG: return( "MSG_BP_CFG" );
        case MSG_BP_CFG_ACK: return( "MSG_BP_CFG_ACK" );
        case MSG_AXIS_BEAT: return( "MSG_AXIS_BEAT" );
        case MSG_AXIS_RDY: return( "MSG_AXIS_RDY" );
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

#pragma pack(push, 1)
struct socket_sync_st {
    uint64_t sc_time_ns;
};
#pragma pack(pop)

static_assert(sizeof(socket_sync_st) == 8, "socket_sync_st wire layout");

#pragma pack(push, 1)
struct socket_reset_st {
    uint64_t sc_time_ns;    // must match pending SYNC quantum (acts as ack)
    uint16_t assert_cycles; // clocks to hold rst_n low
    uint16_t settle_cycles; // clocks after release before ACK
};
#pragma pack(pop)

static_assert(sizeof(socket_reset_st) == 12, "socket_reset_st wire layout");

// MSG_RESET_ACK payload: AxVALID levels sampled after ARESETn assert (both expect 0).
#pragma pack(push, 1)
struct socket_reset_ack_st {
    uint8_t arvalid;
    uint8_t awvalid;
};
#pragma pack(pop)

static_assert(sizeof(socket_reset_ack_st) == 2, "socket_reset_ack_st wire layout");

// AXI slave back-pressure policy (lockstep pysocket_sync, replaces a SYNC ack).
// channel bits: bit0 = WREADY (write data), bit1 = RVALID (read data).
// mode: 0 = clear, 1 = fixed hold of `cycles` clocks before beat `after_beat`
//       of burst `after_burst` (0xFFFF = every burst),
//       2 = random per-beat hold (seed LCG; ~50% of matching beats).
#pragma pack(push, 1)
struct socket_bp_cfg_st {
    uint64_t sc_time_ns;
    uint8_t channel;
    uint8_t mode;
    uint16_t cycles;
    uint16_t after_beat;
    uint16_t after_burst;
    uint32_t seed;
};
#pragma pack(pop)

static_assert(sizeof(socket_bp_cfg_st) == 20, "socket_bp_cfg_st wire layout");

static constexpr uint8_t SOCKET_BP_CH_WREADY = 0x1;
static constexpr uint8_t SOCKET_BP_CH_RVALID = 0x2;
static constexpr uint8_t SOCKET_BP_MODE_CLEAR = 0;
static constexpr uint8_t SOCKET_BP_MODE_FIXED = 1;
static constexpr uint8_t SOCKET_BP_MODE_RANDOM = 2;
static constexpr uint16_t SOCKET_BP_EVERY_BURST = 0xFFFF;

static constexpr const char *PYSOCKET_SYNC_IFC = "pysocket_sync";

static constexpr uint16_t SOCKET_AXI_BURST_BYTES = 4096;
static constexpr uint16_t SOCKET_AXI_OBS_PREVIEW_BYTES = 16;

bool socket_send_msg(int fd, uint8_t msg_type, const void *payload, uint16_t len);

// Reads one framed message. On success, len is the wire payload size (<= max_payload).
bool socket_recv_msg(int fd, uint8_t &msg_type, void *payload, uint16_t &len, uint16_t max_payload);

#endif // SOCKET_TRANSPORT_H
