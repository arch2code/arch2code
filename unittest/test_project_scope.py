#!/usr/bin/env python3
"""Coverage for project-scoped declarations (`_attribs: [projectScope]` +
`_validate: scope: project`).

Four groups: schema-time validation in `schema.py`; one in-process build of a
COMPOSED fixture (an assembling project plus a child IP project, each declaring
a clock named `clk` with different attributes); subprocess builds that assert the
stored rows of one project shape each, including the built-in declarations a
project inherits when it authors none; and subprocess builds for each diagnostic.

The project-scoped section set is DISCOVERED from the shipped schema, so the
structural assertions cannot drift from `config/schema.yaml`.

Fixtures are written OUTSIDE the repository working tree: git does not track
empty directories, so a fixture left under unittest/ is a stray directory
`git status` never reports. Cleanup deliberately does not suppress errors.
"""

import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

from ruamel.yaml import YAML

test_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(test_dir)
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

import pysrc.arch2codeGlobals as g
from pysrc.schema import Schema
from pysrc.processYaml import projectCreate

g.disableColors = True

SHIPPED_SCHEMA = os.path.join(base_dir, 'config', 'schema.yaml')

# Test-only schema extension appended to the real schema. The shipped schema's
# only scope: project reference, resets.clock, is itself project-scoped, so it
# offers none of the shapes below:
#   clockConsumers - a design-YAML section referencing a project-scoped one.
#   plainRows      - references nothing; something legal for a root design
#                    context to declare where the root project declares no clocks.
#   plainRefs      - an ORDINARY include-chain foreign key, so a design file whose
#                    context key spells a scope name can be shown to still resolve
#                    through the include chain.
#   clockAliases   - a _mapto alias of a project-scoped section, which the
#                    pre-pass must resolve before selecting by canonical name.
CONSUMER_SECTION = """
clockConsumers:
  _attribs: [flat]
  clockConsumer: key
  desc: required
  clock:
    _type: required
    _validate:
      section: clocks
      field: clock
      scope: project

plainRows:
  _attribs: [flat]
  plainRow: key
  desc: required

plainRefs:
  _attribs: [flat]
  plainRef: key
  target:
    _type: required
    _validate:
      section: plainRows
      field: plainRow

clockAliases:
  _mapto: clocks
"""

# A scope: project foreign key on a section the SHIPPED system files author, so
# its rows parse into the _a2csystem special context, which belongs to no project
# and is keyed in no bucket. The default value is what makes the validator run: an
# optional field left empty skips validation entirely.
SYSTEM_CONTEXT_FIELD = ('sysClock', {
    '_type': 'optional(clk)',
    '_validate': {'section': 'clocks', 'field': 'clock', 'scope': 'project'},
})


# ---------------------------------------------------------------- fixtures --

def _write_schema(schema_path, system_scope_field):
    yaml = YAML(typ='rt')
    with open(SHIPPED_SCHEMA) as src:
        schema = yaml.load(src)
    if system_scope_field:
        name, spec = SYSTEM_CONTEXT_FIELD
        schema['interface_defs'][name] = spec
    with open(schema_path, 'w') as dst:
        yaml.dump(schema, dst)
        dst.write(CONSUMER_SECTION)


def _make_fixture(root_clocks, child_clocks=None, consumer_clock='clk',
                  root_project_name='assembler', child_consumer_clock='clk',
                  design_yaml_extra='', system_scope_field=False,
                  extra_design_files=()):
    """Write a composed fixture into a fresh temp dir outside the repo tree.

    `consumer_clock=None` makes the root-owned design contexts declare a row
    that references no project-scoped object, for the fixtures where the root
    project declares no clocks. `design_yaml_extra` is appended verbatim to
    top.yaml, to author a project-scoped section in the wrong file.
    `extra_design_files` is a sequence of (name, content) written into the
    fixture and listed in the root project's projectFiles:, so a context key can
    be spelled deliberately (a file named after a scope, for instance).

    Returns (fixture_dir, project_path, db_path).
    """
    fixture = tempfile.mkdtemp(prefix='projscope_')
    _write_schema(os.path.join(fixture, 'testSchema.yaml'), system_scope_field)

    def rootContext(path, key, desc):
        with open(os.path.join(fixture, path), 'w') as f:
            if consumer_clock is None:
                f.write("plainRows:\n"
                        f"  {key}:\n"
                        f"    desc: \"{desc}\"\n")
            else:
                f.write("clockConsumers:\n"
                        f"  {key}:\n"
                        f"    desc: \"{desc}\"\n"
                        f"    clock: {consumer_clock}\n")

    rootContext('top.yaml', 'topUser', 'consumer in the assembling project')
    # Second root-owned context with NO include edge to top.yaml and none to the
    # project file: proves project scope needs no include-chain plumbing.
    rootContext('top2.yaml', 'top2User', 'unrelated second context, no include edge')
    if design_yaml_extra:
        with open(os.path.join(fixture, 'top.yaml'), 'a') as f:
            f.write(design_yaml_extra)

    childFiles = ''
    if child_clocks is not None:
        os.mkdir(os.path.join(fixture, 'ip'))
        with open(os.path.join(fixture, 'ip', 'ipArch.yaml'), 'w') as f:
            f.write("clockConsumers:\n"
                    "  ipUser:\n"
                    "    desc: \"consumer owned by the child IP\"\n"
                    f"    clock: {child_consumer_clock}\n")
        with open(os.path.join(fixture, 'ip', 'ipProject.yaml'), 'w') as f:
            f.write("yamlFormat: 2\n"
                    "projectName: childIp\n"
                    "dbSchema: ../testSchema.yaml\n"
                    "\n"
                    "dirs:\n"
                    "  root: .\n"
                    "\n"
                    "fileGeneration:\n"
                    "  layout: functional\n"
                    "\n"
                    f"{child_clocks}"
                    "\n"
                    "projectFiles:\n"
                    "  - ipArch.yaml\n")
        childFiles = '  - ip/ipProject.yaml\n'

    extraFiles = ''
    for name, content in extra_design_files:
        with open(os.path.join(fixture, name), 'w') as f:
            f.write(content)
        extraFiles += f"  - {name}\n"

    project_path = os.path.join(fixture, 'project.yaml')
    with open(project_path, 'w') as f:
        f.write("yamlFormat: 2\n"
                f"projectName: {root_project_name}\n"
                "dbSchema: testSchema.yaml\n"
                "\n"
                "dirs:\n"
                "  root: .\n"
                "\n"
                f"{root_clocks}"
                "\n"
                "projectFiles:\n"
                "  - top.yaml\n"
                "  - top2.yaml\n"
                f"{extraFiles}"
                f"{childFiles}")
    return fixture, project_path, os.path.join(fixture, 'project.db')


