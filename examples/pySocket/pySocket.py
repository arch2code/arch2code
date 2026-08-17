#!/usr/bin/env python3
"""Sidecar process for pySocket: one TCP connection per interface (see socketFactory).

Environment (set by pySocketConfig before exec):
  PYSOCKET_PORTS — comma-separated name:port pairs, e.g.
    pySocket.test_req_ack:54321,pySocket.test2Python_req_ack:54322

Override script path with absolute PYSOCKET_PY_SCRIPT if the binary is not under the usual
rundir/build layout.
"""

from __future__ import annotations

import asyncio
import ctypes
import os
import struct
import sys

_CATALOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "base")
if _CATALOG_DIR not in sys.path:
    sys.path.insert(0, _CATALOG_DIR)
from pySocketSocketCatalog import name_for_port, required_names

MSG_REQ = 0x01
MSG_ACK = 0x02
MSG_PUSH = 0x03
MSG_PUSH_ACK = 0x04
MSG_VLD = 0x05
MSG_RDY = 0x06
MSG_SYNC = 0x07
MSG_POP = 0x19
MSG_POP_ACK = 0x1A
MSG_NOTIFY = 0x1B
MSG_NOTIFY_ACK = 0x1C
MSG_SHUTDOWN = 0xFE

HEADER_STRUCT = struct.Struct("<BBH")

# test2Python_req_ack param1 that asks the DUT to push/pop Python instead of req_ack.
DUT_PUSH_POP_CMD = 0x50555348
DUT_NOTIFY_CMD = 0x4E4F5449
DUT_NOTIFY_ACK = 0xA11C
DUT_RDY_VLD_CMD = 0x52445956
PUSH_POP_BIAS = 1
RDY_VLD_BIAS = 2


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


def _derived_response(param1: int, param2: int) -> int:
    return (param1 + param2 + PUSH_POP_BIAS) & 0xFFFFFFFF


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


async def python_push_pop_test(tr_push: SocketTransport, tr_pop: SocketTransport) -> None:
    transactions = [(5, 7), (10, 20)]
    for param1, param2 in transactions:
        req = p2s_message_st(param1, param2)
        await tr_push.send_msg(MSG_PUSH, struct_bytes(req))
        msg_type, body = await tr_push.recv_msg()
        if msg_type != MSG_PUSH_ACK or len(body) != 0:
            raise ValueError(f"unexpected PUSH_ACK: type={msg_type} len={len(body)}")
        await tr_pop.send_msg(MSG_POP, b"")
        msg_type, body = await tr_pop.recv_msg()
        if msg_type != MSG_POP_ACK or len(body) != ctypes.sizeof(p2s_response_st):
            raise ValueError(f"unexpected POP_ACK: type={msg_type} len={len(body)}")
        ack = p2s_response_st.from_buffer_copy(body)
        expected = _derived_response(param1, param2)
        if ack.response != expected:
            raise ValueError(f"push/pop mismatch: got {ack.response} expected {expected}")
        print(
            f"pySocket.py: test_push/pop {param1}+{param2}+{PUSH_POP_BIAS} -> {ack.response}",
            flush=True,
        )
    await tr_push.send_msg(MSG_SHUTDOWN, b"")
    await tr_pop.send_msg(MSG_SHUTDOWN, b"")
    await tr_push.close()
    await tr_pop.close()


async def python_notify_test(t: SocketTransport) -> None:
    for i in range(2):
        await t.send_msg(MSG_NOTIFY, b"")
        msg_type, body = await t.recv_msg()
        if msg_type != MSG_NOTIFY_ACK or len(body) != 0:
            raise ValueError(f"unexpected NOTIFY_ACK: type={msg_type} len={len(body)}")
        print(f"pySocket.py: test_notify_ack handshake {i}", flush=True)
    await t.send_msg(MSG_SHUTDOWN, b"")
    await t.close()


async def python_rdy_vld_test(t: SocketTransport) -> None:
    transactions = [(6, 8), (11, 21)]
    for param1, param2 in transactions:
        req = p2s_message_st(param1, param2)
        await t.send_msg(MSG_VLD, struct_bytes(req))
        msg_type, body = await t.recv_msg()
        if msg_type != MSG_RDY or len(body) != 0:
            raise ValueError(f"unexpected RDY: type={msg_type} len={len(body)}")
        print(f"pySocket.py: test_rdy_vld write ({param1},{param2})", flush=True)
    await t.send_msg(MSG_SHUTDOWN, b"")
    await t.close()


