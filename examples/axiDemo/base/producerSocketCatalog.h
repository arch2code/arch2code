#ifndef PRODUCER_SOCKETCATALOG_H
#define PRODUCER_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace producerSocketCatalog {

inline constexpr std::array<const char *, 0> listen_names{};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_axiRd0 = "producer.axiRd0";
inline constexpr const char *name_axiRd1 = "producer.axiRd1";
inline constexpr const char *name_axiRd2 = "producer.axiRd2";
inline constexpr const char *name_axiRd3 = "producer.axiRd3";
inline constexpr const char *name_axiWr0 = "producer.axiWr0";
inline constexpr const char *name_axiWr1 = "producer.axiWr1";
inline constexpr const char *name_axiWr2 = "producer.axiWr2";
inline constexpr const char *name_axiWr3 = "producer.axiWr3";
inline constexpr const char *name_axiStr0 = "producer.axiStr0";
inline constexpr const char *name_axiStr1 = "producer.axiStr1";

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

} // namespace producerSocketCatalog

// GENERATED_CODE_END

#endif //PRODUCER_SOCKETCATALOG_H
