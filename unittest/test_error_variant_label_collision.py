#!/usr/bin/env python3
"""One variant label declared by two of a block's variant sources is a db error.

A block reached only through `inheritContainerParam` is asked for by label, and
the label belongs to the container supplying its Config. Two containers declaring
the same label leave that label naming two different Configs of the same block,
and the HDL wrapper, the Config selection and the factory registration each
resolve it independently: `getStandaloneVariants` keeps whichever container it
visits last, `getDeclaredVariantConfigs` returns both, and the tandem constructor
emits two `registerBlock` calls under one factory key.
`validateVariantSourceLabelCollision` (`pysrc/processYaml.py`, run right after
`calcVariantSourceBlocks`) rejects the ambiguity instead, naming the leaf, the
label and both declaring containers.

The first rejection uses `vsLeaf` inside `vsContA` and `vsContB`, both declaring
`shared`. The second adds an ordinary `vsLeaf` site whose child-owned variant
also uses `shared`, after renaming the second container's label. This mixed case
proves that child and container sources are both present.

The second phase renames `vsContB`'s label. Two containers with disjoint label
sets is what the shipped `inhVar` and `inhTandem` cells do, so it must stay
legal; without this phase a rule that rejected every multi-container leaf would
look identical here.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'variant-label-two-containers')
ARCH = os.path.join('yaml', 'vsTop.yaml')

# Disjoint label sets, anchored on text the fixture carries verbatim so a fixture
# reword fails here loudly rather than skipping the phase.
DISTINGUISH_LABEL = [
    ("instanceType: vsContB,  instGroup: top, variant: shared }",
     "instanceType: vsContB,  instGroup: top, variant: solo }"),
    ("    vsContB:\n        shared:\n", "    vsContB:\n        solo:\n"),
]

MIXED_COLLISION = DISTINGUISH_LABEL + [
    ("    uLeafB:   { container: vsContB,  instanceType: vsLeaf,   instGroup: top, inheritContainerParam: true }\n",
     "    uLeafB:   { container: vsContB,  instanceType: vsLeaf,   instGroup: top, inheritContainerParam: true }\n"
     "    uLeafOwn: { container: vsTop,    instanceType: vsLeaf,   instGroup: top, variant: shared }\n"),
    ("    vsContB:\n        solo:\n            VS_ALGO: VS_ALGO\n",
     "    vsContB:\n        solo:\n            VS_ALGO: VS_ALGO\n"
     "    vsLeaf:\n        shared:\n            VS_ALGO: 3\n"),
]


def make_db(project):
    """Run `make db` against the temp copy, with both roots overridden."""
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    cmd = ['make', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           'db']
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                            env=env)
    return result.returncode, result.stdout + result.stderr


def edit_arch(project, edits):
    """Apply anchored substitutions to the temp copy's architecture YAML."""
    path = os.path.join(project, ARCH)
    with open(path) as f:
        text = f.read()
    for old, new in edits:
        if old not in text:
            raise RuntimeError(f"fixture no longer carries the anchor {old!r}")
        text = text.replace(old, new)
    with open(path, 'w') as f:
        f.write(text)


def check_rejected(project, source_blocks):
    rc, output = make_db(project)
    if rc == 0:
        print("  FAIL: make db accepted one label declared by two containers")
        print(output)
        return False
    if 'Traceback (most recent call last)' in output:
        print("  FAIL: got a Python stack trace instead of a clean rejection")
        print(output)
        return False
    required = ["Variant 'shared'", "block 'vsLeaf' sources its Config from both",
                *(f"'{block}'" for block in source_blocks)]
    missing = [s for s in required if s not in output]
    if missing:
        print(f"  FAIL: diagnostic missing substrings: {missing}")
        print(output)
        return False
    print("  PASS: the collision is rejected, naming the leaf, the label and "
          f"both sources ({', '.join(source_blocks)})")
    return True


def check_accepted(project):
    edit_arch(project, DISTINGUISH_LABEL)
    rc, output = make_db(project)
    if rc != 0:
        print(f"  FAIL: make db rejected two containers with disjoint labels (rc={rc})")
        print(output)
        return False
    print("  PASS: two containers with disjoint labels are accepted")
    return True


def run_all_tests():
    tmp = tempfile.mkdtemp(prefix='variant_label_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'vsReject')
        shutil.copytree(FIXTURE, project)
        ok = check_rejected(project, ('vsContA', 'vsContB'))
        mixed = os.path.join(tmp, 'vsMixedReject')
        shutil.copytree(FIXTURE, mixed)
        edit_arch(mixed, MIXED_COLLISION)
        ok = check_rejected(mixed, ('vsContA', 'vsLeaf')) and ok
        accept = os.path.join(tmp, 'vsAccept')
        shutil.copytree(FIXTURE, accept)
        ok = check_accepted(accept) and ok
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if ok:
        print("\nPASS: two variant sources may not declare one label")
        return 0
    print("\nFAIL: the variant-label collision rule is wrong")
    return 1


if __name__ == '__main__':
    try:
        sys.exit(run_all_tests())
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
