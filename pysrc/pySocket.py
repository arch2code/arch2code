#!/usr/bin/env python3
"""
The module provides a SocketTransport class for communicating with the pySocket
server started in the systemc framework.

The protocol is defined in the SOCKET_INTERFACE_DESIGN.md file in the arch2code repository.
"""

from __future__ import annotations

import asyncio
import ctypes
import os
import socket
import struct
import sys
import select as _select
from collections import deque
from dataclasses import dataclass, field
from typing import Deque

try:
    from cocotb.triggers import Event, NullTrigger
except ImportError:  # pragma: no cover - optional for asyncio-only clients
    Event = None  # type: ignore[misc, assignment]
    NullTrigger = None  # type: ignore[misc, assignment]

MSG_REQ = 0x01
MSG_ACK = 0x02
MSG_PUSH = 0x03
MSG_PUSH_ACK = 0x04
MSG_VLD = 0x05
MSG_RDY = 0x06
MSG_SYNC = 0x07
MSG_APB_REQ = 0x08
MSG_APB_ACK = 0x09
MSG_AXI_RD_REQ = 0x0A
MSG_AXI_RD_RESP = 0x0B
MSG_AXI_WR_REQ = 0x0C
MSG_AXI_WR_RESP = 0x0D
MSG_APB_OBS_REQ = 0x0E
MSG_APB_OBS_RESP = 0x0F
MSG_AXI_RD_OBS_REQ = 0x10
MSG_AXI_RD_OBS_RESP = 0x11
MSG_AXI_WR_OBS_REQ = 0x12
MSG_AXI_WR_OBS_RESP = 0x13
MSG_IRQ_OBS = 0x14
MSG_STATUS_OBS = 0x15
MSG_RESET = 0x16
MSG_RESET_ACK = 0x17
MSG_CTRL_OBS = 0x18
MSG_POP = 0x19
MSG_POP_ACK = 0x1A
MSG_NOTIFY = 0x1B
MSG_NOTIFY_ACK = 0x1C
MSG_BP_CFG = 0x1D
MSG_BP_CFG_ACK = 0x1E
MSG_SHUTDOWN = 0xFE

HEADER_STRUCT = struct.Struct("<BBH")
SYNC_PAYLOAD_STRUCT = struct.Struct("<Q")
RESET_PAYLOAD_STRUCT = struct.Struct("<QHH")  # sc_time_ns, assert_cycles, settle_cycles
# MSG_RESET_ACK: arvalid, awvalid sampled after ARESETn assert
RESET_ACK_PAYLOAD_STRUCT = struct.Struct("<BB")
# sc_time_ns, channel, mode, cycles, after_beat, after_burst, seed
BP_CFG_PAYLOAD_STRUCT = struct.Struct("<QBBHHHI")

PYSOCKET_SYNC_IFC = "pysocket_sync"

SOCKET_BP_CH_WREADY = 0x1
SOCKET_BP_CH_RVALID = 0x2
SOCKET_BP_MODE_CLEAR = 0
SOCKET_BP_MODE_FIXED = 1
SOCKET_BP_MODE_RANDOM = 2
SOCKET_BP_EVERY_BURST = 0xFFFF


def _env_enabled(name: str, *, default: bool = True) -> bool:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    v = value.strip().lower()
    if v in ("0", "false", "no"):
        return False
    if v in ("1", "true", "yes"):
        return True
    return default


def lockstep_enabled() -> bool:
    return _env_enabled("PYSOCKET_LOCKSTEP")


def struct_bytes(obj: ctypes.Structure) -> bytes:
    return ctypes.string_at(ctypes.byref(obj), ctypes.sizeof(obj))


