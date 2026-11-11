#!/usr/bin/env python3
"""An interface type's UVM flags match the members its agent config declares.

The generated env sets `<port>_cfg.max_transfer_bytes` on every port of a type
flagged `uvmMaxTransferBytes: true`, and `<port>_cfg.id_unbound` on a port that
leaves the parameter named by the type's `uvmIdParam` unbound, and in Mode B
`<port>_cfg.credit_vif` on every DUT src port of a type flagged
`uvmModelCredit: true` (`getBDUvm` in pysrc/processYaml.py,
`templates/systemVerilog/uvmPkg.py`). A flag on a type
whose `<type>_config` lacks the member passes `make db` and fails only when a
simulator compiles the env. A config that has the member on an unflagged type
is never set, so its agent runs without the limit the model's channel needs,
or compares IDs a port never drives, or stops in Mode B for want of the
credit pins its testbench top never carries. Every flag needs `uvmAgent: true`, since
only a type with an agent has a config, and `uvmIdParam` must name one of the
type's parameters.

`bfmWriteOrder: true` makes the UVM SystemC wrapper call `setWriteOrder()` on
the type's dst BFM, so it must agree with `<type>_bfm.h` declaring it: a flag
without the declaration fails only when the wrapper compiles, and a declaration
without the flag is never used. It also needs `uvmAgent: true`.

Definitions are discovered by walking the shipped interface trees, Pro's
included when present, so a newly flagged type is checked without anyone
adding it to a list.
"""

import os
import re
import sys

import yaml


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
pro_dir = os.path.join(os.path.dirname(base_dir), 'pro')
INTERFACE_ROOTS = (os.path.join(base_dir, 'interfaces'), os.path.join(pro_dir, 'interfaces'))

# (definition field, config member) pairs
FLAGS = (('uvmMaxTransferBytes', 'max_transfer_bytes'), ('uvmIdParam', 'id_unbound'), ('uvmModelCredit', 'credit_vif'))


def declaration(member):
    return re.compile(rf'^\s*(?:int|bit|logic|longint|shortint|integer|virtual)\b[^;=]*\b{member}\b', re.MULTILINE)


def definitions():
    """(interface type, definition file, definition) for every shipped type."""
    found = list()
    for root in INTERFACE_ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for name in sorted(filenames):
                if not name.endswith('.yaml'):
                    continue
                path = os.path.join(dirpath, name)
                with open(path) as f:
                    content = yaml.safe_load(f)
                for intfType, definition in (content.get('interface_defs') or {}).items():
                    found.append((intfType, path, definition))
    return found


def config_body(intfType, path):
    """The pkg path and the body of <type>_config in the type's agent package."""
    pkg = os.path.join(os.path.dirname(path), f'{intfType}_uvm_pkg.sv')
    with open(pkg) as f:
        text = f.read()
    body = re.search(rf'\bclass\s+{intfType}_config\b(.*?)\bendclass\b', text, re.DOTALL)
    return pkg, body.group(1) if body else ''


def run_all_tests():
    found = definitions()
    problems = list()
    for field, member in FLAGS:
        flagged = [t for t, p, d in found if d.get(field)]
        if not flagged:
            problems.append(f"no shipped interface definition sets {field}; the discovery walk found "
                            f"nothing to check")
            continue
        for intfType, path, definition in found:
            isFlagged = bool(definition.get(field))
            if not definition.get('uvmAgent'):
                if isFlagged:
                    problems.append(f"interface type '{intfType}' ({path}) sets {field} without "
                                    f"uvmAgent: true. Only a type with an agent has a config to carry "
                                    f"{member}; remove the field or ship the agent.")
                continue
            if isFlagged and field == 'uvmIdParam' and definition[field] not in (definition.get('parameters') or {}):
                problems.append(f"interface type '{intfType}' ({path}) sets uvmIdParam "
                                f"'{definition[field]}', which is not one of its parameters.")
            pkg, body = config_body(intfType, path)
            declares = declaration(member).search(body) is not None
            if isFlagged and not declares:
                problems.append(f"interface type '{intfType}' ({path}) sets {field} but {intfType}_config "
                                f"in {pkg} declares no {member}. The generated env sets it; add the "
                                f"member or remove the field.")
            elif declares and not isFlagged:
                problems.append(f"{intfType}_config in {pkg} declares {member} but interface type "
                                f"'{intfType}' ({path}) does not set {field}, so the generated env "
                                f"never sets it. Add the field to the definition.")
            elif isFlagged:
                print(f"  PASS: {intfType} ({os.path.relpath(path, base_dir)}) sets {field} and "
                      f"{intfType}_config declares {member}")
    if not any(d.get('bfmWriteOrder') for t, p, d in found):
        problems.append("no shipped interface definition sets bfmWriteOrder; the discovery walk found nothing "
                        "to check")
    for intfType, path, definition in found:
        isFlagged = bool(definition.get('bfmWriteOrder'))
        if isFlagged and not definition.get('uvmAgent'):
            problems.append(f"interface type '{intfType}' ({path}) sets bfmWriteOrder without uvmAgent: true.")
        bfm = os.path.join(os.path.dirname(path), f'{intfType}_bfm.h')
        declares = os.path.isfile(bfm) and re.search(r'\bsetWriteOrder\s*\(', open(bfm).read()) is not None
        if isFlagged and not declares:
            problems.append(f"interface type '{intfType}' ({path}) sets bfmWriteOrder but {bfm} declares no "
                            f"setWriteOrder(). The UVM SystemC wrapper calls it; add it or remove the field.")
        elif declares and not isFlagged:
            problems.append(f"{bfm} declares setWriteOrder() but interface type '{intfType}' ({path}) does not "
                            f"set bfmWriteOrder, so the UVM SystemC wrapper never calls it. Add the field.")
        elif isFlagged:
            print(f"  PASS: {intfType} ({os.path.relpath(path, base_dir)}) sets bfmWriteOrder and {intfType}_bfm.h "
                  f"declares setWriteOrder()")
    for problem in problems:
        print(f"  FAIL: {problem}")
    if problems:
        print(f"\nFAIL: {len(problems)} UVM interface flag problem(s)")
        return 1
    print("\nPASS: the flagged interface types, and only they, declare the config members their flags set")
    return 0


if __name__ == '__main__':
    sys.exit(run_all_tests())
