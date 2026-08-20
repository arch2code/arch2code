#ifndef IPSTDDECODE_SOCKETCATALOG_H
#define IPSTDDECODE_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=ipStdDecode
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace ipStdDecodeSocketCatalog {

inline constexpr std::array<const char *, 2> listen_names{{
    "ipStdDecode.ipReg_uIp",
    "ipStdDecode.ipReg_uIp_obs",
}};
inline constexpr std::array<const char *, 1> sync_names{{
    PYSOCKET_SYNC_IFC,
}};

inline constexpr const char *name_ipReg = "ipStdDecode.ipReg";
inline constexpr const char *name_ipReg_uIp = "ipStdDecode.ipReg_uIp";
inline constexpr const char *observe_name_ipReg_uIp = "ipStdDecode.ipReg_uIp_obs";

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

} // namespace ipStdDecodeSocketCatalog

// GENERATED_CODE_END

#endif //IPSTDDECODE_SOCKETCATALOG_H
