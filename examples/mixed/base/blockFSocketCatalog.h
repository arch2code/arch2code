#ifndef BLOCKF_SOCKETCATALOG_H
#define BLOCKF_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockF
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace blockFSocketCatalog {

inline constexpr std::array<const char *, 5> listen_names{{
    "blockF.cStuffIf",
    "blockF.dStuffIf",
    "blockF.dSin",
    "blockF.dSout",
    "blockF.rwD_obs",
}};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_cStuffIf = "blockF.cStuffIf";
inline constexpr const char *name_dStuffIf = "blockF.dStuffIf";
inline constexpr const char *name_dSin = "blockF.dSin";
inline constexpr const char *name_dSout = "blockF.dSout";
inline constexpr const char *name_rwD = "blockF.rwD";
inline constexpr const char *observe_name_rwD = "blockF.rwD_obs";

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

} // namespace blockFSocketCatalog

// GENERATED_CODE_END

#endif //BLOCKF_SOCKETCATALOG_H
