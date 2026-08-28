// copyright the arch2code project contributors, see https://bitbucket.org/arch2code/arch2code/src/main/LICENSE
#ifndef SOCKET_SYNC_H
#define SOCKET_SYNC_H

#include "socketTransport.h"
#include "systemc.h"

#include <cstdint>
#include <functional>
#include <memory>

class ThreadSafeEvent;

// Lockstep time-quantum synchronization between SystemC and Python.
// Enabled by default; set PYSOCKET_LOCKSTEP=0 to disable.
// Quantum size from PYSOCKET_SYNC_QUANTUM_NS, else --delay (default 0 → 1 ns).
//
// After each Python SYNC ack, socketSyncAdvanceTime() advances sc_time and
// requests DUT clock edges. Gated clocks must toggle only via
// socketSyncWaitClockEdge() so they cannot free-run during wait(ack).
// Model-only (no gated clock) still advances correctly via wait() in AdvanceTime.
//
// Ack wait uses delta-cycling so the SystemC event queue cannot go empty (this
// TB has no watchDog keep-alive). That freezes sc_time until Python acks.
//
// MSG_RESET (on pysocket_sync, in place of a SYNC ack) requests an ARESETn
// pulse: rst_n held low for assert_cycles, released, then settle_cycles, then
// MSG_RESET_ACK. Optional model soft-reset callback covers non-VL sims.
//
// MSG_BP_CFG (also replaces a SYNC ack) installs an AXI slave back-pressure
// policy consumed by axi_* port_socket between beat handshakes. ACK is
// MSG_BP_CFG_ACK; then the quantum advances normally.

void socketSyncConfigureFromEnvironment();

bool socketSyncLockstepEnabled();

// True when pysocket_sync has an accepted TCP connection. Wrapper reset must
// not follow socketSyncRstN() unless a partner can release it.
bool socketSyncSocketConnected();

// Lockstep env is on and a sync socket is connected (safe to arm lockstep reset).
bool socketSyncLockstepActive();

sc_core::sc_time socketSyncQuantum();

uint64_t socketSyncScTimeNs();

uint64_t socketSyncObserveTimeNs();

bool socketSyncAtBoundary();

void socketSyncRegisterBoundaryEvent(const std::shared_ptr<ThreadSafeEvent> &event);

void socketSyncRegisterApbReqEvent(const std::shared_ptr<ThreadSafeEvent> &event);

void socketSyncStartRxThread();

void socketSyncQuantumThread();

// --- Gated time advance (lockstep) ---

// True when lockstep is on and the quantum thread has entered gated mode
// (after Python ready). Free-running clocks should check this.
bool socketSyncTimeGated();

// Half-period used for gated clock edges (0.5 ns for a 1 ns period).
sc_core::sc_time socketSyncClockHalfPeriod();

// Advance simulation time by `amount`. Requests one clock edge per half-period
// then waits. Call only from the quantum SC thread after Python ack.
void socketSyncAdvanceTime(sc_core::sc_time amount);

// Gated clock: block until the quantum thread requests an edge, then return
// so the clock generator can toggle (no timed wait here).
void socketSyncWaitClockEdge();

// Notify listeners (e.g. VCD flusher) that timed simulation progressed.
void socketSyncNoteTimeAdvanced();

const sc_core::sc_event &socketSyncTimeTickEvent();

// --- Mid-sim ARESETn (active-low rst_n) ---

// Desired rst_n level (1 = out of reset). HDL wrappers should drive rst_n from this.
bool socketSyncRstN();

// Notified whenever socketSyncRstN() changes (initial release + MSG_RESET pulses).
const sc_core::sc_event &socketSyncRstNEvent();

// Optional soft-reset for SystemC model path (no HDL rst_n). Called after pin release.
void socketSyncRegisterModelReset(std::function<void()> cb);

// Optional sampler for ARVALID/AWVALID after ARESETn assert (HDL pin observe).
// Invoked during MSG_RESET before MSG_RESET_ACK; results are returned in the ACK.
void socketSyncRegisterAxiValidSample(std::function<void(uint8_t &arvalid, uint8_t &awvalid)> cb);

// --- AXI slave back-pressure (MSG_BP_CFG) ---

// Wait `clocks` full clock periods (works under gated lockstep via quantum time).
void socketSyncStallClocks(uint16_t clocks);

// True when a fixed/random WREADY/RVALID hold should run before beat `beat`
// of burst `burst`.
bool socketSyncBpShouldStallWready(uint16_t burst, uint16_t beat);
bool socketSyncBpShouldStallRvalid(uint16_t burst, uint16_t beat);

// Hold duration for the armed fixed/random policy (0 if clear).
uint16_t socketSyncBpHoldCycles();

#endif // SOCKET_SYNC_H