async def dut_push_pop_via_req_test(tr_req: SocketTransport) -> None:
    param1, param2 = DUT_PUSH_POP_CMD, 0x11
    req = p2s_message_st(param1, param2)
    await tr_req.send_msg(MSG_REQ, struct_bytes(req))
    msg_type, body = await tr_req.recv_msg()
    if msg_type != MSG_ACK or len(body) != ctypes.sizeof(p2s_response_st):
        raise ValueError(f"unexpected reply on DUT push/pop req: type={msg_type} len={len(body)}")
    ack = p2s_response_st.from_buffer_copy(body)
    expected = _derived_response(param1, param2)
    if ack.response != expected:
        raise ValueError(f"DUT push/pop req mismatch: got {ack.response:#x} want {expected:#x}")
    print(
        f"pySocket.py: test2Python DUT push/pop ({param1:#x},{param2:#x}) -> {ack.response:#x}",
        flush=True,
    )


async def dut_notify_via_req_test(tr_req: SocketTransport) -> None:
    param1, param2 = DUT_NOTIFY_CMD, 0
    req = p2s_message_st(param1, param2)
    await tr_req.send_msg(MSG_REQ, struct_bytes(req))
    msg_type, body = await tr_req.recv_msg()
    if msg_type != MSG_ACK or len(body) != ctypes.sizeof(p2s_response_st):
        raise ValueError(f"unexpected reply on DUT notify req: type={msg_type} len={len(body)}")
    ack = p2s_response_st.from_buffer_copy(body)
    if ack.response != DUT_NOTIFY_ACK:
        raise ValueError(f"DUT notify req mismatch: got {ack.response:#x} want {DUT_NOTIFY_ACK:#x}")
    print(
        f"pySocket.py: test2Python DUT notify ({param1:#x}) -> {ack.response:#x}",
        flush=True,
    )


async def dut_rdy_vld_via_req_test(tr_req: SocketTransport) -> None:
    param1, param2 = DUT_RDY_VLD_CMD, 0x22
    req = p2s_message_st(param1, param2)
    await tr_req.send_msg(MSG_REQ, struct_bytes(req))
    msg_type, body = await tr_req.recv_msg()
    if msg_type != MSG_ACK or len(body) != ctypes.sizeof(p2s_response_st):
        raise ValueError(f"unexpected reply on DUT rdy_vld req: type={msg_type} len={len(body)}")
    ack = p2s_response_st.from_buffer_copy(body)
    expected = (param1 + param2 + RDY_VLD_BIAS) & 0xFFFFFFFF
    if ack.response != expected:
        raise ValueError(f"DUT rdy_vld req mismatch: got {ack.response:#x} want {expected:#x}")
    print(
        f"pySocket.py: test2Python DUT rdy_vld ({param1:#x},{param2:#x}) -> {ack.response:#x}",
        flush=True,
    )
    await tr_req.send_msg(MSG_SHUTDOWN, b"")
    await tr_req.close()


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


class _LastPush:
    msg: p2s_message_st | None = None


async def dut2python_push_target(t: SocketTransport, last: _LastPush) -> None:
    while True:
        msg_type, body = await t.recv_msg()
        if msg_type == MSG_SHUTDOWN:
            break
        if msg_type != MSG_PUSH or len(body) != ctypes.sizeof(p2s_message_st):
            raise ValueError(f"dut2Python_push: bad message type={msg_type} len={len(body)}")
        last.msg = p2s_message_st.from_buffer_copy(body)
        print(
            f"pySocket.py: dut2Python_push_ack ({last.msg.param1:#x},{last.msg.param2:#x})",
            flush=True,
        )
        await t.send_msg(MSG_PUSH_ACK, b"")


async def dut2python_pop_target(t: SocketTransport, last: _LastPush) -> None:
    while True:
        msg_type, body = await t.recv_msg()
        if msg_type == MSG_SHUTDOWN:
            break
        if msg_type != MSG_POP or len(body) != 0:
            raise ValueError(f"dut2Python_pop: bad message type={msg_type} len={len(body)}")
        if last.msg is None:
            raise ValueError("dut2Python_pop: POP before PUSH")
        rsp = p2s_response_st(_derived_response(last.msg.param1, last.msg.param2))
        print(
            f"pySocket.py: dut2Python_pop_ack -> {rsp.response:#x}",
            flush=True,
        )
        await t.send_msg(MSG_POP_ACK, struct_bytes(rsp))


async def dut2python_notify_target(t: SocketTransport) -> None:
    while True:
        msg_type, body = await t.recv_msg()
        if msg_type == MSG_SHUTDOWN:
            break
        if msg_type != MSG_NOTIFY or len(body) != 0:
            raise ValueError(f"dut2Python_notify: bad message type={msg_type} len={len(body)}")
        print("pySocket.py: dut2Python_notify_ack", flush=True)
        await t.send_msg(MSG_NOTIFY_ACK, b"")


