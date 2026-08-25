#ifndef PYSOCKET_SOCKETCATALOG_H
#define PYSOCKET_SOCKETCATALOG_H
// 

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace pySocketSocketCatalog {

inline constexpr std::array<const char *, 13> listen_names{{
    "pySocket.test_req_ack",
    "pySocket.test2Python_req_ack",
    "pySocket.dut2Python_req_ack",
    "pySocket.test_push_ack",
    "pySocket.test_pop_ack",
    "pySocket.dut2Python_push_ack",
    "pySocket.dut2Python_pop_ack",
    "pySocket.test_notify_ack",
    "pySocket.dut2Python_notify_ack",
    "pySocket.test_rdy_vld",
    "pySocket.dut2Python_rdy_vld",
    "pySocket.test_axi4_stream",
    "pySocket.dut2Python_axi4_stream",
}};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_test_req_ack = "pySocket.test_req_ack";
inline constexpr const char *name_test2Python_req_ack = "pySocket.test2Python_req_ack";
inline constexpr const char *name_dut2Python_req_ack = "pySocket.dut2Python_req_ack";
inline constexpr const char *name_test_push_ack = "pySocket.test_push_ack";
inline constexpr const char *name_test_pop_ack = "pySocket.test_pop_ack";
inline constexpr const char *name_dut2Python_push_ack = "pySocket.dut2Python_push_ack";
inline constexpr const char *name_dut2Python_pop_ack = "pySocket.dut2Python_pop_ack";
inline constexpr const char *name_test_notify_ack = "pySocket.test_notify_ack";
inline constexpr const char *name_dut2Python_notify_ack = "pySocket.dut2Python_notify_ack";
inline constexpr const char *name_test_rdy_vld = "pySocket.test_rdy_vld";
inline constexpr const char *name_dut2Python_rdy_vld = "pySocket.dut2Python_rdy_vld";
inline constexpr const char *name_test_axi4_stream = "pySocket.test_axi4_stream";
inline constexpr const char *name_dut2Python_axi4_stream = "pySocket.dut2Python_axi4_stream";

inline bool registerAll()
{
    for (const char *ifc : listen_names) {
        if (socketFactory::registerInterface(ifc) == 0) {
            socketFactory::shutdownAll();
            return false;
        }
    }
    for (const char *ifc : sync_names) {
        if (socketFactory::registerInterface(ifc) == 0) {
            socketFactory::shutdownAll();
            return false;
        }
    }
    return true;
}

inline bool handshakeAll()
{
    for (const char *ifc : listen_names) {
        const int fd = socketFactory::getFd(ifc);
        if (fd < 0 || !socket_send_msg(fd, MSG_SYNC, nullptr, 0)) {
            return false;
        }
    }
    for (const char *ifc : sync_names) {
        const int fd = socketFactory::getFd(ifc);
        if (fd < 0 || !socket_send_msg(fd, MSG_SYNC, nullptr, 0)) {
            return false;
        }
    }
    return true;
}

} // namespace pySocketSocketCatalog

// GENERATED_CODE_END

#endif //PYSOCKET_SOCKETCATALOG_H
