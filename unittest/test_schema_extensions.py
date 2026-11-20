#!/usr/bin/env python3
"""Coverage for `schemaExtensions:`: fragment paths, rows read back through
projectOpen, the build manifest, and the errors Schema() and projectCreate
report for a bad fragment."""

import contextlib
import io
import os
import subprocess
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.merge_utils import merge_with_spec
from pysrc.processYaml import projectCreate, projectOpen

g.disableColors = True

BASE_SCHEMA_PATH = os.path.join(base_dir, 'config', 'schema.yaml')

TOP_SECTION_EXT = """fwNotes:
  _attribs: [flat]
  note: key
  text: required
"""

BLOCKS_SUBTABLE_EXT = """blocks:
  fwQueues:
    _attribs: [optional, multiple]
    queue: key
    depth: required
"""

# Two levels down: a sub-table under the base blocks.clocks sub-table.
CLOCKS_SUBTABLE_EXT = """blocks:
  clocks:
    fwTags:
      _attribs: [optional, multiple]
      tag: key
      weight: required
"""

# Extends the section TOP_SECTION_EXT adds, so it must be listed after it.
TOP_SECTION_FIELD_EXT = """fwNotes:
  owner: optional(nobody)
"""

ARCH_YAML = """blocks:
  qBlock:
    desc: "block carrying firmware queues"
    clocks:
      clk:
        fwTags:
          t0: {weight: 3}
    fwQueues:
      cmdQ: {depth: 8}
      rspQ: {depth: 4}

fwNotes:
  hello: {text: "a note", owner: fw}

customSection:
  one: {extra: yes}
"""

# The round-trip project's dbSchema: is the base schema plus this section,
# which CUSTOM_SECTION_EXT extends.
CUSTOM_SCHEMA_SECTION = """
customSection:
  _attribs: [flat]
  item: key
"""

CUSTOM_SECTION_EXT = """customSection:
  extra: optional
"""


def _write(tmp_dir, name, content):
    path = os.path.join(tmp_dir, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)
    return path


def _project(tmp_dir, project_name, extensions, arch_yaml=None, extra=''):
    """Write the fragments, an optional arch file and the project file into
    tmp_dir. extensions is a list of (project.yaml entry, file path relative to
    tmp_dir or None, text); a None path writes nothing. Returns (project, db,
    fragment paths)."""
    ext_paths = [_write(tmp_dir, path, text) if path else None for _, path, text in extensions]
    lines = [f"projectName: {project_name}", "yamlFormat: 2", "", "dirs:", "  root: .", "",
             "schemaExtensions:"]
    lines += [f"  - {entry}" for entry, _, _ in extensions]
    if arch_yaml is not None:
        _write(tmp_dir, 'arch.yaml', arch_yaml)
        lines += ["", "projectFiles:", "  - arch.yaml"]
    project_path = _write(tmp_dir, 'project.yaml', '\n'.join(lines) + '\n' + extra)
    return project_path, os.path.join(tmp_dir, 'ext.db'), ext_paths


def _local(path, text):
    """An extension entry written relative to the project file."""
    return (path, path, text)


def _release_db():
    if g.db is not None:
        g.db.close()
    g.db = None
    g.cur = None


def _run_case(label, fn):
    try:
        ok = fn()
    except Exception as exc:
        print(f"FAIL: {label}: {exc!r}")
        return False
    print(f"{'PASS' if ok else 'FAIL'}: {label}")
    return ok