ROOT_CLOCKS = ("clocks:\n"
               "  clk: { desc: \"assembler clock\", default: true, period: 1, timeUnit: ns }\n"
               "\n"
               "resets:\n"
               "  rst_n: { desc: \"assembler reset\", default: true, clock: clk }\n")

CHILD_CLOCKS = ("clocks:\n"
                "  clk: { desc: \"child IP clock\", default: true, period: 4, timeUnit: ns }\n")

# The same two declarations with resets: authored ABOVE clocks:.
REVERSED_ROOT_CLOCKS = (
    "resets:\n"
    "  rst_n: { desc: \"assembler reset\", default: true, clock: clk }\n"
    "\n"
    "clocks:\n"
    "  clk: { desc: \"assembler clock\", default: true, period: 1, timeUnit: ns }\n")

# The same declaration spelled through the section's _mapto alias.
ALIASED_ROOT_CLOCKS = (
    "clockAliases:\n"
    "  clk: { desc: \"aliased clock\", default: true, period: 1, timeUnit: ns }\n")

# An unresolved scope: project reference authored INSIDE the project file, i.e.
# on a row whose parse context is the project bucket rather than a file.
UNRESOLVED_IN_PROJECT_FILE = (
    "clocks:\n"
    "  clk: { desc: \"assembler clock\", default: true }\n"
    "\n"
    "resets:\n"
    "  rst_n: { desc: \"reset in an undeclared domain\", clock: noSuchClock }\n")

# Project files whose rows fail one processSimple check each.
BAD_VALUE_IN_PROJECT_FILE = (
    "clocks:\n"
    "  clk: { desc: \"assembler clock\", default: true, timeUnit: xs }\n")

MISSING_FIELD_IN_PROJECT_FILE = (
    "clocks:\n"
    "  clk: { default: true }\n")

UNKNOWN_FIELD_IN_PROJECT_FILE = (
    "clocks:\n"
    "  clk: { desc: \"assembler clock\", default: true, bogusField: 3 }\n")

# A project declaring its own clock under a name that is NOT the built-in one,
# and no resets: at all - the mixed case per-section injection has to handle.
CORE_CLOCK_ONLY = (
    "clocks:\n"
    "  coreClk: { desc: \"the project's own clock\", default: true, period: 2, timeUnit: ns }\n")

# One default among several entries, plus an authored reset omitting clock:.
MULTI_ENTRY_ONE_DEFAULT = (
    "clocks:\n"
    "  clk:     { desc: \"the default clock\", default: true, period: 1, timeUnit: ns }\n"
    "  clkSlow: { desc: \"a second, non-default clock\", period: 4, timeUnit: ns }\n"
    "\n"
    "resets:\n"
    "  rst_n:    { desc: \"default reset, clock unstated\", default: true }\n"
    "  rstAlt_n: { desc: \"non-default reset, slow domain\", clock: clkSlow }\n")

# One entry taking each count field's schema default and one authoring it, so a
# single build sees both halves of the type split the coercion closes.
COUNT_FIELD_TYPES = (
    "clocks:\n"
    "  clk:     { desc: \"default clock, period defaulted\", default: true }\n"
    "  clkSlow: { desc: \"second clock, period authored\", period: 4 }\n"
    "\n"
    "resets:\n"
    "  rst_n:    { desc: \"default reset, releaseCycles defaulted\", default: true, clock: clk }\n"
    "  rstAlt_n: { desc: \"second reset, releaseCycles authored\", clock: clkSlow, releaseCycles: 5 }\n")

# A design file whose context key spells the name of a scope, declaring an
# ORDINARY include-chain foreign key that resolves within itself.
SCOPE_NAMED_CONTEXT = (
    "plainRows:\n"
    "  magicRow:\n"
    "    desc: \"declared in a file named after a scope\"\n"
    "plainRefs:\n"
    "  magicRef:\n"
    "    target: magicRow\n")


def _run_case(label, fn):
    try:
        ok = fn()
    except Exception as exc:
        print(f"FAIL: {label}: {exc}")
        return False
    print(f"{'PASS' if ok else 'FAIL'}: {label}")
    return ok


# ------------------------------------------------------- schema-time cases --

def _schema_rejects(schema_yaml):
    try:
        Schema(schema_yaml=schema_yaml, schema_file='projscope_test.yaml',
               skip_config=True)
    except SystemExit:
        return True
    return False


def _schema_case(target_attribs, scope):
    """A design-style section referencing a target section."""
    target = {'_attribs': target_attribs, 'target': 'key'}
    validate = {'section': 'targets', 'field': 'target'}
    if scope is not None:
        validate['scope'] = scope
    return {
        'targets': target,
        'sources': {'source': 'key',
                    'target': {'_type': 'required', '_validate': validate}},
    }


def _project_scope_source_case(scope):
    """A foreign key on a field OF a projectScope section.

    Such a row is parsed with the declaring projectName as its context, which is
    a bucket key and not a yamlContext key, so an include-chain walk indexes
    yamlContext with a key that does not exist."""
    validate = {'section': 'others', 'field': 'other'}
    if scope is not None:
        validate['scope'] = scope
    return {
        'others': {'_attribs': ['flat'], 'other': 'key'},
        'projRows': {'_attribs': ['flat', 'projectScope'],
                     'projRow': 'key',
                     'ref': {'_type': 'required', '_validate': validate}},
    }


def _project_scope_subtable_case():
    """A scope-less foreign key on a field of a SUB-TABLE of a projectScope
    section.

    A nested node is parsed with its parent's context - the declaring projectName
    - so the bucket-context constraint applies to the whole subtree. The section
    itself carries no foreign key here, so only the walk over sub_nodes can
    reject this."""
    return {
        'others': {'_attribs': ['flat'], 'other': 'key'},
        'projRows': {'_attribs': ['flat', 'projectScope'],
                     'projRow': 'key',
                     'nested': {'_attribs': ['required', 'multiple', 'flat'],
                                'nestedRow': 'key',
                                'ref': {'_type': 'required',
                                        '_validate': {'section': 'others',
                                                      'field': 'other'}}}},
    }


def _project_scope_data_schema_case():
    """A scope-less foreign key inside the _dataSchema of a projectScope section.

    _dataSchema is deliberately excluded from sub_nodes, so it is reachable only
    by following data_schema. The shipped schema puts the bulk of a custom-handler
    section's validators there (connections._dataSchema), so this is real shape,
    not a contrivance."""
    return {
        'others': {'_attribs': ['flat'], 'other': 'key'},
        'projRows': {'_attribs': ['flat', 'projectScope'],
                     '_dataSchema': {
                         'projRow': 'key',
                         'ref': {'_type': 'required',
                                 '_validate': {'section': 'others',
                                               'field': 'other'}}},
                     'projRow': 'key',
                     'desc': 'required'},
    }