async def dut2python_rdy_vld_target(t: SocketTransport) -> None:
    while True:
        msg_type, body = await t.recv_msg()
        if msg_type == MSG_SHUTDOWN:
            break
        if msg_type != MSG_VLD or len(body) != ctypes.sizeof(p2s_message_st):
            raise ValueError(f"dut2Python_rdy_vld: bad message type={msg_type} len={len(body)}")
        msg = p2s_message_st.from_buffer_copy(body)
        print(
            f"pySocket.py: dut2Python_rdy_vld ({msg.param1:#x},{msg.param2:#x})",
            flush=True,
        )
        await t.send_msg(MSG_RDY, b"")


async def _wait_task(task: asyncio.Task) -> None:
    try:
        await asyncio.wait_for(task, timeout=5.0)
    except asyncio.TimeoutError:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def main(argv: list[str]) -> None:
    if len(argv) >= 1:
        ports_file = argv[0]
    else:
        ports_file = None
    ports = parse_ports(ports_file)
    required = required_names()
    for name in required:
        if name not in ports:
            print(f"pySocket.py: missing {name} in PYSOCKET_PORTS", file=sys.stderr)
            sys.exit(1)

    tr_test = SocketTransport("127.0.0.1", ports[name_for_port("test_req_ack")])
    tr_test2 = SocketTransport("127.0.0.1", ports[name_for_port("test2Python_req_ack")])
    tr_dut = SocketTransport("127.0.0.1", ports[name_for_port("dut2Python_req_ack")])
    tr_push = SocketTransport("127.0.0.1", ports[name_for_port("test_push_ack")])
    tr_pop = SocketTransport("127.0.0.1", ports[name_for_port("test_pop_ack")])
    tr_dut_push = SocketTransport("127.0.0.1", ports[name_for_port("dut2Python_push_ack")])
    tr_dut_pop = SocketTransport("127.0.0.1", ports[name_for_port("dut2Python_pop_ack")])
    tr_notify = SocketTransport("127.0.0.1", ports[name_for_port("test_notify_ack")])
    tr_dut_notify = SocketTransport("127.0.0.1", ports[name_for_port("dut2Python_notify_ack")])
    tr_rdy_vld = SocketTransport("127.0.0.1", ports[name_for_port("test_rdy_vld")])
    tr_dut_rdy_vld = SocketTransport("127.0.0.1", ports[name_for_port("dut2Python_rdy_vld")])
    await asyncio.gather(
        tr_test.connect(),
        tr_test2.connect(),
        tr_dut.connect(),
        tr_push.connect(),
        tr_pop.connect(),
        tr_dut_push.connect(),
        tr_dut_pop.connect(),
        tr_notify.connect(),
        tr_dut_notify.connect(),
        tr_rdy_vld.connect(),
        tr_dut_rdy_vld.connect(),
    )
    await asyncio.gather(
        tr_test.recv_sync(),
        tr_test2.recv_sync(),
        tr_dut.recv_sync(),
        tr_push.recv_sync(),
        tr_pop.recv_sync(),
        tr_dut_push.recv_sync(),
        tr_dut_pop.recv_sync(),
        tr_notify.recv_sync(),
        tr_dut_notify.recv_sync(),
        tr_rdy_vld.recv_sync(),
        tr_dut_rdy_vld.recv_sync(),
    )
    print("pySocket.py: connected all interfaces (synced)", flush=True)

    last_push = _LastPush()
    dut_task = asyncio.create_task(dut2python_target(tr_dut))
    dut_push_task = asyncio.create_task(dut2python_push_target(tr_dut_push, last_push))
    dut_pop_task = asyncio.create_task(dut2python_pop_target(tr_dut_pop, last_push))
    dut_notify_task = asyncio.create_task(dut2python_notify_target(tr_dut_notify))
    dut_rdy_vld_task = asyncio.create_task(dut2python_rdy_vld_target(tr_dut_rdy_vld))
    await python2systemc_test(tr_test)
    await python_push_pop_test(tr_push, tr_pop)
    await python_notify_test(tr_notify)
    await python_rdy_vld_test(tr_rdy_vld)
    await systemc2python_test(tr_test2)
    await dut_push_pop_via_req_test(tr_test2)
    await dut_notify_via_req_test(tr_test2)
    await dut_rdy_vld_via_req_test(tr_test2)
    await tr_dut.send_msg(MSG_SHUTDOWN, b"")
    await tr_dut_push.send_msg(MSG_SHUTDOWN, b"")
    await tr_dut_pop.send_msg(MSG_SHUTDOWN, b"")
    await tr_dut_notify.send_msg(MSG_SHUTDOWN, b"")
    await tr_dut_rdy_vld.send_msg(MSG_SHUTDOWN, b"")
    await _wait_task(dut_task)
    await _wait_task(dut_push_task)
    await _wait_task(dut_pop_task)
    await _wait_task(dut_notify_task)
    await _wait_task(dut_rdy_vld_task)
    await tr_dut.close()
    await tr_dut_push.close()
    await tr_dut_pop.close()
    await tr_dut_notify.close()
    await tr_dut_rdy_vld.close()
    print("pySocket.py: done", flush=True)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
