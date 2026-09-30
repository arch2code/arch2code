#!/usr/bin/env python3
"""A `generator: datapath` member makes a structure's emitted storage undecidable.

`projectOpen.structureStorageSignature()` describes the storage an emitted member
occupies, and `buildThunkerView` judges a payload pair eligible for a direct copy
when the two descriptors compare equal. The descriptor is computed from the
DECLARED type of every member.

That is unsound for a `generator: datapath` member. `genSystemC.calcStructure`
rewrites such a member to `uint8_t *` before it is emitted, so the declared type
describes nothing that reaches the C++ definition. Two payloads whose declared
types are storage-equal would compare equal and be judged eligible, while the
members actually emitted are pointers - so the copy would transfer one object's
backdoor pointer into the other, and the call site's `sizeof` static_assert would
not catch it because the sizes agree.

The descriptor therefore reports `None` - "not statically decidable" - for any
structure carrying such a member, which makes every comparison against it refuse
the pair and fall back to pack/unpack. This is the same treatment a parameterizable
array extent already gets, on the same reasoning: the emitted storage is a property
of something other than the declaration.

Three things are pinned here:

- The verdict, on a flat `NamedType` datapath member and on one buried inside a
  `subStruct:`, where the undecidability has to propagate out of the recursion.
- Positive controls carrying no datapath member but otherwise the same shape, so
  a fixture that stopped being eligible for an unrelated reason fails here rather
  than passing vacuously. The controls are what makes the datapath rows evidence.
- The emitter agreement the `None` rests on: `calcStructure` really does rewrite
  the member to `uint8_t *`. If that rewrite is ever retired, this is the test
  that says the `None` has become unnecessary.
"""

import os
import sys

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.systemcGen import genSystemC

from _addrctl_helpers import build_database, cleanup, projectOpen


# Every structure below is non-parameterizable and every member is a plain
# `NamedType` or a `subStruct:`, so nothing but the datapath member can make a
# descriptor undecidable. The A/B declarations of each pair are deliberately
# distinct - different member NAMES over identical member STORAGE - because that
# is the only shape a thunked junction ever presents.
ARCH_YAML = """constants:
    PAYLOAD_WIDTH: { value: 64, desc: "Payload width" }
    TAG_WIDTH:     { value: 8,  desc: "Tag width" }
    BD_WIDTH:      { value: 32, desc: "Declared backdoor width" }

types:
    payloadT: { width: PAYLOAD_WIDTH, desc: "Payload" }
    tagT:     { width: TAG_WIDTH,     desc: "Tag" }
    bdT:      { width: BD_WIDTH,      desc: "Backdoor handle as declared" }

structures:
    # Control: two distinct declarations over identical storage. These MUST be
    # judged eligible, which is what makes the datapath rows below evidence -
    # they are these same declarations with one datapath member added.
    plainASt:
        data: { varType: payloadT, desc: "Payload" }
        tag:  { varType: tagT,     desc: "Tag" }
    plainBSt:
        payload: { varType: payloadT, desc: "Payload" }
        marker:  { varType: tagT,     desc: "Tag" }

    # Flat NamedType datapath member. The declared types still correspond member
    # for member, so a descriptor computed from declared types alone compares
    # these equal and judges them eligible while both emit `uint8_t * bd;`.
    flatDpASt:
        bd:   { varType: bdT,     generator: datapath, desc: "Datapath backdoor" }
        data: { varType: payloadT, desc: "Payload" }
        tag:  { varType: tagT,     desc: "Tag" }
    flatDpBSt:
        bd:      { varType: bdT,      generator: datapath, desc: "Datapath backdoor" }
        payload: { varType: payloadT, desc: "Payload" }
        marker:  { varType: tagT,     desc: "Tag" }

    # Nesting control: the same nesting shape with no datapath member anywhere.
    cleanHdrSt:
        data: { varType: payloadT, desc: "Payload" }
    nestCleanASt:
        hdr: { subStruct: cleanHdrSt, desc: "Header" }
        tag: { varType: tagT,         desc: "Tag" }
    nestCleanBSt:
        header: { subStruct: cleanHdrSt, desc: "Header" }
        marker: { varType: tagT,         desc: "Tag" }

    # Datapath member one level down. The enclosing structure declares no
    # datapath member of its own, so only propagation out of the recursion can
    # make it undecidable.
    dpHdrSt:
        bd:   { varType: bdT,      generator: datapath, desc: "Datapath backdoor" }
        data: { varType: payloadT, desc: "Payload" }
    nestDpASt:
        hdr: { subStruct: dpHdrSt, desc: "Header" }
        tag: { varType: tagT,      desc: "Tag" }
    nestDpBSt:
        header: { subStruct: dpHdrSt, desc: "Header" }
        marker: { varType: tagT,      desc: "Tag" }

blocks:
    top:
        desc: "Top container"
        hasMdl: true

instances:
    uTop: { container: top, instanceType: top }
"""

