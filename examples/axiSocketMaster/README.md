# axiSocketMaster example: Python AXI master, SystemC memory slave over TCP sockets.

Run from `rundir/`:

```bash
make run
```

The testbench has two socket shells, `u_axiSocket0` and `u_axiSocket1`, each
wired to its own `consumer` memory (`u_consumer0`, `u_consumer1`). Socket names
are the shell's instance path plus the port, so the sidecar connects to
`axiSocketMaster_tb.u_axiSocket0.axiRd0`, `axiSocketMaster_tb.u_axiSocket0.axiWr0`,
and the same two ports under `u_axiSocket1`. Each port also has an observe socket
(`<name>_obs`), and the testbench registers `pysocket_sync` once. The demo
connects the observe sockets but does not score their traffic.

`axiSocketMaster.py` writes a different pattern through each shell, then reads it
back through the same shell. The top nibble of every data word names the shell, so
a crossed or shared connection fails the read-back check. The `consumer` stores
each write and returns the stored word on a read (0 for an address never written).
It answers SLVERR on a bad write id, strobe or `wlast`.

The instance paths appear twice, as `SHELL_INSTANCE0`/`SHELL_INSTANCE1` in
`tb/axiSocket/axiSocketConfig.cpp` and as `SHELL_INSTANCES` in
`axiSocketMaster.py`. Change both together.

Set `PYSOCKET_SKIP_PYTHON_SIDECAR=1` to run SystemC only (will hang without a sidecar).
