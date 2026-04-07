// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE

#ifndef PYSOCKET_IPC_H
#define PYSOCKET_IPC_H

#include <cstdint>

namespace pySocketIpc {

// Two localhost TCP listeners (OS-assigned ports). Call in the parent before fork().
bool start_servers_py2sc(std::uint16_t &port_request, std::uint16_t &port_response);
bool start_servers_sc2py(std::uint16_t &port_request, std::uint16_t &port_response);

// Parent only: accept Python on both channels (order-independent). Closes listen fds.
bool accept_clients_py2sc();
bool accept_clients_sc2py();

// SC writes / Python reads
int fd_py2sc_request();

// Python writes / SC reads
int fd_py2sc_response();

// SC writes / Python reads
int fd_sc2py_request();

// Python writes / SC reads
int fd_sc2py_response();

void close_channels_py2sc();
void close_channels_sc2py();
void close_all_channels();

} // namespace pySocketIpc

#endif
