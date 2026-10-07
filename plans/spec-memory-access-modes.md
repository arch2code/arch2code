# Memory port access modes and clocks

Status: draft for review

## Summary

A memory's ports, the access firmware has to it, and the clocks its ports run
on are set by three YAML fields.

- `memoryType` makes a dual-port memory's ports read/write, read-only or
  write-only.
- `regAccess` says what firmware may do with the memory.
- `clock` names the clock of the block-side port. The register port runs on the
  owning block's register clock.

When the register clock and the memory's clock differ, the memory has two
clocks and the RAM is the crossing. The register handler generates no
handshake or synchroniser for it. `spec-clock-reset-requirements.md` (R19, R20,
V24) states the domain rules this document implements.

## Why port access matters

Synthesis maps a memory to one block RAM only when it has one write port and
one read port. A second read path makes the tool copy the array into
distributed LUT RAM. On the lens shading grids that copy cost about 12.6k
LUT4s. A memory whose ports do only what the design needs fits one block RAM.

A second write path is worse. Two writers in two `always` blocks give the array
two drivers, which does not synthesize to flops, and on two clocks does not map
to FPGA block RAM.

## YAML

### `memoryType`

| Value | Port A | Port B |
| :--- | :--- | :--- |
| `singlePort` | read/write | none |
| `dualPort` | read/write | read/write |
| `portRportRW` | read-only | read/write |
| `portRWportW` | read/write | write-only |
| `portRportW` | read-only | write-only |

`dualPort` is the default. A read-only port has no write path in the RTL, and
writes presented to it are ignored. A write-only port has no read path, and its
read data is always zero. Every type applies to `local: true` memories as well.

### `regAccess`

| Value | Meaning |
| :--- | :--- |
| `false` | No firmware access. The default. |
| `true` | Same as `rw`. |
| `rw` | Firmware may read and write the memory. |
| `ro` | Firmware may only read the memory. |
| `wo` | Firmware may only write the memory. |

### `clock`

`clock:` names the owning block's clock that the memory runs on, and defaults
to the block's default clock. It sets the clock of every block-side port. A
memory has no reset, because the array is never reset.

## Register port selection

A firmware access mode needs a port that can do it. `ro` needs a port that
can read, `wo` needs one that can write, and `rw` needs one that can do both.
The generator picks the register port in this order.

1. Keep only the ports that support the mode.
2. If more than one is left, prefer the port whose capability matches the
   mode exactly, for example a read-only port for `ro`.
3. If that still leaves two, use port B.
4. If no port supports the mode, report an error.

The block-side port is whichever port the register handler does not take.

| `memoryType` | `rw` / `true` | `ro` | `wo` |
| :--- | :--- | :--- | :--- |
| `dualPort` | B | B | B |
| `portRportRW` | B | A | B |
| `portRWportW` | A | A | B |
| `portRportW` | error | A | B |
| `singlePort` | the port | the port | the port |

Two cases do most of the work.

- A table that firmware loads and the datapath reads, such as a shading grid or
  a gamma LUT, is `portRportW` with `regAccess: wo`. Firmware writes port B on
  the register clock, and the datapath reads port A on its own clock.
- A capture or statistics buffer that the datapath fills and firmware reads is
  `portRportW` with `regAccess: ro`. Firmware reads port A on the register
  clock, and the datapath writes port B on its own clock.

## Port configurations

What a memory allows depends on how many sides write it. Rows are firmware
access. Columns are the access of the block-side port.

| Firmware \ block | rw | ro | wo |
| :--- | :--- | :--- | :--- |
| rw | One clock on FPGA. Two clocks for simulation only, or as an ASIC memory macro. | One or two clocks. | Same as rw/rw. |
| ro | One or two clocks. | Not valid. Nothing writes. | One or two clocks. |
| wo | Same as rw/rw. | One or two clocks. | Not valid. Nothing reads. |

A memory with one writer works on one clock or two. A memory where firmware and
the block both write works on one clock. Whether that single-clock memory maps
to block RAM depends on the device family. Memory macro support for ASIC flows
is outside this specification.