def _build_fails(project_name, extensions):
    """Build a project that must stop before parsing. Returns (stopped,
    output, fragment paths)."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp_dir:
        project_path, db_path, ext_paths = _project(tmp_dir, project_name, extensions)
        buf = io.StringIO()
        stopped = False
        try:
            with contextlib.redirect_stdout(buf):
                projectCreate(project_path, db_path)
        except SystemExit:
            stopped = True
        finally:
            _release_db()
            os.chdir(original_cwd)
        return stopped, buf.getvalue(), ext_paths


def _build_open(tmp_dir, project_name, extensions, arch_yaml, extra=''):
    """Build a project that must succeed and open it with projectOpen."""
    project_path, db_path, ext_paths = _project(tmp_dir, project_name, extensions, arch_yaml, extra)
    projectCreate(project_path, db_path)
    _release_db()
    return projectOpen(db_path), ext_paths


def _manifest_lists(prj, tmp_dir, paths):
    manifest_yaml = prj.config.getConfig('BUILDMANIFEST')['yamlFiles']
    with open(os.path.join(tmp_dir, '.gen', 'build.mk')) as f:
        yaml_line = next(line for line in f if line.startswith('A2C_YAML_FILES'))
    return all(p in manifest_yaml and p in yaml_line.split() for p in paths)


def _line_of(text, key):
    """1-based line of the first line of text that starts with key."""
    return next(i for i, line in enumerate(text.splitlines(), 1) if line.lstrip().startswith(key))


def test_extension_tables_round_trip():
    """Fragment tables load through projectOpen like base tables, and the
    fragments are in the build manifest. The fragments are listed as a
    relative path, an absolute path and a $root path, and merge onto a
    project dbSchema:."""
    original_cwd = os.getcwd()
    results = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        abs_path = os.path.join(tmp_dir, 'schema', 'blocksSubtable.yaml')
        with open(BASE_SCHEMA_PATH) as f:
            _write(tmp_dir, 'mySchema.yaml', f.read() + CUSTOM_SCHEMA_SECTION)
        try:
            prj, ext_paths = _build_open(
                tmp_dir, 'schema_ext_test',
                [_local('schema/topSection.yaml', TOP_SECTION_EXT),
                 (abs_path, 'schema/blocksSubtable.yaml', BLOCKS_SUBTABLE_EXT),
                 ('$root/schema/clocksSubtable.yaml', 'schema/clocksSubtable.yaml', CLOCKS_SUBTABLE_EXT),
                 _local('schema/topSectionField.yaml', TOP_SECTION_FIELD_EXT),
                 _local('schema/customSection.yaml', CUSTOM_SECTION_EXT)],
                ARCH_YAML, extra='dbSchema: mySchema.yaml\n')

            def top_section_rows():
                notes = prj.data['fwNotes']
                return list(notes) == ['hello/arch.yaml'] \
                    and notes['hello/arch.yaml']['text'] == 'a note'

            def field_on_earlier_extension():
                return prj.data['fwNotes']['hello/arch.yaml']['owner'] == 'fw'

            def blocks_subtable_rows():
                queues = prj.data['blocks']['qBlock/arch.yaml']['fwQueues']
                return {q: row['depth'] for q, row in queues.items()} == {'cmdQ': 8, 'rspQ': 4}

            def two_levels_down_rows():
                tags = prj.data['blocks']['qBlock/arch.yaml']['clocks']['clk']['fwTags']
                return {t: row['weight'] for t, row in tags.items()} == {'t0': 3}

            def custom_db_schema_rows():
                return prj.data['customSection']['one/arch.yaml']['extra'] == 'yes'

            def declaration_order_kept():
                blocks = prj.schema.get_section('blocks')
                fields = list(prj.schema.get_section('fwNotes').fields)
                return list(blocks.sub_nodes)[-1] == 'fwQueues' \
                    and prj.schema.get_table_names()[-2:] == ['customSection', 'fwNotes'] \
                    and fields.index('owner') > fields.index('text')

            for label, fn in [("top-level section rows through projectOpen", top_section_rows),
                              ("field added to an earlier extension's section", field_on_earlier_extension),
                              ("sub-table under blocks: through projectOpen", blocks_subtable_rows),
                              ("sub-table under blocks.clocks through projectOpen", two_levels_down_rows),
                              ("fragment merged onto a project dbSchema:", custom_db_schema_rows),
                              ("extension keys follow existing keys", declaration_order_kept),
                              ("relative, absolute and $root fragments in A2C_YAML_FILES",
                               lambda: _manifest_lists(prj, tmp_dir, ext_paths))]:
                results.append(_run_case(label, fn))
        finally:
            _release_db()
            os.chdir(original_cwd)
    return all(results)


def test_project_under_builder():
    """A project inside the builder tree lists its fragment through $a2c, and
    the fragment is still in the build manifest. projectCreate runs once per
    process, so arch2code.py builds this second project in a subprocess."""
    original_cwd = os.getcwd()
    with tempfile.TemporaryDirectory(dir=test_dir) as tmp_dir:
        a2c_entry = '$a2c/' + os.path.relpath(os.path.join(tmp_dir, 'topSection.yaml'), base_dir)
        project_path, db_path, ext_paths = _project(
            tmp_dir, 'schema_ext_under_builder',
            [(a2c_entry, 'topSection.yaml', TOP_SECTION_EXT)],
            'fwNotes:\n  hello: {text: "a note"}\n')
        build = subprocess.run([sys.executable, os.path.join(base_dir, 'arch2code.py'),
                                '-y', project_path, '--db', db_path], capture_output=True, text=True)
        if build.returncode != 0:
            print(build.stdout + build.stderr)
            return _run_case("project under the builder builds", lambda: False)
        try:
            prj = projectOpen(db_path)
            return _run_case("$a2c fragment of a project under the builder in A2C_YAML_FILES",
                             lambda: 'hello/arch.yaml' in prj.data['fwNotes']
                             and _manifest_lists(prj, tmp_dir, ext_paths))
        finally:
            _release_db()
            os.chdir(original_cwd)


def test_redefinition_errors():
    """Restating an existing key stops the build, naming both files and the
    full key path."""
    results = []

    def existing_field():
        text = "blocks:\n  desc: optional\n"
        stopped, out, (ext,) = _build_fails('ext_existing_field', [_local('ext.yaml', text)])
        return stopped and f"{ext}:{_line_of(text, 'desc')}" in out \
            and BASE_SCHEMA_PATH in out and "'blocks.desc'" in out

    def existing_reserved_key():
        text = "blocks:\n  _attribs: [flat]\n"
        stopped, out, (ext,) = _build_fails('ext_reserved_key', [_local('ext.yaml', text)])
        return stopped and f"{ext}:{_line_of(text, '_attribs')}" in out \
            and BASE_SCHEMA_PATH in out and "'blocks._attribs'" in out

    def nested_validate_key():
        text = "blocks:\n  params:\n    paramSource:\n      _validate: {section: types, field: type}\n"
        stopped, out, (ext,) = _build_fails('ext_nested_validate', [_local('ext.yaml', text)])
        return stopped and f"{ext}:{_line_of(text, 'paramSource')}" in out \
            and BASE_SCHEMA_PATH in out and "'blocks.params.paramSource'" in out

    def two_extensions_same_key():
        first = "blocks:\n  fwLevel: optional\n"
        second = "blocks:\n  fwLevel: optional(0)\n"
        stopped, out, (ext1, ext2) = _build_fails(
            'ext_same_key', [_local('first.yaml', first), _local('second.yaml', second)])
        return stopped and f"{ext2}:{_line_of(second, 'fwLevel')}" in out \
            and f"declared in {ext1}" in out and "'blocks.fwLevel'" in out

    def directive_on_earlier_extension_node():
        second = "fwNotes:\n  _attribs: [flat, optional]\n"
        stopped, out, (ext1, ext2) = _build_fails(
            'ext_directive_earlier', [_local('first.yaml', TOP_SECTION_EXT), _local('second.yaml', second)])
        return stopped and f"{ext2}:{_line_of(second, '_attribs')}" in out \
            and f"declared in {ext1}" in out and "'fwNotes._attribs'" in out

    def mapto_alias():
        text = "enums:\n  extra: optional\n"
        stopped, out, (ext,) = _build_fails('ext_mapto', [_local('ext.yaml', text)])
        return stopped and f"{ext}:{_line_of(text, 'enums')}" in out \
            and "'enums' is an alias of 'types'" in out

    for label, fn in [("restating an existing field", existing_field),
                      ("restating an existing reserved key", existing_reserved_key),
                      ("restating a nested field", nested_validate_key),
                      ("two extensions adding the same key", two_extensions_same_key),
                      ("directive on a node an earlier extension added", directive_on_earlier_extension_node),
                      ("extending a _mapto alias", mapto_alias)]:
        results.append(_run_case(label, fn))
    return all(results)


def test_fragment_file_errors():
    """A fragment that is not a mapping, or is listed twice, stops the build
    with a message naming the file."""
    results = []

    def empty_fragment():
        stopped, out, (ext,) = _build_fails('ext_empty', [_local('ext.yaml', '')])
        return stopped and f"Schema extension {ext} must be a mapping" in out

    def list_fragment():
        stopped, out, (ext,) = _build_fails('ext_list', [_local('ext.yaml', '- blocks\n')])
        return stopped and f"Schema extension {ext} must be a mapping" in out

    def listed_twice():
        with tempfile.TemporaryDirectory() as other_dir:
            ext = _write(other_dir, 'ext.yaml', TOP_SECTION_EXT)
            stopped, out, _ = _build_fails('ext_twice', [(ext, None, ''), (ext, None, '')])
        return stopped and f"Schema extension {ext} is listed more than once" in out \
            and "user, user" in out and "already declared" not in out

    for label, fn in [("empty fragment", empty_fragment),
                      ("fragment whose top level is a list", list_fragment),
                      ("fragment listed twice", listed_twice)]:
        results.append(_run_case(label, fn))
    return all(results)


def test_errors_name_the_fragment():
    """A schema error inside a fragment names the fragment, not the base
    schema file, in each of Schema()'s three reporting paths."""
    results = []

    def bad_type_in_new_section():
        text = "fwBad:\n  item: key\n  size: notAType\n"
        stopped, out, (ext,) = _build_fails('ext_bad_section', [_local('ext.yaml', text)])
        return stopped and f"{ext}:" in out and "notAType" in out and BASE_SCHEMA_PATH not in out

    def bad_scalar_field_on_base_section():
        text = "blocks:\n  fwLevel: notAType\n"
        stopped, out, (ext,) = _build_fails('ext_bad_field', [_local('ext.yaml', text)])
        return stopped and f"{ext}:{_line_of(text, 'fwLevel')}" in out \
            and BASE_SCHEMA_PATH not in out

    def bad_foreign_key_on_base_section():
        # Caught by the post-pass foreign-key check, which has no line.
        text = "blocks:\n  fwOwner:\n    _type: optional\n    _validate: {section: noSuchSection, field: x}\n"
        stopped, out, (ext,) = _build_fails('ext_bad_fk', [_local('ext.yaml', text)])
        return stopped and f"Bad schema detected in {ext}." in out and "noSuchSection" in out

    for label, fn in [("error in a new section names the fragment", bad_type_in_new_section),
                      ("error in a field added to a base section names the fragment",
                       bad_scalar_field_on_base_section),
                      ("foreign-key error names the fragment", bad_foreign_key_on_base_section)]:
        results.append(_run_case(label, fn))
    return all(results)


