#!/usr/bin/env python3
"""An ext register wider than the register bus data width is rejected at make db.

The register bus moves 32 bits per access. An ext register no wider than that
takes one bus write and reaches its owner as one command. A wider one would
need one command per word, and the model and RTL disagree on what the owner
sees between them, so projectCreate rejects it, naming the register, its
block, its file, its width and the limit. A 32-bit ext register builds. A
parameterizable structure is checked at its width with its parameterizable
fields at their maximum, fixed fields included. Users do not write a
structure's maxBitwidth, so the diagnostic names the structure and points at
its fixed fields, the maxBitwidth of its field types and the maxValue of any
constant that sets their width.
"""

import os
import sys

from _addrctl_helpers import (
    APB_PREAMBLE,
    build_database,
    cleanup,
    render_leaf,
    render_plain_block,
    render_router,
)


def _arch(ext_types, ip_params=''):
    """ext_types maps each field type of structure extRegSt to its spec, or to
    None for a type ip_params, an ipParameters: section, declares."""
    types = ''.join(f'    {name}:     {{ {spec}, desc: "ext register field" }}\n'
                    for name, spec in ext_types.items() if spec)
    fields = ''.join(f'        {name}Field: {{ varType: {name}, generator: register, desc: "ext register field" }}\n'
                     for name in ext_types)
    preamble = (APB_PREAMBLE
                .replace('    cfgT:     { width: REG_WIDTH,  desc: "Register payload" }\n',
                         '    cfgT:     { width: REG_WIDTH,  desc: "Register payload" }\n' + types)
                .replace('structures:\n',
                         ip_params + 'structures:\n'
                         '    extRegSt:\n' + fields, 1))
    return (preamble.rstrip() + """

blocks:
""" + render_plain_block('top') + render_router('apbDecode', 'top') + render_leaf('leaf') + """
instances:
    uTop:       { container: top, instanceType: top }
    uAPBDecode: { container: top, instanceType: apbDecode }
    uLeaf:      { container: top, instanceType: leaf, addressGroup: top }

registers:
    - { register: wideExt, regType: ext, block: leaf, structure: extRegSt, desc: "external register" }
""")


def _run_case(label, ext_types, expect_success, width_needles, ip_params=''):
    """build_database raises, after cleaning up, when the outcome is wrong."""
    label = f"{label} ext register {'builds' if expect_success else 'is rejected'}"
    try:
        result = build_database(_arch(ext_types, ip_params), expect_success=expect_success)
    except RuntimeError as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    db_path, project_path, arch_paths = result[:3]
    try:
        if not expect_success:
            combined = result[3].stdout + result[3].stderr
            needles = ["ext register 'wideExt'", "block 'leaf'", os.path.basename(arch_paths[0]),
                       "32-bit register bus"] + width_needles
            missing = [n for n in needles if n not in combined]
            if 'one bus access:' in combined:
                missing.append("no colon after 'one bus access'")
            if missing:
                print(f"FAIL: {label}: diagnostic lacks {missing}\n{combined}")
                return False
        print(f"PASS: {label}")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


PW_PARAMS = """ipParameters:
    constants:
        PW: { value: 16, maxValue: 40, desc: "ext field width" }
    types:
        pwT: { width: PW, maxBitwidth: 40, desc: "ext register field" }

"""


def run_all_tests():
    results = [_run_case(f"{width}-bit", {'extT': f"width: {width}"}, ok, [f"is {width} bits wide", "narrow it"])
               for width, ok in ((32, True), (33, False), (64, False))]
    advice = ("the width of structure 'extRegSt' with its parameterizable fields at their maximum",
              "Narrow its fixed fields, or lower the maxBitwidth of its field types and the maxValue of "
              "any parameterizable constant that sets their width, so the structure fits in 32 bits")
    # every field type's maxBitwidth is 24, yet the structure's worst case is 48 bits
    results.append(_run_case("two parameterizable 24-bit-maximum fields",
                             {'aT': "width: 8, maxBitwidth: 24", 'bT': "width: 8, maxBitwidth: 24"}, False,
                             ["up to 48 bits", *advice]))
    # the field type's maxBitwidth and its width constant's maxValue are both 40
    results.append(_run_case("a field whose width constant has maxValue 40", {'pwT': None}, False,
                             ["up to 40 bits", *advice], ip_params=PW_PARAMS))
    # the fixed 24-bit field counts too, though the parameterizable one alone fits
    results.append(_run_case("a fixed 24-bit field and a 16-bit-maximum field",
                             {'fixT': "width: 24", 'pT': "width: 8, maxBitwidth: 16"}, False,
                             ["up to 40 bits", *advice]))
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