Each valid cell maps to a `memoryType` and a register port through the
selection rules above.

| Firmware | Block | `memoryType` | Register port | Writers | Mode |
| :--- | :--- | :--- | :--- | :--- | :--- |
| rw | rw | `dualPort` | B | 2 | 2RW |
| rw | ro | `portRportRW` | B | 1 | 1RW1R |
| rw | wo | `portRWportW` | A | 2 | RW+WO |
| ro | rw | `portRportRW` | A | 1 | 1RW1R |
| ro | wo | `portRportW` | A | 1 | 1W1R |
| wo | rw | `portRWportW` | B | 2 | RW+WO |
| wo | ro | `portRportW` | B | 1 | 1W1R |

A memory with no `regAccess` has both ports on its own `clock:`. It always has
one clock, and every mode is allowed.

## Clocks

- The register port runs on the owning block's register clock.
- The block-side port runs on the memory's `clock:`.
- With no `regAccess`, both ports run on the memory's `clock:`.
- A `singlePort` memory and a `local: true` memory have one clock. With
  `regAccess` set, the memory's `clock:` must be the register clock.

Clocks compare by block clock name. Two block clocks count as different even
if one instance binds both to the same net, because the block's RTL has to work
under any binding.

The crossing between the two ports is the RAM's own behaviour. When one port
reads an address that the other port writes in the same cycle, the RTL returns
the old data, and block RAM in silicon leaves the read undefined. The SystemC
memory model gives no ordering guarantee for a same-time read and write on two
ports. Firmware loads a table while the datapath is not reading it.

## Register handler

The register handler builds only the paths its `regAccess` mode needs and ties
off the rest.

- For `ro`, the handler drives `wr_en` to `1'b0` and `write_data` to `'0`.
- For `wo`, the handler asserts `enable` only on writes and never consumes
  `read_data`.

The memory keeps the full path that its `memoryType` gives the register port.
A tied-off write path leaves synthesis to remove it by constant propagation. A
design that must guarantee one write port uses the narrowest `memoryType` for
its access, for example `portRportW` rather than `dualPort` for `regAccess: wo`
with a read-only datapath.

The access mode is a contract with firmware. Breaking it does not cause a bus
error.

| Access | RTL | Model |
| :--- | :--- | :--- |
| Firmware write to an `ro` memory | The transfer completes with no `pslverr`, and the memory is unchanged. | The write is dropped, and the model logs a warning naming the memory and the address. |
| Firmware read of a `wo` memory | The transfer completes with no `pslverr` and returns zero. The handler does not read the memory. | Returns zero, and the model logs a warning naming the memory and the address. |

RTL simulation prints nothing for these accesses.

## Generated RTL

The generator picks the module from the clocks of the two ports.

- Both ports on one clock: `memory_dp`, connecting `.clk`.
- Ports on two clocks: `memory_dp_2clk`, connecting `.clkA` and `.clkB`.
- A `local: true` dual-port memory: `memory_dp_ext`, which has one clock.
- A single-port memory: `memory_sp` or `memory_sp_ext`.

The module, port and parameter names match the uvc_rd memory library, so test
benches and bind files written against it work unchanged.

```systemverilog
module memory_dp #(
    parameter DEPTH  = 2,
    parameter type data_t = logic [1:0],
    parameter bit PORTA_READ_ONLY = 1'b0,   // 1: port A has no write path
    parameter bit PORTB_WRITE_ONLY = 1'b0)  // 1: port B has no read path, reads return zero
(
    memory_if.dst mem_portA,
    memory_if.dst mem_portB,
    input clk
);
```

`memory_dp_2clk` has the same parameters and interfaces, with `input clkA` and
`input clkB` in place of `clk`. `memory_dp_ext` adds the array as an output, as
the single-port `_ext` module does, and has one clock.

The generator sets the two parameters from `memoryType`.

| Mode | `PORTA_READ_ONLY` | `PORTB_WRITE_ONLY` | `memoryType` |
| :--- | :--- | :--- | :--- |
| 1W1R | 1 | 1 | `portRportW` |
| 1RW1R | 1 | 0 | `portRportRW` |
| 2RW | 0 | 0 | `dualPort` |
| RW+WO | 0 | 1 | `portRWportW` |

