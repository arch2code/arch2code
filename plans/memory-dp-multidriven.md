# Verilator MULTIDRIVEN on memory_dp with two write ports on different clocks

## What happens

`memory_dp` and `memory_dp_ext` now have separate `clkA` and `clkB` inputs,
ported from uvc_rd PR 6. If both ports can write and the two clocks are on
different nets, Verilator reports that the shared `mem` array is written from
two always blocks on different clocks. `make lint` treats warnings as errors,
so the lint fails.

Reproduced with Verilator 5.038, linting `memory_dp` on its own:

```
%Warning-MULTIDRIVEN: common/systemVerilog/memory_dp.sv:21:13: Signal has multiple driving blocks with different clocking: 'top.uMem.mem'
    common/systemVerilog/memory_dp.sv:43:17: ... Location of first driving block
       43 |                 mem[addrA] <= write_dataA;
    common/systemVerilog/memory_dp.sv:71:17: ... Location of other driving block
       71 |                 mem[addrB] <= write_dataB;
%Error: Exiting due to 1 warning(s)
```

## When it happens

The warning depends only on the primitive's structure: whether port A has a
write path, and whether `clkA` and `clkB` are different nets.

| PORTA_READ_ONLY | PORTB_WRITE_ONLY | Same clock net | Different clock nets |
| :--- | :--- | :--- | :--- |
| 0 | 0 | clean | MULTIDRIVEN |
| 0 | 1 | clean | MULTIDRIVEN |
| 1 | 0 | clean | clean |
| 1 | 1 | clean | clean |

With `PORTA_READ_ONLY = 1`, the port A write block is never generated, so only
one block drives `mem`.

## Which arch2code memories are affected

- **Memory types.** `dualPort` and `portRWportW`, the two types whose port A
  can write. `portRportRW` and `portRportW` are never affected, so the uvc_rd
  `lsc` LUTs (`portRportW`) are fine.
- **Condition.** The memory has `regAccess`, and its `clock:` is not the owning
  block's register clock. The generator puts the register port on the register
  clock and the block port on the memory's clock, so the two clocks differ.
- **Without `regAccess`.** Both block ports run on the memory's clock, so the
  warning never appears.
- **Firmware access mode does not matter.** For example, take `portRWportW`
  with `regAccess: ro`. The register handler drives `wr_en` to 0 on port A,
  but the port A write block still exists in `memory_dp`, so Verilator still
  flags it.

## Why it did not appear before

The old design used a clock-crossing bridge (`memory_reg_bridge`) to move
firmware accesses onto the memory's clock, so both ports always ran on one
clock. You told us that bridge was unnecessary, so we removed it. As a result,
a `dualPort` memory with `regAccess` on a non-register clock linted clean
before this change and fails lint now. No example in the arch2code repo uses
that configuration.

## Simulation

The Verilator simulation test (`unittest/test_memory_dp_ports_sim.py`) covers
all four port types with independent clocks at three clock ratios, and it
passes. It suppresses the warning with `-Wno-MULTIDRIVEN`. The lint test
(`unittest/test_memory_dp_lint.py`) leaves out the two-writer, two-clock case
until this is decided.

## Decision needed

1. **Waive it in the primitive.** Add a scoped
   `/* verilator lint_off MULTIDRIVEN */ ... lint_on` around `mem` in
   `memory_dp.sv` and `memory_dp_ext.sv`. This accepts two write ports on
   independent clocks as a supported true dual-port RAM.
   - **Configurations.** Every one keeps working, including `dualPort` with
     `regAccess` on another clock.
   - **Tests.** We drop `-Wno-MULTIDRIVEN` from the simulation test and add
     the missing lint case.
   - **Your call.** You would be confirming that the target devices and
     synthesis flow support two write clocks on one RAM. You would also be
     deciding what a write to the same address from both ports in the same
     window should do, since the RTL does not arbitrate it.
2. **Reject it in the generator.** `projectCreate` reports an error for a
   memory whose two ports can both write on different clocks. The error tells
   the user to change `memoryType` to `portRportRW` or `portRportW`, or to put
   the memory on the register clock.
   - **Primitive.** `memory_dp` stays as uvc_rd wrote it, with no waiver.
   - **Cost.** `dualPort` or `portRWportW` with `regAccess` on a non-register
     clock becomes illegal, although it was accepted before this change.

## Recommendation

Option 1, if your flow infers true dual-port RAM with independent write
clocks. A memory where firmware and the block both write, each on its own
clock, is a legitimate design. Option 2 is the safer choice if your tools do
not support it. Either way, the change on the generator side is small.
