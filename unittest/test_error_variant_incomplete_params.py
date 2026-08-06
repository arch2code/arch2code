#!/usr/bin/env python3
"""A variant that omits a declared block parameter is a database-time error.

The nested variant schema requires every variant to bind ALL of its block's
declared parameters; there is no default-fill for an omitted parameter. The
completeness check is a variant-row `_post` hook
(`_post_validateVariantParameterCompleteness`, `pysrc/processYaml.py`, attached
to `parametersvariants` in `config/schema.yaml`): it fires once per declared
variant row in the row's own file scope, so it checks every declared variant,
including one that is never instanced (a library variant staged for later use),
which the instance-scoped postParseChecks pass does not reach.

This fixture declares block `ip` with two params (WIDTH, DEPTH). Variant
`vGood` binds both and is instanced (so the instance-scoped check passes);
variant `vBad` binds only WIDTH and is never instanced. The completeness
validator must fail the build and name the block, the variant, and the missing
parameter.
"""

import os
import subprocess
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)


def _write_temp(content, suffix, prefix):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=test_dir)
    os.close(fd)
    with open(path, 'w') as f:
        f.write(content)
    return path


def _cleanup(paths):
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass


# Block `ip` declares WIDTH and DEPTH. vGood binds both (instanced); vBad binds
# only WIDTH and is never instanced. DEPTH omitted on vBad must be rejected.
ARCH_YAML = """ipParameters:
  constants:
    WIDTH: {value: 8, maxValue: 32, desc: "block width param"}
    DEPTH: {value: 4, maxValue: 16, desc: "block depth param"}

blocks:
  ip:
    desc: "Parameterized block with two params"
    params: [WIDTH, DEPTH]
  top:
    desc: "Top block"

instances:
  uTop: { container: top, instanceType: top }
  uIp:  { container: top, instanceType: ip, variant: vGood }

parameters:
  ip:
    vGood:
      WIDTH: 8
      DEPTH: 4
    vBad:
      WIDTH: 8
"""


REQUIRED_SUBSTRINGS = [
    "Variant 'vBad'",
    "block 'ip'",
    "missing required parameter(s): DEPTH",
    "there is no default for an omitted parameter",
]


def _run():
    print("incomplete variant (omitted block parameter) is a db-time error")
    arch_path = _write_temp(ARCH_YAML, '.yaml', 'variant_incomplete_arch_')
    project_yaml = f"""projectName: variant_incomplete_test
yamlFormat: 2
topInstance: uTop

dirs:
  root: ..

projectFiles:
  - {os.path.basename(arch_path)}
"""
    project_path = _write_temp(
        project_yaml, '_project.yaml', 'variant_incomplete_project_')
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        cmd = [sys.executable, os.path.join(base_dir, 'arch2code.py'),
               '--yaml', project_path, '--db', db_path]
        result = subprocess.run(cmd, capture_output=True, text=True,
                                cwd=test_dir, env=env)
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            print("  FAIL: expected error but build succeeded")
            return False
        if 'Traceback (most recent call last)' in combined:
            print("  FAIL: got Python stack trace instead of clean error")
            print(combined)
            return False
        missing = [s for s in REQUIRED_SUBSTRINGS if s not in combined]
        if missing:
            print(f"  FAIL: diagnostic missing substrings: {missing}")
            print(combined)
            return False
        print("  PASS: got expected completeness error")
        return True
    finally:
        _cleanup([project_path, arch_path, db_path])


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
