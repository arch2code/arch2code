#!/usr/bin/env python3
"""Regression tests for schema-time contextKey source validation."""

import sys
import os

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
sys.path.insert(0, base_dir)

from pysrc.schema import Schema


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


def main():
    print("=" * 70)
    print("TESTING SCHEMA CONTEXTKEY VALIDATION")
    print("=" * 70)

    ok_valid = test_valid_context_key_source()
    print(f"  {'PASS' if ok_valid else 'FAIL'}: valid contextKey source")

    ok_invalid = test_invalid_context_key_source()
    print(f"  {'PASS' if ok_invalid else 'FAIL'}: invalid contextKey source rejected")

    all_ok = ok_valid and ok_invalid
    print(f"\nResult: {'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
