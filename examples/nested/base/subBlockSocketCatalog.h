#ifndef SUBBLOCK_SOCKETCATALOG_H
#define SUBBLOCK_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=subBlock
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace subBlockSocketCatalog {

inline constexpr std::array<const char *, 2> listen_names{{
    "subBlock.src",
    "subBlock.dst",
}};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_src = "subBlock.src";
inline constexpr const char *name_dst = "subBlock.dst";

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

} // namespace subBlockSocketCatalog

// GENERATED_CODE_END

#endif //SUBBLOCK_SOCKETCATALOG_H
