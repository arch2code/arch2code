#!/usr/bin/env python3
"""The model decoder holds every slot of an instance it does not dispatch to.

A router with eight 0x1000-byte slots serves leafA in slot 0, a register-less
block in slots 1 and 2 (addressMultiples 2), and leafB in slot 3. The router
has no channel to the register-less block, so its slots are empty: the RTL
decoder reads 32'hBADD_C0DE there and selects leafB from 0x3000. The model
decoder picks a channel by slot index, so its channel list must hold one null
entry per slot of the register-less block. With one null entry for both,
leafB moves to slot 2 in the model and slot 3 reads 32'hBADD_C0DE, the
reverse of the RTL.

A second variant adds an instance of the group whose container is never
instantiated. It still takes slot 1, so the RTL selects leafB from 0x4000, and
the model must leave that slot null rather than close the gap.

The fixture is generated outside the repository working tree. The test reads
the generated model decoder's channel list and the RTL decoder's select
compares, and checks that each child's model slot times the decoder's address
increment is the lower bound of its RTL window.
"""

import os
import re
import shutil
import sys
import tempfile

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from _addrctl_helpers import APB_PREAMBLE, render_leaf, render_plain_block, render_router
from test_memory_firmware_access import PROJECT, _arch2code, _generated_files

DESIGN = """include:
    - shared.yaml

blocks:
{blocks}
instances:
    uTop:       {{ container: top, instanceType: top }}
    uCPU:       {{ container: top, instanceType: cpu }}
    uAPBDecode: {{ container: top, instanceType: apbDecode }}
    uLeafA:     {{ container: top, instanceType: leafA, addressGroup: top }}
{orphan}    uPlain:     {{ container: top, instanceType: plain, addressGroup: top, addressMultiples: 2 }}
    uLeafB:     {{ container: top, instanceType: leafB, addressGroup: top }}

connections:
    - {{ interface: apbReg, src: uCPU, dst: uAPBDecode }}

registers:
    - {{ register: cfgA, regType: rw, block: leafA, structure: cfgRegSt, desc: "leafA configuration" }}
    - {{ register: cfgB, regType: rw, block: leafB, structure: cfgRegSt, desc: "leafB configuration" }}
"""

ORPHAN = "    uOrphan:    { container: island, instanceType: leafA, addressGroup: top }\n"

BLOCKS = (render_plain_block('top') + render_plain_block('cpu') + render_plain_block('plain')
          + render_plain_block('island')
          + render_router('apbDecode', 'top', address_increment='0x1000', max_address_spaces=8)
          + render_leaf('leafA') + render_leaf('leafB'))


def generate(fixture, orphan):
    """Write the design under `fixture`, build its database, scaffold it and
    regenerate every generated file."""
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(PROJECT.replace('fwAccess', 'slotGap'))
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(APB_PREAMBLE)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(DESIGN.format(blocks=BLOCKS, orphan=orphan))
    db = os.path.join(fixture, 'slotGap.db')
    steps = [('database build', ['--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), '--db', db]),
             ('newmodule', ['--db', db, '-r', '--newmodule'])]
    for label, args in steps:
        run = _arch2code(*args, cwd=fixture)
        if run.returncode != 0:
            raise AssertionError(f"{label} failed:\n{run.stdout}\n{run.stderr}")
    for rel in _generated_files(fixture):
        lang = '--systemVerilog' if rel.endswith('.sv') else '--systemc'
        run = _arch2code('--db', db, '-r', lang, '--file', os.path.join(fixture, rel), cwd=fixture)
        if run.returncode != 0:
            raise AssertionError(f"generating {rel} failed:\n{run.stdout}\n{run.stderr}")


def model_slots(fixture):
    """The model decoder's address increment, and the child instance name for
    each slot of its channel list, None for a null slot."""
    paths = [os.path.join(root, name) for root, _, names in os.walk(fixture)
             for name in names if name.startswith('apbDecode.') and not name.endswith('.sv')]
    text = ''.join(open(p).read() for p in paths)
    # decoder(maxAddressSpaces, log2(addressIncrement), port, {channels})
    match = re.search(r',decoder\(\d+, (\d+), \w+, \{(.*?)\}\)', text, re.S)
    if not match:
        raise AssertionError(f"no decoder channel list in {paths}")
    entries = [e.strip() for e in match.group(2).split(',') if e.strip()]
    return 1 << int(match.group(1)), [None if e == 'nullptr' else e.removeprefix('&apbReg_') for e in entries]


def rtl_lower_bounds(fixture):
    """Lower address bound of each child's RTL select compare."""
    text = open(os.path.join(fixture, 'rtl', 'apbDecode.sv')).read()
    bounds = {}
    for compare, child in re.findall(r"(.*)\n\s*apbReg_(\w+)_next_psel = '1;", text):
        low = re.search(r"apb_addr >= \S+'\(32'h([0-9a-f_]+)\)", compare)
        bounds[child] = int(low.group(1).replace('_', ''), 16) if low else 0
    return bounds


def run_case(label, orphan, leaf_b_offset):
    fixture = tempfile.mkdtemp(prefix='a2c_slot_gap_')
    try:
        generate(fixture, orphan)
        increment, slots = model_slots(fixture)
        bounds = rtl_lower_bounds(fixture)
        model = {child: n * increment for n, child in enumerate(slots) if child}
        if model != bounds or bounds != {'uLeafA': 0, 'uLeafB': leaf_b_offset}:
            raise AssertionError(f"model slot offsets {model} (channel list {slots}) "
                                 f"differ from RTL window lower bounds {bounds}, "
                                 f"or leafB is not at 0x{leaf_b_offset:x}")
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
    print(f"PASS: {label}")
    return True


def main():
    results = [run_case("model decoder slots match the RTL windows around a non-dispatched instance", '', 0x3000),
               run_case("model decoder slots match the RTL windows around an unreachable instance", ORPHAN, 0x4000)]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
