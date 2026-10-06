// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef STATUS_PORT_SOCKET_H
#define STATUS_PORT_SOCKET_H

#include "socketObserve.h"
#include "status_channel.h"
#include "systemc.h"

#include <string>

// status_in watcher: blocking read on each status update, then push observe payload.
// Matches APB/AXI port_socket registration style (SC_THREAD calls this helper).
template <class T, class ObserveFn>
void port_observe(status_in<T> &port, const std::string &interface_name, ObserveFn observe)
{
    while (true) {
        const T val = port->read();
        observe(interface_name, val);
    }
}

// Convenience for status structs with a bool/bit irq field (e.g. dma_irq_st).
template <class T>
void port_observe_irq(status_in<T> &port, const std::string &interface_name)
{
    port_observe(port, interface_name, [](const std::string &name, const T &val) {
        socket_observe_irq(name, static_cast<bool>(val.irq));
    });
}

#endif // STATUS_PORT_SOCKET_H
