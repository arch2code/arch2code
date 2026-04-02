// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#ifndef PYSOCKET_IPC_H
#define PYSOCKET_IPC_H

#include <cstdint>

namespace pySocketIpc {

// Two localhost TCP listeners (OS-assigned ports). Call in the parent before fork().
bool start_servers(std::uint16_t &port_py2sc_request, std::uint16_t &port_py2sc_response, std::uint16_t &port_sc2py_request, std::uint16_t &port_sc2py_response);

// Parent only: accept Python on both channels (order-independent). Closes listen fds.
bool accept_clients();

// SC writes / Python reads
int fd_py2sc_request();

// Python writes / SC reads
int fd_py2sc_response();

// SC writes / Python reads
int fd_sc2py_request();

// Python writes / SC reads
int fd_sc2py_response();

void close_channels();

} // namespace pySocketIpc

#endif
