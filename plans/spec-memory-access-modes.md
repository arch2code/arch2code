# Memory port access modes and firmware access

Status: draft for team review

## Summary

Firmware access to a memory on a different clock no longer goes through a
clock-crossing bridge in the register handler. The memory itself carries two
clocks instead. The firmware port runs on the register clock and the block's
port runs on the memory's clock. The dual-clock RAM does the crossing.

Two YAML fields change to support this.

- `memoryType` gains three dual-port types that make a port read-only or
  write-only.
- `regAccess` accepts an access mode as well as `true` and `false`. The mode
  says what firmware may do with the memory.

The generator uses the two fields together to decide which memory port the
register handler attaches to, and which clock each port runs on.

The change ports the `memory_dp` rework from uvc_rd pull request 6
(https://git.latticesemi.com/Arch-Modeling/uvc_rd/pulls/6) into the arch2code
library and makes the generators produce it from YAML.

## Why

The synthesis tool maps a memory to one block RAM only when it has one write
port and one read port. The current `memory_dp` has two read/write ports, and
the tool answers that by building a second copy of the array in distributed
LUT RAM. On the lens shading grids the copy cost 2100 DPR16X4, about 12.6k
LUT4s. Making port A read-only and port B write-only brings the memory back to
one write and one read, which fits a single block RAM.

The same RTL change gives each port its own clock. Firmware writes arrive on
the CPU clock and the datapath reads on the pixel clock, with no handshake
logic between them.

## YAML changes

### `memoryType`

| Value | Port A | Port B | Notes |
| :--- | :--- | :--- | :--- |
| `singlePort` | read/write | none | Unchanged. |
| `dualPort` | read/write | read/write | Unchanged. The default. |
| `portRportRW` | read-only | read/write | New. |
| `portRWportW` | read/write | write-only | New. |
| `portRportW` | read-only | write-only | New. The only dual-port type that fits one block RAM. |

A read-only port has no write path in the RTL. Writes presented to it are
ignored. A write-only port has no read path, and its read data is always zero.

The new types apply to `local: true` memories as well.

### `regAccess`

| Value | Meaning |
| :--- | :--- |
| `false` | No firmware access. The default. |
| `true` | Same as `rw`. Existing YAML keeps its meaning. |
| `rw` | Firmware may read and write the memory. |
| `ro` | Firmware may only read the memory. |
| `wo` | Firmware may only write the memory. |

Any other value is an error.

### `clock`

`clock:` on a memory keeps its current meaning. It names the owning block's
clock that the memory runs on, and defaults to the block's default clock.
Under this change it sets the clock of the block-side port. The register port
always runs on the owning block's register clock.

### Removed

- The memory `reset:` field. Its only use was the reset for the bridge's
  memory side. A memory that still sets it fails with a diagnostic.
- The register handler bridge (`memory_reg_bridge`) and everything that
  generated it. Firmware access to a memory on another clock now goes through
  the memory's second clock port.

## Register port selection

A firmware access mode needs a port that can do it. `ro` needs a port that
can read, `wo` needs one that can write, and `rw` needs one that can do both.
The generator picks the register port in this order.

1. Keep only the ports that support the mode.
2. If more than one is left, prefer the port whose capability matches the
   mode exactly, for example a read-only port for `ro`.
3. If that still leaves two, use port B. This is today's behaviour, so
   existing designs do not move.
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

- A table that firmware loads and the datapath reads, such as the shading
  grids or the gamma LUT, is `portRportW` with `regAccess: wo`. Firmware writes
  port B on the register clock, and the datapath reads port A on its own
  clock.
- A capture or statistics buffer that the datapath fills and firmware reads is
  `portRportW` with `regAccess: ro`. Firmware reads port A on the register
  clock, and the datapath writes port B on its own clock. It also fits one
  block RAM.

## Clocks

- The register port runs on the owning block's register clock.
- The block-side port runs on the memory's `clock:`.
- With no `regAccess`, both ports run on the memory's `clock:`.
- A `singlePort` memory has one clock. With `regAccess` set, its `clock:` must
  be the register clock, or the generator reports an error. Before this change
  the bridge covered that case.

Crossing between the two ports is the RAM's own behaviour. Firmware should
load a table while the datapath is not reading it, or accept that a read that
collides with a write returns undefined data. That is true of the block RAM in
silicon whether or not the simulation model shows it.

## Firmware access in the wrong direction

The access mode is a contract with firmware. Breaking it does not cause a bus
error.

| Access | RTL | Model |
| :--- | :--- | :--- |
| Firmware write to an `ro` memory | The transfer completes with no `pslverr`, and the memory is unchanged. | The write is dropped, and the model logs a warning naming the memory and the address. |
| Firmware read of a `wo` memory | The transfer completes with no `pslverr` and returns zero. The handler does not read the memory. | Returns zero, and the model logs a warning naming the memory and the address. |

RTL simulation prints nothing for these accesses.

## Generated RTL

`memory_dp` and `memory_dp_ext` take the port and parameter names used in
uvc_rd, so the test benches and bind files written there keep working.

```systemverilog
module memory_dp #(
    parameter DEPTH  = 2,
    parameter type data_t = logic [1:0],
    parameter bit PORTA_READ_ONLY = 1'b0,   // 1: port A has no write path
    parameter bit PORTB_WRITE_ONLY = 1'b0)  // 1: port B has no read path, reads return zero
(
    memory_if.dst mem_portA,
    memory_if.dst mem_portB,
    input clkA,
    input clkB
);
```

The generator sets the two parameters from `memoryType` and connects `clkA`
and `clkB` as described in the clocks section. `memory_sp` does not change.

## Examples

A shading grid that firmware writes and the datapath reads. The block's
register port is on `cfg_clk`, and the block's default clock is `clk`.

```yaml
memories:
  - {memory: mem_r, block: lsc, structure: lsc_mem_data_t, addressStruct: lsc_mem_addr_t, wordLines: LSC_MEM_DEPTH,
     memoryType: portRportW, regAccess: wo, ports: [core], desc: "Red lens shading grid"}
```

This generates the instance that uvc_rd carries by hand today.

```systemverilog
memory_dp #(.DEPTH(LSC_MEM_DEPTH), .data_t(lsc_mem_data_t), .PORTA_READ_ONLY(1'b1), .PORTB_WRITE_ONLY(1'b1)) uMem_r (
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
memory_dp #(.DEPTH(AF_STAT_WORDS), .data_t(afStatSt), .PORTA_READ_ONLY(1'b1), .PORTB_WRITE_ONLY(1'b1)) uStats (
    .mem_portA (stats_reg),
    .mem_portB (stats_wr),
    .clkA (cfg_clk),
    .clkB (clk)
);
```

A line buffer with no firmware access. With two block ports, the first port
in `ports:` takes port A and the second takes port B, so the reader is listed
first.

```yaml
memories:
  - {memory: lineBuf, block: preprocess, structure: bayer_pixels_per_clock_t, addressStruct: line_address_st,
     wordLines: ENTRIES_PER_LINE, memoryType: portRportW, ports: [rd, wr], desc: "Line buffer"}
```

## Errors the generator reports

- `regAccess` is not one of `true`, `false`, `rw`, `ro`, `wo`.
- No port of the memory supports the `regAccess` mode, for example
  `portRportW` with `regAccess: rw`.
- A `singlePort` memory has `regAccess` and a `clock:` other than the register
  clock.
- A dual-port memory with `regAccess` lists two ports in `ports:`. The memory
  has two ports in total, and the register handler takes one of them, so only
  one is left for the block. Listing two asks for three users of a two-port
  memory. Today the generator gives the second listed port to the register
  handler without saying so, and the block's second connection is lost.
- A memory sets `reset:`.

## Compatibility

- YAML that uses only `true`/`false` and `singlePort`/`dualPort` means what it
  meant before. The register port stays on port B.
- Every `memory_dp` instance changes `.clk` to `.clkA` and `.clkB`. Generated
  instances update when regenerated. Hand-written instances outside the
  generated regions must be renamed by hand.
- A design that relied on the bridge for a `singlePort` memory on another
  clock must change the memory to a dual-port type. The `twoClk` example is
  that case and will change to `portRportRW`, with firmware on port B and the
  block's read-only port on `clkSlow`.
