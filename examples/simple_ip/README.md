# `simple_ip`: reusing one parameterized IP

The smallest composed example. A project whose own design sits at its root
instantiates a reusable IP owned by a second project, reaches the IP's registers
through a generated router, and checks it from firmware. `ip_test` covers the
same ground with several variants, a bridge and nested projects; start here.

## Sub-projects

| Directory | `projectName` | Owns |
| :-- | :-- | :-- |
| `.` | `simple_ip` | the DUT `simple_ip`, `simple_ip_tb`, `dataGen`, `apbDecode` |
| `common/` | `common` | `shared_types.yaml`, which declares the `apbReg` register bus, and the `cpu` APB master |
| `ip/` | `ip` | the parameterized `ip` block, its `variant0`, and its own testbench harness `ipStdTop` |

`prj/yaml/project.yaml` lists the two child project files and the top design
in `projectFiles:`. `yaml/simple_ip.yaml` `include:`s the child files whose
names it uses. Each child also builds and runs on its own from its `rundir/`.

## Topology

```text
simple_ip_tb
├── uCPU          cpu, runs fw/src through the BSP
└── u_simple_ip   simple_ip (DUT)
    ├── uAPBDecode  apbDecode, the addressBlock: router
    ├── uDataGen    dataGen, fixed-width producer
    └── uIp         ip, variant0, addressGroup: top
```

`uDataGen.out` uses the fixed-width `simpleDataIf`, and `uIp.ipDataIf` is
parameterized, so the connection is adapted by a `push_ack` thunker. The
firmware in `fw/src/fwSimpleMain.cpp` reads the word `uIp` captured and writes
and reads back its `ipCfg` register.

## Layout

The project is hierarchical and flat at the root: `yaml/simple_ip.yaml` is the
root node, so its files generate into `model/`, `rtl/`, `base/`, `tb/`,
`verif/`, `fw/` and `registrar/` beside it. The project file is in `prj/yaml/`.
`ip/` and `common/` are child projects with the same shape, each under its own
root. The parent never writes into them. Its `registrar/` holds its own copies
of the registrars for the children it assembles, `ipRegistrar.cppm` and
`ipVlRegistrar.cpp`.

## The testbench

`tb/simple_ip/` is the DUT's testbench. The External is retargeted at the test
container:

```cpp
// GENERATED_CODE_PARAM --block=simple_ip_tb --excludeInst=u_simple_ip --mode=module
```

so the External instantiates `uCPU`, and the Testbench instantiates
`u_simple_ip` and binds the two. `fw/src/fwModelMain.cpp` holds the end-of-test
voter.

## Build and run

```bash
make -C examples/simple_ip gen            # generates common and ip first
make -C examples/simple_ip/rundir -j run
make -C examples/simple_ip/rundir run-vl  # clean, rebuild with VL_DUT=1, run
```

`run-vl` replaces only the reused leaf with its RTL:
`--vlInst tb.simple_ip.uIp`. The testbench roots its hierarchy at `tb`, so the
DUT is `tb.simple_ip`. From the builder root, `make simple-ip` runs all three.
