# axiSocketSlave example: SystemC AXI master, Python memory slave over TCP sockets.

Run from `rundir/`:

```bash
make run
```

The testbench forks `axiSocketSlave.py`, which serves AXI read and write bursts on
`axiSocketSlave_tb.u_axiSocket.axiRd0` and `axiSocketSlave_tb.u_axiSocket.axiWr0`.
Each socket name is the shell's instance path plus the port. The testbench
registers the shell's names with `axiSocketSocketCatalog::registerInstance`, adds
`pysocket_sync` once when the catalog's `uses_lockstep` is set, and completes
bring-up with `socketFactory::handshakeAll`. The observe sockets (`<name>_obs`) are
connected, but this demo does not score their traffic. The instance path appears as
`SHELL_INSTANCE` in both `tb/axiSocket/axiSocketConfig.cpp` and `axiSocketSlave.py`.

The `producer` block issues short bursts and checks read data against the same
pattern as `axiDemo` (`i * 0x01010101`).

Set `PYSOCKET_SKIP_PYTHON_SIDECAR=1` to run SystemC only (will hang without a sidecar).