def parse_ports(ports_file: str | None) -> dict[str, int]:
    if ports_file is not None:
        with open(ports_file, "r") as f:
            raw = f.read()
    else:
        raw = os.environ.get("PYSOCKET_PORTS", "")
    out: dict[str, int] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        name, _, port_s = part.partition(":")
        if not name or not port_s:
            print(f"pySocket.py: bad PYSOCKET_PORTS segment {part!r}", file=sys.stderr)
            sys.exit(1)
        try:
            out[name] = int(port_s)
        except ValueError as exc:
            print(f"pySocket.py: invalid port in {part!r}: {exc}", file=sys.stderr)
            sys.exit(1)
    return out

def _cocotb_event_factory():
    if Event is None:
        raise ImportError("cocotb is required for SyncSocketTransport lockstep gating")
    return Event()


@dataclass
class _PendingSend:
    msg_type: int
    payload: bytes
    done: object = field(default_factory=_cocotb_event_factory)


class LockstepRegistry:
    """Coordinates quantum-boundary socket I/O for gated transports."""

    def __init__(self) -> None:
        self._gated: list[SyncSocketTransport] = []
        self._pollable: list[SyncSocketTransport] = []
        self._sync: SyncSocketTransport | None = None
        self._bootstrapped = False
        self._draining = False
        self._quantum_loop_started = False
        self._pending_reset: tuple[int, int] | None = None
        self._reset_done: object | None = None
        self._last_reset_axvalid: tuple[int, int] = (0, 0)
        self._pending_bp_cfg: tuple[int, int, int, int, int, int] | None = None
        self._bp_cfg_done: object | None = None
        # Waiters released when the next MSG_SYNC arrives (SC finished AdvanceTime).
        self._quantum_waiters: list = []

    @property
    def bootstrapped(self) -> bool:
        return self._bootstrapped

    @property
    def draining(self) -> bool:
        return self._draining

    def set_sync_transport(self, transport: SyncSocketTransport) -> None:
        self._sync = transport

    def _start_quantum_loop(self) -> None:
        if self._quantum_loop_started:
            return
        from cocotb import start_soon

        self._quantum_loop_started = True
        start_soon(self._quantum_loop())

    async def bootstrap(self) -> None:
        """Tell SystemC Python is ready and complete the first quantum handshake."""
        if self._sync is None:
            raise RuntimeError("lockstep sync transport not registered")
        if self._bootstrapped:
            return
        await self._sync.send_python_ready()
        sc_time_ns = await self._sync.recv_sync_quantum()
        self._draining = True
        try:
            await self.drain_quantum()
        finally:
            self._draining = False
        await self._sync.send_sync_ack(sc_time_ns)
        self._bootstrapped = True
        self._start_quantum_loop()

    async def _quantum_loop(self) -> None:
        """Single owner of the lockstep SYNC/ack handshake."""
        assert self._sync is not None
        while True:
            sc_time_ns = await self._sync.recv_sync_quantum()
            # SC has finished the previous AdvanceTime and is parked at a boundary.
            waiters = self._quantum_waiters
            self._quantum_waiters = []
            for waiter in waiters:
                waiter.set()
            self._draining = True
            try:
                await self.drain_quantum()
            finally:
                self._draining = False
            if self._pending_reset is not None:
                assert_cycles, settle_cycles = self._pending_reset
                self._pending_reset = None
                await self._sync.send_reset(sc_time_ns, assert_cycles, settle_cycles)
                self._last_reset_axvalid = await self._sync.recv_reset_ack()
                if self._reset_done is not None:
                    self._reset_done.set()
                    self._reset_done = None
            elif self._pending_bp_cfg is not None:
                channel, mode, cycles, after_beat, after_burst, seed = self._pending_bp_cfg
                self._pending_bp_cfg = None
                await self._sync.send_bp_cfg(
                    sc_time_ns,
                    channel=channel,
                    mode=mode,
                    cycles=cycles,
                    after_beat=after_beat,
                    after_burst=after_burst,
                    seed=seed,
                )
                await self._sync.recv_bp_cfg_ack()
                if self._bp_cfg_done is not None:
                    self._bp_cfg_done.set()
                    self._bp_cfg_done = None
            else:
                await self._sync.send_sync_ack(sc_time_ns)

    async def pulse_aresetn(
        self, *, assert_cycles: int = 5, settle_cycles: int = 2
    ) -> tuple[int, int]:
        """Request a mid-sim ARESETn pulse (lockstep MSG_RESET).

        Returns ``(arvalid, awvalid)`` sampled in SystemC after assert (expect 0,0).
        """
        if self._sync is None or not self._bootstrapped:
            raise RuntimeError("pulse_aresetn requires bootstrapped lockstep sync")
        if self._pending_reset is not None:
            raise RuntimeError("pulse_aresetn already pending")
        if self._pending_bp_cfg is not None:
            raise RuntimeError("pulse_aresetn blocked by pending BP cfg")
        done = _cocotb_event_factory()
        self._reset_done = done
        self._pending_reset = (assert_cycles, settle_cycles)
        # Yield so the quantum loop can observe the pending request.
        await NullTrigger()
        await done.wait()
        return self._last_reset_axvalid

    async def arm_axi_bp(
        self,
        *,
        channel: int,
        mode: int = SOCKET_BP_MODE_FIXED,
        cycles: int = 50,
        after_beat: int = 0,
        after_burst: int = 0,
        seed: int = 0,
    ) -> None:
        """Install AXI slave back-pressure policy via lockstep MSG_BP_CFG."""
        if self._sync is None or not self._bootstrapped:
            raise RuntimeError("arm_axi_bp requires bootstrapped lockstep sync")
        if self._pending_bp_cfg is not None:
            raise RuntimeError("arm_axi_bp already pending")
        if self._pending_reset is not None:
            raise RuntimeError("arm_axi_bp blocked by pending reset")
        done = _cocotb_event_factory()
        self._bp_cfg_done = done
        self._pending_bp_cfg = (
            channel & 0xFF,
            mode & 0xFF,
            cycles & 0xFFFF,
            after_beat & 0xFFFF,
            after_burst & 0xFFFF,
            seed & 0xFFFFFFFF,
        )
        await NullTrigger()
        await done.wait()

    async def clear_axi_bp(self) -> None:
        """Clear AXI slave back-pressure policy."""
        await self.arm_axi_bp(channel=0, mode=SOCKET_BP_MODE_CLEAR, cycles=0)
    async def complete_quantum(self) -> None:
        """Block until SystemC finishes one AdvanceTime after this call.

        Unlike a bare NullTrigger, this waits for the next MSG_SYNC, which only
        arrives after SC has advanced the previous quantum's clocks. Needed so
        HDL external_reg writes become visible on the APB mirror before reads.
        """
        if not self._bootstrapped:
            return
        done = _cocotb_event_factory()
        self._quantum_waiters.append(done)
        # Let the quantum loop finish an in-progress drain / pick up the waiter.
        await NullTrigger()
        await done.wait()

    def register_gated(self, transport: SyncSocketTransport) -> None:
        if transport not in self._gated:
            self._gated.append(transport)

    def register_pollable(self, transport: SyncSocketTransport) -> None:
        if transport not in self._pollable:
            self._pollable.append(transport)

    async def drain_quantum(self) -> None:
        """Flush gated sends and read all pending replies before SC time advances."""
        while True:
            progressed = False
            for transport in self._gated:
                if transport._flush_pending_sends():
                    progressed = True
                if transport._poll_inbound_once():
                    progressed = True
            for transport in self._pollable:
                if transport._poll_inbound_once():
                    progressed = True

            pending = any(t._has_pending_io() for t in self._gated)
            queued_inbound = any(t._inbound for t in self._gated)
            if not pending and not queued_inbound:
                return
            if not progressed:
                await NullTrigger()


