#ifndef PRODUCER_SOCKETCATALOG_H
#define PRODUCER_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace producerSocketCatalog {

inline constexpr std::array<const char *, 6> listen_names{{
    "producer.src_trans_dest_trans_rv_tracker",
    "producer.src_clock_dest_trans_rv_tracker",
    "producer.src_trans_dest_clock_rv_tracker",
    "producer.src_trans_dest_trans_rv_size",
    "producer.src_clock_dest_trans_rv_size",
    "producer.src_trans_dest_clock_rv_size",
}};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_src_trans_dest_trans_rv_tracker = "producer.src_trans_dest_trans_rv_tracker";
inline constexpr const char *name_src_clock_dest_trans_rv_tracker = "producer.src_clock_dest_trans_rv_tracker";
inline constexpr const char *name_src_trans_dest_clock_rv_tracker = "producer.src_trans_dest_clock_rv_tracker";
inline constexpr const char *name_src_trans_dest_trans_rv_size = "producer.src_trans_dest_trans_rv_size";
inline constexpr const char *name_src_clock_dest_trans_rv_size = "producer.src_clock_dest_trans_rv_size";
inline constexpr const char *name_src_trans_dest_clock_rv_size = "producer.src_trans_dest_clock_rv_size";

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

} // namespace producerSocketCatalog

// GENERATED_CODE_END

#endif //PRODUCER_SOCKETCATALOG_H
