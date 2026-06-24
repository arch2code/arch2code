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
from cocotb.triggers import Event, NullTrigger

MSG_REQ = 0x01
MSG_ACK = 0x02
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
MSG_SHUTDOWN = 0xFE

HEADER_STRUCT = struct.Struct("<BBH")

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

# This class is used to transport messages between the cocotb/pyuvm and the systemc framework.
# It is a blocking transport, so it is used in the cocotb/pyuvm context.
# See the file docs/pyuvm_concurrency_wo_asyncio.md for more details on the concurrency issue related to the use of 
# non-blocking sockets in the cocotb/pyuvm context.
class SyncSocketTransport:
    """Blocking TCP transport for use outside an asyncio event loop (e.g. pyuvm).

    The API mirrors SocketTransport with async def methods so callers can use
    await, but all I/O is performed synchronously via the stdlib socket module.
    """

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._sock: socket.socket | None = None
        self._sync_event = Event()

    async def connect(self) -> None:
        self._sock = socket.create_connection((self._host, self._port))

    async def send_msg(self, msg_type: int, payload: bytes) -> None:
        assert self._sock is not None
        if len(payload) > 0xFFFF:
            raise ValueError("payload too large")
        hdr = HEADER_STRUCT.pack(msg_type, 0, len(payload))
        self._sock.sendall(hdr + payload)

    def _recvexactly(self, n: int) -> bytes:
        buf = bytearray()
        while len(buf) < n:
            chunk = self._sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("connection closed")
            buf += chunk
        return bytes(buf)

    async def recv_msg(self) -> tuple[int, bytes]:
        """Receive one framed message without blocking the cocotb scheduler.

        Polls the socket with select() and yields NullTrigger() when no data
        is ready, letting other cocotb Tasks run between polls.
        """
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
        msg_type, body = await self.recv_msg()
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

class SocketTransport:
    """Framed TCP transport (matches common/systemc/socketTransport)."""

    def __init__(self, host: str, port: int) -> None:
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    async def connect(self) -> None:
        self._reader, self._writer = await asyncio.open_connection(self._host, self._port)

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

    async def close(self) -> None:
        if self._writer is not None:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except (ConnectionError, OSError):
                pass
        self._reader = None
        self._writer = None
