#ifndef BLOCKA_SOCKETCATALOG_H
#define BLOCKA_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockA
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace blockASocketCatalog {

inline constexpr std::array<const char *, 4> listen_names{{
    "blockA.aStuffIf",
    "blockA.cStuffIf",
    "blockA.startDone",
    "blockA.dupIf",
}};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_aStuffIf = "blockA.aStuffIf";
inline constexpr const char *name_cStuffIf = "blockA.cStuffIf";
inline constexpr const char *name_startDone = "blockA.startDone";
inline constexpr const char *name_dupIf = "blockA.dupIf";
inline constexpr const char *name_apbReg = "blockA.apbReg";

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

} // namespace blockASocketCatalog

// GENERATED_CODE_END

#endif //BLOCKA_SOCKETCATALOG_H
