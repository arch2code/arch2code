#ifndef CONSUMER_SOCKETCATALOG_H
#define CONSUMER_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=consumer
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace consumerSocketCatalog {

inline constexpr std::array<const char *, 18> listen_names{{
    "consumer.axiRd0",
    "consumer.axiRd1",
    "consumer.axiRd2",
    "consumer.axiRd3",
    "consumer.axiWr0",
    "consumer.axiWr1",
    "consumer.axiWr2",
    "consumer.axiWr3",
    "consumer.axiStr0",
    "consumer.axiStr1",
    "consumer.axiRd0_obs",
    "consumer.axiRd1_obs",
    "consumer.axiRd2_obs",
    "consumer.axiRd3_obs",
    "consumer.axiWr0_obs",
    "consumer.axiWr1_obs",
    "consumer.axiWr2_obs",
    "consumer.axiWr3_obs",
}};
inline constexpr std::array<const char *, 1> sync_names{{
    PYSOCKET_SYNC_IFC,
}};

inline constexpr const char *name_axiRd0 = "consumer.axiRd0";
inline constexpr const char *observe_name_axiRd0 = "consumer.axiRd0_obs";
inline constexpr const char *name_axiRd1 = "consumer.axiRd1";
inline constexpr const char *observe_name_axiRd1 = "consumer.axiRd1_obs";
inline constexpr const char *name_axiRd2 = "consumer.axiRd2";
inline constexpr const char *observe_name_axiRd2 = "consumer.axiRd2_obs";
inline constexpr const char *name_axiRd3 = "consumer.axiRd3";
inline constexpr const char *observe_name_axiRd3 = "consumer.axiRd3_obs";
inline constexpr const char *name_axiWr0 = "consumer.axiWr0";
inline constexpr const char *observe_name_axiWr0 = "consumer.axiWr0_obs";
inline constexpr const char *name_axiWr1 = "consumer.axiWr1";
inline constexpr const char *observe_name_axiWr1 = "consumer.axiWr1_obs";
inline constexpr const char *name_axiWr2 = "consumer.axiWr2";
inline constexpr const char *observe_name_axiWr2 = "consumer.axiWr2_obs";
inline constexpr const char *name_axiWr3 = "consumer.axiWr3";
inline constexpr const char *observe_name_axiWr3 = "consumer.axiWr3_obs";
inline constexpr const char *name_axiStr0 = "consumer.axiStr0";
inline constexpr const char *name_axiStr1 = "consumer.axiStr1";

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

} // namespace consumerSocketCatalog

// GENERATED_CODE_END

#endif //CONSUMER_SOCKETCATALOG_H
