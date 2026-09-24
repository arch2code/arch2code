#!/usr/bin/env python3
"""Channel constructors must carry their multicycle arguments.

`sc_multicycle_ctor_args` in `pysrc/intf_gen_utils.py` builds the trailing
multiCycleType / maxTransferSize / trackerName arguments for a channel
constructor. A channel built without them keeps a null
`rdy_vld_channel::m_multicycle`, so the first `push_burst()`, `getWritePtr()`
or `getReadPtr()` on it dereferences a null pointer.

These tests pin the helper's contract and assert that every
channel-constructing emitter in the testbench template routes through it.

`sc_multicycle_ctor_args` takes two distinct connection-row shapes: a real
`connectDouble` connection row, where `maxTransferSize` and `tracker` are
schema-guaranteed fields, and a testbench-synthesized `connectionMaps` row
(`_cm_synth_conn` in testbench.py), which has no `tracker` field: that
schema has no alloc/dealloc concept for a local-only channel. `tracker` is
therefore read with a `.get` default; `maxTransferSize` is present on both
row shapes and read directly.
"""

import os
import re
import sys

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.intf_gen_utils import sc_multicycle_ctor_args


class _FakePrj:
    def __init__(self, interfaces):
        self.data = {'interfaces': interfaces}


MULTICYCLE_PRJ = _FakePrj({
    'axiRd': {
        'maxTransferSize': 256,
        'trackerType': '',
        'multiCycleMode': 'api_list_size',
    },
    'plainRv': {
        'maxTransferSize': '0',
        'trackerType': '',
        'multiCycleMode': '',
    },
    'trackedRd': {
        'maxTransferSize': 2048,
        'trackerType': 'cmdid',
        'multiCycleMode': 'api_list_tracker',
    },
})


def _check(label, got, want):
    if got != want:
        print(f"FAIL: {label}\n  got:  {got!r}\n  want: {want!r}")
        return False
    return True


def _test_multicycle_interface_gets_its_arguments():
    extra, auto = sc_multicycle_ctor_args(
        {'interfaceKey': 'axiRd', 'maxTransferSize': '0', 'tracker': ''},
        True, MULTICYCLE_PRJ)
    return (_check("multicycle interface extra args",
                   extra, ', "api_list_size", 256, ""')
            and _check("multicycle interface auto mode", auto, ''))


def _test_tracker_type_is_spelled():
    extra, _ = sc_multicycle_ctor_args(
        {'interfaceKey': 'trackedRd', 'maxTransferSize': '0', 'tracker': ''},
        True, MULTICYCLE_PRJ)
    return _check("tracker type spelled",
                  extra, ', "api_list_tracker", 2048, "tracker:cmdid"')


def _test_connection_overrides_transfer_size():
    extra, _ = sc_multicycle_ctor_args(
        {'interfaceKey': 'axiRd', 'maxTransferSize': '64', 'tracker': ''},
        True, MULTICYCLE_PRJ)
    return _check("connection maxTransferSize override",
                  extra, ', "api_list_size", 64, ""')


def _test_no_arguments_without_a_multicycle_mode():
    extra, _ = sc_multicycle_ctor_args(
        {'interfaceKey': 'plainRv', 'maxTransferSize': '0', 'tracker': ''},
        True, MULTICYCLE_PRJ)
    return _check("interface without multiCycleMode", extra, '')


def _test_no_arguments_when_channel_is_not_multicycle():
    # multicycle_types is the interface definition's sc_channel flag; a channel
    # type with no multicycle overload must not be handed the extra arguments
    # even when the interface declares a mode.
    extra, _ = sc_multicycle_ctor_args(
        {'interfaceKey': 'axiRd', 'maxTransferSize': '0', 'tracker': ''},
        False, MULTICYCLE_PRJ)
    return _check("non-multicycle channel type", extra, '')


def _test_register_interface_is_tolerated():
    # A register (non-interfaceKey) row, exactly as constructor.py's
    # connectDouble loop passes for a register connection.
    extra, auto = sc_multicycle_ctor_args({}, False, MULTICYCLE_PRJ)
    return (_check("register interface extra", extra, '')
            and _check("register interface auto mode", auto, ''))


def _test_connectionmap_row_without_a_tracker_field_is_tolerated():
    # The testbench-synthesized connectionMaps row (_cm_synth_conn in
    # testbench.py) has no 'tracker' field at all: that schema has no
    # alloc/dealloc concept for a local-only channel. The helper must not
    # KeyError on the missing field.
    extra, auto = sc_multicycle_ctor_args(
        {'interfaceKey': 'axiRd', 'maxTransferSize': '0'}, True, MULTICYCLE_PRJ)
    return (_check("connectionMaps row extra args",
                   extra, ', "api_list_size", 256, ""')
            and _check("connectionMaps row auto mode (no tracker field)",
                       auto, ''))


def _test_testbench_emitters_route_through_the_helper():
    # A channel constructor emitted with a hardcoded f-string that closes
    # right after the owning-block name carries no multicycle arguments;
    # every channel-constructing emitter must route through the shared
    # helper. The emissions span several source lines, so match the whole
    # file text.
    template_path = os.path.join(base_dir, 'templates', 'systemc',
                                  'testbench.py')
    with open(template_path) as f:
        template = f.read()

    if 'sc_multicycle_ctor_args' not in template:
        print("FAIL: testbench.py does not call sc_multicycle_ctor_args")
        return False

    # An owning-block argument closing the constructor immediately is a
    # constructor emitted without the multicycle arguments.
    truncated = re.findall(r'"\{(?:instName|srcInst)\}"\)', template)
    if truncated:
        print(f"FAIL: {len(truncated)} channel constructor emission(s) close "
              "right after the block name, so they carry no multicycle "
              "arguments")
        return False

    # Both emitters (the connectDouble loop and the connectionMaps loop in
    # ext_sec_init) must be present.
    complete = re.findall(r'"\{(?:instName|srcInst)\}"\{extra\}\{autoMode\}\)',
                          template)
    if len(complete) < 2:
        print(f"FAIL: expected 2 channel constructor emissions carrying the "
              f"multicycle arguments, found {len(complete)}")
        return False
    return True


TESTS = (
    _test_multicycle_interface_gets_its_arguments,
    _test_tracker_type_is_spelled,
    _test_connection_overrides_transfer_size,
    _test_no_arguments_without_a_multicycle_mode,
    _test_no_arguments_when_channel_is_not_multicycle,
    _test_register_interface_is_tolerated,
    _test_connectionmap_row_without_a_tracker_field_is_tolerated,
    _test_testbench_emitters_route_through_the_helper,
)


def run_all_tests():
    print("multicycle channel constructor arguments")
    failed = 0
    for test in TESTS:
        if not test():
            failed = 1
        else:
            print(f"  PASS {test.__name__}")
    if not failed:
        print("PASS")
    return failed


if __name__ == '__main__':
    sys.exit(run_all_tests())
