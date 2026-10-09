#!/usr/bin/env python3
"""Each field of a non-parameterizable struct in the firmware header carries
its packed bit range as a comment, and the range is where pack() puts it. The
first YAML field is the MSB; the header declares fields last-YAML-field first.
Ranges are absolute bit indices into the packed value.

multiSt spans two 64-bit words and holds an array and a nested struct, so a
range that ignored the array length, the nested width or the word boundary
would show up: lo [39:0], mid [47:40], arr [63:48], hi [79:64]. The model
flavour of the same struct carries no ranges, and neither does a
parameterizable struct, whose widths depend on the variant.
"""

import os
import sys
import types

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.systemcGen import genSystemC
from templates.systemc import structures

from _addrctl_helpers import build_database, cleanup, projectOpen


ARCH_YAML = """ipParameters:
    constants:
        P_W: { value: 8, maxValue: 16, desc: "Parameterized width" }
    types:
        pT: { width: P_W, desc: "Parameterized field" }

types:
    u4T:  { width: 4,  desc: "Nibble" }
    u8T:  { width: 8,  desc: "Byte" }
    u16T: { width: 16, desc: "Half" }
    u40T: { width: 40, desc: "Forty" }

structures:
    innerSt:
        x: { varType: u4T, desc: "inner high" }
        y: { varType: u4T, desc: "inner low" }
    multiSt:
        hi:  { varType: u16T, desc: "first field" }
        arr: { varType: u8T, arraySize: 2, desc: "two bytes" }
        mid: { subStruct: innerSt, desc: "nested" }
        lo:  { varType: u40T, desc: "last field" }
    paramSt:
        pa: { varType: pT, desc: "param first" }
        pb: { varType: u8T, desc: "param last" }

blocks:
    top:
        desc: "Top container"
        hasMdl: true
    ip:
        desc: "Parameterized block"
        params: [P_W]

instances:
    uTop: { container: top, instanceType: top }
    uIp:  { container: top, instanceType: ip, variant: variant0 }

parameters:
    ip:
        variant0:
            P_W: 8
"""

EXPECTED_FW_LINES = [
    "    u40T lo; /* [39:0] */ //last field",
    "    innerSt mid; /* [47:40] */ //nested",
    "    u8T arr[2]; /* [63:48] */ //two bytes",
    "    u16T hi; /* [79:64] */ //first field",
]


def _render(prj, mode, name='multiSt'):
    """Struct `name` as the structures template renders it for `mode`."""
    for context in prj.yamlContext:
        if context.startswith('_'):
            continue
        data = prj.getContextData([context], genSystemC.dataTypeMappings)
        genSystemC.calcStructure(genSystemC, data, prj)
        for struct, value in data['structures'].items():
            if value['structure'] == name:
                args = types.SimpleNamespace(mode=mode, section='header',
                                             template='structures', namespace='')
                return structures.oneStruct(args, prj, data, struct, value)
    raise AssertionError(f"{name} was not rendered into any context")


def test_fw_fields_carry_bit_ranges():
    print("\nTest: fw struct fields carry their packed bit range, MSB-first YAML order")
    ok = True
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    try:
        prj = projectOpen(db_path)
        fw = _render(prj, 'fw')
        model = _render(prj, 'model')
        param = _render(prj, 'fw', 'paramSt')
    finally:
        cleanup([project_path, db_path] + arch_paths)
    declared = [line for line in fw if line.startswith('    ') and line.endswith(
        tuple(f"//{d}" for d in ("last field", "nested", "two bytes", "first field")))]
    if declared != EXPECTED_FW_LINES:
        print("  FAIL: fw field declarations differ from the packed layout")
        print("    expected:\n      " + "\n      ".join(EXPECTED_FW_LINES))
        print("    got:\n      " + "\n      ".join(declared))
        ok = False
    else:
        print("  ok: " + "\n  ok: ".join(declared))
    stray = [line for line in model if '/* [' in line]
    if stray:
        print(f"  FAIL: model struct carries bit ranges: {stray}")
        ok = False
    paramFields = [line for line in param if line.endswith(('//param first', '//param last'))]
    if len(paramFields) != 2:
        print(f"  FAIL: expected paramSt's two field declarations, got {paramFields}")
        ok = False
    stray = [line for line in paramFields if '/* [' in line]
    if stray:
        print(f"  FAIL: parameterizable struct carries bit ranges: {stray}")
        ok = False
    elif len(paramFields) == 2:
        print("  ok: paramSt fields carry no range")
    return ok


def run_all_tests():
    results = [('test_fw_fields_carry_bit_ranges', test_fw_fields_carry_bit_ranges())]
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n  Passed: {passed}/{len(results)}")
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
