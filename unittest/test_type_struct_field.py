#!/usr/bin/env python3
"""Coverage for the `typeStruct` schema field type.

A `typeStruct` field names either a `types` row or a `structures` row in one
YAML key. Four spellings, all resolved the same way in `processSimple`
(`hits` against both sections, filtered to the `kinds` a mode word allows):
  - bare `typeStruct`: accepts either kind (mode word `typeStruct`).
  - `typeStruct(type)` / `typeStruct(struct)`: fix the mode word to `type` /
    `struct` at schema-validation time.
  - `typeStruct(field, <sibling>)`: the mode word is `ret[<sibling>]`, read
    at resolution time; `<sibling>` must be declared earlier in the same
    section.
The mode-word -> accepted-kinds vocabulary lives once, in
`schema.py::Schema.typeStructKindsForMode`; `processSimple` never repeats it.

Since no shipped schema field uses `typeStruct` yet, the fixture project
carries its own schema: the real `config/schema.yaml` plus one extra
top-level section, `typeStructTest`, declaring one field per spelling
(`target`: either, `onlyType`: type-only, `onlyStruct`: struct-only,
`dynamicTarget`: field-selected by the sibling `modeWord`), appended as a
file in a private `TemporaryDirectory` and pointed to via the project's
`dbSchema:` key. The project's own `dirs: root:` also resolves into that
directory, so nothing the test writes lands in the source tree.

Two probe rows resolving a type and a structure through the either field are
written as real YAML, so the full pipeline (schema acceptance, `processSimple`,
DB columns) is exercised end to end. The dynamicTarget "accepts" cases go
through `processSimple` too (synthetic item/schema, still the fixture's real
scope), since that is what proves the sibling lookup and
`typeStructKindsForMode` wiring. The "wrong kind" and "ambiguous" cases call
`projectCreate.resolveTypeStruct` directly with an explicit `kinds` tuple,
since that classification no longer depends on how `kinds` was derived; this
is the same style `test_foreign_key_lookup.py` uses to call
`validateForeignKey` directly with a synthetic source row. Two schema-only
fixtures (their own nested `TemporaryDirectory`) prove a `typeStruct(...)`
with a bad argument, a sibling declared after the field, or a missing
sibling all fail schema validation before any row is parsed."""

import contextlib
import io
import os
import sqlite3
import subprocess
import sys
import tempfile


test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
import pysrc.processYaml as processYaml_module
from pysrc.processYaml import projectCreate, projectOpen

g.disableColors = True

REAL_SCHEMA_PATH = os.path.join(base_dir, 'config', 'schema.yaml')

# The addition under test: a top-level section with one required field per
# typeStruct spelling. `probe` anchors the row; `target` accepts either a
# `types` row or a `structures` row, `onlyType` accepts only a `types` row,
# `onlyStruct` accepts only a `structures` row, and `dynamicTarget` accepts
# whichever kind(s) the earlier-declared `modeWord` field's own value picks.
PROBE_SCHEMA_SECTION = """
typeStructTest:
  probe: key
  target: typeStruct
  onlyType: typeStruct(type)
  onlyStruct: typeStruct(struct)
  modeWord: required
  dynamicTarget: typeStruct(field, modeWord)
"""

# A schema with a typeStruct argument that is neither `struct`, `type`, nor
# `field, <sibling>`; used only to prove schema validation rejects it.
BAD_KIND_SCHEMA_SECTION = """
typeStructTest:
  probe: key
  badKind: typeStruct(enum)
"""

# typeStruct(field, <sibling>) with the sibling declared AFTER the field:
# schema declaration order is the processing order, so this must fail.
BAD_SIBLING_AFTER_SECTION = """
typeStructTest:
  probe: key
  dynBad: typeStruct(field, modeWord2)
  modeWord2: required
"""

# typeStruct(field, <sibling>) naming a sibling that is not declared at all.
BAD_SIBLING_MISSING_SECTION = """
typeStructTest:
  probe: key
  dynBad: typeStruct(field, noSuchSibling)
"""

