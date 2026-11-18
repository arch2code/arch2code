# UVM loopback

`a2c_uvm_loopback_tb.sv` connects each agent package to a copy of itself, with no DUT, and runs the tests the `*_lb_tests.svh` files beside it register. It is the self-test of the UVM library: agents, paired mode, the video library, the real-time checker, expected errors and the register layer. It runs on Xcelium and VCS only. `specs/SIMULATOR_INTEGRATION.md` section 9.9 lists the tests and what each checks.

## Running it

Source the simulator setup, then run from a scratch directory. The build and the logs go to `./loopback_<sim>`, which the script empties first.

```
$A2C_ROOT/common/systemVerilog/uvm/loopback/run_loopback.sh xcelium 7

# with Pro's agents and tests
$A2C_ROOT/common/systemVerilog/uvm/loopback/run_loopback.sh xcelium 7 \
    $A2C_ROOT/pro/common/systemVerilog/uvm/a2cPro_uvm.f

# the reduced loopback, on VCS
$A2C_ROOT/common/systemVerilog/uvm/loopback/run_loopback.sh --subset reduced vcs 7 \
    $A2C_ROOT/pro/common/systemVerilog/uvm/a2cPro_uvm.f
```

The seedRepro checks at the end of the script run with or without `--subset`.

## Before a commit

A change to the UVM library, an agent package, the loopback or a UVM template passes these before it is committed:

1. `make unittest` in base, with `UVM_HOME` set to an Accellera UVM 1.2 release so `test_uvm_sv_parse.py` parses the SV, and `make unit-test` in Pro;
2. the full loopback with Pro on Xcelium.

VCS licences are scarce, so no VCS run blocks a commit. The reduced loopback with Pro on VCS, one VCS licence and under 20 minutes, runs when a licence is free, before or after the commit, and a failure there is fixed in a later commit. The full loopback with Pro on VCS runs the same way. Use one seed for every loopback run of a change.

The two simulators treat some legal SV differently, and only a run on each shows it. A `?:` between two string literals is the one difference a unit test catches, `test_sv_string_select.py`: VCS prints the shorter literal padded with leading spaces, so use `a2c_select_str()`.

## The reduced loopback

`reduced.tests` lists the tests, one per line, with `#` starting a comment, and each layer's `loopback/` directory holds its own. Against a full run, the list covers:

- every agent package in each of its roles: single mode, paired-mode source or master, paired-mode destination or slave, passive, monitor protocol checks and a paired-mode mismatch;
- a test of every `*_lb_tests.svh` file;
- every library report call site that prints in the full loopback;
- every branch the full loopback takes of an `a2c_select_str()` or `a2c_lane_name()` call.

Add a test to the list when it adds an agent role, or when it is the only test that prints a library message. A name in the list that no test file registers fails the run, so a renamed test cannot drop out unnoticed.
