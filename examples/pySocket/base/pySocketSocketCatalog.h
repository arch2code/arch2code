#ifndef PYSOCKET_SOCKETCATALOG_H
#define PYSOCKET_SOCKETCATALOG_H
// 

// GENERATED_CODE_PARAM --block=pySocket
// GENERATED_CODE_BEGIN --template=socketCatalog --section=header
#include "socketFactory.h"
#include <array>
#include <iostream>
#include <string>
#include <string_view>

namespace pySocketSocketCatalog {

inline constexpr bool uses_lockstep = false;

inline constexpr std::array<const char *, 13> listen_suffixes{{
    ".test_req_ack",
    ".test2Python_req_ack",
    ".dut2Python_req_ack",
    ".test_push_ack",
    ".test_pop_ack",
    ".dut2Python_push_ack",
    ".dut2Python_pop_ack",
    ".test_notify_ack",
    ".dut2Python_notify_ack",
    ".test_rdy_vld",
    ".dut2Python_rdy_vld",
    ".test_axi4_stream",
    ".dut2Python_axi4_stream",
}};

inline std::string name_test_req_ack(std::string_view instance) { return std::string(instance) + ".test_req_ack"; }
inline std::string name_test2Python_req_ack(std::string_view instance) { return std::string(instance) + ".test2Python_req_ack"; }
inline std::string name_dut2Python_req_ack(std::string_view instance) { return std::string(instance) + ".dut2Python_req_ack"; }
inline std::string name_test_push_ack(std::string_view instance) { return std::string(instance) + ".test_push_ack"; }
inline std::string name_test_pop_ack(std::string_view instance) { return std::string(instance) + ".test_pop_ack"; }
inline std::string name_dut2Python_push_ack(std::string_view instance) { return std::string(instance) + ".dut2Python_push_ack"; }
inline std::string name_dut2Python_pop_ack(std::string_view instance) { return std::string(instance) + ".dut2Python_pop_ack"; }
inline std::string name_test_notify_ack(std::string_view instance) { return std::string(instance) + ".test_notify_ack"; }
inline std::string name_dut2Python_notify_ack(std::string_view instance) { return std::string(instance) + ".dut2Python_notify_ack"; }
inline std::string name_test_rdy_vld(std::string_view instance) { return std::string(instance) + ".test_rdy_vld"; }
inline std::string name_dut2Python_rdy_vld(std::string_view instance) { return std::string(instance) + ".dut2Python_rdy_vld"; }
inline std::string name_test_axi4_stream(std::string_view instance) { return std::string(instance) + ".test_axi4_stream"; }
inline std::string name_dut2Python_axi4_stream(std::string_view instance) { return std::string(instance) + ".dut2Python_axi4_stream"; }

// Listens on every drive and observe name of one shell instance. A name
// already registered is an error: two shells would share one connection.
inline bool registerInstance(std::string_view instance)
{
    for (const char *suffix : listen_suffixes) {
        const std::string ifc = std::string(instance) + suffix;
        if (socketFactory::registerInterface(ifc) == 0) {
            std::cerr << "pySocketSocketCatalog: cannot register socket " << ifc
                      << " (already registered, or no listen port)" << std::endl;
            socketFactory::shutdownAll();
            return false;
        }
    }
    return true;
}

} // namespace pySocketSocketCatalog

// GENERATED_CODE_END

#endif //PYSOCKET_SOCKETCATALOG_H
