# axiSocketSlave example: SystemC AXI master, Python memory slave over TCP sockets.

Run from `rundir/`:

```bash
make run
```

The testbench forks `axiSocketSlave.py`, which serves AXI read and write bursts on
`axiSocket.axiRd0` and `axiSocket.axiWr0`. Catalog observe sockets (`*_obs`) and
`pysocket_sync` are also registered/connected so bring-up matches `registerAll` /
`handshakeAll`; this demo does not score observe traffic.

The `producer` block issues short bursts and checks read data against the same
pattern as `axiDemo` (`i * 0x01010101`).

Set `PYSOCKET_SKIP_PYTHON_SIDECAR=1` to run SystemC only (will hang without a sidecar).
