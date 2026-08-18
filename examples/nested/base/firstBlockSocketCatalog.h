#ifndef FIRSTBLOCK_SOCKETCATALOG_H
#define FIRSTBLOCK_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=firstBlock
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace firstBlockSocketCatalog {

inline constexpr std::array<const char *, 2> listen_names{{
    "firstBlock.primary",
    "firstBlock.response",
}};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_primary = "firstBlock.primary";
inline constexpr const char *name_response = "firstBlock.response";

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

} // namespace firstBlockSocketCatalog

// GENERATED_CODE_END

#endif //FIRSTBLOCK_SOCKETCATALOG_H
