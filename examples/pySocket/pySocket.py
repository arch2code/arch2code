#!/usr/bin/env python3
"""Sidecar process for pySocket: one TCP connection per req_ack interface (see socketFactory).

Environment (set by pySocketConfig before exec):
  PYSOCKET_PORTS — comma-separated name:port pairs, e.g.
    test_req_ack:54321,test2Python_req_ack:54322,dut2Python_req_ack:54323

Override script path with absolute PYSOCKET_PY_SCRIPT if the binary is not under the usual
rundir/build layout.
"""

from __future__ import annotations

import asyncio
import ctypes
import os
import struct
import sys

MSG_REQ = 0x01
MSG_ACK = 0x02
MSG_SYNC = 0x07
MSG_SHUTDOWN = 0xFE

HEADER_STRUCT = struct.Struct("<BBH")


class p2s_message_st(ctypes.LittleEndianStructure):
    _fields_ = [("param1", ctypes.c_uint32), ("param2", ctypes.c_uint32)]


class p2s_response_st(ctypes.LittleEndianStructure):
    _fields_ = [("response", ctypes.c_uint32)]


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


async def python2systemc_test(t: SocketTransport) -> None:
    transactions = [(1, 2), (3, 4)]
    for param1, param2 in transactions:
        req = p2s_message_st(param1, param2)
        await t.send_msg(MSG_REQ, struct_bytes(req))
        msg_type, body = await t.recv_msg()
        if msg_type != MSG_ACK or len(body) != ctypes.sizeof(p2s_response_st):
            raise ValueError(f"unexpected reply on test_req_ack: type={msg_type} len={len(body)}")
        ack = p2s_response_st.from_buffer_copy(body)
        expected = param1 + param2
        if ack.response != expected:
            raise ValueError(f"sum mismatch: got {ack.response} expected {expected}")
        print(f"pySocket.py: test_req_ack {param1}+{param2} -> {ack.response}", flush=True)
    await t.send_msg(MSG_SHUTDOWN, b"")
    await t.close()


async def systemc2python_test(t: SocketTransport) -> None:
    seq = [
        ((0xCAFEF00D, 0x12345678), 0xDEADBEEF),
        ((1, 2), 3),
        ((0, 0), 0),
    ]
    for (p1, p2), want in seq:
        req = p2s_message_st(p1, p2)
        await t.send_msg(MSG_REQ, struct_bytes(req))
        msg_type, body = await t.recv_msg()
        if msg_type != MSG_ACK or len(body) != ctypes.sizeof(p2s_response_st):
            raise ValueError(f"unexpected reply on test2Python: type={msg_type} len={len(body)}")
        ack = p2s_response_st.from_buffer_copy(body)
        if ack.response != want:
            raise ValueError(f"test2Python mismatch: got {ack.response:#x} want {want:#x}")
        print(f"pySocket.py: test2Python_req_ack ({p1:#x},{p2:#x}) -> {ack.response:#x}", flush=True)
    await t.send_msg(MSG_SHUTDOWN, b"")
    await t.close()


async def dut2python_target(t: SocketTransport) -> None:
    while True:
        msg_type, body = await t.recv_msg()
        if msg_type == MSG_SHUTDOWN:
            break
        if msg_type != MSG_REQ or len(body) != ctypes.sizeof(p2s_message_st):
            raise ValueError(f"dut2Python: bad message type={msg_type} len={len(body)}")
        req = p2s_message_st.from_buffer_copy(body)
        if req.param1 == 0xCAFEF00D and req.param2 == 0x12345678:
            rsp = p2s_response_st(0xDEADBEEF)
        elif req.param1 == 0 and req.param2 == 0:
            rsp = p2s_response_st(0)
        else:
            rsp = p2s_response_st(req.param1 + req.param2)
        print(
            f"pySocket.py: dut2Python_req_ack req ({req.param1:#x},{req.param2:#x}) -> {rsp.response:#x}",
            flush=True,
        )
        await t.send_msg(MSG_ACK, struct_bytes(rsp))


async def main(argv: list[str]) -> None:
    if len(argv) >= 1:
        ports_file = argv[0]
    else:
        ports_file = None
    ports = parse_ports(ports_file)
    required = ("test_req_ack", "test2Python_req_ack", "dut2Python_req_ack")
    for name in required:
        if name not in ports:
            print(f"pySocket.py: missing {name} in PYSOCKET_PORTS", file=sys.stderr)
            sys.exit(1)

    tr_test = SocketTransport("127.0.0.1", ports["test_req_ack"])
    tr_test2 = SocketTransport("127.0.0.1", ports["test2Python_req_ack"])
    tr_dut = SocketTransport("127.0.0.1", ports["dut2Python_req_ack"])
    await asyncio.gather(tr_test.connect(), tr_test2.connect(), tr_dut.connect())
    await asyncio.gather(tr_test.recv_sync(), tr_test2.recv_sync(), tr_dut.recv_sync())
    print("pySocket.py: connected all interfaces (synced)", flush=True)

    dut_task = asyncio.create_task(dut2python_target(tr_dut))
    await python2systemc_test(tr_test)
    await systemc2python_test(tr_test2)
    # Tell the SystemC target bridge to exit; matches finite DUT traffic on dut2Python.
    await tr_dut.send_msg(MSG_SHUTDOWN, b"")
    try:
        await asyncio.wait_for(dut_task, timeout=5.0)
    except asyncio.TimeoutError:
        dut_task.cancel()
        try:
            await dut_task
        except asyncio.CancelledError:
            pass
    await tr_dut.close()
    print("pySocket.py: done", flush=True)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