The modules meet these requirements.

- Reads have one cycle of latency through a flop. A read on the cycle of a
  same-address write on the other port returns the old data.
- A read-only port has no write statement at all, rather than a write guarded
  by a constant.
- The single-clock modules do all reads and writes of a mode in one `always`
  block, so every bit of the array has one driver. In 2RW and RW+WO, port B
  wins when both ports write the same address in the same cycle.
- `memory_dp_2clk` gives each port its own `always` block on its own clock. In
  2RW and RW+WO it reports `$info` at elaboration, saying the mode is for
  simulation or an ASIC memory macro. The report must not fail a Verilator
  build, because simulation is a supported use of the mode.
- No module carries a RAM style attribute. The synthesis flow chooses the RAM
  style.

## Examples

A shading grid that firmware writes and the datapath reads. The block's
register port is on `cfg_clk`, and the block's default clock is `clk`.

```yaml
memories:
  - {memory: mem_r, block: lsc, structure: lsc_mem_data_t, addressStruct: lsc_mem_addr_t, wordLines: LSC_MEM_DEPTH,
     memoryType: portRportW, regAccess: wo, ports: [core], desc: "Red lens shading grid"}
```

```systemverilog
memory_dp_2clk #(.DEPTH(LSC_MEM_DEPTH), .data_t(lsc_mem_data_t), .PORTA_READ_ONLY(1'b1), .PORTB_WRITE_ONLY(1'b1)) uMem_r (
    .mem_portA (mem_r_core),
    .mem_portB (mem_r_reg),
    .clkA (clk),
    .clkB (cfg_clk)
);
```

A statistics buffer that the datapath fills and firmware reads. Here the
register handler takes port A. The block and structure names are made up for
the example.

```yaml
memories:
  - {memory: stats, block: af, structure: afStatSt, addressStruct: afStatAddrSt, wordLines: AF_STAT_WORDS,
     memoryType: portRportW, regAccess: ro, ports: [wr], desc: "Focus statistics, read by firmware"}
```

```systemverilog
memory_dp_2clk #(.DEPTH(AF_STAT_WORDS), .data_t(afStatSt), .PORTA_READ_ONLY(1'b1), .PORTB_WRITE_ONLY(1'b1)) uStats (
    .mem_portA (stats_reg),
    .mem_portB (stats_wr),
    .clkA (cfg_clk),
    .clkB (clk)
);
```

A line buffer with no firmware access. With two block ports, the first port
in `ports:` takes port A and the second takes port B, so the reader is listed
first. Both ports are on `clk`.

```yaml
memories:
  - {memory: lineBuf, block: preprocess, structure: bayer_pixels_per_clock_t, addressStruct: line_address_st,
     wordLines: ENTRIES_PER_LINE, memoryType: portRportW, ports: [rd, wr], desc: "Line buffer"}
```

```systemverilog
memory_dp #(.DEPTH(ENTRIES_PER_LINE), .data_t(bayer_pixels_per_clock_t), .PORTA_READ_ONLY(1'b1), .PORTB_WRITE_ONLY(1'b1)) uLineBuf (
    .mem_portA (lineBuf_rd),
    .mem_portB (lineBuf_wr),
    .clk (clk)
);
```

## Errors the generator reports

- `regAccess` is not one of `true`, `false`, `rw`, `ro`, `wo`.
- No port of the memory supports the `regAccess` mode, for example
  `portRportW` with `regAccess: rw`.
- A `singlePort` or `local: true` memory has `regAccess` and a `clock:` other
  than the register clock. The diagnostic names both clocks.
- A dual-port memory with `regAccess` lists two ports in `ports:`. The memory
  has two ports in total and the register handler takes one, so only one is
  left for the block.

A local memory on two clocks reports like this.

```text
In lsc.yaml:12, memory 'mem_r' of block 'lsc' is local, and its ports run on
two clocks: port A on 'clk' and port B, the register port, on 'cfg_clk'. A
local memory has one clock. Set the memory's clock: to 'cfg_clk', or remove
local.
```
