#!/usr/bin/env python3
"""rtl.f names an include directory only for a context with RTL output.

A context's RTL directory holds its package and its blocks' RTL. A compile
context with neither gets no `+incdir+` in rtl.f, because that directory is
never created. A project's own interface reaches the HDL flows through the
project's `EXTRA_HDL_FILES`, as the base interfaces do through `a2c.f`.

The fixture's design context emits a package and owns the blocks. It includes
a context holding one interface definition and an aggregator context holding
only an `include:` line. After `db`, `newmodule` and generating rtl.f, the
only `+incdir+` is the design's directory and the package is still listed.
"""

import os
import shutil
import sys
import tempfile

from _addrctl_helpers import APB_PREAMBLE, render_leaf, render_plain_block, render_router
from test_memory_firmware_access import PROJECT, _arch2code

INTF = """interface_defs:
  tstlvl :
    timing: fixed
    parameters :
      data_t : { datatype : struct }
    signals:
      data : data_t
    modports :
      src :
        inputs : []
        outputs: ['data']
      dst :
        inputs : ['data']
        outputs: []
    sc_channel :
      type : 'tstlvl'
      multicycle_types : []
      set_initial_value: true
    multiDst : True
"""

AGG = """include:
    - ../intf/tstlvl_if.yaml
"""

DESIGN = """include:
    - shared.yaml
    - intf/tstlvl_if.yaml
    - agg/agg.yaml

blocks:
{blocks}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

registers:
    - {{ register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "leafA configuration" }}
"""

BLOCKS = (render_plain_block('top') + render_plain_block('cpu')
          + render_router('apbDecode', 'top') + render_leaf('leafA'))

FAILURES = []


def check(condition, message):
    print(f"  {'PASS' if condition else 'FAIL'}: {message}")
    if not condition:
        FAILURES.append(message)


def test_rtldotf_skips_interface_only_context():
    fixture = tempfile.mkdtemp(prefix='a2c_rtldotf_intf_')
    try:
        os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
        os.makedirs(os.path.join(fixture, 'yaml', 'intf'))
        os.makedirs(os.path.join(fixture, 'yaml', 'agg'))
        with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
            f.write(PROJECT.replace('fwAccess', 'intfOnly'))
        with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
            f.write(APB_PREAMBLE)
        with open(os.path.join(fixture, 'yaml', 'intf', 'tstlvl_if.yaml'), 'w') as f:
            f.write(INTF)
        with open(os.path.join(fixture, 'yaml', 'agg', 'agg.yaml'), 'w') as f:
            f.write(AGG)
        with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
            f.write(DESIGN.format(blocks=BLOCKS))

        db = os.path.join(fixture, 'intfOnly.db')
        steps = [('database build', ['--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), '--db', db]),
                 ('newmodule', ['--db', db, '-r', '--newmodule'])]
        for label, args in steps:
            run = _arch2code(*args, cwd=fixture)
            if run.returncode != 0:
                check(False, f"{label} succeeds:\n{run.stdout}\n{run.stderr}")
                return

        rtlfs = [os.path.join(root, n) for root, _, names in os.walk(fixture) for n in names if n == 'rtl.f']
        check(len(rtlfs) == 1, f"newmodule scaffolds one rtl.f (found {len(rtlfs)})")
        if len(rtlfs) != 1:
            return
        rtlf = rtlfs[0]
        run = _arch2code('--db', db, '-r', '--systemVerilog', '--file', rtlf, cwd=fixture)
        check(run.returncode == 0, f"rtl.f generates:\n{run.stdout}\n{run.stderr}")
        text = open(rtlf).read()
        incdirs = [line.split('+incdir+', 1)[1].strip() for line in text.splitlines() if line.startswith('+incdir+')]
        check(incdirs == ['.'], f"rtl.f names only the design's include directory ({incdirs})")
        check(any(line.endswith('_package.sv') for line in text.splitlines()),
              "rtl.f still lists the design's package")
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


if __name__ == '__main__':
    test_rtldotf_skips_interface_only_context()
    if FAILURES:
        print(f"\n  SOME TESTS FAILED ({len(FAILURES)})")
        sys.exit(1)
    print("\n  ALL TESTS PASSED!")
    sys.exit(0)
