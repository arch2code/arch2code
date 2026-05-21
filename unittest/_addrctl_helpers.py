"""Shared fixtures for `addressControl` refactor unit tests.

Each consumer assembles a small YAML topology that exercises the new
`addressBlock:` / `registerPorts:` post-parse path
(`config/postParseRegisterPorts.py`), runs `arch2code.py` to populate a
temporary SQLite database, and asserts on `projectOpen` view-data rows.

The helpers here cover the boilerplate shared by every fixture: temp
project / arch file emission, `arch2code.py` invocation, success /
failure capture, and post-parse-row lookup. Test bodies own the
topology YAML and the assertions.
"""

import os
import subprocess
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from pysrc.processYaml import projectOpen


# Canonical APB register-bus interface declaration reused across fixtures.
# Declares the address / data structure pair the APB interface_def
# expects, plus a placeholder register-payload structure.
APB_PREAMBLE = """constants:
    ADDR_WIDTH: { value: 32, desc: "Register bus address width" }
    DATA_WIDTH: { value: 32, desc: "Register bus data width" }
    REG_WIDTH:  { value: 16, desc: "Register payload width" }

types:
    apbAddrT: { width: ADDR_WIDTH, desc: "APB address" }
    apbDataT: { width: DATA_WIDTH, desc: "APB data" }
    cfgT:     { width: REG_WIDTH,  desc: "Register payload" }

structures:
    apbAddrSt:
        address: { varType: apbAddrT, generator: address }
    apbDataSt:
        data: { varType: apbDataT, generator: data }
    cfgRegSt:
        value: { varType: cfgT, generator: register, desc: "Register payload" }

interfaces:
    apbReg:
        desc: "APB register bus"
        interfaceType: apb
        structures:
            - { structure: apbAddrSt, structureType: addr_t }
            - { structure: apbDataSt, structureType: data_t }
"""


def write_temp(content, suffix, prefix):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=test_dir)
    os.close(fd)
    with open(path, 'w') as f:
        f.write(content)
    return path


def make_project(arch_files, top_instance='uTop', project_name='addrctl_test'):
    """Write a temporary project.yaml plus one or more arch YAML files.

    arch_files: list of (filename_hint, content) tuples. The first entry
    is the project's top-level architecture YAML; the rest are siblings
    available for `include:` directives. Returns
    (project_path, [arch_path...]).
    """
    arch_paths = []
    for hint, content in arch_files:
        arch_paths.append(write_temp(content, suffix='.yaml',
                                     prefix=f"addrctl_{hint}_"))

    project_files_section = ''.join(
        f"    - {os.path.basename(p)}\n" for p in arch_paths
    )
    project_content = (
        f"projectName: {project_name}\n"
        f"topInstance: {top_instance}\n"
        f"\n"
        f"dirs:\n"
        f"    root: ..\n"
        f"\n"
        f"instanceGroups:\n"
        f"    top:\n"
        f"        varType: inst_top\n"
        f"        enumPrefix: INST_TOP_\n"
        f"\n"
        f"addressObjects:\n"
        f"    memories:\n"
        f"        alignment: memsize\n"
        f"        sizeRoundUpPowerOf2: true\n"
        f"        sortDescending: true\n"
        f"    registers:\n"
        f"        alignment: 8\n"
        f"        sortDescending: true\n"
        f"\n"
        f"projectFiles:\n"
        f"{project_files_section}"
    )
    project_path = write_temp(project_content, suffix='_project.yaml',
                              prefix='addrctl_proj_')
    return project_path, arch_paths


def run_arch2code(project_path, db_path, timeout=30):
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    return subprocess.run(
        [sys.executable, os.path.join(base_dir, 'arch2code.py'),
         '--yaml', project_path, '--db', db_path],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=base_dir,
        env=env,
    )