# The emitted spelling `calcStructure` rewrites a datapath member to.
DATAPATH_EMITTED_TYPE = 'uint8_t *'


def _header(name):
    print("\n" + "=" * 70)
    print(f"Test: {name}")
    print("=" * 70)


def _structure_key(prj, name):
    return next(key for key, row in prj.data['structures'].items()
                if row['structure'] == name)


def _direct_copy(prj, nameA, nameB):
    """The eligibility predicate exactly as `buildThunkerView` spells it."""
    signature = prj.structureStorageSignature(_structure_key(prj, nameA))
    return (signature is not None
            and signature == prj.structureStorageSignature(
                _structure_key(prj, nameB)))


def _signature(prj, name):
    return prj.structureStorageSignature(_structure_key(prj, name))


def test_datapath_member_makes_storage_undecidable():
    """Flat and nested datapath members both refuse the pair; controls do not."""
    _header("a datapath member makes a structure's emitted storage undecidable")
    ok = True
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    try:
        prj = projectOpen(db_path)

        # Controls first. If either of these is not eligible the fixture has
        # stopped exercising the property and the rows below prove nothing.
        for nameA, nameB, label in (
                ('plainASt', 'plainBSt', 'flat'),
                ('nestCleanASt', 'nestCleanBSt', 'nested')):
            if not _direct_copy(prj, nameA, nameB):
                ok = False
                print(f"  FAIL: control {nameA}/{nameB} ({label}) is not eligible, "
                      f"so the datapath rows below are vacuous")

        # The member-level detection, on the structure that declares it.
        for name in ('flatDpASt', 'flatDpBSt', 'dpHdrSt'):
            if _signature(prj, name) is not None:
                ok = False
                print(f"  FAIL: {name} declares a datapath member but its "
                      f"descriptor is {_signature(prj, name)!r}, not None")

        # Propagation out of the recursion: neither enclosing structure declares
        # a datapath member of its own.
        for name in ('nestDpASt', 'nestDpBSt'):
            if _signature(prj, name) is not None:
                ok = False
                print(f"  FAIL: {name} nests a datapath member but its "
                      f"descriptor is {_signature(prj, name)!r}, not None")

        # The verdicts the adapter actually consumes.
        for nameA, nameB, label in (
                ('flatDpASt', 'flatDpBSt', 'flat NamedType datapath member'),
                ('nestDpASt', 'nestDpBSt', 'datapath member inside a subStruct')):
            if _direct_copy(prj, nameA, nameB):
                ok = False
                print(f"  FAIL: {nameA}/{nameB} ({label}) judged eligible for a "
                      f"direct copy; the emitted members are pointers")
    finally:
        cleanup([project_path, db_path] + arch_paths)
    if ok:
        print("  PASS: both datapath shapes refuse the pair; both controls "
              "remain eligible")
    return ok


def test_datapath_member_is_emitted_as_a_pointer():
    """The rewrite the `None` verdict rests on: the member becomes `uint8_t *`.

    The descriptor is only unsound for a datapath member because `calcStructure`
    replaces the declared type before emission. This pins that rewrite, so if it
    is ever retired the reason for the `None` is known to have gone with it.
    """
    _header("calcStructure rewrites a datapath member to a pointer")
    ok = True
    db_path, project_path, arch_paths = build_database(ARCH_YAML)
    try:
        prj = projectOpen(db_path)
        # calcStructure reads only the class-level dataTypeMappings, so the class
        # stands in for an instance; constructing one requires a file to render.
        seen = dict()
        for context in prj.yamlContext:
            if context.startswith('_'):
                # Framework contexts carry no user structures.
                continue
            data = prj.getContextData([context], genSystemC.dataTypeMappings)
            genSystemC.calcStructure(genSystemC, data, prj)
            for structData in data['structures'].values():
                if 'bd' in structData['vars']:
                    seen[structData['structure']] = \
                        structData['vars']['bd']['varType']

        for name in ('flatDpASt', 'flatDpBSt', 'dpHdrSt'):
            if name not in seen:
                ok = False
                print(f"  FAIL: {name} was not rendered into any context, so the "
                      f"rewrite is unpinned")
            elif seen[name] != DATAPATH_EMITTED_TYPE:
                ok = False
                print(f"  FAIL: {name}'s datapath member emits "
                      f"'{seen[name]}', expected '{DATAPATH_EMITTED_TYPE}'")
    finally:
        cleanup([project_path, db_path] + arch_paths)
    if ok:
        print(f"  PASS: every datapath member emits '{DATAPATH_EMITTED_TYPE}', "
              f"not its declared type")
    return ok


def run_all_tests():
    print("=" * 70)
    print("TESTING: datapath members and emitted-storage decidability")
    print("=" * 70)
    tests = [
        test_datapath_member_makes_storage_undecidable,
        test_datapath_member_is_emitted_as_a_pointer,
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
