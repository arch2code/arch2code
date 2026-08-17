#ifndef PYSOCKET_TB_SOCKETCATALOG_H
#define PYSOCKET_TB_SOCKETCATALOG_H
// 

// GENERATED_CODE_PARAM --block=pySocket_tb
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace pySocket_tbSocketCatalog {

inline constexpr std::array<const char *, 0> listen_names{};
inline constexpr std::array<const char *, 0> sync_names{};


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

} // namespace pySocket_tbSocketCatalog

// GENERATED_CODE_END

#endif //PYSOCKET_TB_SOCKETCATALOG_H
