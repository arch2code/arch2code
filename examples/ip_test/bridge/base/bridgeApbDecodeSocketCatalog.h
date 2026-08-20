#ifndef BRIDGEAPBDECODE_SOCKETCATALOG_H
#define BRIDGEAPBDECODE_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=bridgeApbDecode
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace bridgeApbDecodeSocketCatalog {

inline constexpr std::array<const char *, 4> listen_names{{
    "bridgeApbDecode.apbReg_uBridgeIp0",
    "bridgeApbDecode.apbReg_uBridgeIp1",
    "bridgeApbDecode.apbReg_uBridgeIp0_obs",
    "bridgeApbDecode.apbReg_uBridgeIp1_obs",
}};
inline constexpr std::array<const char *, 1> sync_names{{
    PYSOCKET_SYNC_IFC,
}};

inline constexpr const char *name_apbReg_uBridgeIp0 = "bridgeApbDecode.apbReg_uBridgeIp0";
inline constexpr const char *observe_name_apbReg_uBridgeIp0 = "bridgeApbDecode.apbReg_uBridgeIp0_obs";
inline constexpr const char *name_apbReg_uBridgeIp1 = "bridgeApbDecode.apbReg_uBridgeIp1";
inline constexpr const char *observe_name_apbReg_uBridgeIp1 = "bridgeApbDecode.apbReg_uBridgeIp1_obs";
inline constexpr const char *name_apbReg = "bridgeApbDecode.apbReg";

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

} // namespace bridgeApbDecodeSocketCatalog

// GENERATED_CODE_END

#endif //BRIDGEAPBDECODE_SOCKETCATALOG_H
