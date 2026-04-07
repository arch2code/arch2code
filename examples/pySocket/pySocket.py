#!/usr/bin/env python3
"""Sidecar process for pySocket: two TCP connections to SystemC (see pySocketIpc).

Environment (set by pySocketConfig before exec):
  PYSOCKET_SC2PY_PORT  — SystemC writes, Python reads (this process recv()s here).
  PYSOCKET_PY2SC_PORT  — Python writes, SystemC reads (this process send()s here).

The C++ side resolves pySocket.py from the simulator binary path (.../rundir/build/run →
.../pySocket.py), so the process working directory does not matter. Override with an absolute
PYSOCKET_PY_SCRIPT if the binary is not under the usual rundir/build layout.
"""

import os
import socket
import sys
import struct
import asyncio

class PyTransaction:
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2
        self.packer = struct.Struct('I I') # 4 bytes for int, 4 bytes for int

    def to_bytes(self):
        return self.packer.pack(self.param1, self.param2)

def connect_pair(request_port, response_port):
    print(f"connect_pair: {request_port}, {response_port}", flush=True)
    try:
        p_request = int(os.environ[request_port])
        p_response = int(os.environ[response_port])
    except (KeyError, ValueError) as exc:
        print("pySocket.py: missing or invalid PYSOCKET_*_PORT", exc, file=sys.stderr)
        sys.exit(1)

    s_request = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_response = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_request.connect(("127.0.0.1", p_request))
    s_response.connect(("127.0.0.1", p_response))
    return s_request, s_response

def connect_pair_py2sc():
    return connect_pair("PYSOCKET_PY2SC_REQUEST_PORT", "PYSOCKET_PY2SC_RESPONSE_PORT")

def connect_pair_sc2py():
    return connect_pair("PYSOCKET_SC2PY_REQUEST_PORT", "PYSOCKET_SC2PY_RESPONSE_PORT")

# send a transaction from python to SystemC as a stream of bytes in a single call
def send_transaction(sock: socket.socket, transaction: PyTransaction) -> None:
    print(f"pySocket.py: sending {transaction.param1}, {transaction.param2}", flush=True)
    sock.sendall(transaction.to_bytes())

# wait for a response from SystemC to a transaction sent from python
async def wait_for_response(sock: socket.socket) -> int:
    loop = asyncio.get_running_loop()
    chunk = await loop.sock_recv(sock, 4)
    if len(chunk) != 4:
        raise ValueError("pySocket.py: expected 4 bytes, got %d", len(chunk))
    return struct.unpack('I', chunk)[0]

# loop to send transactions from python to SystemC and wait for responses
async def python2SystemC_transaction_loop(s_request: socket.socket, s_response: socket.socket) -> None:
    print("python2SystemC_transaction_loop: starting")
    # Handshake line for SystemC (read with pySocketIpc::fd_py_to_sc()).
    transactions = [PyTransaction(1, 2), PyTransaction(3, 4)]
    # msgs = [b"py_ready\n", b"2nd send from python\n"]
    unpacker = struct.Struct('I')
    for transaction in transactions:
        send_transaction(s_request, transaction)
        response = await wait_for_response(s_response)
        print(f"python2SystemC_transaction_loop: SC→Py: sum = {response}", flush=True)
    s_request.close()
    s_response.close()

# wait for a command sent from SystemC
async def wait_for_command(sock: socket.socket) -> bytes:
    loop = asyncio.get_running_loop()
    chunk = await loop.sock_recv(sock, 8)
    if len(chunk) != 8:
        raise ValueError("pySocket.py: expected 8 bytes, got %d", len(chunk))
    return chunk

# send response to a command received from SystemC
def send_response(sock: socket.socket, response: int) -> None:
    sock.sendall(struct.pack('I', response))

# loop to wait for commands from SystemC and send responses from python
async def systemC2Python_command_loop(s_request: socket.socket, s_response: socket.socket) -> None:
    print("systemC2Python_command_loop: starting")
    notEndOfTest = True
    while notEndOfTest:
        chunk = await wait_for_command(s_request)
        param1 = struct.unpack('I', chunk[:4])[0]
        param2 = struct.unpack('I', chunk[4:])[0]
        print(f"systemC2Python_command_loop: SC→Py: command = {param1:#08x} {param2:#08x}", flush=True)
        if (param1 == 0xcafef00d):
            response = 0xdeadbeef
        elif (param1 == 0x00000000):
            response = 0
            notEndOfTest = False
        else:
            response = param1
        print(f"systemC2Python_command_loop: SC→Py: response = {response:#08x}", flush=True)
        send_response(s_response, response)
    print("systemC2Python_command_loop: SC→Py: exit", flush=True)

async def main() -> None:
    s_py2sc_request, s_py2sc_response = connect_pair_py2sc()
    print("main: connected py2sc", flush=True)
    s_sc2py_request, s_sc2py_response = connect_pair_sc2py()
    print("main: connected sc2py", flush=True)
    task_python2SystemC = asyncio.create_task(python2SystemC_transaction_loop(s_py2sc_request, s_py2sc_response))
    task_systemC2Python = asyncio.create_task(systemC2Python_command_loop(s_sc2py_request, s_sc2py_response))
    await task_python2SystemC
    await task_systemC2Python
    print("main: done", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
