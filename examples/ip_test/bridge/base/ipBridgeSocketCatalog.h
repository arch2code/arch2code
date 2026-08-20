#ifndef IPBRIDGE_SOCKETCATALOG_H
#define IPBRIDGE_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipBridge
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace ipBridgeSocketCatalog {

inline constexpr std::array<const char *, 2> listen_names{{
    "ipBridge.data8In",
    "ipBridge.data70In",
}};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_data8In = "ipBridge.data8In";
inline constexpr const char *name_data70In = "ipBridge.data70In";
inline constexpr const char *name_apbReg = "ipBridge.apbReg";

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

} // namespace ipBridgeSocketCatalog

// GENERATED_CODE_END

#endif //IPBRIDGE_SOCKETCATALOG_H
