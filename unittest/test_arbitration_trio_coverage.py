#!/usr/bin/env python3
"""Compile-contract coverage for the multi-interface arbitration trio.

`setExternalEvent(sc_event*)` / `isActive()` / `isNotActive()` is a channel
family's opt-in into the documented multi-interface arbitration pattern
(rules/skills/systemc-synchronization.md Section 1). A family that declares
one of the three without the other two silently breaks that pattern for
whichever caller reaches the missing piece: the pure-virtual declaration and
the concrete channel override must both be complete, never partial.

This suite discovers every `*_channel.h` under interfaces/ rather than
listing channel families by name, so a family authored tomorrow that opts
into the trio is checked without anyone updating this file. It also pins the
set of families that support the trio today, because the discovery-based
all-or-nothing check above cannot catch a family silently losing the trio
entirely (e.g. a future edit that removes both the pure-virtual declaration
and the concrete override together leaves nothing for that check to see).
"""

import glob
import os
import re
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAILURES = []


def check(condition, message):
    if condition:
        print(f"  PASS: {message}")
    else:
        print(f"  FAIL: {message}")
        FAILURES.append(message)


# Families that support the full arbitration trio: a single SC_THREAD can
# service N ports of any of these via one shared sc_event, scanning
# isActive()/isNotActive() under a wait(event) loop. Every one of these must
# show up as trio-complete below; a family missing from this set has lost
# arbitration support entirely, which the discovery-based all-or-nothing
# check above cannot detect on its own since it only fires when a family
# declares part of the trio (e.g. raw/status/external_reg carry only
# setExternalEvent and never trip that check, but they also never claimed
# full trio support).
REQUIRED_FAMILIES = {
    'rdy_vld', 'axi_read', 'axi_write', 'axi4_stream', 'apb', 'memory',
}

PURE_VIRTUAL_RE = {
    'isActive': re.compile(r'virtual\s+bool\s+isActive\s*\(\s*\)\s*=\s*0\s*;'),
    'isNotActive': re.compile(r'virtual\s+bool\s+isNotActive\s*\(\s*\)\s*=\s*0\s*;'),
    'setExternalEvent': re.compile(
        r'virtual\s+void\s+setExternalEvent\s*\(\s*sc_event\s*\*\s*event\s*\)\s*=\s*0\s*;'),
}

OVERRIDE_RE = {
    'isActive': re.compile(r'\bisActive\s*\(\s*\)\s*override\b'),
    'isNotActive': re.compile(r'\bisNotActive\s*\(\s*\)\s*override\b'),
    'setExternalEvent': re.compile(
        r'setExternalEvent\s*\(\s*sc_event\s*\*\s*event\s*\)\s*override\b'),
}


def discover_channel_headers():
    """Map channel family name -> `*_channel.h` path, walking interfaces/.

    Discovery rather than a list: a channel family authored tomorrow is
    checked without this file being edited.
    """
    found = {}
    pattern = os.path.join(base_dir, 'interfaces', '*', '*_channel.h')
    for path in sorted(glob.glob(pattern)):
        family = os.path.basename(path)[:-len('_channel.h')]
        found[family] = path
    return found


def test_trio_is_all_or_nothing(headers):
    """A family that declares any one trio method must declare and
    implement all three; a partial family is a silent arbitration-pattern
    break for whichever caller reaches the missing piece."""
    trio_complete_families = set()
    for family, path in headers.items():
        with open(path, 'r') as f:
            text = f.read()

        declared = {name: bool(rx.search(text)) for name, rx in PURE_VIRTUAL_RE.items()}
        if not (declared['isActive'] or declared['isNotActive']):
            # Some families (external_reg, raw, status) declare only
            # setExternalEvent and never adopted isActive/isNotActive;
            # setExternalEvent alone is not treated as an opt-in below, since
            # it is also the marker of that separate, partial shape.
            continue

        implemented = {name: bool(rx.search(text)) for name, rx in OVERRIDE_RE.items()}

        for name in PURE_VIRTUAL_RE:
            check(declared[name],
                  f"{family}_channel.h declares '{name}' as pure virtual")
        for name in OVERRIDE_RE:
            check(implemented[name],
                  f"{family}_channel.h provides a concrete '{name}' override")

        if all(declared.values()) and all(implemented.values()):
            trio_complete_families.add(family)

    return trio_complete_families


def test_required_families_are_trio_complete(trio_complete_families):
    missing = REQUIRED_FAMILIES - trio_complete_families
    check(not missing,
          f"every family that must support the arbitration trio still does "
          f"(missing: {sorted(missing)})" if missing else
          "every family that must support the arbitration trio (rdy_vld, "
          "axi_read, axi_write, axi4_stream, apb, memory) still does")


def main():
    print("=" * 72)
    print("TESTING ARBITRATION TRIO COMPILE-CONTRACT COVERAGE")
    print("=" * 72)
    headers = discover_channel_headers()
    check(len(headers) > 0, "discovered at least one *_channel.h under interfaces/")

    trio_complete_families = test_trio_is_all_or_nothing(headers)
    print(f"  trio-complete families: {sorted(trio_complete_families)}")
    test_required_families_are_trio_complete(trio_complete_families)

    print("\n" + "=" * 72)
    if FAILURES:
        print(f"RESULT: {len(FAILURES)} check(s) FAILED")
        return 1
    print("RESULT: all arbitration trio compile-contract checks passed")
    return 0


if __name__ == '__main__':
    sys.exit(main())