# typeStruct(field, <sibling>) naming a sibling that IS declared, but under a
# different case (declared `modeWord`, referenced `ModeWord`). The sibling
# check must be an exact-name match, not schema.py's case-insensitive
# has_field, so this must fail the same way a wholly undeclared sibling does.
BAD_SIBLING_CASE_SECTION = """
typeStructTest:
  probe: key
  modeWord: required
  dynBad: typeStruct(field, ModeWord)
"""

# A list sub-table (anchor is None; the row's identity comes from its own
# key field, itemKey) with a typeStruct field, used to prove a missing-field
# diagnostic on such a row names the row via its recorded key field instead
# of printing 'key:None'.
LIST_PROBE_SCHEMA_SECTION = """
typeStructListTest:
  probe: key
  items:
    _attribs: [list]
    itemKey: key
    payload: typeStruct
"""


def _write(tmp_dir, name, content):
    path = os.path.join(tmp_dir, name)
    with open(path, 'w') as f:
        f.write(content)
    return path


def _build_project(tmp_dir):
    """Build a definitions-only fixture project (no topInstance, no
    blocks/instances) entirely inside tmp_dir, using a schema that is the
    real schema.yaml plus the typeStructTest probe section."""
    with open(REAL_SCHEMA_PATH) as f:
        schema_path = _write(
            tmp_dir, 'schema.yaml', f.read() + PROBE_SCHEMA_SECTION)

    # sharedName_t is declared as both a type and a structure on purpose:
    # this is the pair a typeStruct field must reject as ambiguous.
    defs_yaml = """types:
  probeType_t:
    desc: "type used for the typeStruct type-hit case"
    width: 8
  sharedName_t:
    desc: "type half of the ambiguous type/structure pair"
    width: 4

structures:
  probeStruct_t:
    field0: {varType: probeType_t}
  sharedName_t:
    field0: {varType: probeType_t}
"""
    defs_path = _write(tmp_dir, 'defs.yaml', defs_yaml)

    # Every row must fill all fields (each is required); onlyType/onlyStruct/
    # modeWord/dynamicTarget carry fixed, always-valid values on these two
    # rows so the interesting accept/reject cases can be exercised
    # separately via direct calls, one field (or resolveTypeStruct) at a time.
    arch_yaml = f"""include:
  - {os.path.basename(defs_path)}

typeStructTest:
  probeTypeHit: {{target: probeType_t, onlyType: probeType_t, onlyStruct: probeStruct_t, modeWord: typeStruct, dynamicTarget: probeType_t}}
  probeStructHit: {{target: probeStruct_t, onlyType: probeType_t, onlyStruct: probeStruct_t, modeWord: typeStruct, dynamicTarget: probeStruct_t}}
"""
    arch_path = _write(tmp_dir, 'arch.yaml', arch_yaml)

    # root: . keeps every generated/derived path under tmp_dir, resolved
    # relative to this project file's own directory.
    project_yaml = f"""projectName: type_struct_field_test
yamlFormat: 2

dirs:
  root: .

dbSchema: {os.path.basename(schema_path)}

projectFiles:
  - {os.path.basename(arch_path)}
"""
    project_path = _write(tmp_dir, 'project.yaml', project_yaml)

    db_path = os.path.join(tmp_dir, 'ts.db')
    return project_path, db_path, arch_path, defs_path


def _build_bad_schema_project(tmp_dir, section_yaml, project_name):
    """A project whose schema section is invalid in some way: schema
    validation must reject it before any YAML row is parsed, so no arch file
    is needed."""
    with open(REAL_SCHEMA_PATH) as f:
        schema_path = _write(tmp_dir, 'schema.yaml', f.read() + section_yaml)

    project_yaml = f"""projectName: {project_name}
yamlFormat: 2

dirs:
  root: .

dbSchema: {os.path.basename(schema_path)}
"""
    project_path = _write(tmp_dir, 'project.yaml', project_yaml)
    db_path = os.path.join(tmp_dir, 'ts_bad.db')
    return project_path, db_path


