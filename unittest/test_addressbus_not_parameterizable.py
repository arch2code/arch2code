#!/usr/bin/env python3
"""A register-bus interface may not carry a parameterizable structure.

Registers and memories may be parameterizable; the bus itself must stay
fixed-width so every router, leaf, and synthesised handler on it shares one
C++ type. `apbReg`'s data structure (`apbDataSt`) references an ipParameters
constant, so `make db` must reject it.
"""

import os
import shutil
import subprocess
import sys
import tempfile

from _addrctl_helpers import base_dir, test_dir


FIXTURE = os.path.join(test_dir, 'fixtures', 'addressbus-parameterizable')

EXPECTED_PATTERNS = [
    'apbReg',
    'apb',
    'address-bus',
    'apbDataSt',
    'fixed-width',
]

ARCH_RELPATH = os.path.join('yaml', 'addrBus.yaml')

# Same interface violation, but with no addressBlock: anywhere in the
# project, so _collectRouterBlocks finds no router. Every block touching the
# parameterizable apbReg interface declares its own params: (cpu, apbDecode,
# leaf) or inherits top's (via inheritContainerParam), so the own-surface
# rule is satisfied and the only remaining error is the address-bus check.
ROUTERLESS_ARCH = """\
ipParameters:
    constants:
        BUS_DATA_WIDTH: { value: 32, maxValue: 64, desc: "Illegal: register-bus data width as a parameter" }

constants:
    ADDR_WIDTH: { value: 32, desc: "Register bus address width" }
    CFG_WIDTH:  { value: 16, desc: "cfg register payload width" }

types:
    apbAddrT: { width: ADDR_WIDTH,     desc: "APB address" }
    apbDataT: { width: BUS_DATA_WIDTH, maxBitwidth: 64, desc: "Parameterizable APB data (illegal on a bus)" }
    cfgT:     { width: CFG_WIDTH,      desc: "cfg register payload" }

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "cfg payload" }

interfaces:
    apbReg:
        desc: "APB register bus with a parameterizable data structure"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }

blocks:
    top_tb:
        desc: "Root testbench container"
        hasMdl: false
        hasTb: false
        hasRtl: false
        hasVl: false
    top:
        desc: "DUT top"
        params: [BUS_DATA_WIDTH]
        hasMdl: true
        hasTb: false
        hasRtl: false
        hasVl: false
    cpu:
        desc: "APB master"
        params: [BUS_DATA_WIDTH]
        hasMdl: true
        hasRtl: false
        hasVl: false
    apbDecode:
        desc: "APB endpoint, no addressBlock: router in this project"
        params: [BUS_DATA_WIDTH]
        hasMdl: true
        hasRtl: false
        hasVl: false
    leaf:
        desc: "Owns the test register, wired directly with no router"
        params: [BUS_DATA_WIDTH]
        hasMdl: true
        hasRtl: false
        hasVl: false

instances:
    top_tb:     { container: top_tb, instanceType: top_tb,   instGroup: top }
    u_top:      { container: top_tb, instanceType: top,      instGroup: top, variant: widthA }
    uCpu:       { container: top,    instanceType: cpu,       instGroup: top, inheritContainerParam: true }
    uApbDecode: { container: top,    instanceType: apbDecode, instGroup: top, inheritContainerParam: true }
    uLeaf:      { container: top,    instanceType: leaf,      instGroup: top, inheritContainerParam: true }

connections:
    - { interface: apbReg, src: uCpu, dst: uApbDecode, name: cpu_main }

registers:
    - { register: cfg, regType: rw, block: leaf, structure: cfgRegSt, desc: "Test register" }

parameters:
    top:
        widthA:
            BUS_DATA_WIDTH: BUS_DATA_WIDTH
"""


def copy_fixture(project):
    shutil.copytree(
        FIXTURE, project,
        ignore=shutil.ignore_patterns('*.db', '*.db-*', '.gen', 'build'))


def env():
    e = os.environ.copy()
    e['NO_COLOR'] = '1'
    return e


def make(target, project, e):
    cmd = ['make', '-C', project, f'REPO_ROOT={project}', f'A2C_ROOT={base_dir}',
           '-j8', target]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=e)


def require_make(target, project, e):
    result = make(target, project, e)
    if result.returncode != 0:
        raise RuntimeError(
            f"make {target} failed:\n{result.stdout}\n{result.stderr}")
    return result


def test_router_present_rejected():
    e = env()
    tmp = tempfile.mkdtemp(prefix='addressbus_parameterizable_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'addrBus')
        copy_fixture(project)

        require_make('clean', project, e)
        result = make('db', project, e)

        full_output = result.stdout + '\n' + result.stderr
        if result.returncode == 0:
            print("FAIL: make db succeeded; an address-bus interface must "
                  "reject a parameterizable structure")
            return False

        if 'Traceback (most recent call last):' in full_output:
            print("FAIL: got a Python stack trace instead of a clean error")
            print(full_output)
            return False

        missing = [p for p in EXPECTED_PATTERNS if p.lower() not in full_output.lower()]
        if missing:
            print(f"FAIL: missing expected patterns: {missing}")
            print(full_output)
            return False

        print("PASS: make db rejects the parameterizable register-bus "
              "interface, naming the interface, its interfaceType, and the "
              "parameterizable structure")
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_router_less_rejected():
    # _validateAddressBusFixedWidth used to run after postProcess's early
    # return for a project with no addressBlock: router, so this same
    # violation passed make db uncaught.
    e = env()
    tmp = tempfile.mkdtemp(prefix='addressbus_parameterizable_norouter_', dir=test_dir)
    try:
        project = os.path.join(tmp, 'addrBus')
        copy_fixture(project)
        with open(os.path.join(project, ARCH_RELPATH), 'w') as f:
            f.write(ROUTERLESS_ARCH)

        require_make('clean', project, e)
        result = make('db', project, e)

        full_output = result.stdout + '\n' + result.stderr
        if result.returncode == 0:
            print("FAIL: make db succeeded for a router-less project; an "
                  "address-bus interface must reject a parameterizable "
                  "structure regardless of whether a router is present")
            return False

        if 'Traceback (most recent call last):' in full_output:
            print("FAIL: got a Python stack trace instead of a clean error")
            print(full_output)
            return False

        missing = [p for p in EXPECTED_PATTERNS if p.lower() not in full_output.lower()]
        if missing:
            print(f"FAIL: missing expected patterns: {missing}")
            print(full_output)
            return False

        print("PASS: make db rejects the parameterizable register-bus "
              "interface in a router-less project too")
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_all_tests():
    results = [test_router_present_rejected(), test_router_less_rejected()]
    return all(results)


if __name__ == '__main__':
    try:
        sys.exit(0 if run_all_tests() else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