def test_list_order():
    """mergeProjectConfig's two merge_with_spec calls append the lists in
    base, Pro, user order."""
    base = {'schemaExtensions': ['$a2c/config/baseExt.yaml']}
    pro = {'schemaExtensions': ['$a2c/pro/config/proExt.yaml']}
    user = {'schemaExtensions': ['schema/userExt.yaml']}

    def merged(*layers):
        result = {}
        for layer in layers:
            result = merge_with_spec(result, layer, projectCreate.MERGE_SPEC, path=())
        return result['schemaExtensions']

    results = [
        _run_case("base, pro, user order",
                  lambda: merged(base, pro, user) ==
                  ['$a2c/config/baseExt.yaml', '$a2c/pro/config/proExt.yaml', 'schema/userExt.yaml']),
        _run_case("no pro layer", lambda: merged(base, {}, user) ==
                  ['$a2c/config/baseExt.yaml', 'schema/userExt.yaml']),
        _run_case("user only", lambda: merged({}, {}, user) == ['schema/userExt.yaml']),
    ]
    return all(results)


def run_all_tests():
    print("schemaExtensions")
    # The successful builds run first: the failing builds leave g.errorCount
    # raised for the rest of the process.
    results = [test_list_order(),
               test_project_under_builder(),
               test_extension_tables_round_trip(),
               test_redefinition_errors(),
               test_fragment_file_errors(),
               test_errors_name_the_fragment()]
    return 0 if all(results) else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
