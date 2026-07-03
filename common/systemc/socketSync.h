// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef SOCKET_SYNC_H
#define SOCKET_SYNC_H

#include "socketTransport.h"
#include "systemc.h"

#include <cstdint>
#include <memory>

class ThreadSafeEvent;

// Lockstep time-quantum synchronization between SystemC and Python.
// Enabled when PYSOCKET_LOCKSTEP=1; quantum size from PYSOCKET_SYNC_QUANTUM_NS (default 1000).

void socketSyncConfigureFromEnvironment();

bool socketSyncLockstepEnabled();

sc_core::sc_time socketSyncQuantum();

uint64_t socketSyncScTimeNs();

uint64_t socketSyncObserveTimeNs();

bool socketSyncAtBoundary();

void socketSyncRegisterBoundaryEvent(const std::shared_ptr<ThreadSafeEvent> &event);

void socketSyncRegisterApbReqEvent(const std::shared_ptr<ThreadSafeEvent> &event);

void socketSyncStartRxThread();

void socketSyncQuantumThread();

#endif // SOCKET_SYNC_H
