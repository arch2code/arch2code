#ifndef XPSKTLEAF_SOCKETCATALOG_H
#define XPSKTLEAF_SOCKETCATALOG_H
// 

// GENERATED_CODE_PARAM --block=xpSktLeaf
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include <array>
#include <iostream>
#include <string>
#include <string_view>

namespace xpSktLeafSocketCatalog {

inline constexpr bool uses_lockstep = false;

inline constexpr std::array<const char *, 1> listen_suffixes{{
    ".out",
}};

inline std::string name_out(std::string_view instance) { return std::string(instance) + ".out"; }

// Listens on every drive and observe name of one shell instance. A name
// already registered is an error: two shells would share one connection.
inline bool registerInstance(std::string_view instance)
{
    for (const char *suffix : listen_suffixes) {
        const std::string ifc = std::string(instance) + suffix;
        if (socketFactory::registerInterface(ifc) == 0) {
            std::cerr << "xpSktLeafSocketCatalog: cannot register socket " << ifc
                      << " (already registered, or no listen port)" << std::endl;
            socketFactory::shutdownAll();
            return false;
        }
    }
    return true;
}

} // namespace xpSktLeafSocketCatalog

// GENERATED_CODE_END

#endif //XPSKTLEAF_SOCKETCATALOG_H
