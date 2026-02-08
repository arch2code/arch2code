# Skill: RTL Patterns

## Purpose
Reference common RTL implementation patterns to solve frequent design problems efficiently and consistently in SystemVerilog.

## 1. Finite State Machine (FSM)
Use for control logic with multiple states.
*   **Key:** Use `always_comb` for next state logic and `DFF` macros for state register.
*   **Ref:** `rtl-core.md`

## 2. Streaming Pipeline (`rdy_vld`)
Use for data processing stages.
*   **Forward Flow:** `valid` indicates data availability.
*   **Backward Flow:** `ready` indicates ability to accept.
*   **Logic:** `process_en = in.valid & out.ready`.
*   **Ref:** `rtl-interfaces.md`

## 3. Request-Response (`req_ack`)
Use for transactional operations (e.g., memory access, configuration).
*   **Req:** Source drives `req` high.
*   **Ack:** Destination drives `ack` high when complete.
*   **Handshake:** Source holds `req` until `ack` is seen.

## 4. Arbitration
Use when multiple sources contend for a single resource.
*   **Round Robin:** Fair access.
*   **Fixed Priority:** Critical path optimization.
*   **Components:** `memArb` (memory ports), `vldAckArb` (streaming interfaces).
*   **Ref:** `rtl-arbitration.md`

## 5. Datapath Buffering
Use to break timing paths or match rates.
*   **FIFO:** Store data, decouple rates.
*   **Capture Reg:** Latch `rdy_vld` data (`rdyVldCapture`).
*   **Ref:** `rtl-datapath.md`
