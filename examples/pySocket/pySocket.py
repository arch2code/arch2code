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

class PyTransaction:
    def __init__(self, param1, param2):
        self.param1 = param1
        self.param2 = param2
        self.packer = struct.Struct('I I') # 4 bytes for int, 4 bytes for int

    def to_bytes(self):
        return self.packer.pack(self.param1, self.param2)

def connect_pair():
    try:
        p_sc2py = int(os.environ["PYSOCKET_SC2PY_PORT"])
        p_py2sc = int(os.environ["PYSOCKET_PY2SC_PORT"])
    except (KeyError, ValueError) as exc:
        print("pySocket.py: missing or invalid PYSOCKET_*_PORT", exc, file=sys.stderr)
        sys.exit(1)

    s_sc2py = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_py2sc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_sc2py.connect(("127.0.0.1", p_sc2py))
    s_py2sc.connect(("127.0.0.1", p_py2sc))
    return s_sc2py, s_py2sc


def main() -> None:
    print("pySocket.py: starting")
    s_sc2py, s_py2sc = connect_pair()
    print("pySocket.py: connected (sc→py and py→sc)", flush=True)
    # Handshake line for SystemC (read with pySocketIpc::fd_py_to_sc()).
    transactions = [PyTransaction(1, 2), PyTransaction(3, 4)]
    # msgs = [b"py_ready\n", b"2nd send from python\n"]
    unpacker = struct.Struct('I')
    for transaction in transactions:
        print(f"pySocket.py: sending {transaction.param1}, {transaction.param2}", flush=True)
        s_py2sc.sendall(transaction.to_bytes())

        try:
            chunk = s_sc2py.recv(4096)
            sum = unpacker.unpack(chunk)[0]
            print(f"pySocket.py: SC→Py: sum = {sum}", flush=True)
        except:
            print("pySocket.py: error receiving from SC", file=sys.stderr)
            break
    s_sc2py.close()
    s_py2sc.close()


if __name__ == "__main__":
    main()
