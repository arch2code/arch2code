#ifndef AXISOCKET_SOCKETCATALOG_H
#define AXISOCKET_SOCKETCATALOG_H
// 

// GENERATED_CODE_PARAM --block=axiSocket
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include <array>
#include <iostream>
#include <string>
#include <string_view>

namespace axiSocketSocketCatalog {

inline constexpr bool uses_lockstep = true;

inline constexpr std::array<const char *, 4> listen_suffixes{{
    ".axiRd0",
    ".axiWr0",
    ".axiRd0_obs",
    ".axiWr0_obs",
}};

inline std::string name_axiRd0(std::string_view instance) { return std::string(instance) + ".axiRd0"; }
inline std::string observe_name_axiRd0(std::string_view instance) { return std::string(instance) + ".axiRd0_obs"; }
inline std::string name_axiWr0(std::string_view instance) { return std::string(instance) + ".axiWr0"; }
inline std::string observe_name_axiWr0(std::string_view instance) { return std::string(instance) + ".axiWr0_obs"; }

// Listens on every drive and observe name of one shell instance. A name
// already registered is an error: two shells would share one connection.
inline bool registerInstance(std::string_view instance)
{
    for (const char *suffix : listen_suffixes) {
        const std::string ifc = std::string(instance) + suffix;
        if (socketFactory::registerInterface(ifc) == 0) {
            std::cerr << "axiSocketSocketCatalog: cannot register socket " << ifc
                      << " (already registered, or no listen port)" << std::endl;
            socketFactory::shutdownAll();
            return false;
        }
    }
    return true;
}

} // namespace axiSocketSocketCatalog

// GENERATED_CODE_END

#endif //AXISOCKET_SOCKETCATALOG_H
