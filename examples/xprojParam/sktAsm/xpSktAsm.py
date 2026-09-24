#!/usr/bin/env python3
"""Sidecar for sktAsm: pushes four samples through uLeaf's socket shell.

The shell is xpSktLeafSocket at xpSktAsm's own `asm` Config (SK_PIXEL_WIDTH
12); xpSktChk checks every sample and ends the test.
"""

from __future__ import annotations

import asyncio
import ctypes
import os
import sys

_EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
_CATALOG_DIR = os.path.join(_EXAMPLE_DIR, "..", "sktIp", "base")
_PYSRC_DIR = os.path.abspath(os.path.join(_EXAMPLE_DIR, "..", "..", "..", "pysrc"))
for path in (_CATALOG_DIR, _PYSRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

import pySocket
from xpSktLeafSocketCatalog import name_for_port, required_names

# Matches LEAF_INSTANCE in tb/xpSktAsmTop/xpSktAsmTopConfig.cpp.
LEAF_INSTANCE = "xpSktAsmTop.uLeaf"
SAMPLE_COUNT = 4
FIRST_PIXEL = 0x10


# Memory image of skSampleSt_v<12>: the uint64_t pixel, then the uint8_t tag.
class sk_sample_st(ctypes.LittleEndianStructure):
    _fields_ = [
        ("data", ctypes.c_uint64),
        ("tag", ctypes.c_uint8),
    ]


async def main(argv: list[str]) -> None:
    ports = pySocket.parse_ports(argv[0] if argv else None)
    for name in required_names(LEAF_INSTANCE):
        if name not in ports:
            print(f"xpSktAsm.py: missing {name} in PYSOCKET_PORTS", file=sys.stderr)
            sys.exit(1)

    tr_out = pySocket.SocketTransport("127.0.0.1", ports[name_for_port("out", LEAF_INSTANCE)])
    await tr_out.connect()
    await tr_out.recv_sync()
    for i in range(SAMPLE_COUNT):
        sample = sk_sample_st(data=FIRST_PIXEL + i, tag=i)
        await tr_out.send_msg(pySocket.MSG_PUSH, pySocket.struct_bytes(sample))
        msg_type, body = await tr_out.recv_msg()
        if msg_type != pySocket.MSG_PUSH_ACK or body:
            raise ValueError(f"push ack: type={msg_type} len={len(body)}")
        print(f"xpSktAsm.py: pushed tag {i} data {FIRST_PIXEL + i:#x}", flush=True)
    await tr_out.send_msg(pySocket.MSG_SHUTDOWN, b"")
    await tr_out.close()
    print("xpSktAsm.py: done", flush=True)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
