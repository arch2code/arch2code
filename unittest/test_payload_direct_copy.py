#!/usr/bin/env python3
"""C++ definition compatibility at a thunked junction.

A cross-interface adapter always bridges two DIFFERENT payload declarations. When
those two declarations happen to emit identical member storage, the adapter can
transfer the payload whole instead of packing every field to its bit position and
unpacking it again. `projectOpen.structureStorageSignature()` decides that, and
`buildThunkerView` records one boolean per payload pair, which the SystemC layer
spells as a trailing `bool` template argument on the emitted thunker member. The
thunker's copy sites pass that flag to the shared `copyPayload()` helper.

Three things are pinned here:

- The storage descriptor against the emitted declaration. The predicate is only
  as sound as its agreement with what `templates/systemc/includes.py::includeTypes`
  actually emits; if the two ever disagree the verdict is silently wrong and a
  direct copy scrambles data. The descriptor is therefore spelled back into a C++
  declaration and matched against the rendered output, for every type of two
  example projects, with all four storage arms required to be exercised.
- The four labelled verdict classes of `examples/xprojParam/cppAxis`. Every one of
  its four junctions is bit-layout compatible and reaches the adapter; they differ
  only in emitted C++ member storage. `make xproj-param` runs real data through
  all four and checks every field, so this suite pins the verdicts and the flags
  emitted onto the member declaration while the example pins the observable
  behaviour.
- Slot-to-flag correspondence where a protocol carries more than one payload slot.
  Every multi-slot junction in the tree is apb with both slots eligible, so the
  emitted text cannot distinguish a correct flag order from a swapped one; the
  correspondence is pinned instead by rendering the real view under each verdict
  assignment, mixed ones included.
"""

import os
import sys
import tempfile
import types

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen
import pysrc.intf_gen_utils as intf_gen_utils
from pysrc.systemcGen import genSystemC
from templates.systemc.includes import includeTypes

from _addrctl_helpers import cleanup, run_arch2code

CPP_AXIS_PROJECT = os.path.join(
    base_dir, 'examples', 'xprojParam', 'cppAxis', 'prj', 'yaml',
    'xpCppAxisProject.yaml')
IP_TEST_PROJECT = os.path.join(
    base_dir, 'examples', 'ip_test', 'prj', 'yaml', 'ip_testProject.yaml')
SIMPLE_IP_PROJECT = os.path.join(
    base_dir, 'examples', 'simple_ip', 'prj', 'yaml', 'project.yaml')

# The four cppAxis junctions and the verdict each must produce. See the
# "C++ definitions at a thunked junction" section of the example's README for the
# declarations behind each one.
EXPECTED_VERDICTS = {
    # Corresponding storage: (uint64_t, uint8_t) on both sides, sizeof 16/16.
    'uLeafEq':    True,
    # Reversed member storage order: {uint8_t, uint64_t} against
    # {uint64_t, uint8_t}. Equal sizeof and trivially copyable, and a byte copy
    # would still scramble the payload.
    'uLeafOrder': False,
    # Differing signedness only. A copy would in fact be correct here; the
    # predicate is "the definitions are identical", not "a copy happens to work".
    'uLeafSign':  False,
    # Nested against flat: three members against four, sizeof 24 against 16,
    # because the nested header's trailing padding is elided when inlined.
    'uLeafNest':  False,
}

# The thunker member declarations the four junctions must emit. push_ack carries
# one payload pair, so each declaration carries exactly one trailing verdict flag,
# and only the eligible junction's is true.
EXPECTED_MEMBERS = [
    'push_ack_port_thunker<wrapEqSt<Config>, leafEqSt<xpCppLeafEqV0Config>, true>'
    ' thunker_uLeafEq;',
    'push_ack_port_thunker<wrapOrderSt<Config>, leafOrderSt<xpCppLeafOrderV0Config>,'
    ' false> thunker_uLeafOrder;',
    'push_ack_port_thunker<wrapSignSt<Config>, leafSignSt<xpCppLeafSignV0Config>,'
    ' false> thunker_uLeafSign;',
    'push_ack_port_thunker<wrapNestSt<Config>, leafNestSt<xpCppLeafNestV0Config>,'
    ' false> thunker_uLeafNest;',
]


