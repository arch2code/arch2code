#ifndef DUT_SOCKETCATALOG_H
#define DUT_SOCKETCATALOG_H
// 

// GENERATED_CODE_PARAM --block=dut
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace dutSocketCatalog {

inline constexpr std::array<const char *, 11> listen_names{{
    "dut.test_req_ack",
    "dut.test2Python_req_ack",
    "dut.dut2Python_req_ack",
    "dut.test_push_ack",
    "dut.test_pop_ack",
    "dut.dut2Python_push_ack",
    "dut.dut2Python_pop_ack",
    "dut.test_notify_ack",
    "dut.dut2Python_notify_ack",
    "dut.test_rdy_vld",
    "dut.dut2Python_rdy_vld",
}};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_test_req_ack = "dut.test_req_ack";
inline constexpr const char *name_test2Python_req_ack = "dut.test2Python_req_ack";
inline constexpr const char *name_dut2Python_req_ack = "dut.dut2Python_req_ack";
inline constexpr const char *name_test_push_ack = "dut.test_push_ack";
inline constexpr const char *name_test_pop_ack = "dut.test_pop_ack";
inline constexpr const char *name_dut2Python_push_ack = "dut.dut2Python_push_ack";
inline constexpr const char *name_dut2Python_pop_ack = "dut.dut2Python_pop_ack";
inline constexpr const char *name_test_notify_ack = "dut.test_notify_ack";
inline constexpr const char *name_dut2Python_notify_ack = "dut.dut2Python_notify_ack";
inline constexpr const char *name_test_rdy_vld = "dut.test_rdy_vld";
inline constexpr const char *name_dut2Python_rdy_vld = "dut.dut2Python_rdy_vld";

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

} // namespace dutSocketCatalog

// GENERATED_CODE_END

#endif //DUT_SOCKETCATALOG_H
