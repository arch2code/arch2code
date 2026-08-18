#ifndef BLOCKBREGS_SOCKETCATALOG_H
#define BLOCKBREGS_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockBRegs
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace blockBRegsSocketCatalog {

inline constexpr std::array<const char *, 1> listen_names{{
    "blockBRegs.roBsize_obs",
}};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_apbReg = "blockBRegs.apbReg";
inline constexpr const char *name_rwD = "blockBRegs.rwD";
inline constexpr const char *name_roBsize = "blockBRegs.roBsize";
inline constexpr const char *observe_name_roBsize = "blockBRegs.roBsize_obs";
inline constexpr const char *name_blockBTableExt = "blockBRegs.blockBTableExt";
inline constexpr const char *name_blockBTable37Bit = "blockBRegs.blockBTable37Bit";
inline constexpr const char *name_blockBTable1 = "blockBRegs.blockBTable1";

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

} // namespace blockBRegsSocketCatalog

// GENERATED_CODE_END

#endif //BLOCKBREGS_SOCKETCATALOG_H
