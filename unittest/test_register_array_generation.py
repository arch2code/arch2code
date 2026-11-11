#!/usr/bin/env python3
"""Generated output for register arrays.

Three fixtures, each scaffolded and fully regenerated outside the repository
working tree:

- An ext array whose two elements go to two instances of one child block, one
  `index:` row each. The owner's channel vector has three ends, the handler
  and one child per element, but each element channel has two. The owner
  model, the owner RTL and the child's Verilator wrappers must generate, and
  the owner binds each child to its own element.
- A register handler model whose block owns a `regType: memory` register and
  a larger rw array. The array is placed below the memory, and the handler
  registers its address ranges in ascending order, because addressMap asserts
  that each range starts at or above the end of the previous one.
- One child block reached from two owners, one spelling the array count as
  the literal 2 and one as the constant N2. Both registerConnections orders
  must generate identical child files.
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
from test_memory_firmware_access import PROJECT, _arch2code

HEAD = """include:
    - shared.yaml

blocks:
"""

COMMON_BLOCKS = (render_plain_block('top') + render_plain_block('cpu')
                 + render_router('apbDecode', 'top', address_increment='0x1000', max_address_spaces=8))

COMMON_INSTANCES = """instances:
    uTop:       { container: top, instanceType: top }
    uCPU:       { container: top, instanceType: cpu }
    uAPBDecode: { container: top, instanceType: apbDecode }
"""

COMMON_CONNECTIONS = """connections:
    - { interface: apbReg, src: uCPU, dst: uAPBDecode }
"""

SPLIT_EXT = HEAD + COMMON_BLOCKS + render_leaf('owner') \
    + render_plain_block('child', '        hasVl: true\n') + COMMON_INSTANCES + """\
    uOwner:     { container: top, instanceType: owner, addressGroup: top }
    uF0:        { container: owner, instanceType: child }
    uF1:        { container: owner, instanceType: child }

""" + COMMON_CONNECTIONS + """
registers:
    - { register: extArr, regType: ext, block: owner, structure: cfgRegSt, count: 2, desc: "ext array split across two instances" }

registerConnections:
    - { register: extArr, block: owner, instance: uF0, index: 0 }
    - { register: extArr, block: owner, instance: uF1, index: 1 }
"""

MEMORY_BELOW_ARRAY = HEAD + COMMON_BLOCKS + render_leaf('owner') + render_plain_block('child') \
    + COMMON_INSTANCES + """\
    uOwner:     { container: top, instanceType: owner, addressGroup: top }
    uC:         { container: owner, instanceType: child }

""" + COMMON_CONNECTIONS + """
registers:
    - { register: tbl, regType: memory, block: owner, structure: cfgRegSt, addressStruct: idxSt, wordLines: 2, desc: "small register memory" }
    - { register: arr, regType: rw, block: owner, structure: cfgRegSt, count: 9, desc: "array larger than tbl" }

registerConnections:
    - { register: arr, block: owner, instance: uC }
"""

INDEX_SHARED = APB_PREAMBLE.replace("\nstructures:\n", """    idxT:     { width: 1, desc: "Register memory row index" }

structures:
    idxSt:
        index: { varType: idxT, generator: address }
""", 1)

TWO_OWNERS = HEAD + COMMON_BLOCKS + render_leaf('ownerX') + render_leaf('ownerY') \
    + render_plain_block('child', '        hasVl: true\n') + COMMON_INSTANCES + """\
    uOwnerX:    { container: top, instanceType: ownerX, addressGroup: top }
    uOwnerY:    { container: top, instanceType: ownerY, addressGroup: top }
    uCX:        { container: ownerX, instanceType: child }
    uCY:        { container: ownerY, instanceType: child }

""" + COMMON_CONNECTIONS + """
registers:
    - { register: arr, regType: rw, block: ownerX, structure: cfgRegSt, count: 2, desc: "array with a literal count" }
    - { register: arr, regType: rw, block: ownerY, structure: cfgRegSt, count: N2, desc: "array with a constant count" }

