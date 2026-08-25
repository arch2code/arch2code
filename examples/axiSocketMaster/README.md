# axiSocketMaster example: Python AXI master, SystemC memory slave over TCP sockets.

Run from `rundir/`:

```bash
make run
```

The testbench forks `axiSocketMaster.py`, which issues AXI read and write bursts on
`axiSocket.axiRd0` and `axiSocket.axiWr0`. Catalog observe sockets (`*_obs`) and
`pysocket_sync` are registered/connected for bring-up consistency; this demo does
not score observe traffic.

The `consumer` block returns the same read pattern as `axiDemo` / `axiSocketSlave`
(`i * 0x01010101`) and checks write data.

Set `PYSOCKET_SKIP_PYTHON_SIDECAR=1` to run SystemC only (will hang without a sidecar).