def _nested_project_scope_case():
    """projectScope declared on a NESTED node.

    The project-file pre-pass selects sections to parse by top-level section
    name, so the attribute is inert here: the node is neither parsed from the
    project file nor covered by the bucket-context foreign-key rule."""
    return {
        'others': {'_attribs': ['flat'], 'other': 'key'},
        'outers': {'_attribs': ['flat'],
                   'outer': 'key',
                   'inners': {'_attribs': ['required', 'multiple', 'flat',
                                           'projectScope'],
                              'inner': 'key',
                              'ref': {'_type': 'required',
                                      '_validate': {'section': 'others',
                                                    'field': 'other'}}}},
    }


def _project_scope_order_case(target_first):
    """Two project-scoped sections, one referencing the other with scope:
    project.

    The pre-pass parses project-scoped sections in SCHEMA declaration order and
    validates foreign keys as it parses, so a target declared after its referrer
    is not yet in its bucket and an entirely valid project file is rejected. A
    user's project file therefore depends on the order of two sections in
    config/schema.yaml, which nothing else enforces."""
    target = {'projTargets': {'_attribs': ['flat', 'projectScope'],
                              'projTarget': 'key'}}
    source = {'projSources': {'_attribs': ['flat', 'projectScope'],
                              'projSource': 'key',
                              'ref': {'_type': 'required',
                                      '_validate': {'section': 'projTargets',
                                                    'field': 'projTarget',
                                                    'scope': 'project'}}}}
    # dicts preserve insertion order, and so does the schema loader, so this is
    # the declaration order the check reads.
    return {**target, **source} if target_first else {**source, **target}


def _combo_project_scope_case():
    """A COMBO foreign key declaring scope: project.

    Project resolution is a direct dict hit on the target's storage key and never
    compares combo component fields, so a combo FK must not be allowed to
    declare it."""
    return {
        'targets': {'_attribs': ['flat', 'projectScope'],
                    'a': 'required',
                    'b': 'required',
                    'ab': {'_key': {'a': 'required', 'b': 'required'}}},
        'sources': {'source': 'key',
                    'a': 'required',
                    'b': 'required',
                    'ab': {'_type': 'required',
                           '_combo': {'a': 'required', 'b': 'required'},
                           '_validate': {'section': 'targets', 'field': 'ab',
                                         'scope': 'project'}}},
    }


def run_schema_cases():
    results = []

    results.append(_run_case(
        "schema accepts scope: project against a projectScope section",
        lambda: not _schema_rejects(
            _schema_case(['flat', 'projectScope'], 'project'))))
    results.append(_run_case(
        "schema rejects an unknown scope value",
        lambda: _schema_rejects(_schema_case(['flat'], 'yamlFile'))))
    results.append(_run_case(
        "schema rejects scope: project against a non-projectScope section",
        lambda: _schema_rejects(_schema_case(['flat'], 'project'))))
    results.append(_run_case(
        "schema rejects a projectScope target referenced without scope: project",
        lambda: _schema_rejects(
            _schema_case(['flat', 'projectScope'], None))))
    results.append(_run_case(
        "schema rejects an include-chain FK on a field of a projectScope section",
        lambda: _schema_rejects(_project_scope_source_case(None))))
    results.append(_run_case(
        "schema accepts scope: global on a field of a projectScope section",
        lambda: not _schema_rejects(_project_scope_source_case('global'))))
    results.append(_run_case(
        "schema rejects an include-chain FK on a sub-table of a projectScope section",
        lambda: _schema_rejects(_project_scope_subtable_case())))
    results.append(_run_case(
        "schema rejects an include-chain FK in a projectScope _dataSchema",
        lambda: _schema_rejects(_project_scope_data_schema_case())))
    results.append(_run_case(
        "schema rejects projectScope on a nested node",
        lambda: _schema_rejects(_nested_project_scope_case())))
    results.append(_run_case(
        "schema rejects a scope: project target declared after its referrer",
        lambda: _schema_rejects(_project_scope_order_case(target_first=False))))
    results.append(_run_case(
        "schema accepts the same pair with the target declared first",
        lambda: not _schema_rejects(_project_scope_order_case(target_first=True))))
    results.append(_run_case(
        "schema rejects scope: project on a combo foreign key",
        lambda: _schema_rejects(_combo_project_scope_case())))
    # No FK references this section, so only the projectScope/flat check itself
    # can reject it.
    results.append(_run_case(
        "schema rejects projectScope without flat",
        lambda: _schema_rejects(
            {'lonelyRows': {'_attribs': ['projectScope'], 'lonelyRow': 'key'}})))
    # scope is meaningless on a values validator, but still an authoring error.
    results.append(_run_case(
        "schema rejects an unknown scope on a non-section validator",
        lambda: _schema_rejects(
            {'targets': {'_attribs': ['flat'], 'target': 'key',
                         'mode': {'_type': 'optional(a)',
                                  '_validate': {'values': ['a', 'b'],
                                                'scope': 'nonsense'}}}})))
    return all(results)


# ------------------------------------------------------- in-process build ---