def _build_list_probe_project(tmp_dir):
    """A project whose schema adds a list sub-table (LIST_PROBE_SCHEMA_SECTION)
    with a typeStruct field, and whose arch YAML leaves that field off one row.
    Exercises the missing-field diagnostic's row identification when anchor is
    None (list sub-table rows are keyed from item data, not a YAML anchor)."""
    with open(REAL_SCHEMA_PATH) as f:
        schema_path = _write(
            tmp_dir, 'schema.yaml', f.read() + LIST_PROBE_SCHEMA_SECTION)

    arch_yaml = """types:
  probeType_t: {desc: "type for the list-table payload field", width: 8}

typeStructListTest:
  probeList:
    items:
      - {itemKey: good, payload: probeType_t}
      - {itemKey: bad}
"""
    arch_path = _write(tmp_dir, 'arch.yaml', arch_yaml)

    project_yaml = f"""projectName: type_struct_list_test
yamlFormat: 2

dirs:
  root: .

dbSchema: {os.path.basename(schema_path)}

projectFiles:
  - {os.path.basename(arch_path)}
"""
    project_path = _write(tmp_dir, 'project.yaml', project_yaml)
    db_path = os.path.join(tmp_dir, 'ts_list.db')
    return project_path, db_path


def _run_case(label, fn):
    try:
        ok = fn()
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    print(f"{'PASS' if ok else 'FAIL'}: {label}")
    return ok


def _direct_probe_row(creator, arch_context, probe, item, schema):
    """Call processSimple directly on the fixture's own creator, in the
    fixture arch file's own scope, with a synthetic item/schema holding only
    the fields under test. This exercises the same lookupInScope/_a2csystem
    walk a real row in that file would get, without a second project build
    that would abort at the first error, and without needing the other
    typeStruct fields the real section also declares. `item`/`schema` order
    matters when a field's mode word is read from an earlier field in the
    same call (the dynamicTarget cases), exactly as it does for a real row."""
    return creator.processSimple(
        'typeStructTest', probe, item, arch_context, schema=schema)


def _direct_probe(creator, arch_context, probe, field, value):
    """Single-field convenience wrapper over _direct_probe_row, for the
    typeStruct fields whose kinds are a schema-time constant."""
    return _direct_probe_row(
        creator, arch_context, probe, {field: value}, {field: 'typeStruct'})


