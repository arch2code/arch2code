#!/usr/bin/env python3
"""Router files written before the template rename keep generating the same RTL.

The router template is regBusDecodeModule. Its earlier key, apbDecodeModule, is
a second entry in the templates map that names the same file, so a router whose
generated region still starts `--template=apbDecodeModule` regenerates without
migration.

The fixture's router is scaffolded by newmodule, which must name the new key,
and generated. The same file with the old key must then regenerate to the same
bytes, and keep them on a second run. A key that is in neither map entry must
still fail generation and leave the file alone.
"""

import os
import shutil
import sys
import tempfile

from test_apb_decode_rtl_empty_slot import generate
from test_memory_firmware_access import _arch2code

NEW_MARKER = '// GENERATED_CODE_BEGIN --template=regBusDecodeModule\n'
OLD_MARKER = '// GENERATED_CODE_BEGIN --template=apbDecodeModule\n'
BAD_MARKER = '// GENERATED_CODE_BEGIN --template=noSuchTemplate\n'


def regenerate(fixture, router):
    return _arch2code('--db', os.path.join(fixture, 'emptySlot.db'), '-r', '--systemVerilog',
                      '--file', router, cwd=fixture)


def read(path):
    with open(path) as f:
        return f.read()


def write(path, text):
    with open(path, 'w') as f:
        f.write(text)


def check_alias(fixture):
    router = os.path.join(fixture, 'rtl', 'apbDecode.sv')
    scaffolded = read(router)
    if NEW_MARKER not in scaffolded or 'apbDecodeModule' in scaffolded:
        raise AssertionError(f"newmodule did not scaffold the router with {NEW_MARKER.strip()}:\n{scaffolded}")
    if 'module apbDecode' not in scaffolded or 'endmodule' not in scaffolded:
        raise AssertionError(f"the regBusDecodeModule key generated no router body:\n{scaffolded}")

    expected = scaffolded.replace(NEW_MARKER, OLD_MARKER)
    write(router, expected)
    for attempt in ('first', 'second'):
        run = regenerate(fixture, router)
        if run.returncode != 0:
            raise AssertionError(f"{attempt} apbDecodeModule regeneration failed:\n{run.stdout}\n{run.stderr}")
        if read(router) != expected:
            raise AssertionError(f"{attempt} apbDecodeModule regeneration changed the router:\n{read(router)}")

    unknown = scaffolded.replace(NEW_MARKER, BAD_MARKER)
    write(router, unknown)
    run = regenerate(fixture, router)
    if run.returncode == 0 or 'Template noSuchTemplate does not exist in project configuration' not in run.stdout + run.stderr:
        raise AssertionError(f"an unknown template key did not fail (exit {run.returncode}):\n{run.stdout}\n{run.stderr}")
    if read(router) != unknown:
        raise AssertionError("a failed generation rewrote the router file")


def main():
    fixture = tempfile.mkdtemp(prefix='a2c_decode_alias_')
    try:
        generate(fixture)
        check_alias(fixture)
    except Exception as exc:
        print(f"FAIL: apbDecodeModule router files regenerate as regBusDecodeModule: {exc}")
        return 1
    finally:
        shutil.rmtree(fixture, ignore_errors=True)
    print("PASS: apbDecodeModule router files regenerate as regBusDecodeModule")
    return 0


if __name__ == '__main__':
    sys.exit(main())
