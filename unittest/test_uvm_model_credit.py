#!/usr/bin/env python3
"""Each memory port the DUT drives gets a model credit rendezvous in Mode B.

memory has no handshake, so in Mode B the A2C_DST agent of a DUT `src` memory
port tells the model's BFM how many accesses the DUT lane has made, and the
BFM holds the model's access n until that count exceeds n
(SIMULATOR_INTEGRATION.md section 9.12). The interface definition opts in with
`uvmModelCredit: true`. For each such port, `<port>_model_credit`, 32 bits out
of the testbench module, and `<port>_model_held`, one bit in, sit after the
clocks and resets and before the completion pins, in the testbench module,
its VCS port map and its Xcelium shell, and in no HDL wrapper top. The
testbench module ties each credit pin to zero outside A2C_UVM_BOTH_DUT. Under
it, an a2c_credit_if per port carries both pins and is published as
`<port>_credit`, which the variant package's env fetches into the agent's
cfg.credit_vif and stops on when it is missing. The SystemC wrapper binds the
pins to signals and hands them to the port's memory_dst_bfm only when the run
holds the RTL as well as the model. The BFMs of the two or more memory ports
the DUT drives (bfmWriteOrder) get one memory_write_order, only when the run
holds the model alone.

The case is a copy of examples/uvmMem, whose DUT drives two memory ports, wr
and rd, given a third memory port, lut, that the DUT serves as a `dst`, and
two rdy_vld ports. Only wr and rd may carry credit. The same copy with
hasMdl: false on the DUT has no model lane, so no port carries credit.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir
from _tmp_helpers import remove_tree

EXAMPLE = os.path.join(base_dir, 'examples', 'uvmMem')
CREDITED = ['wr', 'rd']
UNCREDITED = ['cmd', 'out', 'lut']

EDITS = [
    ('            rd:  { interface: uvmMemPortIf, direction: src }\n',
     '            rd:  { interface: uvmMemPortIf, direction: src }\n'
     '            lut: { interface: uvmMemPortIf, direction: dst }\n'),
    ('            cmd: { interface: uvmMemCmdIf, direction: src }\n',
     '            cmd: { interface: uvmMemCmdIf, direction: src }\n'
     '            lut: { interface: uvmMemPortIf, direction: src }\n'),
    ('    - { interface: uvmMemPortIf, src: u_uvmMem, srcport: rd,  dst: uStore,   dstport: rd }\n',
     '    - { interface: uvmMemPortIf, src: u_uvmMem, srcport: rd,  dst: uStore,   dstport: rd }\n'
     '    - { interface: uvmMemPortIf, src: uSrc,     srcport: lut, dst: u_uvmMem, dstport: lut }\n'),
]

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def make(work, target):
    env = dict(os.environ, NO_COLOR='1')
    return subprocess.run(['make', '-C', work, f'A2C_ROOT={base_dir}', f'REPO_ROOT={work}', target],
                          capture_output=True, text=True, timeout=1800, env=env)


NO_MODEL = ('        hasMdl: true\n        hasTb: true\n        hasUvm: true\n',
            '        hasMdl: false\n        hasTb: true\n        hasUvm: true\n')


def copy_example(work, edits):
    def ignore(directory, names):
        skip = {'.gen', 'build', 'build_xrun', 'uvmMem.db', '.uvmMem.db'}
        return [name for name in names if name in skip]
    shutil.copytree(EXAMPLE, work, ignore=ignore, dirs_exist_ok=True)
    path = os.path.join(work, 'yaml', 'uvmMem.yaml')
    with open(path) as f:
        text = f.read()
    for old, new in edits:
        if old not in text:
            return f"the example YAML no longer holds {old.strip()!r}"
        text = text.replace(old, new, 1)
    with open(path, 'w') as f:
        f.write(text)
    return None


def read(work, *parts):
    with open(os.path.join(work, *parts)) as f:
        return f.read()


def pins(path):
    """The pin names of a port map, in order."""
    with open(path) as f:
        return [line.split()[0] for line in f if line.strip() and not line.startswith('#')]


def credit_pins(ports):
    return [pin for port in ports for pin in (f'{port}_model_credit', f'{port}_model_held')]


def check_boundary(work):
    vl = os.path.join(work, '.gen', 'vl')
    tb = pins(os.path.join(vl, 'uvmMem_uvm_tb.portmap'))
    want = credit_pins(CREDITED)
    got = [pin for pin in tb if 'model_credit' in pin or 'model_held' in pin]
    check(got == want, f"the testbench port map holds the credit pins of wr and rd only, in port order (got {got})")
    if all(pin in tb for pin in want + ['rst_n', 'uvm_done']):
        check(tb.index('rst_n') < tb.index(want[0]) and tb.index(want[-1]) < tb.index('uvm_done'),
              "the credit pins sit after the resets and before the completion pins")
    with open(os.path.join(vl, 'uvmMem_uvm_tb.portmap')) as f:
        rows = {line.split()[0]: line.split()[1:] for line in f if line.strip() and not line.startswith('#')}
    check(all(rows.get(f'{p}_model_credit') == ['32', 'bitvector', 'sc_bv'] for p in CREDITED)
          and all(rows.get(f'{p}_model_held') == ['1', 'bit', 'bool'] for p in CREDITED),
          "each credit pin is a 32-bit vector and each held pin one bit in the port map")
    shell = read(work, '.gen', 'vl', 'uvmMem_uvm_tb_xcelium.h')
    check(all(f'sc_out<sc_bv<32>> {p}_model_credit;' in shell and f'sc_in<bool> {p}_model_held;' in shell for p in CREDITED)
          and not any(f'{p}_model_' in shell for p in UNCREDITED),
          "the Xcelium shell drives each credit pin out and takes each held pin in, for wr and rd only")
    hdl = read(work, '.gen', 'vl', 'uvmMem_hdl_sv_wrapper.portmap')
    check('model_credit' not in hdl and 'model_held' not in hdl, "the HDL wrapper top has no credit pins")


def branch(text, start, end):
    """The lines of the testbench module between two preprocessor lines."""
    lines = text.splitlines()
    first = lines.index(start)
    last = next(i for i in range(first + 1, len(lines)) if lines[i].startswith(end))
    return '\n'.join(lines[first + 1:last])


def check_testbench(work):
    text = read(work, 'uvm', 'uvmMem_uvm_tb.sv')
    both = branch(text, '`ifdef A2C_UVM_BOTH_DUT', '`elsif')
    rtl = branch(text, '`elsif A2C_UVM_RTL_DUT', '`else')
    model = branch(text, '`else', '`endif')
    for port in CREDITED:
        check(f'a2c_credit_if {port}_credit();' in both
              and f'assign {port}_model_credit = {port}_credit.credit;' in both
              and f'assign {port}_credit.held = {port}_model_held;' in both,
              f"under A2C_UVM_BOTH_DUT, {port}_credit carries {port}'s credit and held pins")
        for name, body in (('rtl', rtl), ('model', model)):
            check(f"assign {port}_model_credit = '0;" in body and f'{port}_credit' not in body,
                  f"the {name} branch ties {port}_model_credit to zero and declares no a2c_credit_if")
        sets = [line.strip() for line in text.splitlines() if f'"{port}_credit"' in line]
        check(len(sets) == 1 and sets[0] == f'uvm_config_db#(virtual a2c_credit_if)::set(null, "uvm_test_top.*", "{port}_credit", {port}_credit);',
              f"one config_db set publishes {port}_credit (got {sets})")
    for port in UNCREDITED:
        check(f'{port}_credit' not in text and f'{port}_model_credit' not in text, f"{port} has no credit in the testbench module")
    if sum(len(re.findall(rf'"{p}_credit"', text)) for p in CREDITED):
        sets_at = text.index('"wr_credit"')
        guard = text.rfind('`ifdef A2C_UVM_BOTH_DUT', 0, sets_at)
        check(guard != -1 and text.find('`endif', guard) > sets_at and text.find('`else', guard) > sets_at,
              "the credit sets are under A2C_UVM_BOTH_DUT")


def check_env(work):
    text = read(work, 'uvm', 'uvmMem_uvm_pkg.sv')
    for port in CREDITED:
        fetch = f'if (!uvm_config_db#(virtual a2c_credit_if)::get(this, "", "{port}_credit", {port}_cfg.credit_vif)) begin'
        check(fetch in text and f'`uvm_fatal("A2C_CFG", "no virtual a2c_credit_if \'{port}_credit\'")' in text,
              f"the env fetches {port}_credit into {port}_cfg.credit_vif and stops without it")
        model_fetch = text.find(f'"{port}_model", {port}_cfg.model_vif')
        check(model_fetch != -1 and text.find(fetch) > model_fetch,
              f"the env fetches {port}'s credit only where it fetches its model lane")
    for port in UNCREDITED:
        check(f'{port}_cfg.credit_vif' not in text, f"the env gives {port} no credit_vif")


def check_wrapper(work):
    text = read(work, 'uvm', 'uvmMem_uvm_sc_wrapper.h')
    for port in CREDITED:
        check(f'sc_signal<sc_bv<32>> {port}_model_credit;' in text and f'sc_signal<bool> {port}_model_held;' in text
              and f'tb_hdl.{port}_model_credit({port}_model_credit);' in text
              and f'tb_hdl.{port}_model_held({port}_model_held);' in text,
              f"the wrapper binds {port}'s credit and held pins to signals")
        call = re.search(rf'if \(uvmMem_uvm_run::rtlDut\) \{{\s*{port}_bfm_inst->setModelCredit\(&{port}_model_credit, &{port}_model_held\);\s*\}}',
                         text)
        check(call is not None, f"the wrapper hands {port}'s memory_dst_bfm its credit only when the run holds the RTL")
    for port in UNCREDITED:
        check(f'{port}_bfm_inst->setModelCredit' not in text and f'{port}_model_credit' not in text,
              f"{port}'s BFM gets no credit")
    orders = re.findall(r'(\w+)_bfm_inst->setWriteOrder\(&m_writeOrder\);', text)
    model_only = re.findall(r'if \(!uvmMem_uvm_run::rtlDut\) \{\s*(\w+)_bfm_inst->setWriteOrder\(&m_writeOrder\);\s*\}', text)
    check('memory_write_order m_writeOrder;' in text and orders == CREDITED and model_only == CREDITED,
          f"the wrapper gives the BFMs of wr and rd one write order, only when the run holds the model alone "
          f"(got {orders}, {model_only} under !rtlDut)")


def check_no_model(work):
    tb = pins(os.path.join(work, '.gen', 'vl', 'uvmMem_uvm_tb.portmap'))
    got = [pin for pin in tb if 'model_credit' in pin or 'model_held' in pin]
    check(got == [], f"without a model the testbench port map holds no credit pins (got {got})")
    text = read(work, 'uvm', 'uvmMem_uvm_tb.sv')
    check('a2c_credit_if' not in text and '_model_credit' not in text,
          "without a model the testbench module has no credit pins or a2c_credit_if")
    check('credit_vif' not in read(work, 'uvm', 'uvmMem_uvm_pkg.sv'), "without a model the env sets no credit_vif")


def run_all_tests():
    print("\n" + "=" * 70)
    print("UVM MODE B MEMORY CREDIT")
    print("=" * 70)
    for edits, checks in ((EDITS, (check_boundary, check_testbench, check_env, check_wrapper)),
                          (EDITS + [NO_MODEL], (check_no_model,))):
        work = tempfile.mkdtemp(prefix='a2c_uvm_model_credit_')
        try:
            problem = copy_example(work, edits)
            if problem:
                check(False, problem)
                continue
            for target in ('db', 'newmodule', 'gen', os.path.join(work, '.gen', 'vl', '.boundary')):
                result = make(work, target)
                if result.returncode != 0:
                    check(False, f"make {target} succeeds (rc={result.returncode})\n{result.stdout[-3000:]}\n{result.stderr[-3000:]}")
                    break
            else:
                for check_case in checks:
                    check_case(work)
        finally:
            remove_tree(work)
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        return 1
    print("\n  ALL TESTS PASSED!")
    return 0


if __name__ == '__main__':
    sys.exit(run_all_tests())