def _run():
    print("typeStruct field resolution")
    original_cwd = os.getcwd()
    results = []
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path, db_path, arch_path, defs_path = _build_project(tmp_dir)
            arch_context = os.path.basename(arch_path)
            defs_context = os.path.basename(defs_path)

            creator = projectCreate(project_path, db_path)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            g.db = conn
            g.cur = conn.cursor()

            def type_hit_row_scope():
                # Real YAML: probeTypeHit resolves probeType_t against
                # `types`. The lookup walks the arch row's own include chain
                # to reach defs_path, so the qualification in targetKey is
                # defs_context (where probeType_t is declared), not
                # arch_context (where the probe row lives).
                row = conn.execute(
                    "SELECT target, targetKey, targetKind FROM typeStructTest "
                    "WHERE probe = 'probeTypeHit'").fetchone()
                return row is not None \
                    and row['target'] == 'probeType_t' \
                    and row['targetKind'] == 'types' \
                    and row['targetKey'] == f'probeType_t/{defs_context}'

            def structure_hit_row_scope():
                # Real YAML: probeStructHit resolves probeStruct_t against
                # `structures`, in the same scope.
                row = conn.execute(
                    "SELECT target, targetKey, targetKind FROM typeStructTest "
                    "WHERE probe = 'probeStructHit'").fetchone()
                return row is not None \
                    and row['target'] == 'probeStruct_t' \
                    and row['targetKind'] == 'structures' \
                    and row['targetKey'] == f'probeStruct_t/{defs_context}'

            def neither_errors():
                before = g.errorCount
                processYaml_module.continueOnError = True
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        _direct_probe(
                            creator, arch_context, 'probeNeither', 'target',
                            'noSuchName_t')
                finally:
                    processYaml_module.continueOnError = False
                output = buf.getvalue()
                # The message must name the file, section, field, and the
                # value, and say it is neither a type nor a structure.
                return g.errorCount > before \
                    and arch_context in output \
                    and 'typeStructTest' in output \
                    and 'target' in output \
                    and 'noSuchName_t' in output \
                    and 'neither a type nor a structure' in output

            def both_errors():
                before = g.errorCount
                processYaml_module.continueOnError = True
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        _direct_probe(
                            creator, arch_context, 'probeBoth', 'target',
                            'sharedName_t')
                finally:
                    processYaml_module.continueOnError = False
                output = buf.getvalue()
                # The message must name the file, section, field, and the
                # value, and say the name is ambiguous.
                return g.errorCount > before \
                    and arch_context in output \
                    and 'typeStructTest' in output \
                    and 'target' in output \
                    and 'sharedName_t' in output \
                    and 'ambiguous' in output

            def a2csystem_fallback():
                # No shipped types/structures load into _a2csystem by
                # default, so seed one directly (same primitive
                # lookupInScope already falls back to; see the
                # a2csystem_fallback case in test_foreign_key_lookup.py) and
                # confirm the typeStruct branch finds it there when it is
                # not in the file's own include chain.
                creator.data['types'].setdefault('_a2csystem', {})['sysProbe_t'] = {
                    'type': 'sysProbe_t',
                    '_context': '_a2csystem',
                    'width': 5,
                    'isParameterizable': False,
                }
                ret = _direct_probe(
                    creator, arch_context, 'probeSysHit', 'target',
                    'sysProbe_t')
                return ret['target'] == 'sysProbe_t' \
                    and ret['targetKind'] == 'types' \
                    and ret['targetKey'] == 'sysProbe_t/_a2csystem'

            def only_type_accepts_type():
                # onlyType: typeStruct(type) resolves a types row.
                ret = _direct_probe(
                    creator, arch_context, 'probeOnlyTypeOk', 'onlyType',
                    'probeType_t')
                return ret['onlyType'] == 'probeType_t' \
                    and ret['onlyTypeKind'] == 'types' \
                    and ret['onlyTypeKey'] == f'probeType_t/{defs_context}'

            def only_type_rejects_structure():
                # onlyType: typeStruct(type) must not resolve a structures
                # row, even though probeStruct_t is a real structure visible
                # from this scope; it must name the mismatch, not "neither".
                before = g.errorCount
                processYaml_module.continueOnError = True
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        _direct_probe(
                            creator, arch_context, 'probeOnlyTypeBad',
                            'onlyType', 'probeStruct_t')
                finally:
                    processYaml_module.continueOnError = False
                output = buf.getvalue()
                return g.errorCount > before \
                    and arch_context in output \
                    and 'typeStructTest' in output \
                    and 'onlyType' in output \
                    and 'probeStruct_t' in output \
                    and 'accepts only a type' in output \
                    and 'is a structure' in output \
                    and defs_context in output

            def only_struct_accepts_structure():
                # onlyStruct: typeStruct(struct) resolves a structures row.
                ret = _direct_probe(
                    creator, arch_context, 'probeOnlyStructOk', 'onlyStruct',
                    'probeStruct_t')
                return ret['onlyStruct'] == 'probeStruct_t' \
                    and ret['onlyStructKind'] == 'structures' \
                    and ret['onlyStructKey'] == f'probeStruct_t/{defs_context}'

            def only_struct_rejects_type():
                # onlyStruct: typeStruct(struct) must not resolve a types
                # row, even though probeType_t is a real type visible from
                # this scope; it must name the mismatch, not "neither".
                before = g.errorCount
                processYaml_module.continueOnError = True
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        _direct_probe(
                            creator, arch_context, 'probeOnlyStructBad',
                            'onlyStruct', 'probeType_t')
                finally:
                    processYaml_module.continueOnError = False
                output = buf.getvalue()
                return g.errorCount > before \
                    and arch_context in output \
                    and 'typeStructTest' in output \
                    and 'onlyStruct' in output \
                    and 'probeType_t' in output \
                    and 'accepts only a structure' in output \
                    and 'is a type' in output \
                    and defs_context in output

            def _direct_resolve(name, kinds):
                # Drives resolveTypeStruct directly with an explicit kinds
                # tuple: the wrong-kind/ambiguous classification does not
                # depend on whether kinds came from a constant spelling or
                # from a sibling's value, so there is no need to route
                # through processSimple (or a synthetic schema) to reach it.
                before = g.errorCount
                processYaml_module.continueOnError = True
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        result = creator.resolveTypeStruct(
                            name, arch_context, kinds, 'where')
                finally:
                    processYaml_module.continueOnError = False
                return result, buf.getvalue(), g.errorCount > before

            def dynamic_type_accepts_type():
                # dynamicTarget: typeStruct(field, modeWord); modeWord's own
                # value ('type') picks the kinds at resolution time.
                ret = _direct_probe_row(
                    creator, arch_context, 'probeDynTypeOk',
                    {'modeWord': 'type', 'dynamicTarget': 'probeType_t'},
                    {'modeWord': 'required', 'dynamicTarget': 'typeStruct'})
                return ret['dynamicTarget'] == 'probeType_t' \
                    and ret['dynamicTargetKind'] == 'types' \
                    and ret['dynamicTargetKey'] == f'probeType_t/{defs_context}'

            def dynamic_struct_accepts_structure():
                ret = _direct_probe_row(
                    creator, arch_context, 'probeDynStructOk',
                    {'modeWord': 'struct', 'dynamicTarget': 'probeStruct_t'},
                    {'modeWord': 'required', 'dynamicTarget': 'typeStruct'})
                return ret['dynamicTarget'] == 'probeStruct_t' \
                    and ret['dynamicTargetKind'] == 'structures' \
                    and ret['dynamicTargetKey'] == f'probeStruct_t/{defs_context}'

            def dynamic_typeStruct_accepts_either():
                # modeWord 'typeStruct' accepts both kinds: prove it against
                # one name of each kind.
                retType = _direct_probe_row(
                    creator, arch_context, 'probeDynEitherType',
                    {'modeWord': 'typeStruct', 'dynamicTarget': 'probeType_t'},
                    {'modeWord': 'required', 'dynamicTarget': 'typeStruct'})
                retStruct = _direct_probe_row(
                    creator, arch_context, 'probeDynEitherStruct',
                    {'modeWord': 'typeStruct', 'dynamicTarget': 'probeStruct_t'},
                    {'modeWord': 'required', 'dynamicTarget': 'typeStruct'})
                return retType['dynamicTargetKind'] == 'types' \
                    and retStruct['dynamicTargetKind'] == 'structures'

            def dynamic_type_rejects_structure():
                result, output, errored = _direct_resolve(
                    'probeStruct_t', ('types',))
                return result is None and errored \
                    and 'accepts only a type' in output \
                    and 'is a structure' in output \
                    and defs_context in output

            def dynamic_struct_rejects_type():
                result, output, errored = _direct_resolve(
                    'probeType_t', ('structures',))
                return result is None and errored \
                    and 'accepts only a structure' in output \
                    and 'is a type' in output \
                    and defs_context in output

            def dynamic_typeStruct_ambiguous():
                result, output, errored = _direct_resolve(
                    'sharedName_t', ('types', 'structures'))
                return result is None and errored and 'ambiguous' in output

            def dynamic_sibling_non_scalar_errors():
                # The sibling's own value (modeWord) is a YAML list, not a
                # scalar mode word: this must log a clean error naming the
                # offending value, not raise TypeError out of
                # typeStructKindsForMode's dict.get(word).
                before = g.errorCount
                processYaml_module.continueOnError = True
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        ret = _direct_probe_row(
                            creator, arch_context, 'probeSiblingList',
                            {'modeWord': ['type'], 'dynamicTarget': 'probeType_t'},
                            {'modeWord': 'required', 'dynamicTarget': 'typeStruct'})
                finally:
                    processYaml_module.continueOnError = False
                output = buf.getvalue()
                return g.errorCount > before \
                    and ret['dynamicTargetKey'] == 'InvalidValueInYaml' \
                    and ret['dynamicTargetKind'] == 'InvalidValueInYaml' \
                    and 'modeWord' in output \
                    and 'must be a scalar' in output

            def dynamic_field_non_scalar_errors():
                # The typeStruct field's own value (dynamicTarget) is a YAML
                # list, not a name: this must log a clean error, not raise
                # TypeError out of resolveTypeStruct's lookupInScope.
                before = g.errorCount
                processYaml_module.continueOnError = True
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        ret = _direct_probe_row(
                            creator, arch_context, 'probeFieldList',
                            {'modeWord': 'type', 'dynamicTarget': ['probeType_t']},
                            {'modeWord': 'required', 'dynamicTarget': 'typeStruct'})
                finally:
                    processYaml_module.continueOnError = False
                output = buf.getvalue()
                return g.errorCount > before \
                    and ret['dynamicTargetKey'] == 'InvalidValueInYaml' \
                    and ret['dynamicTargetKind'] == 'InvalidValueInYaml' \
                    and 'dynamicTarget' in output \
                    and 'must be a scalar' in output

            def sentinel_sibling_value_errors():
                # A user who literally types the sentinel string
                # InvalidValueInYaml as the sibling's value must get the same
                # "not 'type', 'struct', or 'typeStruct'" error any other
                # unrecognised mode word gets, not silent acceptance.
                before = g.errorCount
                processYaml_module.continueOnError = True
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        _direct_probe_row(
                            creator, arch_context, 'probeSentinel',
                            {'modeWord': 'InvalidValueInYaml',
                             'dynamicTarget': 'probeType_t'},
                            {'modeWord': 'required', 'dynamicTarget': 'typeStruct'})
                finally:
                    processYaml_module.continueOnError = False
                output = buf.getvalue()
                return g.errorCount > before \
                    and 'InvalidValueInYaml' in output \
                    and "not 'type', 'struct', or 'typeStruct'" in output

            def missing_field_sets_row_shape():
                # The typeStruct field itself absent from the row: ret[field]
                # must still be populated (None), the same way the `required`
                # branch handles a missing field, so continueOnError callers
                # do not crash with a KeyError reading it back downstream.
                before = g.errorCount
                processYaml_module.continueOnError = True
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        ret = _direct_probe_row(
                            creator, arch_context, 'probeMissingField',
                            {'modeWord': 'type'},
                            {'modeWord': 'required', 'dynamicTarget': 'typeStruct'})
                finally:
                    processYaml_module.continueOnError = False
                return g.errorCount > before \
                    and ret['dynamicTarget'] is None \
                    and ret['dynamicTargetKey'] == 'InvalidValueInYaml' \
                    and ret['dynamicTargetKind'] == 'InvalidValueInYaml'

            results.append(_run_case(
                "type hit (row scope)", type_hit_row_scope))
            results.append(_run_case(
                "structure hit (row scope)", structure_hit_row_scope))
            results.append(_run_case("neither errors", neither_errors))
            results.append(_run_case("both errors (ambiguous)", both_errors))
            results.append(_run_case(
                "_a2csystem fallback", a2csystem_fallback))
            results.append(_run_case(
                "typeStruct(type) accepts a type", only_type_accepts_type))
            results.append(_run_case(
                "typeStruct(type) rejects a structure",
                only_type_rejects_structure))
            results.append(_run_case(
                "typeStruct(struct) accepts a structure",
                only_struct_accepts_structure))
            results.append(_run_case(
                "typeStruct(struct) rejects a type",
                only_struct_rejects_type))
            results.append(_run_case(
                "typeStruct(field, modeWord) type accepts a type",
                dynamic_type_accepts_type))
            results.append(_run_case(
                "typeStruct(field, modeWord) struct accepts a structure",
                dynamic_struct_accepts_structure))
            results.append(_run_case(
                "typeStruct(field, modeWord) typeStruct accepts either",
                dynamic_typeStruct_accepts_either))
            results.append(_run_case(
                "typeStruct(field, modeWord) type rejects a structure",
                dynamic_type_rejects_structure))
            results.append(_run_case(
                "typeStruct(field, modeWord) struct rejects a type",
                dynamic_struct_rejects_type))
            results.append(_run_case(
                "typeStruct(field, modeWord) typeStruct errors on ambiguity",
                dynamic_typeStruct_ambiguous))
            results.append(_run_case(
                "typeStruct(field, modeWord) non-scalar sibling value errors",
                dynamic_sibling_non_scalar_errors))
            results.append(_run_case(
                "typeStruct(field, modeWord) non-scalar field value errors",
                dynamic_field_non_scalar_errors))
            results.append(_run_case(
                "typeStruct(field, modeWord) literal sentinel sibling value errors",
                sentinel_sibling_value_errors))
            results.append(_run_case(
                "typeStruct(field, modeWord) missing field sets row shape",
                missing_field_sets_row_shape))

            # projectOpen.datatypeRef: close the write connection this test
            # opened, then reopen the persisted DB read-only through
            # projectOpen, matching how test_eval_canonical_view.py hands
            # off between the two.
            conn.close()
            conn = None
            g.db = None
            g.cur = None

            def datatype_ref_contract():
                prj = projectOpen(db_path)
                typeInfo = prj.datatypeRef(
                    'types', f'probeType_t/{defs_context}')
                structInfo = prj.datatypeRef(
                    'structures', f'probeStruct_t/{defs_context}')
                return typeInfo['kind'] == 'types' \
                    and typeInfo['name'] == 'probeType_t' \
                    and typeInfo['context'] == defs_context \
                    and typeInfo['isParameterizable'] == False \
                    and typeInfo['width'] == 8 \
                    and typeInfo['row']['type'] == 'probeType_t' \
                    and structInfo['kind'] == 'structures' \
                    and structInfo['name'] == 'probeStruct_t' \
                    and structInfo['context'] == defs_context \
                    and structInfo['row']['structure'] == 'probeStruct_t'

            results.append(_run_case(
                "projectOpen.datatypeRef contract", datatype_ref_contract))

            # Release the projectOpen connection and leave tmp_dir before the
            # TemporaryDirectory context manager removes it.
            if g.db is not None:
                g.db.close()
            g.db = None
            g.cur = None
            os.chdir(original_cwd)

        def _schema_validation_error(section_yaml, project_name):
            # Schema() construction (inside projectCreate.__init__) must
            # reject the bad section before any YAML row is parsed. Each
            # case gets its own TemporaryDirectory, independent of the one
            # above and of each other.
            with tempfile.TemporaryDirectory() as bad_tmp_dir:
                bad_project_path, bad_db_path = _build_bad_schema_project(
                    bad_tmp_dir, section_yaml, project_name)
                buf = io.StringIO()
                raised = False
                try:
                    with contextlib.redirect_stdout(buf):
                        projectCreate(bad_project_path, bad_db_path)
                except SystemExit:
                    raised = True
                finally:
                    if g.db is not None:
                        try:
                            g.db.close()
                        except Exception:
                            pass
                    g.db = None
                    g.cur = None
                    os.chdir(original_cwd)
                return raised, buf.getvalue()

        def bad_kind_argument_rejected():
            # typeStruct(enum) is none of 'struct', 'type', or 'field, ...'.
            raised, output = _schema_validation_error(
                BAD_KIND_SCHEMA_SECTION, 'type_struct_bad_kind_test')
            return raised \
                and 'badKind' in output \
                and "'struct'" in output \
                and "'type'" in output

        def sibling_declared_after_rejected():
            # typeStruct(field, modeWord2) with modeWord2 declared after it.
            raised, output = _schema_validation_error(
                BAD_SIBLING_AFTER_SECTION,
                'type_struct_bad_sibling_after_test')
            return raised \
                and 'dynBad' in output \
                and 'modeWord2' in output

        def sibling_missing_rejected():
            # typeStruct(field, noSuchSibling) naming an undeclared sibling.
            raised, output = _schema_validation_error(
                BAD_SIBLING_MISSING_SECTION,
                'type_struct_bad_sibling_missing_test')
            return raised \
                and 'dynBad' in output \
                and 'noSuchSibling' in output

        def sibling_case_mismatch_rejected():
            # typeStruct(field, ModeWord) with the sibling declared as
            # modeWord: the sibling check is an exact-name match (schema.py
            # node.fields), not schema.py's case-insensitive has_field, so a
            # case mismatch must be rejected the same way a wholly missing
            # sibling is.
            raised, output = _schema_validation_error(
                BAD_SIBLING_CASE_SECTION,
                'type_struct_bad_sibling_case_test')
            return raised \
                and 'dynBad' in output \
                and 'ModeWord' in output \
                and 'declared earlier in the same section' in output

        def list_table_missing_field_names_row():
            # A list sub-table row's missing-field diagnostic must identify
            # the row via its own recorded key field (processSubTable's
            # storage_key_field), not print 'key:None' (anchor is None for
            # list sub-table rows; the key comes from item data instead).
            # Run through a real arch2code.py subprocess, like
            # test_block_own_surface_param_no_params.py, rather than a second
            # in-process projectCreate: processYaml's class-level ownership
            # dicts (contextOwningProject, includeName, ...) accumulate across
            # instances within one process, and the main fixture above already
            # parsed a same-named 'defs.yaml'/'arch.yaml' context in-process.
            with tempfile.TemporaryDirectory() as list_tmp_dir:
                list_project_path, list_db_path = _build_list_probe_project(
                    list_tmp_dir)
                env = os.environ.copy()
                env['NO_COLOR'] = '1'
                result = subprocess.run(
                    [sys.executable, os.path.join(base_dir, 'arch2code.py'),
                     '--yaml', list_project_path, '--db', list_db_path],
                    capture_output=True, text=True, cwd=list_tmp_dir, env=env,
                    timeout=60)
                output = result.stdout + result.stderr
                return result.returncode != 0 \
                    and 'Traceback (most recent call last)' not in output \
                    and 'key:None' not in output \
                    and 'bad' in output \
                    and 'payload' in output

        results.append(_run_case(
            "typeStruct(enum) fails schema validation",
            bad_kind_argument_rejected))
        results.append(_run_case(
            "typeStruct(field, sibling) declared after fails schema validation",
            sibling_declared_after_rejected))
        results.append(_run_case(
            "typeStruct(field, sibling) missing sibling fails schema validation",
            sibling_missing_rejected))
        results.append(_run_case(
            "typeStruct(field, sibling) case mismatch fails schema validation",
            sibling_case_mismatch_rejected))
        results.append(_run_case(
            "list sub-table missing-field diagnostic names the row",
            list_table_missing_field_names_row))

        return all(results)
    except Exception as exc:
        print(f"FAIL: setup raised {exc}")
        return False
    finally:
        processYaml_module.continueOnError = False
        if g.db is not None:
            try:
                g.db.close()
            except Exception:
                pass
        g.db = None
        g.cur = None
        os.chdir(original_cwd)


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
