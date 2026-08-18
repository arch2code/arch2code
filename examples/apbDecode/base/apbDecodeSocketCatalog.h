#ifndef APBDECODE_SOCKETCATALOG_H
#define APBDECODE_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=apbDecode
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace apbDecodeSocketCatalog {

inline constexpr std::array<const char *, 4> listen_names{{
    "apbDecode.apbReg_uBlockA",
    "apbDecode.apbReg_uBlockB",
    "apbDecode.apbReg_uBlockA_obs",
    "apbDecode.apbReg_uBlockB_obs",
}};
inline constexpr std::array<const char *, 1> sync_names{{
    PYSOCKET_SYNC_IFC,
}};

inline constexpr const char *name_apbReg_uBlockA = "apbDecode.apbReg_uBlockA";
inline constexpr const char *observe_name_apbReg_uBlockA = "apbDecode.apbReg_uBlockA_obs";
inline constexpr const char *name_apbReg_uBlockB = "apbDecode.apbReg_uBlockB";
inline constexpr const char *observe_name_apbReg_uBlockB = "apbDecode.apbReg_uBlockB_obs";
inline constexpr const char *name_apbReg = "apbDecode.apbReg";

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
