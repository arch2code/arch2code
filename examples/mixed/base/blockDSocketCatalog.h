#ifndef BLOCKD_SOCKETCATALOG_H
#define BLOCKD_SOCKETCATALOG_H
// copyright the arch2code project contributors, see https://github.com/arch2code/arch2code/blob/main/LICENSE

// GENERATED_CODE_PARAM --block=blockD
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include "socketTransport.h"
#include <array>

namespace blockDSocketCatalog {

inline constexpr std::array<const char *, 7> listen_names{{
    "blockD.cStuffIf",
    "blockD.dee0",
    "blockD.dee1",
    "blockD.outD",
    "blockD.inD",
    "blockD.btod",
    "blockD.rwD_obs",
}};
inline constexpr std::array<const char *, 0> sync_names{};

inline constexpr const char *name_cStuffIf = "blockD.cStuffIf";
inline constexpr const char *name_dee0 = "blockD.dee0";
inline constexpr const char *name_dee1 = "blockD.dee1";
inline constexpr const char *name_outD = "blockD.outD";
inline constexpr const char *name_inD = "blockD.inD";
inline constexpr const char *name_btod = "blockD.btod";
inline constexpr const char *name_rwD = "blockD.rwD";
inline constexpr const char *observe_name_rwD = "blockD.rwD_obs";
inline constexpr const char *name_roBsize = "blockD.roBsize";
inline constexpr const char *name_blockBTableExt = "blockD.blockBTableExt";
inline constexpr const char *name_blockBTable37Bit = "blockD.blockBTable37Bit";
inline constexpr const char *name_blockBTable1 = "blockD.blockBTable1";
inline constexpr const char *name_blockBTableSP = "blockD.blockBTableSP";

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

} // namespace blockDSocketCatalog

// GENERATED_CODE_END

#endif //BLOCKD_SOCKETCATALOG_H
