#!/usr/bin/env python3
"""Every committed example's SV modules and packages are named by their files.

Runs pysrc/checkSvNames.py over each directory under examples/. A generated
design unit takes its file's stem, so a mismatch is a template or naming-map
fault; a user endmodule label that names no unit in its file was left stale by
a rename that `make migrate` should have relabelled.
"""

import os
import sys

from _addrctl_helpers import base_dir

sys.path.insert(0, base_dir)
from pysrc import checkSvNames  # noqa: E402


def main():
    examples = os.path.join(base_dir, 'examples')
    failed = False
    total = 0
    for name in sorted(os.listdir(examples)):
        directory = os.path.join(examples, name)
        if not os.path.isdir(directory):
            continue
        checked, _, mismatches = checkSvNames.checkProject(directory)
        total += checked
        for line in mismatches:
            print(f"FAIL: examples/{name}/{line}")
            failed = True
    if total == 0:
        print("FAIL: no SV file found under examples/")
        failed = True
    if failed:
        print("SOME TESTS FAILED: an SV module or package is not named by its file stem, "
              "or an end label names no unit in its file")
        return 1
    print(f"PASS: {total} SV files under examples/ declare the unit their file stem names")
    print("ALL TESTS PASSED")
    return 0


if __name__ == '__main__':
    sys.exit(main())