def run_composed_build():
    """One build of the composed fixture; every assertion reads its state."""
    original_cwd = os.getcwd()
    fixture, project_path, db_path = _make_fixture(ROOT_CLOCKS, CHILD_CLOCKS)
    conn = None
    results = []
    try:
        try:
            creator = projectCreate(project_path, db_path)
        except BaseException as exc:
            # In-process, so a build error raises (projectCreate calls exit() on a
            # YAML error) and would end the whole run with no named failure and
            # every assertion below unreported.
            print(f"FAIL: the composed fixture builds: {exc!r}")
            return False
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        buckets = ('assembler', 'childIp')

        def clock_rows():
            return {r['clockKey']: dict(r)
                    for r in conn.execute('select * from clocks')}

        def consumer_rows():
            return {r['clockConsumer']: dict(r)
                    for r in conn.execute('select * from clockConsumers')}

        def project_scope_discovery():
            # The projectScope set is schema-derived and must not also be
            # persisted into config.
            sections = creator.projectScopeSections
            if not sections:
                raise AssertionError(
                    "config/schema.yaml declares no projectScope section; the "
                    "mechanism has no shipped consumer to validate")
            for section in sections:
                if creator.config.getConfig(section.upper()) is not None:
                    raise AssertionError(
                        f"projectScope section '{section}' was also saved into "
                        f"the DB-backed config as {section.upper()}; it must be "
                        f"parsed into its bucket only")
            return True

        def no_artifact_for_project_file():
            # A project file carrying project-scoped rows must stay valid: False
            # in includeValid, so saveIncludeFiles emits no context header for it.
            # The child project file IS walked by the ordinary parser so it has an
            # entry; the root project file is not a context at all.
            childProjectFile = os.path.join('ip', 'ipProject.yaml')
            if childProjectFile not in creator.includeValid:
                raise AssertionError(
                    f"{childProjectFile} has no includeValid entry; contexts are "
                    f"{sorted(creator.includeValid)}, so this assertion no longer "
                    f"checks the include gate it claims to")
            if creator.includeValid[childProjectFile]['valid']:
                raise AssertionError(
                    f"{childProjectFile} is marked a valid include context, so "
                    f"saveIncludeFiles emits a generated context header for a "
                    f"project file")
            return True

        def declaring_project_bucket():
            rows = creator.data['clocks']
            if 'assembler' not in rows or 'childIp' not in rows:
                raise AssertionError(
                    f"clocks buckets are {sorted(rows)}; each project file "
                    f"declaring clocks: must own a bucket keyed by its "
                    f"projectName")
            return rows['assembler']['clk']['period'] == 1 \
                and rows['childIp']['clk']['period'] == 4

        def same_name_two_projects():
            # The case scope: global cannot pass: one name, two projects, two
            # rows, no duplicate-key error.
            rows = clock_rows()
            for key in ('clk/assembler', 'clk/childIp'):
                if key not in rows:
                    raise AssertionError(
                        f"{key} is absent from the clocks table; rows are "
                        f"{sorted(rows)}. Each project's rows must reach the "
                        f"one database of a composed build")
            return rows['clk/assembler']['desc'] != rows['clk/childIp']['desc']

        def design_yaml_resolves():
            rows = consumer_rows()
            if rows['topUser']['clockKey'] != 'clk/assembler':
                raise AssertionError(
                    f"top.yaml resolved clk to "
                    f"{rows['topUser']['clockKey']}, expected clk/assembler")
            return True

        def unrelated_context_resolves():
            # top2.yaml includes nothing and is included by nothing, so an
            # include-chain walk could not reach the declaration.
            rows = consumer_rows()
            context = creator.data['clockConsumers']
            top2 = [c for c in context if c.endswith('top2.yaml')]
            if not top2:
                raise AssertionError(
                    f"top2.yaml produced no clockConsumers context; buckets "
                    f"are {sorted(context)}")
            if creator.yamlContext[top2[0]].keys() != {top2[0]}:
                raise AssertionError(
                    f"top2.yaml has include-chain entries "
                    f"{list(creator.yamlContext[top2[0]])}; the fixture must "
                    f"keep it edge-free for this assertion to mean anything")
            return rows['top2User']['clockKey'] == 'clk/assembler'

        def child_resolves_in_own_project():
            rows = consumer_rows()
            if rows['ipUser']['clockKey'] != 'clk/childIp':
                raise AssertionError(
                    f"the child IP's design YAML resolved clk to "
                    f"{rows['ipUser']['clockKey']}, expected clk/childIp; a "
                    f"scope: project reference must resolve in the referring "
                    f"row's OWN project")
            return True

        def no_context_registry_leak():
            registries = {
                'yamlContext': creator.yamlContext,
                'includeValid': creator.includeValid,
                'includeName': creator.includeName,
                'CONTEXTNODEDIR': creator.config.getConfig('CONTEXTNODEDIR'),
                'YAMLCONTEXT': creator.config.getConfig('YAMLCONTEXT'),
            }
            for bucket in buckets:
                for name, registry in registries.items():
                    if bucket in registry:
                        raise AssertionError(
                            f"project bucket '{bucket}' appears in {name}. A "
                            f"project bucket is deliberately not a parse "
                            f"context; registering it there makes every "
                            f"context-iterating consumer see a key that is not "
                            f"a design YAML file")
            return True

        def owning_project_identity_only():
            extra = set(creator.contextOwningProject) - set(creator.yamlAllFiles)
            if extra != set(buckets):
                raise AssertionError(
                    f"contextOwningProject carries non-file keys {sorted(extra)}, "
                    f"expected exactly the project buckets {sorted(buckets)}")
            for bucket in buckets:
                if creator.contextOwningProject[bucket] != bucket:
                    raise AssertionError(
                        f"contextOwningProject['{bucket}'] is "
                        f"{creator.contextOwningProject[bucket]}, expected the "
                        f"identity entry")
            return True

        def reset_clock_resolves_in_project():
            # The one scope: project reference the shipped schema declares.
            rows = {r['resetKey']: dict(r)
                    for r in conn.execute('select * from resets')}
            return rows['rst_n/assembler']['clockKey'] == 'clk/assembler'

        results.append(_run_case(
            "projectScope sections are schema-derived and not saved to config",
            project_scope_discovery))
        results.append(_run_case(
            "a project file carrying project-scoped rows is no include context",
            no_artifact_for_project_file))
        results.append(_run_case(
            "each declaring project owns a projectName-keyed bucket",
            declaring_project_bucket))
        results.append(_run_case(
            "two projects declare the same clock name without collision",
            same_name_two_projects))
        results.append(_run_case(
            "design YAML resolves a project-file-declared name",
            design_yaml_resolves))
        results.append(_run_case(
            "an unrelated context with no include edge resolves too",
            unrelated_context_resolves))
        results.append(_run_case(
            "a child project's design YAML resolves in the child's bucket",
            child_resolves_in_own_project))
        results.append(_run_case(
            "shipped resets.clock resolves through scope: project",
            reset_clock_resolves_in_project))
        results.append(_run_case(
            "no project bucket key leaks into a context registry",
            no_context_registry_leak))
        results.append(_run_case(
            "contextOwningProject gains only the identity entries",
            owning_project_identity_only))
        return all(results)
    finally:
        if conn is not None:
            conn.close()
        os.chdir(original_cwd)
        shutil.rmtree(fixture)