registerConnections:
{rows}"""

ROW_X = "    - { register: arr, block: ownerX, instance: uCX }\n"
ROW_Y = "    - { register: arr, block: ownerY, instance: uCY }\n"
N2 = "    N2:         { value: 2, desc: \"array count\" }\n"


def generated_files(fixture):
    """Every file under the fixture that carries generated regions."""
    found = []
    for root, _, names in os.walk(fixture):
        for name in names:
            if not name.endswith(('.sv', '.svh', '.cppm', '.h', '.cpp')):
                continue
            path = os.path.join(root, name)
            with open(path) as f:
                if 'GENERATED_CODE_BEGIN' in f.read():
                    found.append(os.path.relpath(path, fixture))
    return sorted(found)


def generate(fixture, design, shared=APB_PREAMBLE):
    """Write the design under `fixture`, build its database, scaffold it and
    regenerate every generated file. Returns {relative path: text}."""
    os.makedirs(os.path.join(fixture, 'prj', 'yaml'))
    os.makedirs(os.path.join(fixture, 'yaml'))
    with open(os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), 'w') as f:
        f.write(PROJECT.replace('fwAccess', 'regArr'))
    with open(os.path.join(fixture, 'yaml', 'shared.yaml'), 'w') as f:
        f.write(shared)
    with open(os.path.join(fixture, 'yaml', 'top.yaml'), 'w') as f:
        f.write(design)
    db = os.path.join(fixture, 'regArr.db')
    for label, args in (('database build', ['--yaml', os.path.join(fixture, 'prj', 'yaml', 'project.yaml'), '--db', db]),
                        ('newmodule', ['--db', db, '-r', '--newmodule'])):
        run = _arch2code(*args, cwd=fixture)
        if run.returncode != 0:
            raise AssertionError(f"{label} failed:\n{run.stdout}\n{run.stderr}")
    emitted = dict()
    for rel in generated_files(fixture):
        lang = '--systemVerilog' if rel.endswith(('.sv', '.svh')) else '--systemc'
        run = _arch2code('--db', db, '-r', lang, '--file', os.path.join(fixture, rel), cwd=fixture)
        if run.returncode != 0:
            raise AssertionError(f"generating {rel} failed:\n{run.stdout}\n{run.stderr}")
        with open(os.path.join(fixture, rel)) as f:
            emitted[rel] = f.read()
    return emitted


def emitted_text(emitted, name):
    """The text of the one generated file whose base name is `name`."""
    matches = [rel for rel in emitted if os.path.basename(rel) == name]
    if len(matches) != 1:
        raise AssertionError(f"expected one generated {name}, found {matches} in {sorted(emitted)}")
    return emitted[matches[0]]


def check_split_ext(fixture):
    emitted = generate(fixture, SPLIT_EXT)
    model = emitted_text(emitted, 'owner.cppm')
    for bind in ('uF0->extArr(extArr[0]);', 'uF1->extArr(extArr[1]);', 'u_owner_regs->extArr.bind(extArr);'):
        if bind not in model:
            raise AssertionError(f"owner model does not bind `{bind}`:\n{model}")
    rtl = emitted_text(emitted, 'owner.sv')
    for bind in (r'\.extArr\s*\(extArr\[0\]\)', r'\.extArr\s*\(extArr\[1\]\)'):
        if len(re.findall(bind, rtl)) != 1:
            raise AssertionError(f"owner RTL does not bind `{bind}` once:\n{rtl}")


def check_registration_order(fixture):
    emitted = generate(fixture, MEMORY_BELOW_ARRAY, INDEX_SHARED)
    handler = emitted_text(emitted, 'owner_regs.cppm')
    offsets = {name: int(value, 16) for name, value in
               re.findall(r'constexpr uint64_t (\w+) = (0x[0-9a-fA-F]+);', handler)}
    order = re.findall(r'_a2cRegs\.add(?:Memory|Register)\(\s*(\w+)', handler)
    if len(order) != 2 or any(n not in offsets for n in order) or offsets[order[0]] >= offsets[order[1]]:
        raise AssertionError(f"handler registers {order} out of ascending offset order {offsets}:\n{handler}")


def check_count_spelling_order(fixture):
    shared = APB_PREAMBLE.replace('constants:\n', 'constants:\n' + N2, 1)
    outputs = []
    for label, rows in (('xy', ROW_X + ROW_Y), ('yx', ROW_Y + ROW_X)):
        emitted = generate(os.path.join(fixture, label), TWO_OWNERS.replace('{rows}', rows), shared)
        outputs.append({rel: text for rel, text in emitted.items() if os.path.basename(rel).startswith('child')})
    if not outputs[0] or outputs[0].keys() != outputs[1].keys():
        raise AssertionError(f"child file sets differ: {sorted(outputs[0])} against {sorted(outputs[1])}")
    differ = [rel for rel in outputs[0] if outputs[0][rel] != outputs[1][rel]]
    if differ:
        raise AssertionError(f"child files depend on registerConnections order: {differ}")
    port = [line for line in emitted_text(outputs[0], 'child.sv').splitlines() if 'status_if' in line]
    if not port or any('N2' in line or '[2]' not in line for line in port):
        raise AssertionError(f"child RTL port does not take the resolved count 2: {port}")


def run_case(label, check):
    fixture = tempfile.mkdtemp(prefix='a2c_reg_array_gen_')
    try:
        check(fixture)
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
    print(f"PASS: {label}")
    return True


def main():
    results = [
        run_case("an ext array split by index rows generates, each child bound to its element", check_split_ext),
        run_case("the register handler model registers address ranges in ascending order", check_registration_order),
        run_case("a child port's count spelling does not depend on registerConnections order", check_count_spelling_order),
    ]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(main())
