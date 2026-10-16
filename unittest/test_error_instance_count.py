#!/usr/bin/env python3
"""An instance that sets `count:` to anything other than 1.

No generator replicates an instance, so `count: 12` would silently produce one
instance. `_post_validateInstanceParameterBinding` (`pysrc/processYaml.py`)
rejects it at `make db`; `count: 1` and an omitted count are accepted.
"""

import sys

from _addrctl_helpers import build_database, cleanup, render_plain_block


def arch_yaml(count_field):
    return (
        "blocks:\n"
        + render_plain_block('top')
        + render_plain_block('leaf')
        + f"""
instances:
    uTop:  {{ container: top, instanceType: top }}
    uLeaf: {{ container: top, instanceType: leaf{count_field} }}
"""
    )


def test_count_other_than_one_rejected():
    print("instance count: 12 is rejected")
    try:
        db_path, project_path, arch_paths, completed = build_database(
            arch_yaml(', count: 12'), expect_success=False)
    except RuntimeError as e:
        print(f"  FAIL: {e}")
        return False
    try:
        combined = completed.stdout + completed.stderr
        needles = ["instance 'uLeaf'", "count: 12", "Instance replication is not supported"]
        missing = [needle for needle in needles if needle not in combined]
        if missing:
            print(f"  FAIL: diagnostic missing {missing}:\n{combined}")
            return False
        print("  PASS")
        return True
    finally:
        cleanup([project_path, db_path] + arch_paths)


def test_count_one_accepted():
    ok = True
    for label, field in (("count: 1", ', count: 1'), ("no count", '')):
        print(f"instance with {label} is accepted")
        try:
            db_path, project_path, arch_paths = build_database(arch_yaml(field))
        except RuntimeError as e:
            print(f"  FAIL: {e}")
            ok = False
            continue
        cleanup([project_path, db_path] + arch_paths)
        print("  PASS")
    return ok


def run_all_tests():
    ok = test_count_other_than_one_rejected()
    ok = test_count_one_accepted() and ok
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