def run_child_only_build():
    """Root project declares nothing; only the CHILD declares `clocks:`.

    The only shape that makes createProjectConfig's
    `ignoreSections.update(projectScopeSections)` load-bearing: when the ROOT
    declares the section, the generic `for item in self.proj` loop already covers
    it. With the root silent, dropping the update lets the CHILD project file -
    walked by the ordinary parser as a normal file - have its clocks: parsed a
    SECOND time into its own file context, and the build still exits 0.

    Built in a SUBPROCESS: projectCreate keeps its parse state in CLASS
    attributes, so a second in-process build inherits the first's contexts and,
    because both fixtures spell their design files identically, its content.
    """
    results = []
    fixture, project_path, db_path = _make_fixture(
        "", CHILD_CLOCKS, consumer_clock=None)
    conn = None
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print("FAIL: a child-only project-scoped declaration builds\n"
                  f"{output}")
            return False
        print("PASS: a child-only project-scoped declaration builds")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        clocks = [dict(r) for r in
                  conn.execute('select clockKey, _context from clocks')]

        def no_clocks_row_has_a_file_context():
            if not clocks:
                raise AssertionError(
                    "the clocks table is empty, so this assertion checks "
                    "nothing; the child project file must still contribute its "
                    "rows to the composed database")
            fileRows = [r for r in clocks if r['_context'].endswith('.yaml')]
            if fileRows:
                raise AssertionError(
                    f"clocks rows {[r['clockKey'] for r in fileRows]} carry a "
                    f".yaml _context ({[r['_context'] for r in fileRows]}); a "
                    f"project-scoped row's context is the declaring "
                    f"projectName, so a file context means the project file was "
                    f"parsed a second time as an ordinary design context")
            return True

        def child_declaration_is_not_duplicated():
            keys = sorted(r['clockKey'] for r in clocks)
            if keys != ['clk/assembler', 'clk/childIp']:
                raise AssertionError(
                    f"clocks rows are {keys}, expected exactly "
                    f"['clk/assembler', 'clk/childIp']: the root authors no "
                    f"clocks: and so inherits the built-in one, and the child's "
                    f"single declaration must produce a single row")
            return True

        def child_design_yaml_still_resolves():
            rows = {r['clockConsumer']: dict(r)
                    for r in conn.execute('select * from clockConsumers')}
            if rows['ipUser']['clockKey'] != 'clk/childIp':
                raise AssertionError(
                    f"the child's design YAML resolved clk to "
                    f"{rows['ipUser']['clockKey']}, expected clk/childIp")
            return True

        results.append(_run_case(
            "no clocks row carries a .yaml context (no duplicate re-parse)",
            no_clocks_row_has_a_file_context))
        results.append(_run_case(
            "a child-only declaration produces exactly one row",
            child_declaration_is_not_duplicated))
        results.append(_run_case(
            "a child-only declaration resolves for the child's design YAML",
            child_design_yaml_still_resolves))
        return all(results)
    finally:
        if conn is not None:
            conn.close()
        shutil.rmtree(fixture)


def run_authored_order_build():
    """A project file declaring resets: ABOVE clocks: must build.

    The pre-pass walks project-scoped sections in SCHEMA declaration order, not
    in the order the author happened to write them. resets.clock is a foreign key
    validated at parse time, so the authored order would otherwise decide whether
    a valid project file is accepted."""
    fixture, project_path, db_path = _make_fixture(REVERSED_ROOT_CLOCKS)
    conn = None
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print("FAIL: a project file declaring resets: above clocks: builds\n"
                  f"{output}")
            return False
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        def reset_resolved_across_authored_order():
            rows = {r['resetKey']: dict(r)
                    for r in conn.execute('select * from resets')}
            if rows['rst_n/assembler']['clockKey'] != 'clk/assembler':
                raise AssertionError(
                    f"rst_n resolved its clock to "
                    f"{rows['rst_n/assembler']['clockKey']}, expected "
                    f"clk/assembler")
            return True

        return _run_case(
            "resets: authored above clocks: still resolves into clocks:",
            reset_resolved_across_authored_order)
    finally:
        if conn is not None:
            conn.close()
        shutil.rmtree(fixture)


def run_mapto_alias_build():
    """A project file spelling a project-scoped section through its _mapto alias.

    processSingleFile resolves aliases before dispatch, so a design YAML
    authoring the alias is rejected. The pre-pass must resolve them too, or an
    aliased section is dropped with no row and no diagnostic."""
    fixture, project_path, db_path = _make_fixture(ALIASED_ROOT_CLOCKS)
    conn = None
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print("FAIL: a project file may declare a project-scoped section "
                  f"through its _mapto alias\n{output}")
            return False
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        def aliased_declaration_produces_a_row():
            rows = {r['clockKey']: dict(r)
                    for r in conn.execute('select * from clocks')}
            if 'clk/assembler' not in rows:
                raise AssertionError(
                    f"clocks rows are {sorted(rows)}; a project file authoring "
                    f"the _mapto alias must contribute the same row as the "
                    f"canonical spelling, or the declaration is swallowed")
            if rows['clk/assembler']['desc'] != 'aliased clock':
                raise AssertionError(
                    f"clk/assembler carries desc "
                    f"{rows['clk/assembler']['desc']!r}, so the row did not come "
                    f"from the aliased declaration")
            return True

        return _run_case(
            "a project file may declare through a _mapto alias",
            aliased_declaration_produces_a_row)
    finally:
        if conn is not None:
            conn.close()
        shutil.rmtree(fixture)


def run_scope_named_context_build():
    """A design file whose context key spells a scope name keeps its own scope.

    A dispatch that selects the project-scope path by comparing the referring
    row's context against the string 'project' misroutes an extension-less design
    file named `project` into a project bucket, where nothing resolves."""
    fixture, project_path, db_path = _make_fixture(
        ROOT_CLOCKS, extra_design_files=(('project', SCOPE_NAMED_CONTEXT),))
    conn = None
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print("FAIL: a design file named after a scope resolves its "
                  f"include-chain foreign keys\n{output}")
            return False
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        def include_chain_fk_resolved_in_its_own_file():
            rows = {r['plainRef']: dict(r)
                    for r in conn.execute('select * from plainRefs')}
            if rows['magicRef']['targetKey'] != 'magicRow/project':
                raise AssertionError(
                    f"magicRef resolved its target to "
                    f"{rows['magicRef']['targetKey']}, expected "
                    f"magicRow/project: a validator that declares no scope must "
                    f"walk the referring file's include chain whatever that file "
                    f"is named")
            return True

        return _run_case(
            "a design file named after a scope keeps include-chain resolution",
            include_chain_fk_resolved_in_its_own_file)
    finally:
        if conn is not None:
            conn.close()
        shutil.rmtree(fixture)


def run_empty_body_accepted_by_guard():
    """`clocks: {}` and `clocks: []` must reach the section's own rules.

    An empty container is the one body shape the malformed-body guard must not
    reject, and it is indistinguishable from a null body once the guard tests
    truthiness rather than type. The section is nonetheless declared and empty,
    so the exactly-one-default rule rejects it - which is the proof the guard let
    it through: the body-shape diagnostic must NOT be what fails the build."""
    results = []
    for shape, body in (('an empty mapping', "clocks: {}\n"),
                        ('an empty list', "clocks: []\n")):
        fixture, project_path, db_path = _make_fixture(body, consumer_clock=None)
        label = (f"a project-scoped section with {shape} body passes the "
                 f"body-shape guard")
        try:
            code, output = _build(project_path, db_path)
            if 'mapping of named entries' in output:
                print(f"FAIL: {label}: the malformed-body guard rejected an "
                      f"empty container\n{output}")
                results.append(False)
            elif 'no entry declares default: true' not in output:
                print(f"FAIL: {label}: expected the empty section to be "
                      f"rejected for declaring no default\n{output}")
                results.append(False)
            elif code == 0:
                print(f"FAIL: {label}: a declared section with no default "
                      f"entry must fail the build\n{output}")
                results.append(False)
            else:
                print(f"PASS: {label}")
                results.append(True)
        finally:
            shutil.rmtree(fixture)
    return all(results)


