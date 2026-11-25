---
name: verify-uvm
description: Guide for writing and running tests on a generated arch2code UVM testbench (hasUvm): where user code goes, sequences, directed and register tests, scoreboards, negative tests with a2c_expected_error, running on Xcelium or VCS, and debugging a failing run
---
# Skill: Verify with the UVM testbench

A block with `hasUvm: true` gets a generated UVM testbench that runs its SystemC model, its RTL, or both side by side (paired mode). `specs/SIMULATOR_INTEGRATION.md` section 9 is the reference. Its "Terms" table defines single mode, paired mode, lane, pair, unit and the other words this skill uses, and its "A first test" walks `examples/uvmMem` from generation to a new test. Read both before writing a first bench.

## Where code goes
1.  The block needs `hasVl: true` as well as `hasUvm: true`. Run `make newmodule`, then `make gen`; see `manage-build`. `make db` names any rule the block breaks (spec section 9.1).
2.  Never edit between `GENERATED_CODE_BEGIN` and `GENERATED_CODE_END`. `make gen` rewrites those sections and keeps everything else.
3.  The project's code goes in `uvm/<block>_uvm_test_pkg.sv`:
    *   user span 1, after the `header` section: `<block>_tb_env extends <block>_env`, scoreboards, sequences and helpers;
    *   user span 2, after the generated `<block>_base_test`: `<block>_smoke_test` and every other test.
4.  Do not rename `<block>_smoke_test`. The generated `<block>_fail_test`, `<block>_rt_fire_test` and `<block>_model_mismatch_test` in the `footer` section extend it.
5.  Code a parent block's bench must also compile, such as a check, a scoreboard or a configuration sequence, goes in the user span of the variant package `uvm/<stem>_uvm_pkg.sv` (`// user package items here`) instead. It must not name anything of the test package. See spec section 9.15.
6.  The scaffolded smoke test sends nothing, so it warns `A2C_NO_STIMULUS` until its `run_body()` sends stimulus.

## Write a sequence
*   The variant package gives each port the typedefs `<port>_item_t`, `<port>_agent_t`, `<port>_config_t` and `<port>_vif_t`. Use them; never spell an agent's parameters by hand.
*   Draw item fields with `randomize() with {...}`, not `$urandom()`, so a derived test can constrain them. Every item except `apb`, `raw` and `status` has a `rand` `gap`, the idle clocks before the transfer.

```systemverilog
class cmd_burst_seq extends uvm_sequence #(cmd_item_t);
    int unsigned n = 16;
    `uvm_object_utils(cmd_burst_seq)

    function new(string name = "cmd_burst_seq");
        super.new(name);
    endfunction

    virtual task body();
        repeat (n) begin
            cmd_item_t it = cmd_item_t::type_id::create("it");
            start_item(it);
            if (!it.randomize() with { gap inside {[0:3]}; }) `uvm_error("SEQ", "randomize failed")
            finish_item(it);
        end
    endtask
endclass
```

*   `memory`, `axi_read` and `axi_write` return their responses after `item_done()`. A sequence on them extends `memory_base_seq`, `axi_read_base_seq` or `axi_write_base_seq` and waits in `wait_for_reads()` or `wait_for_writes()` before it ends (spec section 9.10, "Read data back to the sequence").

## Write a directed test
1.  Extend `<block>_base_test`, or `<block>_smoke_test` to reuse its configuration.
2.  Put the stimulus in `run_body()`. Start sequences on `env.<port>_agent.sqr`.
3.  Declare every output's transactions with `env.<port>_counter.expect_count(n)`. After `run_body()` returns, the base test waits for every declared count and then a quiet window. A short or extra count is an `A2C_TXN_COUNT` error.
4.  Never raise or drop objections. The base test owns its one objection, the reset wait, the end-of-test wait and the run timeout.
5.  Set knobs in the constructor. Their plusargs override them at run time. The knobs and plusargs are listed in spec section 9.6.

