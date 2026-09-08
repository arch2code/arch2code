#!/usr/bin/env python3
"""Sidecar for axiSocketSlave: Python AXI memory slave (read + write) over TCP sockets.

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

SOCKET_AXI_BURST_BYTES = 4096
BEAT_BYTES = 4


class socket_axi_rd_req_st(ctypes.LittleEndianStructure):
    _fields_ = [
        ("arid", ctypes.c_uint8),
        ("pad0", ctypes.c_uint8 * 3),
        ("araddr", ctypes.c_uint32),
        ("arlen", ctypes.c_uint8),
        ("arsize", ctypes.c_uint8),
        ("arburst", ctypes.c_uint8),
        ("pad1", ctypes.c_uint8),
    ]


class socket_axi_rd_resp_st(ctypes.LittleEndianStructure):
    _fields_ = [
        ("rid", ctypes.c_uint8),
        ("rresp", ctypes.c_uint8),
        ("pad", ctypes.c_uint8 * 2),
        ("data", ctypes.c_uint8 * SOCKET_AXI_BURST_BYTES),
    ]


class socket_axi_wr_req_st(ctypes.LittleEndianStructure):
    _fields_ = [
        ("awid", ctypes.c_uint8),
        ("pad0", ctypes.c_uint8 * 3),
        ("awaddr", ctypes.c_uint32),
        ("awlen", ctypes.c_uint8),
        ("awsize", ctypes.c_uint8),
        ("awburst", ctypes.c_uint8),
        ("pad1", ctypes.c_uint8),
        ("data", ctypes.c_uint8 * SOCKET_AXI_BURST_BYTES),
        ("strb", ctypes.c_uint16 * (SOCKET_AXI_BURST_BYTES // 16)),
    ]


class socket_axi_wr_resp_st(ctypes.LittleEndianStructure):
    _fields_ = [
        ("bid", ctypes.c_uint8),
        ("bresp", ctypes.c_uint8),
        ("pad", ctypes.c_uint8 * 2),
    ]


class HostMemory:
    def __init__(self) -> None:
        self._mem: dict[int, int] = {}

    def write_beat(self, addr: int, beat: bytes, strb: int) -> None:
        for byte_idx in range(BEAT_BYTES):
            if strb & (1 << byte_idx):
                self._mem[(addr + byte_idx) & 0xFFFFFFFF] = beat[byte_idx]


async def axi_read_slave(t: pySocket.SocketTransport) -> None:
    while True:
        msg_type, body = await t.recv_msg()
        if msg_type == pySocket.MSG_SHUTDOWN:
            break
        if msg_type == pySocket.MSG_SYNC:
            continue
        if msg_type != pySocket.MSG_AXI_RD_REQ or len(body) != ctypes.sizeof(socket_axi_rd_req_st):
            raise ValueError(f"AXI read req: type={msg_type} len={len(body)}")

        req = socket_axi_rd_req_st.from_buffer_copy(body)
        beat_count = int(req.arlen) + 1
        byte_count = beat_count * BEAT_BYTES
        if byte_count > SOCKET_AXI_BURST_BYTES:
            raise ValueError(f"AXI read burst too large: arlen={req.arlen}")

        resp = socket_axi_rd_resp_st()
        resp.rid = req.arid
        resp.rresp = 0
        for beat_idx in range(beat_count):
            value = (beat_idx * 0x01010101) & 0xFFFFFFFF
            beat_bytes = value.to_bytes(BEAT_BYTES, byteorder="little")
            offset = beat_idx * BEAT_BYTES
            ctypes.memmove(
                ctypes.byref(resp.data, offset),
                beat_bytes,
                BEAT_BYTES,
            )
        await t.send_msg(pySocket.MSG_AXI_RD_RESP, pySocket.struct_bytes(resp))
        print(
            f"axiSocketSlave.py: read AR addr={req.araddr:#010x} arlen={req.arlen}",
            flush=True,
        )


async def axi_write_slave(t: pySocket.SocketTransport, memory: HostMemory) -> None:
    while True:
        msg_type, body = await t.recv_msg()
        if msg_type == pySocket.MSG_SHUTDOWN:
            break
        if msg_type == pySocket.MSG_SYNC:
            continue
        if msg_type != pySocket.MSG_AXI_WR_REQ or len(body) != ctypes.sizeof(socket_axi_wr_req_st):
            raise ValueError(f"AXI write req: type={msg_type} len={len(body)}")

        req = socket_axi_wr_req_st.from_buffer_copy(body)
        beat_count = int(req.awlen) + 1
        byte_count = beat_count * BEAT_BYTES
        burst_data = bytes(req.data[:byte_count])
        for beat_idx in range(beat_count):
            beat_addr = req.awaddr + beat_idx * BEAT_BYTES
            beat = burst_data[beat_idx * BEAT_BYTES : (beat_idx + 1) * BEAT_BYTES]
            memory.write_beat(beat_addr, beat, int(req.strb[beat_idx]) & 0xFFFF)

        resp = socket_axi_wr_resp_st()
        resp.bid = req.awid
        resp.bresp = 0
        await t.send_msg(pySocket.MSG_AXI_WR_RESP, pySocket.struct_bytes(resp))
        print(
            f"axiSocketSlave.py: write AW addr={req.awaddr:#010x} awlen={req.awlen}",
            flush=True,
        )


async def drain_observe(t: pySocket.SocketTransport) -> None:
    """Keep the observe TCP socket alive for accept/handshake; discard payloads."""
    while True:
        msg_type, _body = await t.recv_msg()
        if msg_type == pySocket.MSG_SHUTDOWN:
            break


async def shutdown_all(*transports: pySocket.SocketTransport) -> None:
    for t in transports:
        await t.send_msg(pySocket.MSG_SHUTDOWN, b"")
    for t in transports:
        await t.close()


async def main(argv: list[str]) -> None:
    ports_file = argv[0] if argv else None
    ports = pySocket.parse_ports(ports_file)
    for name in required_names():
        if name not in ports:
            print(f"axiSocketSlave.py: missing {name} in PYSOCKET_PORTS", file=sys.stderr)
            sys.exit(1)

    tr_rd = pySocket.SocketTransport("127.0.0.1", ports[name_for_port("axiRd0")])
    tr_wr = pySocket.SocketTransport("127.0.0.1", ports[name_for_port("axiWr0")])
    tr_rd_obs = pySocket.SocketTransport("127.0.0.1", ports[observe_name_for_port("axiRd0")])
    tr_wr_obs = pySocket.SocketTransport("127.0.0.1", ports[observe_name_for_port("axiWr0")])
    tr_sync = pySocket.SocketTransport("127.0.0.1", ports[pySocket.PYSOCKET_SYNC_IFC])

    transports = (tr_rd, tr_wr, tr_rd_obs, tr_wr_obs, tr_sync)
    await asyncio.gather(*(t.connect() for t in transports))
    await asyncio.gather(*(t.recv_sync() for t in transports))
    print("axiSocketSlave.py: connected (synced)", flush=True)

    memory = HostMemory()
    rd_task = asyncio.create_task(axi_read_slave(tr_rd))
    wr_task = asyncio.create_task(axi_write_slave(tr_wr, memory))
    rd_obs_task = asyncio.create_task(drain_observe(tr_rd_obs))
    wr_obs_task = asyncio.create_task(drain_observe(tr_wr_obs))

    sync_task = None
    if pySocket.lockstep_enabled():
        async def _quantum_sync_loop() -> None:
            while True:
                sc_time_ns = await tr_sync.recv_sync_quantum()
                await tr_sync.send_sync_ack(sc_time_ns)

        sync_task = asyncio.create_task(_quantum_sync_loop())
        await tr_sync.send_python_ready()

    try:
        await asyncio.gather(rd_task, wr_task)
    finally:
        await shutdown_all(tr_rd, tr_wr, tr_rd_obs, tr_wr_obs)
        for task in (rd_task, wr_task, rd_obs_task, wr_obs_task):
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        if sync_task is not None:
            with contextlib.suppress(Exception):
                await sync_task
            await tr_sync.close()
    print("axiSocketSlave.py: done", flush=True)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