def _rows_by_key(db_path, table, keyField):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return {r[keyField]: dict(r)
                for r in conn.execute(f'select * from {table}')}
    finally:
        conn.close()


def _built_rows(label, root_clocks, consumer_clock, checks):
    """Build a single-project fixture and run `checks` over its stored rows.

    Each check is (name, fn(clocks, resets)); fn returns True or raises."""
    fixture, project_path, db_path = _make_fixture(
        root_clocks, consumer_clock=consumer_clock)
    try:
        code, output = _build(project_path, db_path)
        if code != 0:
            print(f"FAIL: {label}\n{output}")
            return False
        print(f"PASS: {label}")
        clocks = _rows_by_key(db_path, 'clocks', 'clockKey')
        resets = _rows_by_key(db_path, 'resets', 'resetKey')
        return all(_run_case(name, lambda fn=fn: fn(clocks, resets))
                   for name, fn in checks)
    finally:
        shutil.rmtree(fixture)


def run_implicit_default_build():
    """A project declaring NEITHER section owns both built-in declarations.

    Injection is what keeps such a project - every project in existence today -
    building unchanged while consumers may assume a default clock and reset
    exist. It is asserted on the stored rows, since a build that merely succeeds
    is equally consistent with nothing having been injected at all."""

    def clock_injected(clocks, resets):
        if sorted(clocks) != ['clk/assembler']:
            raise AssertionError(
                f"clocks rows are {sorted(clocks)}, expected exactly "
                f"['clk/assembler']: a project authoring no clocks: inherits the "
                f"built-in one")
        row = clocks['clk/assembler']
        if not (row['default'] and row['period'] == 1 and row['timeUnit'] == 'ns'):
            raise AssertionError(
                f"the injected clock is {row['clock']} default={row['default']} "
                f"period={row['period']} timeUnit={row['timeUnit']}, expected the "
                f"built-in default clk/1/ns")
        return True

    def reset_injected_and_resolved(clocks, resets):
        if sorted(resets) != ['rst_n/assembler']:
            raise AssertionError(
                f"resets rows are {sorted(resets)}, expected exactly "
                f"['rst_n/assembler']")
        row = resets['rst_n/assembler']
        if not row['default']:
            raise AssertionError(
                f"the injected reset is default={row['default']}, expected the "
                f"built-in default")
        # The injected row states no clock:, so the stored value can only come
        # from the unstated-means-default resolution.
        if (row['clock'], row['clockKey']) != ('clk', 'clk/assembler'):
            raise AssertionError(
                f"the injected reset stored clock={row['clock']!r} "
                f"clockKey={row['clockKey']!r}, expected ('clk', "
                f"'clk/assembler'): an unstated clock: is the project's default "
                f"clock, resolved once so no consumer sees an empty field")
        return True

    return _built_rows(
        "a project declaring no project-scoped section builds", "", None,
        (("a project authoring no clocks: inherits the built-in clock",
          clock_injected),
         ("a project authoring no resets: inherits the built-in reset",
          reset_injected_and_resolved)))


def run_own_clock_injected_reset_build():
    """A project declaring its own clocks: and no resets:.

    The mixed case: injection is per section, so this project owns its clocks and
    still inherits the reset. A literal `clock: clk` on the injected reset would
    be an unresolvable reference here, since the project declares no clock of
    that name."""

    def no_clock_injected(clocks, resets):
        if sorted(clocks) != ['coreClk/assembler']:
            raise AssertionError(
                f"clocks rows are {sorted(clocks)}; a project declaring the "
                f"section owns it completely and must receive no injected row")
        return True

    def reset_resolved_to_own_default(clocks, resets):
        row = resets['rst_n/assembler']
        if (row['clock'], row['clockKey']) != ('coreClk', 'coreClk/assembler'):
            raise AssertionError(
                f"the inherited reset stored clock={row['clock']!r} "
                f"clockKey={row['clockKey']!r}, expected ('coreClk', "
                f"'coreClk/assembler'): the unstated clock: is THIS project's "
                f"default clock, whatever it is named")
        return True

    return _built_rows(
        "a project declaring its own clocks: and no resets: builds",
        CORE_CLOCK_ONLY, 'coreClk',
        (("a declared section receives no injection", no_clock_injected),
         ("an inherited reset resolves to the project's own default clock",
          reset_resolved_to_own_default)))


def run_multi_entry_one_default_build():
    """Several entries with exactly ONE default: the feature's happy path.

    The rule is exactly one default, not one entry, so a section carrying
    non-default entries alongside the default must be accepted - the shape every
    multi-clock project has."""

    def both_clocks_stored(clocks, resets):
        if sorted(clocks) != ['clk/assembler', 'clkSlow/assembler']:
            raise AssertionError(
                f"clocks rows are {sorted(clocks)}, expected both entries; a "
                f"section with one default among several must be accepted whole")
        if clocks['clkSlow/assembler']['default']:
            raise AssertionError(
                "clkSlow is stored as a default entry, so this fixture no longer "
                "has exactly one default and asserts nothing about the rule")
        return True

    def authored_reset_defaults_to_default_clock(clocks, resets):
        if resets['rst_n/assembler']['clockKey'] != 'clk/assembler':
            raise AssertionError(
                f"the authored reset omitting clock: resolved to "
                f"{resets['rst_n/assembler']['clockKey']}, expected "
                f"clk/assembler: the unstated-means-default rule applies to "
                f"authored rows, not only injected ones")
        if resets['rstAlt_n/assembler']['clockKey'] != 'clkSlow/assembler':
            raise AssertionError(
                f"the authored reset naming clkSlow resolved to "
                f"{resets['rstAlt_n/assembler']['clockKey']}; a stated clock: "
                f"must not be overwritten by the default")
        return True

    return _built_rows(
        "a section with several entries and exactly one default builds",
        MULTI_ENTRY_ONE_DEFAULT, 'clkSlow',
        (("every entry of a one-default section is stored", both_clocks_stored),
         ("an unstated clock: resolves to the default, a stated one survives",
          authored_reset_defaults_to_default_clock)))


