#!/usr/bin/env python3
"""Regression tests for schema-time contextKey source validation."""

import sys
import os

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.schema import Schema

# Disable ANSI colorized warnings/errors in this test to avoid
# color-state spill in aggregated test logs.
g.disableColors = True


def test_valid_context_key_source():
    """A regular key field should make its contextKey resolvable."""
    schema_yaml = {
        "constants": {
            "constant": "key",
            "desc": "required",
            "value": "eval",
            "valueType": "optional(uint)",
        }
    }
    Schema(schema_yaml=schema_yaml, schema_file="test_valid_contextkey.yaml", skip_config=True)
    return True


def test_invalid_context_key_source():
    """A manually declared unresolved contextKey should fail at schema build time."""
    schema_yaml = {
        "bad_section": {
            "item": "key",
            "desc": "required",
            "orphanKey": "contextKey",
        }
    }
    try:
        Schema(schema_yaml=schema_yaml, schema_file="test_invalid_contextkey.yaml", skip_config=True)
    except SystemExit:
        return True
    return False


def test_plain_fk_target_must_be_flat():
    """Plain FK validation requires a flat target section."""
    schema_yaml = {
        "targets": {
            "target": "key",
        },
        "sources": {
            "source": "key",
            "target": {
                "_type": "required",
                "_validate": {
                    "section": "targets",
                    "field": "target",
                },
            },
        },
    }
    try:
        Schema(schema_yaml=schema_yaml, schema_file="test_plain_fk_flat.yaml", skip_config=True)
    except SystemExit:
        return True
    return False


def test_combo_fk_sources_must_match():
    """Combo FK source and target component declarations must match."""
    schema_yaml = {
        "targets": {
            "parent": "required",
            "port": "required",
            "parentPort": {
                "_key": {
                    "parent": "required",
                    "port": "required",
                },
            },
        },
        "sources": {
            "source": "key",
            "parent": "required",
            "otherPort": "required",
            "parentPort": {
                "_type": "required",
                "_combo": {
                    "parent": "required",
                    "otherPort": "required",
                },
                "_validate": {
                    "section": "targets",
                    "field": "parentPort",
                },
            },
        },
    }
    try:
        Schema(schema_yaml=schema_yaml, schema_file="test_combo_fk_match.yaml", skip_config=True)
    except SystemExit:
        return True
    return False


def main():
    print("=" * 70)
    print("TESTING SCHEMA CONTEXTKEY VALIDATION")
    print("=" * 70)

    ok_valid = test_valid_context_key_source()
    print(f"  {'PASS' if ok_valid else 'FAIL'}: valid contextKey source")

    ok_invalid = test_invalid_context_key_source()
    print(f"  {'PASS' if ok_invalid else 'FAIL'}: invalid contextKey source rejected")

    ok_plain_fk_flat = test_plain_fk_target_must_be_flat()
    print(f"  {'PASS' if ok_plain_fk_flat else 'FAIL'}: plain FK target flat check")

    ok_combo_fk_match = test_combo_fk_sources_must_match()
    print(f"  {'PASS' if ok_combo_fk_match else 'FAIL'}: combo FK source match check")

    all_ok = ok_valid and ok_invalid and ok_plain_fk_flat and ok_combo_fk_match
    print(f"\nResult: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
