#ifndef HIERVLDEMO_SOCKETCATALOG_H
#define HIERVLDEMO_SOCKETCATALOG_H
// 

// GENERATED_CODE_PARAM --block=hierVlDemo
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace hierVlDemoSocketCatalog {

inline constexpr std::array<const char *, 0> listen_names{};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_axis4_t1 = "hierVlDemo.axis4_t1";
inline constexpr const char *name_axis4_t2 = "hierVlDemo.axis4_t2";

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

} // namespace hierVlDemoSocketCatalog

// GENERATED_CODE_END

#endif //HIERVLDEMO_SOCKETCATALOG_H
