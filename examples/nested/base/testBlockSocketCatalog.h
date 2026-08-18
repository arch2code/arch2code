#ifndef TESTBLOCK_SOCKETCATALOG_H
#define TESTBLOCK_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=testBlock
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace testBlockSocketCatalog {

inline constexpr std::array<const char *, 4> listen_names{{
    "testBlock.loop1src",
    "testBlock.loop1dst",
    "testBlock.loop2src",
    "testBlock.loop2dst",
}};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_loop1src = "testBlock.loop1src";
inline constexpr const char *name_loop1dst = "testBlock.loop1dst";
inline constexpr const char *name_loop2src = "testBlock.loop2src";
inline constexpr const char *name_loop2dst = "testBlock.loop2dst";

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

} // namespace testBlockSocketCatalog

// GENERATED_CODE_END

#endif //TESTBLOCK_SOCKETCATALOG_H
