#ifndef AXISOCKET_SOCKETCATALOG_H
#define AXISOCKET_SOCKETCATALOG_H
// 

// GENERATED_CODE_PARAM --block=axiSocket
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace axiSocketSocketCatalog {

inline constexpr std::array<const char *, 4> listen_names{{
    "axiSocket.axiRd0",
    "axiSocket.axiWr0",
    "axiSocket.axiRd0_obs",
    "axiSocket.axiWr0_obs",
}};
inline constexpr std::array<const char *, 1> sync_names{{
    PYSOCKET_SYNC_IFC,
}};

inline constexpr const char *name_axiRd0 = "axiSocket.axiRd0";
inline constexpr const char *observe_name_axiRd0 = "axiSocket.axiRd0_obs";
inline constexpr const char *name_axiWr0 = "axiSocket.axiWr0";
inline constexpr const char *observe_name_axiWr0 = "axiSocket.axiWr0_obs";

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

} // namespace axiSocketSocketCatalog

// GENERATED_CODE_END

#endif //AXISOCKET_SOCKETCATALOG_H
