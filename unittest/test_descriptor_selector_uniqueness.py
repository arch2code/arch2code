#!/usr/bin/env python3
"""The descriptor selectors in pysrc/processYaml.py unpack a single element,
so a producer emitting zero or several matches fails at the selector.

projectOpen._selectDeclaredDescriptor: validateVariantLabelBuildOwnership
rejects a label several projects declare unless the build's own project is
one of them, so the build's own descriptor wins when present and otherwise
the label has exactly one declarer. Both callers pass PROJECTNAME.

projectOpen._instanceVariantDescriptor: resolveInstanceVariantDeclarers
persists one declaring project per labelled instance and
calcVariantConfigDescriptors emits one descriptor per (project, label), so
the (variant, declaringProject) filter lands on one row.

projectCreate.calcRegistrarPairs.selectedDescriptor is a closure; the
example pipelines exercise its single-match path.
"""

import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pysrc import processYaml


def test_selectDeclaredDescriptor_consumer_among_declarers():
    """Two declarers, one the consumer: the consumer's own descriptor wins."""
    descriptors = [
        {'variant': 'v0', 'declaringProject': 'myProj', 'block': 'blk'},
        {'variant': 'v0', 'declaringProject': 'foreign', 'block': 'blk'},
    ]
    selected = processYaml.projectOpen._selectDeclaredDescriptor(None, descriptors, 'myProj')
    assert selected['declaringProject'] == 'myProj', \
        f"expected the consumer's own descriptor, got {selected!r}"
    print("PASS: _selectDeclaredDescriptor picks the consumer's own descriptor")


def test_selectDeclaredDescriptor_single_foreign_declarer():
    """One foreign declarer, consumer absent: that descriptor is returned."""
    descriptors = [{'variant': 'v0', 'declaringProject': 'foreign', 'block': 'blk'}]
    selected = processYaml.projectOpen._selectDeclaredDescriptor(None, descriptors, 'myProj')
    assert selected['declaringProject'] == 'foreign', \
        f"expected the sole foreign descriptor, got {selected!r}"
    print("PASS: _selectDeclaredDescriptor returns the sole foreign descriptor")


def test_selectDeclaredDescriptor_two_foreign_declarers_raises():
    """Two foreign declarers, consumer absent: validateVariantLabelBuildOwnership
    should have rejected this build already, so the selector raises ValueError."""
    descriptors = [
        {'variant': 'v0', 'declaringProject': 'foreignA', 'block': 'blk'},
        {'variant': 'v0', 'declaringProject': 'foreignB', 'block': 'blk'},
    ]
    try:
        processYaml.projectOpen._selectDeclaredDescriptor(None, descriptors, 'myProj')
    except ValueError:
        print("PASS: _selectDeclaredDescriptor raises on two foreign declarers")
        return
    assert False, "two foreign declarers with no consumer descriptor must raise ValueError"


def test_instanceVariantDescriptor_single_match():
    """Exactly one descriptor matches (variant, declaringProject): it is returned."""
    fake = SimpleNamespace(
        instanceVariantDeclarers={'i1': 'pA'},
        variantConfigDescriptors={'blk': [{'variant': 'v0', 'declaringProject': 'pA',
                                            'block': 'blk'}]})
    instanceData = {'instanceKey': 'i1', 'instanceTypeKey': 'blk', 'variant': 'v0'}
    descriptor = processYaml.projectOpen._instanceVariantDescriptor(fake, instanceData)
    assert descriptor['declaringProject'] == 'pA', \
        f"expected the single matching descriptor, got {descriptor!r}"
    print("PASS: _instanceVariantDescriptor returns the single matching descriptor")


def test_instanceVariantDescriptor_no_match_raises():
    """No descriptor matches the declared (variant, declaringProject): ValueError."""
    fake = SimpleNamespace(
        instanceVariantDeclarers={'i1': 'pA'},
        variantConfigDescriptors={'blk': [{'variant': 'v1', 'declaringProject': 'pA',
                                            'block': 'blk'}]})
    instanceData = {'instanceKey': 'i1', 'instanceTypeKey': 'blk', 'variant': 'v0'}
    try:
        processYaml.projectOpen._instanceVariantDescriptor(fake, instanceData)
    except ValueError:
        print("PASS: _instanceVariantDescriptor raises when nothing matches")
        return
    assert False, "no matching descriptor must raise ValueError"


def test_instanceVariantDescriptor_two_matches_raises():
    """Two descriptors both matching (v0, pA): the uniqueness premise is
    violated, so the selector raises ValueError rather than pick one silently."""
    fake = SimpleNamespace(
        instanceVariantDeclarers={'i1': 'pA'},
        variantConfigDescriptors={'blk': [
            {'variant': 'v0', 'declaringProject': 'pA', 'block': 'blk'},
            {'variant': 'v0', 'declaringProject': 'pA', 'block': 'blk'},
        ]})
    instanceData = {'instanceKey': 'i1', 'instanceTypeKey': 'blk', 'variant': 'v0'}
    try:
        processYaml.projectOpen._instanceVariantDescriptor(fake, instanceData)
    except ValueError:
        print("PASS: _instanceVariantDescriptor raises on two matching descriptors")
        return
    assert False, "two matching descriptors must raise ValueError"


def test_instanceVariantDescriptor_no_variant_returns_none():
    """An instance naming no variant short-circuits to None before touching
    either declarer or descriptor lookup."""
    fake = SimpleNamespace(instanceVariantDeclarers={}, variantConfigDescriptors={})
    instanceData = {'instanceKey': 'i1', 'instanceTypeKey': 'blk', 'variant': ''}
    descriptor = processYaml.projectOpen._instanceVariantDescriptor(fake, instanceData)
    assert descriptor is None, f"expected None for an unlabelled instance, got {descriptor!r}"
    print("PASS: _instanceVariantDescriptor returns None when the instance names no variant")


def run_all_tests():
    test_selectDeclaredDescriptor_consumer_among_declarers()
    test_selectDeclaredDescriptor_single_foreign_declarer()
    test_selectDeclaredDescriptor_two_foreign_declarers_raises()
    test_instanceVariantDescriptor_single_match()
    test_instanceVariantDescriptor_no_match_raises()
    test_instanceVariantDescriptor_two_matches_raises()
    test_instanceVariantDescriptor_no_variant_returns_none()
    print("\nALL TESTS PASSED!")


if __name__ == "__main__":
    run_all_tests()
