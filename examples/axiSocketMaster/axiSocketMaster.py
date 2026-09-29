#!/usr/bin/env python3
"""Sidecar for axiSocketMaster: Python AXI master over TCP sockets.

Two socket shells, each wired to its own consumer memory. Python writes a
different pattern through each shell and reads it back through the same shell,
so a crossed or shared connection fails the read-back check.

Environment (set by axiSocketConfig before exec):
  PYSOCKET_PORTS — comma-separated name:port pairs from the generated catalog
  (drive, observe, and pysocket_sync). Observe sockets are connected for accept
  consistency only; this demo does not score observe traffic.
"""

from __future__ import annotations

import asyncio
import contextlib
import ctypes
import os
import sys

_EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
_CATALOG_DIR = os.path.join(_EXAMPLE_DIR, "base")
_PYSRC_DIR = os.path.abspath(os.path.join(_EXAMPLE_DIR, "..", "..", "pysrc"))
for path in (_CATALOG_DIR, _PYSRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

import pySocket
from axiSocketSocketCatalog import name_for_port, observe_name_for_port, required_names

# Match SHELL_INSTANCE0/1 in tb/axiSocket/axiSocketConfig.cpp.
SHELL_INSTANCES = ("axiSocketMaster_tb.u_axiSocket0", "axiSocketMaster_tb.u_axiSocket1")

SOCKET_AXI_BURST_BYTES = 4096
SOCKET_AXI_USER_BYTES = 8
BEAT_BYTES = 4
LOOPCOUNT = 4
BURST_LEN = 3


class socket_axi_rd_req_st(ctypes.LittleEndianStructure):
    _fields_ = [
        ("arid", ctypes.c_uint16),
        ("pad0", ctypes.c_uint8 * 2),
        ("araddr", ctypes.c_uint32),
        ("arlen", ctypes.c_uint8),
        ("arsize", ctypes.c_uint8),
        ("arburst", ctypes.c_uint8),
        ("pad1", ctypes.c_uint8),
        ("aruser", ctypes.c_uint8 * SOCKET_AXI_USER_BYTES),
    ]


class socket_axi_rd_resp_st(ctypes.LittleEndianStructure):
    _fields_ = [
        ("rid", ctypes.c_uint16),
        ("rresp", ctypes.c_uint8),
        ("pad", ctypes.c_uint8),
        ("data", ctypes.c_uint8 * SOCKET_AXI_BURST_BYTES),
        ("ruser", (ctypes.c_uint8 * SOCKET_AXI_USER_BYTES) * (SOCKET_AXI_BURST_BYTES // 16)),
    ]


class socket_axi_wr_req_st(ctypes.LittleEndianStructure):
    _fields_ = [
        ("awid", ctypes.c_uint16),
        ("pad0", ctypes.c_uint8 * 2),
        ("awaddr", ctypes.c_uint32),
        ("awlen", ctypes.c_uint8),
        ("awsize", ctypes.c_uint8),
        ("awburst", ctypes.c_uint8),
        ("pad1", ctypes.c_uint8),
        ("data", ctypes.c_uint8 * SOCKET_AXI_BURST_BYTES),
        ("strb", ctypes.c_uint16 * (SOCKET_AXI_BURST_BYTES // 16)),
        ("awuser", ctypes.c_uint8 * SOCKET_AXI_USER_BYTES),
        ("wuser", (ctypes.c_uint8 * SOCKET_AXI_USER_BYTES) * (SOCKET_AXI_BURST_BYTES // 16)),
    ]


class socket_axi_wr_resp_st(ctypes.LittleEndianStructure):
    _fields_ = [
        ("bid", ctypes.c_uint16),
        ("bresp", ctypes.c_uint8),
        ("pad", ctypes.c_uint8),
        ("buser", ctypes.c_uint8 * SOCKET_AXI_USER_BYTES),
    ]


async def drain_observe(t: pySocket.SocketTransport) -> None:
    """Keep the observe TCP socket alive for accept/handshake; discard payloads."""
    while True:
        msg_type, _body = await t.recv_msg()
        if msg_type == pySocket.MSG_SHUTDOWN:
            break


def beat_value(shell: int, loop: int, beat: int) -> int:
    """Data word for one beat; the top nibble names the shell it was written through."""
    return ((shell + 1) << 28) | (loop << 8) | beat


def burst_addr(loop: int) -> int:
    return loop * (BURST_LEN + 1) * BEAT_BYTES


async def run_axi_writes(t: pySocket.SocketTransport, shell: int) -> None:
    for loop in range(LOOPCOUNT):
        req = socket_axi_wr_req_st()
        req.awid = 0x1
        req.awaddr = burst_addr(loop)
        req.awlen = BURST_LEN
        req.awsize = 0x2
        req.awburst = 0x1  # INCR
        for beat_idx in range(BURST_LEN + 1):
            offset = beat_idx * BEAT_BYTES
            ctypes.memmove(
                ctypes.byref(req.data, offset),
                beat_value(shell, loop, beat_idx).to_bytes(BEAT_BYTES, "little"),
                BEAT_BYTES,
            )
            req.strb[beat_idx] = 0xF
        await t.send_msg(pySocket.MSG_AXI_WR_REQ, pySocket.struct_bytes(req))

        msg_type, body = await t.recv_msg()
        if msg_type != pySocket.MSG_AXI_WR_RESP or len(body) != ctypes.sizeof(socket_axi_wr_resp_st):
            raise ValueError(f"AXI write resp: type={msg_type} len={len(body)}")
        resp = socket_axi_wr_resp_st.from_buffer_copy(body)
        if resp.bid != req.awid or resp.bresp != 0:
            raise ValueError(f"AXI write resp mismatch bid={resp.bid} bresp={resp.bresp}")
        print(
            f"axiSocketMaster.py: shell {shell} write AW addr={req.awaddr:#010x} awlen={req.awlen} OK",
            flush=True,
        )


async def run_axi_reads(t: pySocket.SocketTransport, shell: int) -> None:
    for loop in range(LOOPCOUNT):
        req = socket_axi_rd_req_st()
        req.arid = 0x1
        req.araddr = burst_addr(loop)
        req.arlen = BURST_LEN
        req.arsize = 0x2
        req.arburst = 0x1  # INCR
        await t.send_msg(pySocket.MSG_AXI_RD_REQ, pySocket.struct_bytes(req))

        msg_type, body = await t.recv_msg()
        if msg_type != pySocket.MSG_AXI_RD_RESP or len(body) != ctypes.sizeof(socket_axi_rd_resp_st):
            raise ValueError(f"AXI read resp: type={msg_type} len={len(body)}")
        resp = socket_axi_rd_resp_st.from_buffer_copy(body)
        if resp.rid != req.arid or resp.rresp != 0:
            raise ValueError(f"AXI read resp mismatch rid={resp.rid} rresp={resp.rresp}")
        for beat_idx in range(BURST_LEN + 1):
            expected = beat_value(shell, loop, beat_idx)
            offset = beat_idx * BEAT_BYTES
            got = int.from_bytes(bytes(resp.data[offset : offset + BEAT_BYTES]), "little")
            if got != expected:
                raise ValueError(
                    f"AXI read data mismatch shell={shell} loop={loop} beat={beat_idx} "
                    f"got={got:#010x} exp={expected:#010x}"
                )
        print(
            f"axiSocketMaster.py: shell {shell} read AR addr={req.araddr:#010x} arlen={req.arlen} OK",
            flush=True,
        )


async def run_shell(tr_rd: pySocket.SocketTransport, tr_wr: pySocket.SocketTransport, shell: int) -> None:
    """Write this shell's pattern, then read it back through the same shell."""
    await run_axi_writes(tr_wr, shell)
    await run_axi_reads(tr_rd, shell)


async def shutdown_all(*transports: pySocket.SocketTransport) -> None:
    for t in transports:
        await t.send_msg(pySocket.MSG_SHUTDOWN, b"")
    for t in transports:
        await t.close()


async def main(argv: list[str]) -> None:
    ports_file = argv[0] if argv else None
    ports = pySocket.parse_ports(ports_file)
    for instance in SHELL_INSTANCES:
        for name in required_names(instance):
            if name not in ports:
                print(f"axiSocketMaster.py: missing {name} in PYSOCKET_PORTS", file=sys.stderr)
                sys.exit(1)

    def transport(name: str) -> pySocket.SocketTransport:
        return pySocket.SocketTransport("127.0.0.1", ports[name])

    tr_rd = [transport(name_for_port("axiRd0", inst)) for inst in SHELL_INSTANCES]
    tr_wr = [transport(name_for_port("axiWr0", inst)) for inst in SHELL_INSTANCES]
    tr_obs = [transport(observe_name_for_port(port, inst))
              for inst in SHELL_INSTANCES for port in ("axiRd0", "axiWr0")]
    tr_sync = transport(pySocket.PYSOCKET_SYNC_IFC)

    shell_transports = (*tr_rd, *tr_wr, *tr_obs)
    transports = (*shell_transports, tr_sync)
    await asyncio.gather(*(t.connect() for t in transports))
    await asyncio.gather(*(t.recv_sync() for t in transports))
    print("axiSocketMaster.py: connected (synced)", flush=True)

    obs_tasks = [asyncio.create_task(drain_observe(t)) for t in tr_obs]

    sync_task = None
    if pySocket.lockstep_enabled():
        async def _quantum_sync_loop() -> None:
            while True:
                sc_time_ns = await tr_sync.recv_sync_quantum()
                await tr_sync.send_sync_ack(sc_time_ns)

        sync_task = asyncio.create_task(_quantum_sync_loop())
        await tr_sync.send_python_ready()

    try:
        await asyncio.gather(*(run_shell(tr_rd[k], tr_wr[k], k) for k in range(len(SHELL_INSTANCES))))
    finally:
        await shutdown_all(*shell_transports)
        for task in obs_tasks:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        if sync_task is not None:
            with contextlib.suppress(Exception):
                await sync_task
            await tr_sync.close()
    print("axiSocketMaster.py: done", flush=True)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