```systemverilog
class blk_burst_test extends blk_base_test;
    `uvm_component_utils(blk_burst_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
        quiet_cycles = 2000;
    endfunction

    virtual task run_body();
        cmd_burst_seq seq = cmd_burst_seq::type_id::create("seq");
        seq.n = 64;
        env.out_counter.expect_count(64);
        seq.start(env.cmd_agent.sqr);
    endtask
endclass
```

*   An output whose count depends on the data: in paired mode set `expect_from_model` and the model lane's count becomes the expectation. In single mode the test computes the count from its stimulus.
*   A long test, such as one sending whole frames, fixes its budget with `run_timeout.fix(<clocks>)` in `run_body()` before it sends (spec section 9.6, "The run timeout").
*   Timing knobs are `rand` on each agent config. Constrain them with `randomize() with {...}` in `connect_phase`. For a directed stall pattern, override the driver's `a2c_ready_policy` with `a2c_pattern_ready_policy` (spec section 9.10, "Constrained-random knobs and the ready policy").
*   A reset during the test: call `reset_dut()`. It works only with `--uvmDut rtl`; a run that holds the model refuses it with `A2C_RESET`.

## Registers
*   The env holds `regmodel`, built from the block's address rows, so its offsets match `fw/<block>RegAddresses.h`. Reach a register as `env.regmodel.<reg>`. A top that hosts a router or passes its register bus through gets a hierarchical model: `env.regmodel.<instance>.<reg>`, such as `env.regmodel.uBridge.uDeep.cfg` in `examples/uvmRegs`.
*   `env.write_reg(rg, value)` writes a register through the front door, reads it back, and raises `A2C_REG` on a bad status or a read-back that differs. Use it for registers whose fields are all read-write. Call `rg.write()`, `rg.read()` or `rg.mirror()` for the others.
*   A register access test is one class. `a2c_reg_test` runs `uvm_reg_hw_reset_seq`, an aliasing pass and `uvm_reg_bit_bash_seq` on `env.regmodel`, and sets `no_stimulus_expected`:

```systemverilog
class blk_reg_test extends a2c_reg_test #(blk_base_test);
    `uvm_component_utils(blk_reg_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction
endclass
```

    Override `run_body()` around `super.run_body()` to add checks. `examples/uvmRegs` (`uvmRegs_reg_test`) adds a reset check of one child block.
*   In paired mode, program registers only while the datapath is quiescent: configure, stream, call `wait_for_outputs()`, then configure again. A write, or a read of a volatile register, while outputs are pending is an `A2C_MIDSTREAM` error. List registers that can never compare, such as a free-running counter, with `skip_reg()` on the bus agent's `model_cmp`, under `if (dual_dut)` (spec section 9.12).

## Add a scoreboard
1.  Write the scoreboard in user span 1 and create it in `<block>_tb_env`'s `build_phase`, after `super.build_phase(phase)`.
2.  In `connect_phase`, connect `<port>_agent.mon.ap` of each input and output it needs. Declare several imports with `` `uvm_analysis_imp_decl ``. `uvmMem_scoreboard` in `examples/uvmMem/uvm/uvmMem_uvm_test_pkg.sv` is the reference.
3.  Predict from the stimulus and the register mirror, never from the model. Paired mode already compares the RTL with the model; it misses an error both make.
4.  Run the check in every mode. In paired mode, also connect `<port>_agent.model_mon.ap` to a second instance, so a model error fails on the model lane as well.
5.  Nothing warns about an output with no such check. Decide per output, and say in the bench why an output has none.
6.  To share one memory between two `memory` ports, create one `a2c_mem_model` in `build_phase` and set `cfg.mem` on both ports' configs (spec section 9.10, "`a2c_mem_model`").

## Real-time checks
A stream whose timing is a contract gets an `a2c_rt_checker` in `<block>_tb_env`; base wires none. Follow the four wiring steps in spec section 9.6, "Wiring a checker into a project": a unit rule, the checker and its `connect_in()` and `connect_out()`, bounds measured from a passing run's `A2C_RT` summary, and the generated `<block>_rt_fire_test` to prove the wiring.

## Negative tests
*   A test that provokes an error on purpose expects it with `a2c_expected_error`. Set `id`, `text` and `count` in `build_phase`. It demotes exactly `count` matching `UVM_ERROR`s to info, and at `check_phase` any other number raises `A2C_EXPECTED_ERROR`, so a missing error fails the test as an extra one does.

```systemverilog
bfm_break       = a2c_expected_error::type_id::create("bfm_break", this);   // build_phase
bfm_break.id    = "A2C_BFM_CONTRACT";
bfm_break.text  = "SystemC stalled a backpressure: false producer";
if (!uvm_config_db#(bit)::get(env, "", "a2c_model_dut", model_dut))        // connect_phase
    `uvm_error("A2C_CFG", "no a2c_model_dut config key")
bfm_break.count = (model_dut || env.dual_dut) ? 1 : 0;
```

*   Set `count` per DUT: an error that only the model's BFMs raise is 0 on the RTL.
*   Two `a2c_expected_error`s whose matches overlap depend on catcher order; give the narrower one the earlier name (spec section 9.8).
*   Do not write new tests on `a2c_error_demoter`. It demotes every match and checks no count.

## Run
From the project's `rundir`, with the simulator setup sourced. On VCS use `USE_VCS=1` and `build/run`:

```text
make -j8 USE_UVM=1 USE_XCELIUM=1 UVM_DUT=rtl all
../builder/dutRun.py build_xrun/run <block>_uvm --seed 7 --verbosity=low --uvmTop <stem> --uvmDut rtl +UVM_TESTNAME=<test>
```

*   `UVM_DUT` and `--uvmDut` take `model`, `rtl` or `both`; the run's must match the snapshot's. `make -j8 USE_UVM=1 USE_XCELIUM=1 uvm_snapshots` builds every DUT of the default top.
*   A passing run exits 0 and ends with `UVM finished with 0 UVM_ERROR/UVM_FATAL`.
*   A regression file lists each test once per DUT group, with `--uvmDut` per group and `+UVM_TESTNAME` per entry. Copy `examples/uvmMem/rundir/regr_uvmMem_uvm_xcelium.json`, and see `run-regression-tests` for seeds, labels and the rule files.
*   Every port's monitor feeds an `a2c_txn_digest`, which prints `A2C_DIGEST <port> <DUT|model> paired=<0|1> items=<n> digest=<hex>` at `report_phase`. A run repeated with the same seed on the same simulator must print the same lines. A project item whose `convert2string()` leaves payload out must implement `a2c_digest_fields`, or the digest misses that payload.
*   Check reproducibility with a `seed_repro` group, which runs each entry twice under `seedRepro.py` and compares the digests. Put a random test of each DUT in it (spec section 9.7).

## Debug
1.  Find the first `UVM_ERROR` or `UVM_FATAL` in the log and look its ID up in spec section 9.17, the message catalogue. Later reports are often its consequences.
2.  Copy the `A2C_RERUN` line printed beside it. It repeats the run with the same seed on the same snapshot.
3.  Add `+UVM_VERBOSITY=UVM_HIGH`, or `+uvm_set_verbosity=<component path>,<id>,<level>,run` for one port. `--verbosity` controls the SystemC side separately.
4.  For waves, rebuild with `WAVES=1` and run the `A2C_RERUN` command. `WAVES_SCOPE=<scope>` narrows the dump.
5.  An `A2C_MODEL_CMP` report gives the pair index and each lane's sample time. Spec section 9.14, "From a pair to the waveform", walks from there to the signals.
6.  Spec section 9.14, "When a check fires", covers the real-time checker, `A2C_MODEL_THROTTLE` and the `HDL lowered ready` and `HDL changed read data` breaks.

## Constraints
*   Never hand-edit generated sections to make a test pass. Fix the test, the YAML, the model or the RTL, then regenerate.
*   A trailing model lane, `A2C_MODEL_THROTTLE` and a memory access held for its credit are model defects. Fix the model's queuing; do not raise the bound that reported it.
*   Do not loosen a real-time bound, a deadline or a timeout in a regression entry to make a run pass. Change a bound in the test's constructor, with a comment saying what it guarantees.
*   Do not add a fallback or a demoter that hides a failure. Expect errors only in a negative test, with an exact count.
*   What the flow does not verify is listed in spec section 10.1. Say in the bench how any of it that matters is covered.