# simple_ip's apb register bus is a multi-slot junction: apb carries two payload
# slots, addr_t then data_t, so its adapter takes two parent types, two child types
# and two trailing verdict flags. The block holds exactly one such member.
MULTI_SLOT_BLOCK = 'simple_ip'
MULTI_SLOT_MEMBER = 'thunker_apbReg_uIp_uIp'

# The declaration the multi-slot member must emit for each (slot 0, slot 1) verdict
# assignment. Both live verdicts are true, so only the two mixed rows distinguish a
# correct flag order from a swapped one.
EXPECTED_MULTI_SLOT = {
    (True, True):
        'apb_port_thunker<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt, '
        'true, true> thunker_apbReg_uIp_uIp;',
    (True, False):
        'apb_port_thunker<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt, '
        'true, false> thunker_apbReg_uIp_uIp;',
    (False, True):
        'apb_port_thunker<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt, '
        'false, true> thunker_apbReg_uIp_uIp;',
    (False, False):
        'apb_port_thunker<apbAddrSt, apbDataSt, ipRegAddrSt, ipRegDataSt, '
        'false, false> thunker_apbReg_uIp_uIp;',
}


def _build_db(project_path, label):
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    result = run_arch2code(project_path, db_path, timeout=180)
    if result.returncode != 0:
        cleanup([db_path])
        raise RuntimeError(
            f"arch2code.py failed on {label}:\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    return db_path


def _pair_verdicts(blockData):
    """{mapped instance name: directCopy} over every adapted connectionMap."""
    verdicts = dict()
    for value in blockData['connectionMaps'].values():
        for end in value.get('crossInterfaceEnds', []):
            pairs = end['thunker']['payloadPairs']
            assert len(pairs) == 1, \
                f"push_ack carries one payload pair, got {len(pairs)}"
            verdicts[end['instance']] = pairs[0]['directCopy']
    return verdicts


def _block_data(prj, blockName):
    key = next(key for key, row in prj.data['blocks'].items()
               if row['block'] == blockName)
    return prj.getBlockData(key)


def _multi_slot_ends(blockData):
    """Every flagged end whose protocol carries more than one payload slot."""
    ends = []
    for byChannelType in blockData['connectDouble'].values():
        for value in byChannelType.values():
            ends += value.get('crossInterfaceEnds', [])
    for value in blockData['connectionMaps'].values():
        ends += value.get('crossInterfaceEnds', [])
    return [end for end in ends if len(end['thunker']['payloadPairs']) > 1]


def _declaration_from_descriptor(typeRow, storage):
    """Spell the C++ declaration includeTypes must emit for this storage."""
    _kind, storageBits, isSigned, wordCount = storage
    container = f"{'int' if isSigned else 'uint'}{storageBits}_t"
    name = typeRow['type']
    if typeRow['isParameterizable']:
        if wordCount == 1:
            return f"template<typename Config> using { name } = {container};"
        return (f"template<typename Config> struct { name } "
                f"{{ uint64_t word[ {wordCount} ]; }};")
    if wordCount == 1:
        return f"typedef { container } { name };"
    return f"struct { name } {{ { container } word[ {wordCount} ]; }};"


def _storage_arm(typeRow, storage):
    return ('parameterizable' if typeRow['isParameterizable'] else 'literal',
            'word array' if storage[3] > 1 else 'scalar')


def _header(name):
    print("\n" + "=" * 70)
    print(f"Test: {name}")
    print("=" * 70)


def test_storage_descriptor_matches_emitted_declaration():
    """The descriptor the predicate compares must spell the type the emitter emits.

    Renders includeTypes for every context of two example projects and requires
    the descriptor's own spelling to appear verbatim in the rendered text. All
    four storage arms must be exercised, so a fixture that stops covering one
    fails here rather than leaving the arm silently unpinned.
    """
    _header("storage descriptor agrees with the emitted type declaration")
    ok = True
    seenArms = set()
    dbs = []
    try:
        for project, label in ((CPP_AXIS_PROJECT, 'cppAxis'),
                               (IP_TEST_PROJECT, 'ip_test')):
            db = _build_db(project, label)
            dbs.append(db)
            prj = projectOpen(db)
            args = types.SimpleNamespace(mode='model', section='')
            for context in prj.yamlContext:
                if context.startswith('_'):
                    # Framework contexts carry no user type declarations.
                    continue
                data = prj.getContextData([context], genSystemC.dataTypeMappings)
                rendered = includeTypes(args, prj, data)
                for typeRow in data['types'].values():
                    storage = prj.typeStorage(typeRow)
                    seenArms.add(_storage_arm(typeRow, storage))
                    expected = _declaration_from_descriptor(typeRow, storage)
                    if expected not in rendered:
                        ok = False
                        print(f"  FAIL: {label} type '{typeRow['type']}' "
                              f"storage {storage} spells\n"
                              f"        {expected}\n"
                              f"        which the emitter did not produce")
        for arm in (('literal', 'scalar'), ('literal', 'word array'),
                    ('parameterizable', 'scalar'),
                    ('parameterizable', 'word array')):
            if arm not in seenArms:
                ok = False
                print(f"  FAIL: no example type exercised the {arm} storage arm")
    finally:
        cleanup(dbs)
    if ok:
        print(f"  PASS: every type's descriptor matched its emitted declaration "
              f"across {len(seenArms)} storage arms")
    return ok


def test_cpp_axis_pair_verdicts():
    """The four labelled cppAxis junctions get the verdicts the fixture records."""
    _header("cppAxis payload pairs get the recorded C++ compatibility verdicts")
    ok = True
    db = _build_db(CPP_AXIS_PROJECT, 'cppAxis')
    try:
        verdicts = _pair_verdicts(_block_data(projectOpen(db), 'xpCppWrap'))
        if set(verdicts) != set(EXPECTED_VERDICTS):
            print(f"  FAIL: adapted junctions are {sorted(verdicts)}, "
                  f"expected {sorted(EXPECTED_VERDICTS)}")
            return False
        for instance, expected in EXPECTED_VERDICTS.items():
            if verdicts[instance] != expected:
                ok = False
                print(f"  FAIL: {instance} directCopy is {verdicts[instance]}, "
                      f"expected {expected}")
    finally:
        cleanup([db])
    if ok:
        print("  PASS: eligible on corresponding storage; ineligible on reversed "
              "order, differing signedness and nesting")
    return ok


def test_cpp_axis_member_flag_emission():
    """The verdict reaches C++ as a trailing template argument on the member."""
    _header("cppAxis spells each junction's verdict onto its thunker member")
    ok = True
    db = _build_db(CPP_AXIS_PROJECT, 'cppAxis')
    try:
        prj = projectOpen(db)
        blockData = _block_data(prj, 'xpCppWrap')
        members = intf_gen_utils.sc_declare_thunkers(blockData, prj, '', blockData)
        if members != EXPECTED_MEMBERS:
            ok = False
            print("  FAIL: emitted thunker members differ from the expected set")
            for line in members:
                print(f"    got:      {line}")
            for line in EXPECTED_MEMBERS:
                print(f"    expected: {line}")
    finally:
        cleanup([db])
    if ok:
        print("  PASS: trailing flag is true for wrapEqSt/leafEqSt only")
    return ok


def test_multi_slot_flag_slot_correspondence():
    """Flag i belongs to payload slot i, on a protocol carrying more than one slot.

    Two properties, both invisible in the emitted tree. Every multi-slot junction
    that exists is apb with both slots eligible, so a generator that emitted the
    flags in the wrong order would produce byte-identical output; and apb's four
    payload declarations are all the same size, so the adapters' sizeof
    static_assert backstop would not fire on a swap either.

    So the pairing is checked structurally - pair i must join payload i to payload
    i+N and the two must be the same protocol slot - and the emission is checked by
    driving the real renderer over the real view four times, once per verdict
    assignment, with only the verdict field overridden. The two mixed assignments
    are the ones a swapped flag order cannot survive.
    """
    _header("multi-slot thunker flags follow payload slot order")
    ok = True
    db = _build_db(SIMPLE_IP_PROJECT, 'simple_ip')
    try:
        prj = projectOpen(db)
        blockData = _block_data(prj, MULTI_SLOT_BLOCK)
        ends = _multi_slot_ends(blockData)
        if len(ends) != 1:
            print(f"  FAIL: expected one multi-slot junction in {MULTI_SLOT_BLOCK}, "
                  f"found {len(ends)}; the slot-order coverage has no fixture")
            return False
        thunker = ends[0]['thunker']
        payloads = thunker['payloads']
        pairs = thunker['payloadPairs']
        slots = len(pairs)
        if slots != 2 or len(payloads) != 2 * slots:
            print(f"  FAIL: apb must carry two payload slots on each side, got "
                  f"{slots} pairs over {len(payloads)} payloads")
            return False

        # Pair i joins the parent and child declarations of the SAME protocol slot,
        # held at view positions i and i+N. A pairing swap compares an address
        # declaration against a data declaration, which this catches whatever the
        # verdicts happen to be.
        for index, pair in enumerate(pairs):
            if (pair['parent'] is not payloads[index]
                    or pair['child'] is not payloads[slots + index]):
                ok = False
                print(f"  FAIL: pair {index} is not payloads[{index}] against "
                      f"payloads[{slots + index}]")
            if pair['parent']['structureType'] != pair['child']['structureType']:
                ok = False
                print(f"  FAIL: pair {index} joins protocol slot "
                      f"'{pair['parent']['structureType']}' to "
                      f"'{pair['child']['structureType']}'")
        if len({pair['parent']['structureType'] for pair in pairs}) != slots:
            ok = False
            print("  FAIL: the slots do not carry distinct protocol payloads, so a "
                  "swapped pairing would be undetectable here")

        # Emission: each assignment must reach the member in slot order.
        for assignment, expected in sorted(EXPECTED_MULTI_SLOT.items()):
            for index, verdict in enumerate(assignment):
                pairs[index]['directCopy'] = verdict
            members = [line for line
                       in intf_gen_utils.sc_declare_thunkers(blockData, prj, '', blockData)
                       if line.endswith(f" {MULTI_SLOT_MEMBER};")]
            if members != [expected]:
                ok = False
                print(f"  FAIL: verdicts {assignment} emitted")
                for line in members:
                    print(f"    got:      {line}")
                print(f"    expected: {expected}")
    finally:
        cleanup([db])
    if ok:
        print("  PASS: slot 0 and slot 1 flags track their own payload pair, "
              "including both mixed assignments")
    return ok


def run_all_tests():
    print("=" * 70)
    print("TESTING: C++ definition compatibility at a thunked junction")
    print("=" * 70)
    tests = [
        test_storage_descriptor_matches_emitted_declaration,
        test_cpp_axis_pair_verdicts,
        test_cpp_axis_member_flag_emission,
        test_multi_slot_flag_slot_correspondence,
    ]
    results = []
    for test_func in tests:
        try:
            results.append((test_func.__name__, test_func()))
        except Exception as e:
            print(f"\n  EXCEPTION in {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_func.__name__, False))

    print("\n" + "=" * 70 + "\nTEST SUMMARY\n" + "=" * 70)
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print(f"\n  Passed: {passed}/{len(results)}")
    if passed == len(results):
        print("\n  ALL TESTS PASSED!")
        return 0
    print("\n  SOME TESTS FAILED")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
