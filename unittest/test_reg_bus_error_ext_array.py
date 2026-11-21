#!/usr/bin/env python3
"""Each element of an ext array register returns its own owner's write error.

With fileGeneration.regBusErrorResponses, a write to an ext register completes
with the PSLVERR its owner drives on the register's pslverr. An ext register
with count: is an array of external_reg interfaces, one per element, each at
the register's offset plus k element strides. The generated register handler
(templates/systemVerilog/moduleRegs.py) decodes each element on its own, so a
write to element k must capture element k's pslverr.

The fixture is leafA behind a router, holding ext cmd with count: 3. The test
generates leafA_regs.sv and checks, for each element, the write arm at that
element's address drives that element's write strobe and captures that
element's pslverr.
"""

import os
import sys

from _addrctl_helpers import APB_PREAMBLE, render_leaf, render_plain_block, render_router
from _tmp_helpers import temp_dir
from test_memory_firmware_access import PROJECT, _arch2code

COUNT = 3

DESIGN = """include:
    - shared.yaml

blocks:
""" + (render_plain_block('top') + render_plain_block('cpu') + render_router('apbDecode', 'top')
       + render_leaf('leafA')) + """
instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeafA:     { container: top, instanceType: leafA, addressGroup: top }

connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }

registers:
    - { register: cmd, regType: ext, block: leafA, structure: cfgRegSt, count: %d, desc: "ext array" }
""" % COUNT

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def generate_handler(fixture):
    """Build the fixture with regBusErrorResponses on, scaffold it and return
    the text of the generated rtl/leafA_regs.sv."""
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(PROJECT.replace('fwAccess', 'extArrErr') + "    regBusErrorResponses: true\n")
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(DESIGN)
    db = os.path.join(fixture, 'extArrErr.db')
    handler = os.path.join(fixture, 'rtl', 'leafA_regs.sv')
    steps = [('database build', ['--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), '--db', db]),
             ('newmodule', ['--db', db, '-r', '--newmodule']),
             ('generating leafA_regs.sv', ['--db', db, '-r', '--systemVerilog', '--file', handler])]
    for label, args in steps:
        run = _arch2code(*args, cwd=fixture)
        if run.returncode != 0:
            raise AssertionError(f"{label} failed:\n{run.stdout}\n{run.stderr}")
    with open(handler) as f:
        return f.read()


def write_arm(text, k):
    """The lines of the write case arm for element k of cmd, from its label to
    its end, or None when the handler has no such arm."""
    lines = [line.strip() for line in text.splitlines()]
    label = f"REG_LEAFA_CMD_{k} : begin"
    if label not in lines:
        return None
    start = lines.index(label)
    return lines[start:lines.index('end', start) + 1]


def main():
    try:
        with temp_dir(prefix='a2c_ext_arr_err_') as fixture:
            text = generate_handler(fixture)
        check("assign regs.pslverr = wr_slverr | rd_slverr;" in text, "handler drives PSLVERR")
        for k in range(COUNT):
            arm = write_arm(text, k)
            check(arm is not None, f"element {k} has a write arm at REG_LEAFA_CMD_{k}")
            if arm is None:
                continue
            check(f"cmd[{k}].write = 1;" in arm, f"element {k} arm strobes cmd[{k}].write")
            check(f"nxt_wr_slverr = cmd[{k}].pslverr;" in arm, f"element {k} arm captures cmd[{k}].pslverr")
            others = [j for j in range(COUNT) if j != k and any(f"cmd[{j}]" in line for line in arm)]
            check(not others, f"element {k} arm touches no other element")
    except Exception as exc:
        check(False, str(exc))
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        return 1
    print("\n  ALL TESTS PASSED!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
