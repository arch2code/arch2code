#ifndef APBDECODE_SOCKETCATALOG_H
#define APBDECODE_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace apbDecodeSocketCatalog {

inline constexpr std::array<const char *, 6> listen_names{{
    "apbDecode.apbReg_uBridge",
    "apbDecode.apbReg_uIp0",
    "apbDecode.apbReg_uIp1",
    "apbDecode.apbReg_uBridge_obs",
    "apbDecode.apbReg_uIp0_obs",
    "apbDecode.apbReg_uIp1_obs",
}};
inline constexpr std::array<const char *, 1> sync_names{{
    PYSOCKET_SYNC_IFC,
}};

inline constexpr const char *name_apbReg_uBridge = "apbDecode.apbReg_uBridge";
inline constexpr const char *observe_name_apbReg_uBridge = "apbDecode.apbReg_uBridge_obs";
inline constexpr const char *name_apbReg_uIp0 = "apbDecode.apbReg_uIp0";
inline constexpr const char *observe_name_apbReg_uIp0 = "apbDecode.apbReg_uIp0_obs";
inline constexpr const char *name_apbReg_uIp1 = "apbDecode.apbReg_uIp1";
inline constexpr const char *observe_name_apbReg_uIp1 = "apbDecode.apbReg_uIp1_obs";
inline constexpr const char *name_cpu_main = "apbDecode.cpu_main";

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

} // namespace apbDecodeSocketCatalog

// GENERATED_CODE_END

#endif //APBDECODE_SOCKETCATALOG_H
