#ifndef PRODUCER_SOCKETCATALOG_H
#define PRODUCER_SOCKETCATALOG_H
// 

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace producerSocketCatalog {

inline constexpr std::array<const char *, 4> listen_names{{
    "producer.axiRd0",
    "producer.axiWr0",
    "producer.axiRd0_obs",
    "producer.axiWr0_obs",
}};
inline constexpr std::array<const char *, 1> sync_names{{
    PYSOCKET_SYNC_IFC,
}};

inline constexpr const char *name_axiRd0 = "producer.axiRd0";
inline constexpr const char *observe_name_axiRd0 = "producer.axiRd0_obs";
inline constexpr const char *name_axiWr0 = "producer.axiWr0";
inline constexpr const char *observe_name_axiWr0 = "producer.axiWr0_obs";

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