def run_count_field_types_build():
    """A count field is stored as one int whether authored or defaulted.

    An optional(N) schema default is stored as the string from the schema text
    while an authored N arrives as an int, so without coercion one stored fact
    has two types and anything comparing or adding it must convert first. The
    emitters only interpolate the value, so this is invisible in emitted text and
    can only be asserted on the stored type."""

    def periods_are_ints(clocks, resets):
        for key, expected in (('clk/assembler', 1), ('clkSlow/assembler', 4)):
            value = clocks[key]['period']
            if type(value) is not int or value != expected:
                raise AssertionError(
                    f"{key} stored period {value!r} ({type(value).__name__}), "
                    f"expected the int {expected}")
        return True

    def release_counts_are_ints(clocks, resets):
        for key, expected in (('rst_n/assembler', 3), ('rstAlt_n/assembler', 5)):
            value = resets[key]['releaseCycles']
            if type(value) is not int or value != expected:
                raise AssertionError(
                    f"{key} stored releaseCycles {value!r} "
                    f"({type(value).__name__}), expected the int {expected}")
        return True

    return _built_rows(
        "a project mixing authored and defaulted count fields builds",
        COUNT_FIELD_TYPES, 'clkSlow',
        (("a defaulted and an authored period are both stored as ints",
          periods_are_ints),
         ("a defaulted and an authored releaseCycles are both stored as ints",
          release_counts_are_ints)))


# ------------------------------------------------------------ diagnostics --

def _build(project_path, db_path):
    """Run one database build in a subprocess. Returns (returncode, output).

    Always launched from unittest/, so a caller may spell --yaml relative to
    that directory to exercise how the root project file path is recorded."""
    env = os.environ.copy()
    env['NO_COLOR'] = '1'
    completed = subprocess.run(
        [sys.executable, os.path.join(base_dir, 'arch2code.py'),
         '--yaml', project_path, '--db', db_path],
        capture_output=True, text=True, timeout=300, env=env, cwd=test_dir)
    return completed.returncode, completed.stdout + completed.stderr


def _build_expecting_failure(**fixtureKwargs):
    fixture, project_path, db_path = _make_fixture(**fixtureKwargs)
    try:
        return _build(project_path, db_path)
    finally:
        shutil.rmtree(fixture)


def _expect_diagnostic(label, needles, **fixtureKwargs):
    def check():
        code, output = _build_expecting_failure(**fixtureKwargs)
        if code == 0:
            raise AssertionError(
                f"build succeeded; it must fail.\n{output}")
        # A crash is not a diagnostic: an unguarded dict index exits non-zero
        # too, which would satisfy the returncode check above on its own.
        if 'Traceback' in output:
            raise AssertionError(
                f"the build crashed instead of reporting a diagnostic.\n{output}")
        for needle in needles:
            if needle not in output:
                raise AssertionError(
                    f"diagnostic does not mention '{needle}', so the author is "
                    f"not pointed at what to fix.\n{output}")
        return True
    return _run_case(label, check)


def _project_file_diagnostic_case(label, root_clocks, needles, expect_failure=True):
    """Every message about a row authored in the project file names that FILE.

    A project-scoped row is parsed with the declaring projectName as its context,
    so a message printing the parse context names a project, not a file the author
    can open; every processSimple check is reachable from a project file by a
    one-token typo. --yaml is spelled relative to a different directory here too:
    the root project file's recorded path must sit on the same absolute base as
    every child's, or one family of diagnostics reports two path bases.

    `expect_failure=False` covers the checks that only warn - the message still
    has to name a file."""
    def check():
        fixture, project_path, db_path = _make_fixture(root_clocks)
        try:
            code, output = _build(os.path.relpath(project_path, test_dir), db_path)
            if expect_failure and code == 0:
                raise AssertionError(f"build succeeded; it must fail.\n{output}")
            if not expect_failure and code != 0:
                raise AssertionError(
                    f"build failed; this input must only warn.\n{output}")
            if 'Traceback' in output:
                raise AssertionError(
                    f"the build crashed instead of reporting a diagnostic.\n{output}")
            for needle in (f"In file {project_path}:", *needles):
                if needle not in output:
                    raise AssertionError(
                        f"message does not mention '{needle}', so it does not "
                        f"name the file and line the author must edit.\n{output}")
            return True
        finally:
            shutil.rmtree(fixture)
    return _run_case(label, check)


