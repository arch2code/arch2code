#!/usr/bin/env python3
"""The descriptor selector in pysrc/processYaml.py unpacks a single element,
so a producer emitting zero or several matches fails at the selector.

projectOpen.instanceVariantDescriptor: resolveInstanceVariantDeclarers
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


def test_instanceVariantDescriptor_single_match():
    """Exactly one descriptor matches (variant, declaringProject): it is returned."""
    fake = SimpleNamespace(
        instanceVariantDeclarers={'i1': 'pA'},
        variantConfigDescriptors={'blk': [{'variant': 'v0', 'declaringProject': 'pA',
                                            'block': 'blk'}]})
    instanceData = {'instanceKey': 'i1', 'instanceTypeKey': 'blk', 'variant': 'v0'}
    descriptor = processYaml.projectOpen.instanceVariantDescriptor(fake, instanceData)
    assert descriptor['declaringProject'] == 'pA', \
        f"expected the single matching descriptor, got {descriptor!r}"
    print("PASS: instanceVariantDescriptor returns the single matching descriptor")


def test_instanceVariantDescriptor_no_match_raises():
    """No descriptor matches the declared (variant, declaringProject): ValueError."""
    fake = SimpleNamespace(
        instanceVariantDeclarers={'i1': 'pA'},
        variantConfigDescriptors={'blk': [{'variant': 'v1', 'declaringProject': 'pA',
                                            'block': 'blk'}]})
    instanceData = {'instanceKey': 'i1', 'instanceTypeKey': 'blk', 'variant': 'v0'}
    try:
        processYaml.projectOpen.instanceVariantDescriptor(fake, instanceData)
    except ValueError:
        print("PASS: instanceVariantDescriptor raises when nothing matches")
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
        processYaml.projectOpen.instanceVariantDescriptor(fake, instanceData)
    except ValueError:
        print("PASS: instanceVariantDescriptor raises on two matching descriptors")
        return
    assert False, "two matching descriptors must raise ValueError"


def test_instanceVariantDescriptor_no_variant_returns_none():
    """An instance naming no variant short-circuits to None before touching
    either declarer or descriptor lookup."""
    fake = SimpleNamespace(instanceVariantDeclarers={}, variantConfigDescriptors={})
    instanceData = {'instanceKey': 'i1', 'instanceTypeKey': 'blk', 'variant': ''}
    descriptor = processYaml.projectOpen.instanceVariantDescriptor(fake, instanceData)
    assert descriptor is None, f"expected None for an unlabelled instance, got {descriptor!r}"
    print("PASS: instanceVariantDescriptor returns None when the instance names no variant")


def run_all_tests():
    test_instanceVariantDescriptor_single_match()
    test_instanceVariantDescriptor_no_match_raises()
    test_instanceVariantDescriptor_two_matches_raises()
    test_instanceVariantDescriptor_no_variant_returns_none()
    print("\nALL TESTS PASSED!")


if __name__ == "__main__":
    run_all_tests()