_LOCKSTEP_REGISTRY: LockstepRegistry | None = None


def get_lockstep_registry() -> LockstepRegistry:
    global _LOCKSTEP_REGISTRY
    if _LOCKSTEP_REGISTRY is None:
        _LOCKSTEP_REGISTRY = LockstepRegistry()
    return _LOCKSTEP_REGISTRY

# This class is used to transport messages between the cocotb/pyuvm and the systemc framework.
# It is a blocking transport, so it is used in the cocotb/pyuvm context.
# See the file docs/pyuvm_concurrency_wo_asyncio.md for more details on the concurrency issue related to the use of 
# non-blocking sockets in the cocotb/pyuvm context.
class SyncSocketTransport:
    """Blocking TCP transport for use outside an asyncio event loop (e.g. pyuvm).

    The API mirrors SocketTransport with async def methods so callers can use
    await, but all I/O is performed synchronously via the stdlib socket module.

    When ``gated=True`` and lockstep is enabled, socket I/O is deferred to the
    quantum drain handler so APB transactions are stamped at deterministic SC times.
    """

    def __init__(self, host: str, port: int, *, gated: bool = False, pollable: bool = False) -> None:
        self._host = host
        self._port = port
        self._sock: socket.socket | None = None
        self._sync_event = Event()
        self._gated = gated and lockstep_enabled()
        self._pollable = pollable and lockstep_enabled() and not self._gated
        self._pending_sends: Deque[_PendingSend] = deque()
        self._inbound: Deque[tuple[int, bytes]] = deque()
        self._recv_waiters: Deque[Event] = deque()
        self._awaiting_reply = False
        self._awaiting_recv = False
        if self._gated:
            get_lockstep_registry().register_gated(self)
        elif self._pollable:
            get_lockstep_registry().register_pollable(self)

    async def connect(self) -> None:
        if self._sock is not None:
            return
        self._sock = socket.create_connection((self._host, self._port))
        self._sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def _send_raw(self, msg_type: int, payload: bytes) -> None:
        assert self._sock is not None
        if len(payload) > 0xFFFF:
            raise ValueError("payload too large")
        hdr = HEADER_STRUCT.pack(msg_type, 0, len(payload))
        self._sock.sendall(hdr + payload)

    async def send_msg(self, msg_type: int, payload: bytes, *, expects_reply: bool = True) -> None:
        if not self._gated:
            self._send_raw(msg_type, payload)
            return

        pending = _PendingSend(msg_type, payload)
        self._pending_sends.append(pending)
        # Responses (e.g. AXI_RD_RESP) must not hold the quantum drain open —
        # under gated clocks the DUT cannot produce the next request until after
        # ack/AdvanceTime, which would deadlock if we waited for another inbound.
        self._awaiting_reply = expects_reply
        registry = get_lockstep_registry()
        if registry.draining or not registry.bootstrapped:
            self._flush_pending_sends()
        await pending.done.wait()

    def _flush_pending_sends(self) -> bool:
        if not self._pending_sends:
            return False
        while self._pending_sends:
            pending = self._pending_sends[0]
            self._send_raw(pending.msg_type, pending.payload)
            self._pending_sends.popleft()
            pending.done.set()
        return True

    def _has_pending_io(self) -> bool:
        return bool(self._pending_sends or self._awaiting_reply)

    def _deliver_inbound(self, msg_type: int, body: bytes) -> None:
        self._inbound.append((msg_type, body))
        self._awaiting_reply = False
        if self._recv_waiters:
            self._recv_waiters.popleft().set()

    def _poll_inbound_once(self) -> bool:
        assert self._sock is not None
        readable, _, _ = _select.select([self._sock], [], [], 0)
        if not readable:
            return False
        hdr = self._recvexactly(4)
        msg_type, _reserved, plen = HEADER_STRUCT.unpack(hdr)
        body = self._recvexactly(plen) if plen else b""
        self._deliver_inbound(msg_type, body)
        return True

    def _recvexactly(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("connection closed")
            buf += chunk
        return bytes(buf)

    async def _recv_raw(self) -> tuple[int, bytes]:
        """Receive one message directly from the socket (bypasses lockstep gating)."""
        assert self._sock is not None
        while True:
            readable, _, _ = _select.select([self._sock], [], [], 0)
            if readable:
                hdr = self._recvexactly(4)
                msg_type, _reserved, plen = HEADER_STRUCT.unpack(hdr)
                body = self._recvexactly(plen) if plen else b""
                return msg_type, body
            await NullTrigger()

    async def recv_msg(self) -> tuple[int, bytes]:
        """Receive one framed message without blocking the cocotb scheduler.

        Polls the socket with select() and yields NullTrigger() when no data
        is ready, letting other cocotb Tasks run between polls.
        """
        if self._gated or self._pollable:
            self._awaiting_recv = True
            try:
                while not self._inbound:
                    registry = get_lockstep_registry()
                    if registry.bootstrapped:
                        await NullTrigger()
                    else:
                        self._poll_inbound_once()
                        if not self._inbound:
                            await NullTrigger()
                return self._inbound.popleft()
            finally:
                self._awaiting_recv = False

        assert self._sock is not None
        while True:
            readable, _, _ = _select.select([self._sock], [], [], 0)
            if readable:
                hdr = self._recvexactly(4)
                msg_type, _reserved, plen = HEADER_STRUCT.unpack(hdr)
                body = self._recvexactly(plen) if plen else b""
                return msg_type, body
            await NullTrigger()

    async def recv_sync(self) -> None:
        """Wait for TB startup handshake (sent after accept, before full sc_start)."""
        msg_type, body = await self._recv_raw()
        if msg_type != MSG_SYNC or len(body) != 0:
            raise ValueError(f"expected MSG_SYNC, got type={msg_type} len={len(body)}")
        else:
            self._sync_event.set()

    async def close(self) -> None:
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    # wait for flag that indicates that the socket has established sync
    async def wait_for_sync(self) -> None:
        await self._sync_event.wait()

    async def send_python_ready(self) -> None:
        """Tell SystemC that Python finished startup and can enter lockstep."""
        self._send_raw(MSG_SYNC, b"")

    async def send_sync_ack(self, sc_time_ns: int) -> None:
        payload = SYNC_PAYLOAD_STRUCT.pack(sc_time_ns & 0xFFFFFFFFFFFFFFFF)
        self._send_raw(MSG_SYNC, payload)

    async def send_reset(
        self, sc_time_ns: int, assert_cycles: int = 5, settle_cycles: int = 2
    ) -> None:
        """Ack the current quantum with MSG_RESET (mid-sim ARESETn pulse)."""
        payload = RESET_PAYLOAD_STRUCT.pack(
            sc_time_ns & 0xFFFFFFFFFFFFFFFF,
            assert_cycles & 0xFFFF,
            settle_cycles & 0xFFFF,
        )
        self._send_raw(MSG_RESET, payload)

    async def recv_reset_ack(self) -> tuple[int, int]:
        while True:
            msg_type, body = await self._recv_raw()
            if msg_type == MSG_SHUTDOWN:
                raise ConnectionError("sync socket shutdown during reset")
            if msg_type == MSG_RESET_ACK and len(body) == RESET_ACK_PAYLOAD_STRUCT.size:
                arvalid, awvalid = RESET_ACK_PAYLOAD_STRUCT.unpack(body)
                return int(arvalid), int(awvalid)
            # Legacy empty ACK (pre-AxVALID sample).
            if msg_type == MSG_RESET_ACK and len(body) == 0:
                return 0, 0
            raise ValueError(
                f"expected MSG_RESET_ACK, got type={msg_type} len={len(body)}"
            )

    async def send_bp_cfg(
        self,
        sc_time_ns: int,
        *,
        channel: int,
        mode: int,
        cycles: int,
        after_beat: int,
        after_burst: int,
        seed: int = 0,
    ) -> None:
        """Ack the current quantum with MSG_BP_CFG (AXI slave stall policy)."""
        payload = BP_CFG_PAYLOAD_STRUCT.pack(
            sc_time_ns & 0xFFFFFFFFFFFFFFFF,
            channel & 0xFF,
            mode & 0xFF,
            cycles & 0xFFFF,
            after_beat & 0xFFFF,
            after_burst & 0xFFFF,
            seed & 0xFFFFFFFF,
        )
        self._send_raw(MSG_BP_CFG, payload)

    async def recv_bp_cfg_ack(self) -> None:
        while True:
            msg_type, body = await self._recv_raw()
            if msg_type == MSG_SHUTDOWN:
                raise ConnectionError("sync socket shutdown during BP cfg")
            if msg_type == MSG_BP_CFG_ACK and len(body) == 0:
                return
            raise ValueError(
                f"expected MSG_BP_CFG_ACK, got type={msg_type} len={len(body)}"
            )

    async def recv_sync_quantum(self) -> int:
        """Wait for a runtime lockstep MSG_SYNC carrying the quantum boundary time."""
        while True:
            msg_type, body = await self._recv_raw()
            if msg_type == MSG_SHUTDOWN:
                raise ConnectionError("sync socket shutdown during lockstep")
            if msg_type != MSG_SYNC:
                raise ValueError(f"expected MSG_SYNC, got type={msg_type} len={len(body)}")
            if len(body) == 0:
                continue
            if len(body) != SYNC_PAYLOAD_STRUCT.size:
                raise ValueError(f"expected {SYNC_PAYLOAD_STRUCT.size}-byte SYNC payload, got {len(body)}")
            (sc_time_ns,) = SYNC_PAYLOAD_STRUCT.unpack(body)
            return sc_time_ns

class SocketTransport:
    """Framed TCP transport (matches common/systemc/socketTransport)."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        self._reader, self._writer = await asyncio.open_connection(self._host, self._port)
        sock = self._writer.get_extra_info("socket")
        if sock is not None:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    async def send_msg(self, msg_type: int, payload: bytes) -> None:
        assert self._writer is not None
        if len(payload) > 0xFFFF:
            raise ValueError("payload too large")
        hdr = HEADER_STRUCT.pack(msg_type, 0, len(payload))
        self._writer.write(hdr + payload)
        await self._writer.drain()

    async def recv_msg(self) -> tuple[int, bytes]:
        assert self._reader is not None
        hdr = await self._reader.readexactly(4)
        msg_type, _reserved, plen = HEADER_STRUCT.unpack(hdr)
        body = await self._reader.readexactly(plen) if plen else b""
        return msg_type, body

    async def recv_sync(self) -> None:
        """Wait for TB startup handshake (sent after accept, before full sc_start)."""
        msg_type, body = await self.recv_msg()
        if msg_type != MSG_SYNC or len(body) != 0:
            raise ValueError(f"expected MSG_SYNC, got type={msg_type} len={len(body)}")

    async def send_python_ready(self) -> None:
        await self.send_msg(MSG_SYNC, b"")

    async def send_sync_ack(self, sc_time_ns: int) -> None:
        payload = SYNC_PAYLOAD_STRUCT.pack(sc_time_ns & 0xFFFFFFFFFFFFFFFF)
        await self.send_msg(MSG_SYNC, payload)

    async def recv_sync_quantum(self) -> int:
        while True:
            msg_type, body = await self.recv_msg()
            if msg_type == MSG_SHUTDOWN:
                raise ConnectionError("sync socket shutdown during lockstep")
            if msg_type != MSG_SYNC:
                raise ValueError(f"expected MSG_SYNC, got type={msg_type} len={len(body)}")
            if len(body) == 0:
                continue
            if len(body) != SYNC_PAYLOAD_STRUCT.size:
                raise ValueError(f"expected {SYNC_PAYLOAD_STRUCT.size}-byte SYNC payload, got {len(body)}")
            (sc_time_ns,) = SYNC_PAYLOAD_STRUCT.unpack(body)
            return sc_time_ns

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except (ConnectionError, OSError):
                pass
        self._reader = None
        self._writer = None