def build_database(arch_yaml, top_instance='uTop',
                   extra_files=None, expect_success=True,
                   project_name='addrctl_test'):
    """Compile `arch_yaml` into a fresh SQLite database.

    arch_yaml: string contents of the project's top-level arch YAML.
    extra_files: optional list of (filename_hint, content) tuples for
    additional yaml files (`include:` targets, leaf-scope yamls, etc.).
    Returns (db_path, project_path, arch_paths) on success, or
    (db_path, project_path, arch_paths, completed_process) when
    expect_success=False and the build is expected to fail.
    """
    arch_files = [('arch', arch_yaml)]
    if extra_files:
        arch_files.extend(extra_files)
    project_path, arch_paths = make_project(
        arch_files, top_instance=top_instance, project_name=project_name)
    db_path = tempfile.mktemp(suffix='.db', dir=test_dir)
    try:
        result = run_arch2code(project_path, db_path)
        if expect_success and result.returncode != 0:
            raise RuntimeError(
                f"arch2code.py failed unexpectedly:\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        if (not expect_success) and result.returncode == 0:
            raise RuntimeError(
                f"arch2code.py succeeded unexpectedly:\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        if expect_success:
            return db_path, project_path, arch_paths
        return db_path, project_path, arch_paths, result
    except Exception:
        cleanup([project_path, db_path] + arch_paths)
        raise


def cleanup(paths):
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.unlink(path)
            except OSError:
                pass


def find_block(prj, simple_name):
    """Return (blockKey, blockRow) for the block whose simple name matches."""
    for blockKey, row in prj.data['blocks'].items():
        if isinstance(row, dict) and row.get('block') == simple_name:
            return blockKey, row
    raise AssertionError(
        f"No block with simple name '{simple_name}' found")


def find_instance(prj, simple_name):
    """Return (instanceKey, instRow) for the instance with the given simple name."""
    for instKey, row in prj.data['instances'].items():
        if isinstance(row, dict) and row.get('instance') == simple_name:
            return instKey, row
    raise AssertionError(
        f"No instance with simple name '{simple_name}' found")


def iter_rows(prj, section):
    """Yield (key, row) for each row of a section table after projectOpen
    flattening. `prj.data[section]` is flat-keyed at view time, keyed by
    `<simple>/<context>` strings; rows expose `_context`."""
    for key, row in prj.data.get(section, {}).items():
        if isinstance(row, dict):
            yield key, row


def assert_no_global_register_binds(prj):
    """Stage 7 invariant: synthesised register-bus rows never carry
    `_context: '_global'`. Asserts on connections and connectionMaps
    whose interface resolves to an addressBus: true interface_def, since
    those are the rows the post-parse pass authors."""
    addressBusTypes = set()
    for row in prj.data.get('interface_defs', {}).values():
        if isinstance(row, dict) and row.get('addressBus'):
            addressBusTypes.add(row.get('interface_type'))

    def _ifaceType(intf_name):
        for ifaceRow in prj.data.get('interfaces', {}).values():
            if ifaceRow.get('interface') == intf_name:
                return ifaceRow.get('interfaceType')
        return None

    offenders = []
    for section in ('connections', 'connectionMaps'):
        for _key, row in iter_rows(prj, section):
            intf = row.get('interface')
            if intf and _ifaceType(intf) in addressBusTypes:
                if row.get('_context') == '_global':
                    offenders.append((section, intf, row))
    assert not offenders, (
        f"Register-bus rows tagged with _context '_global': {offenders}"
    )


def find_connections(prj, src=None, dst=None, interface=None):
    """Return connection rows matching any provided simple-name filters."""
    out = []
    for _key, row in iter_rows(prj, 'connections'):
        if src is not None and row.get('src') != src:
            continue
        if dst is not None and row.get('dst') != dst:
            continue
        if interface is not None and row.get('interface') != interface:
            continue
        out.append(row)
    return out


def find_connection_maps(prj, instance=None, port=None, interface=None):
    out = []
    for _key, row in iter_rows(prj, 'connectionMaps'):
        if instance is not None and row.get('instance') != instance:
            continue
        if port is not None and row.get('port') != port:
            continue
        if interface is not None and row.get('interface') != interface:
            continue
        out.append(row)
    return out


def render_router(block_name, address_group, *,
                  upstream_port='apbReg', register_decoder_port='apbReg',
                  enum_prefix=None, var_type=None,
                  address_increment='0x01000000', max_address_spaces=16,
                  extra_block_lines=''):
    """Emit a YAML snippet declaring a router block with the new schema."""
    enum_prefix = enum_prefix or f"ADDR_ID_{address_group.upper()}_"
    var_type = var_type or f"addr_id_{address_group}"
    return f"""    {block_name}:
        desc: "Router block '{block_name}'"
        hasMdl: true
{extra_block_lines}        addressBlock:
            addressGroup: {address_group}
            addressIncrement: {address_increment}
            maxAddressSpaces: {max_address_spaces}
            varType: {var_type}
            enumPrefix: {enum_prefix}
            upstreamPort: {upstream_port}
            registerDecoderPort: {register_decoder_port}
"""


def render_leaf(block_name, *, port_name='regs',
                interface='apbReg', extra_block_lines=''):
    """Emit a YAML snippet declaring a routed leaf block."""
    return f"""    {block_name}:
        desc: "Routed leaf block '{block_name}'"
        hasMdl: true
{extra_block_lines}        registerPorts:
            {port_name}: {{ interface: {interface} }}
"""


def render_plain_block(block_name, extra_block_lines=''):
    """Emit a non-router, non-leaf block declaration."""
    return f"""    {block_name}:
        desc: "Plain block '{block_name}'"
        hasMdl: true
{extra_block_lines}"""