def run_diagnostic_cases():
    results = []

    # One case per reachable check: each interpolates the parse context itself.
    results.append(_project_file_diagnostic_case(
        "an unresolved reference in the project file names that file's path",
        UNRESOLVED_IN_PROJECT_FILE, ('noSuchClock', 'clocks:')))
    results.append(_project_file_diagnostic_case(
        "a values-validator rejection in the project file names that file's path",
        BAD_VALUE_IN_PROJECT_FILE, ('timeUnit', 'xs')))
    results.append(_project_file_diagnostic_case(
        "a missing required field in the project file names that file's path",
        MISSING_FIELD_IN_PROJECT_FILE, ('missing required field desc',)))
    results.append(_project_file_diagnostic_case(
        "an unknown field in the project file names that file's path",
        UNKNOWN_FIELD_IN_PROJECT_FILE, ('unknown field bogusField',),
        expect_failure=False))

    # An undeclared name must name the owning project AND its project file,
    # because there is no include chain the author could repair instead.
    results.append(_expect_diagnostic(
        "undeclared name names the owning project and its project file",
        ["noSuchClock", "'assembler'", "project.yaml", "clocks:"],
        root_clocks=ROOT_CLOCKS, consumer_clock='noSuchClock'))

    # A projectName equal to a context file key would silently merge two
    # unrelated declaration sets in the shared self.data[section] keyspace.
    results.append(_expect_diagnostic(
        "projectName colliding with a context key is rejected",
        ["top.yaml", "collides"],
        root_clocks=ROOT_CLOCKS, root_project_name='top.yaml'))

    # A declared section with no default entry, caught once per project per
    # section. Both sections are covered because they are independent, and the
    # message must name the project file rather than the bucket key the rows were
    # parsed under.
    no_default_clock = (
        "clocks:\n"
        "  clkA: { desc: \"the only clock, and not the default\" }\n")
    results.append(_expect_diagnostic(
        "a clocks: section declaring no default is rejected",
        ["project.yaml", "clocks", "no entry declares default: true",
         "exactly one default"],
        root_clocks=no_default_clock, consumer_clock='clkA'))

    no_default_reset = (
        "clocks:\n"
        "  clk: { desc: \"only clock\", default: true }\n"
        "\n"
        "resets:\n"
        "  rst_n: { desc: \"the only reset, and not the default\", clock: clk }\n")
    results.append(_expect_diagnostic(
        "a resets: section declaring no default is rejected",
        ["project.yaml", "resets", "no entry declares default: true",
         "exactly one default"],
        root_clocks=no_default_reset))

    # The same rule on a CHILD project's section, naming the child's own project
    # file: the check runs per project in the build, not only for the root, and a
    # message naming the root's project file would point at the wrong file.
    no_default_child_clock = (
        "clocks:\n"
        "  clkC: { desc: \"the child's only clock, and not the default\" }\n")
    results.append(_expect_diagnostic(
        "a child project's section declaring no default is rejected",
        [os.path.join('ip', 'ipProject.yaml'), "'childIp'",
         "no entry declares default: true"],
        root_clocks=ROOT_CLOCKS, child_clocks=no_default_child_clock,
        child_consumer_clock='clkC'))

    # The other failure mode of the one rule: more than one default.
    two_defaults = (
        "clocks:\n"
        "  clk:     { desc: \"first\", default: true }\n"
        "  clkSlow: { desc: \"second\", default: true }\n")
    results.append(_expect_diagnostic(
        "a second default: true clock in one project is rejected",
        ["clkSlow", "exactly one default"],
        root_clocks=two_defaults))

    # The same rule on the independent resets: section.
    two_reset_defaults = (
        "clocks:\n"
        "  clk: { desc: \"only clock\", default: true }\n"
        "\n"
        "resets:\n"
        "  rst_n:    { desc: \"first\", default: true, clock: clk }\n"
        "  rstAlt_n: { desc: \"second\", default: true, clock: clk }\n")
    results.append(_expect_diagnostic(
        "a second default: true reset in one project is rejected",
        ["rstAlt_n", "exactly one default"],
        root_clocks=two_reset_defaults))

    # Two project files declaring ONE projectName share one bucket. The clock
    # names are distinct and only one is default, so nothing else objects:
    # without the guard the merge is silent and the build exits 0.
    results.append(_expect_diagnostic(
        "two project files declaring one projectName are rejected",
        ["childIp", "two project files", "ipProject.yaml"],
        root_clocks="clocks:\n  clkA: { desc: \"root clock\", default: true }\n",
        child_clocks="clocks:\n  clkB: { desc: \"child clock\" }\n",
        root_project_name='childIp',
        consumer_clock='clkA', child_consumer_clock='clkB'))

    # The SECOND project file needs no declaration of its own: the duplicate name
    # is what points its design YAML at the first project's bucket, where clk
    # would silently resolve against the ROOT's declaration.
    results.append(_expect_diagnostic(
        "a duplicate projectName is rejected when the second declares nothing",
        ["childIp", "two project files", "ipProject.yaml"],
        root_clocks=ROOT_CLOCKS, child_clocks="",
        root_project_name='childIp'))

    # ignoreSections is consulted before the unknown-section check, so without the
    # guard a projectScope section in a DESIGN yaml is dropped silently. Every body
    # shape must reach the diagnostic: a null body (every entry commented out) and
    # a scalar carry no ruamel position.
    for shape, extra in (
            ('a mapping', "\nclocks:\n"
                          "  clkWrongFile: { desc: \"declared in design yaml\" }\n"),
            ('a list', "\nclocks:\n  - clkWrongFile\n"),
            ('a null body', "\nclocks:\n"),
            ('a scalar body', "\nclocks: notAMapping\n")):
        results.append(_expect_diagnostic(
            f"a projectScope section with {shape} in a design YAML is rejected",
            ["top.yaml", "clocks:", "project file"],
            root_clocks=ROOT_CLOCKS, design_yaml_extra=extra))

    # The project file is the authoring location for a project-scoped section, so
    # every malformed body shape must be named there too. The pre-pass drives
    # processSection directly, so nothing upstream inspects the body first.
    for shape, body, needle in (
            ('a null body', "clocks:\n", 'mapping of named entries'),
            ('a body of only comments',
             "clocks:\n#  clk: { desc: \"commented out\" }\n",
             'mapping of named entries'),
            ('a scalar body', "clocks: notAMapping\n", "got str 'notAMapping'"),
            ('a list of scalars', "clocks:\n  - clkA\n",
             'must be a mapping of fields')):
        results.append(_expect_diagnostic(
            f"a project-scoped section with {shape} in the project file is rejected",
            ['project.yaml', 'clocks', needle],
            root_clocks=body, consumer_clock=None))

    # A count field below one, or not a whole number at all, reaches the
    # generated wrapper as C++ nobody reads: `cycle < 0` never runs, so the reset
    # is released at time zero and never asserted. Rejected at parse time
    # instead, per section, and the message must name the entry and the value.
    for section, entry, template in (
            ('resets', 'rst_n',
             "clocks:\n"
             "  clk: { desc: \"only clock\", default: true }\n"
             "\n"
             "resets:\n"
             "  rst_n: { desc: \"only reset\", default: true, clock: clk, "
             "releaseCycles: %s }\n"),
            ('clocks', 'clk',
             "clocks:\n"
             "  clk: { desc: \"only clock\", default: true, period: %s }\n")):
        field = 'releaseCycles' if section == 'resets' else 'period'
        for authored, rendered in (('0', '0'), ('-1', '-1'), ('2.5', '2.5'),
                                   ('abc', "'abc'")):
            results.append(_expect_diagnostic(
                f"{section}.{field}: {authored} is rejected",
                ['project.yaml', "'assembler'", f"{section}:",
                 f"entry '{entry}'", f"{field}: {rendered}",
                 'not a positive integer'],
                root_clocks=template % authored))

    # A special context belongs to no project and is keyed in no bucket, so
    # without the guard the direct bucket hit raises a bare KeyError.
    results.append(_expect_diagnostic(
        "a scope: project reference from a special context is rejected",
        ["_a2csystem", "belongs to no project"],
        root_clocks=ROOT_CLOCKS, system_scope_field=True))

    return all(results)


def _run():
    print("Project-scoped declarations (scope: project)")
    # In-process builds first: the schema cases drive Schema() to printError/exit,
    # leaving errors in the global counter that a later projectCreate would report.
    ok = run_composed_build()
    ok = run_child_only_build() and ok
    ok = run_authored_order_build() and ok
    ok = run_mapto_alias_build() and ok
    ok = run_scope_named_context_build() and ok
    ok = run_empty_body_accepted_by_guard() and ok
    ok = run_implicit_default_build() and ok
    ok = run_own_clock_injected_reset_build() and ok
    ok = run_multi_entry_one_default_build() and ok
    ok = run_count_field_types_build() and ok
    ok = run_schema_cases() and ok
    ok = run_diagnostic_cases() and ok
    return ok


def run_all_tests():
    return 0 if _run() else 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
