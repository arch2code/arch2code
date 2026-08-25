#ifndef PRODUCER_SOCKETCATALOG_H
#define PRODUCER_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=producer
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace producerSocketCatalog {

inline constexpr std::array<const char *, 18> listen_names{{
    "producer.axiRd0",
    "producer.axiRd1",
    "producer.axiRd2",
    "producer.axiRd3",
    "producer.axiWr0",
    "producer.axiWr1",
    "producer.axiWr2",
    "producer.axiWr3",
    "producer.axiStr0",
    "producer.axiStr1",
    "producer.axiRd0_obs",
    "producer.axiRd1_obs",
    "producer.axiRd2_obs",
    "producer.axiRd3_obs",
    "producer.axiWr0_obs",
    "producer.axiWr1_obs",
    "producer.axiWr2_obs",
    "producer.axiWr3_obs",
}};
inline constexpr std::array<const char *, 1> sync_names{{
    PYSOCKET_SYNC_IFC,
}};

inline constexpr const char *name_axiRd0 = "producer.axiRd0";
inline constexpr const char *observe_name_axiRd0 = "producer.axiRd0_obs";
inline constexpr const char *name_axiRd1 = "producer.axiRd1";
inline constexpr const char *observe_name_axiRd1 = "producer.axiRd1_obs";
inline constexpr const char *name_axiRd2 = "producer.axiRd2";
inline constexpr const char *observe_name_axiRd2 = "producer.axiRd2_obs";
inline constexpr const char *name_axiRd3 = "producer.axiRd3";
inline constexpr const char *observe_name_axiRd3 = "producer.axiRd3_obs";
inline constexpr const char *name_axiWr0 = "producer.axiWr0";
inline constexpr const char *observe_name_axiWr0 = "producer.axiWr0_obs";
inline constexpr const char *name_axiWr1 = "producer.axiWr1";
inline constexpr const char *observe_name_axiWr1 = "producer.axiWr1_obs";
inline constexpr const char *name_axiWr2 = "producer.axiWr2";
inline constexpr const char *observe_name_axiWr2 = "producer.axiWr2_obs";
inline constexpr const char *name_axiWr3 = "producer.axiWr3";
inline constexpr const char *observe_name_axiWr3 = "producer.axiWr3_obs";
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
